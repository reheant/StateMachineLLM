import os
import re
import csv
import io
from typing import Optional
import sys

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "resources"))


from resources.util import call_openrouter_llm
from resources.prompts.single_prompt.grading_prompt_template import (
    build_grading_prompt,
)
from resources import state_machine_descriptions as sm_descriptions
from resources.n_shot_examples_single_prompt_mermaid import (
    get_example_mermaid_code,
)
from errors import (
    ErrorType,
    RunError,
    write_success,
    write_failure,
)

MAX_GRADING_ATTEMPTS = 3


def _run_single_grading_attempt(
    prompt: str,
    model: str,
    gt_fieldnames: list[str],
    gt_rows: list[dict[str, str]],
    paths: dict,
    attempt_idx: int,
) -> tuple[bool, list[dict[str, str]], list[str], str, str, dict]:
    """Execute one grading LLM call and parse its CSV response.

    Returns:
        (rows_are_valid, rows, fieldnames, validation_error, grading_response, error_details)
    """

    grading_response = call_openrouter_llm(
        prompt,
        max_tokens=8000,
        temperature=0.0,
        model=model,
    )

    if paths.get("grading_output_path"):
        with open(paths["grading_output_path"], "w") as f:
            f.write(grading_response)

    _append_log(
        paths.get("llm_log_path"),
        f"=== Automatic Grading Response (attempt {attempt_idx + 1}) ===\n",
    )
    _append_log(paths.get("llm_log_path"), grading_response + "\n\n")

    response_csv_text = _extract_csv_text_from_response(grading_response, gt_fieldnames)
    try:
        response_fieldnames, response_rows = _read_csv_rows(
            response_csv_text, expected_headers=gt_fieldnames
        )
    except Exception as exc:
        validation_error = f"Could not parse CSV output. Ensure the response is valid CSV only. Parser error: {exc}"
        _append_log(
            paths.get("llm_log_path"),
            f"CSV Parsing Failed (attempt {attempt_idx + 1}): {validation_error}\n",
        )
        error_details = {"parser_error": str(exc)}
        return (
            False,
            gt_rows,
            gt_fieldnames,
            validation_error,
            grading_response,
            error_details,
        )

    # Log CSV parsing details for debugging
    _append_log(
        paths.get("llm_log_path"),
        f"CSV Parsing: extracted {len(response_rows)} rows, {len(response_fieldnames or [])} fieldnames.\n",
    )
    _append_log(
        paths.get("llm_log_path"),
        f"Ground Truth: {len(gt_rows)} rows, {len(gt_fieldnames)} fieldnames.\n",
    )

    fieldnames = response_fieldnames if response_fieldnames else gt_fieldnames

    fieldnames_match = [_normalize_header(h) for h in fieldnames] == [
        _normalize_header(h) for h in gt_fieldnames
    ]

    rows_are_valid = False
    validation_error = ""
    error_details: dict = {}

    if fieldnames_match and response_rows:
        (
            rows_are_valid,
            validation_error,
            response_rows,
            was_reordered,
            error_details,
        ) = _validate_completed_grading_rows(gt_rows, response_rows, gt_fieldnames)
        if not rows_are_valid:
            _append_log(
                paths.get("llm_log_path"),
                f"CSV Validation Failed (attempt {attempt_idx + 1}): {validation_error}\n",
            )
        elif was_reordered:
            _append_log(
                paths.get("llm_log_path"),
                "Immutable columns were auto-repaired to match the ground-truth rubric.\n",
            )
    else:
        expected_header = ", ".join(gt_fieldnames)
        seen_header = ", ".join(response_fieldnames)
        validation_error = (
            "Header mismatch or no rows parsed from CSV response. "
            f"Expected header: [{expected_header}] but received: [{seen_header}]."
        )
        error_details = {
            "expected_header": gt_fieldnames,
            "received_header": list(response_fieldnames),
        }
        _append_log(
            paths.get("llm_log_path"),
            f"CSV Header/Content Check Failed (attempt {attempt_idx + 1}): {validation_error}\n",
        )

    rows = response_rows if rows_are_valid else gt_rows
    fieldnames = fieldnames if rows_are_valid else gt_fieldnames

    return (
        rows_are_valid,
        rows,
        fieldnames,
        validation_error,
        grading_response,
        error_details,
    )


def _resolve_ground_truth_csv_path(base_dir: str, example_key: str) -> str:
    ground_truth_dir = os.path.join(base_dir, "resources", "ground_truth_grading")

    return os.path.join(ground_truth_dir, f"{example_key}.csv")


