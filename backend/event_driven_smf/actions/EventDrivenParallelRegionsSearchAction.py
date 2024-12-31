from resources.SMFAction import SMFAction
from resources.util import call_llm, extract_states_events_table, extract_parallel_states_table


class EventDrivenParallelRegionsSearchAction(SMFAction):
    name: str = "event_driven_parallel_regions_search_action"
    args: dict = {}
    usage: str = "Identify Parallel Regions from States and Events"
    description: str = ""
    log_file_path: str = ""

    def execute(self):
        self.log(f"Running {self.name}...")

        transitions_table = self.belief.get('event_driven_create_transitions_action')
        modeled_system = self.belief.get('event_driven_system_name_search_action')

        prompt = f"""
            You are an AI assistant specialized in identifying parallel regions in a state machine from a problem description and a table that lists all the states and events of the state machine. 
             
            In a state machine, parallel states (also called orthogonal states) are independent states that can be active simultaneously, allowing the system to be in multiple states at once. They typically represent different aspects or components of the system that can operate independently of each other.
            Think of it like a media player that can both be "Playing" music AND in "Shuffle" mode at the same time - these are two parallel states that don't interfere with each other but together describe the complete state of the system.

            You can identify parallel states by asking yourself: Is there an event in which the state machine can react in more than 1 state at the same time? Should the state machine remember be active in more than 1 state at a time? 

            Note that parallel states are not common, should be used sparingly and ONLY if needed. 
            If there is no need for parallel states, then output the string "NO PARALLEL STATES IDENTIFIED". 
            If you have identified the need for a parallel state, you MUST add the Parallel States and its substates in an HTML table with the following format and headers:
            ```html <table border="1"> <tr> <th>Parallel State</th> <th>Parallel Region</th> <th>Substate</th> </tr> </table>```

            If there are parallel states, also update the states and events accordingly using the HTML table columns below. You MUST use the exact columns provided below and build off of the states and events table provided. 
            If there are no parallel states, then return the original states and events table that you are provided in this prompt.
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> </table>``` 

            The system description: {self.description}

            The system you are modeling: {modeled_system}

            The original HTML table descibing the states and events is: {transitions_table}

            Output:
            """
        
        self.log(prompt)

        response = call_llm(prompt)
        self.log(response)

        if ("NO PARALLEL STATES IDENTIFIED" in response):
            return (transitions_table, None)
        
        updated_state_event_table = extract_states_events_table(llm_response=response)
        updated_parallel_state_table = extract_parallel_states_table(llm_response=response)

        return (updated_state_event_table, updated_parallel_state_table)