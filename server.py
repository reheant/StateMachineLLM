"""
Sherpa — FastAPI backend
Replaces `chainlit run app.py` with `uvicorn server:app --reload --port 8000`
"""

import asyncio
import contextlib
import io
import json
import logging
import os
import queue
import threading
import time
import traceback
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import backend.resources.state_machine_descriptions as sm_descriptions
from backend.grading import run_automatic_grading
from backend.resources.util import setup_file_paths
from backend.single_prompt import process_custom_mermaid, run_single_prompt
from backend.two_shot_prompt import run_two_shot_prompt

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Sherpa")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
RESOURCES_DIR = BASE_DIR / "backend" / "resources"

# ---------------------------------------------------------------------------
# Model mapping (copied from app.py)
# ---------------------------------------------------------------------------

# Keys match app.py chat profile names (provider:model-id format)
# Values are OpenRouter model strings
PROFILE_TO_OPENROUTER: dict[str, str] = {
    "anthropic:claude-4-5-sonnet": "anthropic/claude-4.5-sonnet",
    "anthropic:claude-3-5-sonnet-20241022": "anthropic/claude-3.5-sonnet",
    "anthropic:claude-sonnet-4": "anthropic/claude-sonnet-4",
    "openai:gpt-4o": "openai/gpt-4o",
    "openai:gpt-4o-mini": "openai/gpt-4o-mini",
    "openai:gpt-4-turbo": "openai/gpt-4-turbo",
    "openai:o1": "openai/o1",
    "openai:o1-mini": "openai/o1-mini",
    "google:gemini-2-0-flash-exp": "google/gemini-2.0-flash-exp",
    "google:gemini-1-5-pro-001": "google/gemini-pro-1.5",
    "google:gemini-1-5-flash": "google/gemini-flash-1.5",
    "meta:llama-3-3-70b-instruct": "meta-llama/llama-3.3-70b-instruct",
    "meta:llama-3-1-405b-instruct": "meta-llama/llama-3.1-405b-instruct",
    "meta:llama-3-1-70b-instruct": "meta-llama/llama-3.1-70b-instruct",
    "meta:llama-3-2-3b-instruct": "meta-llama/llama-3.2-3b-instruct",
    "qwen:qwq-32b": "qwen/qwq-32b",
    "qwen:qwen-2-5-72b-instruct": "qwen/qwen-2.5-72b-instruct",
}

# ---------------------------------------------------------------------------
# Example catalogue (copied from app.py)
# ---------------------------------------------------------------------------

EXAMPLE_META: dict[str, tuple[str, str, str]] = {
    "printer_winter_2017": (
        "🖨️",
        "Printer System",
        "office printer with card authentication, print/scan, and error handling",
    ),
    "spa_manager_winter_2018": (
        "🧖",
        "Spa Manager",
        "sauna & Jacuzzi control with temperature regulation and water jets",
    ),
    "dishwasher_winter_2019": (
        "✨",
        "Smart Dishwasher",
        "automated dishwasher with multiple programs, drying, and door safety",
    ),
    "chess_clock_fall_2019": (
        "🕰️",
        "Digital Chess Clock",
        "tournament chess clock with multiple timing modes and player controls",
    ),
    "automatic_bread_maker_fall_2020": (
        "🥖",
        "Automatic Bread Maker",
        "programmable bread maker with crust options and delayed start",
    ),
    "thermomix_fall_2021": (
        "🔪",
        "Thermomix TM6",
        "guided recipe steps and ingredient processing",
    ),
    "ATAS_fall_2022": (
        "🚆",
        "Train Automation System",
        "driverless trains across a rail network with signals and stations",
    ),
    "WUMPLE_fall_2023_Version_A": (
        "⌚",
        "Wumple Watch",
        "timekeeping, alarm, and countdown modes with backlight and flash alerts",
    ),
    "SSC7_fall_2024_Version_A": (
        "🛒",
        "SSC7 Self-Checkout",
        "supermarket self-checkout with scanning, weighing, payment, and staff override",
    ),
}

EXAMPLE_FALLBACK_ICON = "🧩"


def _humanize_example_key(key: str) -> str:
    parts = [p for p in key.split("_") if p]
    filtered = [
        p
        for p in parts
        if p.lower()
        not in {"fall", "winter", "spring", "summer", "version", "a", "b", "c"}
        and not p.isdigit()
    ]
    return " ".join(p.capitalize() for p in filtered) or key


