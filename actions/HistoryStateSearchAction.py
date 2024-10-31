from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_history_state_table, appendTables, addColumn, extractColumn
from bs4 import Tag

class HistoryStateSearchAction(BaseAction):
    name: str = "history_state_search_action"
    args: dict = {}
    usage: str = "Identify all history states for hierarchical states in the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")
        hierarchical_states_table, transition_table = self.belief.get('hierarchical_state_search_action')
        hierarchical_states = list(set(extractColumn(hierarchical_states_table, 0)))
        modeled_system, _ = self.belief.get('state_event_search_action')
        areThereHistoryStates = False

        for i in range(len(hierarchical_states)):
            prompt = f'''
            You are an AI assistant specialized in creating state machines.
            Determine if the hierarchical state {hierarchical_states[i]} requires a history state to remember a past state after a transition.
            Note that history states are only required if there are transitions to them.
            
            The system description:
            {self.description}
            The system you are modeling: 
            {modeled_system}

            If the hierarchical state doesn't require a history state, output NONE.
            Otherwise, output your answer in the following HTML form with a row per transition to the history state:
            ```html <table border="1"> <tr> <th>From State</th> <th>Event</th> <th>Guard</th> <th>Action</th> </tr>
            <tr> <td rowspan="3"> State1 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> </tr>
            <tr> <td rowspan="3"> State3 </td> <td> Event2 </td> <td> NONE </td> </tr> <td> Action2 </td> </table> ```
            '''
            answer = call_gpt4(prompt)
            raw_table = extract_history_state_table(answer, False)
            if raw_table:
                tmp = addColumn(raw_table, None, 1, f'{hierarchical_states[i]}.H')
                history_state_table = tmp if not areThereHistoryStates else appendTables(history_state_table, tmp)
                areThereHistoryStates = True
        
        updated_transition_table = appendTables(transition_table, history_state_table) if areThereHistoryStates else transition_table
        return updated_transition_table
