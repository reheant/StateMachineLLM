from sherpa_ai.actions.base import BaseAction

class ActionSearchAction(BaseAction):
    name: str = "action_search_action"
    args: dict = {}
    usage: str = "Identify all actions for transitions between states in the system"

    def execute(self):
        print(f"Hello action_search_action")
        return f"Event 1, Event 2"
