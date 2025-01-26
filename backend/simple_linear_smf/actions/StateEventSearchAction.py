from resources.SMFAction import SMFAction
from resources.util import call_llm
from resources.util import extract_states_events_table
import re
from resources.n_shot_examples_simple_linear import get_n_shot_examples

class StateEventSearchAction(SMFAction):
    """
    The StateEventSearchAction is the first step in the Linear SMF. It identifies
    states based on the events that occur in the system

    Input(s): description of system
    Output(s): name of the system, and an HTML table containing columns "Current State", "Event", and "Next State(s)"
    """
    
    name: str = "state_event_search_action"
    args: dict = {} # provided from the LLM
    usage: str = "Identify all states and their associated events that trigger transitions in the system"
    description: str = ""
    log_file_path: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to identify the states/events 
        using a 2-shot prompting approach
        """

        self.log(f"Running {self.name}...")
        n_shot_example_list = self.belief.get("n_shot_examples")

        prompt = f"""
            Given the problem description, identify what the states and events are and make sure not to include any redundant states or events by making sure that you parse the output for any states or events that might be redundant. Ensure that the states are defined specifically in the context of the object being modeled. It’s important to note that a complete state machine has an initial state and that states might have multiple events occurring on them resulting in multiple transitions from the current state to other states. 
            
            Output the name of the system in the following format:  
            <system_name>System Name</system_name> 
            
            Then produce the HTML table that summarizes the states and events MUST use these table headers:
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> </table> ```

            {get_n_shot_examples(n_shot_example_list, ["system_description", "transitions_events_table"])}
            
            Example:
            
            system_name: 

            system_description: {self.belief.get("description")}

            transitions_events_table:

            Your expertise in identifying system events is critical for defining the precise triggers that drive our state machine's behavior. Each event you recognize shapes how the system reacts to its environment and internal changes. Your systematic analysis of what truly constitutes a meaningful event will create a responsive and well-structured design. Take pride in knowing that your careful event identification lays the foundation for clear and predictable state transitions.
        """

        states_response_in_html = call_llm(prompt)

        system_name_search = re.search(r"<system_name>(.*?)</system_name>", states_response_in_html)

        if system_name_search:
            system_name = system_name_search.group(1)
        else:
            system_name = "NOT FOUND"
        self.log(system_name)
        
        # get the states and events table
        state_events_table = extract_states_events_table(states_response_in_html)

        self.log(f"System name: {system_name}")
        self.log(f"State event table: {state_events_table}")
        return (system_name, state_events_table)