from resources.SMFAction import SMFAction
from resources.util import call_llm, umpleCodeProcessing, umpleCodeSearch, graphVizGeneration, setup_file_paths, process_umple_attempt
from resources.n_shot_examples_simple_linear import get_n_shot_examples
import re
import os

class AutomatedGenerationAction(SMFAction):
    """
    The AutomatedGenerationAction automatically generates umple code based on the input tables provided

    Input(s): A table of states, transitions, events, guards, actions, and history states, a hierarchal states table, and a parallel states table
    Output(s): Generated and compilable umple code that represents the system described in the input tables
    """

    name: str = "automated_generation_action"
    args: dict = {}
    usage: str = "Automatically generate the umple code from the HTML tables provided"
    description: str = ""
    log_file_path: str = ""
    
    def execute(self):
        """
        The execute function prompts the LLM to identify the transitions of the UML State Machine and their
        guards
        """

        self.log(f"Running {self.name}...")
        updated_hierarchical_state_table, updated_transitions_table, updated_parallel_state_table = self.belief.get('sanity_check_action')
        n_shot_example_list = self.belief.get("n_shot_examples")

        
        prompt = f"""

        You are an expert code generation assistant specializing in creating Umple state machine models from structured data. Your task is to analyze the provided state machine data and generate valid Umple code that accurately represents the system.

        First, carefully review the following input data:

        1. States, Transitions, Events, Guards, Actions, and History Table:
        <transitions_events_guards_actions_history_table>
        {updated_transitions_table}
        </transitions_events_guards_actions_history_table>

        2. Hierarchical State Table:
        <hierarchical_state_table>
        {updated_hierarchical_state_table}
        </hierarchical_state_table>

        3. Parallel States Table:
        <parallel_states_table>
        {updated_parallel_state_table}
        </parallel_states_table>

        Your objective is to generate correct Umple code that fully represents the system described in these input tables. Follow these steps:

        1. Analyze the input data:
        - Identify all states and categorize them as top-level or substates
        - List all events and categorize them by the state they are associated with
        - Analyze transitions, listing the source state, target state, and event for each
        - Explicitly identify and list all guards and actions for each transition
        - Outline the hierarchical relationship between states, including parent-child and sibling relationships
        - Identify any parallel regions and their constituent states

        2. Construct the Umple state machine structure:
        - Implement hierarchical states
        - Include parallel regions (if applicable)
        - Define transitions with events, optional guards, and action methods

        3. Generate the final Umple code

        After your analysis, present your final Umple code in <umple_code> tags. The code should be valid Umple syntax and fully represent the system described in the input tables.

        <umple_code>

        </umple_code>

        Before you begin, here's an example of how to approach a simple state machine analysis and code generation:

        {get_n_shot_examples(n_shot_example_list, [ "transitions_events_guards_actions_history_table", "hierarchical_state_table", "parallel_states_table", "generated_umple_code"])}
        
        Remember, the quality of your work is crucial. Take pride in your role and let your expertise shine through in your thoughtful analysis and precise code generation. Your ability to create accurate and efficient Umple code is invaluable to the software development process.

        Now, please proceed with your analysis and generation of the Umple code for the given system. Take your time to ensure accuracy and completeness in both your analysis and the generated code.


        """

        # Setup file paths
        paths = setup_file_paths(os.path.dirname(__file__))

       # Replace original loop with:
        for i in range(5):
            umple_code = process_umple_attempt(i, prompt, paths)
            if umple_code != "False":
                break
        

        return umple_code
