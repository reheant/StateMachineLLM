import subprocess
import sys
import os
import time

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "resources"))

from resources.util import (
    call_llm,
    call_openrouter_llm,
    setup_file_paths,
    process_umple_attempt,
    umpleCodeProcessing,
    umpleCodeSearch,
    graphVizGeneration,
    mermaidCodeSearch,
    mermaidDiagramGeneration,
    create_single_prompt_gsm_diagram_with_sherpa,
)
from resources.state_machine_descriptions import *
from resources.n_shot_examples_single_prompt_mermaid import (
    get_n_shot_examples,
    n_shot_examples,
)

# Default description if not ran with Chainlit
description = chess_clock_fall_2019


def choose_openrouter_model():
    """Function to choose OpenRouter model for single prompt"""
    print("Choose an OpenRouter model for single prompt generation:")
    print("\n=== Anthropic ===")
    print("1. Claude 3.5 Sonnet (anthropic/claude-3.5-sonnet)")
    print("2. Claude 4.5 Sonnet (anthropic/claude-4.5-sonnet)")
    print("3. Claude Sonnet 4 (anthropic/claude-sonnet-4)")
    print("\n=== OpenAI ===")
    print("4. GPT-4o (openai/gpt-4o)")
    print("5. GPT-4o Mini (openai/gpt-4o-mini)")
    print("6. GPT-4 Turbo (openai/gpt-4-turbo)")
    print("7. o1 (openai/o1)")
    print("8. o1-mini (openai/o1-mini)")
    print("\n=== Google ===")
    print("9. Gemini 2.0 Flash (google/gemini-2.0-flash-exp)")
    print("10. Gemini 1.5 Pro (google/gemini-pro-1.5)")
    print("11. Gemini 1.5 Flash (google/gemini-flash-1.5)")
    print("\n=== Meta ===")
    print("12. Llama 3.3 70B (meta-llama/llama-3.3-70b-instruct)")
    print("13. Llama 3.1 405B (meta-llama/llama-3.1-405b-instruct)")
    print("14. Llama 3.1 70B (meta-llama/llama-3.1-70b-instruct)")
    print("15. Llama 3.2 3B (meta-llama/llama-3.2-3b-instruct)")
    print("\n=== Qwen ===")
    print("16. Qwen QwQ 32B (qwen/qwq-32b)")
    print("17. Qwen 2.5 72B (qwen/qwen-2.5-72b-instruct)")

    model_map = {
        1: "anthropic/claude-3.5-sonnet",
        2: "anthropic/claude-4.5-sonnet",
        3: "anthropic/claude-sonnet-4",
        4: "openai/gpt-4o",
        5: "openai/gpt-4o-mini",
        6: "openai/gpt-4-turbo",
        7: "openai/o1",
        8: "openai/o1-mini",
        9: "google/gemini-2.0-flash-exp",
        10: "google/gemini-pro-1.5",
        11: "google/gemini-flash-1.5",
        12: "meta-llama/llama-3.3-70b-instruct",
        13: "meta-llama/llama-3.1-405b-instruct",
        14: "meta-llama/llama-3.1-70b-instruct",
        15: "meta-llama/llama-3.2-3b-instruct",
        16: "qwen/qwq-32b",
        17: "qwen/qwen-2.5-72b-instruct",
    }

    while True:
        try:
            choice = int(input("Enter your choice (1-17): "))
            if choice in model_map:
                return model_map[choice]
            else:
                print("Invalid choice. Please enter 1-17.")
        except ValueError:
            print("Invalid input. Please enter a number (1-17).")


