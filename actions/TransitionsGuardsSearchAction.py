from sherpa_ai.actions.base import BaseAction

class TransitionsGuardsSearchAction(BaseAction):
    name: str = "transitions_guards_search_action"
    args: dict = {}
    usage: str = "Identify all transitions and guards of the state machine from the system description"

    def execute(self):
        print(f"Hello transitions_guards_search_action")
        return f"Event 1, Event 2"
