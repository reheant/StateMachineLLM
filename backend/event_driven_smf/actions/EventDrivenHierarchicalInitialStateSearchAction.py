from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_gpt4, group_parent_child_states
import re

class EventDrivenHierarchicalInitialStateSearchAction(BaseAction):
    """
    The EventDrivenHierarchicalInitialStateSearchAction prompts the LLM 
    to identify the initial state of each hierarchical state, as identified by the
    EventDrivenCreateHierarchicalStatesAction
    """
    name: str = "event_driven_hierarchical_initial_state_search"
    args: dict = {}
    usage: str = "Given a description of a system and the Hierarchical States of the system, identify the initial state of each Hierarchical State in the UML state machine of the system."
    description: str = ""

    def identify_initial_state(self, parent_state, child_states):
        """
        The identify_initial_state function takes a hierarchical parent state
        and a list of its child states and prompts the LLM to choose an initial state
        of the hierarchical parent state from the list of childstates
        """
        system_name = self.belief.get("event_driven_system_name_search_action")
        formatted_child_states = ", ".join(child_states)

        prompt = f"""
You are an expert requirements engineer specializing in designing UML state machines from textual descriptions of systems. Your task is to create a hierarchical state machine design based on the provided system information.

Here's the information for the system you need to analyze:

<system_description>
{self.description}
</system_description>

<system_name>
{system_name}
</system_name>

superstate_inspected:
<superstate_inspected>{parent_state}</superstate_inspected>

substates_inspected:
<substates_inspected>{formatted_child_states}</substates_inspected>

Your objective is to determine ALL superstates and substates of the system, creating a hierarchical state machine design. Follow these steps:

1. Carefully analyze the provided system description, name, states table, and transitions table.
2. Use the transitions in the identified transitions table to determine the superstates and substates of the system.
3. Create a hierarchical state machine design that captures commonalities by organizing the states as a hierarchy.
4. Ensure that higher-level states in the hierarchy perform common message handling, while lower-level states inherit commonality from higher-level ones and perform state-specific functions.

Before providing your final output, wrap your analysis inside <state_machine_analysis> tags. In your analysis:
- List all states from the transitions table
- Identify potential superstates based on common transitions or behaviors
- Group substates under each potential superstate
- Explain your reasoning for each hierarchical relationship
- Ensure that ALL states from the original table of identified transitions appear in your analysis

After your analysis, present your final hierarchical state machine design in an HTML table with the following format:

<hierarchical_table>```html<table border="1">
<tr><th>Superstate</th><th>Substate</th></tr>
<tr><td>State1</td><td>State2</td></tr>
<tr><td>State3</td><td>State4</td></tr>
<tr><td>-</td><td>State5</td></tr>
</table>```</hierarchical_table>

Important rules for your final output:
1. ALL states from the original table of identified transitions MUST appear in the "Substate" column EXACTLY ONCE.
2. If a state from the original table of identified transitions DOES NOT have a parent state in your design, enter "-" in the "Superstate" column.
3. Be concise in your final output, providing only the requested HTML table.

{get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'superstate_inspected', 'substates_inspected', 'superstate_initial_state'])}

Remember, your expertise in UML state machines is crucial for creating an accurate and efficient hierarchical design. The quality of your work will directly impact the success of the system's implementation. Take pride in your role as a key contributor to this important project.
"""

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        superstate_initial_state_search = re.search(r"<superstate_initial_state>(.*?)</superstate_initial_state>", response)

        if superstate_initial_state_search:
            superstate_initial_state = superstate_initial_state_search.group(1)
        else:
            superstate_initial_state = "NOT FOUND"
        print(superstate_initial_state)


    def execute(self):
        """
        The execute function uses the table of hierarchical states identified in EventDrivenCreateHierarchicalStatesAction,
        map the parent states to a list of its child states, and prompts the LLM through the identify_initial_state()
        function to find the initial state of each parent hierarchical state
        """
        print(f"Running {self.name}...")

        event_driven_hierarchical_state_table = self.belief.get("event_driven_create_hierarchical_states_action")

        parent_child_states_dict = group_parent_child_states(event_driven_hierarchical_state_table)

        initial_states_dict = {}

        for parent_state in parent_child_states_dict:
            child_states = parent_child_states_dict[parent_state]
            initial_state = self.identify_initial_state(parent_state=parent_state,
                                                        child_states=child_states)

            initial_states_dict[parent_state] = initial_state

        print(initial_states_dict)
        return initial_states_dict