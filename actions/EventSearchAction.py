from sherpa_ai.actions.base import BaseAction
from util import call_gpt4

class EventSearchAction(BaseAction):
    name: str = "event_search_action"
    args: dict = {}
    usage: str = "Identify all events that trigger transitions between states in the system"

    def execute(self):
        print(f"Hello event_search_action")
        msg = call_gpt4("What is Capital of France?")
        print(msg)
        return f"Event 1, Event 2"
