from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_event_driven_events_table

class EventDrivenEventSearchAction(BaseAction):
    """
    The EventDrivenEventSearchAction prompts the LLM to find all the events that occur in the
    UML State Machine from a textual description of the system.

    Input(s): description of the system, name of the system
    Output(s): An HTML table with a column "Event Name", containing the names of all the events in the UML State Machine of the system
    """
    name: str = "event_driven_event_search_action"
    args: dict = {}
    usage: str = "Given a description of a system, identify all events that occur in the system relevant to the UML state machine of the system"
    description: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to find all the events that occur in the
        UML State Machine from a textual description of the system. The output of this
        step is a table containing all events of the UML State Machine of the system
        """

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
        2. Determine all events of the UML state machine from the description of the system.
        3. Finally, give a list of the events in the following HTML table format:

        ```html <table border="1"> 
        <tr> <th>Event Name</th> </tr> 
        <tr> <td>ExampleEvent1</td> </tr> 
        <tr> <td>ExampleEvent2</td></tr> 
        </table> ```
        
        The HTML table you output MUST be in the above format, or else your solution will be rejected.
        """

        response = call_gpt4(prompt=prompt,
                             temperature=0.7)

        event_driven_events_table = extract_event_driven_events_table(llm_response=response)

        print(event_driven_events_table)

        return event_driven_events_table