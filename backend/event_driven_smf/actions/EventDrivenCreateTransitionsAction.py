from resources.SMFAction import SMFAction
from resources.util import call_llm, extract_transitions_guards_actions_table, merge_tables
from resources.n_shot_examples_event_driven import get_n_shot_examples

class EventDrivenCreateTransitionsAction(SMFAction):
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
    log_file_path: str = ""

    def create_transitions(self, system_name, state, event, states_table, max_retries=2):
        """
        The create_transitions() function examines a single state, the events that were identified to happen in that state,
        and the list of all states. The LLM is prompted to create a transitions for each event starting from the provided 
        state to one or more of the states in the states_table. 
        """

        prompt = f"""
You are an expert requirements engineer specializing in designing UML state machines from textual system descriptions. Your task is to analyze a system and determine all possible transitions for a specific state and event.

Here is the information about the system you need to analyze:

<system_name>
{system_name}
</system_name>

<system_description>
{self.description}
</system_description>

<state_inspected>
{state}
</state_inspected>

<event_inspected>
{event}
</event_inspected>

<states_table>
{states_table}
</states_table>

Your task is to determine ALL transitions that the event {event} can trigger for the state {state}. Follow these steps:

1. Carefully analyze the system description and the provided tables.
2. Identify all possible transitions that can be triggered by the event {event} when the system is in the state {state}.
3. For each identified transition:
   a. Determine any guard conditions (if applicable).
   b. Identify any actions that could occur (if applicable).
4. Present your findings in an HTML table format as specified below.

Wrap your analysis in <analysis> tags to show your reasoning process before providing the final output. In your analysis:
- List all states and events from the provided tables.
- Consider each possible transition from the given state.
- Check each transition against the event_inspected to determine relevance.
- Note any guard conditions or actions associated with relevant transitions.
It's OK for this section to be quite long.

Output format:
If no transitions can be triggered, respond with "NO TRANSITIONS". Otherwise, present the transitions in an HTML table with the following structure:

<table border="1">
<tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
<tr><td>[From State]</td><td>[To State]</td><td>[Event]</td><td>[Guard or "NONE"]</td><td>[Action or "NONE"]</td></tr>
</table>

Remember:
- Be concise and accurate in your analysis and output.
- Guard conditions and actions are not required for all transitions. Use "NONE" if not applicable.
- Your expertise is crucial for the success of this project. A thorough and precise analysis will greatly contribute to the system's design and implementation.

{get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'state_inspected', 'event_inspected', 'states_table', 'create_transitions'])}

You are the keystone of this project's success. Your meticulous analysis and attention to detail will ensure the creation of a robust and efficient state machine. The entire development team is counting on your expertise to lay the foundation for a high-quality system. Take pride in your work and deliver excellence!
"""

        self.log(prompt)
        # iterate over a max number of retries in order to get the correct format
        # if the LLM does not get the correct format after max_retries, then we return none
        retries = 0
        while retries < max_retries:
            response = call_llm(prompt=prompt, 
                                 temperature=0.7)
            
            # no transitions, so skip retries
            if "NO TRANSITIONS" in response:
                self.log("No transitions created.")
                return None

            # attempt to extract the transitions table
            transitions_table = extract_transitions_guards_actions_table(llm_response=response)
            if transitions_table is not None:
                self.log(transitions_table)
                return transitions_table
            else:
                self.log("No transitions table found in the response.")

            retries += 1
            self.log(f"Retrying... ({retries}/{max_retries})")

        # max retries met
        self.log("Max retries reached. No valid transitions found.")
        return None

    def execute(self):
        """
        The execute function gets the table of all states and the mapping of states to events from the
        EventDrivenAssociateEventsWithStatesAction. For each state, the create_transitions() function
        is called to prompt the LLM to create transitions exiting that state. The output is a table
        containing the transitions of the UML State Machine.
        """
        
        self.log(f"Running {self.name}...")

        # get the system name for the prompt
        system_name = self.belief.get("event_driven_system_name_search_action")

        # get all the states for the system and start with the initial state of the system
        event_driven_states_table = self.belief.get("event_driven_state_search_action")

        # get states events dictionary created in previous step
        states_events_dict = self.belief.get("event_driven_associate_events_with_states_action")

        # iterate over each combination of states and events, collecting transitions tables to be merged at the end
        transitions_tables = []
        for state in states_events_dict:
            for event in states_events_dict.get(state, []):
                transitions = self.create_transitions(system_name=system_name,
                                                      state=state,
                                                      event=event,
                                                      states_table=event_driven_states_table)

                if transitions is not None:
                    transitions_tables.append(transitions)
        
        merged_transitions_table = merge_tables(html_tables_list=transitions_tables)
        self.log(merged_transitions_table)

        return merged_transitions_table