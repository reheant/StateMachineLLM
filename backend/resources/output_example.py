# example EventDrivenSystemNameSearchAction output
event_driven_system_name_search = 'Thermomix TM6'

# example EventDrivenStateSearchAction output table
event_driven_state_search = '''
<table border="1">
<tr> <th>State Name</th> </tr>
<tr> <td>Transportation Mode</td> </tr>
<tr> <td>Off State</td> </tr>
<tr> <td>Home Screen</td> </tr>
<tr> <td>Automatic Shutdown Warning</td> </tr>
<tr> <td>Recipe Selection</td> </tr>
<tr> <td>Ingredient Weighing</td> </tr>
<tr> <td>Chopping Ingredients</td> </tr>
<tr> <td>Cooking</td> </tr>
<tr> <td>Meal Ready</td> </tr>
<tr> <td>Error State</td> </tr>
</table>'''

# example EventDrivenInitialStateSearchAction state name
event_driven_initial_state_search = 'Transportation Mode'

# example EventDrivenEventSearchAction event table
event_driven_event_search = '''<table border="1">
<tr> <th>Event Name</th> </tr>
<tr> <td>Press Selector in Transportation Mode</td> </tr>
<tr> <td>Press Selector to Turn On</td> </tr>
<tr> <td>Hold Selector to Turn Off</td> </tr>
<tr> <td>Automatic Shutoff</td> </tr>
<tr> <td>Cancel Automatic Shutdown</td> </tr>
<tr> <td>Select Recipe</td> </tr>
<table border="1">
<tr> <th>Event Name</th> </tr>
<tr> <td>Press Selector in Transportation Mode</td> </tr>
<tr> <td>Press Selector to Turn On</td> </tr>
<tr> <td>Hold Selector to Turn Off</td> </tr>
<tr> <td>Automatic Shutoff</td> </tr>
<tr> <td>Cancel Automatic Shutdown</td> </tr>
<tr> <td>Select Recipe</td> </tr>
<tr> <td>Press Selector in Transportation Mode</td> </tr>
<tr> <td>Press Selector to Turn On</td> </tr>
<tr> <td>Hold Selector to Turn Off</td> </tr>
<tr> <td>Automatic Shutoff</td> </tr>
<tr> <td>Cancel Automatic Shutdown</td> </tr>
<tr> <td>Select Recipe</td> </tr>
<tr> <td>Hold Selector to Turn Off</td> </tr>
<tr> <td>Automatic Shutoff</td> </tr>
<tr> <td>Cancel Automatic Shutdown</td> </tr>
<tr> <td>Select Recipe</td> </tr>
<tr> <td>Add Ingredients</td> </tr>
<tr> <td>Automatic Shutoff</td> </tr>
<tr> <td>Cancel Automatic Shutdown</td> </tr>
<tr> <td>Select Recipe</td> </tr>
<tr> <td>Add Ingredients</td> </tr>
<tr> <td>Select Next Step</td> </tr>
<tr> <td>Cancel Automatic Shutdown</td> </tr>
<tr> <td>Select Recipe</td> </tr>
<tr> <td>Add Ingredients</td> </tr>
<tr> <td>Select Next Step</td> </tr>
<tr> <td>Remove Cooking Bowl</td> </tr>
<tr> <td>Add Ingredients</td> </tr>
<tr> <td>Select Next Step</td> </tr>
<tr> <td>Remove Cooking Bowl</td> </tr>
<tr> <td>Select Next Step</td> </tr>
<tr> <td>Remove Cooking Bowl</td> </tr>
</table>
<tr> <td>Remove Cooking Bowl</td> </tr>
</table>
</table>'''

