from sherpa_ai.actions.base import BaseAction

class EventDrivenDisplayResultsAction(BaseAction):
    """
    The EventDrivenDisplayResultsAction displays all tables at the end of
    the state machine creation process: the table of all states, the initial
    state of the system, the initial state of each hierarchical state, and the
    transitions of the UML state machine
    """

    name: str = "event_driven_display_results_action"
    args: dict = {}
    usage: str = "Display the results of the SMF"

    def execute(self):
        """
        The execute function prints the states, initial states, and transitions
        of the UML state machine to the console
        """
        
        print(f"Running {self.name}...")

        event_driven_hierarchical_states_table = self.belief.get("event_driven_create_hierarchical_states_action")
        print(f"Hierarchical States Table:\n{event_driven_hierarchical_states_table}")

        event_driven_initial_state = self.belief.get("event_driven_initial_state_search_action")
        print(f"Initial System State: {event_driven_initial_state}")

        event_driven_hierarchical_initial_states = self.belief.get("event_driven_hierarchical_initial_state_search")
        print(f"Hierarchical Initial States:\n{event_driven_hierarchical_initial_states}")

        event_driven_transitions = self.belief.get("event_driven_history_state_search_action")
        print(f"Transitions:\n{event_driven_transitions}")

        transitionsParallelRegionsTuple = self.belief.get('event_driven_parallel_regions_search_action')
        print(f"Parallel Regions:\n{transitionsParallelRegionsTuple[1]}")
