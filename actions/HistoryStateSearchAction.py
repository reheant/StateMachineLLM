from sherpa_ai.actions.base import BaseAction

class HistoryStateSearchAction(BaseAction):
    name: str = "history_state_search_action"
    args: dict = {}
    usage: str = "Identify all history states for hierarchical states in the system"

    def execute(self):
        print(f"Hello history_state_search_action")
        return f"Event 1, Event 2"
