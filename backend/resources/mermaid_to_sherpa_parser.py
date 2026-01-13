"""
Convert mermaid-parser-py StateDiagramConverter output to Sherpa state machine format.

This is the UPDATED version that uses StateDiagramConverter instead of raw MermaidParser,
which gives us the correct parent_id relationships and nearest common ancestor logic.
"""
import re
from mermaid_parser.converters.state_diagram import StateDiagramConverter


def parse_mermaid_with_library(mermaid_code: str):
    """
    Parse Mermaid stateDiagram-v2 using mermaid-parser-py StateDiagramConverter
    and convert to Sherpa-compatible format.

    Returns: (states_list, transitions_list, hierarchical_dict, initial_state, parallel_regions)
    """
    # Use StateDiagramConverter instead of raw MermaidParser
    converter = StateDiagramConverter()
    result = converter.convert(mermaid_code)

    # Track states and their hierarchical relationships
    all_states = {}  # id -> state object
    hierarchical_states = {}  # parent -> [children]
    initial_state = None
    transitions = []
    parallel_regions = []
    state_parents = {}  # state -> parent mapping

    # Step 1: Build state mappings from converter output
    for state in result.states:
        state_id = getattr(state, 'id_', None)
        parent_id = getattr(state, 'parent_id', None)

        if not state_id:
            continue

        # Skip start/end markers and internal markers
        if (state_id.endswith('_start') or
            state_id.endswith('_end') or
            state_id == '[*]' or
            '----note-' in state_id or
            '----parent' in state_id):
            continue

        all_states[state_id] = state

        # Track parent relationship
        if parent_id:
            state_parents[state_id] = parent_id

            # Add to parent's children list
            if parent_id not in hierarchical_states:
                hierarchical_states[parent_id] = []
            if state_id not in hierarchical_states[parent_id]:
                hierarchical_states[parent_id].append(state_id)

        # Initialize children list for composite states
        state_type = type(state).__name__
        if state_type in ['Composite', 'Concurrent']:
            if state_id not in hierarchical_states:
                hierarchical_states[state_id] = []

    # Step 2: Find initial state from transitions
    for transition in result.transitions:
        from_state = getattr(transition, 'from_state', None)
        to_state = getattr(transition, 'to_state', None)

        if not from_state or not to_state:
            continue

        from_id = getattr(from_state, 'id_', None)
        to_id = getattr(to_state, 'id_', None)

        # Handle initial state (from root_start or [*])
        if from_id in ['root_start', '[*]']:
            if not initial_state:
                initial_state = to_id
            continue

        # Skip transitions from/to start markers
        if (from_id and (from_id.endswith('_start') or from_id == '[*]')) or \
           (to_id and (to_id.endswith('_start') or to_id == '[*]')):
            continue

    # Step 3: Convert transitions to Sherpa format
    for transition in result.transitions:
        from_state = getattr(transition, 'from_state', None)
        to_state = getattr(transition, 'to_state', None)
        label = getattr(transition, 'label', '')

        if not from_state or not to_state:
            continue

        from_id = getattr(from_state, 'id_', None)
        to_id = getattr(to_state, 'id_', None)

        # Skip start/end markers
        if not from_id or not to_id:
            continue
        if from_id in ['root_start', '[*]'] or from_id.endswith('_start'):
            continue
        if to_id.endswith('_start') or to_id == '[*]':
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

            # What remains is the trigger/event
            trigger = label.strip() if label.strip() else None

        # Build full hierarchical path for nested states
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
        start_formatted = get_full_state_path(from_id)
        end_formatted = get_full_state_path(to_id)

        trans = {
            'trigger': trigger if trigger else 'auto',
            'source': start_formatted,
            'dest': end_formatted
        }

        if guard:
            trans['conditions'] = guard
        if action:
            trans['before'] = action

        transitions.append(trans)

    # Step 4: Build states list in Sherpa NESTED format (not flat!)
    # Sherpa needs a nested structure where children are objects within their parent's children array

    def build_nested_state(state_id):
        """Recursively build nested state structure"""
        if state_id in hierarchical_states and hierarchical_states[state_id]:
            # This is a composite state - build it with nested children
            nested_children = []
            for child_id in hierarchical_states[state_id]:
                # Recursively build each child (might also be composite)
                nested_child = build_nested_state(child_id)
                nested_children.append(nested_child)

            return {
                'name': state_id,
                'children': nested_children
            }
        else:
            # Simple state (leaf node)
            return state_id

    # Build the states list with only ROOT-level states (not nested ones)
    states_list = []
    all_child_states = set()
    for parent, children in hierarchical_states.items():
        all_child_states.update(children)

    # Only add states that have no parent (root-level)
    for state_id in all_states.keys():
        if state_id not in all_child_states:
            # This is a root-level state
            nested_state = build_nested_state(state_id)
            states_list.append(nested_state)

    # Step 5: Set initial state if not found
    if not initial_state and states_list:
        # Use first state
        first_state = states_list[0]
        initial_state = first_state if isinstance(first_state, str) else first_state['name']

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
    print("\nTransitions:", transitions)
    print("\nHierarchical:", hierarchical)
    print("\nInitial:", initial)
    print("\nParallel:", parallel)
