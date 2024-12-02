from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, extract_hierarchical_state_table

class EventDrivenCreateHierarchicalStatesAction(BaseAction):
    name: str = "event_driven_create_hierarchical_states_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the transitions of the system, identify all Hierarchical States in the UML state machine of the system."
    description: str = ""

    def execute(self):
        print(f"Running {self.name}")
        
        
        system_name = self.belief.get("event_driven_system_name_search_action")
        states_table = self.belief.get("event_driven_state_search_action")
        event_driven_transitions_table = self.belief.get("event_driven_create_transitions_action")

        prompt = f"""
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the name of the system you are modeling a state machine for, the description of the state machine, a table of all identified states of the system, and a table of all transitions of the system.
        Your task is to determine ALL superstat

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Using the transitions in the identified transitions table, determine the superstates and substates of the system (hierarchical state machine). A Hierarchical state machine design captures the commonality by organizing the states as a hierarchy. The states at the higher level in hierarchy perform the common message handling, while the lower level states inherit the commonality from higher level ones and perform the state specific functions.
        3. Your output MUST be a table with the following format:
        
        <hierarchical_table>```html<table border="1"> 
        <tr><th>Superstate</th><th>Substate</th></tr>
        <tr><td>State1</td><td>State2</td></tr> 
        <tr><td>State3</td><td>State4</td></tr>
        <tr><td>-</td><td>State5</td></tr>
        </table>```</hierarchical_table>

        For the solution, ALL states from the original table of identified transitions MUST appear in the "Substate" column EXACTLY ONCE; otherwise, your solution will be rejected. If a state from the original table of identified transitions DOES NOT have a parent state in your design of the Hierarchical State Machine, enter "-" in the "Superstate" column, as demonstrated in the example above.
        
        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'states_table', 'transitions_table', 'hierarchical_table'])}

        Here is your input:
        system_name:
        <system_name>{system_name}</system_name>

        system_description:
        <system_description>{self.description}</system_description>

        states_table:
        <states_table>{states_table}</states_table>
        
        transitions_table:
        <transitions_table>{event_driven_transitions_table}</transitions_table>
        
        hierarchical_table:
        """

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        hierarchical_state_table = None
        if "NO HIERARCHY" not in response:
            hierarchical_state_table = extract_hierarchical_state_table(llm_response=response)
        
        print(hierarchical_state_table)

        return hierarchical_state_table