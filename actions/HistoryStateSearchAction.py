from sherpa_ai.actions.base import BaseAction

class HistoryStateSearchAction(BaseAction):
    name: str = "history_state_search_action"
    args: dict = {}
    usage: str = "Identify all history states for hierarchical states in the system"

    def execute(self):
        hierarchical_states = self.belief.get('hierarchical_state_search_action')
        for hierarchical_state in hierarchical_states:
            prompt = '''
            You are an AI assistant specialized in creating state machines.
            Determine if the hierarchical state <state> requires a history state to remember a past state after a transition.
            Output your answer in a table format containing a single row with the following columns: Does the state <state> require a history state?, Sentences in the problem description that implied the information (max 3)

            You are an AI assistant specialized in identifying the guards and transitions for a state machine. Given a problem description, a table of all the states and events: {statesAndEvents}, and a table of the parallel states and their substrates {parallelRegions}, note that the parallel state table input is optional so if user doesn’t provide one, assume that there is not parallel states in the state machine.
            Parse through each state in the states table and identify if there exists any missing events from the table. Parse through each state in the states table to identify whether the event triggers transitions to another state. If the state is a substate then there can only exist a transition inside the parallel region and from and to the parent state.
            Definition: A transition shows a path between states that indicates that a change of state is occurring. A trigger, a guard condition, and an effect are the three parts of a transition, all of which are optional.

            The system description:
            {description}
            The system you are modeling: 
            {modeled_system}

            If one or more transitions should be triggered for each state because of an event, then you should also specify if there are any conditions or guards that must happen so that the event for the transition is triggered.
            Finally, your job is to summarize your output in an HTML transition table that specifies the your answer in a table format with the following format:

            Output your answer in HTML form:
            ```html <table border="1"> <tr> <th>From State</th> <th>To State</th> <th>Event</th> <th>Guard</th> </tr>
            <tr> <td rowspan="3"> State1 </td> <td> State2 </td> <td> Event1 </td> <td> Condition1 </td> </tr>
            <tr> <td rowspan="3"> State3 </td> <td> State4 </td> <td> Event2 </td> <td> NONE </td> </tr> </table> ```

            '''
        return f"Event 1, Event 2"
