"""
Convert mermaid-parser-py StateDiagramConverter output to Sherpa state machine format.

This is the UPDATED version that uses StateDiagramConverter instead of raw MermaidParser,
which gives us the correct parent_id relationships and nearest common ancestor logic.
Includes support for shallow history states (displayed as "H" pseudo-states).
"""
import re
import sys
from mermaid_parser.converters.state_diagram import StateDiagramConverter
from mermaid_parser.structs.state_diagram import HistoryState


def debug_print(msg):
    """Print debug message to stderr (unbuffered)"""
    print(f"[HISTORY DEBUG] {msg}", file=sys.stderr, flush=True)


def parse_mermaid_with_library(mermaid_code: str):
    """
    Parse Mermaid stateDiagram-v2 using mermaid-parser-py StateDiagramConverter
    and convert to Sherpa-compatible format.

    Returns: (states_list, transitions_list, hierarchical_dict, initial_state, parallel_regions)
    """
    debug_print("=== PARSING MERMAID CODE ===")

    # Use StateDiagramConverter instead of raw MermaidParser
    converter = StateDiagramConverter()
    result = converter.convert(mermaid_code)

    debug_print(f"Converter returned {len(result.states)} states, {len(result.transitions)} transitions, {len(result.notes)} notes")

    # Track states and their hierarchical relationships
    # Use scoped_id as the unique key to handle same-named states in different scopes
    all_states = {}  # scoped_id -> state object
    hierarchical_states = {}  # parent_id -> [children_ids] (for display names)
    initial_state = None
    transitions = []
    parallel_regions = []
    state_parents = {}  # scoped_id -> parent_id mapping
    scoped_to_bare = {}  # scoped_id -> bare id_ mapping

    # Track history states from the converter result
    history_states_map = getattr(result, 'history_states', {})  # composite_id -> HistoryState
    history_transitions_map = getattr(result, 'history_transitions', {})  # (from, trigger) -> composite

    # Debug output for history states
    debug_print(f"History states map from converter: {list(history_states_map.keys()) if history_states_map else 'EMPTY'}")
    debug_print(f"History transitions map: {history_transitions_map if history_transitions_map else 'EMPTY'}")

    # Step 1: Build state mappings from converter output
    for state in result.states:
        state_id = getattr(state, 'id_', None)
        parent_id = getattr(state, 'parent_id', None)
        # Use scoped_id if available, otherwise fall back to state_id
        scoped_id = getattr(state, 'scoped_id', state_id)

        if not state_id:
            continue

        # Skip start/end markers and internal markers
        if (state_id.endswith('_start') or
            state_id.endswith('_end') or
            state_id == '[*]' or
            '----note-' in state_id or
            '----parent' in state_id):
            continue

        # Skip HistoryState objects - they will be added as children of their parent composite
        if isinstance(state, HistoryState) or getattr(state, 'is_history_state', False):
            continue

        # Use scoped_id as the unique key
        all_states[scoped_id] = state
        scoped_to_bare[scoped_id] = state_id

        # Track parent relationship using scoped_id as key
        if parent_id:
            state_parents[scoped_id] = parent_id

            # Add to parent's children list (using bare id for display)
            if parent_id not in hierarchical_states:
                hierarchical_states[parent_id] = []
            if state_id not in hierarchical_states[parent_id]:
                hierarchical_states[parent_id].append(state_id)

        # Initialize children list for composite states
        state_type = type(state).__name__
        if state_type in ['Composite', 'Concurrent']:
            if state_id not in hierarchical_states:
                hierarchical_states[state_id] = []

        # Check for parallel regions
        if hasattr(state, 'parallel_regions') and state.parallel_regions:
            parallel_regions.append({
                'parent': state_id,
                'regions': state.parallel_regions
            })

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
        # Use scoped_id which already contains the full hierarchical path
        # This correctly handles same-named states in different scopes (e.g., parallel regions)
        from_scoped = getattr(from_state, 'scoped_id', from_id)
        to_scoped = getattr(to_state, 'scoped_id', to_id)

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
            # Extract action: supports both "/ {action}" and "/ action" formats
            # First try with curly braces: / {action}
            action_match = re.search(r'/\s*\{(.+?)\}', label)
            if action_match:
                action = action_match.group(1)
                label = re.sub(r'/\s*\{.+?\}', '', label).strip()
            else:
                # Try without curly braces: / action (captures until end of string or next special char)
                action_match = re.search(r'/\s*([^\[\]]+)$', label)
                if action_match:
                    action = action_match.group(1).strip()
                    label = re.sub(r'/\s*[^\[\]]+$', '', label).strip()

            # Extract guard: [condition]
            guard_match = re.search(r'\[(.+?)\]', label)
            if guard_match:
                guard = guard_match.group(1)
                label = re.sub(r'\[.+?\]', '', label).strip()

            # What remains is the trigger/event
            trigger = label.strip() if label.strip() else None

        # Helper to build full path from scoped_id by walking up the hierarchy
        # The scoped_id might be region-prefixed (e.g., SpaManager_region_0_Sauna_Off)
        # We need to convert it to proper hierarchical format (SpaManager_Sauna_Off)
        def normalize_scoped_path(scoped_id, bare_id):
            """Convert scoped_id to hierarchical path, removing region prefixes."""
            if not scoped_id:
                return bare_id
            # Remove region markers (e.g., _region_0_, _region_1_)
            normalized = re.sub(r'_region_\d+', '', scoped_id)
            return normalized

        # Format source and destination using scoped_id (already contains full path)
        start_formatted = normalize_scoped_path(from_scoped, from_id)
        end_formatted = normalize_scoped_path(to_scoped, to_id)

        # Check if this is a history transition (destination is a HistoryState)
        is_history_transition = getattr(transition, 'is_history_transition', False)
        if is_history_transition or isinstance(to_state, HistoryState):
            # The destination should be the H pseudo-state inside the parent composite
            # HistoryState has parent_state_id attribute
            parent_composite = getattr(to_state, 'parent_state_id', None)
            if parent_composite:
                # Find the full hierarchical path to the composite state
                # Look up the composite's scoped path from all_states
                composite_full_path = None
                for scoped_key, state in all_states.items():
                    bare = scoped_to_bare.get(scoped_key, scoped_key)
                    if bare == parent_composite:
                        composite_full_path = normalize_scoped_path(scoped_key, bare)
                        break

                if composite_full_path:
                    end_formatted = f"{composite_full_path}_H"
                else:
                    end_formatted = f"{parent_composite}_H"
                debug_print(f"Transition {start_formatted} -> {end_formatted} (history of {parent_composite})")

        trans = {
            'trigger': trigger if trigger else 'auto',
            'source': start_formatted,
            'dest': end_formatted
        }

        if guard:
            trans['conditions'] = guard
        if action:
            trans['before'] = action

        # Build label for display on diagram: "trigger [guard] / action"
        display_label = trigger if trigger else ''
        if guard:
            display_label += f' [{guard}]' if display_label else f'[{guard}]'
        if action:
            display_label += f' / {action}' if display_label else f'/ {action}'
        if display_label:
            trans['label'] = display_label

        transitions.append(trans)

    # Step 4: Build states list in Sherpa NESTED format (not flat!)
    # Sherpa needs a nested structure where children are objects within their parent's children array

    # Debug: Print hierarchical structure
    debug_print(f"Hierarchical states: {hierarchical_states}")
    debug_print(f"History states to add H: {list(history_states_map.keys()) if history_states_map else 'NONE'}")

    # Create a lookup for parallel region info by parent state
    parallel_info_by_state = {p['parent']: p['regions'] for p in parallel_regions}

    def build_nested_state(state_id):
        """Recursively build nested state structure, including history pseudo-states"""
        # Check if this state has parallel regions
        if state_id in parallel_info_by_state:
            regions = parallel_info_by_state[state_id]

            # Collect all children from all regions (excluding start states)
            nested_children = []
            parallel_region_children = []  # Track the composite children that form parallel regions

            for region in regions:
                region_initial = region.get('initial')

                for child_id, child_state in region['states'].items():
                    # Skip start states (they have generated IDs like "divider-id-1_start")
                    if child_id.endswith('_start') or child_id == '[*]':
                        continue

                    # Only add states whose parent is the current state (state_id)
                    # This prevents adding nested children at the wrong level
                    child_parent = getattr(child_state, 'parent_id', None)
                    if child_parent != state_id:
                        continue

                    # Recursively build each child
                    nested_child = build_nested_state(child_id)
                    if nested_child not in nested_children:
                        nested_children.append(nested_child)
                        # If this child is a composite state (dict), track it as a parallel region child
                        if isinstance(nested_child, dict):
                            parallel_region_children.append(nested_child['name'])

            # Add history pseudo-state "H" if this composite state has history
            if state_id in history_states_map:
                nested_children.append("H")
                debug_print(f"Added 'H' to parallel state: {state_id}")

            # Return state with parallel structure
            # When 'initial' is a LIST, transitions library renders parallel regions
            result = {
                'name': state_id,
                'children': nested_children
            }

            # For parallel regions, the initial should be the composite children (e.g., ['Sauna', 'Jacuzzi'])
            # Each composite child should have its own internal initial state
            if parallel_region_children:
                result['initial'] = parallel_region_children  # LIST triggers parallel rendering

            return result

        elif state_id in hierarchical_states and hierarchical_states[state_id]:
            # This is a regular composite state - build it with nested children
            nested_children = []
            for child_id in hierarchical_states[state_id]:
                # Recursively build each child (might also be composite)
                nested_child = build_nested_state(child_id)
                nested_children.append(nested_child)

            # Add history pseudo-state "H" if this composite state has history
            if state_id in history_states_map:
                nested_children.append("H")
                debug_print(f"Added 'H' to composite state: {state_id}")

            result = {
                'name': state_id,
                'children': nested_children
            }

            # Try to find initial state for this composite from parallel regions info
            # The initial state is typically the first child or specified in region info
            for p in parallel_regions:
                for region in p['regions']:
                    if state_id in region.get('states', {}):
                        region_initial = region.get('initial')
                        if region_initial and region_initial in hierarchical_states.get(state_id, []):
                            result['initial'] = region_initial
                            break

            return result
        else:
            # Simple state (leaf node)
            return state_id

    # Build the states list with only ROOT-level states (not nested ones)
    states_list = []
    all_child_states = set()
    for parent, children in hierarchical_states.items():
        all_child_states.update(children)

    # Only add states that have no parent (root-level)
    # We need to check the BARE id (not scoped_id) against all_child_states
    added_bare_ids = set()  # Track which bare IDs we've already added
    for scoped_id, state in all_states.items():
        bare_id = scoped_to_bare.get(scoped_id, scoped_id)
        # Skip if this bare ID is a child of another state
        if bare_id in all_child_states:
            continue
        # Skip if we've already added this bare ID (avoid duplicates)
        if bare_id in added_bare_ids:
            continue
        # This is a root-level state
        nested_state = build_nested_state(bare_id)
        states_list.append(nested_state)
        added_bare_ids.add(bare_id)

    # Step 5: Set initial state if not found
    if not initial_state and states_list:
        # Use first state
        first_state = states_list[0]
        initial_state = first_state if isinstance(first_state, str) else first_state['name']

    return states_list, transitions, hierarchical_states, initial_state, parallel_regions


