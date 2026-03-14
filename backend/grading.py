import os
import re
import csv
import io
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


def _normalize_prompt_text(value: str) -> str:
    """Normalize prompt text for resilient matching across trim/whitespace edits."""
    return " ".join(value.split()).strip().lower()


def _resolve_example_key(system_prompt: str) -> Optional[str]:
    normalized_prompt = _normalize_prompt_text(system_prompt)

    for name in dir(sm_descriptions):
        if name.startswith("_"):
            continue
        value = getattr(sm_descriptions, name)
        if not isinstance(value, str):
            continue

        # Fast-path for exact string equality.
        if value == system_prompt:
            return name

        # Fallback for harmless formatting differences (trim/newline collapse).
        if _normalize_prompt_text(value) == normalized_prompt:
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


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _extract_csv_text_from_response(
    grading_response: str, expected_headers: list[str]
) -> str:
    """Extract CSV text from an LLM response, tolerating markdown fences and preamble."""
    # Prefer fenced CSV blocks if present.
    fenced_match = re.search(
        r"```(?:csv)?\s*(.*?)\s*```", grading_response, re.DOTALL | re.IGNORECASE
    )
    candidate = (
        fenced_match.group(1).strip() if fenced_match else grading_response.strip()
    )

    lines = candidate.splitlines()
    if not lines:
        return ""

    expected = [_normalize_header(h) for h in expected_headers if h is not None]
    if not expected:
        return candidate

    # If there is extra text before the table, keep content from the header line onward.
    for idx, line in enumerate(lines):
        normalized_cells = [_normalize_header(cell) for cell in line.split(",")]
        if len(normalized_cells) >= len(expected) and all(
            normalized_cells[i] == expected[i] for i in range(len(expected))
        ):
            return "\n".join(lines[idx:]).strip()

    return candidate


def _read_csv_rows(csv_text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = reader.fieldnames or []
    rows = [
        {key: (value if value is not None else "") for key, value in row.items()}
        for row in reader
    ]
    return fieldnames, rows


def _write_structured_grading_files(
    paths: dict, rows: list[dict[str, str]], fieldnames: list[str]
) -> None:

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


def _pick_column(fieldnames: list[str], keywords: tuple[str, ...]) -> Optional[str]:
    normalized = {name: _normalize_header(name) for name in fieldnames}
    for keyword in keywords:
        norm_keyword = _normalize_header(keyword)
        for original, norm_name in normalized.items():
            if norm_keyword in norm_name:
                return original
    return None


def _validate_completed_grading_rows(
    ground_truth_rows: list[dict[str, str]],
    completed_rows: list[dict[str, str]],
    fieldnames: list[str],
) -> tuple[bool, str]:
    if len(ground_truth_rows) != len(completed_rows):
        return (
            False,
            f"Row count mismatch: expected {len(ground_truth_rows)}, got {len(completed_rows)}",
        )

    score_col = _pick_column(fieldnames, ("grading", "rater"))
    notes_col = _pick_column(fieldnames, ("notes", "justification", "comment"))

    mutable_columns = {col for col in (score_col, notes_col) if col}
    immutable_columns = [col for col in fieldnames if col not in mutable_columns]

    for idx, (gt_row, llm_row) in enumerate(
        zip(ground_truth_rows, completed_rows), start=1
    ):
        for col in immutable_columns:
            if (gt_row.get(col, "") or "").strip() != (
                llm_row.get(col, "") or ""
            ).strip():
                return (
                    False,
                    f"Unexpected change in row {idx}, column '{col}'.",
                )

    return True, ""


def run_automatic_grading(
    student_mermaid_code: str,
    system_prompt: str,
    system_name: Optional[str],
    model: str,
    paths: dict,
    base_dir: str,
) -> Optional[str]:
    """Run automatic grading using ground-truth CSV and persist grading artifacts."""
    print("Running automatic grading")
    print("Evaluating generation against ground truth")

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
        max_tokens=15000,
        temperature=0.0,
        model=model,
    )

    if paths.get("grading_output_path"):
        with open(paths["grading_output_path"], "w") as f:
            f.write(grading_response)

    gt_fieldnames, gt_rows = _read_csv_rows(ground_truth_csv)
    response_csv_text = _extract_csv_text_from_response(grading_response, gt_fieldnames)
    response_fieldnames, response_rows = _read_csv_rows(response_csv_text)

    rows = response_rows
    fieldnames = response_fieldnames if response_fieldnames else gt_fieldnames

    fieldnames_match = [_normalize_header(h) for h in fieldnames] == [
        _normalize_header(h) for h in gt_fieldnames
    ]

    rows_are_valid = False
    validation_error = ""
    if fieldnames_match and rows:
        rows_are_valid, validation_error = _validate_completed_grading_rows(
            gt_rows, rows, gt_fieldnames
        )
    else:
        validation_error = "Header mismatch or no rows parsed from CSV response."

    if not rows_are_valid:
        rows = gt_rows
        fieldnames = gt_fieldnames
        if rows:
            notes_col = _pick_column(fieldnames, ("notes", "justification", "comment"))
            if notes_col:
                rows[0][
                    notes_col
                ] = f"Automatic grading response parse/validation failed: {validation_error}"
        _append_log(
            paths.get("llm_log_path"),
            "Structured grading export used fallback rows from ground truth CSV. "
            f"Reason: {validation_error}\n\n",
        )

    _write_structured_grading_files(paths, rows, fieldnames)

    _append_log(paths.get("llm_log_path"), "=== Automatic Grading Response ===\n")
    _append_log(paths.get("llm_log_path"), grading_response + "\n\n")

    print("Automatic grading completed")
    return grading_response
