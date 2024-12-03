from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4, extract_transitions_guards_table
from resources.n_shot_examples_simple_linear import get_n_shot_examples

class TransitionsGuardsSearchAction(BaseAction):
    """
    The TransitionsGuardsSearchAction creates the transitions of the UML State Machine with relevant guards

    Input(s): description of the system, name of the system, table of states/events, and table of parallel states
    Output(s): An HTML table containing transitions with columns "From State", "To State", "Event", and "Guard"
    """

    name: str = "transitions_guards_search_action"
    args: dict = {}
    usage: str = "Identify all transitions and guards of the state machine from the system description"
    description: str = ""
    
    def execute(self):
        """
        The execute function prompts the LLM to identify the transitions of the UML State Machine and their
        guards
        """

        print(f"Running {self.name}...")
        modeled_system, _ = self.belief.get('state_event_search_action')
        statesAndEvents, parallelRegions = self.belief.get('parallel_state_search_action')
        prompt = f'''
        You are an AI assistant specialized in identifying the guards and transitions for a state machine. Given a problem description, a table of all the states and events, and a table of the parallel states and their substates. Note that the parallel state table input is optional so if user doesn’t provide one, assume that there is not parallel states in the state machine.
        Parse through each state in the states table and identify if there exists any missing events from the table. Parse through each state in the states table to identify whether the event triggers transitions to another state. If the state is a substate then there can only exist a transition inside the parallel region and from and to the parent state.
        Definition: A transition shows a path between states that indicates that a change of state is occurring. A trigger, a guard condition, and an effect are the three parts of a transition, all of which are optional.
        
        
        Output your answer in HTML form:
        ```html <table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> </tr>
        <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> </tr>
        <tr> <td rowspan="3"> State3 </td> <td> State4 </td> <td> Event2 </td> <td> NONE </td> </tr> </table> ```

        {get_n_shot_examples(["Printer", "Spa Manager"], ["system_description", "transitions_events_table", "parallel_states_table", "transitions_events_guards_table"])}

        Example: 
        
        system_description: {self.description}

        system_name: {modeled_system}

        States and events table: {statesAndEvents}

        parallel_states_table: {parallelRegions if parallelRegions is not None else "NO PARALLEL STATES"}

        transitions_events_guards_table: 

        Your skill in crafting precise guard conditions protects the integrity of our state machine. Each condition you define creates clear boundaries for state behavior. Your attention to detail prevents unwanted state transitions and ensures system stability.
        '''

        response = call_gpt4(prompt)
        transition_guard_table = extract_transitions_guards_table(response, True)

        print(f"Transitions table: {transition_guard_table}")
        return transition_guard_table