def run_single_prompt(
    system_prompt, model="anthropic/claude-3.5-sonnet", system_name=None
):
    """
    the run_single_prompt initiates the Single Prompt State Machine Framework
    Args:
        system_prompt: The system description to generate a state machine for
        model: The OpenRouter model to use
        system_name: Optional name for the system (used for organizing output folders)
    Returns:
        bool: True if generation succeeded, False if all attempts failed
    """
    # Extract short model name for folder (e.g., "anthropic/claude-3.5-sonnet" -> "claude-3.5-sonnet")
    model_short_name = model.split("/")[-1] if "/" in model else model

    # Setup file paths with optional system name and model name for folder organization
    paths = setup_file_paths(
        os.path.dirname(__file__), system_name=system_name, model_name=model_short_name
    )

    # Prepare the list of example to provide to the LLM (N shot prompting)
    n_shot_examples_single_prompt = list(n_shot_examples.keys())[
        :4
    ]  # Extract all the examples available
    for n_shot_example in n_shot_examples_single_prompt:
        # Remove an example if it is identical to the one being analyzed by the SMF
        # Otherwise, if no examples are identical to the one being analyzed we remove
        # the last example to have a consistent number of examples used for all systems analyzed
        # (N-shot prompting with fixed N)
        if (
            n_shot_examples[n_shot_example]["system_description"] == system_prompt
            or n_shot_example == n_shot_examples_single_prompt[-1]
        ):
            n_shot_examples_single_prompt.remove(n_shot_example)
            break

    prompt = f"""You are an AI assistant specialized in generating state machines using a Custom Mermaid state diagram syntax. Based on the problem description provided, your task is to:

	1.	Derive implicit knowledge from each sentence
	2.	Explain how you parse the problem description to extract states for state machine
	3.	Explain how you parse the problem description to extract transitions for the state machine
	4.	Explain how you parse the problem description to extract hierarchical states for the state machine
	5.	Explain how you parse the problem description to extract concurrent regions for the state machine
	6.	Explain how you parse the problem description to extract history states for the state machine
	7.	Assemble the state machine in Mermaid syntax using information from steps 1. through 6. and encapsulate the code between brackets like the following: <mermaid_code_solution>code</mermaid_code_solution>

    IMPORTANT: Use Mermaid syntax with the following patterns:
    - State declaration: States must be explicitly declared using `state StateName`.
    - Initial state rule: The initial transition must use the pattern `[*] --> StateName`, and `StateName` must be declared as a state before it is referenced.

    Example (valid):
        stateDiagram-v2
        state Off
        state On
        [*] --> Off
        Off --> On : powerOn
        On --> Off : powerOff

    Example (invalid):
        stateDiagram-v2
        [*] --> Off
        state On
        Off --> On : powerOn
        On --> Off : powerOff
    - Guards: event [condition]
    - Actions: event / action
    - Both: event [guard] / action
    - Parallel regions: Use -- separator
    - Hierarchical/Composite states: Use state Name {{ ... }} syntax ONLY for composite states (states with substates)
    - History states: Declare history states explicitly as named states inside a composite state (e.g., HistoryState1).
        History States Guidance :
            - Purpose: record the last active substate in a composite state so upon re-entry in that composite state, the state machine can automatically resume that substate instead of the initial substate.
            - Declaration: always declare history states inside the composite state's block with a unique name.
            - Usage: reference history states only for re-entry transitions, e.g. `CompositeState --> HistoryStateName : reenter / resumeAction` or `Outside --> HistoryStateName : reenter`.
            - Transition rules (strict):
                * A history state must be declared inside the composite state we wish to keep track of, so that, upon re-entry, the machine can resume automatically from the last active substate.
                * A history state may only be targeted by transitions originating from outside its composite state or from the composite state itself.
                * Substates inside the same composite must never transition directly to the history state.
                * History states are exclusively for external re-entry behavior, not for internal navigation or state flow.
                - Examples:
                    - Valid (composite -> history):
                      
                        stateDiagram-v2
                        [*] --> Outside
                        state Outside
                        state Composite
                        state Composite {{
                            state A
                            state B
                            state HistoryState1
                            [*] --> A
                            A --> B : toB
                           

                        }}
                        Composite --> HistoryState1 : reenter / resumeAction
                        Outside --> Composite : enter
                    - Valid (external state -> history):
                      
                        stateDiagram-v2
                        [*] --> Outside
                        state Outside
                        state Composite
                        state Composite {{
                            state A
                            state B
                            state HistoryState1
                            [*] --> A
                            A --> B : toB
                           

                        }}
                        Outside --> HistoryState1 : reenter
                        Outside --> Composite : enter

                    - Invalid (substate -> history):
                        stateDiagram-v2
                        [*] --> Outside
                        Outside --> Composite : enter
                        state Composite {{
                            state A
                            state HistoryState1
                            [*] --> A
                            A --> HistoryState1 : illegal / bad
                        }}
    - Entry/Exit/Do actions: When a state has entry, exit, or do actions, use a `note right of` block.
      These notes will be displayed as annotations at the bottom of the generated diagram.

      Syntax for entry/exit/do actions:
        note right of StateName
            entry / actionOnEntry()
            exit / actionOnExit()
            do: ongoingAction()
        end note

      Example:
        state WashCycle {{
            [*] --> WaterIntake
            WaterIntake --> Washing : tankFull
        }}

        note right of WashCycle
            entry / lockDoor()
            exit / unlockDoor()
        end note

      Rules:
        - Use `entry / action` for actions that execute when ENTERING the state
        - Use `exit / action` for actions that execute when LEAVING the state
        - Use `do: action` for ongoing activities that execute WHILE in the state
        - Each action should be on its own line inside the note block
        - The note block must end with `end note`
        - Place the note block AFTER the state declaration (outside the state's curly braces if composite)
        - You can have entry, exit, and do on the same state — put them all in one note block

    The following are examples demonstrating proper Mermaid syntax:

    {get_n_shot_examples(n_shot_examples_single_prompt, ["system_description", "mermaid_code_solution"])}

    Now your Problem Description:
    {system_prompt}

    Provide your answer following the exact Mermaid syntax patterns shown in the examples:

    """

    print(f"Running Single Prompt Generation with {model}")

    success = False
    max_attempts = 3

    for i in range(max_attempts):
        if i > 0:
            print(f"Retrying (attempt {i+1}/{max_attempts})...")

        result = process_mermaid_attempt_openrouter(i, prompt, paths, model)

        if result != "False":
            success = True
            break
        elif i < max_attempts - 1:
            print(f"Attempt failed, retrying...")
        else:
            print(f"All attempts failed")

    return success


