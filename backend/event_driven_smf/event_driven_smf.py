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
from actions.EventDrivenFactorOutTransitionsForHierarchalStates import EventDrivenFactorOutTransitionsForHierarchalStates
from actions.EventDrivenParallelRegionsSearchAction import EventDrivenParallelRegionsSearchAction
from event_driven_smf_transitions import transitions
from resources.state_machine_descriptions import spa_manager_winter_2018
import mermaid as md
from mermaid.graph import Graph
from resources.util import gsm_tables_to_dict
import time

description = spa_manager_winter_2018

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
event_driven_parallel_regions_search_action = EventDrivenParallelRegionsSearchAction(belief=belief, description=description)
event_driven_create_hierarchical_states_action = EventDrivenCreateHierarchicalStatesAction(belief=belief,
                                                                                           description=description)
event_driven_hierarchical_initial_state_search_action = EventDrivenHierarchicalInitialStateSearchAction(belief=belief,
                                                                                                        description=description)
event_driven_refactor_transition_names_action =  EventDrivenRefactorTransitionNamesAction(belief=belief,
                                                                                          description=description)
event_driven_factor_out_transitions_for_hierarchal_states = EventDrivenFactorOutTransitionsForHierarchalStates(belief=belief,
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
    event_driven_parallel_regions_search_action.name: event_driven_parallel_regions_search_action,
    event_driven_create_hierarchical_states_action.name: event_driven_create_hierarchical_states_action,
    event_driven_hierarchical_initial_state_search_action.name: event_driven_hierarchical_initial_state_search_action,
    event_driven_refactor_transition_names_action.name: event_driven_refactor_transition_names_action,
    event_driven_factor_out_transitions_for_hierarchal_states.name: event_driven_factor_out_transitions_for_hierarchal_states,
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
            "ParallelRegionsSearch",
            "CreateHierarchicalStates",
            "HierarchicalInitialStateSearch",
            "RefactorTransitionNames",
            "FactorOutHierarchalTransitions",
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
llm = SherpaChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
policy = ReactPolicy(role_description="Help the user finish the task", output_instruction="Determine which action and arguments would be the best continuing the task", llm=llm)
qa_agent = QAAgent(llm=llm, belief=belief, num_runs=100, policy=policy)

def run_event_driven_smf():
    with open(f'{os.path.dirname(__file__)}\\..\\resources\\event_driven_log\\output_event_driven{time.strftime("%m_%d_%H_%M_%S")}.txt', 'w') as f:
        sys.stdout = f
        qa_agent.run()

        gsm_states, gsm_transitions, gsm_parallel_regions = gsm_tables_to_dict(belief.get("event_driven_create_hierarchical_states_action"), belief.get("event_driven_history_state_search_action"), None)
        print(f"States: {gsm_states}")
        print(f"Transitions: {gsm_transitions}")
        print(f"Parallel Regions: {gsm_parallel_regions}")
        gsm = SherpaStateMachine(states=gsm_states, transitions=gsm_transitions, initial=belief.get("event_driven_initial_state_search_action").replace(' ',''), sm_cls=HierarchicalGraphMachine)
        print(gsm.sm.get_graph().draw(None))
        sequence = Graph('Sequence-diagram',gsm.sm.get_graph().draw(None))
        render = md.Mermaid(sequence)
        render.to_png('ExhibitA.png')

if __name__ == "__main__":
    run_event_driven_smf()
