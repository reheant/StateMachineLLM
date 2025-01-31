import re
import subprocess
import sys
import os
import time

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources'))

import graphviz
from resources.util import call_llm
from resources.state_machine_descriptions import *
from resources.n_shot_examples_single_prompt import get_n_shot_examples, n_shot_examples

# Default description if not ran with Chainlit
description = chess_clock_fall_2019

def run_single_prompt(system_prompt):
    """
    the run_event_driven_smf initiates the Simple Linear State Machine Framework
    """

    # Define the base directory for logs
    log_base_dir = os.path.join(os.path.dirname(__file__), "resources", "single_prompt_log")
    os.makedirs(log_base_dir, exist_ok=True)  # Ensure the directory exists

    # Construct the log file path
    file_prefix = f'output_single_prompt_{time.strftime("%Y_%m_%d_%H_%M_%S")}'
    log_file_name = f"{file_prefix}.txt"
    log_file_path = os.path.join(log_base_dir, log_file_name)
    generated_umple_code_path = os.path.join(log_base_dir, f"{file_prefix}.ump")
    umple_jar_path = os.path.join(os.path.dirname(__file__), "resources", 'umple.jar')

    # construct the diagram file path
    diagram_base_dir = os.path.join(os.path.dirname(__file__), "resources", "single_prompt_diagrams")
    os.makedirs(diagram_base_dir, exist_ok=True)  # Ensure the directory exists
    diagram_file_name = f"{file_prefix}"
    diagram_file_path = os.path.join(diagram_base_dir, diagram_file_name)

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
    
    for i in range(5):
        answer = call_llm(prompt)
        
        generated_umple_code_search = re.search(r"<umple_code_solution>(.*?)</umple_code_solution>", answer, re.DOTALL)

        if generated_umple_code_search:
            generated_umple_code = generated_umple_code_search.group(1)
        else:
            error = f"Attempt {i} at extracting umple code failed\n\n"
            with open(log_file_path, 'a') as file:
                file.write(error)
            print(error)
            continue
        
        print(f"Attempt {i} at extracting umple code successful\nGenerated umple code:")
        print(generated_umple_code)

        #Log the generated code
        with open(log_file_path, 'a') as file:
            file.write(generated_umple_code)

        #Create a file to store generated code
        with open(generated_umple_code_path, 'w') as file:
            file.write(generated_umple_code)
        
        try:
            result = subprocess.run(['java', '-jar', umple_jar_path, generated_umple_code_path, '-g', 'GvStateDiagram', '--path', log_base_dir], capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            error = f"Attempt {i} at processing umple code failed\n\n"
            with open(log_file_path, 'a') as file:
                file.write(error)
            print(error)

            with open(log_file_path, 'a') as file:
                file.write(f"{e.stderr}\n\n")
            print(f"{e.stderr}\n\n")
            continue
        
        print(f"Attempt {i} at processing umple code successful")

        with open(os.path.join(log_base_dir, f"{file_prefix}.gv"), 'r') as file:
            dot_code = file.read()

        # Render the DOT file using Graphviz
        graph = graphviz.Source(dot_code)
        graph.render(diagram_file_path, format='png')
        break


if __name__ == "__main__":
    run_single_prompt(description)