# example EventDrivenCreateTransitionsAction transition table output
event_driven_create_transitions = '''
<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Transportation Mode</td><td>Home Screen</td><td>Press Selector in Transportation Mode</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Transportation Mode</td><td>Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Off State</td><td>Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Turn on and show home screen</td></tr><tr><td>Home Screen</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td> Home Screen </td><td> Off State </td><td> Automatic Shutoff </td><td> Inactivity for 15 minutes </td><td> Display warning message </td></tr><tr><td>Home Screen</td><td>Recipe Selection</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td> Home Screen </td><td> Home Screen </td><td> Remove Cooking Bowl </td><td> NONE </td><td> NONE </td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Show confirmation message</td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Automatic Shutoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Home Screen</td><td>Cancel Automatic Shutdown</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>Selector held for at least five seconds</td><td>Display shutdown confirmation message</td></tr><tr><td>Recipe Selection</td><td>Ingredient Weighing</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Ingredient Weighing</td><td>Add Ingredients</td><td>NONE</td><td>Initiate Weighing Process</td></tr><tr><td>Recipe Selection</td><td>Ingredient Weighing</td><td>Select Next Step</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Ingredient Weighing </td><td> Off State </td><td> Hold Selector to Turn Off </td><td> NONE </td><td> Display shutdown confirmation message </td></tr><tr><td>Ingredient Weighing</td><td>Chopping Ingredients</td><td>Add Ingredients</td><td>Correct Amount Added</td><td>NONE</td></tr><tr><td>Ingredient Weighing</td><td>Chopping Ingredients</td><td>Select Next Step</td><td>Correct amount of ingredients added</td><td>NONE</td></tr><tr><td>Ingredient Weighing</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Chopping Ingredients </td><td> Off State </td><td> Hold Selector to Turn Off </td><td> NONE </td><td> System turns off after confirmation </td></tr><tr><td> Chopping Ingredients </td><td> Cooking </td><td> Select Next Step </td><td> NONE </td><td> NONE </td></tr><tr><td>Chopping Ingredients</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Cooking</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td> Cooking </td><td> Ingredient Weighing </td><td> Add Ingredients </td><td> NONE </td><td> Weigh Ingredients </td></tr><tr><td>Cooking</td><td>Meal Ready</td><td>Select Next Step</td><td>NONE</td><td>Notify user that the meal is ready</td></tr><tr><td> Cooking </td><td> Home Screen </td><td> Remove Cooking Bowl </td><td> NONE </td><td> Stop Cooking Process </td></tr><tr><td>Meal Ready</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display shutdown confirmation message</td></tr><tr><td>Meal Ready</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Error State</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>if the error is not critical</td><td>Reset device</td></tr></table>
'''

# example EventDrivenFilterTransitionsAction transition table output
event_driven_filter_transitions = '''
<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Transportation Mode</td><td>Home Screen</td><td>Press Selector in Transportation Mode</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Transportation Mode</td><td>Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Off State</td><td>Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Turn on and show home screen</td></tr><tr><td>Home Screen</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td> Home Screen </td><td> Off State </td><td> Automatic Shutoff </td><td> Inactivity for 15 minutes </td><td> Display warning message </td></tr><tr><td>Home Screen</td><td>Recipe Selection</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td> Home Screen </td><td> Home Screen </td><td> Remove Cooking Bowl </td><td> NONE </td><td> NONE </td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Show confirmation message</td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Automatic Shutoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Home Screen</td><td>Cancel Automatic Shutdown</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>Selector held for at least five seconds</td><td>Display shutdown confirmation message</td></tr><tr><td>Recipe Selection</td><td>Ingredient Weighing</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Ingredient Weighing</td><td>Select Next Step</td><td>NONE</td><td>NONE</td></tr><tr><td>Recipe Selection</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Ingredient Weighing </td><td> Off State </td><td> Hold Selector to Turn Off </td><td> NONE </td><td> Display shutdown confirmation message </td></tr><tr><td>Ingredient Weighing</td><td>Chopping Ingredients</td><td>Add Ingredients</td><td>Correct Amount Added</td><td>NONE</td></tr><tr><td>Ingredient Weighing</td><td>Chopping Ingredients</td><td>Select Next Step</td><td>Correct amount of ingredients added</td><td>NONE</td></tr><tr><td>Ingredient Weighing</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td> Chopping Ingredients </td><td> Off State </td><td> Hold Selector to Turn Off </td><td> NONE </td><td> System turns off after confirmation </td></tr><tr><td> Chopping Ingredients </td><td> Cooking </td><td> Select Next Step </td><td> NONE </td><td> NONE </td></tr><tr><td>Cooking</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td> Cooking </td><td> Ingredient Weighing </td><td> Add Ingredients </td><td> NONE </td><td> Weigh Ingredients </td></tr><tr><td>Cooking</td><td>Meal Ready</td><td>Select Next Step</td><td>NONE</td><td>Notify user that the meal is ready</td></tr><tr><td> Cooking </td><td> Home Screen </td><td> Remove Cooking Bowl </td><td> NONE </td><td> Stop Cooking Process </td></tr><tr><td>Meal Ready</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display shutdown confirmation message</td></tr><tr><td>Meal Ready</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Error State</td><td>Home Screen</td><td>Remove Cooking Bowl</td><td>if the error is not critical</td><td>Reset device</td></tr></table>
'''

