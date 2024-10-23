from sherpa_ai.actions.base import BaseAction

class SanityCheckAction(BaseAction):
    name: str = "sanity_check_action"
    args: dict = {}
    usage: str = "Confirm that sentences from the problem description are captured in the generated state machine"

    def execute(self):
        print(f"Hello sanity_check_action")
        return f"Event 1, Event 2"
