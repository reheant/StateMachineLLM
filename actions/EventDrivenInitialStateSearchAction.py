import re
from sherpa_ai.actions.base import BaseAction
from util import call_gpt4

class EventDrivenInitialStateSearchSearchAction(BaseAction):
    name: str = "event_driven_initial_state_search_action"
    args: dict = {}
    usage: str = "Given a description of a system and a list of all states of the system, identify the Initial State of the UML state machine of the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")

        system_name = self.belief.get("event_driven_system_name_search_action")
        event_driven_states_table = self.belief.get("event_driven_state_search_action")

        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system and a table containing all identified states of the system, your task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        Table of identified states of the UML state machine:
        {event_driven_states_table}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Using the system description and the HTML table containing identified states, identify exactly ONE (1) Initial State of the system.
        3. Finally, output the initial state of the system in the following format:  
        
        Initial State: "Initial State"
        
        The Initial State you output MUST be in the above format, or else your solution will be rejected.
        """

        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        initial_state = re.search(r"Initial State:\s*\"(.*?)\"", response).group(1)

        print(initial_state)

        return initial_state