def _build_examples() -> list[tuple[str, str, str, str, str]]:
    keys = [
        name
        for name in dir(sm_descriptions)
        if not name.startswith("_") and isinstance(getattr(sm_descriptions, name), str)
    ]
    keys.sort()

    examples: list[tuple[str, str, str, str, str]] = []
    for key in keys:
        desc = getattr(sm_descriptions, key)
        if key in EXAMPLE_META:
            icon, label, blurb = EXAMPLE_META[key]
        else:
            icon = EXAMPLE_FALLBACK_ICON
            label = _humanize_example_key(key)
            blurb = desc.strip().split("\n", 1)[0][:120]
        examples.append((key, icon, label, blurb, desc))
    return examples


EXAMPLES = _build_examples()

# ---------------------------------------------------------------------------
# Path safety helper
# ---------------------------------------------------------------------------


def _safe_path(raw: str) -> Path:
    """Resolve path and ensure it's inside RESOURCES_DIR."""
    resolved = Path(raw).resolve()
    if not str(resolved).startswith(str(RESOURCES_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Path outside resources directory")
    return resolved


# ---------------------------------------------------------------------------
# History helpers
# ---------------------------------------------------------------------------


def _scan_runs() -> list[dict]:
    """Walk both output dirs and return a list of run metadata dicts."""
    runs = []
    for strategy in (
        "single_prompt",
        "two_shot_prompt",
        "mermaid_compiler",
        "automatic_grader",
    ):
        outputs_dir = RESOURCES_DIR / f"{strategy}_outputs"
        if not outputs_dir.exists():
            continue
        for date_dir in outputs_dir.iterdir():
            if not date_dir.is_dir():
                continue
            for model_dir in date_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                for system_dir in model_dir.iterdir():
                    if not system_dir.is_dir():
                        continue
                    for time_dir in system_dir.iterdir():
                        if not time_dir.is_dir():
                            continue
                        has_png = any(time_dir.glob("*.png"))
                        date_fmt = date_dir.name.replace("_", "-")
                        time_fmt = time_dir.name.replace("_", ":")
                        runs.append(
                            {
                                "strategy": strategy,
                                "date": date_fmt,
                                "time": time_fmt,
                                "model": model_dir.name,
                                "system": system_dir.name,
                                "folder": str(time_dir),
                                "has_png": has_png,
                                "sort_key": f"{date_dir.name}_{time_dir.name}",
                            }
                        )
    runs.sort(key=lambda r: r["sort_key"], reverse=True)
    for r in runs:
        del r["sort_key"]
    return runs


def _sanitize_system_name(system_name: str) -> str:
    safe_system_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in system_name
    )
    return safe_system_name.strip().replace(" ", "_")


def _has_run_artifacts(run_dir: Path) -> bool:
    return any(
        child.is_file()
        and (
            child.suffix in {".png", ".mmd", ".txt", ".csv", ".tsv"}
            or child.name in {"LLM_log.txt", "grading_prompt.txt", "grading_output.txt"}
        )
        for child in run_dir.iterdir()
    )


def _find_latest_run_folder(
    strategy: str,
    *,
    system_name: str | None = None,
    model_name: str | None = None,
    since: float | None = None,
) -> str | None:
    """Find the newest matching top-level run folder for a strategy."""
    outputs_dir = RESOURCES_DIR / f"{strategy}_outputs"
    if not outputs_dir.exists():
        return None

    safe_system_name = _sanitize_system_name(system_name) if system_name else None
    latest_path: Path | None = None
    latest_mtime = 0.0

    for date_dir in outputs_dir.iterdir():
        if not date_dir.is_dir():
            continue
        for model_dir in date_dir.iterdir():
            if not model_dir.is_dir():
                continue
            if model_name and model_dir.name != model_name:
                continue
            for system_dir in model_dir.iterdir():
                if not system_dir.is_dir():
                    continue
                if safe_system_name and system_dir.name != safe_system_name:
                    continue
                for time_dir in system_dir.iterdir():
                    if not time_dir.is_dir() or not _has_run_artifacts(time_dir):
                        continue
                    try:
                        mtime = time_dir.stat().st_mtime
                    except OSError:
                        continue
                    if since is not None and mtime < since:
                        continue
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_path = time_dir

    return str(latest_path) if latest_path else None


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.get("/api/examples")
def get_examples():
    return [
        {
            "key": k,
            "icon": icon,
            "label": label,
            "blurb": blurb,
            "description": description,
        }
        for k, icon, label, blurb, description in EXAMPLES
    ]


@app.get("/api/description")
def get_description(preset: str = Query(...)):
    """Return the full description text for an example preset."""
    text = getattr(sm_descriptions, preset, None)
    if text is None:
        raise HTTPException(status_code=404, detail=f"Preset '{preset}' not found")
    return {"description": text}


@app.get("/api/models")
def get_models():
    return list(PROFILE_TO_OPENROUTER.keys())


@app.get("/api/history")
def get_history():
    return _scan_runs()


@app.get("/api/artifacts")
def get_artifacts(folder: str = Query(...)):
    path = _safe_path(folder)
    if not path.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    files: dict[str, str | None] = {
        "png": None,
        "mmd": None,
        "txt": None,
        "shot1_png": None,
        "shot1_mmd": None,
        "shot1_txt": None,
        "llm_log": None,
        "grading_prompt": None,
        "grading_output": None,
        "ground_truth_csv": None,
        "grading_csv": None,
        "grading_tsv": None,
    }

    for f in path.iterdir():
        if f.suffix == ".png":
            files["png"] = str(f)
        elif f.suffix == ".mmd":
            files["mmd"] = str(f)
        elif f.name == "LLM_log.txt":
            files["llm_log"] = str(f)
        elif f.name == "grading_prompt.txt":
            files["grading_prompt"] = str(f)
        elif f.name == "grading_output.txt":
            files["grading_output"] = str(f)
        elif f.name == "ground_truth.csv":
            files["ground_truth_csv"] = str(f)
        elif f.name == "grading_results.csv":
            files["grading_csv"] = str(f)
        elif f.name == "grading_results.tsv":
            files["grading_tsv"] = str(f)
        elif f.suffix == ".txt" and f.name != "LLM_log.txt":
            files["txt"] = str(f)

    shot1_dir = path / "shot1"
    if shot1_dir.is_dir():
        for f in shot1_dir.iterdir():
            if f.suffix == ".png":
                files["shot1_png"] = str(f)
            elif f.suffix == ".mmd":
                files["shot1_mmd"] = str(f)
            elif f.suffix == ".txt":
                files["shot1_txt"] = str(f)

    return files


@app.get("/api/image")
def serve_image(path: str = Query(...)):
    resolved = _safe_path(path)
    if not resolved.exists():
        raise HTTPException(status_code=404)
    return FileResponse(resolved, media_type="image/png")


@app.get("/api/file")
def serve_file(path: str = Query(...)):
    resolved = _safe_path(path)
    if not resolved.exists():
        raise HTTPException(status_code=404)
    return FileResponse(resolved, media_type="text/plain")


# ---------------------------------------------------------------------------
# Generation — SSE streaming
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    strategy: Literal["single_prompt", "two_shot_prompt"]
    model: str
    system_name: str
    description: str
    example_key: str | None = None
    enable_auto_grading: bool = True
    input_mode: Literal["example", "custom"] | None = None


class _QueueWriter(io.RawIOBase):
    """Redirect stdout lines into a queue for SSE streaming."""

    def __init__(self, q: queue.Queue):
        self._q = q
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self._q.put(("progress", line.strip()))
        return len(text)

    def flush(self):
        if self._buf.strip():
            self._q.put(("progress", self._buf.strip()))
            self._buf = ""


class _QueueLogHandler(logging.Handler):
    """Mirror logging output into the SSE progress queue."""

    def __init__(self, q: queue.Queue):
        super().__init__(level=logging.INFO)
        self._q = q

    def emit(self, record: logging.LogRecord):
        try:
            message = self.format(record).strip()
        except Exception:
            self.handleError(record)
            return
        if message:
            self._q.put(("progress", message))


@app.post("/api/generate")
def generate(req: GenerateRequest):
    openrouter_model = PROFILE_TO_OPENROUTER.get(req.model, req.model)
    q: queue.Queue = queue.Queue()

    def _run():
        writer = _QueueWriter(q)
        log_handler = _QueueLogHandler(q)
        log_handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s: %(message)s")
        )
        root_logger = logging.getLogger()
        previous_root_level = root_logger.level
        request_started_at = time.time()
        try:
            root_logger.addHandler(log_handler)
            if root_logger.getEffectiveLevel() > logging.INFO:
                root_logger.setLevel(logging.INFO)
            effective_auto_grading = (
                req.enable_auto_grading and req.input_mode != "custom"
            )
            if effective_auto_grading and not req.example_key:
                q.put(
                    (
                        "error",
                        "example_key is required when automatic grading is enabled.",
                    )
                )
                return

            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(
                writer
            ):  # type: ignore[arg-type]
                if req.strategy == "single_prompt":
                    success = run_single_prompt(
                        req.description,
                        openrouter_model,
                        req.system_name,
                        effective_auto_grading,
                        req.example_key,
                    )
                else:
                    success = run_two_shot_prompt(
                        req.description,
                        openrouter_model,
                        req.system_name,
                        effective_auto_grading,
                        req.example_key,
                    )
            writer.flush()
            log_handler.flush()
            if not success:
                q.put(("error", "Generation failed before producing artifacts."))
                return

            model_short_name = (
                openrouter_model.split("/")[-1]
                if "/" in openrouter_model
                else openrouter_model
            )
            folder = _find_latest_run_folder(
                req.strategy,
                system_name=req.system_name,
                model_name=model_short_name,
                since=request_started_at,
            )
            if not folder:
                q.put(("error", "Generation finished without a fresh output folder."))
                return
            q.put(("complete", {"folder": folder}))
        except BaseException as exc:
            tb = traceback.format_exc().strip()
            if tb:
                for line in tb.splitlines():
                    if line.strip():
                        q.put(("progress", line))
            q.put(("error", str(exc)))
        finally:
            writer.flush()
            log_handler.flush()
            root_logger.removeHandler(log_handler)
            root_logger.setLevel(previous_root_level)
            q.put(None)  # sentinel

    threading.Thread(target=_run, daemon=True).start()

    def _stream():
        while True:
            try:
                item = q.get(timeout=60)
            except queue.Empty:
                yield "event: error\ndata: timeout\n\n"
                break
            if item is None:
                break
            event_type, payload = item
            data = json.dumps(payload) if isinstance(payload, dict) else payload
            yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Mermaid sandbox — render custom Mermaid code without LLM
