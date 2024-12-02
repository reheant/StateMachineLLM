import re
from sherpa_ai.actions.base import BaseAction
from resources.util import call_gpt4

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
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, your task is to identify the name of the system for which you are creating the UML state machine.

        You MUST output the name of the system in the following format:  
        System: "System Name"

        The textual description of the system is the following:
        {self.description}
        """

        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        system_name = re.search(r"System:\s*\"(.*?)\"", response).group(1)

        print(system_name)

        return system_name