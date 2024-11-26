import re
from sherpa_ai.actions.base import BaseAction
from resources.util import call_llm, remove_transitions_from_exit_transition_table, extract_table_entries, create_exit_transitions_table, find_events_for_transitions_table, merge_tables

class EventDrivenFilterTransitionsAction(BaseAction):
    name: str = "event_driven_filter_transitions_action"
    args: dict = {}
    usage: str = "Given a description of a system and the identified transitions of the system, reduce the number of inaccurate or unneccesary transitions in the UML State Machine"
    description: str = ""

    
    def send_filter_transitions_prompt(self, system_name, transitions_table, events, state):
        events_formatted = ", ".join(events)
        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, a state, and a table containing the transitions exiting the provided state, your task is to answer a question answering task.
        
        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        The identified state is:
        {state}

        The table of identified transitions exiting the state is:
        {transitions_table}

        The events associated with the transitions are:
        {events_formatted}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Examine the events and transitions that are exiting the current state.
        3. Examine the description of the system. Using the description of the system, determine partial orderings of the events related to the transitions. A partial ordering of events refers to a system where some events must occur in a specific sequence due to dependencies, while others can happen independently or concurrently.
        4. Based on the partial orderings which you generate and the provided state, identify the transitions that violate the partial orderings. In other words, based on the state and the partial orderings which you have generated, identify the transitions that CANNOT occur for the given state.
        5. If there are transitions to remove based on the partial orderings. Output "NO TRANSITIONS REMOVED".
        6. Otherwise, if transitions need to be removed, output the IDs of the transitions, as indicated in the "Transition ID" column, in a comma separated list in the following format:

        Transitions Removed: <first_id>, <second_id>, <third_id>, ...

        The IDs that you provide should come from the original transitions table provided to you above. DO NOT add transition IDs that do not exist.
        Your solution MUST be in the above format, otherwise it will be rejected.
        """

        response = call_llm(prompt=prompt,
                             temperature=0.7)
        
        match = re.search(r"Transitions Removed:\s*([\w\s,]+)", response)
        
        if "NO TRANSITIONS REMOVED" in response:
            print("No transitions removed")
            transitions_table = remove_transitions_from_exit_transition_table(transitions_table, set())
            return transitions_table
        else:
            if match:
                # extract either a comma separated list or a single ID provided by the LLM
                ids_to_remove_str = match.group(1)
                ids_to_remove = [id.strip() for id in ids_to_remove_str.split(",") if id.strip()]
                updated_transitions = remove_transitions_from_exit_transition_table(transitions_table=transitions_table,
                                                                                    ids_to_remove=ids_to_remove)
                print(f"Removed transitions {ids_to_remove}")
                return updated_transitions
            else:
                print(f"Match not found. Response: {response}")
                transitions_table = remove_transitions_from_exit_transition_table(transitions_table, set())
                return transitions_table
        

    def execute(self):
        print(f"Running {self.name}...")
        system_name = self.belief.get("event_driven_system_name_search_action", "Thermomix TM6")

        event_driven_transitions_table = self.belief.get("event_driven_create_transitions_action")
        event_driven_states_table = self.belief.get("event_driven_state_search_action")
        states = extract_table_entries(table=event_driven_states_table)

        filtered_transitions_tables = []

        # create partial orders based on the transitions that exit each state 
        for state in states:
            exit_transitions = create_exit_transitions_table(transitions_table=event_driven_transitions_table,
                                                                   from_state=state)
            
            events = find_events_for_transitions_table(transitions_table=exit_transitions)
            
            filtered_transitions_table = self.send_filter_transitions_prompt(system_name=system_name,
                                                                             transitions_table=exit_transitions, 
                                                                             events=events, 
                                                                             state=state)
            
            filtered_transitions_tables.append(filtered_transitions_table)
        
        filtered_transitions_table = merge_tables(html_tables_list=filtered_transitions_tables)

        print(filtered_transitions_table)
        return filtered_transitions_table
                

