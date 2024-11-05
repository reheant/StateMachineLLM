from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_transitions_guards_table, appendTables, extractColumn

class TransitionsGuardsSearchAction(BaseAction):
    name: str = "transitions_guards_search_action"
    args: dict = {}
    usage: str = "Identify all transitions and guards of the state machine from the system description"
    description: str = ""

    def multiplePrompting(self, description):
        transitions = []
        modeled_system, statesAndEvents = self.belief.get('state_event_search_action')
        states = extractColumn(statesAndEvents, 0)
        states.extend(extractColumn(statesAndEvents, 2))
        states = list(set(states))
        events = extractColumn(statesAndEvents, 1)
        for state in states:
            for event in events:
                print(f'{state}, {event}')
                prompt = f'''
                You are an AI assistant specialized in identifying transitions in a state machine from a problem description and a table that lists all the states and events of the state machine. Given the following definition of a transition:
                Definition: A transition shows a path between states that indicates that a change of state is occurring. A trigger, a guard condition, and an effect are the three parts of a transition, all of which are optional.

                The system description:
                {description}
                The system you are modeling: 
                {modeled_system}
                
                Your task is to find transitions for the following derived state {state}, and the following derived event {event}. Identify if the event {event} triggers transitions for the state {state}.
                If one or more transitions should be triggered for the state {state} because of the event {event}, then you should also specify if there are conditions in addition to the event for the transition to trigger.

                Note that a state,event pair may not result in the creation of a new transition. In this case output ONLY the string: NONE. 
                Otherwise, output your answer in HTML form:
                <table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> </tr>
                <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> </tr>
                <tr> <td rowspan="3"> State3 </td> <td> State4 </td> <td> Event2 </td> <td> NONE </td> </tr> </table>  

                '''
                transitions.append(call_gpt4(prompt))

        final_transition_table = ''
        for i in range(len(transitions)):
            mid_table =  extract_transitions_guards_table(transitions[i], i == 0)
            final_transition_table = appendTables(final_transition_table, mid_table)

        return final_transition_table
    
    def execute(self):
        print(f"Running {self.name}...")
        modeled_system, _ = self.belief.get('state_event_search_action')
        statesAndEvents, parallelRegions = self.belief.get('parallel_state_search_action')
        prompt = f'''
        You are an AI assistant specialized in identifying the guards and transitions for a state machine. Given a problem description, a table of all the states and events, and a table of the parallel states and their substates. Note that the parallel state table input is optional so if user doesn’t provide one, assume that there is not parallel states in the state machine.
        Parse through each state in the states table and identify if there exists any missing events from the table. Parse through each state in the states table to identify whether the event triggers transitions to another state. If the state is a substate then there can only exist a transition inside the parallel region and from and to the parent state.
        Definition: A transition shows a path between states that indicates that a change of state is occurring. A trigger, a guard condition, and an effect are the three parts of a transition, all of which are optional.
        
        
        Output your answer in HTML form:
        ```html <table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> </tr>
        <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> </tr>
        <tr> <td rowspan="3"> State3 </td> <td> State4 </td> <td> Event2 </td> <td> NONE </td> </tr> </table> ```

        Example 1:

        The system description: 
        The printer has a master switch which turns the printer on or off. Once the printer is turned on, a user needs to log in before being able to print or scan a document. To login, a user taps her/his printer card on the printer's card reader. Each printer card has a unique ID. If the printer card is authorized, the user can either choose "scan" or "print". If the printer card is not authorized, a login error message is shown. For the "print" option, the user presses the start button to print the user's first document in the user's print queue. If there is no document in the print queue, an error message is shown instead of performing the printing task. For the "scan" option, the user presses the start button for the printer to scan an original document, which was placed by the user in the automatic page feeder. The scan is sent to the user's email inbox. If the printer does not detect an original document, an error message is shown instead of performing the scanning task. When the printer is done printing or scanning, the user can print or scan the next document. The user may also stop the printing/scanning task at any time by pressing the stop button. The user is allowed to logoff either before or after a printing/scanning task but not while the printer is in the middle of a printing/scanning task. If there is a paper jam, the printer will suspend the printing/scanning task to allow the user to clear the paper jam. The user may then either cancel the printing/scanning task or resume it. In case the printer runs out of paper during a printing task, the printer suspends the printing task to allow the user to resupply paper. The user may then either cancel the printing task or resume it.   
            
        The system you are modeling: 
        Printer with integrated scanner

        State and Events Table: 
        <table border="1"><tr><th>Current State</th><th>Event</th><th>Next State(s)</th></tr><tr><td>Off</td><td>Turn On</td><td>On</td></tr><tr><td>On</td><td>Turn Off</td><td>Off</td></tr><tr><td>Idle</td><td>User Login with Unauthorized Card</td><td>Idle</td></tr><tr><td>Idle</td><td>User Login with Authorized Card</td><td>Ready</td></tr><tr><td>Ready</td><td>User Logoff</td><td>Idle</td></tr><tr><td>Ready</td><td>Start Scan without Document</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Start Print with Empty Queue</td><td>Ready (Error)</td></tr><tr><td>Ready</td><td>Select Scan Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Select Print Option</td><td>Ready</td></tr><tr><td>Ready</td><td>Start Scan with Document Loaded</td><td>ScanAndEmail</td></tr><tr><td>Ready</td><td>Start Print with Document in Queue</td><td>Print</td></tr><tr><td>ScanAndEmail</td><td>Scan Complete</td><td>Ready</td></tr><tr><td>Print</td><td>Out of Paper</td><td>Suspended</td></tr><tr><td>Print</td><td>Paper Jam</td><td>Suspended</td></tr><tr><td>Print</td><td>Stop Printing</td><td>Ready</td></tr><tr><td>Print</td><td>Print Complete</td><td>Ready</td></tr><tr><td>Suspended</td><td>Cancel Task</td><td>Ready</td></tr><tr><td>Suspended</td><td>Resume Task</td><td>Previous State (Print or Scan)</td></tr></table>

        Parallel Regions Table:
        No Parallel Regions

        Output:

        Output of HTML Transition Table:
        <table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th></tr><tr><td>Off</td><td>On</td><td>on</td><td>NONE</td></tr><tr><td>On</td><td>Off</td><td>off</td><td>NONE</td></tr><tr><td>Idle</td><td>Idle</td><td>login</td><td>!idAuthorized(cardID)</td></tr><tr><td>Idle</td><td>Ready</td><td>login</td><td>idAuthorized(cardID)</td></tr><tr><td>Ready</td><td>Idle</td><td>logoff</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="scan"&&!originalLoaded()</td></tr><tr><td>Ready</td><td>Ready</td><td>start</td><td>action=="print"&&!documentInQueue()</td></tr><tr><td>Ready</td><td>Ready</td><td>scan</td><td>NONE</td></tr><tr><td>Ready</td><td>Ready</td><td>print</td><td>NONE</td></tr><tr><td>Ready</td><td>ScanAndEmail</td><td>start</td><td>action=="scan"&&originalLoaded()</td></tr><tr><td>Ready</td><td>Print</td><td>start</td><td>action=="print"&&documentInQueue()</td></tr><tr><td>Print</td><td>Suspended</td><td>outOfPaper</td><td>NONE</td></tr><tr><td>Print</td><td>Suspended</td><td>jam</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>stop</td><td>NONE</td></tr><tr><td>Print</td><td>Ready</td><td>done</td><td>NONE</td></tr><tr><td>Suspended</td><td>Ready</td><td>cancel</td><td>NONE</td></tr><tr><td>Suspended</td><td>Busy (history)</td><td>resume</td><td>NONE</td></tr></table>

        Example 2: 
        
        The system description:
        {self.description}

        The system you are modeling: 
        {modeled_system}

        States and events table:
        {statesAndEvents}

        Parallel regions table:
        {parallelRegions if parallelRegions is not None else "NO PARALLEL STATES"}

        Output: 

        '''

        response = call_gpt4(prompt)
        transition_guard_table = extract_transitions_guards_table(response, True)

        return transition_guard_table
