from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_states_events_table
from util import extract_parallel_states_table
from util import extract_transitions_guards_actions_table

class SanityCheckAction(BaseAction):
    name: str = "sanity_check_action"
    args: dict = {
                  "system_description": "A detailed paragraph description of the system that the generated UML state machine represents (str)", 
                  "state_event_table": "An HTML table describing states and events of the generated UML state machine for the system description. Contains Current State, Event, and Next State(s) columns (str)",
                  "parallel_state_table": "An HTML table describing the parallel states of the generated UML state machine for the system description. Contains Parallel State, Substate, and Reference from Problem Description columns (str)",
                  "transitions_table": "An HTML table describing the transitions of the generated state UML state machine for the system description. Contains From State, To State, Event, Guard, Entry Action, and Exit Action columns (str)" 
                 }
    usage: str = "Confirm that sentences from the system description are captured in the generated state machine represented by HTML tables"
    
    def send_sanity_check(self, sentence, state_event_table, parallel_state_table, transitions_table, max_retries=5):
        """
        send the sanity check prompt to GPT 4 for a given sentence and the provided state/event, parallel state, and transitons
        tables. max_retries indicates the amount of times the prompt should be resent in the event that one of the requested
        tables is not in the reply from GPT 4
        """
        
        prompt = f"""
                      You are an AI assistant specialized in creating UML state machines. You will be provided with a single sentence from the problem description. Additionally, you will be provided with a table containing states and events, a table containing parallel states, and a table containing transitions of a UML State Machine.
                      Your task is to ensure that the provided sentence is encapsulated by at least one state, transition, guard, action, hierarchical state, and/or history state from the provided tables. If there is no entry in a table that encapsulates the provided sentence, propose a new UML state machine component that will encapsulate the sentence, and add it to its corresponding table. Then, output the updated states and events, parallel states, and transitions tables.
                      The single sentence is:
                      {sentence}
                      The table describing states and events is:
                      {state_event_table}
                      The table describing parallel states is:
                      {parallel_state_table}
                      The table describing transitions is:
                      {transitions_table}
                      """
                      
        retries = 0
        retry = True
        
        # call GPT 4 while we should retry and we haven't reached max retries
        while retries < 5 and retry:
            response = call_gpt4(prompt)
            
            # extract tables
            updated_state_event_table = extract_states_events_table(llm_response=response)
            updated_parallel_state_table = extract_parallel_states_table(llm_response=response)
            updated_transitions_table = extract_transitions_guards_actions_table(llm_response=response)
            
            updated_tables = (updated_state_event_table, updated_parallel_state_table, updated_transitions_table)
            
            # if any of the tables are not provided, try again
            if None in updated_tables:
                retry = True
            else:
                retry = False
            
            retries += 1
        
        return updated_tables
        

    def execute(self, system_description: str, state_event_table: str, parallel_state_table: str, transitions_table: str):
        """
        the execute function for the sanity check prompt. iterates over each sentence in the system description and 
        applies updates to state/event, parallel states, and transitions table as advised by the LLM
        """
        
        system_description_sentences = system_description.split(".")
        
        for sentence in system_description_sentences:
            updated_tables = self.send_sanity_check(sentence=sentence,
                                                    state_event_table=state_event_table,
                                                    parallel_state_table=parallel_state_table,
                                                    transitions_table=transitions_table)
            
            if None in updated_tables:
                raise Exception(f"Max retries reach for SanityCheckAction for sentence: {sentence}")
            
            state_event_table, parallel_state_table, transitions_table = updated_tables
            
        return state_event_table, parallel_state_table, transitions_table
