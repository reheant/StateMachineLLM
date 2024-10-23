from sherpa_ai.actions.base import BaseAction

class StateSearchAction(BaseAction):
    name: str = "do_search_states"
    args: dict = {}
    usage: str = "identify states in microwave system"

    def execute(self):
        print(f"Hello do_search_states")
        return f"On, Off"