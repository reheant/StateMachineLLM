from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_hierarchical_state_table, extract_transitions_guards_actions_table

class HierarchicalStateSearchAction(BaseAction):
    name: str = "hierarchical_state_search_action"
    args: dict = {}
    usage: str = "Identify all hierarchical states in the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")

        modeled_system, _ = self.belief.get('state_event_search_action')
        transitions_table = self.belief.get('action_search_action')
        prompt = f'''You are an AI assistant specialized in analyzing and optimizing state machines and state diagrams. You will be provided with a table that lists transitions between states, including the originating state, destination state, triggering event, associated action, and any guard conditions.

        Determine Parent States:
        Given a state transition table with states and their transitions, identify parent (hierarchical) states that encapsulate the logic of the original states. Produce an optimized state machine by removing redundancies.

        Instructions:

            1.	Analyze the Input Transition Table:
                Examine the transitions to identify states that can be logically grouped based on similar transitions or behaviors.
                Look for guard conditions that apply to multiple transitions; this can help in determining parent states.
            2.	Determine Parent States:
                Identify states that encapsulate or logically group other states based on their transitions.
                Parent states should manage how their child states transition to other states and encapsulate common behaviors.
            3.	Remove Redundancies:
                After identifying parent states, eliminate any redundant transitions, guard conditions, actions, states, and events that are no longer necessary.
                Ensure that the optimized state machine maintains the same overall behavior as the original.
            4.	Produce the Optimized State Machine:
                Update the transition table to reflect the introduction of parent states and the removal of redundancies.
                Ensure consistency and correctness in the transitions and states.
                In the end you need to output 2 html tables with the following format:
        
        Example 1:

        The system description: 
        The printer has a master switch which turns the printer on or off. Once the printer is turned on, a user needs to log in before being able to print or scan a document. To login, a user taps her/his printer card on the printer's card reader. Each printer card has a unique ID. If the printer card is authorized, the user can either choose "scan" or "print". If the printer card is not authorized, a login error message is shown. For the "print" option, the user presses the start button to print the user's first document in the user's print queue. If there is no document in the print queue, an error message is shown instead of performing the printing task. For the "scan" option, the user presses the start button for the printer to scan an original document, which was placed by the user in the automatic page feeder. The scan is sent to the user's email inbox. If the printer does not detect an original document, an error message is shown instead of performing the scanning task. When the printer is done printing or scanning, the user can print or scan the next document. The user may also stop the printing/scanning task at any time by pressing the stop button. The user is allowed to logoff either before or after a printing/scanning task but not while the printer is in the middle of a printing/scanning task. If there is a paper jam, the printer will suspend the printing/scanning task to allow the user to clear the paper jam. The user may then either cancel the printing/scanning task or resume it. In case the printer runs out of paper during a printing task, the printer suspends the printing task to allow the user to resupply paper. The user may then either cancel the printing task or resume it.   
            
        The system you are modeling: 
        Printer with integrated scanner

        The transitions table: 
        <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login</td><td>!idAuthorized(cardID)</td></tr><tr><td>Idle</td><td>Ready</td><td>login</td><td>idAuthorized(cardID)</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>jam</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>stop</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>done</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy (history)</td><td>resume</td><td>NONE</td></tr></table>

        Output:

        Parent state table:
        <table border="1"><tr><th>Superstate</th><th>Substate</th></tr><tr><td>Printer</td><td>Off</td></tr><tr><td>Printer</td><td>On</td></tr><tr><td>On</td><td>Idle</td></tr><tr><td>On</td><td>Ready</td></tr><tr><td>On</td><td>Busy</td></tr><tr><td>On</td><td>Suspended</td></tr><tr><td>Busy</td><td>ScanAndEmail</td></tr><tr><td>Busy</td><td>Print</td></tr></table>

        Updated transitions table: 
        <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login(cardID)</td><td>!idAuthorized(cardID)</td><td>NONE</td></tr><tr><td>Idle</td><td>Ready</td><td>login(cardID)</td><td>idAuthorized(cardID)</td><td>action="none";</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan" && !originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print" && !documentInQueue()</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td><td>action="scan";</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td><td>action="print";</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan" && originalLoaded()</td><td>NONE</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print" && documentInQueue()</td><td>NONE</td></tr><tr><td>Busy</td><td>Suspended</td><td>jam</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>stop</td><td>NONE</td><td>NONE</td></tr><tr><td>Busy</td><td>Ready</td><td>done</td><td>NONE</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td><td>NONE</td></tr></table>

        Example 2:

        The system description:
        {self.description}

        The system you are modeling: 
        {modeled_system}

        The transitions table: 
        {transitions_table}

        Output:

        Parent state table:

        Updated transitions table: 
       

        '''
        answer = call_gpt4(prompt)
        hierarchical_state_table = extract_hierarchical_state_table(answer)
        updated_transitions_table = extract_transitions_guards_actions_table(answer)
        return hierarchical_state_table, updated_transitions_table
