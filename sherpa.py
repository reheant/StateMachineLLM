from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from transitions.extensions import HierarchicalGraphMachine
from sherpa_ai.models import SherpaChatOpenAI
from sherpa_ai.policies.react_policy import ReactPolicy
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import Event, EventType
from sherpa_ai.memory import SharedMemory

from sherpa_ai.actions.base import BaseAction

class StateSearch(BaseAction):
    name: str = "do_search_states"
    args: dict = {}
    usage: str = "identify states in microwave system"

    def execute(self):
        print(f"On, Off")
        return f"On, Off"
    
belief = Belief()
search_state_action = StateSearch(usage="identifying states in typical microwave state machine", belief=belief)

action_map = {
    search_state_action.name: search_state_action
}

states = ["States", "Done"]
initial = "States"
transitions = [{
    "trigger": "do_search_states",
    "source": "States",
    "dest": "Done",
    "before": "do_search_states",
}]

sm = SherpaStateMachine(
    states=states,
    transitions=transitions,
    initial=initial,
    action_map=action_map,
    sm_cls=HierarchicalGraphMachine,
)
belief.state_machine = sm
print(sm.sm.get_graph().draw(None))

llm = SherpaChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
policy = ReactPolicy(
    role_description="Help the user finish the task",
    output_instruction="Determine which action and arguments would be the best continuing the task",
    llm=llm,
)

belief.get_actions()

qa_agent = QAAgent(llm=llm, belief=belief, num_runs=1, policy=policy)

belief.set_current_task(Event(EventType.task, "user", "User wants to identify the states in a state machine for a typical microwave"))
sharedmemory = SharedMemory(objective="User wants to identify the states in a state machine for a typical microwave")

print(qa_agent.run())