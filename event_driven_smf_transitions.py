system_name_search = {
    "trigger": "start_event_driven_system_name_search",
    "source": "SystemNameSearch",
    "dest": "StateSearch",
    "before": "event_driven_system_name_search_action",
}

state_search = {
    "trigger": "start_event_driven_state_search",
    "source": "StateSearch",
    "dest": "InitialStateSearch",
    "before": "event_driven_state_search_action",
}

initial_state_search = {
    "trigger": "start_event_driven_initial_state_search",
    "source": "InitialStateSearch",
    "dest": "EventSearch",
    "before": "event_driven_initial_state_search_action",
}

event_search = {
    "trigger": "start_event_driven_event_search",
    "source": "EventSearch",
    "dest" : "AssociateEventsWithStates",
    "before": "event_driven_event_search_action"
}

associate_events_with_states = {
    "trigger": "start_event_driven_associate_events_with_states_action",
    "source": "AssociateEventsWithStates",
    "dest" : "CreateTransitions",
    "before": "event_driven_associate_events_with_states_action"
}

create_transitions = {
    "trigger": "start_event_driven_create_transitions",
    "source": "CreateTransitions",
    "dest": "FilterTransitions",
    "before": "event_driven_create_transitions_action"
}

filter_transitions = {
    "trigger": "start_event_driven_filter_transitions",
    "source": "FilterTransitions",
    "dest": "CreateHierarchicalStates",
    "before": "event_driven_filter_transitions_action"
}

create_hierarchical_states = {
    "trigger": "start_event_driven_create_hierarchical_states",
    "source": "CreateHierarchicalStates",
    "dest": "HierarchicalInitialStateSearch",
    "before": "event_driven_create_hierarchical_states_action"
}

hierarchical_initial_state_search = {
    "trigger": "start_event_driven_hierarchical_initial_state_search",
    "source": "HierarchicalInitialStateSearch",
    "dest": "RefactorTransitionNames",
    "before": "event_driven_hierarchical_initial_state_search"
}

refactor_transition_names = {
    "trigger": "start_event_driven_refactor_transition_names",
    "source": "RefactorTransitionNames",
    "dest": "HistoryStateSearch",
    "before": "event_driven_refactor_transition_names_action"
}

history_state_search = {
    "trigger": "start_event_driven_history_state_search_action",
    "source": "HistoryStateSearch",
    "dest": "DisplayResults",
    "before": "event_driven_history_state_search_action"
}

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