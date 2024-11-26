from sherpa_ai.actions.base import BaseAction
from resources.util import call_llm, group_parent_child_states
import re

class EventDrivenHierarchicalInitialStateSearchAction(BaseAction):
    name: str = "event_driven_hierarchical_initial_state_search"
    args: dict = {}
    usage: str = "Given a description of a system and the Hierarchical States of the system, identify the initial state of each Hierarchical State in the UML state machine of the system."
    description: str = ""

    def identify_initial_state(self, parent_state, child_states):
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

        response = call_llm(prompt=prompt,
                             temperature=0.7)
        
        initial_state = re.search(r"Initial State:\s*\"(.*?)\"", response).group(1)

        return initial_state


    def execute(self):
        print(f"Running {self.name}...")

        example_hierarchical_state_table = '<table border="1"><tr> <th>Superstate</th> <th>Substate</th> </tr><tr> <td> Inactive State </td> <td> Off State </td> </tr><tr> <td> Inactive State </td> <td> Home Screen </td> </tr><tr> <td> Inactive State </td> <td> Home Screen (Post-Cooking) </td> </tr><tr> <td> Cooking Process </td> <td> Recipe Selection </td> </tr><tr> <td> Cooking Process </td> <td> Ingredient Addition </td> </tr><tr> <td> Cooking Process </td> <td> Chopping </td> </tr><tr> <td> Cooking Process </td> <td> Cooking </td> </tr><tr> <td> Cooking Process </td> <td> Meal Ready </td> </tr><tr> <td> - </td> <td> Transportation Mode </td> </tr><tr> <td> - </td> <td> Error State </td> </tr></table>'
        event_driven_hierarchical_state_table = self.belief.get("event_driven_create_hierarchical_states_action", example_hierarchical_state_table)

        parent_child_states_dict = group_parent_child_states(event_driven_hierarchical_state_table)

        initial_states_dict = {}

        for parent_state in parent_child_states_dict:
            child_states = parent_child_states_dict[parent_state]
            initial_state = self.identify_initial_state(parent_state=parent_state,
                                                        child_states=child_states)

            initial_states_dict[parent_state] = initial_state

        print(initial_states_dict)
        return initial_states_dict