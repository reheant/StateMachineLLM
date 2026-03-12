import os
import sys

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


def run_two_shot_prompt(
    system_prompt, model="anthropic/claude-3.5-sonnet", system_name=None
):
    """
    Run the Two-Shot Prompt State Machine Framework.

    Shot 1: LLM generates an initial Mermaid diagram from the system description.
    Shot 2: LLM reviews its own output against known error patterns and produces
            a corrected version, which is then rendered.

    Args:
        system_prompt: The system description to generate a state machine for.
        model: The OpenRouter model to use.
        system_name: Optional name for the system (used for output folder organization).

    Returns:
        bool: True if the shot 2 diagram rendered successfully, False otherwise.
    """
    model_short_name = model.split("/")[-1] if "/" in model else model

    paths = setup_file_paths(
        os.path.dirname(__file__),
        file_type="two_shot_prompt",
        system_name=system_name,
        model_name=model_short_name,
    )

    # Prepare n-shot examples (same logic as single_prompt)
    n_shot_examples_list = list(n_shot_examples.keys())[:4]
    for n_shot_example in n_shot_examples_list:
        if (
            n_shot_examples[n_shot_example]["system_description"] == system_prompt
            or n_shot_example == n_shot_examples_list[-1]
        ):
            n_shot_examples_list.remove(n_shot_example)
            break

    first_prompt = build_single_prompt(
        mermaid_syntax=mermaid_syntax,
        n_shot_examples_str=get_n_shot_examples(
            n_shot_examples_list,
            ["system_description", "mermaid_code_solution"],
        ),
        system_prompt=system_prompt,
    )

    # Save shot 1 prompt so every run has a prompt artifact with the outputs.
    shot1_prompt_path = os.path.join(paths["log_base_dir"], "prompt_shot1.txt")
    with open(shot1_prompt_path, "w") as f:
        f.write(first_prompt)

    print(f"Running Two-Shot Prompt Generation with {model}")

    success = False
    max_attempts = 3

    for i in range(max_attempts):
        if i > 0:
            print(f"Retrying (attempt {i+1}/{max_attempts})...")

        result = process_two_shot_attempt(
            first_prompt, system_prompt, paths, model, attempt_index=i + 1
        )

        if result != "False":
            success = True
            break
        elif i < max_attempts - 1:
            print("Attempt failed, retrying...")
        else:
            print("All attempts failed")

    return success


def process_two_shot_attempt(
    first_prompt: str,
    system_prompt: str,
    paths: dict,
    model: str = "anthropic/claude-3.5-sonnet",
    attempt_index: int = 1,
) -> str:
    """
    Execute one full two-shot attempt: initial generation followed by refinement.

    Args:
        first_prompt: The fully assembled first-turn prompt (from build_single_prompt).
        paths: Dictionary of file paths from setup_file_paths.
        model: OpenRouter model identifier.

    Returns:
        str: The refined Mermaid code if the diagram rendered successfully,
             "False" otherwise.
    """
    try:
        # --- Shot 1: Initial generation ---
        print("Running Shot 1: Initial Mermaid generation")
        first_answer = call_openrouter_llm(
            first_prompt, max_tokens=6000, temperature=0.01, model=model
        )

        # Log raw response so extraction failures can be diagnosed
        with open(paths["log_file_path"], "a") as f:
            f.write(f"=== Shot 1 Raw LLM Response ===\n{first_answer}\n\n")

        try:
            shot1_mermaid = mermaidCodeSearch(
                first_answer,
                paths["generated_mermaid_code_path"],
                writeFile=False,
            )
        except Exception as e:
            error = "Shot 1: Failed to extract Mermaid code from LLM response"
            with open(paths["log_file_path"], "a") as f:
                f.write(f"{error}\nError: {str(e)}\n\n")
            print(f"{error}: {str(e)}")
            return "False"

        # Save shot 1 mermaid and render its diagram into a subfolder for comparison
        shot1_dir = os.path.join(paths["log_base_dir"], "shot1")
        os.makedirs(shot1_dir, exist_ok=True)

        shot1_mmd_path = os.path.join(shot1_dir, "output_shot1.mmd")
        with open(shot1_mmd_path, "w") as f:
            f.write(shot1_mermaid)

        # Render shot 1 — must succeed before proceeding to shot 2
        try:
            shot1_diagram_path = os.path.join(shot1_dir, "output_shot1")
            success = create_single_prompt_gsm_diagram_with_sherpa(
                shot1_mermaid, shot1_diagram_path
            )
            if not success:
                raise Exception("Shot 1 diagram rendering failed")
        except Exception as e:
            with open(paths["log_file_path"], "a") as f:
                f.write(f"Shot 1 rendering failed: {str(e)}\n\n")
            print(f"Shot 1 rendering failed: {str(e)}")
            return "False"

        with open(paths["log_file_path"], "a") as f:
            f.write(f"=== Shot 1 (Initial) ===\n{shot1_mermaid}\n\n")

        # --- Shot 2: Refinement ---
        print("Running Shot 2: Refinement")
        refinement_prompt = build_refinement_prompt(
            shot1_mermaid, system_prompt, mermaid_syntax
        )

        # Save shot 2 prompt separately for traceability across retries.
        shot2_prompt_path = os.path.join(
            paths["log_base_dir"], f"prompt_shot2_attempt_{attempt_index}.txt"
        )
        with open(shot2_prompt_path, "w") as f:
            f.write(refinement_prompt)

        with open(paths["log_file_path"], "a") as f:
            f.write(
                f"=== Shot 2 Refinement Prompt (sent to LLM) ===\n{refinement_prompt}\n\n"
            )

        second_answer = call_openrouter_llm(
            refinement_prompt, max_tokens=6000, temperature=0.3, model=model
        )

        with open(paths["log_file_path"], "a") as f:
            f.write(f"=== Shot 2 Raw LLM Response ===\n{second_answer}\n\n")

        try:
            shot2_mermaid = mermaidCodeSearch(
                second_answer, paths["generated_mermaid_code_path"]
            )
        except Exception as e:
            error = "Shot 2: Failed to extract Mermaid code from LLM response"
            with open(paths["log_file_path"], "a") as f:
                f.write(f"{error}\nError: {str(e)}\n\n")
            print(f"{error}: {str(e)}")
            return "False"

        with open(paths["log_file_path"], "a") as f:
            f.write(f"=== Shot 2 (Refined, Final) ===\n{shot2_mermaid}\n\n")

        # --- Render shot 2 ---
        try:
            success = create_single_prompt_gsm_diagram_with_sherpa(
                shot2_mermaid, paths["diagram_file_path"]
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
                        "mermaid_code": shot2_mermaid,
                    },
                    f,
                    indent=2,
                )

            with open(paths["log_file_path"], "a") as f:
                f.write(f"{error}\nError: {str(e)}\nTraceback:\n{full_traceback}\n\n")

            print(f"{error}: {str(e)}")
            return "False"

        return shot2_mermaid

    except Exception as e:
        import traceback

        full_traceback = traceback.format_exc()
        error_msg = f"Unexpected error in two-shot attempt: {str(e)}\n{full_traceback}"
        # Print to stderr so it reaches the terminal even when stdout is redirected
        print(error_msg, file=sys.stderr)
        print(error_msg)
        try:
            with open(paths["log_file_path"], "a") as f:
                f.write(f"=== UNEXPECTED ERROR ===\n{error_msg}\n\n")
        except Exception:
            pass
        return "False"
