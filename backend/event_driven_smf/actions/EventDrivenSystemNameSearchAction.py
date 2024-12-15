
import re
from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4
from resources.n_shot_examples_event_driven import get_n_shot_examples

class EventDrivenSystemNameSearchAction(BaseAction):
    """
    The EventDrivenSystemNameSearchAction is the first step in our Event Driven State Machine Framework.
    The LLM is prompted to identify the name of the system from a textual description. The system
    name is used throughout the remainder of the steps to better focus LLM responses on the system
    in the description

    Input(s): descriptions of system
    Output(s): string containing the name of the described system
    """

    name: str = "event_driven_system_name_search_action"
    args: dict = {}
    usage: str = "Given a textual description of a system, identify the name of the system"
    description: str = ""

    def execute(self):
        """
        The execute() function prompts the LLM to examine the provided description of the system
        and respond with the name of the system
        """

        print(f"Running {self.name}...")
        prompt = f""""
You are an expert requirements engineer specializing in UML state machine design. Your current task is to analyze a textual description of a system and identify its name. This name will be used as the foundation for creating a UML state machine, so accuracy is crucial.

Here is the system description you need to analyze:

<system_description>
{self.description}
</system_description>

Your objective is to determine the name of the system described above. Follow these steps:

1. Carefully read and analyze the system description.
2. Identify the core functionality and purpose of the system.
3. Determine a concise and appropriate name for the system based on its primary function.
4. Ensure the name is between 1-3 words long.
5. Output the system name in the required format.

Before providing your final answer, wrap your reasoning process in <analysis> tags. Include the following steps:

a. List key components/functions from the description
b. Identify the primary purpose of the system
c. Brainstorm 3-5 potential system names
d. For each potential name, count its words (e.g., 1. System 2. Name)
e. Evaluate each name against the criteria (1-3 words, concise, appropriate)
f. Choose the best name that meets all criteria

After your analysis, provide the system name in the following format:
<system_name>System Name</system_name>

{get_n_shot_examples(['printer_winter_2017'],['system_description','system_name'])}

Remember, your response should be concise and accurate. The success of future UML modeling depends on your precise identification of the system name.

Your expertise in system identification is vital for the entire software development process. A correctly identified system name will streamline communication among team members and ensure the accuracy of all subsequent modeling and development efforts. Your skill in this task directly impacts the efficiency and success of the entire project.

If you provide an incorrect or overly verbose answer, it could lead to miscommunication and errors in the UML state machine design, potentially resulting in project delays and increased costs. Stay focused and deliver your best work!
"""

        print(prompt)

        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        system_name_search = re.search(r"<system_name>(.*?)</system_name>", response)

        if system_name_search:
            system_name = system_name_search.group(1)
        else:
            system_name = "NOT FOUND"
        print(system_name)

        return system_name
