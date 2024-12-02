from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, extract_event_driven_states_table

class EventDrivenStateSearchAction(BaseAction):
    """
    The EventDrivenStateSearchAction uses the description of a system to find
    all states in the UML state machine of the system

    Input(s): description of the system, name of the system
    Output(s): An HTML table with a column "State Name", containing the names of all the states in the UML State Machine of the system
    """

    name: str = "event_driven_state_search_action"
    args: dict = {}
    usage: str = "Given a description of a system, identify all states in the UML state machine of the system"
    description: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to find all states in the UML state machine from the textual
        description of the system
        """

        print(f"Running {self.name}...")

        system_name = self.belief.get("event_driven_system_name_search_action")

        prompt = f"""
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the name of the system you are modeling a state machine for, and the description of the state machine.
        Your task is to identify all states of the UML state machine from the description of the system.

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Determine all states of the UML state machine from the description of the system.
        3. You MUST output the list of all states in the following format HTML format:

        <states_table>```html<table border="1"> 
        <tr><th>StateName</th></tr> 
        <tr><td>ExampleState1</td></tr> 
        <tr><td>ExampleState2</td></tr> 
        </table>```</states_table>

        Keep your answer concise. If you answer incorrectly, you will be fired from your job.

        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_name','system_description', 'states_table'])}

        Here is your input:
        system_name:
        <system_name>{system_name}</system_name>

        system_description:
        <system_description>{self.description}</system_description>

        states_table:
        """

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)

        event_driven_states_table = extract_event_driven_states_table(llm_response=response)

        print(event_driven_states_table)

        return event_driven_states_table