from sherpa_ai.actions.base import BaseAction
from resources.util import refactor_transition_table_with_parent_states

class EventDrivenRefactorTransitionNamesAction(BaseAction):
    """
    The EventDrivenRefactorTransitionNamesAction takes the table of hierarchical states
    and renames all "From States" and "To States" in the transitions table to follow
    the "ParentState.ChildState" syntax, if a "From State" or "To State" has a parent state
    """
    name: str = "event_driven_refactor_transition_names_action"
    args: dict = {}
    usage: str = "Given the hierarchical states and transitions of a UML state machine, refactor the names of the transitions to match the ParentState.ChildState format"


    def execute(self):
        """
        The execute function does not prompt the LLM to rename the "From States" and "To States" table
        entries. Rather, the execute function calls the refactor_transition_table_with_parent_states
        util function to perform the renaming. The output of this action is the table of transitions, 
        with the "From State" and "To State" column entries renamed in the format "ParentState.ChildState"
        """

        print(f"Running {self.name}...")

        event_driven_hierarchical_state_table = self.belief.get("event_driven_create_hierarchical_states_action")
        event_driven_transitions_table = self.belief.get("event_driven_create_transitions_action")

        refactored_event_driven_transitions_table = refactor_transition_table_with_parent_states(transitions_table=event_driven_transitions_table,
                                                                                                 hierarchical_state_table=event_driven_hierarchical_state_table)
        
        print(refactored_event_driven_transitions_table)
        return refactored_event_driven_transitions_table