if __name__ == "__main__":
    # Test the parser with a history state example (Printer)
    test_mermaid = """stateDiagram-v2
    [*] --> Off
    Off --> On : on

    state On {
        [*] --> Idle
        On --> Off : off

        Idle --> Ready : login

        state Busy {
            [*] --> Print
            state Print
            Busy --> Suspended : jam
            Busy --> Ready : done
        }

        Ready --> Busy : start

        state Suspended
        Suspended --> Ready : cancel
        Suspended --> Busy : resume

        note right of Suspended
            resume transitions to Busy history state
        end note
    }
"""

    print("=" * 50)
    print("Testing History State Support")
    print("=" * 50)

    states, transitions, hierarchical, initial, parallel = parse_mermaid_with_library(test_mermaid)

    print("\nStates:")
    for s in states:
        print(f"  {s}")
    print("\nTransitions:")
    for t in transitions:
        print(f"  {t}")
    print("\nHierarchical:", hierarchical)
    print("\nInitial:", initial)
    print("\nParallel:", parallel)

    # Check if history state was detected
    print("\n" + "=" * 50)
    print("History State Verification:")
    history_found = False
    for s in states:
        if isinstance(s, dict) and 'children' in s:
            if 'H' in s.get('children', []):
                print(f"  ✓ Found 'H' pseudo-state in composite state: {s['name']}")
                history_found = True
    if not history_found:
        print("  ✗ No history states found")

    # Check if transition to H exists
    history_trans = [t for t in transitions if '_H' in t.get('dest', '')]
    if history_trans:
        print(f"  ✓ Found {len(history_trans)} transition(s) to history state:")
        for t in history_trans:
            print(f"    {t['source']} --{t['trigger']}--> {t['dest']}")
    else:
        print("  ✗ No transitions to history state found")
