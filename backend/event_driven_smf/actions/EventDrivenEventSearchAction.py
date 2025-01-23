from resources.SMFAction import SMFAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_llm, extract_event_driven_events_table

class EventDrivenEventSearchAction(SMFAction):
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
    log_file_path: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to find all the events that occur in the
        UML State Machine from a textual description of the system. The output of this
        step is a table containing all events of the UML State Machine of the system
        """

        self.log(f"Running {self.name}...")

        system_name = self.belief.get("event_driven_system_name_search_action")
        n_shot_example_list = self.belief.get("n_shot_examples")

        prompt = f"""
                You are an expert requirements engineer specialized in designing UML state machines from textual system descriptions. Your task is to identify all events that could trigger state transitions in a UML state machine based on the given system description.

                Here is the system name:
                <system_name>
                {system_name}
                </system_name>

                Now, carefully read through the following system description:
                <system_description>
                {self.description}
                </system_description>

                Your goal is to analyze this description and identify all events that could trigger state transitions in the UML state machine for this system. Follow these steps:

                1. Thoroughly analyze the system description.
                2. Identify all possible events that could trigger state transitions.
                3. Create a list of these events.
                4. Format the events in an HTML table as specified below.

                Before providing your final output, wrap your thought process in <event_identification_process> tags. In this section:
                - List key components or subsystems mentioned in the description
                - Identify state-changing actions or processes for each component
                - Consider external inputs or triggers that might affect the system
                - Reflect on potential error states or exceptional conditions

                This will help ensure a thorough interpretation of the data and identification of all relevant events. It's OK for this section to be quite long, as a detailed analysis will lead to a more comprehensive list of events.

                After your analysis, present your final list of events in an HTML table using the following format:

                <events_table>
                ```html
                <table border="1">
                <tr><th>EventName</th></tr>
                <tr><td>Event1</td></tr>
                <tr><td>Event2</td></tr>
                ...
                </table>
                ```
                </events_table>

                {get_n_shot_examples(n_shot_example_list,['system_name', 'system_description', 'events_table'])}

                Important guidelines:
                - Include only the event names in the table, without additional details.
                - If an event requires parameters, include them in parentheses after the event name (e.g., login(cardID)).
                - Ensure that your list is comprehensive and captures all possible events mentioned or implied in the system description.
                - Keep your event names concise and clear.

                Emotional reminder: Your expertise in identifying the correct events table is vital for the success of the entire system modeling process. Your accurate analysis will lay the foundation for a robust and reliable state machine design. Take pride in your role and let your expertise shine through in your thoughtful analysis and precise selection.


                Now, proceed with your analysis and creation of the events table.
                """

        self.log(prompt)
        response = call_llm(prompt=prompt)

        event_driven_events_table = extract_event_driven_events_table(llm_response=response)

        self.log(event_driven_events_table)

        return event_driven_events_table
