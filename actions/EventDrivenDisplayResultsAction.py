from sherpa_ai.actions.base import BaseAction

class EventDrivenDisplayResultsAction(BaseAction):
    name: str = "event_driven_display_results_action"
    args: dict = {}
    usage: str = "Display the results of the SMF"

    def execute(self):
        print(f"Running {self.name}...")


        event_driven_hierarchical_states_table = self.belief.get("event_driven_create_hierarchical_states_action")

        print(f"Hierarchical States Table:\n{event_driven_hierarchical_states_table}")

        event_driven_initial_state = self.belief.get("event_driven_initial_state_search_action")

        print(f"Initial System State: {event_driven_initial_state}")

        event_driven_hierarchical_initial_states = self.belief.get("event_driven_hierarchical_initial_state_search")

        print(f"Hierarchical Initial States:\n{event_driven_hierarchical_initial_states}")

        event_driven_transitions = self.belief.get("event_driven_refactor_transition_names_action")

        print(f"Transitions:\n{event_driven_transitions}")