# ---------------------------------------------------------------------------


class MermaidRequest(BaseModel):
    mermaid_code: str
    system_name: str = "CustomMermaid"


@app.post("/api/render-mermaid")
def render_mermaid(req: MermaidRequest):
    success, _ = process_custom_mermaid(
        req.mermaid_code,
        req.system_name,
        file_type="mermaid_compiler",
    )
    if not success:
        raise HTTPException(
            status_code=422,
            detail="Mermaid rendering failed. Check your diagram syntax.",
        )
    folder = _find_latest_run_folder("mermaid_compiler")
    if not folder:
        raise HTTPException(
            status_code=500, detail="Could not locate rendered output folder."
        )
    return {"folder": folder}


class AutomaticGraderRequest(BaseModel):
    mermaid_code: str
    example_key: str
    model: str = "anthropic:claude-4-5-sonnet"


@app.post("/api/automatic-grade")
def automatic_grade(req: AutomaticGraderRequest):
    system_prompt = getattr(sm_descriptions, req.example_key, None)
    if system_prompt is None:
        raise HTTPException(status_code=404, detail="Example not found")

    openrouter_model = PROFILE_TO_OPENROUTER.get(req.model, req.model)
    model_short_name = (
        openrouter_model.split("/")[-1] if "/" in openrouter_model else openrouter_model
    )
    backend_dir = BASE_DIR / "backend"
    paths = setup_file_paths(
        str(backend_dir),
        file_type="automatic_grader",
        system_name=req.example_key,
        model_name=model_short_name,
    )

    with open(paths["generated_mermaid_code_path"], "w") as f:
        f.write(req.mermaid_code.strip())

    run_automatic_grading(
        student_mermaid_code=req.mermaid_code.strip(),
        system_prompt=system_prompt,
        system_name=req.example_key,
        model=openrouter_model,
        paths=paths,
        base_dir=str(backend_dir),
        example_key=req.example_key,
    )

    folder = _find_latest_run_folder("automatic_grader")
    if not folder:
        raise HTTPException(
            status_code=500, detail="Could not locate grading output folder."
        )
    return {"folder": folder}