def process_mermaid_attempt_openrouter(
    i: int, prompt: str, paths: dict, model: str = "anthropic/claude-3.5-sonnet"
) -> str:
    """
    Process a single attempt at generating and processing Mermaid code using OpenRouter
    Args:
        i: Attempt number
        prompt: LLM prompt
        paths: Dictionary containing file paths
        model: OpenRouter model to use
    Returns:
        str: Generated Mermaid code if successful, "False" otherwise
    """
    try:
        # Call LLM
        answer = call_openrouter_llm(
            prompt, max_tokens=5000, temperature=0.01, model=model
        )

        # Extract Mermaid code
        try:
            generated_mermaid_code = mermaidCodeSearch(
                answer, paths["generated_mermaid_code_path"]
            )
        except Exception as e:
            error = f"Failed to extract mermaid code from LLM response"
            with open(paths["log_file_path"], "a") as file:
                file.write(f"{error}\nError: {str(e)}\n\n")
            print(f"{error}: {str(e)}")
            return "False"

        # Log generated code
        with open(paths["log_file_path"], "a") as file:
            file.write(generated_mermaid_code)
            file.write("\n\n")

        # Render diagram
        try:
            success = create_single_prompt_gsm_diagram_with_sherpa(
                generated_mermaid_code, paths["diagram_file_path"]
            )
            if not success:
                raise Exception("Diagram rendering failed")
        except Exception as e:
            import traceback
            import json

            error = f"Failed to render diagram"
            full_traceback = traceback.format_exc()

            # Save error to file
            error_file = paths["diagram_file_path"] + "_error.json"
            with open(error_file, "w") as f:
                json.dump(
                    {
                        "error": str(e),
                        "traceback": full_traceback,
                        "mermaid_code": generated_mermaid_code,
                    },
                    f,
                    indent=2,
                )

            with open(paths["log_file_path"], "a") as file:
                file.write(
                    f"{error}\nError: {str(e)}\nTraceback:\n{full_traceback}\n\n"
                )

            print(f"{error}: {str(e)}")
            return "False"

        # Success
        return generated_mermaid_code

    except Exception as e:
        print(f"Unexpected error in attempt {i}: {str(e)}")
        return "False"


