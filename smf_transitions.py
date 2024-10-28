states_events = {
    "trigger": "start_state_event_search",
    "source": "SearchStatesEvents",
    "dest": "ParallelRegions",
    "before": "state_event_search_action",
}

parallel_regions = {
    "trigger": "start_parallel_regions",
    "source": "ParallelRegions",
    "dest": "TransitionsGuards",
    "before": "parallel_state_search_action",
}

transition_guards = {
    "trigger": "start_transition_guards",
    "source": "TransitionsGuards",
    "dest": "FiguringActions",
    "before": "transitions_guards_search_action",
}

actions = {
    "trigger": "start_finding_actions",
    "source": "FiguringActions",
    "dest": "HierarchicalStates",
    "before": "action_search_action",
}

hierarchical_states = {
    "trigger": "start_hierarchical_states",
    "source": "HierarchicalStates",
    "dest": "HistoryStates",
    "before": "hierarchical_state_search_action",
}

history_states = {
    "trigger": "start_history_states",
    "source": "HistoryStates",
    "dest": "SanityCheck",
    "before": "history_state_search_action",
}

sanity_check = {
    "trigger": "start_sanity_check",
    "source": "SanityCheck",
    "dest": "Done",
    "before": "sanity_check_action",
}

transitions = [states_events, parallel_regions, transition_guards, actions, hierarchical_states, history_states, sanity_check]