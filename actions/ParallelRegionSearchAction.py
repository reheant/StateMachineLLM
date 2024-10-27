from sherpa_ai.actions.base import BaseAction
from sherpa_ai.memory.belief import Belief
from util import call_gpt4
from util import extract_states_events_table
from util import extract_parallel_states_table

class ParallelStateSearchAction(BaseAction):
    name: str = "parallel_state_search_action"
    args: dict = {
                  "description": "A detailed paragraph description of the system that the generated UML state machine represents (str)", 
                 }
    usage: str = "Identify all parallel regions of the state machine from the system description"
    
    def send_parallel_state_search(self, description : str, system_name :str, state_event_table: str):
        """
        send the parallel states prompt to GPT 4 for a given system and problem description alongside the state and events tables. 
        maximum retries indicates the amount of times that the prompt should be resent in the event that one of the tables are not provided
        """

        system_name, state_event_table = self.belief.get('state_event_search_action')

        prompt = f""" 
            You are an AI assistant specialized in identifying parallel regions in a state machine from a problem description and a table that lists all the states and events of the state machine. Given the following definition of a parallel region;
            Definition: A parallel state is a state that is divided into separate regions.  
            
            Each region contains more substates.  When a parallel state is entered, each of the regions are also entered; their initial states are entered and so on, parallel states are used when the machine needs to combine several discrete behaviors at the same time.
            Your goal is to parse through problem description and table of states and events to identify events that occur independently but concurrently as this will help you to identify if a parallel state exists.

            Note that a state machine may not have parallel states so ensure that the parallel state that you are outputting is one that follows the guidelines above and is not already encapsulated by a state, furthermore make sure that the state that you are outputting makes sense in the context about the object that you are modeling. 
            If you have identified the need for a parallel state then after identifying the events that take place concurrently, place the states that the events are being performed on under a parallel state with a state name that encompasses the behavior of such a state and identify the events that causes the state machine to enter and leave the parallel state. 
            
            Finally, if there is no need for parallel states then output the string EMPTY otherwise if you are able identify the need for parallel states your task is to output your answer in the following HTML table format and update the original input table with the new parallel states bulisting them updating all the columns with the necessary changes based on these new parallel states but keep the original headings from the original state and event table

            The system description:
            {description}
            The system you are modeling: 
            {system_name}
            The table descibing the states and events is:
            {state_event_table}

            The event and state table output format in HTML form:
            ```html <table border="1"> <tr> <th>Current State</th> <th>Event</th> <th>Next State(s)</th> </tr> <tr> <td rowspan="2">S0</td> <td>Event 1</td> <td>S0, S1</td> </tr> <tr> <td>Event 2</td> <td>S2</td> </tr> <tr> <td rowspan="2">S1</td> <td>Event 3</td> <td>S2</td> </tr> <tr> <td>Event 4</td> <td>S3</td> </tr> <tr> <td>S2</td> <td>Event 5</td> <td>S1, S3</td> </tr> <tr> <td>S3</td> <td>Event 6</td> <td>S0</td> </tr> </table> ```                                        

            The parallel state table output format in HTML form:
            ```html <table border="1"> <tr> <th>Parallel State</th> <th>Substate</th> </tr> <tr> <td rowspan="3">Parallel State 1</td> <td>S0</td> </tr> <tr> <td>S1</td> </tr> <tr> <td>S2</td> </tr> <tr> <td rowspan="2">Parallel State 2</td> <td>SS0</td> </tr> <tr> <td>SS1</td> </tr> <tr> <td rowspan="4">Parallel State 3</td> <td>X0</td> </tr> <tr> <td>X1</td> </tr> <tr> <td>X2</td> </tr> <tr> <td>X3</td> </tr> </table>
        """
        
        retries = 0
        retry = True
        
        # call GPT 4 while we should retry and we haven't reached max retries
        while retries < 5 and retry:
            response = call_gpt4(prompt)

            updated_state_event_table = extract_states_events_table(llm_response=response)
            
            if ("EMPTY" in response):
                return (updated_state_event_table, None)
            # extract tables

            updated_parallel_state_table = extract_parallel_states_table(llm_response=response)
            print(updated_parallel_state_table)
            updated_tables = (updated_state_event_table, updated_parallel_state_table)
            print(updated_state_event_table)
            # if any of the tables are not provided, try again
            if None in updated_tables:
                retry = True
            else:
                retry = False
            
            retries += 1
        
        return updated_tables
    
    def execute(self, description: str):
        """
        the execute function for the parallel state prompt. calls the send_parallel_state_search function and applies the updates to event and states 
        table while also generating the output table for the parallel states
        """
        system, state_event_table = self.belief.get('state_event_search_action')
        print(system)
        print(state_event_table)

        updated_tables = self.send_parallel_state_search(description, system, state_event_table)

        if (updated_tables[0] and updated_tables[1]) is None:
            raise Exception(f"Max retries reach for ParallelRegionSearchAction for problem description: {description}")
        
        if updated_tables[1] is None:
            print(f"No parallel states found")
        else:
            state_event_table, parallel_state_table = updated_tables
            
        
        return state_event_table, parallel_state_table
            