# example EventDrivenCreateHierarchicalStatesAction hierarchical state table output
event_driven_create_hierarchical_states = '''
<table border="1">
<tr> <th>Superstate</th> <th>Substate</th> </tr>
<tr> <td> On </td> <td> Home Screen </td> </tr>
<tr> <td> On </td> <td> Idle </td> </tr>
<tr> <td> On </td> <td> Shutdown Warning </td> </tr>
<tr> <td> Cooking Process </td> <td> Cooking Preparation </td> </tr>     
<tr> <td> Cooking Process </td> <td> Chopping </td> </tr>
<tr> <td> Cooking Process </td> <td> Cooking </td> </tr>
<tr> <td> Cooking Process </td> <td> Meal Ready </td> </tr>
<tr> <td> - </td> <td> Off </td> </tr>
<tr> <td> - </td> <td> Transportation Mode </td> </tr>
<tr> <td> - </td> <td> Error State </td> </tr>
</table>'''

# example EventDrivenHierarchicalInitialStateSearchAction hierarchical initial states dictionary output
event_driven_hierarchical_initial_state_search = '''
{'Operational': 'Home Screen'}'''

# example EventDrivenRefactorTransitionNames transitions table output
event_driven_refactor_transition_names = '''
<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Transportation Mode</td><td>Operational.Home Screen</td><td>Press Selector in Transportation Mode</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Transportation Mode</td><td>Operational.Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Off State</td><td>Operational.Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Turn on and show home screen</td></tr><tr><td>Operational.Home Screen</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Operational.Home Screen</td><td>Off State</td><td> Automatic Shutoff </td><td> Inactivity for 15 minutes </td><td> Display warning message </td></tr><tr><td>Operational.Home Screen</td><td>Operational.Recipe Selection</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Home Screen</td><td>Operational.Home Screen</td><td> Remove Cooking Bowl </td><td> NONE </td><td> NONE </td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Show confirmation message</td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Automatic Shutoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Operational.Home Screen</td><td>Cancel Automatic Shutdown</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Recipe Selection</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>Selector held for at least five seconds</td><td>Display shutdown confirmation message</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Ingredient Weighing</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Ingredient Weighing</td><td>Add Ingredients</td><td>NONE</td><td>Initiate Weighing Process</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Ingredient Weighing</td><td>Select Next Step</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Ingredient Weighing</td><td>Off State</td><td> Hold Selector to Turn Off </td><td> NONE </td><td> Display shutdown confirmation message </td></tr><tr><td>Operational.Ingredient Weighing</td><td>Operational.Chopping Ingredients</td><td>Add Ingredients</td><td>Correct Amount Added</td><td>NONE</td></tr><tr><td>Operational.Ingredient Weighing</td><td>Operational.Chopping Ingredients</td><td>Select Next Step</td><td>Correct amount of ingredients added</td><td>NONE</td></tr><tr><td>Operational.Ingredient Weighing</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Chopping Ingredients</td><td>Off State</td><td> Hold Selector to Turn Off </td><td> NONE </td><td> System turns off after confirmation </td></tr><tr><td>Operational.Chopping Ingredients</td><td>Operational.Cooking</td><td> Select Next Step </td><td> NONE </td><td> NONE </td></tr><tr><td>Operational.Chopping Ingredients</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Cooking</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Operational.Cooking</td><td>Operational.Ingredient Weighing</td><td> Add Ingredients </td><td> NONE </td><td> Weigh Ingredients </td></tr><tr><td>Operational.Cooking</td><td>Operational.Meal Ready</td><td>Select Next Step</td><td>NONE</td><td>Notify user that the meal is ready</td></tr><tr><td>Operational.Cooking</td><td>Operational.Home Screen</td><td> Remove Cooking Bowl </td><td> NONE </td><td> Stop Cooking Process </td></tr><tr><td>Operational.Meal Ready</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display shutdown confirmation message</td></tr><tr><td>Operational.Meal Ready</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Error State</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>if the error is not critical</td><td>Reset device</td></tr></table>
'''

