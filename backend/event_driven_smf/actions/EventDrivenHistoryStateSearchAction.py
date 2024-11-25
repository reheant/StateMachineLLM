from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4, extract_history_state_table, addColumn, appendTables, gsm_tables_to_dict
from resources.n_shot_examples import get_n_shot_examples

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
        transitions_table = self.belief.get('event_driven_refactor_transition_names_action')
        modeled_system = self.belief.get('event_driven_system_name_search_action')
        superstates = [state for state in gsm_tables_to_dict(self.belief.get('event_driven_create_hierarchical_states_action'), transitions_table, None)[0] if isinstance(state, dict)]
        events = self.belief.get('event_driven_event_search_action')

        for superstate in superstates:
            prompt = f'''
            You are an AI assistant specialized in creating state machines.

            Objective:
            Given the system description, system being modeled and a super state (a state that contains substates), determine whether the super state requires a history state (to remember the last active substate after a transition), and the transitions to the history state in the state machine.

            Definitions:

                •	History State: A mechanism in state machines that allows a composite state to remember its last active substate when re-entered, instead of starting from its initial substate.

            Criteria for Requiring a History State:

                1.	Transitions Targeting the Parent State: A history state is needed if there are transitions to a parent state from outside its hierarchy.
                2.	Resuming Previous Substate: The system's behavior requires resuming the last active substate rather than starting from the initial substate upon re-entry.

            Instructions:

                1.	Analyze the System:
                    Review the system description, the modeled system, and the transition table provided below.
                2.	Determine the Need for History States:
                    For the given super state, decide if a history state is required based on the criteria.
                3.	Identify Transitions to the History state:
                    Find all transitions to the history states triggered by one of the following events:
                    {events}
                4.	Output Format:
                    If no history state is required for the super state, output: NO_HISTORY_STATE.
                    Otherwise output the following table representing the transitions to the history state of the given super state:
                    ```html <table border="1"> 
                    <tr> <th>From State</th> <th>Event</th> <th>Guard</th> <th>Action</th> </tr> 
                    <tr> <td rowspan="3"> State1 </td> <td> Event1 </td> <td> Condition1 </td> <td> Action 1 </td> </tr> 
                    <tr> <td rowspan="3"> State2 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> </tr> 
                    <tr> <td rowspan="3"> State4 </td> <td> Event3 </td> <td> NONE </td> <td> Action 1 </td> </tr> 
                    <tr> <td rowspan="3"> State2 </td> <td> Event1 </td> <td> NONE </td> <td> NONE </td> </tr> 
                    </table> ```

            Input:
                The system description:
                {self.description}

                The system you are modeling: 
                {modeled_system}

                Transition table:
                {transitions_table}

                Super state:
                {superstate["name"]}
                Substates of the super state:
                {superstate["children"]}

            Your answer:
            '''

            answer = call_gpt4(prompt)
            history_transitions = extract_history_state_table(answer)

            if not history_transitions:
                print('Not Found history state')
                continue
            else:
                print('Found history state')
                history_transitions = addColumn(history_transitions, None, 2, f'{superstate["name"]}.H')
                transitions_table = appendTables(transitions_table, history_transitions)
        print(transitions_table)
        return transitions_table
