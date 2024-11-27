from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4, extract_history_state_table, addColumn, appendTables, gsm_tables_to_dict

class EventDrivenParallelRegionsSearchAction(BaseAction):
    name: str = "event_driven_parallel_regions_search_action"
    args: dict = {}
    usage: str = "Identify Parallel Regions from States and Events"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")

        transitions_table = self.belief.get('event_driven_factor_out_transitions_for_hierarchal_states_action')
        modeled_system = self.belief.get('event_driven_system_name_search_action')
        superstates = [state for state in gsm_tables_to_dict(self.belief.get('event_driven_create_hierarchical_states_action'), transitions_table, None)[0] if isinstance(state, dict)]
        events = self.belief.get('event_driven_event_search_action')

        print(transitions_table)
        print(modeled_system)
        print(superstates)
        print(events)

        return ""