# example console output of EventDrivenDisplayResultsAction
event_driven_display_results_action = '''
Hierarchical States Table:
<table border="1">
<tr><th>Superstate</th><th>Substate</th></tr>
<tr><td>Operational</td><td>Home Screen</td></tr>
<tr><td>Operational</td><td>Recipe Selection</td></tr>
<tr><td>Operational</td><td>Ingredient Weighing</td></tr>
<tr><td>Operational</td><td>Chopping Ingredients</td></tr>
<tr><td>Operational</td><td>Cooking</td></tr>
<tr><td>Operational</td><td>Meal Ready</td></tr>
<tr><td>-</td><td>Off State</td></tr>
<tr><td>-</td><td>Transportation Mode</td></tr>
<tr><td>-</td><td>Automatic Shutdown Warning</td></tr>
<tr><td>-</td><td>Error State</td></tr>
</table>
Initial System State: Transportation Mode
Hierarchical Initial States:
{'Operational': 'Home Screen'}
Transitions:
<table border="1"><tr><th>From State</th><th>To State</th><th>Event</th><th>Guard</th><th>Action</th></tr><tr><td>Transportation Mode</td><td>Operational.Home Screen</td><td>Press Selector in Transportation Mode</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Transportation Mode</td><td>Operational.Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Deactivate Transportation Mode and Show Home Screen</td></tr><tr><td>Off State</td><td>Operational.Home Screen</td><td>Press Selector to Turn On</td><td>NONE</td><td>Turn on and show home screen</td></tr><tr><td>Operational.Home Screen</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Operational.Home Screen</td><td>Off State</td><td> Automatic Shutoff </td><td> Inactivity for 15 minutes </td><td> Display warning message </td></tr><tr><td>Operational.Home Screen</td><td>Operational.Recipe Selection</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Home Screen</td><td>Operational.Home Screen</td><td> Remove Cooking Bowl </td><td> NONE </td><td> NONE </td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Show confirmation message</td></tr><tr><td>Automatic Shutdown Warning</td><td>Off State</td><td>Automatic Shutoff</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Operational.Home Screen</td><td>Cancel Automatic Shutdown</td><td>NONE</td><td>NONE</td></tr><tr><td>Automatic Shutdown Warning</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Recipe Selection</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>Selector held for at least five seconds</td><td>Display shutdown confirmation message</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Ingredient Weighing</td><td>Select Recipe</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Ingredient Weighing</td><td>Add Ingredients</td><td>NONE</td><td>Initiate Weighing Process</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Ingredient Weighing</td><td>Select Next Step</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Recipe Selection</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Ingredient Weighing</td><td>Off State</td><td> Hold Selector to Turn Off </td><td> NONE </td><td> Display shutdown confirmation message </td></tr><tr><td>Operational.Ingredient Weighing</td><td>Operational.Chopping Ingredients</td><td>Add Ingredients</td><td>Correct Amount Added</td><td>NONE</td></tr><tr><td>Operational.Ingredient Weighing</td><td>Operational.Chopping Ingredients</td><td>Select Next Step</td><td>Correct amount of ingredients added</td><td>NONE</td></tr><tr><td>Operational.Ingredient Weighing</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Chopping Ingredients</td><td>Off State</td><td> Hold Selector to Turn Off </td><td> NONE </td><td> System turns off after confirmation </td></tr><tr><td>Operational.Chopping Ingredients</td><td>Operational.Cooking</td><td> Select Next Step </td><td> NONE </td><td> NONE </td></tr><tr><td>Operational.Chopping Ingredients</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Operational.Cooking</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display confirmation message</td></tr><tr><td>Operational.Cooking</td><td>Operational.Ingredient Weighing</td><td> Add Ingredients </td><td> NONE </td><td> Weigh Ingredients </td></tr><tr><td>Operational.Cooking</td><td>Operational.Meal Ready</td><td>Select Next Step</td><td>NONE</td><td>Notify user that the meal is ready</td></tr><tr><td>Operational.Cooking</td><td>Operational.Home Screen</td><td> Remove Cooking Bowl </td><td> NONE </td><td> Stop Cooking Process </td></tr><tr><td>Operational.Meal Ready</td><td>Off State</td><td>Hold Selector to Turn Off</td><td>NONE</td><td>Display shutdown confirmation message</td></tr><tr><td>Operational.Meal Ready</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>NONE</td><td>NONE</td></tr><tr><td>Error State</td><td>Operational.Home Screen</td><td>Remove Cooking Bowl</td><td>if the error is not critical</td><td>Reset device</td></tr></table>
'''