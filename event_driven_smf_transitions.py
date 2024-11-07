states_events = {
    "trigger": "start_event_driven_system_name_search",
    "source": "SystemNameSearch",
    "dest": "Done",
    "before": "event_driven_system_name_search_action",
}

transitions = [
                states_events
              ]