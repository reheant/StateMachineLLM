# step 1: identify the states and events of the UML State Machine in a "From State" to "To State" manner using StateEventSearchAction
states_events = {
    "trigger": "start_state_event_search",
    "source": "SearchStatesEvents",
    "dest": "ParallelRegions",
    "before": "state_event_search_action",
}

# step 2: identify the parallel states of the UML State Machine using ParallelRegionSearchAction
parallel_regions = {
    "trigger": "start_parallel_regions",
    "source": "ParallelRegions",
    "dest": "TransitionsGuards",
    "before": "parallel_state_search_action",
}

# step 3: identify the transitions along with their guards of the UML State Machine using TransitionsGuardsSearchAction
transition_guards = {
    "trigger": "start_transition_guards",
    "source": "TransitionsGuards",
    "dest": "FiguringActions",
    "before": "transitions_guards_search_action",
}

# step 4: add actions to identified transitions using ActionSearchAction
actions = {
    "trigger": "start_finding_actions",
    "source": "FiguringActions",
    "dest": "HierarchicalStates",
    "before": "action_search_action",
}

# step 5: group similar states using HierarchicalStateSearchAction
hierarchical_states = {
    "trigger": "start_hierarchical_states",
    "source": "HierarchicalStates",
    "dest": "HistoryStates",
    "before": "hierarchical_state_search_action",
}

# step 6: identify history states using HistoryStateSearchAction
history_states = {
    "trigger": "start_history_states",
    "source": "HistoryStates",
    "dest": "SanityCheck",
    "before": "history_state_search_action",
}

# step 7: ask LLM to revise its created tables using FinalSanityCheckAction
sanity_check = {
    "trigger": "start_sanity_check",
    "source": "SanityCheck",
    "dest": "Done",
    "before": "sanity_check_action",
}

transitions = [
                states_events, 
                parallel_regions, 
                transition_guards, 
                actions, 
                hierarchical_states,
                history_states,
                sanity_check
               ]