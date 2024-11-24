import sys
import os

script_dir = os.path.dirname(__file__)
resources_dir = os.path.join(script_dir, '..')
print(resources_dir)
sys.path.append(resources_dir)

from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from transitions.extensions import HierarchicalGraphMachine
from sherpa_ai.events import Event, EventType
from sherpa_ai.models import SherpaChatOpenAI
from sherpa_ai.policies.react_policy import ReactPolicy
from sherpa_ai.agents.qa_agent import QAAgent

from actions.EventDrivenSystemNameSearchAction import EventDrivenSystemNameSearchAction
from actions.EventDrivenStateSearchAction import EventDrivenStateSearchSearchAction
from actions.EventDrivenInitialStateSearchAction import EventDrivenInitialStateSearchSearchAction
from actions.EventDrivenEventSearchAction import EventDrivenEventSearchAction
from actions.EventDrivenAssociateEventsWithStatesAction import EventDrivenAssociateEventsWithStatesAction
from actions.EventDrivenCreateTransitionsAction import EventDrivenCreateTransitionsAction
from actions.EventDrivenCreateHierarchicalStatesAction import EventDrivenCreateHierarchicalStatesAction
from actions.EventDrivenHierarchicalInitialStateSearchAction import EventDrivenHierarchicalInitialStateSearchAction
from actions.EventDrivenRefactorTransitionNamesAction import EventDrivenRefactorTransitionNamesAction
from actions.EventDrivenDisplayResultsAction import EventDrivenDisplayResultsAction
from actions.EventDrivenHistoryStateSearchAction import EventDrivenHistoryStateSearchAction
from event_driven_smf_transitions import transitions
from resources.state_machine_descriptions import thermomix_fall_2021

description = thermomix_fall_2021

belief = Belief()
belief.set("description", description)
event_driven_system_name_search_action = EventDrivenSystemNameSearchAction(belief=belief,
                                                                           description=description)
event_driven_state_search_action = EventDrivenStateSearchSearchAction(belief=belief,
                                                                      description=description)
event_driven_initial_state_search_action = EventDrivenInitialStateSearchSearchAction(belief=belief,
                                                                                     description=description)
event_driven_event_search_action = EventDrivenEventSearchAction(belief=belief,
                                                                description=description)
event_driven_associate_events_with_states = EventDrivenAssociateEventsWithStatesAction(belief=belief,
                                                                                       description=description)
event_driven_create_transitions_action = EventDrivenCreateTransitionsAction(belief=belief,
                                                                            description=description)
event_driven_create_hierarchical_states_action = EventDrivenCreateHierarchicalStatesAction(belief=belief,
                                                                                           description=description)
event_driven_hierarchical_initial_state_search_action = EventDrivenHierarchicalInitialStateSearchAction(belief=belief,
                                                                                                        description=description)
event_driven_refactor_transition_names_action =  EventDrivenRefactorTransitionNamesAction(belief=belief,
                                                                                          description=description)
event_driven_history_state_search_action =  EventDrivenHistoryStateSearchAction(belief=belief,
                                                                                          description=description)
event_driven_display_results_action = EventDrivenDisplayResultsAction(belief=belief,
                                                                      description=description)

event_driven_action_map = {
    event_driven_system_name_search_action.name: event_driven_system_name_search_action,
    event_driven_state_search_action.name: event_driven_state_search_action,
    event_driven_initial_state_search_action.name: event_driven_initial_state_search_action,
    event_driven_event_search_action.name: event_driven_event_search_action,
    event_driven_associate_events_with_states.name: event_driven_associate_events_with_states,
    event_driven_create_transitions_action.name: event_driven_create_transitions_action,
    event_driven_create_hierarchical_states_action.name: event_driven_create_hierarchical_states_action,
    event_driven_hierarchical_initial_state_search_action.name: event_driven_hierarchical_initial_state_search_action,
    event_driven_refactor_transition_names_action.name: event_driven_refactor_transition_names_action,
    event_driven_history_state_search_action.name: event_driven_history_state_search_action,
    event_driven_display_results_action.name: event_driven_display_results_action
}

states = [
            "SystemNameSearch",
            "StateSearch",
            "InitialStateSearch",
            "EventSearch",
            "AssociateEventsWithStates",
            "CreateTransitions",
            "CreateHierarchicalStates",
            "HierarchicalInitialStateSearch",
            "RefactorTransitionNames",
            "HistoryStateSearch",
            "DisplayResults",
            "Done"
         ]

# create event driven state macine
initial = "SystemNameSearch"
event_driven_smf = SherpaStateMachine(states=states, 
                                      transitions=transitions, 
                                      initial=initial, 
                                      action_map=event_driven_action_map, 
                                      sm_cls=HierarchicalGraphMachine)

belief.state_machine = event_driven_smf
belief.set_current_task(Event(EventType.task, 
                              "user", 
                              "User wants to generate a UML State Machine from the provided system description and display the results at the end"))

# set up task to be run
llm = SherpaChatOpenAI(model_name="gpt-4o-mini", temperature=0.5)
policy = ReactPolicy(role_description="Help the user finish the task", output_instruction="Determine which action and arguments would be the best continuing the task", llm=llm)
qa_agent = QAAgent(llm=llm, belief=belief, num_runs=100, policy=policy)

def run_event_driven_smf():
    qa_agent.run()

if __name__ == "__main__":
    run_event_driven_smf()
