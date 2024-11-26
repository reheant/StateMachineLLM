import re
from sherpa_ai.actions.base import BaseAction
from resources.util import call_llm

class EventDrivenSystemNameSearchAction(BaseAction):
    name: str = "event_driven_system_name_search_action"
    args: dict = {}
    usage: str = "Given a textual description of a system, identify the name of the system"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")
        prompt = f""""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, your task is to identify the name of the system for which you are creating the UML state machine.

        You MUST output the name of the system in the following format:  
        System: "System Name"

        The textual description of the system is the following:
        {self.description}
        """

        response = call_llm(prompt=prompt,
                             temperature=0.7)
        
        system_name = re.search(r"System:\s*\"(.*?)\"", response).group(1)

        print(system_name)

        return system_name