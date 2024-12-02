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
        You are a requirements engineer specialized in designing UML state machines from a textual description of a system.
        You are given the description of the system.
        Your task is to identify the name of the system for which you are creating the UML state machine from the description.

        You MUST output the name of the system in the following format:
        <system_name>System Name</system_name>

        Keep your answer concise. If you answer incorrectly, you will be fired from your job.

        Here is an example:
        {get_n_shot_examples(['printer_winter_2017'],['system_description','system_name'])}

        Here is your input:
        system_description:
        <system_description>{self.description}</system_description>

        system_name:
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