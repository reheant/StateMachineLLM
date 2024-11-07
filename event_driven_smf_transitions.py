system_name_search = {
    "trigger": "start_event_driven_system_name_search",
    "source": "SystemNameSearch",
    "dest": "StateSearch",
    "before": "event_driven_system_name_search_action",
}

state_search = {
    "trigger": "start_event_driven_state_search",
    "source": "StateSearch",
    "dest": "Done",
    "before": "event_driven_state_search_action",
}

transitions = [
                system_name_search,
                state_search
              ]