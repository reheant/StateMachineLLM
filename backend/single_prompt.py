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
)
from resources.state_machine_descriptions import *
from resources.n_shot_examples_single_prompt import get_n_shot_examples, n_shot_examples

# Default description if not ran with Chainlit
description = chess_clock_fall_2019


def choose_openrouter_model():
    """Function to choose OpenRouter model for single prompt"""
    print("Choose an OpenRouter model for single prompt generation:")
    print("1. Qwen QwQ 32B (qwen/qwq-32b)")
    print("2. Qwen 2.5 72B Instruct (qwen/qwen-2.5-72b-instruct)")
    print("3. Claude 3.5 Sonnet (anthropic/claude-3.5-sonnet)")
    print("4. GPT-4o (openai/gpt-4o)")
    print("5. GPT-4o Mini (openai/gpt-4o-mini)")
    print("6. Llama 3.2 3B (meta-llama/llama-3.2-3b-instruct)")
    print("7. Gemini Pro 1.5 (google/gemini-pro-1.5)")

    model_map = {
        1: "qwen/qwq-32b",
        2: "qwen/qwen-2.5-72b-instruct",
        3: "anthropic/claude-3.5-sonnet",
        4: "openai/gpt-4o",
        5: "openai/gpt-4o-mini",
        6: "meta-llama/llama-3.2-3b-instruct",
        7: "google/gemini-pro-1.5",
    }

    while True:
        try:
            choice = int(input("Enter your choice (1-7): "))
            if choice in model_map:
                return model_map[choice]
            else:
                print("Invalid choice. Please enter 1-7.")
        except ValueError:
            print("Invalid input. Please enter a number (1-7).")


def run_single_prompt(system_prompt, model="anthropic/claude-3.5-sonnet"):
    """
    the run_single_prompt initiates the Single Prompt State Machine Framework
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

    prompt = f"""You are an AI assistant specialized in generating state machines using Umple syntax. Based on the problem description provided, your task is to:

	1.	Derive implicit knowledge from each sentence
	2.	Explain how you parse the problem description to extract states for state machine
	3.	Explain how you parse the problem description to extract transitions for the state machine
	4.	Explain how you parse the problem description to extract hierarchical states for the state machine
	5.	Explain how you parse the problem description to extract concurrent regions for the state machine
	6.	Explain how you parse the problem description to extract history states for the state machine
	7.	Assemble the state machine in umple code using information from steps 1. through 6. and encapsulate the code between brackets like the following: <umple_code_solution>code</umple_code_solution>

    Use Umple documentation as a guide and ensure the state machines generated comply with Umple syntax standards. Additionally, ensure that there are no warnings or errors generated from the Umple code you provide.

    The following are examples.

    {get_n_shot_examples(n_shot_examples_single_prompt, ["system_description", "umple_code_solution"])}

    Now your Problem Description: 
    {system_prompt}

    Provide your answer:

    """

    print(f"Using OpenRouter model: {model}")

    # Replace original loop with OpenRouter implementation:
    for i in range(5):
        if process_umple_attempt_openrouter(i, prompt, paths, model) != "False":
            break


def process_umple_attempt_openrouter(
    i: int, prompt: str, paths: dict, model: str = "anthropic/claude-3.5-sonnet"
) -> str:
    """
    Process a single attempt at generating and processing Umple code using OpenRouter
    Args:
        i: Attempt number
        prompt: LLM prompt
        paths: Dictionary containing file paths
        model: OpenRouter model to use
    Returns:
        str: Generated Umple code if successful, "False" otherwise
    """
    try:
        answer = call_openrouter_llm(
            prompt, max_tokens=1500, temperature=0.01, model=model
        )

        # Extract Umple code
        try:
            generated_umple_code = umpleCodeSearch(
                answer, paths["generated_umple_code_path"]
            )
        except Exception as e:
            error = f"Attempt {i} at extracting umple code failed\n\n"
            with open(paths["log_file_path"], "a") as file:
                file.write(error)
            print(error)
            return "False"

        print(f"Attempt {i} at extracting umple code successful\nGenerated umple code:")
        print(generated_umple_code)

        # Log generated code
        with open(paths["log_file_path"], "a") as file:
            file.write(generated_umple_code)

        # Process Umple code
        try:
            generated_umple_gv_path = umpleCodeProcessing(
                paths["umple_jar_path"],
                paths["generated_umple_code_path"],
                paths["log_base_dir"],
            )
        except subprocess.CalledProcessError as e:
            error = f"Attempt {i} at processing umple code failed\n\n"
            with open(paths["log_file_path"], "a") as file:
                file.write(error)
                file.write(f"{e.stderr}\n\n")
            print(error)
            print(f"{e.stderr}\n\n")
            return "False"

        print(f"Attempt {i} at processing umple code successful")

        # Generate GraphViz diagram
        graphVizGeneration(generated_umple_gv_path, paths["diagram_file_path"])
        return generated_umple_code

    except Exception as e:
        print(f"Unexpected error in attempt {i}: {str(e)}")
        return "False"


if __name__ == "__main__":
    # When run standalone, use interactive model selection
    selected_model = choose_openrouter_model()
    run_single_prompt(description, selected_model)