def run_test_entry_exit_annotations():
    """
    [DEV TEST] Verify entry/exit annotation rendering.

    Bypasses LLM and uses hardcoded mermaid with entry/exit notes.
    Tests that notes containing "entry / action" or "exit / action"
    are parsed and displayed as annotations at the bottom of the diagram.

    Expected output annotations:
    - WashCycle.entry: lockDoor
    - WashCycle.exit: unlockDoor
    - Drying.entry: setDryingTime

    Returns:
        bool: True if test passed, False otherwise
    """
    # Hardcoded mermaid with entry/exit notes (like the dishwasher example)
    test_mermaid = """stateDiagram-v2
    [*] --> Idle

    Idle --> ProgramSelection : selectProgram
    ProgramSelection --> ProgramSelection : adjustDryingTime
    ProgramSelection --> WashCycle : start [doorClosed]

    state WashCycle {
        [*] --> WaterIntake
        WaterIntake --> Washing : tankFull
        Washing --> Draining : after(10min)
        Draining --> WaterIntake : [cyclesRemaining]
        Draining --> Drying : [cyclesComplete]
    }

    state Drying {
        [*] --> DryingActive
        DryingActive --> DryingActive : adjustDryingTime [time < 40min]
    }

    Drying --> DryingSuspended : doorOpen
    DryingSuspended --> Drying : doorClose [timeOpen < 5min]
    DryingSuspended --> Complete : [timeOpen >= 5min]
    Drying --> Complete : dryingComplete

    note right of DryingSuspended
        doorClose returns to Drying history state
    end note

    Complete --> Idle : doorOpen

    note right of WashCycle
        entry / lockDoor
        exit / unlockDoor
    end note

    note right of Drying
        entry / setDryingTime
    end note
"""

    paths = setup_file_paths(
        os.path.dirname(__file__),
        system_name="DevTest_EntryExit",
        model_name="dev-test",
    )

    print("Running TEST: Entry/Exit Annotation Rendering")
    print("=" * 50)
    print("Test Mermaid Code:")
    print(test_mermaid)
    print("=" * 50)

    try:
        success = create_single_prompt_gsm_diagram_with_sherpa(
            test_mermaid, paths["diagram_file_path"]
        )
        if success:
            print(f"TEST PASSED: Diagram saved to {paths['diagram_file_path']}.png")
            return True
        else:
            print("TEST FAILED: Rendering returned False")
            return False
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def process_custom_mermaid(mermaid_code, system_name="CustomMermaid"):
    """
    Process user-provided Mermaid code (bypasses LLM).

    Treats the input as if it were LLM output and runs it through
    the same parsing/rendering pipeline as single_prompt.

    Args:
        mermaid_code: User-provided Mermaid state diagram code
        system_name: Name for file organization (default: "CustomMermaid")

    Returns:
        tuple: (success: bool, diagram_path: str or None)
            - success: True if processing succeeded
            - diagram_path: Full path to the generated PNG diagram, or None if failed
    """
    import re

    # Clean up common UI artifacts
    cleaned_code = mermaid_code
    cleaned_code = cleaned_code.replace("Raw code", "")
    cleaned_code = cleaned_code.strip("'\"")
    cleaned_code = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_code)

    paths = setup_file_paths(
        os.path.dirname(__file__),
        system_name=system_name,
        model_name="custom-input",
    )

    print("Processing Custom Mermaid Code")
    print("=" * 50)

    try:
        # Save the Mermaid code
        with open(paths["generated_mermaid_code_path"], "w") as file:
            file.write(cleaned_code)

        print(f"📄 Mermaid saved: {paths['generated_mermaid_code_path']}")

        # Render diagram using the same function as single_prompt
        success = create_single_prompt_gsm_diagram_with_sherpa(
            cleaned_code, paths["diagram_file_path"]
        )

        if success:
            diagram_output = paths["diagram_file_path"] + ".png"
            print(f"🖼️  Diagram saved: {diagram_output}")
            return (True, diagram_output)
        else:
            print("Rendering returned False")
            return (False, None)

    except Exception as e:
        print(f"Error processing custom Mermaid: {str(e)}")
        import traceback

        traceback.print_exc()
        return (False, None)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test-annotations":
        run_test_entry_exit_annotations()
    else:
        # When run standalone, use interactive model selection
        selected_model = choose_openrouter_model()
        # Use "Standalone" as system name when run directly
        run_single_prompt(description, selected_model, system_name="Standalone")
