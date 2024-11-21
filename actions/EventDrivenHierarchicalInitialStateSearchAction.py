from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, group_parent_child_states
import re

class EventDrivenHierarchicalInitialStateSearchAction(BaseAction):
    """
    The EventDrivenHierarchicalInitialStateSearchAction prompts the LLM 
    to identify the initial state of each hierarchical state, as identified by the
    EventDrivenCreateHierarchicalStatesAction
    """
    name: str = "event_driven_hierarchical_initial_state_search"
    args: dict = {}
    usage: str = "Given a description of a system and the Hierarchical States of the system, identify the initial state of each Hierarchical State in the UML state machine of the system."
    description: str = ""

    def identify_initial_state(self, parent_state, child_states):
        """
        The identify_initial_state function takes a hierarchical parent state
        and a list of its child states and prompts the LLM to choose an initial state
        of the hierarchical parent state from the list of childstates
        """
        system_name = self.belief.get("event_driven_system_name_search_action")
        formatted_child_states = ", ".join(child_states)

        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system and the Hierarchical States of the system, your task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        The Parent State is:
        {parent_state}

        The Child States of {parent_state} are:
        {formatted_child_states}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. For the provided Parent State and Child States, determine which Child State is the Initial State of its Parent State. Provide the answer in the following format:
        
        Initial State: "Initial State"
        
        The Initial State you output MUST be in the above format, or else your solution will be rejected.
        """

        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        initial_state = re.search(r"Initial State:\s*\"(.*?)\"", response).group(1)

        return initial_state


    def execute(self):
        """
        The execute function uses the table of hierarchical states identified in EventDrivenCreateHierarchicalStatesAction,
        map the parent states to a list of its child states, and prompts the LLM through the identify_initial_state()
        function to find the initial state of each parent hierarchical state
        """
        print(f"Running {self.name}...")

        event_driven_hierarchical_state_table = self.belief.get("event_driven_create_hierarchical_states_action")

        parent_child_states_dict = group_parent_child_states(event_driven_hierarchical_state_table)

        initial_states_dict = {}

        for parent_state in parent_child_states_dict:
            child_states = parent_child_states_dict[parent_state]
            initial_state = self.identify_initial_state(parent_state=parent_state,
                                                        child_states=child_states)

            initial_states_dict[parent_state] = initial_state

        print(initial_states_dict)
        return initial_states_dict