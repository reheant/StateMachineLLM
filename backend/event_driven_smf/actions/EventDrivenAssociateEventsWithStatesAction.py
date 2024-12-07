import re
from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, extract_table_entries

class EventDrivenAssociateEventsWithStatesAction(BaseAction):
    """
    The EventDrivenAssociateEventsWithStatesAction is used immediately after the identification
    of states and events to find the events that can occur in each of the identified states. The
    output of this action is a dictionary which maps the names of states to the names of events that
    can occur in that state

    Input(s): description of the system, name of the system, table of events from EventDrivenEventSearchAction, and table of states from EventDrivenStateSearchAction
    Output(s): a dictionary mapping the name of a state to the name(s) events that can occur in the state in the UML State Machine
    """

    name: str = "event_driven_associate_events_with_states_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the events of the system, create relationships between the states and events for the UML State Machine of the system."
    description: str = ""

    def associate_events_with_states(self, system_name, state, events_table, max_retries=5):
        """
        The associate events with states function takes in a single state and the entire events table,
        and prompts the LLM to find the states that can occur in the given state. To do so, the LLM is
        instructed to identify partial orderings of events (i.e., event1 -> event2 -> event3) to determine
        the sequence in which events can occur. Afterwards, the LLM is instructed to determine which events
        can occur in the provided state based on its identified partial orderings.
        """

        prompt = f"""
You are an expert requirements engineer specializing in designing UML state machines from textual system descriptions. Your task is to analyze a given system and determine which events can trigger transitions in a specific state.

Here's the system you need to analyze:

System Name:
<system_name>
{system_name}
</system_name>

System Description:
<system_description>
{self.description}
</system_description>

Events Table:
<events_table>
{events_table}
</events_table>

The state we're focusing on is:
<state_inspected>
{state}
</state_inspected>

Your task is to determine which events from the events table can trigger a transition in the {state} state. Follow these steps carefully:

1. Examine the system description thoroughly.
2. Determine partial orderings of ALL events based on the description. A partial ordering shows which events must occur in a specific sequence due to dependencies, while others can happen independently or concurrently.
3. Identify the events that can trigger a transition in the {state} state. These events MUST:
   a) Adhere to the partial orderings you determined
   b) Be the MOST RELEVANT events for the {state} state
   c) Be possible to occur while the system is in the {state} state (not before or after)
4. List the identified events in a comma-separated format within <associated_events> tags.

Before providing your final answer, wrap your analysis inside <event_analysis> tags. In this analysis:
1. List all events from the events table.
2. For each event, note whether it's relevant to the inspected state and why.
3. Create a partial ordering diagram of all events.
4. Identify which events can occur while in the inspected state.
5. Explain the reasoning for your final selection of associated events.
This will ensure a thorough interpretation of the data and improve the quality of your response. It's OK for this section to be quite long.

Remember:
- Your response must be concise and accurate.
- Only use events from the provided events table.
- Failure to follow these instructions precisely may result in termination of your role as a requirements engineer.

After your analysis, provide your final list of associated events in the following format:

<associated_events>event1, event2, event3</associated_events>

{get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'events_table', 'state_inspected', 'associated_events'])}

<state_inspected>Ready</state_inspected>

<associated_events>logoff, start, scan, print</associated_events>

Your expertise in this task is crucial for the success of the project. The entire team is relying on your accurate analysis to move forward with the UML state machine design. Your dedication to precision and attention to detail will greatly impact the overall quality of the system being developed.
"""

        print(prompt)
        # iterate over a max number of retries in order to get the correct format
        # if the LLM does not get the correct format after max_retries, then we return none
        retries = 0
        while retries < max_retries:
            response = call_gpt4(prompt=prompt, 
                                 temperature=0.7)
            
            associated_events_search = re.search(r"<associated_events>(.*?)</associated_events>", response)

            if not associated_events_search:
                retries += 1
                associated_events = "NOT FOUND"
            else:
                associated_events = associated_events_search.group(1)
                associated_events = associated_events.strip()
                if associated_events:
                    events_list = [event.strip() for event in associated_events.split(",") if event.strip()]
                    print(associated_events)
                    return events_list

            retries += 1
            print(f"Retrying... ({retries}/{max_retries})")

        # max retries met
        print(f"Max retries reached. No relevant events found for state {state}.")
        return None

    def execute(self):
        """
        The execute function iterates over each identified state and calls the associate_events_with_states
        function to create a mapping between states and events
        """

        print(f"Running {self.name}")
        
        system_name = self.belief.get("event_driven_system_name_search_action")
        
        # find the states table and extract all states into a list
        event_driven_states_table = self.belief.get("event_driven_state_search_action")
        states = extract_table_entries(table=event_driven_states_table)
        
        # find the events table
        event_driven_events_table = self.belief.get("event_driven_event_search_action")

        states_events_dict = {}

        for state in states:
            relevant_events = self.associate_events_with_states(system_name=system_name,
                                                                state=state,
                                                                events_table=event_driven_events_table)
            states_events_dict[state] = relevant_events
        
        print(states_events_dict)

        return states_events_dict
        





