from sherpa_ai.actions.base import BaseAction

class ParallelStateSearchAction(BaseAction):
    name: str = "parallel_state_search_action"
    args: dict = {}
    usage: str = "Identify all parallel regions of the state machine from the system description"

    def execute(self):
        print(f"Hello parallel_state_search_action")
        return f"Event 1, Event 2"
