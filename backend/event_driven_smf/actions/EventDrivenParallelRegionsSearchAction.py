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
        system_name = self.belief.get('event_driven_system_name_search_action')

        prompt = f"""
            You are an AI assistant specialized in analyzing state machines and identifying parallel regions. Your task is to examine a system description, system name, and a transitions table to determine if parallel states exist and provide appropriate output.

            Here is the input you need to analyze:

            <system_description>
            {{system_description}}
            </system_description>

            <system_name>
            {{modeled_system}}
            </system_name>

            <transitions_table>
            {{transitions_table}}
            </transitions_table>

            Now, follow these steps to complete your analysis:

            1. Thoroughly analyze the provided information, paying special attention to the state transitions and system behavior.

            2. Determine if parallel states exist in the state machine. Remember that parallel states:
            - Are independent states that can be active simultaneously
            - Allow the system to be in multiple states at once
            - Typically represent different aspects or components of the system that can operate independently

            3. Use the following questions to guide your analysis:
            - Is there an event in which the state machine can react in more than one state at the same time?
            - Should the state machine remember being active in more than one state at a time?

            4. Document your thought process and analysis in <state_machine_analysis> tags. Be thorough in your reasoning and explain how you arrived at your conclusions. Include the following steps:
            a. List out all states and events from the transitions table
            b. Identify potential parallel states by looking for states that can be active simultaneously
            c. Examine each potential parallel state pair and provide reasoning for why they might or might not be parallel
            d. Summarize your findings

            It's okay for this section to be quite long, as we want a thorough analysis.

            5. Based on your analysis, provide one of the following outputs:

            a. If no parallel states are identified:
                - Output the exact string: "NO PARALLEL STATES IDENTIFIED"
                - Return the original states and events table provided in the <transitions_table> section

            b. If parallel states are identified:
                - Create an HTML table listing the parallel states and their substates using the following format:
                    ```html
                    <table border="1">
                    <tr>
                        <th>Parallel State</th>
                        <th>Parallel Region</th>
                        <th>Substate</th>
                    </tr>
                    <tr>
                        <td>[Parallel State Name]</td>
                        <td>[Parallel Region Name]</td>
                        <td>[Substate Name]</td>
                    </tr>
                    <!-- Add more rows as needed -->
                    </table>
                    ```
                - Update the states and events table to reflect the parallel states, using the following format:
                    ```html
                    <table border="1">
                    <tr>
                        <th>Current State</th>
                        <th>Event</th>
                        <th>Next State(s)</th>
                    </tr>
                    <tr>
                        <td>[Current State]</td>
                        <td>[Event]</td>
                        <td>[Next State(s)]</td>
                    </tr>
                    <!-- Add more rows as needed -->
                    </table>
                    ```

            Remember, parallel states should be used sparingly and only when necessary. Be confident in your analysis and provide clear, well-structured output.

            Your expertise in state machine analysis is crucial for the success of this task. The accuracy and clarity of your output will greatly impact the system design process.

            """
        
        self.log(prompt)

        response = call_llm(prompt)
        self.log(response)

        if ("NO PARALLEL STATES IDENTIFIED" in response):
            return (transitions_table, None)
        
        updated_state_event_table = extract_states_events_table(llm_response=response)
        updated_parallel_state_table = extract_parallel_states_table(llm_response=response)

        return (updated_state_event_table, updated_parallel_state_table)
