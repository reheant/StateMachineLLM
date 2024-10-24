from sherpa_ai.actions.base import BaseAction

class SanityCheckAction(BaseAction):
    name: str = "sanity_check_action"
    args: dict = {
                  "system_description": "A detailed paragraph description of the system that the generated UML state machine represents (str)", 
                  "state_event_table": "An HTML table describing states and events of the generated UML state machine for the system description. Contains Current State, Event, and Next State(s) columns (str)",
                  "parallel_state_table": "An HTML table describing the parallel states of the generated UML state machine for the system description. Contains Parallel State, Substate, and Reference from Problem Description columns (str)",
                  "transitions_table": "An HTML table describing the transitions of the generated state UML state machine for the system description. Contains From State, To State, Event, Guard, Entry Action, and Exit Action columns (str)" 
                 }
    usage: str = "Confirm that sentences from the system description are captured in the generated state machine represented by HTML tables"

    def execute(self, problem_description: str, state_event_table: str, parallel_state_table: str, transitions_table: str):
        print(f"Hello sanity_check_action")
        return f"Event 1, Event 2"
