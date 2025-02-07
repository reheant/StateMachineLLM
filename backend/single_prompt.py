import subprocess
import sys
import os
import time

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources'))

from resources.util import call_llm, setup_file_paths, process_umple_attempt, umpleCodeProcessing, umpleCodeSearch, graphVizGeneration
from resources.state_machine_descriptions import *
from resources.n_shot_examples_single_prompt import get_n_shot_examples, n_shot_examples

# Default description if not ran with Chainlit
description = chess_clock_fall_2019

def run_single_prompt(system_prompt):
    """
    the run_event_driven_smf initiates the Simple Linear State Machine Framework
    """
    # Setup file paths
    paths = setup_file_paths(os.path.dirname(__file__))
    
    # Prepare the list of example to provide to the LLM (N shot prompting)
    n_shot_examples_single_prompt = list(n_shot_examples.keys())[:4] # Extract all the examples available
    for n_shot_example in n_shot_examples_single_prompt:
        #Remove an example if it is identical to the one being analyzed by the SMF
        #Otherwise, if no examples are identical to the one being analyzed we remove
        #the last example to have a consistent number of examples used for all systems analyzed
        #(N-shot prompting with fixed N)
        if n_shot_examples[n_shot_example]["system_description"] == system_prompt \
        or n_shot_example == n_shot_examples_single_prompt[-1]:
            n_shot_examples_single_prompt.remove(n_shot_example)
            break

    prompt = f'''You are an AI assistant specialized in generating state machines using Umple syntax. Based on the problem description provided, your task is to:

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

    '''

    # Replace original loop with:
    for i in range(5):
        if process_umple_attempt(i, prompt, paths) != "False":
            break

if __name__ == "__main__":
    run_single_prompt(description)