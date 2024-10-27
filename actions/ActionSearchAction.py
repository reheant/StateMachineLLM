from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_transitions_guards_actions_table

class ActionSearchAction(BaseAction):
    name: str = "action_search_action"
    args: dict = {
                    "system_description": "A detailed paragraph description of the system that the generated UML state machine represents (str)"
                 }
    usage: str = "Identify all actions for transitions between states in the system"

    def execute(self, system_description : str):
        
        transition_table = self.belief.get("transitions_guards_search_action")


        prompt = f"""
                     You are an AI assistant specialized in creating UML state machines. You will be provided an HTML table containing information related to the transitions of a UML state machine along with a problem description.
                     Your task is to update the transition table with Entry Actions and Exit Actions identified from the problem description. Provide updates to the provided HTML transition table by including two new columns for the Entry Action (The action performed on the To State after the transition), and the Exit Action (The action performed on the From State before the transition). 
                     The HTML table format should be as follows:
                     ```html <table border="1"> 
                     <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Entry Action</th> <th>Exit Action</th> </tr> 
                     <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> <td> Entry Action 1 </td> <td> Entry Action 2 </td> </tr> 
                     <tr> <td rowspan="3"> State2 </td> <td> State3 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> <td> NONE </td> </tr> 
                     </table> ```
                     If the transition does not have an Entry Action or Exit Action, leave the action entry in the table blank.
                     The definition of an action in a UML state machine is described below:
                     When an event instance is dispatched, the state machine responds by performing actions, such as changing a variable, performing I/O, invoking a function, generating another event instance, or changing to another state. Any parameter values associated with the current event are available to all actions directly caused by that event.
                     The transition table is: 
                     {transition_table}
                     The problem description is: 
                     {system_description}
                  """

        response = call_gpt4(prompt=prompt)

        print(response)

        transitions_guards_actions_table = extract_transitions_guards_actions_table(response)
        print(transitions_guards_actions_table)
        return transitions_guards_actions_table
