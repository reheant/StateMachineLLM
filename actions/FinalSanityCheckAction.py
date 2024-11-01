from sherpa_ai.actions.base import BaseAction
from util import call_gpt4
from util import extract_hierarchical_state_table
from util import extract_parallel_states_table
from util import extract_transitions_guards_actions_table

class FinalSanityCheckAction(BaseAction):
    name: str = "sanity_check_action"
    args: dict = {}
    usage: str = "Confirm that sentences from the system description are captured in the generated state machine represented by HTML tables"
    description: str = ""
    
    def send_sanity_check(self, table, table_name, max_retries=5):
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
                      {self.description}

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
            if table_name == "Hierarchical States":
                updated_table = extract_hierarchical_state_table(llm_response=response)
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

        return updated_table
        

    def execute(self):
        """
        the execute function for the sanity check prompt. iterates over each sentence in the system description and 
        applies updates to state/event, parallel states, and transitions table as advised by the LLM
        """

        print(f"Running {self.name}...")
        
        hierarchical_state_table, _ = self.belief.get("hierarchical_state_search_action")
        _, parallel_state_table = self.belief.get("parallel_state_search_action")
        transitions_table = self.belief.get("history_state_search_action")


        # sanity check on hierarchical states
        updated_hierarchical_state_table = self.send_sanity_check(table=hierarchical_state_table,
                                                                  table_name="Hierarchical States")
        
        # parallel state table is an optional output. if it is not identified by ParallelStateSearchAction, the output is None
        updated_parallel_state_table = None
        if parallel_state_table is not None:
            updated_parallel_state_table = self.send_sanity_check(table=parallel_state_table,
                                                                table_name="Parallel States")
            
        # sanity check on transitions
        updated_transitions_table = self.send_sanity_check(table=transitions_table,
                                                           table_name="Transitions")

        print(f"Updated Hierarchical State Table: {updated_hierarchical_state_table}")
        print(f"Updated Parallel State Table: {updated_parallel_state_table}")
        print(f"Updated Transitions Table: {updated_transitions_table}")

        return updated_hierarchical_state_table, updated_parallel_state_table, updated_transitions_table
