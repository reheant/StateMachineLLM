"""
Convert mermaid-parser-py JSON output to Sherpa state machine format
"""
import re
from mermaid_parser import MermaidParser


def parse_mermaid_with_library(mermaid_code: str):
    """
    Parse Mermaid stateDiagram-v2 using mermaid-parser-py library
    and convert to Sherpa-compatible format.

    Returns: (states_list, transitions_list, hierarchical_dict, initial_state, parallel_regions)
    """
    parser = MermaidParser()
    parsed = parser.parse(mermaid_code)

    graph_data = parsed.get('graph_data', {})
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])

    # Track states and their hierarchical relationships
    all_states = set()
    hierarchical_states = {}  # parent -> [children]
    initial_state = None
    transitions = []
    parallel_regions = []  # Format: [{'name': 'ParentState', 'parallel': [{'name': 'Region1', 'children': [...]}, ...]}]
    state_parents = {}  # state -> parent mapping
    divider_count = graph_data.get('dividerCnt', 0)

    # Step 1: Detect parallel regions from dividers
    # When mermaid-parser-py sees parallel regions (separated by --), it creates:
    # - A composite state named "divider-id-X" for the first region
    # - Auto-generated composite states for subsequent regions
    # All these region containers are children of the parent composite state
    parallel_state_regions = {}  # parent_state -> [{'name': region_container, 'children': [states]}, ...]
    divider_containers = set()  # Track which states are parallel region containers

    if divider_count > 0:
        # Find all divider containers and auto-generated region containers
        for node in nodes:
            node_id = node['id']
            parent_id = node.get('parentId')

            # Check if this is a divider container or auto-generated region container
            if (node_id.startswith('divider-id-') or
                (node.get('isGroup', False) and parent_id and
                 any(n['id'].startswith('divider-id-') and n.get('parentId') == parent_id for n in nodes))):

                if parent_id:
                    divider_containers.add(node_id)

                    # This container is a parallel region
                    if parent_id not in parallel_state_regions:
                        parallel_state_regions[parent_id] = []

                    # Collect children of this region container
                    region_children = []
                    for child_node in nodes:
                        if (child_node.get('parentId') == node_id and
                            not child_node['id'].endswith('_start') and
                            not child_node['id'].endswith('_end')):
                            region_children.append(child_node['id'])

                    if region_children:
                        parallel_state_regions[parent_id].append({
                            'name': node_id,
                            'children': region_children
                        })

    # Step 2: Build parent-child relationships using parentId from nodes
    # TODO: Currently mermaid-parser-py has a bug where parentId is set for states
    # referenced in transitions even if they're siblings. This will be fixed in the future.
    for node in nodes:
        node_id = node['id']

        # Skip start/end nodes, note nodes, dividers, and parallel region containers
        if (node_id.endswith('_start') or
            node_id.endswith('_end') or
            '----note-' in node_id or
            '----parent' in node_id or
            node_id in divider_containers):
            continue

        # Add to all states (but skip history state markers like StateName.H)
        if not (node_id.endswith('.H') or node_id.endswith('_H')):
            all_states.add(node_id)

        # Check if this is a composite state (but not a parallel region container)
        if node.get('isGroup', False):
            if node_id not in hierarchical_states:
                hierarchical_states[node_id] = []

        # Track parent relationship using parentId
        parent_id = node.get('parentId')
        if parent_id and parent_id != node_id:
            # If parent is a divider container, skip up to the grandparent
            if parent_id in divider_containers:
                # Find the actual parent (grandparent of this state)
                for p_node in nodes:
                    if p_node['id'] == parent_id:
                        actual_parent = p_node.get('parentId')
                        if actual_parent:
                            state_parents[node_id] = actual_parent
                        break
            else:
                state_parents[node_id] = parent_id

                # Add to parent's children list (only if parent doesn't have parallel regions)
                if parent_id not in parallel_state_regions:
                    if parent_id not in hierarchical_states:
                        hierarchical_states[parent_id] = []
                    if node_id not in hierarchical_states[parent_id]:
                        hierarchical_states[parent_id].append(node_id)

    for edge in edges:
        start = edge['start']
        end = edge['end']
        label = edge.get('label', '').strip()

        # Handle initial state (from root_start or <State>_start)
        if start == 'root_start':
            initial_state = end
            continue
        elif start.endswith('_start'):
            # This is a child state's initial transition
            continue

        # Skip if start or end is a start node
        if start.endswith('_start') or end.endswith('_start'):
            continue

        # Parse transition label for trigger, guard, and action
        trigger = None
        guard = None
        action = None

        if label:
            # Extract action: / {action}
            action_match = re.search(r'/\s*\{(.+?)\}', label)
            if action_match:
                action = action_match.group(1)
                label = re.sub(r'/\s*\{.+?\}', '', label).strip()

            # Extract guard: [condition]
            guard_match = re.search(r'\[(.+?)\]', label)
            if guard_match:
                guard = guard_match.group(1)
                label = re.sub(r'\[.+?\]', '', label).strip()

            # What remains is the trigger/event (might include function call like "login(cardID)")
            trigger = label.strip() if label.strip() else None

        # Format state names with full parent path for pytransitions
        # Build full parent path for nested states
        def get_full_state_path(state_id):
            """Build full hierarchical path for a state (e.g., 'On_Playing_WhiteTurn')"""
            path = [state_id]
            current = state_id
            while current in state_parents:
                parent = state_parents[current]
                path.insert(0, parent)
                current = parent
            return '_'.join(path)

        # Format source and destination with full parent paths
        start_formatted = get_full_state_path(start)
        end_formatted = get_full_state_path(end)

        transition = {
            'trigger': trigger if trigger else 'auto',
            'source': start_formatted,
            'dest': end_formatted
        }

        if guard:
            transition['conditions'] = guard
        if action:
            transition['before'] = action

        transitions.append(transition)

    # Step 3: Build states list in Sherpa format
    # Handle both hierarchical and parallel states
    states_list = []

    for state in all_states:
        # Check if this state has parallel regions
        if state in parallel_state_regions and parallel_state_regions[state]:
            # This is a parallel state - format with 'parallel' field
            regions = []
            for idx, region_data in enumerate(parallel_state_regions[state]):
                # Use Region1, Region2, etc. as names (ignore the divider-id container names)
                regions.append({
                    'name': f'Region{idx+1}',
                    'children': region_data['children']
                })

            parallel_regions.append({
                'name': state,
                'parallel': regions
            })

            states_list.append({
                'name': state,
                'parallel': regions
            })
        elif state in hierarchical_states and hierarchical_states[state]:
            # This is a regular composite state with children
            states_list.append({
                'name': state,
                'children': hierarchical_states[state]
            })
        elif state not in state_parents:
            # This is a root-level simple state (not a child of any parent)
            states_list.append(state)

    # Step 4: Detect history states in transitions
    # History states are transitions where the destination ends with .H
    # Example: "StateA --> StateB.H" means transition to history state of StateB
    for transition in transitions:
        dest = transition['dest']
        # Check if destination is a history state (ends with .H or _H)
        if dest.endswith('.H') or dest.endswith('_H'):
            # Keep the .H format for pytransitions
            # pytransitions recognizes StateName.H as history state transition
            pass  # Already correctly formatted

    return states_list, transitions, hierarchical_states, initial_state, parallel_regions


if __name__ == "__main__":
    # Test the parser
    test_mermaid = """stateDiagram-v2
    [*] --> Off
    Off --> On : on

    state On {
        [*] --> Idle
        On --> Off : off

        Idle --> Idle : login(cardID) [!idAuthorized(cardID)]
        Idle --> Ready : login(cardID) [idAuthorized(cardID)] / {action="none"}

        Ready --> Idle : logoff
    }
"""

    states, transitions, hierarchical, initial, parallel = parse_mermaid_with_library(test_mermaid)

    print("States:", states)
    print("Transitions:", transitions)
    print("Hierarchical:", hierarchical)
    print("Initial:", initial)
    print("Parallel:", parallel)
