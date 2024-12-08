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
from actions.EventDrivenStateSearchAction import EventDrivenStateSearchAction
from actions.EventDrivenInitialStateSearchAction import EventDrivenInitialStateSearchAction
from actions.EventDrivenEventSearchAction import EventDrivenEventSearchAction
from actions.EventDrivenAssociateEventsWithStatesAction import EventDrivenAssociateEventsWithStatesAction
from actions.EventDrivenCreateTransitionsAction import EventDrivenCreateTransitionsAction
from actions.EventDrivenCreateHierarchicalStatesAction import EventDrivenCreateHierarchicalStatesAction
from actions.EventDrivenHierarchicalInitialStateSearchAction import EventDrivenHierarchicalInitialStateSearchAction
from actions.EventDrivenDisplayResultsAction import EventDrivenDisplayResultsAction
from actions.EventDrivenFilterTransitionsAction import EventDrivenFilterTransitionsAction
from actions.EventDrivenHistoryStateSearchAction import EventDrivenHistoryStateSearchAction
from actions.EventDrivenFactorOutTransitionsForHierarchalStates import EventDrivenFactorOutTransitionsForHierarchalStates
from actions.EventDrivenParallelRegionsSearchAction import EventDrivenParallelRegionsSearchAction
from event_driven_smf_transitions import transitions
from resources.state_machine_descriptions import spa_manager_winter_2018
from resources.util import create_event_based_gsm_diagram
import time

description = spa_manager_winter_2018

belief = Belief()
belief.set("description", description)

# Sherpa actions of the Event State Machine Framework
event_driven_system_name_search_action = EventDrivenSystemNameSearchAction(belief=belief,
                                                                           description=description)
event_driven_state_search_action = EventDrivenStateSearchAction(belief=belief,
                                                                      description=description)
event_driven_initial_state_search_action = EventDrivenInitialStateSearchAction(belief=belief,
                                                                                     description=description)
event_driven_event_search_action = EventDrivenEventSearchAction(belief=belief,
                                                                description=description)
event_driven_associate_events_with_states = EventDrivenAssociateEventsWithStatesAction(belief=belief,
                                                                                       description=description)
event_driven_create_transitions_action = EventDrivenCreateTransitionsAction(belief=belief,
                                                                            description=description)
event_driven_filter_transitions_action = EventDrivenFilterTransitionsAction(belief=belief,
                                                                            description=description)
event_driven_filter_transitions_action = EventDrivenFilterTransitionsAction(belief=belief,description=description)
event_driven_parallel_regions_search_action = EventDrivenParallelRegionsSearchAction(belief=belief, description=description)
event_driven_create_hierarchical_states_action = EventDrivenCreateHierarchicalStatesAction(belief=belief,
                                                                                           description=description)
event_driven_hierarchical_initial_state_search_action = EventDrivenHierarchicalInitialStateSearchAction(belief=belief,
                                                                                                        description=description)
event_driven_factor_out_transitions_for_hierarchal_states = EventDrivenFactorOutTransitionsForHierarchalStates(belief=belief,
                                                                                          description=description)
event_driven_history_state_search_action =  EventDrivenHistoryStateSearchAction(belief=belief,
                                                                                          description=description)
event_driven_display_results_action = EventDrivenDisplayResultsAction(belief=belief,
                                                                      description=description)

# mapping between the names of Sherpa actions and their Action class
event_driven_action_map = {
    event_driven_system_name_search_action.name: event_driven_system_name_search_action,
    event_driven_state_search_action.name: event_driven_state_search_action,
    event_driven_initial_state_search_action.name: event_driven_initial_state_search_action,
    event_driven_event_search_action.name: event_driven_event_search_action,
    event_driven_associate_events_with_states.name: event_driven_associate_events_with_states,
    event_driven_create_transitions_action.name: event_driven_create_transitions_action,
    event_driven_parallel_regions_search_action.name: event_driven_parallel_regions_search_action,
    event_driven_filter_transitions_action.name: event_driven_filter_transitions_action,
    event_driven_create_hierarchical_states_action.name: event_driven_create_hierarchical_states_action,
    event_driven_hierarchical_initial_state_search_action.name: event_driven_hierarchical_initial_state_search_action,
    event_driven_factor_out_transitions_for_hierarchal_states.name: event_driven_factor_out_transitions_for_hierarchal_states,
    event_driven_history_state_search_action.name: event_driven_history_state_search_action,
    event_driven_display_results_action.name: event_driven_display_results_action
}

# states of the Event Driven State Machine Framework
states = [
            "SystemNameSearch",
            "StateSearch",
            "InitialStateSearch",
            "EventSearch",
            "AssociateEventsWithStates",
            "CreateTransitions",            
            "ParallelRegionsSearch",
            "FilterTransitions",
            "CreateHierarchicalStates",
            "HierarchicalInitialStateSearch",
            "FactorOutHierarchalTransitions",
            "HistoryStateSearch",
            "DisplayResults",
            "Done"
         ]

# create Sherpa state machine and set the task for creating a UML State Machine
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
qa_agent = QAAgent(llm=llm, belief=belief, num_runs=20, policy=policy)

def run_event_driven_smf():
    """
    the run_event_driven_smf initiates the Sherpa Event Driven State Machine Framework
    """
    try:
        # Define the base directory for logs
        base_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "event_driven_log")
        os.makedirs(base_dir, exist_ok=True)  # Ensure the directory exists

        # Construct the log file path
        log_file_name = f'output_event_driven_{time.strftime("%Y_%m_%d_%H_%M_%S")}.txt'
        log_file_path = os.path.join(base_dir, log_file_name)

        # Redirect stdout to the log file
        with open(log_file_path, 'w') as f:
            sys.stdout = f  # Redirect all print statements to the log file
            try:
                # Execute QA agent
                qa_agent.run()

                # Extract GSM state information and create the Mermaid diagram
                hierarchical_states_table = belief.get("event_driven_create_hierarchical_states_action")
                transitions_table = belief.get("event_driven_history_state_search_action")
                parallel_state_table = None
                initial_state = belief.get("event_driven_initial_state_search_action").replace(' ', '')

                create_event_based_gsm_diagram(hierarchical_states_table=hierarchical_states_table,
                                               transitions_table=transitions_table,
                                               parallel_state_table=parallel_state_table,
                                               initial_state=initial_state)
                

            finally:
                # Restore original stdout
                sys.stdout = sys.__stdout__

        print(f"Log successfully written to: {log_file_path}")

    except Exception as e:
        # Handle and print any errors that occur
        sys.stdout = sys.__stdout__  # Ensure stdout is restored before printing
        print(f"Error during event-driven logging: {e}")


if __name__ == "__main__":
    run_event_driven_smf()
