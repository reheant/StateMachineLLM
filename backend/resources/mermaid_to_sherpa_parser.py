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
    parallel_regions = []
    state_parents = {}  # state -> parent mapping

    # Step 1: Build parent-child relationships using parentId from nodes
    # TODO: Currently mermaid-parser-py has a bug where parentId is set for states
    # referenced in transitions even if they're siblings. This will be fixed in the future.
    for node in nodes:
        node_id = node['id']

        # Skip start/end nodes and note nodes
        if (node_id.endswith('_start') or
            node_id.endswith('_end') or
            '----note-' in node_id or
            '----parent' in node_id):
            continue

        # Add to all states
        all_states.add(node_id)

        # Check if this is a composite state
        if node.get('isGroup', False):
            if node_id not in hierarchical_states:
                hierarchical_states[node_id] = []

        # Track parent relationship using parentId
        parent_id = node.get('parentId')
        if parent_id and parent_id != node_id:
            state_parents[node_id] = parent_id

            # Add to parent's children list
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

    # Build states list in Sherpa format
    # Only include states that are either composite or not children of any other state
    states_list = []
    for state in all_states:
        if state in hierarchical_states and hierarchical_states[state]:
            # This is a composite state with children
            states_list.append({
                'name': state,
                'children': hierarchical_states[state]
            })
        elif state not in state_parents:
            # This is a root-level simple state (not a child of any parent)
            states_list.append(state)

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
