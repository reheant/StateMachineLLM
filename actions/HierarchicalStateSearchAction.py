from sherpa_ai.actions.base import BaseAction
from util import call_gpt4

class HierarchicalStateSearchAction(BaseAction):
    name: str = "hierarchical_state_search_action"
    args: dict = {}
    usage: str = "Identify all hierarchical states in the system"

    def execute(self):
        hierarchical_state = []
        for state in hierarchical_states:
            prompt = f'''You are an AI assistant specialized in creating state machines. Given the following problem description {problem_desc}: 
            Determine if the hierarchical state {state} requires a history state to remember a past state after a transition.
            Output your answer in a table format containing a single row with the following columns: Does the state {state} require a history state?, Sentences in the problem description that implied the information (max 3)'''
            hierarchical_state.append(call_gpt4(prompt))
        return f"Event 1, Event 2"
