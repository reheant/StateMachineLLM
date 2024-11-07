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
    "dest" : "Done",
    "before": "event_driven_event_search_action"
}

transitions = [
                system_name_search,
                state_search,
                initial_state_search,
                event_search
              ]