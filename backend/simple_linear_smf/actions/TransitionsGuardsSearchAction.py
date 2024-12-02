from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4, extract_transitions_guards_table, appendTables, extractColumn
from resources.n_shot_examples_simple_linear import get_n_shot_examples

class TransitionsGuardsSearchAction(BaseAction):
    name: str = "transitions_guards_search_action"
    args: dict = {}
    usage: str = "Identify all transitions and guards of the state machine from the system description"
    description: str = ""

    def multiplePrompting(self, description):
        transitions = []
        modeled_system, statesAndEvents = self.belief.get('state_event_search_action')
        states = extractColumn(statesAndEvents, 0)
        states.extend(extractColumn(statesAndEvents, 2))
        states = list(set(states))
        events = extractColumn(statesAndEvents, 1)
        for state in states:
            for event in events:
                print(f'{state}, {event}')
                prompt = f'''
                You are an AI assistant specialized in identifying transitions in a state machine from a problem description and a table that lists all the states and events of the state machine. Given the following definition of a transition:
                Definition: A transition shows a path between states that indicates that a change of state is occurring. A trigger, a guard condition, and an effect are the three parts of a transition, all of which are optional.

                The system description:
                {description}
                The system you are modeling: 
                {modeled_system}
                
                Your task is to find transitions for the following derived state {state}, and the following derived event {event}. Identify if the event {event} triggers transitions for the state {state}.
                If one or more transitions should be triggered for the state {state} because of the event {event}, then you should also specify if there are conditions in addition to the event for the transition to trigger.

                Note that a state,event pair may not result in the creation of a new transition. In this case output ONLY the string: NONE. 
                Otherwise, output your answer in HTML form:
                <table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> </tr>
                <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> </tr>
                <tr> <td rowspan="3"> State3 </td> <td> State4 </td> <td> Event2 </td> <td> NONE </td> </tr> </table>  

                '''
                transitions.append(call_gpt4(prompt))

        final_transition_table = ''
        for i in range(len(transitions)):
            mid_table =  extract_transitions_guards_table(transitions[i], i == 0)
            final_transition_table = appendTables(final_transition_table, mid_table)

        return final_transition_table
    
    def execute(self):
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
        
        The system description:
        {self.description}

        The system you are modeling: 
        {modeled_system}

        States and events table:
        {statesAndEvents}

        Parallel regions table:
        {parallelRegions if parallelRegions is not None else "NO PARALLEL STATES"}

        Output: 
        '''

        response = call_gpt4(prompt)
        transition_guard_table = extract_transitions_guards_table(response, True)

        print(f"Transitions table: {transition_guard_table}")
        return transition_guard_table
