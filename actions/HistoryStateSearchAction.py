from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_transitions_guards_table
from bs4 import Tag

class HistoryStateSearchAction(BaseAction):
    name: str = "history_state_search_action"
    args: dict = {}
    usage: str = "Identify all history states for hierarchical states in the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")
        hierarchical_states_table, transition_table = self.belief.get('hierarchical_state_search_action')
        modeled_system, _ = self.belief.get('state_event_search_action')
       
        prompt = f'''
        You are an AI assistant specialized in creating state machines.
        
        Objective:
        Given the system description, system being modeled and the hierarchical states table and transitions table, determine whether each parent (composite) state in the hierarchical state machine requires a history state to remember the last active substate after a transition. 

        Definitions:

            •	History State: A mechanism in state machines that allows a composite state to remember its last active substate when re-entered, instead of starting from its initial substate.

        Criteria for Requiring a History State:

            1.	Transitions Targeting the Parent State: A history state is needed if there are transitions to a parent state from outside its hierarchy.
            2.	Resuming Previous Substate: The system’s behavior requires resuming the last active substate rather than starting from the initial substate upon re-entry.

        Instructions:

            1.	Analyze the System:
                Review the system description and the modeled system provided below.
                Identify all parent (composite) states and their substates.
            2.	Identify Transitions:
                Find all transitions that target parent states from outside their hierarchy.
                Determine if these transitions should resume at the last active substate.
            3.	Determine the Need for History States:
                For each parent state, decide if a history state is required based on the criteria.
            4.	Output Format:
                If no history states are required, output: NONE.
                If history states are required, update the transitions table to include the history state by appending another row that includes the history state:
            
        
        Example 1:

        The system description: 
        The printer has a master switch which turns the printer on or off. Once the printer is turned on, a user needs to log in before being able to print or scan a document. To login, a user taps her/his printer card on the printer's card reader. Each printer card has a unique ID. If the printer card is authorized, the user can either choose "scan" or "print". If the printer card is not authorized, a login error message is shown. For the "print" option, the user presses the start button to print the user's first document in the user's print queue. If there is no document in the print queue, an error message is shown instead of performing the printing task. For the "scan" option, the user presses the start button for the printer to scan an original document, which was placed by the user in the automatic page feeder. The scan is sent to the user's email inbox. If the printer does not detect an original document, an error message is shown instead of performing the scanning task. When the printer is done printing or scanning, the user can print or scan the next document. The user may also stop the printing/scanning task at any time by pressing the stop button. The user is allowed to logoff either before or after a printing/scanning task but not while the printer is in the middle of a printing/scanning task. If there is a paper jam, the printer will suspend the printing/scanning task to allow the user to clear the paper jam. The user may then either cancel the printing/scanning task or resume it. In case the printer runs out of paper during a printing task, the printer suspends the printing task to allow the user to resupply paper. The user may then either cancel the printing task or resume it.   
            
        The system you are modeling: 
        Printer with integrated scanner

        Hierarchical state table:
        <table border="1"><tr><th>Superstate</th><th>Substate</th></tr><tr><td>Printer</td><td>Off</td></tr><tr><td>Printer</td><td>On</td></tr><tr><td>On</td><td>Idle</td></tr><tr><td>On</td><td>Ready</td></tr><tr><td>On</td><td>Busy</td></tr><tr><td>On</td><td>Suspended</td></tr><tr><td>Busy</td><td>ScanAndEmail</td></tr><tr><td>Busy</td><td>Print</td></tr></table>

        Transitions table: 
        <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login(cardID)</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr><tr><td>Idle</td><td>Ready</td><td>login(cardID)</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan" && !originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print" && !documentInQueue()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan" && originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print" && documentInQueue()</td><td>NONE</td></tr><tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr></table>

        Output:

        Changes made:
        Busy has a history state and so the table is updated to include the resume transition from Suspended to Busy.H

        Updated transition table:        
        <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login(cardID)</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr><tr><td>Idle</td><td>Ready</td><td>login(cardID)</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan" && !originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print" && !documentInQueue()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan" && originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print" && documentInQueue()</td><td>NONE</td></tr><tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy.H</td><td>resume</td><td>NONE</td><td>NONE</td></tr></table>

        Example 2:

        The system description:
        {self.description}

        The system you are modeling: 
        {modeled_system}

        Hierarchical state table:
        {hierarchical_states_table}

        Transitions table:
        {transition_table}

        Updated transition table:

        '''
        
        answer = call_gpt4(prompt)
        
        if "NONE" in answer:
            return transition_table
        else:
            return extract_transitions_guards_table(answer, True)

