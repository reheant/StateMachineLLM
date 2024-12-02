import re
from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4

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
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the name of the system you are modeling a state machine for, the description of the state machine, and a table containing all identified states of the system.
        Your task is to identify exactly ONE (1) Initial State for the system.

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. After examining the system description and the HTML table containing identified states, identify exactly ONE (1) Initial State of the system. The Initial State MUST be one of the states in the given table.
        3. Your output the initial state of the system MUST be in the following format:  
        
        <initial_state>InitialState</initial_state>
        
        Keep your answer concise. If you answer incorrectly, you will be fired from your job.
        
        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_name','system_description', 'states_table', 'initial_state'])}

        Here is your input:
        system_name:
        <system_name>{system_name}</system_name>

        system_description:
        <system_description>{self.description}</system_description>

        states_table:
        <states_table>{event_driven_states_table}</states_table>

        initial_state:
        """

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        initial_state_search = re.search(r"<initial_state>(.*?)</initial_state>", response)

        if initial_state_search:
            initial_state = initial_state_search.group(1)
        else:
            initial_state = "NOT FOUND"
        print(initial_state)

        return initial_state