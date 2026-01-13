#!/usr/bin/env python3
"""Test advanced Mermaid state diagram features"""

from mermaid_parser import MermaidParser
import json

# Test parallel states
parallel_test = """stateDiagram-v2
    [*] --> Active

    state Active {
        [*] --> NumLockOff
        NumLockOff --> NumLockOn : EvNumLockPressed
        NumLockOn --> NumLockOff : EvNumLockPressed
        --
        [*] --> CapsLockOff
        CapsLockOff --> CapsLockOn : EvCapsLockPressed
        CapsLockOn --> CapsLockOff : EvCapsLockPressed
    }
"""

# Test history states
history_test = """stateDiagram-v2
    [*] --> Active

    state Active {
        [*] --> Running
        Running --> Paused : pause
        Paused --> Running : resume
    }

    Active --> Suspended : suspend
    Suspended --> Active : resume
"""

# Test final states
final_test = """stateDiagram-v2
    [*] --> Running
    Running --> Finished : complete
    Finished --> [*]
"""

# Test choice/fork
choice_test = """stateDiagram-v2
    [*] --> IsPositive
    IsPositive --> Positive : if n > 0
    IsPositive --> Negative : if n < 0
    IsPositive --> Zero : if n == 0
"""

parser = MermaidParser()

print("=" * 80)
print("PARALLEL STATES TEST")
print("=" * 80)
try:
    result = parser.parse(parallel_test)
    print("✓ Parsed successfully")
    # Check if parallel regions are detected
    nodes = result['graph_data']['nodes']
    print(f"  Nodes found: {[n['id'] for n in nodes if n.get('shape') != 'stateStart']}")
    # Look for divider info
    print(f"  Divider count: {result['graph_data'].get('dividerCnt', 0)}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 80)
print("HISTORY STATES TEST")
print("=" * 80)
try:
    result = parser.parse(history_test)
    print("✓ Parsed successfully")
    nodes = result['graph_data']['nodes']
    print(f"  Nodes found: {[n['id'] for n in nodes if n.get('shape') != 'stateStart']}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 80)
print("FINAL STATES TEST")
print("=" * 80)
try:
    result = parser.parse(final_test)
    print("✓ Parsed successfully")
    nodes = result['graph_data']['nodes']
    print(f"  Nodes found: {[(n['id'], n.get('shape')) for n in nodes]}")
    edges = result['graph_data']['edges']
    print(f"  Edges: {[(e['start'], e['end']) for e in edges]}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 80)
print("CHOICE/FORK TEST")
print("=" * 80)
try:
    result = parser.parse(choice_test)
    print("✓ Parsed successfully")
    edges = result['graph_data']['edges']
    for edge in edges:
        print(f"  {edge['start']} --> {edge['end']} : {edge.get('label', '')}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("Testing what Mermaid stateDiagram-v2 features are supported...")
