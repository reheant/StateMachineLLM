import re
from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_table_entries

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
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, a single identified state of the system, and all events of the system, you task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        The single identified state of the system is:
        {state}

        The table of identified events of the system is:
        {events_table}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Examine the description of the system. Using the description of the system, determine partial orderings of ALL events. A partial ordering of events refers to a system where some events must occur in a specific sequence due to dependencies, while others can happen independently or concurrently.
        3. Determine which events out of ALL events apply to the state {state} based on the partial orderings you determined in step 2. The events that occur in this state MUST adhere to the orderings that you generated in step 2. You MUST identify only the MOST RELEVANT events for the given state. Ensure no events that you identify can occur only before or after the event has been reached in the UML state machine. You MUST provide events for the given state, otherwise your solution will be rejected.
        4. Finally, give a list of the events that apply to the state {state} in a comma seperated list in the following format:

        Relevant Events: <first_event>, <second_event>, <third_event>, ...
        
        The events that you provide MUST come from the original events table provided to you above. DO NOT add events that do not exist.
        Your solution MUST be in the above format, otherwise it will be rejected.
        """

        # iterate over a max number of retries in order to get the correct format
        # if the LLM does not get the correct format after max_retries, then we return none
        retries = 0
        while retries < max_retries:
            response = call_gpt4(prompt=prompt, 
                                 temperature=0.7)
            
            match = re.search(r"Relevant Events:\s*([\w\s,]+)", response)
            if not match:
                retries += 1
            else:
                events = match.group(1)
                events = events.strip()
                if events:
                    events_list = [event.strip() for event in events.split(",") if event.strip()]
                    print(events_list)
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
        





