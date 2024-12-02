from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4, extract_hierarchical_state_table, extract_transitions_guards_actions_table
from resources.n_shot_examples_simple_linear import get_n_shot_examples

class HierarchicalStateSearchAction(BaseAction):
    """
    The HierarchicalStateSearchAction creates the Hierarchical State of the UML State Machine from the system description,
    and updates the transitions table to reflect the new parent states

    Input(s): description of the system, name of the system, and transitions table created by ActionSearchAction
    Output(s): An HTML table containing the Hierarchical states and its child states, and the updated transitions table to reflect the new Hierarchical States
    """

    name: str = "hierarchical_state_search_action"
    args: dict = {}
    usage: str = "Identify all hierarchical states in the system"
    description: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to create hierarchical states and update transitions using a 2-shot prompting approach
        """
        
        print(f"Running {self.name}...")

        modeled_system, _ = self.belief.get('state_event_search_action')
        transitions_table = self.belief.get('action_search_action')
        prompt = f'''You are an AI assistant specialized in analyzing and optimizing state machines and state diagrams. You will be provided with a table that lists transitions between states, including the originating state, destination state, triggering event, associated action, and any guard conditions.

        Determine Parent States:
        Given a state transition table with states and their transitions, identify parent (hierarchical) states that encapsulate the logic of the original states. Produce an optimized state machine by removing redundancies.

        Instructions:

            1.	Analyze the Input Transition Table:
                Examine the transitions to identify states that can be logically grouped based on similar transitions or behaviors.
                Look for guard conditions that apply to multiple transitions; this can help in determining parent states.
            2.	Determine Parent States:
                Identify states that encapsulate or logically group other states based on their transitions.
                Parent states should manage how their child states transition to other states and encapsulate common behaviors.
            3.	Remove Redundancies:
                After identifying parent states, eliminate any redundant transitions, guard conditions, actions, states, and events that are no longer necessary.
                Ensure that the optimized state machine maintains the same overall behavior as the original.
            4.	Produce the Optimized State Machine:
                Update the transition table to reflect the introduction of parent states and the removal of redundancies.
                Ensure consistency and correctness in the transitions and states.
                In the end you need to output 2 html tables with the following format:
        
        {get_n_shot_examples(["Printer", "Spa Manager"], ["system_description", "transitions_events_guards_table", "hierarchical_state_table", "transitions_events_guards_table"])}

        Example:

        The system description: {self.description}

        The system you are modeling: {modeled_system}

        The transitions table: {transitions_table}

        Parent state table:

        Updated transitions table: 
        '''
        answer = call_gpt4(prompt)
        hierarchical_state_table = extract_hierarchical_state_table(answer)
        updated_transitions_table = extract_transitions_guards_actions_table(answer)

        print(f"Hierarchical State Table: {hierarchical_state_table}")
        print(f"Updated Transitions State Table: {updated_transitions_table}")
        return hierarchical_state_table, updated_transitions_table
