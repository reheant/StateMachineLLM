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


def run_single_prompt(system_prompt, model="anthropic/claude-3.5-sonnet"):
    """
    the run_single_prompt initiates the Single Prompt State Machine Framework
    Returns:
        bool: True if generation succeeded, False if all attempts failed
    """
    # Setup file paths
    paths = setup_file_paths(os.path.dirname(__file__))

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

    prompt = f"""You are an AI assistant specialized in generating state machines using Mermaid state diagram syntax. Based on the problem description provided, your task is to:

	1.	Derive implicit knowledge from each sentence
	2.	Explain how you parse the problem description to extract states for state machine
	3.	Explain how you parse the problem description to extract transitions for the state machine
	4.	Explain how you parse the problem description to extract hierarchical states for the state machine
	5.	Explain how you parse the problem description to extract concurrent regions for the state machine
	6.	Explain how you parse the problem description to extract history states for the state machine
	7.	Assemble the state machine in Mermaid syntax using information from steps 1. through 6. and encapsulate the code between brackets like the following: <mermaid_code_solution>code</mermaid_code_solution>

    IMPORTANT: Use Mermaid stateDiagram-v2 syntax with the following patterns:
    - Guards: event [condition]
    - Actions: event / action
    - Both: event [guard] / action
    - Parallel regions: Use -- separator
    - Hierarchical states: Use state Name {{ ... }} syntax ONLY for composite states (states with substates)
    - History states: When a transition should return to the last active substate of a composite state, use this pattern:
      1. The transition MUST go TO the composite state name (e.g., "Suspended --> Busy : resume")
      2. Add a note referencing the EXACT composite state name: "note right of Suspended\\n    resume returns to Busy history state\\nend note"
      3. IMPORTANT: The state name in the note MUST match an actual composite state (one with substates defined using "state Name {{ ... }}")
      4. Do NOT use generic terms like "operation", "task", or "previous" - use the actual state name
    - Entry/Exit actions: Use notes to specify entry/exit/do actions for states:
      ```
      note right of WashCycle
          entry / lockDoor
          exit / unlockDoor
      end note

      note right of Heating
          do / maintainTemperature
      end note
      ```
    - NEVER combine multiple composite states in a single note.
    - NEVER use phrasing like: "Print or Scan history state"
    History State Example (CORRECT pattern):
    ```
    state Busy {{
        [*] --> Processing
        state Processing
        Busy --> Paused : pause
    }}
    state Paused
    Paused --> Busy : resume
    note right of Paused
        resume returns to Busy history state
    end note
    ```
    In this example: "Busy" is a composite state (has substates), the transition goes TO "Busy", and the note references "Busy" exactly.

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
        
        result = process_umple_attempt_openrouter(i, prompt, paths, model)
        
        if result != "False":
            success = True
            break
        elif i < max_attempts - 1:
            print(f"Attempt failed, retrying...")
        else:
            print(f"All attempts failed")

    return success


def process_umple_attempt_openrouter(
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

        # Display generated Mermaid code
        print(f"\nGenerated Mermaid Code:\n```mermaid\n{generated_mermaid_code}\n```")
        print(f"\n📄 Mermaid saved: {paths['generated_mermaid_code_path']}")

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
                json.dump({
                    "error": str(e),
                    "traceback": full_traceback,
                    "mermaid_code": generated_mermaid_code
                }, f, indent=2)
            
            with open(paths["log_file_path"], "a") as file:
                file.write(f"{error}\nError: {str(e)}\nTraceback:\n{full_traceback}\n\n")
            
            print(f"{error}: {str(e)}")
            return "False"

        # Success - show where diagram was saved
        diagram_output = paths['diagram_file_path'] + ".png"
        print(f"🖼️  Diagram saved: {diagram_output}")

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

    paths = setup_file_paths(os.path.dirname(__file__))

    print("Running TEST: Entry/Exit Annotation Rendering")
    print("=" * 50)
    print("Test Mermaid Code:")
    print(test_mermaid)
    print("=" * 50)

    try:
        success = create_single_prompt_gsm_diagram_with_sherpa(
            test_mermaid,
            paths["diagram_file_path"]
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


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test-annotations":
        run_test_entry_exit_annotations()
    else:
        # When run standalone, use interactive model selection
        selected_model = choose_openrouter_model()
        run_single_prompt(description, selected_model)
