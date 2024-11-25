from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4, extract_transitions_guards_table
from resources.n_shot_examples import get_n_shot_examples

class HistoryStateSearchAction(BaseAction):
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

    def execute(self):
        """
        The execute function prompts the LLM to identify transitions to history states and update
        the transitions table
        """
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
            
        {get_n_shot_examples(["Printer", "Spa Manager"], ["system_description", "hierarchical_state_table", "transitions_events_guards_actions_table", "transitions_events_guards_actions_history_table"])}
        
        Example:

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

