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
    "dest" : "CreateTransitions",
    "before": "event_driven_event_search_action"
}

create_transitions = {
    "trigger": "start_event_driven_create_transitions",
    "source": "CreateTransitions",
    "dest": "CreateHierarchicalStates",
    "before": "event_driven_create_transitions_action"
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
    "dest": "Done",
    "before": "event_driven_hierarchical_initial_state_search"
}

refactor_transition_names = {
    "trigger": "start_event_driven_refactor_transition_names",
    "source": "RefactorTransitionNames",
    "dest": "Done",
    "before": "event_driven_refactor_transition_names_action"
}

transitions = [
                system_name_search,
                state_search,
                initial_state_search,
                event_search,
                create_transitions,
                create_hierarchical_states,
                hierarchical_initial_state_search,
                refactor_transition_names,
              ]