def _csv_has_non_header_data(csv_text: str) -> bool:
    lines = [
        line.strip()
        for line in _sanitize_csv_text(csv_text).splitlines()
        if line.strip()
    ]
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


def _record_failure(paths: dict, message: str, exc: Optional[Exception] = None) -> None:
    """Persist an error message (and optional traceback) to logs and grading output."""
    trace = ""
    if exc:
        import traceback

        trace = "\n" + "".join(traceback.format_exception(exc)).strip()

    combined = message + trace + "\n"

    _append_log(paths.get("llm_log_path"), f"\n=== GRADING ERROR ===\n{combined}\n")

    grading_output_path = paths.get("grading_output_path")
    if grading_output_path:
        try:
            with open(grading_output_path, "w", encoding="utf-8") as f:
                f.write(combined)
        except OSError:
            pass


def _sanitize_csv_text(csv_text: str) -> str:
    """Strip fence markers, BOMs, and non-printable noise before parsing."""
    if not csv_text:
        return ""

    text = csv_text.replace("\ufeff", "")  # drop BOM
    text = text.replace("\r\n", "\n")

    # Remove stray markdown/code fences without removing the content itself.
    text = re.sub(r"^```.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"```", "", text)

    # Collapse excessive spacing but preserve newlines for CSV parsing.
    text = re.sub(r"[\t\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r" +", " ", text)

    return text.strip()


def _clean_cell_value(value: str) -> str:
    """Normalize cell values for reliable matching (case/spacing/quotes)."""
    cleaned = (value or "").strip().strip('"').strip("'")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower()


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

    candidate = _sanitize_csv_text(candidate)

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


def _read_csv_rows(
    csv_text: str, expected_headers: Optional[list[str]] = None
) -> tuple[list[str], list[dict[str, str]]]:
    """Read CSV text with proper handling of quotes and encoding."""

    sanitized = _sanitize_csv_text(csv_text)
    parse_errors: list[str] = []

    # Try common delimiters; prefer comma, but tolerate semicolon-heavy outputs.
    delimiters: list[str] = [","]
    if sanitized.count(";") > sanitized.count(","):
        delimiters.append(";")

    for delimiter in delimiters:
        try:
            reader = csv.DictReader(
                io.StringIO(sanitized),
                delimiter=delimiter,
                quoting=csv.QUOTE_MINIMAL,
                skipinitialspace=True,
            )
            fieldnames = reader.fieldnames or []
            rows: list[dict[str, str]] = []
            for row in reader:
                cleaned_row = {
                    key: (value if value is not None else "").strip()
                    for key, value in row.items()
                }

                # Drop trailing entirely-empty rows that LLMs sometimes emit.
                if all(not (v or "").strip() for v in cleaned_row.values()):
                    continue
                rows.append(cleaned_row)

            return fieldnames, rows
        except Exception as exc:  # Keep trying other delimiters before failing
            parse_errors.append(f"delimiter '{delimiter}': {exc}")
            continue

    raise ValueError("Failed to parse CSV response: " + "; ".join(parse_errors))


def _write_structured_grading_files(
    paths: dict, rows: list[dict[str, str]], fieldnames: list[str]
) -> None:
    """Write grading rows to CSV and TSV files with proper quoting and error handling."""
    csv_path = paths.get("grading_csv_path")
    tsv_path = paths.get("grading_tsv_path")

    if csv_path:
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    quoting=csv.QUOTE_MINIMAL,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(rows)
        except Exception as exc:
            raise IOError(f"Failed to write CSV to {csv_path}: {exc}") from exc

    if tsv_path:
        try:
            with open(tsv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter="\t",
                    quoting=csv.QUOTE_MINIMAL,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(rows)
        except Exception as exc:
            raise IOError(f"Failed to write TSV to {tsv_path}: {exc}") from exc


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
) -> tuple[bool, str, list[dict[str, str]], bool, dict]:
    """Validate LLM grading rows against the ground truth.

    Returns:
        (is_valid, error_message, rows, was_reordered, error_details)
    """
    error_details: dict = {}

    # --- Check row count ---
    if len(ground_truth_rows) != len(completed_rows):
        error_details = {
            "expected_rows": len(ground_truth_rows),
            "got_rows": len(completed_rows),
        }
        if len(completed_rows) > len(ground_truth_rows):
            error_details["issue"] = "extra_rows"
        else:
            error_details["issue"] = "missing_rows"
        return (
            False,
            f"Row count mismatch: expected {len(ground_truth_rows)}, got {len(completed_rows)}. "
            "Do not add or remove rows from the grading sheet.",
            completed_rows,
            False,
            error_details,
        )

    score_col = _pick_column(fieldnames, ("grading", "rater"))
    notes_col = _pick_column(fieldnames, ("notes", "justification", "comment"))

    mutable_columns = {col for col in (score_col, notes_col) if col}
    immutable_columns = [col for col in fieldnames if col not in mutable_columns]

    # --- Check for empty required grading fields ---
    empty_grading_rows = []
    for idx, row in enumerate(completed_rows):
        if score_col and not (row.get(score_col, "") or "").strip():
            row_label = _row_label(row, immutable_columns, idx)
            empty_grading_rows.append(row_label)
    if empty_grading_rows:
        error_details = {"empty_grading_rows": empty_grading_rows[:5]}
        return (
            False,
            f"Empty grading values in {len(empty_grading_rows)} row(s): "
            + ", ".join(empty_grading_rows[:5])
            + (
                f" (and {len(empty_grading_rows) - 5} more)"
                if len(empty_grading_rows) > 5
                else ""
            )
            + ". Every row must have a grading value.",
            completed_rows,
            False,
            error_details,
        )

    # --- Build row signatures for alignment ---
    def _row_signature(row: dict[str, str]) -> tuple[str, ...]:
        return tuple(_clean_cell_value(row.get(col, "")) for col in immutable_columns)

    # --- Positional verification: each row's immutable columns must match ground truth at the same index ---
    mismatched_rows: list[str] = []
    for idx, (gt_row, llm_row) in enumerate(zip(ground_truth_rows, completed_rows)):
        gt_sig = _row_signature(gt_row)
        llm_sig = _row_signature(llm_row)
        if gt_sig != llm_sig:
            label = _row_label(llm_row, immutable_columns, idx)
            expected_label = _row_label(gt_row, immutable_columns, idx)
            mismatched_rows.append(
                f"row {idx + 1} (expected {', '.join(gt_sig)} but got {', '.join(llm_sig)})"
            )

    was_repaired = False
    if mismatched_rows:
        # Auto-repair: if most rows already match positionally, the LLM likely
        # kept the correct order but mislabeled some Type/Element values.
        matching_count = len(ground_truth_rows) - len(mismatched_rows)
        repair_ratio = (
            matching_count / len(ground_truth_rows) if ground_truth_rows else 0
        )
        if repair_ratio >= 0.95:
            for gt_row, comp_row in zip(ground_truth_rows, completed_rows):
                for col in immutable_columns:
                    comp_row[col] = gt_row[col]
            was_repaired = True
        else:
            error_details = {"mismatched_rows": mismatched_rows[:5]}
            return (
                False,
                "Immutable columns (Type, Element) do not match ground truth at the "
                f"same row position. {', '.join(mismatched_rows[:5])}. "
                "Ensure immutable columns ("
                + ", ".join(immutable_columns)
                + ") stay identical and rows are not reordered, added, or removed.",
                completed_rows,
                False,
                error_details,
            )

    # --- Validate grading values ---
    invalid_scores = []
    for idx, row in enumerate(completed_rows, start=1):
        if not score_col:
            break
        score_raw = (row.get(score_col, "") or "").strip()
        if not score_raw:
            continue  # already checked above

        # Check element for "additional elements" rows
        element_col = _pick_column(fieldnames, ("element",))
        is_additional = False
        if element_col:
            is_additional = "additional elements" in _clean_cell_value(
                row.get(element_col, "")
            )

        if is_additional:
            try:
                val = int(score_raw)
                if val < 0:
                    invalid_scores.append(
                        f"Row {idx}: '{score_raw}' (additional elements must be >= 0)"
                    )
            except ValueError:
                invalid_scores.append(
                    f"Row {idx}: '{score_raw}' (additional elements must be an integer)"
                )
        else:
            if score_raw not in ("0", "0.5", "1"):
                invalid_scores.append(
                    f"Row {idx}: '{score_raw}' (must be 0, 0.5, or 1)"
                )

    if invalid_scores:
        error_details = {"invalid_scores": invalid_scores[:5]}
        return (
            False,
            "Invalid grading values: "
            + "; ".join(invalid_scores[:5])
            + (
                f" (and {len(invalid_scores) - 5} more)"
                if len(invalid_scores) > 5
                else ""
            ),
            completed_rows,
            False,
            error_details,
        )

    return True, "", completed_rows, was_repaired, {}


def _row_label(row: dict[str, str], immutable_columns: list[str], idx: int) -> str:
    """Build a short human-readable label for a row (for error messages)."""
    parts = []
    for col in immutable_columns[:2]:
        val = (row.get(col, "") or "").strip()
        if val:
            parts.append(val)
    if parts:
        return f"row {idx + 1} ({', '.join(parts)})"
    return f"row {idx + 1}"


def run_automatic_grading(
    student_mermaid_code: str,
    system_prompt: str,
    system_name: Optional[str],
    model: str,
    paths: dict,
    base_dir: str,
    example_key: str,
) -> Optional[str]:
    """Run automatic grading using ground-truth CSV and persist grading artifacts.

    Args:
        student_mermaid_code: The Mermaid code generated by the LLM.
        system_prompt: The system description/prompt used.
        system_name: Optional display name for the system.
        model: The model used for grading.
        paths: Dictionary of file paths for output artifacts.
        base_dir: Base directory for resolving relative paths.
        example_key: The preset example key (e.g., 'printer_winter_2017') or a slug name for custom systems.

    Returns:
        The raw grading response text on success.

    Raises:
        FileNotFoundError: Ground-truth CSV missing.
        ValueError: Ground-truth CSV empty.
        RuntimeError: All grading attempts failed validation.
    """
    print("Running automatic grading", flush=True)

    try:
        csv_path = _resolve_ground_truth_csv_path(base_dir, example_key)
        _append_log(
            paths.get("llm_log_path"), f"=== Grading CSV Path ===\n{csv_path}\n\n"
        )

        if not os.path.exists(csv_path):
            message = (
                f"Automatic grading failed: ground-truth CSV not found at {csv_path}.\n"
                "Create and fill this file to enable grading.\n\n"
            )
            _record_failure(paths, message)
            error = RunError(
                type=ErrorType.GRADING_VALIDATION,
                message="Ground-truth CSV not found.",
                details={"csv_path": csv_path},
            )
            write_failure(paths, error)
            print("Automatic grading failed (missing CSV)", flush=True)
            raise FileNotFoundError(message)

        with open(csv_path, "r") as f:
            ground_truth_csv = f.read()

        run_ground_truth_path = os.path.join(
            paths.get("log_base_dir", base_dir), "ground_truth.csv"
        )
        with open(run_ground_truth_path, "w") as f:
            f.write(ground_truth_csv)

        if not _csv_has_non_header_data(ground_truth_csv):
            message = (
                f"Automatic grading failed: ground-truth CSV is empty at {csv_path}.\n"
                "Paste the grading sheet rows, then re-run generation.\n\n"
            )
            _record_failure(paths, message)
            error = RunError(
                type=ErrorType.GRADING_VALIDATION,
                message="Ground-truth CSV is empty.",
                details={"csv_path": csv_path},
            )
            write_failure(paths, error)
            print("Automatic grading failed (empty CSV)", flush=True)
            raise ValueError(message)

        ground_truth_mermaid_code = (
            get_example_mermaid_code(example_key) if example_key else ""
        ) or ""

        grading_prompt = build_grading_prompt(
            student_mermaid_code=student_mermaid_code,
            ground_truth_csv=ground_truth_csv,
            ground_truth_mermaid_code=ground_truth_mermaid_code,
            system_description=system_prompt,
        )

        if paths.get("grading_prompt_path"):
            with open(paths["grading_prompt_path"], "w") as f:
                f.write(grading_prompt)

        _append_log(paths.get("llm_log_path"), "=== Automatic Grading Prompt ===\n")
        _append_log(paths.get("llm_log_path"), grading_prompt + "\n\n")

        print("Evaluating generation against ground truth", flush=True)

        gt_fieldnames, gt_rows = _read_csv_rows(ground_truth_csv)

        # Pre-compute immutable columns for retry prompts
        _score_col = _pick_column(gt_fieldnames, ("grading", "rater"))
        _notes_col = _pick_column(gt_fieldnames, ("notes", "justification", "comment"))
        _mutable_set = {col for col in (_score_col, _notes_col) if col}
        _immutable_cols = [col for col in gt_fieldnames if col not in _mutable_set]

        last_validation_error = ""
        last_error_details: dict = {}
        grading_response: Optional[str] = None
        retry_requirements = (
            "Use the exact header from the grading sheet, keep the same number and order of rows as the ground truth, "
            "do not add or remove rows, and only modify the grading and notes/justification columns. "
            "Every row must have a grading value filled in."
        )

        for attempt in range(MAX_GRADING_ATTEMPTS):
            if attempt == 0:
                effective_prompt = grading_prompt
            else:
                retry_hint = (
                    last_validation_error
                    or "CSV did not match required header or rows."
                )

                specific_guidance = ""
                if last_error_details.get("issue") in ("missing_rows", "extra_rows"):
                    row_list = []
                    for i, gt_row in enumerate(gt_rows, start=1):
                        vals = [gt_row.get(col, "") for col in _immutable_cols]
                        row_list.append(f"  Row {i}: {', '.join(vals)}")
                    specific_guidance = (
                        f"\nThe CSV must have exactly {len(gt_rows)} data rows (plus the header). "
                        f"Here are all {len(gt_rows)} rows with their exact Type and Element values "
                        "that you must preserve:\n" + "\n".join(row_list) + "\n\n"
                    )
                elif last_error_details.get("mismatched_rows"):
                    specific_guidance = (
                        "\nThe following rows had incorrect Type or Element values:\n"
                        + "\n".join(
                            f"  - {r}" for r in last_error_details["mismatched_rows"]
                        )
                        + "\nDo NOT modify the Type or Element columns. "
                        "Copy them exactly from the grading sheet.\n\n"
                    )

                effective_prompt = (
                    f"{grading_prompt}\n\n"
                    f"IMPORTANT: Your previous attempt (attempt {attempt}) was rejected because: {retry_hint}\n"
                    f"{specific_guidance}"
                    f"{retry_requirements}\n"
                    "Return a valid CSV only."
                )

            (
                rows_are_valid,
                rows,
                fieldnames,
                validation_error,
                grading_response,
                error_details,
            ) = _run_single_grading_attempt(
                effective_prompt,
                model,
                gt_fieldnames,
                gt_rows,
                paths,
                attempt,
            )

            if rows_are_valid:
                try:
                    _write_structured_grading_files(paths, rows, fieldnames)
                except IOError as write_exc:
                    _record_failure(
                        paths,
                        f"Failed to write CSV/TSV: {write_exc}",
                        write_exc,
                    )
                    error = RunError(
                        type=ErrorType.UNEXPECTED,
                        message=f"Failed to write grading files: {write_exc}",
                        attempts=attempt + 1,
                    )
                    write_failure(paths, error)
                    raise
                _append_log(
                    paths.get("llm_log_path"),
                    f"\n=== GRADING SUCCESS ===\nAutomatic grading completed successfully on attempt {attempt + 1}.\n",
                )
                write_success(paths)
                print("Automatic grading completed", flush=True)
                return grading_response

            last_validation_error = validation_error
            last_error_details = error_details
            _append_log(
                paths.get("llm_log_path"),
                f"\n--- Attempt {attempt + 1} Invalid ---\nValidation Error: {validation_error}\n",
            )
            if attempt < MAX_GRADING_ATTEMPTS - 1:
                _append_log(
                    paths.get("llm_log_path"),
                    f"Retrying with error feedback...\n",
                )

        # Fallback: persist ground truth with error note so the UI shows the failure.
        fallback_rows = gt_rows
        fallback_fieldnames = gt_fieldnames
        if fallback_rows:
            notes_col = _pick_column(
                fallback_fieldnames, ("notes", "justification", "comment")
            )
            if notes_col:
                fallback_rows[0][
                    notes_col
                ] = f"Automatic grading failed after retries: {last_validation_error}"

        try:
            _write_structured_grading_files(paths, fallback_rows, fallback_fieldnames)
        except IOError as write_exc:
            _record_failure(
                paths,
                f"Failed to write fallback CSV/TSV: {write_exc}",
                write_exc,
            )
            print(f"Warning: Failed to write fallback CSV: {write_exc}", flush=True)

        error_message = f"Automatic grading failed after {MAX_GRADING_ATTEMPTS} attempt(s): {last_validation_error}"
        _record_failure(paths, error_message)

        # Determine error type from the details
        error_type = ErrorType.GRADING_VALIDATION
        if last_error_details.get("parser_error"):
            error_type = ErrorType.GRADING_PARSE
        elif last_error_details.get("expected_header"):
            error_type = ErrorType.GRADING_SCHEMA

        error = RunError(
            type=error_type,
            message=error_message,
            details=last_error_details,
            attempts=MAX_GRADING_ATTEMPTS,
        )
        write_failure(paths, error)

        print(
            f"Automatic grading failed after retries: {last_validation_error}",
            flush=True,
        )
        raise RuntimeError(error_message)

    except (FileNotFoundError, ValueError, RuntimeError):
        # Already handled above — re-raise as-is.
        raise
    except Exception as exc:
        _record_failure(
            paths, f"Automatic grading encountered an unexpected error: {exc}", exc
        )
        error = RunError(
            type=ErrorType.UNEXPECTED,
            message=f"Automatic grading encountered an unexpected error: {exc}",
        )
        write_failure(paths, error)
        raise
