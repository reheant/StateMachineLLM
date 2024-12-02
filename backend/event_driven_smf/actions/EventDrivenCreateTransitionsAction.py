from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, extract_table_entries, extract_transitions_guards_actions_table, merge_tables

class EventDrivenCreateTransitionsAction(BaseAction):
    name: str = "event_driven_create_transitions_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the events of the system, identify all transitions in the UML state machine of the system"
    description: str = ""

    def create_transitions(self, system_name, state, event, states_table, max_retries=2):
        prompt = f"""
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the name of the system you are modeling a state machine for, the description of the state machine, one of the identified states of the system, one of the identified events of the system, and a table of all identified states of the system.
        Your task is to determine ALL transitions that the event {event} can trigger for the state {state}.

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Determine all the transitions that can be triggered by the event {event} when the system is in the state {state}
        3. If any transitions were identified, identify any guard conditions for each of the identified transitions. Note that guard conditions are NOT required for transitions, so it is possible that a transition may not have a guard condition. If there are no guard conditions identified for one of the transitions, output "NONE" in the guard column of the table.
        4. If any transitions were identified, identify any actions that could occur for each of the identified transitions. Note that actions are NOT required for transitions, so it is possible that a transition may not have an associated action. If there are no actions identified for one of the transitions, output "NONE" in the guard column of the table.
        5. If no transitions can be triggered by the event {event} in the state {state}, reply with "NO TRANSITIONS". Otherwise, give a list of transitions in the following HTML table format:
        
        <create_transitions>```html<table border="1">
        <tr><th>FromState</th><th>ToState</th><th>Event</th><th>Guard</th><th>Action</th></tr>
        <tr><td rowspan="3">State1</td><td>State2</td><td>Event1</td><td>Condition1</td><td>Action1</td></tr>
        <tr><td rowspan="3">State2</td><td>State3</td><td>Event1</td><td>Condition1</td><td>NONE</td></tr>
        </table>```<create_transitions>

        Keep your answer concise. If you answer incorrectly, you will be fired from your job.

        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'state_inspected', 'event_inspected', 'states_table', 'create_transitions'])}

        Here is your input:
        system_name:
        <system_name>{system_name}</system_name>

        system_description:
        <system_description>{self.description}</system_description>

        state_inspected:
        <state_inspected>{state}</state_inspected>

        event_inspected:
        <event_inspected>{event}</event_inspected>

        states_table:
        <states_table>{states_table}</states_table>
        
        create_transitions:
        """

        print(prompt)
        # iterate over a max number of retries in order to get the correct format
        # if the LLM does not get the correct format after max_retries, then we return none
        retries = 0
        while retries < max_retries:
            response = call_gpt4(prompt=prompt, 
                                 temperature=0.7)
            
            # no transitions, so skip retries
            if "NO TRANSITIONS" in response:
                print("No transitions created.")
                return None

            # attempt to extract the transitions table
            transitions_table = extract_transitions_guards_actions_table(llm_response=response)
            if transitions_table is not None:
                print(transitions_table)
                return transitions_table
            else:
                print("No transitions table found in the response.")

            retries += 1
            print(f"Retrying... ({retries}/{max_retries})")

        # max retries met
        print("Max retries reached. No valid transitions found.")
        return None

    def execute(self):
        print(f"Running {self.name}...")

        # get the system name for the prompt
        system_name = self.belief.get("event_driven_system_name_search_action")

        # get all the states for the system and start with the initial state of the system
        event_driven_states_table = self.belief.get("event_driven_state_search_action")

        # get states events dictionary created in previous step
        states_events_dict = self.belief.get("event_driven_associate_events_with_states_action")

        # iterate over each combination of states and events, collecting transitions tables to be merged at the end
        transitions_tables = []
        for state in states_events_dict:
            for event in states_events_dict.get(state, []):
                transitions = self.create_transitions(system_name=system_name,
                                                      state=state,
                                                      event=event,
                                                      states_table=event_driven_states_table)

                if transitions is not None:
                    transitions_tables.append(transitions)
        
        merged_transitions_table = merge_tables(html_tables_list=transitions_tables)
        print(merged_transitions_table)

        return merged_transitions_table