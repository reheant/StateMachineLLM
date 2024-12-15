from sherpa_ai.actions.base import BaseAction
from resources.n_shot_examples_event_driven import get_n_shot_examples
from resources.util import call_llm, extract_hierarchical_state_table

class EventDrivenCreateHierarchicalStatesAction(BaseAction):
    """
    The EventDrivenCreateHierarchicalStatesAction takes the transitions after they have been
    filtered by the EventDrivenFilterTransitionsAction and produces hierarchical states based
    on events that share common transitions

    Input(s): description of the system, name of the system, and table of transitions from EventDrivenFilterTransitionsAction
    Output(s): an HTML table containing columns "Superstate" and "Substate" which provide the hierarchical states of the UML State Machine of the system
    """

    name: str = "event_driven_create_hierarchical_states_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the transitions of the system, identify all Hierarchical States in the UML state machine of the system."
    description: str = ""

    def execute(self):
        """
        The execute function prompts the LLM to examine the table of created transitions and group states
        together that share transitions. The output is a table containing a list of the original states,
        now grouped with their hierarchical parent state.
        """
        
        print(f"Running {self.name}")
        
        
        system_name = self.belief.get("event_driven_system_name_search_action")
        states_table = self.belief.get("event_driven_state_search_action")
        event_driven_transitions_table = self.belief.get("event_driven_parallel_regions_search_action")

        prompt = f"""
You are an expert requirements engineer specializing in designing UML state machines from textual descriptions of systems. Your task is to create a hierarchical state machine design based on the provided system information.

Here's the information for the system you need to analyze:

<system_name>
{system_name}
</system_name>

<system_description>
{self.description}
</system_description>

<states_table>
{states_table}
</states_table>

<transitions_table>
{event_driven_transitions_table}
</transitions_table>

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

{get_n_shot_examples(['printer_winter_2017'],['system_name', 'system_description', 'states_table', 'transitions_table', 'hierarchical_table'])}

Remember, your expertise in UML state machines is crucial for creating an accurate and efficient hierarchical design. The quality of your work will directly impact the success of the system's implementation. Take pride in your role as a key contributor to this important project.
"""

        print(prompt)
        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        hierarchical_state_table = None
        if "NO HIERARCHY" not in response:
            hierarchical_state_table = extract_hierarchical_state_table(llm_response=response)
        
        print(hierarchical_state_table)

        return hierarchical_state_table
