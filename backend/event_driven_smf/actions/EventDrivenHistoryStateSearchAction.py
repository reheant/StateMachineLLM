from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, extract_history_state_table, addColumn, appendTables, gsm_tables_to_dict

class EventDrivenHistoryStateSearchAction(BaseAction):
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

    def execute(self):
        """
        The execute function prompts the LLM to create transitions to history states based on the tables of
        hierarchical states, transitions, and events identified.
        """
        
        print(f"Running {self.name}...")
        
        transitions_table = self.belief.get('event_driven_factor_out_transitions_for_hierarchal_states_action')
        modeled_system = self.belief.get('event_driven_system_name_search_action')
        superstates = [state for state in gsm_tables_to_dict(self.belief.get('event_driven_create_hierarchical_states_action'), transitions_table, None)[0] if isinstance(state, dict)]
        events = self.belief.get('event_driven_event_search_action')

        for superstate in superstates:
            prompt = f'''
            You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
            You are given the name of the system you are modeling a state machine for, the description of the state machine, the table of transitions identified, the table of events identified, a superstate identified, and its associated substates.
            Your task is to determine whether the superstate given requires a history state (to remember the last active substate after a transition), and the transitions to the history state in the state machine.

            Definitions:
            History State: A mechanism in state machines that allows a superstate to remember its last active substate when re-entered, instead of starting from its initial substate.

            Criteria for Requiring a History State:
            1.	Transitions Targeting the Parent State: A history state is needed if there are transitions to a parent state from outside its hierarchy.
            2.	Resuming Previous Substate: The system's behavior requires resuming the last active substate rather than starting from the initial substate upon re-entry.

            Solution structure:
            1. Begin the response with "Let's think step by step."
            2.	Analyze the system description, the modeled system, and the transition table provided below to determine if the given superstate needs a history state.
            3.	If the superstate does not require a history state, output "NO_HISTORY_STATE", otherwise output a table listing all transitions to the history state triggered by one of the events in the events table in the following HTML format:
            
            <history_state_table>```html<table border="1"> 
            <tr><th>FromState</th><th>Event</th><th>Guard</th><th>Action</th></tr>
            <tr><td>State1</td><td>Event1</td><td>Condition1</td><td>Action1</td></tr>
            <tr><td>State2</td><td>Event1</td><td>Condition1</td><td>NONE</td></tr>
            <tr><td>State4</td><td>Event3</td><td>NONE</td><td>Action1</td></tr>
            <tr><td>State2</td><td>Event1</td><td>NONE</td><td>NONE</td></tr>
            </table>```</history_state_table>

            Note that the events in the Event column MUST be part of the provided event table, otherwise your answer will be rejected.
            
            Here is an example:
            {get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'transitions_table', 'events_table', 'superstate_inspected_for_history_state', 'substates_inspected_for_history_state', 'history_state_table'])}

            Here is your input:
            system_name:
            <system_name>{modeled_system}</system_name>

            system_description:
            <system_description>{self.description}</system_description>

            transitions_table:
            <transitions_table>{transitions_table}</transitions_table>

            events_table:
            <events_table>{events}</events_table>

            superstate_inspected_for_history_state:
            <superstate_inspected_for_history_state>{superstate["name"]}</superstate_inspected_for_history_state>

            substates_inspected_for_history_state:
            <substates_inspected_for_history_state>{superstate["children"]}</substates_inspected_for_history_state>

            history_state_table:
            '''

            print(prompt)
            answer = call_gpt4(prompt)
            history_transitions = extract_history_state_table(answer)

            if not history_transitions:
                print('Not Found history state')
                continue
            else:
                print('Found history state')
                history_transitions = addColumn(history_transitions, None, 1, f'{superstate["name"]}.H')
                transitions_table = appendTables(transitions_table, history_transitions)
        print(transitions_table)
        return transitions_table
