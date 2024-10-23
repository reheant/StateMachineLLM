from sherpa_ai.actions.base import BaseAction

class StateSearch(BaseAction):
    name: str = "state_search_action"
    args: dict = {}
    usage: str = "Identify all states in the system"

    def execute(self):
        print("The states are: On, Off")
        return "The states are: On, Off"