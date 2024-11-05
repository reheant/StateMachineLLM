from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from util import call_gpt4
from util import extract_states_events_table
from util import extract_parallel_states_table

class ParallelStateSearchAction(BaseAction):
    name: str = "parallel_state_search_action"
    args: dict = {}
    usage: str = "Identify all parallel regions of the state machine from the system description"
    description: str = ""
    
    def send_parallel_state_search(self, system_name :str, state_event_table: str):
        """
        send the parallel states prompt to GPT 4 for a given system and problem description alongside the state and events tables. 
        maximum retries indicates the amount of times that the prompt should be resent in the event that one of the tables are not provided
        """

        system_name, state_event_table = self.belief.get('state_event_search_action')

        prompt = f""" 
            You are an AI assistant specialized in identifying parallel regions in a state machine from a problem description and a table that lists all the states and events of the state machine. The definition of a parallel state is:
            A parallel state is a state that is divided into separate regions. Each region contains more substates.  When a parallel state is entered, each of the regions are also entered; their initial states are entered and so on, parallel states are used when the machine needs to combine several discrete behaviors at the same time.
            
            Your goal is to parse through problem description and table of states and events to identify events that occur independently but concurrently as this will help you to identify if a parallel state exists.

            Note that a state machine may not have parallel states so ensure that the parallel state that you are outputting is one that follows the guidelines above and is not already encapsulated by a state. Furthermore, make sure that the state that you are outputting makes sense in the context about the object that you are modeling. 
            Note that parallel states are not common and should be used sparingly, and ONLY if needed. If there is no need for parallel states, then output the string EMPTY. If you have identified the need for a parallel state, you MUST add the Parallel States and its substates in an HTML table with the following format and headers:
            ```html <table border="1"> <tr> <th>Parallel State</th> <th>Substate</th> </tr> </table> ```
            

            If there are parallel states, identify the events that take place concurrently. To do this, update the provided HTML table describing states and events. place the states that the events are being performed on under a parallel state with a state name that encompasses the behavior of such a state and identify the events that causes the state machine to enter and leave the parallel state to.  
            To do this, update the states and events accordingly using the HTML table columns below. You MUST use the exact columns provided below and build off of the states and events table provided. If there are no parallel states, then return the original states and events table that you are provided in this prompt.
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> </table> ```                          
        

            Example 1:
            
            Inputs:

            The system description:
            The printer has a master switch which turns the printer on or off. Once the printer is turned on, a user needs to log in before being able to print or scan a document. To login, a user taps her/his printer card on the printer's card reader. Each printer card has a unique ID. If the printer card is authorized, the user can either choose "scan" or "print". If the printer card is not authorized, a login error message is shown. For the "print" option, the user presses the start button to print the user's first document in the user's print queue. If there is no document in the print queue, an error message is shown instead of performing the printing task. For the "scan" option, the user presses the start button for the printer to scan an original document, which was placed by the user in the automatic page feeder. The scan is sent to the user's email inbox. If the printer does not detect an original document, an error message is shown instead of performing the scanning task. When the printer is done printing or scanning, the user can print or scan the next document. The user may also stop the printing/scanning task at any time by pressing the stop button. The user is allowed to logoff either before or after a printing/scanning task but not while the printer is in the middle of a printing/scanning task. If there is a paper jam, the printer will suspend the printing/scanning task to allow the user to clear the paper jam. The user may then either cancel the printing/scanning task or resume it. In case the printer runs out of paper during a printing task, the printer suspends the printing task to allow the user to resupply paper. The user may then either cancel the printing task or resume it.   
            
            The system you are modeling: 
            Printer with integrated scanner

            The original HTML table descibing the states and events is:
            <table border="1"><tr><th>Current State</th><th>Event</th><th>Next State(s)</th></tr><tr><td>Off</td><td>Turn On</td><td>On</td></tr><tr><td>On</td><td>Turn Off</td><td>Off</td></tr><tr><td>Idle</td><td>User Login with Unauthorized Card</td><td>Idle</td></tr><tr><td>Idle</td><td>User Login with Authorized Card</td><td>Ready</td></tr><tr><td>Ready</td><td>User Logoff</td><td>Idle</td></tr><tr><td>Ready</td><td>Start Scan without Document</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Start Print with Empty Queue</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Select Scan Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Select Print Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Start Scan with Document Loaded</td><td>ScanAndEmail</td></tr><tr><td>Ready</td><td>Start Print with Document in Queue</td><td>Print</td></tr><tr><td>ScanAndEmail</td><td>Scan Complete</td><td>Ready</td></tr><tr><td>Print</td><td>Out of Paper</td><td>Suspended</td></tr><tr><td>Print</td><td>Paper Jam</td><td>Suspended</td></tr><tr><td>Print</td><td>Stop Printing</td><td>Ready</td></tr><tr><td>Print</td><td>Print Complete</td><td>Ready</td></tr><tr><td>Suspended</td><td>Cancel Task</td><td>Ready</td></tr><tr><td>Suspended</td><td>Resume Task</td><td>Previous State (Print or Scan)</td></tr></table>

            Output:
            NO PARALLEL STATES

            Example 2:

            The system description:
            {self.description}
            The system you are modeling: 
            {system_name}
            The original HTML table descibing the states and events is:
            {state_event_table}

            Output:
            
        """
        
        retries = 0
        retry = True
        
        # call GPT 4 while we should retry and we haven't reached max retries
        while retries < 5 and retry:
            response = call_gpt4(prompt)
            updated_state_event_table = extract_states_events_table(llm_response=response)
            
            if ("EMPTY" in response):
                return (updated_state_event_table, None)
            # extract tables

            updated_parallel_state_table = extract_parallel_states_table(llm_response=response)
            updated_tables = (updated_state_event_table, updated_parallel_state_table)
            # if any of the tables are not provided, try again
            if None in updated_tables:
                retry = True
            else:
                retry = False
            
            retries += 1
        
        return updated_tables
    
    def execute(self):
        """
        the execute function for the parallel state prompt. calls the send_parallel_state_search function and applies the updates to event and states 
        table while also generating the output table for the parallel states
        """
        print(f"Running {self.name}...")
        system, state_event_table = self.belief.get('state_event_search_action')
        
        # the parallel state search response returns an updated state/event table (required), and a parallel_state table (optional)
        updated_state_event_table, parallel_state_table = self.send_parallel_state_search(system, state_event_table)
        

        # the state event table must be updated, so if the LLM does not return it throw an error so the state machine will try again
        if updated_state_event_table is None:
            raise Exception(f"Max retries reached for ParallelRegionSearchAction")
        
        # if no parallel state table is returned, log a message warning that no parallel states were found
        if parallel_state_table is None:
            print(f"No parallel states found")
        
        # state_event_table will never be None, parallel_state_table may be None if there are no parallel states
        return state_event_table, parallel_state_table
            

