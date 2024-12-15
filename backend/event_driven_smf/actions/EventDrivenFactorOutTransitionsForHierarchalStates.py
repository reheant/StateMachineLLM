
from sherpa_ai.actions.base import BaseAction
from resources.util import parse_html_table, getStateHierarchyDictFromList, dict_to_html_table
from collections import defaultdict
import copy

class EventDrivenFactorOutTransitionsForHierarchalStates(BaseAction):
    name: str = "event_driven_factor_out_transitions_for_hierarchal_states_action"
    args: dict = {}
    usage: str = "Given a description of a system and the identified transitions of the system, factor out transitions from substates to superstates"
    description: str = ""

    def execute(self):
        print(f"Running {self.name}...")

        event_driven_transitions = str(self.belief.get("event_driven_create_transitions_action"))
        state_hierarchy = str(self.belief.get("event_driven_create_hierarchical_states_action"))

        transitions_list = parse_html_table(event_driven_transitions)
        state_hierarchy_list = parse_html_table(state_hierarchy)
        state_hierarchy_dict = getStateHierarchyDictFromList(state_hierarchy_list)

        res = factor_transitions(transitions_list, state_hierarchy_dict)
        html_table = dict_to_html_table(res)

        return html_table

def factor_transitions(transitions, hierarchy):
    substate_to_superstate = {}
    for superstate, substates in hierarchy.items():
        for substate in substates:
            substate_to_superstate[substate] = superstate

    modified_transitions = copy.deepcopy(transitions)

    for superstate, substates in hierarchy.items():
        substates_set = set(substates)
        substate_transitions = defaultdict(set)
        for t in transitions:
            from_state = t['FromState']
            if from_state in substates_set:
                key = (t['ToState'], t['Event'], t['Guard'], t['Action'])
                substate_transitions[key].add(from_state)

        common_transitions = []
        for key, from_states in substate_transitions.items():
            if from_states == substates_set:
                common_transition = {
                    'FromState': superstate,
                    'ToState': key[0],
                    'Event': key[1],
                    'Guard': key[2],
                    'Action': key[3]
                }
                common_transitions.append(common_transition)

                modified_transitions = [
                    t for t in modified_transitions if not (
                        t['FromState'] in substates_set and
                        t['ToState'] == key[0] and
                        t['Event'] == key[1] and
                        t['Guard'] == key[2] and
                        t['Action'] == key[3]
                    )
                ]

        modified_transitions.extend(common_transitions)

    return modified_transitions
