from sherpa_ai.actions.base import BaseAction

class HierarchicalStateSearchAction(BaseAction):
    name: str = "hierarchical_state_search_action"
    args: dict = {}
    usage: str = "Identify all hierarchical states in the system"

    def execute(self):
        print(f"Hello hierarchical_state_search_action")
        return f"Event 1, Event 2"
