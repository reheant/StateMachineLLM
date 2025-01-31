import sys
import os
import time

from sherpa_ai.memory.belief import Belief
from sherpa_ai.memory.state_machine import SherpaStateMachine
from sherpa_ai.models import SherpaChatOpenAI
from sherpa_ai.policies.react_policy import ReactPolicy
from sherpa_ai.agents.qa_agent import QAAgent
from sherpa_ai.events import Event, EventType
from transitions.extensions import HierarchicalGraphMachine
import mermaid as md
from mermaid.graph import Graph

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from actions.StateEventSearchAction import StateEventSearchAction
from actions.ParallelRegionSearchAction import ParallelStateSearchAction
from actions.TransitionsGuardsSearchAction import TransitionsGuardsSearchAction
from actions.ActionSearchAction import ActionSearchAction
from actions.HierarchicalStateSearchAction import HierarchicalStateSearchAction
from actions.HistoryStateSearchAction import HistoryStateSearchAction
from actions.FinalSanityCheckAction import FinalSanityCheckAction
from actions.InitialStateSearchAction import InitialStateSearchAction
from actions.AutomatedGenerationAction import AutomatedGenerationAction
from simple_linear_smf_transitions import transitions
from resources.util import create_simple_linear_gsm_diagram, map_state_to_pytransitions_name
import mermaid as md
from mermaid.graph import Graph
from resources.state_machine_descriptions import *
from resources.environmental_impact.impact_tracker import tracker
from resources.n_shot_examples_simple_linear import n_shot_examples

# Default description if not ran with Chainlit
description = spa_manager_winter_2018

def run_simple_linear_smf(system_prompt):
    """
    the run_event_driven_smf initiates the Simple Linear State Machine Framework
    """

    # Define the base directory for logs
    log_base_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "simple_linear_log")
    os.makedirs(log_base_dir, exist_ok=True)  # Ensure the directory exists

    # Construct the log file path
    file_prefix = f'output_simple_linear_{time.strftime("%Y_%m_%d_%H_%M_%S")}'
    log_file_name = f"{file_prefix}.txt"
    log_file_path = os.path.join(log_base_dir, log_file_name)

    # construct the diagram file path
    diagram_base_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "simple_linear_diagrams")
    os.makedirs(diagram_base_dir, exist_ok=True)  # Ensure the directory exists
    diagram_file_name = f"{file_prefix}.png"
    diagram_file_path = os.path.join(diagram_base_dir, diagram_file_name)

    belief = Belief()
    belief.set("description", system_prompt)

    # Prepare the list of example to provide to the LLM (N shot prompting)
    n_shot_examples_simple_linear = list(n_shot_examples.keys()) # Extract all the examples available
    for n_shot_example in n_shot_examples_simple_linear:
        #Remove an example if it is identical to the one being analyzed by the SMF
        #Otherwise, if no examples are identical to the one being analyzed we remove
        #the last example to have a consistent number of examples used for all systems analyzed
        #(N-shot prompting with fixed N)
        if n_shot_examples[n_shot_example]["system_description"] == system_prompt \
        or n_shot_example == n_shot_examples_simple_linear[-1]:
            n_shot_examples_simple_linear.remove(n_shot_example)
            break
    belief.set("n_shot_examples", n_shot_examples_simple_linear)

    # Sherpa actions of the Linear State Machine Framework
    state_event_state_action = StateEventSearchAction(usage="identifying events in problem description for state machine", 
                                                      belief=belief, 
                                                      description=system_prompt,
                                                      log_file_path=log_file_path)
    parallel_state_action = ParallelStateSearchAction(usage="identifying parallel regions in problem description for state machine", 
                                                      belief=belief, 
                                                      description=system_prompt,
                                                      log_file_path=log_file_path)
    transitions_guards_action = TransitionsGuardsSearchAction(usage="identifying transitions and guards in problem description for state machine", 
                                                              belief=belief, 
                                                              description=system_prompt,
                                                              log_file_path=log_file_path)
    action_search_action = ActionSearchAction(usage="identifying actions in problem description for state machine", 
                                              belief=belief, 
                                              description=system_prompt,
                                              log_file_path=log_file_path)
    hierarchical_state_action = HierarchicalStateSearchAction(usage="identifying hierarchical states in problem description for state machine", 
                                                              belief=belief, 
                                                              description=system_prompt,
                                                              log_file_path=log_file_path)
    history_state_action = HistoryStateSearchAction(usage="identifying history states in problem description for state machine", 
                                                    belief=belief, 
                                                    description=system_prompt,
                                                    log_file_path=log_file_path)
    initial_state_search_action = InitialStateSearchAction(usage="identifying initial state in state machine", 
                                                           belief=belief, 
                                                           description=system_prompt,
                                                           log_file_path=log_file_path)
    sanity_check_action = FinalSanityCheckAction(usage="compare generated state machine with problem description", 
                                                 belief=belief, 
                                                 description=system_prompt,
                                                 log_file_path=log_file_path)
    automated_generation_action = AutomatedGenerationAction(usage="automatically generate umple code from state machine", 
                                                            belief=belief, 
                                                            description=system_prompt,
                                                            log_file_path=log_file_path)

    # mapping between the names of Sherpa actions and their Action class
    action_map = {
        state_event_state_action.name: state_event_state_action,
        parallel_state_action.name: parallel_state_action,
        transitions_guards_action.name: transitions_guards_action,
        action_search_action.name: action_search_action,
        hierarchical_state_action.name: hierarchical_state_action,
        history_state_action.name: history_state_action,
        initial_state_search_action.name: initial_state_search_action,
        sanity_check_action.name: sanity_check_action,
        automated_generation_action.name: automated_generation_action
    }

    # states of the Linear State Machine Framework
    states = [
                "SearchStatesEvents", 
                "ParallelRegions", 
                "TransitionsGuards", 
                "FiguringActions", 
                "HierarchicalStates", 
                "HistoryStates", 
                "InitialStateSearch",
                "SanityCheck", 
                "Code Generation"
                "Done"
            ]
    initial = "SearchStatesEvents"

    # create Sherpa state machine and set the task for creating a UML State Machine
    sm = SherpaStateMachine(states=states, transitions=transitions, initial=initial, action_map=action_map, sm_cls=HierarchicalGraphMachine)
    belief.state_machine = sm
    belief.set_current_task(Event(EventType.task, "user", "User wants to generate a UML State Machine from the provided system description and display the results at the end"))

    llm = SherpaChatOpenAI(model_name="gpt-4o-mini", temperature=0.5)
    policy = ReactPolicy(role_description="Help the user finish the task", output_instruction="Determine which action and arguments would be the best continuing the task", llm=llm)

    qa_agent = QAAgent(llm=llm, belief=belief, num_runs=10, policy=policy)
        
    qa_agent.run()

    
    print(belief.get("automated_generation_action"))
    # Commented out to test run_simple_linear_smf
    # initial_state = belief.get("initial_state_search_action")
    # create_simple_linear_gsm_diagram(
    #     *belief.get("sanity_check_action"),
    #     initial_state,
    #     hierarchical_initial_states={},
    #     diagram_file_path=diagram_file_path
    # )

    tracker.print_metrics()

if __name__ == "__main__":
    run_simple_linear_smf(description)