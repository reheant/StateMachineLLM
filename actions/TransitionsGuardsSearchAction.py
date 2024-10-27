from sherpa_ai.actions.base import BaseAction
from util import call_gpt4

class TransitionsGuardsSearchAction(BaseAction):
    name: str = "transitions_guards_search_action"
    args: dict = {}
    usage: str = "Identify all transitions and guards of the state machine from the system description"

    def execute(self):
        print(f"Hello transitions_guards_search_action")
        transitions = []
        for state in states:
            for event in events:
                prompt = f'''You are an AI assistant specialized in creating state machines. Given the following problem description {problem_desc}, the following derived state {state}, the following derived event {event}:
                    Identify if the event {event} triggers transitions for the state {state}.
                    If one or more transitions should be triggered for the state {state} because of the event {event}, then you should also specify if there are conditions in addition to the event for the transition to trigger.
                    Output your answer in a table format with the following columns: Destination state for the transition, additional condition for the event to trigger the transition, Sentences in the problem description that implied the information (max 3)
                    Then group all of the rows from all of the iterations of the nested for loop in a larger table for all transitions.'''
                transitions.append(call_gpt4(prompt))
        return f"Event 1, Event 2"
