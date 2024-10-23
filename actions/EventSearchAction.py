from sherpa_ai.actions.base import BaseAction

class EventSearch(BaseAction):
    name: str = "event_search_action"
    args: dict = { "system": "the description of the system (str)"}
    usage: str = "Identify all events that trigger transitions between states in the system"

    def execute(self, system: str):
        return f"Identify all events that trigger transitions between states in the following system: \n {system}"
