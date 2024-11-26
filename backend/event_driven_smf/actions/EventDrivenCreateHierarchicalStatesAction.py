from sherpa_ai.actions.base import BaseAction
from resources.util import call_llm, extract_hierarchical_state_table

class EventDrivenCreateHierarchicalStatesAction(BaseAction):
    name: str = "event_driven_create_hierarchical_states_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the transitions of the system, identify all Hierarchical States in the UML state machine of the system."
    description: str = ""

    def execute(self):
        print(f"Running {self.name}")
        
        
        system_name = self.belief.get("event_driven_system_name_search_action")
        event_driven_transitions_table = self.belief.get("event_driven_create_transitions_action")

        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, the states of the system, and the transitions of the system, your task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        The table of identified transitions is:
        {event_driven_transitions_table}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Using the transitions in the identified transitions table, determine if the state machine can be modified into a Hierarchical State Machine. Hierarchical state machine design captures the commonality by organizing the states as a hierarchy. The states at the higher level in hierarchy perform the common message handling, while the lower level states inherit the commonality from higher level ones and perform the state specific functions.
        3. If the state machine CANNOT be modified into a Hierarchical State Machine, reply with "NO HIERARCHY".
        4. If the state machine CAN be modified into a Hierarchical State Machine, output a table with the following format:
        
        ```html <table border="1"> 
        <tr> <th>Superstate</th> <th>Substate</th> </tr> 
        <tr> <td> State1 </td> <td> State2 </td> </tr> 
        <tr> <td> State3 </td> <td> State4 </td> </tr>
        <tr> <td> - </td> <td> State5 </td> </tr>
        </table> ```

        Your solution MUST be in the above format, otherwise it will be rejected. For the solution, ALL states from the original table of identified transitions MUST appear in the "Substate" column EXACTLY ONCE; otherwise, your solution will be rejected. If a state from the original table of identified transitions DOES NOT have a parent state in your design of the Hierarchical State Machine, enter "-" in the "Superstate" column, as demonstrated in the example above.
        """

        response = call_llm(prompt=prompt,
                             temperature=0.7)
        
        hierarchical_state_table = None
        if "NO HIERARCHY" not in response:
            hierarchical_state_table = extract_hierarchical_state_table(llm_response=response)
        
        print(hierarchical_state_table)

        return hierarchical_state_table