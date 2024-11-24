import sys
import os

script_dir = os.path.dirname(__file__)
resources_dir = os.path.join(script_dir, '..')
print(resources_dir)
sys.path.append(resources_dir)

from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from transitions.extensions import HierarchicalGraphMachine
from sherpa_ai.models import SherpaChatOpenAI
from sherpa_ai.policies.react_policy import ReactPolicy
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import Event, EventType
from actions.StateEventSearchAction import StateEventSearchAction
from actions.ParallelRegionSearchAction import ParallelStateSearchAction
from actions.TransitionsGuardsSearchAction import TransitionsGuardsSearchAction
from actions.ActionSearchAction import ActionSearchAction
from actions.HierarchicalStateSearchAction import HierarchicalStateSearchAction
from actions.HistoryStateSearchAction import HistoryStateSearchAction
from actions.FinalSanityCheckAction import FinalSanityCheckAction
from simple_linear_smf_transitions import transitions
from resources.util import gsm_tables_to_dict
import mermaid as md
from mermaid.graph import Graph
from resources.state_machine_descriptions import *


description = thermomix_fall_2021

belief = Belief()
belief.set("description", description)
state_event_state_action = StateEventSearchAction(usage="identifying events in problem description for state machine", belief=belief, description=description)
parallel_state_action = ParallelStateSearchAction(usage="identifying parallel regions in problem description for state machine", belief=belief, description=description)
transitions_guards_action = TransitionsGuardsSearchAction(usage="identifying transitions and guards in problem description for state machine", belief=belief, description=description)
action_search_action = ActionSearchAction(usage="identifying actions in problem description for state machine", belief=belief, description=description)
hierarchical_state_action = HierarchicalStateSearchAction(usage="identifying hierarchical states in problem description for state machine", belief=belief, description=description)
history_state_action = HistoryStateSearchAction(usage="identifying history states in problem description for state machine", belief=belief, description=description)
sanity_check_action = FinalSanityCheckAction(usage="compare generated state machine with problem description", belief=belief, description=description)

action_map = {
    state_event_state_action.name: state_event_state_action,
    parallel_state_action.name: parallel_state_action,
    transitions_guards_action.name: transitions_guards_action,
    action_search_action.name: action_search_action,
    hierarchical_state_action.name: hierarchical_state_action,
    history_state_action.name: history_state_action,
    sanity_check_action.name: sanity_check_action
}
 
states = ["SearchStatesEvents", "ParallelRegions", "TransitionsGuards", "FiguringActions", "HierarchicalStates", "HistoryStates", "SanityCheck", "Done"]
initial = "SearchStatesEvents"

sm = SherpaStateMachine(states=states, transitions=transitions, initial=initial, action_map=action_map, sm_cls=HierarchicalGraphMachine)
belief.state_machine = sm
belief.set_current_task(Event(EventType.task, "user", "User wants to generate a state machine for a Thermomix"))

llm = SherpaChatOpenAI(model_name="gpt-4o-mini", temperature=0.5)
policy = ReactPolicy(role_description="Help the user finish the task", output_instruction="Determine which action and arguments would be the best continuing the task", llm=llm)

qa_agent = QAAgent(llm=llm, belief=belief, num_runs=10, policy=policy)

def run_sherpa_task():
    print(qa_agent.run())

    gsm_states, gsm_transitions, gsm_parallel_regions = gsm_tables_to_dict(*belief.get("sanity_check_action"))
    print(f"States: {gsm_states}")
    print(f"Transitions: {gsm_transitions}")
    print(f"Parallel Regions: {gsm_parallel_regions}")
    gsm = SherpaStateMachine(states=gsm_states, transitions=gsm_transitions, initial=[sms for sms in gsm_states if not isinstance(sms, dict)][0], sm_cls=HierarchicalGraphMachine)
    print(gsm.sm.get_graph().draw(None))
    sequence = Graph('Sequence-diagram',gsm.sm.get_graph().draw(None))
    render = md.Mermaid(sequence)
    render.to_png('ExhibitA.png')

if __name__ == "__main__":
    run_sherpa_task()
    