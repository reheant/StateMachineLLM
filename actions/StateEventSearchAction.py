from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_states_events_table
import re

class StateEventSearchAction(BaseAction):
    name: str = "state_event_search_action"
    args: dict = {} # provided from the LLM
    usage: str = "Identify all states and their associated events that trigger transitions in the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")
        states_response_in_html = call_gpt4(f"""
            Given the following system:
            {self.belief.get("description")}
                                            
            Identify what the states and events are and make sure not to include any redundant states or events by making sure that you parse the output for any states or events that might be redundant. Ensure that the states are defined specifically in the context of the object being modeled. It’s important to note that a complete state machine has an initial state and that states might have multiple events occurring on them resulting in multiple transitions from the current state to other states. 
            
            Output the name of the system in the following format:  
            System: "System Name" 
            
            Then produce the HTML table that summarizes the states and events using the following format: 
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> <tr> <td rowspan="2">S0</td> <td>Event 1</td> <td>S0, S1</td> </tr> <tr> <td>Event 2</td> <td>S2</td> </tr> <tr> <td rowspan="2">S1</td> <td>Event 3</td> <td>S2</td> </tr> <tr> <td>Event 4</td> <td>S3</td> </tr> <tr> <td>S2</td> <td>Event 5</td> <td>S1, S3</td> </tr> <tr> <td>S3</td> <td>Event 6</td> <td>S0</td> </tr> </table> ```                                        
        """)
        
        system_name = re.search(r"System:\s*\"(.*?)\"", states_response_in_html).group(1)

        res = extract_states_events_table(states_response_in_html)

        return (system_name, res)
