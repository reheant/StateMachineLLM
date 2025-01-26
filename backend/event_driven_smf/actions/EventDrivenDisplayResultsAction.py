from resources.SMFAction import SMFAction
from resources.environmental_impact.impact_tracker import tracker

class EventDrivenDisplayResultsAction(SMFAction):
    """
    The EventDrivenDisplayResultsAction displays all tables at the end of
    the state machine creation process: the table of all states, the initial
    state of the system, the initial state of each hierarchical state, and the
    transitions of the UML state machine
    """

    name: str = "event_driven_display_results_action"
    args: dict = {}
    usage: str = "Display the results of the SMF"
    log_file_path: str = ""

    def execute(self):
        """
        The execute function prints the states, initial states, and transitions
        of the UML state machine to the console
        """
        
        self.log(f"Running {self.name}...")

        event_driven_hierarchical_states_table = self.belief.get("event_driven_create_hierarchical_states_action")
        self.log(f"Hierarchical States Table:\n{event_driven_hierarchical_states_table}")

        event_driven_initial_state = self.belief.get("event_driven_initial_state_search_action")
        self.log(f"Initial System State: {event_driven_initial_state}")

        event_driven_hierarchical_initial_states = self.belief.get("event_driven_hierarchical_initial_state_search")
        self.log(f"Hierarchical Initial States:\n{event_driven_hierarchical_initial_states}")

        event_driven_transitions = self.belief.get("event_driven_history_state_search_action")
        self.log(f"Transitions:\n{event_driven_transitions}")

        transitionsParallelRegionsTuple = self.belief.get('event_driven_parallel_regions_search_action')
        self.log(f"Parallel Regions:\n{transitionsParallelRegionsTuple[1]}")
        self.log("\nEnvironmental Assessment:")
        self.log(f"Total Completion Tokens: {tracker.total_completion_tokens}")
        self.log(f"Total Carbon Emissions: {tracker.carbon_emissions} kgCO2eq")
        self.log(f"Total Energy Use: {tracker.energy_consumed} kWh")
        self.log(f"Total Abiotic Resource Use: {tracker.abiotic_resource_depletion} gSbeq")
        self.log("\n")
