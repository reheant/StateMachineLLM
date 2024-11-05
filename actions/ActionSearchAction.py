from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_transitions_guards_actions_table

class ActionSearchAction(BaseAction):
    name: str = "action_search_action"
    args: dict = {}
    usage: str = "Identify all actions for transitions between states in the system"
    description: str = ""
    def execute(self):
        print(f"Running {self.name}...")
        transition_table = self.belief.get("transitions_guards_search_action")


        prompt = f"""
                     You are an AI assistant specialized in creating UML state machines. You will be provided an HTML table containing information related to the transitions of a UML state machine along with a problem description.
                     Your task is to update the transition table to include an Action for each transition. Entry Actions and Exit Actions identified from the problem description. Provide updates to the provided HTML transition table by including a new column for Action. 
                     
                     The HTML table format MUST be as follows. You are NOT allowed to add extra columns or entries into the updated transitions table.
                     
                     ```html <table border="1"> 
                     <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Action</th> </tr> 
                     <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> <td> Action 1 </td> </tr> 
                     <tr> <td rowspan="3"> State2 </td> <td> State3 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> </tr> 
                     </table> ```
                     
                     If the transition does not have an Action, enter NONE into the table.
                     The definition of an action in a UML state machine is described below:
                     When an event instance is dispatched, the state machine responds by performing actions, such as changing a variable, performing I/O, invoking a function, generating another event instance, or changing to another state. Any parameter values associated with the current event are available to all actions directly caused by that event.
                     

                    Example 1:

                    The system description: 
                    The printer has a master switch which turns the printer on or off. Once the printer is turned on, a user needs to log in before being able to print or scan a document. To login, a user taps her/his printer card on the printer's card reader. Each printer card has a unique ID. If the printer card is authorized, the user can either choose "scan" or "print". If the printer card is not authorized, a login error message is shown. For the "print" option, the user presses the start button to print the user's first document in the user's print queue. If there is no document in the print queue, an error message is shown instead of performing the printing task. For the "scan" option, the user presses the start button for the printer to scan an original document, which was placed by the user in the automatic page feeder. The scan is sent to the user's email inbox. If the printer does not detect an original document, an error message is shown instead of performing the scanning task. When the printer is done printing or scanning, the user can print or scan the next document. The user may also stop the printing/scanning task at any time by pressing the stop button. The user is allowed to logoff either before or after a printing/scanning task but not while the printer is in the middle of a printing/scanning task. If there is a paper jam, the printer will suspend the printing/scanning task to allow the user to clear the paper jam. The user may then either cancel the printing/scanning task or resume it. In case the printer runs out of paper during a printing task, the printer suspends the printing task to allow the user to resupply paper. The user may then either cancel the printing task or resume it.   
                        
                    Transitions Table:
                    <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login</td><td>!idAuthorized(cardID)</td></tr><tr><td>Idle</td><td>Ready</td><td>login</td><td>idAuthorized(cardID)</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>jam</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>stop</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>done</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy (history)</td><td>resume</td><td>NONE</td></tr></table>


                    

                    Output:

                    Output of HTML Transition, Guard and Action Table:
                    <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr><tr><td>Idle</td><td>Ready</td><td>login</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy.H</td><td>resume</td><td>NONE</td><td>NONE</td></tr></table>
                    
                    Example 2: 
                    
                    The transition table is: 
                    {transition_table}
                     
                    The problem description is: 
                    {self.description}

                    Output: 

                """

        response = call_gpt4(prompt=prompt)



        transitions_guards_actions_table = extract_transitions_guards_actions_table(response)

        return transitions_guards_actions_table
