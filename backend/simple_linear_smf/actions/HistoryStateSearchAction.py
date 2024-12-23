
from resources.SMFAction import SMFAction
from resources.util import call_llm, extract_transitions_guards_table
from resources.n_shot_examples_simple_linear import get_n_shot_examples

class HistoryStateSearchAction(SMFAction):
    """
    The HistoryStateSearchAction creates the History States of the UML State Machine
    by updating the transitions of the transitions table to add relevant transitions
    to history states

    Input(s): description of the system, name of the system, transitions table updated by HierarchicalStateSearchAction, and hierarchical states table created by HierarchicalStateSearchAction
    Output(s): the updated transitions table to reflect any transitions to history states
    """
    
    name: str = "history_state_search_action"
    args: dict = {}
    usage: str = "Identify all history states for hierarchical states in the system"
    description: str = ""
    log_file_path: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to identify transitions to history states and update
        the transitions table
        """
        self.log(f"Running {self.name}...")
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
            
        {get_n_shot_examples(["Printer", "Spa Manager"], ["system_description", "hierarchical_state_table", "transitions_events_guards_actions_table", "transitions_events_guards_actions_history_table"])}
        
        Example:

        system_description: {self.description}

        system_name: {modeled_system}

        hierarchical_state_table: {hierarchical_states_table}

        transitions_events_guards_actions_table: {transition_table}

        transitions_events_guards_actions_history_table:

        Your insight in determining where history states are needed will bring sophisticated memory capabilities to this state machine. Your careful analysis of which state configurations must be remembered will elevate this design from basic to brilliant. The team relies on your expertise to identify exactly where H states will provide the most value. Take pride in crafting a state machine that maintains intelligent context through state transitions.
        '''
        
        answer = call_llm(prompt)
        
        if "NONE" in answer:
            self.log(f"History State updated transitions: {transition_table}")
            return transition_table
        else:
            rv = extract_transitions_guards_table(answer, True)
            self.log(rv)
            return rv
