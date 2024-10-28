from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_history_state_table, appendTables, addColumn, extractColumn

class HistoryStateSearchAction(BaseAction):
    name: str = "history_state_search_action"
    args: dict = {
                    "description": "A detailed paragraph description of the system that the generated UML state machine represents (str)"
                 }
    usage: str = "Identify all history states for hierarchical states in the system"

    def execute(self, description):
        print(f"Running {self.name}...")
        hierarchical_states, tmp = self.belief.get('hierarchical_state_search_action')
        print(hierarchical_states)
        hierarchical_states = extractColumn(hierarchical_states, 0)
        modeled_system, tmp = self.belief.get('state_event_search_action')

        for i in range(len(hierarchical_states)):
            prompt = f'''
            You are an AI assistant specialized in creating state machines.
            Determine if the hierarchical state {hierarchical_states[i]} requires a history state to remember a past state after a transition.
            Note that history states are only required if there are transitions to them.
            
            The system description:
            {description}
            The system you are modeling: 
            {modeled_system}

            If the hierarchical state doesn't require a history state, output NONE.
            Otherwise, output your answer in the following HTML form with a row per transition to the history state:
            ```html <table border="1"> <tr> <th>From State</th> <th>Event</th> <th>Guard</th> </tr>
            <tr> <td rowspan="3"> State1 </td> <td> Event1 </td> <td> Condition1 </td> </tr>
            <tr> <td rowspan="3"> State3 </td> <td> Event2 </td> <td> NONE </td> </tr> </table> ```
            '''
            answer = call_gpt4(prompt)
            print(answer)
            history_state_table = None
            if not history_state_table:
                raw_table = extract_history_state_table(answer, True)
                print(raw_table)
                if raw_table:
                    history_state_table = addColumn(raw_table, 'To State', 1, hierarchical_states[i])
            else:
                raw_table = extract_history_state_table(answer, False)
                print(raw_table)
                if raw_table:
                    tmp = addColumn(raw_table, None, 1, hierarchical_states[i])
                    history_state_table = appendTables(history_state_table, tmp)

        return history_state_table
