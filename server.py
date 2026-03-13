"""
Sherpa — FastAPI backend
Replaces `chainlit run app.py` with `uvicorn server:app --reload --port 8000`
"""

import asyncio
import contextlib
import io
import json
import os
import queue
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import backend.resources.state_machine_descriptions as sm_descriptions
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

EXAMPLES = [
    (
        "printer_winter_2017",
        "🖨️",
        "Printer System",
        "office printer with card authentication, print/scan, and error handling",
    ),
    (
        "spa_manager_winter_2018",
        "🧖",
        "Spa Manager",
        "sauna & Jacuzzi control with temperature regulation and water jets",
    ),
    (
        "dishwasher_winter_2019",
        "✨",
        "Smart Dishwasher",
        "automated dishwasher with multiple programs, drying, and door safety",
    ),
    (
        "chess_clock_fall_2019",
        "🕰️",
        "Digital Chess Clock",
        "tournament chess clock with multiple timing modes and player controls",
    ),
    (
        "automatic_bread_maker_fall_2020",
        "🥖",
        "Automatic Bread Maker",
        "programmable bread maker with crust options and delayed start",
    ),
    (
        "thermomix_fall_2021",
        "🔪",
        "Thermomix TM6",
        "guided recipe steps and ingredient processing",
    ),
    (
        "ATAS_fall_2022",
        "🚆",
        "Train Automation System",
        "driverless trains across a rail network with signals and stations",
    ),
    (
        "WUMPLE_fall_2023_Version_A",
        "⌚",
        "Wumple Watch",
        "timekeeping, alarm, and countdown modes with backlight and flash alerts",
    ),
    (
        "SSC7_fall_2024_Version_A",
        "🛒",
        "SSC7 Self-Checkout",
        "supermarket self-checkout with scanning, weighing, payment, and staff override",
    ),
]

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
    for strategy in ("single_prompt", "two_shot_prompt"):
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


def _find_latest_run_folder(strategy: str) -> str | None:
    """After generation, find the most-recently modified run folder."""
    outputs_dir = RESOURCES_DIR / f"{strategy}_outputs"
    latest_path: Path | None = None
    latest_mtime = 0.0
    for png in outputs_dir.rglob("*.png"):
        mtime = png.stat().st_mtime
        if mtime > latest_mtime:
            latest_mtime = mtime
            latest_path = png.parent
    return str(latest_path) if latest_path else None


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.get("/api/examples")
def get_examples():
    return [
        {"key": k, "icon": icon, "label": label, "blurb": blurb}
        for k, icon, label, blurb in EXAMPLES
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
    enable_auto_grading: bool = True


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


@app.post("/api/generate")
def generate(req: GenerateRequest):
    openrouter_model = PROFILE_TO_OPENROUTER.get(req.model, req.model)
    q: queue.Queue = queue.Queue()

    def _run():
        writer = _QueueWriter(q)
        try:
            with contextlib.redirect_stdout(writer):  # type: ignore[arg-type]
                if req.strategy == "single_prompt":
                    run_single_prompt(
                        req.description,
                        openrouter_model,
                        req.system_name,
                        req.enable_auto_grading,
                    )
                else:
                    run_two_shot_prompt(
                        req.description,
                        openrouter_model,
                        req.system_name,
                        req.enable_auto_grading,
                    )
            writer.flush()
            folder = _find_latest_run_folder(req.strategy)
            q.put(("complete", {"folder": folder}))
        except Exception as exc:
            q.put(("error", str(exc)))
        finally:
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
    success, _ = process_custom_mermaid(req.mermaid_code, req.system_name)
    if not success:
        raise HTTPException(
            status_code=422,
            detail="Mermaid rendering failed. Check your diagram syntax.",
        )
    folder = _find_latest_run_folder("single_prompt")
    if not folder:
        raise HTTPException(
            status_code=500, detail="Could not locate rendered output folder."
        )
    return {"folder": folder}
