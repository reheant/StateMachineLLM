from sherpa_ai.actions.base import BaseAction
from util import call_gpt4, extract_hierarchical_state_table

class EventDrivenCreateHierarchicalStatesAction(BaseAction):
    name: str = "event_driven_create_hierarchical_states_action"
    args: dict = {}
    usage: str = "Given a description of a system, the states of the system, and the transitions of the system, identify all Hierarchical States in the UML state machine of the system."
    description: str = ""

    def execute(self):
        print(f"Running {self.name}")

        example_transitions_table = '<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Transportation Mode</td><td>Home Screen</td><td>PressSelectorToStart</td><td>NONE</td><td>Deactivate Transportation Mode</td></tr><tr><td>Transportation Mode</td><td>Home Screen</td><td>PressSelectorToTurnOn</td><td>NONE</td><td>NONE</td></tr><tr><td>Home Screen</td><td>Off State</td><td>HoldSelectorToTurnOff</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Home Screen</td><td>Off State</td><td>AutomaticShutdown</td><td>NONE</td><td>Display warning message for 30 seconds</td></tr><tr><td>Home Screen</td><td>Home Screen</td><td>CancelAutomaticShutdown</td><td>Automatic shutdown warning active</td><td>Dismiss automatic shutdown warning</td></tr><tr><td>Home Screen</td><td>Recipe Selection</td><td>SelectRecipe</td><td>NONE</td><td>NONE</td></tr><tr><td> Home Screen </td><td> Recipe Selection </td><td> PlaceCookingBowl </td><td> NONE </td><td> NONE </td></tr><tr><td>Off State</td><td>Home Screen</td><td>PressSelectorToStart</td><td>NONE</td><td>Show Home Screen</td></tr><tr><td> Off State </td><td> Home Screen </td><td> PressSelectorToTurnOn </td><td> NONE </td><td> NONE </td></tr><tr><td> On State </td><td> Off State </td><td> HoldSelectorToTurnOff </td><td> NONE </td><td> NONE </td></tr><tr><td>On State</td><td>Off State</td><td>AutomaticShutdown</td><td>Inactive for 15 minutes</td><td>Display shutdown warning message</td></tr><tr><td>On State</td><td>Recipe Selection</td><td>SelectRecipe</td><td>NONE</td><td>NONE</td></tr><tr><td>On State</td><td>Home Screen (Post-Cooking)</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td>On State</td><td>Home Screen</td><td>PlaceCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>HoldSelectorToTurnOff</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>AutomaticShutdown</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Home Screen</td><td>CancelAutomaticShutdown</td><td>NONE</td><td>NONE</td></tr><tr><td> Automatic Shutdown Warning </td><td> Home Screen </td><td> RemoveCookingBowl </td><td> NONE </td><td> Display Home Screen </td></tr><tr><td>Automatic Shutdown Warning</td><td>Home Screen</td><td>PlaceCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Recipe Selection </td><td> Off State </td><td> HoldSelectorToTurnOff </td><td> NONE </td><td> Display shutdown confirmation message </td></tr><tr><td>Recipe Selection</td><td>Ingredient Addition</td><td>SelectRecipe</td><td>NONE</td><td>NONE</td></tr><tr><td> Recipe Selection </td><td> Ingredient Addition </td><td> AddIngredients </td><td> NONE </td><td> NONE </td></tr><tr><td>Recipe Selection</td><td>Home Screen</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Ingredient Addition</td><td>PlaceCookingBowl</td><td>Cooking bowl correctly placed</td><td>NONE</td></tr><tr><td>Ingredient Addition</td><td>Off State</td><td>HoldSelectorToTurnOff</td><td>NONE</td><td>Show confirmation message and power down</td></tr><tr><td>Ingredient Addition</td><td>Chopping</td><td>AddIngredients</td><td>Correct amount of ingredients added</td><td>NONE</td></tr><tr><td> Ingredient Addition </td><td> Chopping </td><td> SelectNextStep </td><td> NONE </td><td> NONE </td></tr><tr><td>Ingredient Addition</td><td>Home Screen</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Chopping</td><td>Off State</td><td>HoldSelectorToTurnOff</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Chopping</td><td>Cooking</td><td>SelectNextStep</td><td>NONE</td><td>NONE</td></tr><tr><td>Chopping</td><td>Error State</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Cooking</td><td>Off State</td><td>HoldSelectorToTurnOff</td><td>NONE</td><td>Display message to confirm switching off</td></tr><tr><td>Cooking</td><td>Ingredient Addition</td><td>AddIngredients</td><td>System prompts user</td><td>NONE</td></tr><tr><td> Cooking </td><td> Meal Ready </td><td> SelectNextStep </td><td> NONE </td><td> NONE </td></tr><tr><td>Cooking</td><td>Home Screen (Post-Cooking)</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Meal Ready </td><td> Off State </td><td> HoldSelectorToTurnOff </td><td> NONE </td><td> Display shutdown confirmation message </td></tr><tr><td>Meal Ready</td><td>Off State</td><td>AutomaticShutdown</td><td>Idle for 15 minutes</td><td>Display shutdown message</td></tr><tr><td>Meal Ready</td><td>Home Screen (Post-Cooking)</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Home Screen (Post-Cooking) </td><td> Off State </td><td> HoldSelectorToTurnOff </td><td> NONE </td><td> Display switch-off confirmation message </td></tr><tr><td>Home Screen (Post-Cooking)</td><td>Off State</td><td>AutomaticShutdown</td><td>NONE</td><td>Message appears for last 30 seconds</td></tr><tr><td>Home Screen (Post-Cooking)</td><td>Recipe Selection</td><td>SelectRecipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Home Screen (Post-Cooking)</td><td>Home Screen</td><td>RemoveCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Home Screen (Post-Cooking)</td><td>Home Screen</td><td>PlaceCookingBowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Error State </td><td> Home Screen </td><td> PlaceCookingBowl </td><td> NONE </td><td> NONE </td></tr></table>'
        example_states_table = '<table border="1"><tr><th>State Name</th></tr><tr><td>Transportation Mode</td></tr><tr><td>Home Screen</td></tr><tr><td>Off State</td></tr><tr><td>On State</td></tr><tr><td>Automatic Shutdown Warning</td></tr><tr><td>Recipe Selection</td></tr><tr><td>Ingredient Addition</td></tr><tr><td>Chopping</td></tr><tr><td>Cooking</td></tr><tr><td>Meal Ready</td></tr><tr><td>Home Screen (Post-Cooking)</td></tr><tr><td>Error State</td></tr></table>'
        
        
        system_name = self.belief.get("event_driven_system_name_search_action")
        event_driven_states_table = self.belief.get("event_driven_state_search_action", example_states_table)
        event_driven_transitions_table = self.belief.get("event_driven_create_transitions_action", example_transitions_table)

        prompt = f"""
        You are an AI assistant specialized in designing UML state machines from a textual description of a system. Given the description of the system, the states of the system, and the transitions of the system, your task is to solve a question answering task.

        Name of the system:
        {system_name}

        Description of the system:
        {self.description}

        The table of identified transitions is:
        {event_driven_transitions_table}

        Solution structure:
        1. Begin the response with "Let's think step by step."
        2. Using the transitions in the identified transitions table, determine if the state machine can be modified into a Hierarchical State Machine. Hierarchical state machine design captures the commonality by organizing the states as a hierarchy. The states at the higher level in hierarchy perform the common message handling, while the lower level states inherit the commonality from higher level ones and perform the state specific functions.
        3. If the state machine CANNOT be modified into a Hierarchical State Machine, reply with "NO HIERARCHY".
        4. If the state machine CAN be modified into a Hierarchical State Machine, output a table with the following format:
        
        ```html <table border="1"> 
        <tr> <th>Superstate</th> <th>Substate</th> </tr> 
        <tr> <td> State1 </td> <td> State2 </td> </tr> 
        <tr> <td> State3 </td> <td> State4 </td> </tr>
        <tr> <td> - </td> <td> State5 </td> </tr>
        </table> ```

        Your solution MUST be in the above format, otherwise it will be rejected. For the solution, ALL states from the original table of identified transitions MUST appear in the "Substate" column EXACTLY ONCE; otherwise, your solution will be rejected. If a state from the original table of identified transitions DOES NOT have a parent state in your design of the Hierarchical State Machine, enter "-" in the "Superstate" column, as demonstrated in the example above.
        """

        response = call_gpt4(prompt=prompt,
                             temperature=0.7)
        
        if "NO HIERARCHY" not in response:
            hierarchical_state_table = extract_hierarchical_state_table(llm_response=response)
        
        print(hierarchical_state_table)

        return hierarchical_state_table