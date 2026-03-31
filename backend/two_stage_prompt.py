import os
import sys
import logging

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "resources"))

from resources.util import (
    call_openrouter_llm,
    setup_file_paths,
    mermaidCodeSearch,
    create_single_prompt_gsm_diagram_with_sherpa,
)
from resources.prompts.single_prompt.custom_mermaid_syntax import mermaid_syntax
from resources.prompts.single_prompt.single_prompt_template import build_single_prompt
from resources.prompts.single_prompt.refinement_prompt_template import (
    build_refinement_prompt,
)
from resources.state_machine_descriptions import *
from resources.n_shot_examples_single_prompt_mermaid import (
    get_n_shot_examples,
    n_shot_examples,
)
from grading import run_automatic_grading
from errors import (
    ErrorType,
    RunError,
    write_success,
    write_failure,
    write_partial,
    write_in_progress,
)

logger = logging.getLogger(__name__)


def _make_attempt_error(kind: str, message: str, attempt: int) -> dict:
    return {"kind": kind, "message": message, "attempt": attempt}


def run_two_stage_prompt(
    system_prompt,
    model="anthropic/claude-3.5-sonnet",
    system_name=None,
    enable_auto_grading=True,
    example_key=None,
):
    """
    Run the Two-Stage Prompt State Machine Framework.

    Stage 1: LLM generates an initial Mermaid diagram from the system description.
    Stage 2: LLM reviews its own output against known error patterns and produces
             a corrected version, which is then rendered.

    Args:
        system_prompt: The system description to generate a state machine for.
        model: The OpenRouter model to use.
        system_name: Optional name for the system (used for output folder organization).
        enable_auto_grading: Whether automatic grading is executed after a successful run.
        example_key: Optional key identifying which preset example is being used (e.g., 'printer_winter_2017')

    Returns:
        bool: True if the stage 2 diagram rendered successfully, False otherwise.
    """
    if enable_auto_grading and not example_key:
        raise ValueError("example_key is required when automatic grading is enabled")

    model_short_name = model.split("/")[-1] if "/" in model else model

    paths = setup_file_paths(
        os.path.dirname(__file__),
        file_type="two_stage_prompt",
        system_name=system_name,
        model_name=model_short_name,
    )

    # Prepare n-shot examples (same logic as single_prompt)
    n_shot_examples_list = list(n_shot_examples.keys())
    found = False
    for n_shot_example in list(n_shot_examples_list):
        if n_shot_examples[n_shot_example]["system_description"] == system_prompt:
            n_shot_examples_list.remove(n_shot_example)
            found = True
            break
    if not found:
        n_shot_examples_list = n_shot_examples_list[
            1:
        ]  # skip first ("printer_winter_2017")

    n_shot_examples_msg = f"N-shot examples used: {', '.join(n_shot_examples_list)}"
    logger.info(n_shot_examples_msg)
    print(n_shot_examples_msg, flush=True)

    first_prompt = build_single_prompt(
        mermaid_syntax=mermaid_syntax,
        n_shot_examples_str=get_n_shot_examples(
            n_shot_examples_list,
            ["system_description", "mermaid_code_solution"],
        ),
        system_prompt=system_prompt,
    )

    print(f"Running Two-Stage Prompt Generation with {model}")

    write_in_progress(paths)

    success = False
    max_attempts = 3
    attempt_errors: list[dict] = []

    for i in range(max_attempts):
        if i > 0:
            print(f"Retrying (attempt {i+1}/{max_attempts})...")

        result, attempt_error = process_two_stage_attempt(
            first_prompt, system_prompt, paths, model, i
        )

        if result != "False":
            success = True
            if enable_auto_grading:
                try:
                    run_automatic_grading(
                        student_mermaid_code=result,
                        system_prompt=system_prompt,
                        system_name=system_name,
                        model=model,
                        paths=paths,
                        base_dir=os.path.dirname(__file__),
                        example_key=example_key,
                    )
                except Exception as e:
                    # Generation succeeded but grading failed — mark as partial.
                    print(f"Automatic grading failed: {str(e)}")
                    error = RunError(
                        type=ErrorType.GRADING_VALIDATION,
                        message=f"Automatic grading failed: {str(e)}",
                    )
                    write_partial(paths, error)
            else:
                print("Automatic grading disabled")
                write_success(paths)
            break
        else:
            if attempt_error:
                attempt_errors.append(attempt_error)
            if i < max_attempts - 1:
                print("Attempt failed, retrying...")
            else:
                print("All attempts failed")
                # Use the last attempt's error type if available.
                last_error_type = ErrorType.GENERATION
                if attempt_errors:
                    last_kind = attempt_errors[-1].get("kind", "")
                    if last_kind == "mermaid_compilation":
                        last_error_type = ErrorType.MERMAID_COMPILATION
                error = RunError(
                    type=last_error_type,
                    message="All generation attempts failed.",
                    details={"attempt_errors": attempt_errors},
                    attempts=max_attempts,
                )
                write_failure(paths, error)

    return success


