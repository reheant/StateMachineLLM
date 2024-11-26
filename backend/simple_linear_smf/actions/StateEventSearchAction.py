from sherpa_ai.actions.base import BaseAction
from resources.util import call_llm
from resources.util import extract_states_events_table
import re
from resources.n_shot_examples import get_n_shot_examples

class StateEventSearchAction(BaseAction):
    name: str = "state_event_search_action"
    args: dict = {} # provided from the LLM
    usage: str = "Identify all states and their associated events that trigger transitions in the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")
        states_response_in_html = call_llm(f"""
            Given the problem description, identify what the states and events are and make sure not to include any redundant states or events by making sure that you parse the output for any states or events that might be redundant. Ensure that the states are defined specifically in the context of the object being modeled. It’s important to note that a complete state machine has an initial state and that states might have multiple events occurring on them resulting in multiple transitions from the current state to other states. 
            
            Output the name of the system in the following format:  
            System: "System Name" 
            
            Then produce the HTML table that summarizes the states and events MUST use these table headers:
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> </table> ```

            {get_n_shot_examples(["Printer", "Spa Manager"], ["system_description", "transitions_events_table"])}
            
            Example:
            
            System: 

            Problem Description:                           
            {self.belief.get("description")}

            Output:
        """)
        
        system_name = re.search(r"System:\s*\"(.*?)\"", states_response_in_html).group(1)

        state_events_table = extract_states_events_table(states_response_in_html)

        print(f"System name: {system_name}")
        print(f"State event table: {state_events_table}")
        return (system_name, state_events_table)
