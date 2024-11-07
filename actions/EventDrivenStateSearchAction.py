from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_event_driven_states_table

class EventDrivenStateSearchSearchAction(BaseAction):
    name: str = "event_driven_state_search_action"
    args: dict = {}
    usage: str = "Given a description of a system, identify all states in the UML state machine of the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")

        system_name = self.belief.get("event_driven_system_name_search_action")

        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, your task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Determine all states of the UML state machine from the description of the system.
        3. Finally, give a list of the states in the following HTML table format:

        ```html <table border="1"> 
        <tr> <th>State Name</th> </tr> 
        <tr> <td>ExampleState1</td> </tr> 
        <tr> <td>ExampleState2</td></tr> 
        </table> ```
        
        The HTML table you output MUST be in the above format, or else your solution will be rejected.
        """

        response = call_gpt4(prompt=prompt)

        event_driven_states_table = extract_event_driven_states_table(llm_response=response)

        print(event_driven_states_table)

        return event_driven_states_table