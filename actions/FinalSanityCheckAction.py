from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_states_events_table
from util import extract_parallel_states_table
from util import extract_transitions_guards_actions_table

class FinalSanityCheckAction(BaseAction):
    name: str = "sanity_check_action"
    args: dict = {
                  "description": "A detailed paragraph description of the system that the generated UML state machine represents (str)", 
                 }
    usage: str = "Confirm that sentences from the system description are captured in the generated state machine represented by HTML tables"
    
    def send_sanity_check(self, description, table, table_name, max_retries=5):
        """
        send the sanity check prompt to GPT 4 for a given sentence and the provided state/event, parallel state, and transitons
        tables. max_retries indicates the amount of times the prompt should be resent in the event that one of the requested
        tables is not in the reply from GPT 4
        """
        
        prompt = f"""
                      You are an AI assistant specialized in creating UML state machines. You will be provided with a system description. Additionally, you will be provided with a table containing {table_name}.
                      Your task is to ensure to examine each sentence in the description. If the sentence is relevant to {table_name}, then add an entry in the {table_name} table. If the sentence is not relevant to {table_name}, then do not add an entry to the table for the sentence.

                      Your output tables must have the same exact format as specified below. You are NOT allowed to add extra columns. You must update the respective tables in place.

                      The system description is:
                      {description}

                      The {table_name} table is:
                      ```html {table} ```

                      A reminder that you MUST return the updated table using the above format.
                      """
                      
        retries = 0
        retry = True
        
        # call GPT 4 while we should retry and we haven't reached max retries
        while retries < max_retries and retry:
            response = call_gpt4(prompt)
            
            # extract table based on table name
            if table_name == "States and Events":
                updated_table = extract_states_events_table(llm_response=response)
            elif table_name == "Parallel States":
                updated_table = extract_parallel_states_table(llm_response=response)
            else:
                updated_table = extract_transitions_guards_actions_table(llm_response=response)
            # if any of the tables are not provided, try again
            if updated_table is None:
                retry = True
            else:
                retry = False
            
            retries += 1
        
        print(response)
        return updated_table
        

    def execute(self, description):
        """
        the execute function for the sanity check prompt. iterates over each sentence in the system description and 
        applies updates to state/event, parallel states, and transitions table as advised by the LLM
        """

        print(f"Hello {self.name}")
        
        state_event_table = self.belief.get("state_event_search_action")
        parallel_state_table = self.belief.get("parallel_state_search_action")
        transitions_table = self.belief.get("action_search_action")


        updated_state_event_table = self.send_sanity_check(description=description,
                                                           table=state_event_table,
                                                           table_name="States and Events")
        updated_parallel_state_table = self.send_sanity_check(description=description,
                                                              table=parallel_state_table,
                                                              table_name="Parallel States")
        updated_transitions_table = self.send_sanity_check(description=description,
                                                           table=transitions_table,
                                                           table_name="Transitions")

        print(updated_state_event_table, updated_parallel_state_table, updated_transitions_table)
        return updated_state_event_table, updated_parallel_state_table, updated_transitions_table
