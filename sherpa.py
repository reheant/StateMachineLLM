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
from actions.SanityCheckAction import SanityCheckAction
from smf_transitions import transitions

belief = Belief()
state_event_state_action = StateEventSearchAction(usage="identifying events in problem description for state machine", belief=belief)
parallel_state_action = ParallelStateSearchAction(usage="identifying parallel regions in problem description for state machine", belief=belief)
transitions_guards_action = TransitionsGuardsSearchAction(usage="identifying transitions and guards in problem description for state machine", belief=belief)
action_search_action = ActionSearchAction(usage="identifying actions in problem description for state machine", belief=belief)
hierarchical_state_action = HierarchicalStateSearchAction(usage="identifying hierarchical states in problem description for state machine", belief=belief)
history_state_action = HistoryStateSearchAction(usage="identifying history states in problem description for state machine", belief=belief)
sanity_check_action = SanityCheckAction(usage="compare generated state machine with problem description", belief=belief)

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
belief.set_current_task(Event(EventType.task, "user", "User wants to generate a state machine for a typical microwave"))

llm = SherpaChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
policy = ReactPolicy(role_description="Help the user finish the task", output_instruction="Determine which action and arguments would be the best continuing the task", llm=llm)

qa_agent = QAAgent(llm=llm, belief=belief, num_runs=9, policy=policy)

print(qa_agent.run())