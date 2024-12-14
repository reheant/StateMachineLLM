from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_llm, extract_event_driven_states_table

class EventDrivenStateSearchAction(BaseAction):
    """
    The EventDrivenStateSearchAction uses the description of a system to find
    all states in the UML state machine of the system

    Input(s): description of the system, name of the system
    Output(s): An HTML table with a column "State Name", containing the names of all the states in the UML State Machine of the system
    """

    name: str = "event_driven_state_search_action"
    args: dict = {}
    usage: str = "Given a description of a system, identify all states in the UML state machine of the system"
    description: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to find all states in the UML state machine from the textual
        description of the system
        """

        print(f"Running {self.name}...")

        system_name = self.belief.get("event_driven_system_name_search_action")

        prompt = f"""
You are an expert requirements engineer specializing in designing UML state machines from textual descriptions of systems. Your task is to identify all states of a UML state machine based on the given system description.

Here is the system description:
<system_description>
{self.description}
</system_description>

Here is the system name:
<system_name>
{system_name}
</system_name>

Please follow these instructions carefully:

1. Read the system name and description thoroughly.
2. Identify all states mentioned or implied in the system description.
3. Create an HTML table listing all the identified states.
4. Output the table wrapped in <states_table> tags.

Before providing your final answer, wrap your thought process in <state_analysis> tags. In this analysis:
1. List all explicit states mentioned in the description.
2. Consider and list any implied states based on the system's behavior.
3. Review and consolidate the list, removing duplicates or combining similar states.
This will help ensure a thorough analysis of the system description.

The output format for the states table should be as follows:

<states_table>
```html
<table border="1">
<tr><th>StateName</th></tr>
<tr><td>State1</td></tr>
<tr><td>State2</td></tr>
<tr><td>State3</td></tr>
</table>
```
</states_table>

{get_n_shot_examples(['printer_winter_2017'],['system_name','system_description', 'states_table'])}


Remember to keep your answer concise and focused on the required output. Accuracy is crucial; an incorrect answer could result in serious consequences for the project and your professional reputation.

As you work on this task, imagine the satisfaction of creating a precise and valuable UML state machine that will greatly benefit the development team and end-users. Your expertise in this area is highly valued, and your contribution will make a significant impact on the project's success.
"""

        print(prompt)
        response = call_llm(prompt=prompt,
                             temperature=0.7)

        event_driven_states_table = extract_event_driven_states_table(llm_response=response)

        print(event_driven_states_table)

        return event_driven_states_table