def process_two_stage_attempt(
    first_prompt: str,
    system_prompt: str,
    paths: dict,
    model: str = "anthropic/claude-3.5-sonnet",
    attempt_index: int = 0,
) -> tuple[str, dict | None]:
    """
    Execute one full two-stage attempt: initial generation followed by refinement.

    Args:
        first_prompt: The fully assembled first-turn prompt (from build_single_prompt).
        system_prompt: The original system description.
        paths: Dictionary of file paths from setup_file_paths.
        model: OpenRouter model identifier.
        attempt_index: Zero-based attempt counter for error reporting.

    Returns:
        tuple: (mermaid_code, error_info)
            - mermaid_code: The refined Mermaid code if rendered successfully, "False" otherwise.
            - error_info: dict with 'kind' and 'message' on failure, None on success.
    """
    attempt_num = attempt_index + 1
    try:
        # --- Stage 1: Initial generation ---
        print("Running Stage 1: Initial Mermaid generation")
        try:
            first_answer = call_openrouter_llm(
                first_prompt, max_tokens=15000, temperature=0.01, model=model
            )
        except Exception as e:
            error_msg = f"Stage 1: LLM call failed: {str(e)}"
            print(error_msg)
            try:
                with open(paths["llm_log_path"], "a") as f:
                    f.write(f"{error_msg}\n\n")
            except Exception:
                pass
            return "False", _make_attempt_error("llm_call", error_msg, attempt_num)

        # Log raw response so extraction failures can be diagnosed
        with open(paths["llm_log_path"], "a") as f:
            f.write(f"=== Stage 1 Raw LLM Response ===\n{first_answer}\n\n")

        try:
            stage1_mermaid = mermaidCodeSearch(
                first_answer,
                paths["generated_mermaid_code_path"],
                writeFile=False,
            )
        except Exception as e:
            error = "Stage 1: Failed to extract Mermaid code from LLM response"
            with open(paths["llm_log_path"], "a") as f:
                f.write(f"{error}\nError: {str(e)}\n\n")
            print(f"{error}: {str(e)}")
            return "False", _make_attempt_error(
                "mermaid_extraction", f"{error}: {str(e)}", attempt_num
            )

        # Save stage 1 mermaid and render its diagram into a subfolder for comparison
        stage1_dir = os.path.join(paths["log_base_dir"], "stage1")
        os.makedirs(stage1_dir, exist_ok=True)

        stage1_mmd_path = os.path.join(stage1_dir, "output_stage1.mmd")
        with open(stage1_mmd_path, "w") as f:
            f.write(stage1_mermaid)

        stage1_txt_path = os.path.join(stage1_dir, "output_stage1.txt")
        with open(stage1_txt_path, "w") as f:
            f.write(stage1_mermaid)

        # Render stage 1 — must succeed before proceeding to stage 2
        try:
            stage1_diagram_path = os.path.join(stage1_dir, "output_stage1")
            success = create_single_prompt_gsm_diagram_with_sherpa(
                stage1_mermaid, stage1_diagram_path
            )
            if not success:
                raise Exception("Stage 1 diagram rendering failed")
        except Exception as e:
            with open(paths["llm_log_path"], "a") as f:
                f.write(f"Stage 1 rendering failed: {str(e)}\n\n")
            print(f"Stage 1 rendering failed: {str(e)}")
            return "False", _make_attempt_error(
                "mermaid_compilation",
                f"Stage 1 rendering failed: {str(e)}",
                attempt_num,
            )

        with open(paths["llm_log_path"], "a") as f:
            f.write(f"=== Stage 1 (Initial) ===\n{stage1_mermaid}\n\n")

        # --- Stage 2: Refinement ---
        print("Running Stage 2: Refinement")
        refinement_prompt = build_refinement_prompt(
            stage1_mermaid, system_prompt, mermaid_syntax
        )

        with open(paths["llm_log_path"], "a") as f:
            f.write(
                f"=== Stage 2 Refinement Prompt (sent to LLM) ===\n{refinement_prompt}\n\n"
            )

        try:
            second_answer = call_openrouter_llm(
                refinement_prompt, max_tokens=15000, temperature=0.3, model=model
            )
        except Exception as e:
            error_msg = f"Stage 2: LLM call failed: {str(e)}"
            print(error_msg)
            try:
                with open(paths["llm_log_path"], "a") as f:
                    f.write(f"{error_msg}\n\n")
            except Exception:
                pass
            return "False", _make_attempt_error("llm_call", error_msg, attempt_num)

        with open(paths["llm_log_path"], "a") as f:
            f.write(f"=== Stage 2 Raw LLM Response ===\n{second_answer}\n\n")

        try:
            stage2_mermaid = mermaidCodeSearch(
                second_answer, paths["generated_mermaid_code_path"]
            )
        except Exception as e:
            error = "Stage 2: Failed to extract Mermaid code from LLM response"
            with open(paths["llm_log_path"], "a") as f:
                f.write(f"{error}\nError: {str(e)}\n\n")
            print(f"{error}: {str(e)}")
            return "False", _make_attempt_error(
                "mermaid_extraction", f"{error}: {str(e)}", attempt_num
            )

        with open(paths["llm_log_path"], "a") as f:
            f.write(f"=== Stage 2 (Refined, Final) ===\n{stage2_mermaid}\n\n")

        # --- Render stage 2 ---
        try:
            success = create_single_prompt_gsm_diagram_with_sherpa(
                stage2_mermaid, paths["diagram_file_path"]
            )
            if not success:
                raise Exception("Diagram rendering failed")
        except Exception as e:
            import traceback
            import json

            error = "Failed to render diagram"
            full_traceback = traceback.format_exc()

            error_file = paths["diagram_file_path"] + "_error.json"
            with open(error_file, "w") as f:
                json.dump(
                    {
                        "error": str(e),
                        "traceback": full_traceback,
                        "mermaid_code": stage2_mermaid,
                    },
                    f,
                    indent=2,
                )

            with open(paths["llm_log_path"], "a") as f:
                f.write(f"{error}\nError: {str(e)}\nTraceback:\n{full_traceback}\n\n")

            print(f"{error}: {str(e)}")
            return "False", _make_attempt_error(
                "mermaid_compilation", f"{error}: {str(e)}", attempt_num
            )

        # Write the final Mermaid code in .txt form as well.
        with open(paths["log_file_path"], "w") as f:
            f.write(stage2_mermaid)

        final_txt_path = os.path.join(paths["log_base_dir"], "output_stage2.txt")
        with open(final_txt_path, "w") as f:
            f.write(stage2_mermaid)

        return stage2_mermaid, None

    except Exception as e:
        import traceback

        full_traceback = traceback.format_exc()
        error_msg = f"Unexpected error in two-stage attempt: {str(e)}\n{full_traceback}"
        # Print to stderr so it reaches the terminal even when stdout is redirected
        print(error_msg, file=sys.stderr)
        print(error_msg)
        try:
            with open(paths["llm_log_path"], "a") as f:
                f.write(f"=== UNEXPECTED ERROR ===\n{error_msg}\n\n")
        except Exception:
            pass
        return "False", _make_attempt_error(
            "unexpected", f"Unexpected error: {str(e)}", attempt_num
        )
