from sherpa_ai.actions.base import BaseAction
from resources.util import call_llm, extract_history_state_table, addColumn, appendTables, gsm_tables_to_dict

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
You are an expert requirements engineer specializing in UML state machine design. Your task is to analyze a given system description and determine whether a specified superstate requires a history state. This analysis is crucial for creating accurate and efficient state machine models.

Here is the system you need to analyze:

<system_name>
{modeled_system}
</system_name>

<system_description>
{self.description}
</system_description>

Please carefully review the following transition table for the system:

                Transition table:
                {transitions_table}

                Super state:
                {superstate["name"]}
                Substates of the super state:
                {superstate["children"]}

            Your answer:
            '''

            answer = call_llm(prompt)
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
