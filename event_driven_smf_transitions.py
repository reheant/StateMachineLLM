# step 1: search for system name from description using EventDrivenSystemNameSearchAction
system_name_search = {
    "trigger": "start_event_driven_system_name_search",
    "source": "SystemNameSearch",
    "dest": "StateSearch",
    "before": "event_driven_system_name_search_action",
}

# step 2: search for states of the UML State Machine from description using EventDrivenStateSearchAction
state_search = {
    "trigger": "start_event_driven_state_search",
    "source": "StateSearch",
    "dest": "InitialStateSearch",
    "before": "event_driven_state_search_action",
}

# step 3: search for the initial state of the UML State Machine using EventDrivenInitialStateSearchAction
initial_state_search = {
    "trigger": "start_event_driven_initial_state_search",
    "source": "InitialStateSearch",
    "dest": "EventSearch",
    "before": "event_driven_initial_state_search_action",
}

# step 4: search for events of the UML State Machine using EventDrivenEventSearchAction
event_search = {
    "trigger": "start_event_driven_event_search",
    "source": "EventSearch",
    "dest" : "AssociateEventsWithStates",
    "before": "event_driven_event_search_action"
}

# step 5: identify the events that can occur in each state using EventDrivenAssociateEventsWithStatesAction
associate_events_with_states = {
    "trigger": "start_event_driven_associate_events_with_states_action",
    "source": "AssociateEventsWithStates",
    "dest" : "CreateTransitions",
    "before": "event_driven_associate_events_with_states_action"
}

# step 6: create transitions based on groups of states and events using EventDrivenCreateTransitionsAction
create_transitions = {
    "trigger": "start_event_driven_create_transitions",
    "source": "CreateTransitions",
    "dest": "FilterTransitions",
    "before": "event_driven_create_transitions_action"
}

# step 7: filter the transitions created in step 6 to reduce number of false positives using EventDrivenFilterTransitionsAction
filter_transitions = {
    "trigger": "start_event_driven_filter_transitions",
    "source": "FilterTransitions",
    "dest": "CreateHierarchicalStates",
    "before": "event_driven_filter_transitions_action"
}

# step 8: using the identified transitions, create hierarchical states in the UML State Machine using EventDrivenCreateHierarchicalStatesAction
create_hierarchical_states = {
    "trigger": "start_event_driven_create_hierarchical_states",
    "source": "CreateHierarchicalStates",
    "dest": "HierarchicalInitialStateSearch",
    "before": "event_driven_create_hierarchical_states_action"
}

# step 9: identify the initial state of each hierarchical state using EventDrivenHierarchicalInitialStateSearchAction
hierarchical_initial_state_search = {
    "trigger": "start_event_driven_hierarchical_initial_state_search",
    "source": "HierarchicalInitialStateSearch",
    "dest": "RefactorTransitionNames",
    "before": "event_driven_hierarchical_initial_state_search"
}

# step 10: rename the states in the transitions table using ParentState.ChildState notation using EventDrivenRefactorTransitionNamesAction
refactor_transition_names = {
    "trigger": "start_event_driven_refactor_transition_names",
    "source": "RefactorTransitionNames",
    "dest": "HistoryStateSearch",
    "before": "event_driven_refactor_transition_names_action"
}

# step 11: identify necessary history states in the UML State Machine using EventDrivenHistoryStateSearchAction
history_state_search = {
    "trigger": "start_event_driven_history_state_search_action",
    "source": "HistoryStateSearch",
    "dest": "DisplayResults",
    "before": "event_driven_history_state_search_action"
}

# step 12: print the final tables representing the UML State Machine
display_results = {
    "trigger": "start_event_driven_display_results_action",
    "source": "DisplayResults",
    "dest": "Done",
    "before": "event_driven_display_results_action"
}

transitions = [
                system_name_search,
                state_search,
                initial_state_search,
                event_search,
                associate_events_with_states,
                create_transitions,
                filter_transitions,
                create_hierarchical_states,
                hierarchical_initial_state_search,
                refactor_transition_names,
                history_state_search,
                display_results
              ]