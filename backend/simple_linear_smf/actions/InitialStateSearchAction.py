import re
from resources.SMFAction import SMFAction
from resources.n_shot_examples_simple_linear import get_n_shot_examples
from resources.util import call_llm

class InitialStateSearchAction(SMFAction):
    """
    The InitialStateSearchSearchAction class prompts the LLM to examine
    the description of the system and the identified states of the UML State Machine
    to determine the Initial State of the UML State Machine

    Input(s): description of the system, name of the system, and the state table output from EventDrivenStateSearchAction
    Output(s): string containing the name of the initial state of the UML State Machine
    """

    name: str = "initial_state_search_action"
    args: dict = {}
    usage: str = "Given a description of a system and a list of all states of the system, identify the Initial State of the UML state machine of the system"
    description: str = ""
    log_file_path: str = ""

    def execute(self):
        self.log(f"Running {self.name}...")

        system_name, state_event_table = self.belief.get('state_event_search_action')
        n_shot_example_list = self.belief.get("n_shot_examples")

        prompt = f"""
        You are an expert requirements engineer specializing in designing UML state machines from textual descriptions of systems. Your task is to identify the initial state of a system based on the provided information.
        Here's the information you'll be working with:

        1. System Description:
        <system_description>
        {self.description}
        </system_description>

        2. System Name:
        <system_name>
        {system_name}
        </system_name>

        3. States Table:
        <states_table>
        {state_event_table}
        </states_table>

        Your objective is to identify exactly ONE (1) Initial State for the system. This Initial State MUST be one of the states listed in the provided states table.

        Please follow these steps:

        1. Carefully read and analyze the system description, name, and states table.
        2. Wrap your analysis inside <initial_state_analysis> tags. Consider the following:
        - List all states from the states table
        - What does the system description say about how the system starts or is initialized?
        - Analyze each state's relevance as a potential initial state
        - Rank the top 3 candidates for initial state, providing brief reasoning for each
        - Which state in the states table best represents the system's starting point?
        - Are there any states that logically precede all others?
        3. Select exactly ONE initial state based on your analysis.
        4. Verify that your selected initial state is present in the states table.
        5. Output your answer using the following format:

        <initial_state>InitialState</initial_state>

        Remember, your response should be concise and accurate. The quality of your work is crucial, and incorrect answers may result in termination of your role.

        {get_n_shot_examples(n_shot_example_list,['system_description', 'hierarchical_state_table', 'initial_state'])}

        Your expertise in identifying the correct initial state is vital for the success of the entire system modeling process. Your accurate analysis will lay the foundation for a robust and reliable state machine design. Take pride in your role and let your expertise shine through in your thoughtful analysis and precise selection.

        Now, please proceed with your analysis and identification of the initial state for the given system. It's OK for the initial_state_analysis section to be quite long.
        """

        self.log(prompt)
        response = call_llm(prompt=prompt)
        
        initial_state_search = re.search(r"<initial_state>(.*?)</initial_state>", response)

        if initial_state_search:
            initial_state = initial_state_search.group(1)
        else:
            initial_state = "NOT FOUND"
        self.log(initial_state)

        return initial_state