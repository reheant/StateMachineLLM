from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_states_events_table
import re

class StateEventSearchAction(BaseAction):
    name: str = "state_event_search_action"
    args: dict = {} # provided from the LLM
    usage: str = "Identify all states and their associated events that trigger transitions in the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")
        states_response_in_html = call_gpt4(f"""
            Given the problem description, identify what the states and events are and make sure not to include any redundant states or events by making sure that you parse the output for any states or events that might be redundant. Ensure that the states are defined specifically in the context of the object being modeled. It’s important to note that a complete state machine has an initial state and that states might have multiple events occurring on them resulting in multiple transitions from the current state to other states. 
            
            Output the name of the system in the following format:  
            System: "System Name" 
            
            Then produce the HTML table that summarizes the states and events MUST use these table headers:
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> </table> ```

            Example 1:

            Problem Description:
            The printer has a master switch which turns the printer on or off. Once the printer is turned on, a user needs to log in before being able to print or scan a document. To login, a user taps her/his printer card on the printer's card reader. Each printer card has a unique ID. If the printer card is authorized, the user can either choose "scan" or "print". If the printer card is not authorized, a login error message is shown. For the "print" option, the user presses the start button to print the user's first document in the user's print queue. If there is no document in the print queue, an error message is shown instead of performing the printing task. For the "scan" option, the user presses the start button for the printer to scan an original document, which was placed by the user in the automatic page feeder. The scan is sent to the user's email inbox. If the printer does not detect an original document, an error message is shown instead of performing the scanning task. When the printer is done printing or scanning, the user can print or scan the next document. The user may also stop the printing/scanning task at any time by pressing the stop button. The user is allowed to logoff either before or after a printing/scanning task but not while the printer is in the middle of a printing/scanning task. If there is a paper jam, the printer will suspend the printing/scanning task to allow the user to clear the paper jam. The user may then either cancel the printing/scanning task or resume it. In case the printer runs out of paper during a printing task, the printer suspends the printing task to allow the user to resupply paper. The user may then either cancel the printing task or resume it.   

            Output:
            
            System: "Printer Scanner"

            Output table in HTML Format:
            <table border="1"><tr><th>Current State</th><th>Event</th><th>Next State(s)</th></tr><tr><td>Off</td><td>Turn On</td><td>On</td></tr><tr><td>On</td><td>Turn Off</td><td>Off</td></tr><tr><td>Idle</td><td>User Login with Unauthorized Card</td><td>Idle</td></tr><tr><td>Idle</td><td>User Login with Authorized Card</td><td>Ready</td></tr><tr><td>Ready</td><td>User Logoff</td><td>Idle</td></tr><tr><td>Ready</td><td>Start Scan without Document</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Start Print with Empty Queue</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Select Scan Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Select Print Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Start Scan with Document Loaded</td><td>ScanAndEmail</td></tr><tr><td>Ready</td><td>Start Print with Document in Queue</td><td>Print</td></tr><tr><td>ScanAndEmail</td><td>Scan Complete</td><td>Ready</td></tr><tr><td>Print</td><td>Out of Paper</td><td>Suspended</td></tr><tr><td>Print</td><td>Paper Jam</td><td>Suspended</td></tr><tr><td>Print</td><td>Stop Printing</td><td>Ready</td></tr><tr><td>Print</td><td>Print Complete</td><td>Ready</td></tr><tr><td>Suspended</td><td>Cancel Task</td><td>Ready</td></tr><tr><td>Suspended</td><td>Resume Task</td><td>Previous State (Print or Scan)</td></tr></table>
            
            Example 2:  

            Problem Description:                           
            {self.belief.get("description")}

            Output:
            
            System: 

            Output table in HTML Format:

        """)
        
        system_name = re.search(r"System:\s*\"(.*?)\"", states_response_in_html).group(1)

        state_events_table = extract_states_events_table(states_response_in_html)

        return (system_name, state_events_table)
