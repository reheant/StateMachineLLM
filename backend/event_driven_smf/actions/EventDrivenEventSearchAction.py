from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, extract_event_driven_events_table

class EventDrivenEventSearchAction(BaseAction):
    name: str = "event_driven_event_search_action"
    args: dict = {}
    usage: str = "Given a description of a system, identify all events that occur in the system relevant to the UML state machine of the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")

        system_name = self.belief.get("event_driven_system_name_search_action")

        prompt = f"""
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the name of the system you are modeling a state machine for, and the description of the state machine.
        Your task is to identify all events of the UML state machine that could trigger state transitions.
        
        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Determine all events of the UML state machine from the description of the system that could trigger state transitions.
        3. Your output of the list of the events MUST be in the following HTML table format:
        
        <events_table>```html<table border="1"> 
        <tr><th>EventName</th></tr> 
        <tr><td>ExampleEvent1</td></tr> 
        <tr><td>ExampleEvent2</td></tr> 
        </table>```</events_table>
        
        Keep your answer concise. If you answer incorrectly, you will be fired from your job.
        
        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'events_table'])}

        Here is your input:
        system_name:
        <system_name>{system_name}</system_name>

        system_description:
        <system_description>{self.description}</system_description>

        events_table:
        """

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)

        event_driven_events_table = extract_event_driven_events_table(llm_response=response)

        print(event_driven_events_table)

        return event_driven_events_table