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
from smf_transitions import transitions

description = """
              The Thermomix TM6 is an all-in-one kitchen appliance that
              preps ingredients and cooks them to perfection.
              On delivery, the Thermomix TM6 is set to transportation
              mode. When the selector (button) is pressed to start up the
              Thermomix TM6 for the first time, the transportation
              mode is automatically deactivated, and the home screen is
              shown. To turn the Thermomix TM6 off, hold the selector
              down for at least five seconds until a message appears to
              confirm that the Thermomix TM6 is switching off. You can
              then release the selector. If the Thermomix TM6 has been
              turned off, pressing the selector turns it back on and the
              home screen is shown. To save energy, the Thermomix TM6 switches off automatically after 15
              minutes when not in use. A message appears for the last 30 seconds, allowing automatic shutdown to
              be canceled and the home screen to be shown (by selecting cancel on the appliance's screen or by
              removing the cooking bowl).
              To cook a meal, select a recipe on the screen and then select start to follow the step-by-step
              instructions. First, add ingredients as instructed. The integrated scale weighs them and allows the
              next step only if the correct amount has been added. Continue to the next step by selecting next on
              the screen. The Thermomix TM6 chops the ingredients for as long as and at the speed required for
              the recipe. When the chopping step is done, select next for the Thermomix TM6 to start the cooking
              step. Again, the Thermomix TM6 cooks the meal at the temperature and time required for the
              recipe. At the end of any recipe step, the Thermomix TM6 may prompt you to add further
              ingredients, which are then again weighed, chopped, and cooked. After the last step, the
              Thermomix TM6 informs you that the meal is ready to be served. When the cooking bowl is
              removed, the Thermomix TM6 returns to the home screen. It is not possible to cook a meal if the
              cooking bowl is not correctly placed on the Thermomix TM6.
              """

belief = Belief()
belief.set("description", description)
state_event_state_action = StateEventSearchAction(usage="identifying events in problem description for state machine", belief=belief, description=description)
# parallel_state_action = ParallelStateSearchAction(usage="identifying parallel regions in problem description for state machine", belief=belief, description=description)
transitions_guards_action = TransitionsGuardsSearchAction(usage="identifying transitions and guards in problem description for state machine", belief=belief, description=description)
action_search_action = ActionSearchAction(usage="identifying actions in problem description for state machine", belief=belief, description=description)
hierarchical_state_action = HierarchicalStateSearchAction(usage="identifying hierarchical states in problem description for state machine", belief=belief, description=description)
history_state_action = HistoryStateSearchAction(usage="identifying history states in problem description for state machine", belief=belief, description=description)
sanity_check_action = FinalSanityCheckAction(usage="compare generated state machine with problem description", belief=belief, description=description)

action_map = {
    state_event_state_action.name: state_event_state_action,
    # parallel_state_action.name: parallel_state_action,
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

qa_agent.run()