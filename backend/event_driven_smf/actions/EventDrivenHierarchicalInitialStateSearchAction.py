from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, group_parent_child_states
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
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the name of the system you are modeling a state machine for, the description of the state machine, a superstate identified, and its associated substates.
        Your task is to determine the initial state of the superstate when the system enters the superstate.

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. For the provided superstate and substates, determine which substate is the Initial State of its superstate. Your answer MUST be in the following format:
        
        <superstate_initial_state>InitialState</superstate_initial_state>

        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'superstate_inspected', 'substates_inspected', 'superstate_initial_state'])}

        Here is your input:
        system_name:
        <system_name>{system_name}</system_name>

        system_description:
        <system_description>{self.description}</system_description>

        superstate_inspected:
        <superstate_inspected>{parent_state}</superstate_inspected>
        
        substates_inspected:
        <substates_inspected>{formatted_child_states}</substates_inspected>
        
        superstate_initial_state:
        """

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        superstate_initial_state_search = re.search(r"<superstate_initial_state>(.*?)</superstate_initial_state>", response)

        if superstate_initial_state_search:
            superstate_initial_state = superstate_initial_state_search.group(1)
        else:
            superstate_initial_state = "NOT FOUND"
        print(superstate_initial_state)


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