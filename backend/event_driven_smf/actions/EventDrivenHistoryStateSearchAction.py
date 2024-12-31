from resources.SMFAction import SMFAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_llm, extract_history_state_table, addColumn, appendTables, gsm_tables_to_dict

class EventDrivenHistoryStateSearchAction(SMFAction):
    """
    The EventDrivenHistoryStateSearchAction examines the transitions, events, and hierarchical states
    of the UML State Machine and prompts the LLM to identify which hierarchical states and transitions
    can be simplified by adding a history state to hierarchical states.

    Input(s): description of the system, name of the system, table of events in the UML State Machine, table of transitions in the UML State Machine, and table of hierarchical states and states in the UML State Machine of the system
    Output(s): table of transitions in the UML State Machine with necessary transitions to history states
    """

    name: str = "event_driven_history_state_search_action"
    args: dict = {}
    usage: str = "Identify all history states for hierarchical states in the system"
    description: str = ""
    log_file_path: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to create transitions to history states based on the tables of
        hierarchical states, transitions, and events identified.
        """
        
        self.log(f"Running {self.name}...")
        
        transitions_table = self.belief.get('event_driven_factor_out_transitions_for_hierarchal_states_action')
        modeled_system = self.belief.get('event_driven_system_name_search_action')
        superstates = [state for state in gsm_tables_to_dict(self.belief.get('event_driven_create_hierarchical_states_action'), transitions_table, None)[0] if isinstance(state, dict)]
        events = self.belief.get('event_driven_event_search_action')

        for superstate in superstates:
            prompt = f'''
                You are an expert requirements engineer specializing in UML state machine design. Your task is to analyze a given system description and determine whether a specified superstate requires a history state. This analysis is crucial for creating accurate and efficient state machine models.

                Here is the system you need to analyze:

                <system_name>
                {modeled_system}
                </system_name>

                <system_description>
                {self.description}
                </system_description>

                Please carefully review the following transition table for the system:

                <transitions_table>
                {transitions_table}
                </transitions_table>

                These are the events that can occur in the system:

                <events_table>
                {events}
                </events_table>

                You need to determine if the following superstate requires a history state:

                <superstate_inspected_for_history_state>
                {superstate["name"]}
                </superstate_inspected_for_history_state>

                These are the substates associated with the superstate:

                <substates_inspected_for_history_state>
                {superstate["children"]}
                </substates_inspected_for_history_state>

                Instructions:
                1. Analyze the system description, focusing on the behavior related to the specified superstate.
                2. Examine the transition table, paying close attention to transitions involving the superstate and its substates.
                3. Consider the criteria for requiring a history state:
                a. Are there transitions targeting the parent state from outside its hierarchy?
                b. Does the system's behavior require resuming the last active substate rather than starting from the initial substate upon re-entry?
                4. Make a decision on whether the superstate needs a history state.
                5. If a history state is needed, create a table listing all transitions to the history state triggered by one of the events in the events table.

                Please show your reasoning process inside <state_machine_analysis> tags. In your analysis:
                1. List all transitions involving the superstate and its substates, numbering each one.
                2. Identify transitions targeting the parent state from outside its hierarchy.
                3. Analyze whether the system's behavior requires resuming the last active substate upon re-entry.
                4. Consider arguments for and against the need for a history state.

                Be thorough but concise in your analysis. It's OK for this section to be quite long.

                If the superstate does not require a history state, output "NO_HISTORY_STATE".

                If a history state is needed, present the table in the following HTML format:

                <history_state_table>
                <table border="1">
                <tr><th>From State</th><th>Event</th><th>Guard</th><th>Action</th></tr>
                <tr><td>[From State]</td><td>[Event]</td><td>[Guard]</td><td>[Action]</td></tr>
                </table>
                </history_state_table>

                Note: The events in the Event column MUST be part of the provided event table.

                {get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'transitions_table', 'events_table', 'superstate_inspected_for_history_state', 'substates_inspected_for_history_state', 'history_state_table'])}

                Remember, your analysis and decision are critical for the correct implementation of this state machine. The success of the entire system design depends on your expertise and attention to detail. Your concise and accurate assessment will greatly impact the efficiency and reliability of the final product.
                '''

            self.log(prompt)
            answer = call_llm(prompt)
            history_transitions = extract_history_state_table(answer)

            if not history_transitions:
                self.log('Not Found history state')
                continue
            else:
                self.log('Found history state')
                history_transitions = addColumn(history_transitions, None, 1, f'{superstate["name"]}.H')
                transitions_table = appendTables(transitions_table, history_transitions)
        self.log(transitions_table)
        return transitions_table