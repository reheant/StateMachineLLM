from sherpa_ai.actions.base import BaseAction
from util import call_gpt4

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
        problem_description_sentences = problem_description.split(".")
        
        for sentence in problem_description_sentences:
        
            prompt = f"""
                      You are an AI assistant specialized in creating UML state machines. You will be provided with a single sentence from the problem description. Additionally, you will be provided with a table containing states and events, a table containing parallel states, and a table containing transitions of a UML State Machine.
                      Your task is to ensure that the provided sentence is encapsulated by at least one state, transition, guard, action, hierarchical state, and/or history state from the provided tables. If there is no entry in a table that encapsulates the provided sentence, propose a new UML state machine component that will encapsulate the sentence, and add it to its corresponding table. Then, output the updated states and events, parallel states, and transitions tables.
                      The single sentence is:
                      {sentence}
                      The table describing states and events is:
                      {state_event_table}
                      The table describing parallel states is:
                      {parallel_state_table}
                      The table describing transitions is:
                      {transitions_table}
                      """
            response = call_gpt4(prompt)
        
        print(f"Hello sanity_check_action")
        return f"Event 1, Event 2"
