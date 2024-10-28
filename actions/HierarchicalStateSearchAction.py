from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_hierarchical_state_table, extract_transitions_guards_actions_table

class HierarchicalStateSearchAction(BaseAction):
    name: str = "hierarchical_state_search_action"
    args: dict = {
                    "description": "A detailed paragraph description of the system that the generated UML state machine represents (str)"
                 }
    usage: str = "Identify all hierarchical states in the system"

    def execute(self, description : str):
        print(f"Running {self.name}...")

        modeled_system, _ = self.belief.get('state_event_search_action')
        transitions_table = self.belief.get('action_search_action')
        prompt = f'''You are an AI assistant specialized in analyzing and optimizing state machines and state diagrams. You will be provided with a table that lists transitions between states, including the originating state, destination state, triggering event, associated action, and any guard conditions.

        Determine Parent States:
        Look for states that encapsulate or logically group other states based on their transitions, if their transition are similar
        Parent states usually contain groups of related transitions or behaviors and manage how their child state transitions to other states
        Consider guard conditions that apply to multiple transitions for child states this will help determine the parent states.
        
        The system description:
        {description}
        The system you are modeling: 
        {modeled_system}
        Input transitions table:
        {transitions_table}
        
        Understand and analyze the input transition table to produce the Optimized State Machine:
        Remove Redundancies: After identifying the parent states, eliminate any redundant transitions, guards, actions, states, and events that are no longer necessary after identifying the parent states.
        
        In the end you need to output 2 html tables with the following format:
        Table1:
        ```html <table border="1"> 
        <tr> <th>Superstate</th> <th>Substate</th> </tr> 
        <tr> <td> State1 </td> <td> State2 </td> </tr> 
        <tr> <td> State3 </td> <td> State4 </td> </tr>
        </table> ```

        Table2:
        ```html <table border="1"> 
        <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> <th>Action</th> </tr> 
        <tr> <td> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> <td> Action 1 </td> </tr> 
        <tr> <td> State2 </td> <td> State3 </td> <td> Event1 </td> <td> Condition1 </td> <td> NONE </td> </tr> 
        </table> ```
        '''
        answer = call_gpt4(prompt)
        hierarchical_state_table = extract_hierarchical_state_table(answer)
        updated_transitions_table = extract_transitions_guards_actions_table(answer)
        return hierarchical_state_table, updated_transitions_table
