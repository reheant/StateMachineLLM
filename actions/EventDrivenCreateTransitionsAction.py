from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_transitions_guards_actions_table, merge_tables

class EventDrivenCreateTransitionsAction(BaseAction):
    """
    The EventDrivenCreateTransitionsAction iterates over the mapping of states and events identified in the
    EventDrivenAssociateEventsWithStatesAction and prompts the LLM to create transitions.

    Input(s): description of the system, name of the system, table of states of the system from EventDrivenStateSearchAction, dictionary mapping states to events from EventDrivenAssociateEventsWithStatesAction
    Outputs(s): an HTML table with columns "From State", "To State", "Event", "Guard", and "Action" containing all transitions of the UML State Machine 
    """

    name: str = "event_driven_create_transitions_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the events of the system, identify all transitions in the UML state machine of the system"
    description: str = ""

    def create_transitions(self, system_name, state, events, states_table, max_retries=5):
        """
        The create_transitions() function examines a single state, the events that were identified to happen in that state,
        and the list of all states. The LLM is prompted to create a transitions for each event starting from the provided 
        state to one or more of the states in the states_table. 
        """

        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, one of the identified states of the system, one of the identified events of the system, and a table of all identified states of the system, your task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        The identified state is:
        {state}

        The list of relevant events is:
        {events}

        The table of identified events is:
        {states_table}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. For each event, determine if the event can actually occur in the provided state {state}.
        3. If the event CANNOT occur in the state, skip to step 7. Otherwise, if the event CAN occur in the state, create transition(s) for when the event occurs in the state. Use the table of provided states to determine the destination state when the provided event occurs in the provided state.
        4. If any transitions were identified, identify any guard conditions for each of the identified transitions. Note that guard conditions are NOT required for transitions, so it is possible that a transition may not have a guard condition. If there are no guard conditions identified for one of the transitions, output "NONE".
        5. If any transitions were identified, identify any actions/side effects for each of the identified transitions. Note that actions are NOT required for transitions, so it is possible that a transition may not have an associated action. If there are no actions identified for one of the transitions, output "NONE".
        6. If any transitions were identified, give a list of transitions in the following HTML table format:
        
        ```html <table border="1"> 
        <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Action</th> </tr> 
        <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> <td> Action 1 </td> </tr> 
        <tr> <td rowspan="3"> State2 </td> <td> State3 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> </tr> 
        </table> ```

        where the "From State", "To State", and "Event" column entries are required, but the "Guard" and "Action" are NOT required. If no "Guard" or "Action" has been identified for a transition, fill the "Guard" or "Action" entry with "NONE".

        7. If there are events remaining in the list of events, go back to step 2 and repeat the process.
        8. Combine all transitions tables into a single table in the format:

        ```html <table border="1"> 
        <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Action</th> </tr> 
        <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> <td> Action 1 </td> </tr> 
        <tr> <td rowspan="3"> State2 </td> <td> State3 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> </tr> 
        </table> ```
        """

        # iterate over a max number of retries in order to get the correct format
        # if the LLM does not get the correct format after max_retries, then we return none
        retries = 0
        while retries < max_retries:
            response = call_gpt4(prompt=prompt, 
                                 temperature=0.7)
            
            # attempt to extract the transitions table
            transitions_table = extract_transitions_guards_actions_table(llm_response=response)
            if transitions_table is not None:
                print("Valid transitions found.")
                return transitions_table
            else:
                print("No transitions table found in the response.")

            retries += 1
            print(f"Retrying... ({retries}/{max_retries})")

        # max retries met
        print("Max retries reached. No valid transitions found.")
        return None

    def execute(self):
        """
        The execute function gets the table of all states and the mapping of states to events from the
        EventDrivenAssociateEventsWithStatesAction. For each state, the create_transitions() function
        is called to prompt the LLM to create transitions exiting that state. The output is a table
        containing the transitions of the UML State Machine.
        """

        print(f"Running {self.name}...")

        # get the system name for the prompt
        system_name = self.belief.get("event_driven_system_name_search_action")

        # get all the states for the system and start with the initial state of the system
        event_driven_states_table = self.belief.get("event_driven_state_search_action")

        # get states events dictionary created in previous step
        states_events_dict = self.belief.get("event_driven_associate_events_with_states_action")

        # iterate over each combination of states and events, collecting transitions tables to be merged at the end
        transitions_tables = []
        for state, events in states_events_dict.items():
            transitions = self.create_transitions(system_name=system_name,
                                                  state=state,
                                                  events=events,
                                                  states_table=event_driven_states_table)

            transitions_tables.append(transitions)
        
        # merged all transition tables created in the above loop
        merged_transitions_table = merge_tables(html_tables_list=transitions_tables)
        print(merged_transitions_table)

        return merged_transitions_table