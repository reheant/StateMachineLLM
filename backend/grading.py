import os
import re
import csv
import xml.etree.ElementTree as ET
from typing import Optional

try:
    from backend.resources.util import call_openrouter_llm
    from backend.resources.prompts.single_prompt.grading_prompt_template import (
        build_grading_prompt,
    )
    from backend.resources import state_machine_descriptions as sm_descriptions
except ImportError:
    from resources.util import call_openrouter_llm
    from resources.prompts.single_prompt.grading_prompt_template import (
        build_grading_prompt,
    )
    from resources import state_machine_descriptions as sm_descriptions


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _resolve_example_key(system_prompt: str) -> Optional[str]:
    for name in dir(sm_descriptions):
        if name.startswith("_"):
            continue
        value = getattr(sm_descriptions, name)
        if isinstance(value, str) and value == system_prompt:
            return name
    return None


def _resolve_ground_truth_csv_path(
    base_dir: str, system_prompt: str, system_name: Optional[str]
) -> str:
    ground_truth_dir = os.path.join(base_dir, "resources", "ground_truth_grading")

    preset_key = _resolve_example_key(system_prompt)
    if preset_key:
        return os.path.join(ground_truth_dir, f"{preset_key}.csv")

    if system_name:
        return os.path.join(ground_truth_dir, f"{_slugify(system_name)}.csv")

    return os.path.join(ground_truth_dir, "custom.csv")


def _csv_has_non_header_data(csv_text: str) -> bool:
    lines = [line.strip() for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return False

    # If there is only one line and it looks like a header, consider this empty.
    if len(lines) == 1 and lines[0].lower().startswith("type,"):
        return False

    return True


def _append_log(path: Optional[str], text: str) -> None:
    if not path:
        return
    with open(path, "a") as f:
        f.write(text)


def _extract_rows_from_grading_response(grading_response: str) -> list[dict[str, str]]:
    """Extract tabular grading rows from <grading_report> XML output."""
    rows: list[dict[str, str]] = []

    match = re.search(
        r"<grading_report>.*?</grading_report>", grading_response, re.DOTALL
    )
    if not match:
        return rows

    try:
        root = ET.fromstring(match.group(0))
    except ET.ParseError:
        return rows

    atomic_components = root.find("atomic_components")
    if atomic_components is not None:
        for item in atomic_components.findall("item"):
            rows.append(
                {
                    "section": "atomic_components",
                    "category_or_type": (item.findtext("type") or "").strip(),
                    "element": (item.findtext("element") or "").strip(),
                    "score": (item.findtext("score") or "").strip(),
                    "justification": (item.findtext("justification") or "").strip(),
                }
            )

    additional_elements = root.find("additional_elements")
    if additional_elements is not None:
        for item in additional_elements.findall("item"):
            rows.append(
                {
                    "section": "additional_elements",
                    "category_or_type": (item.findtext("category") or "").strip(),
                    "element": "",
                    "score": (item.findtext("score") or "").strip(),
                    "justification": (item.findtext("justification") or "").strip(),
                }
            )

    return rows


def _write_structured_grading_files(paths: dict, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "section",
        "category_or_type",
        "element",
        "score",
        "justification",
    ]

    csv_path = paths.get("grading_csv_path")
    tsv_path = paths.get("grading_tsv_path")

    if csv_path:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    if tsv_path:
        with open(tsv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)


def run_automatic_grading(
    student_mermaid_code: str,
    system_prompt: str,
    system_name: Optional[str],
    model: str,
    paths: dict,
    base_dir: str,
) -> Optional[str]:
    """Run automatic grading using ground-truth CSV and persist grading artifacts."""
    print("Running Automatic Grading")

    csv_path = _resolve_ground_truth_csv_path(base_dir, system_prompt, system_name)
    _append_log(paths.get("llm_log_path"), f"=== Grading CSV Path ===\n{csv_path}\n\n")

    if not os.path.exists(csv_path):
        message = (
            f"Automatic grading skipped: ground-truth CSV not found at {csv_path}.\n"
            "Create and fill this file to enable grading.\n\n"
        )
        _append_log(paths.get("llm_log_path"), message)
        if paths.get("grading_output_path"):
            with open(paths["grading_output_path"], "w") as f:
                f.write(message)
        print("Automatic grading skipped (missing CSV)")
        return None

    with open(csv_path, "r") as f:
        ground_truth_csv = f.read()

    run_ground_truth_path = os.path.join(
        paths.get("log_base_dir", base_dir), "ground_truth.csv"
    )
    with open(run_ground_truth_path, "w") as f:
        f.write(ground_truth_csv)

    if not _csv_has_non_header_data(ground_truth_csv):
        message = (
            f"Automatic grading skipped: ground-truth CSV is empty at {csv_path}.\n"
            "Paste the grading sheet rows, then re-run generation.\n\n"
        )
        _append_log(paths.get("llm_log_path"), message)
        if paths.get("grading_output_path"):
            with open(paths["grading_output_path"], "w") as f:
                f.write(message)
        print("Automatic grading skipped (empty CSV)")
        return None

    grading_prompt = build_grading_prompt(
        student_mermaid_code=student_mermaid_code,
        ground_truth_csv=ground_truth_csv,
        system_description=system_prompt,
    )

    if paths.get("grading_prompt_path"):
        with open(paths["grading_prompt_path"], "w") as f:
            f.write(grading_prompt)

    _append_log(paths.get("llm_log_path"), "=== Automatic Grading Prompt ===\n")
    _append_log(paths.get("llm_log_path"), grading_prompt + "\n\n")

    grading_response = call_openrouter_llm(
        grading_prompt,
        max_tokens=5000,
        temperature=0.0,
        model=model,
    )

    if paths.get("grading_output_path"):
        with open(paths["grading_output_path"], "w") as f:
            f.write(grading_response)

    rows = _extract_rows_from_grading_response(grading_response)
    if not rows:
        rows = [
            {
                "section": "raw_response",
                "category_or_type": "unparsed",
                "element": "",
                "score": "",
                "justification": grading_response.strip(),
            }
        ]
        _append_log(
            paths.get("llm_log_path"),
            "Structured grading export used fallback row: unable to parse <grading_report> XML.\n\n",
        )

    _write_structured_grading_files(paths, rows)

    _append_log(paths.get("llm_log_path"), "=== Automatic Grading Response ===\n")
    _append_log(paths.get("llm_log_path"), grading_response + "\n\n")

    print("Automatic grading completed")
    return grading_response
