#!/usr/bin/env python3
"""
Test to verify that the parser REJECTS Mermaid diagrams with implicit/inferred history states.
The parser should only accept EXPLICIT history state mentions in notes.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from resources.mermaid_to_sherpa_parser import parse_mermaid_with_library


def test_explicit_history_state_passes():
    """Test that EXPLICIT history state mention is accepted"""
    
    mermaid_code = """
stateDiagram-v2
    [*] --> Idle
    
    state Composite {
        [*] --> SubState1
        SubState1 --> SubState2: event1
        SubState2 --> SubState1: event2
    }
    
    Idle --> Composite: start
    Composite --> Paused: pause
    Paused --> Composite: resume
    
    note right of Paused: returns to Composite history state
    """
    
    print("Testing EXPLICIT history state mention (should PASS)...")
    try:
        states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(mermaid_code)
        print("  ✓ PASS: Explicit history state accepted")
        
        # Verify H was added to Composite
        composite_found = False
        for state in states:
            if isinstance(state, dict) and state.get('name') == 'Composite':
                if 'H' in state.get('children', []):
                    composite_found = True
                    print("  ✓ H pseudo-state correctly added to Composite")
        
        if not composite_found:
            print("  ✗ FAIL: H pseudo-state not found in Composite")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ FAIL: Should have accepted explicit history state")
        print(f"  Error: {e}")
        return False


def test_implicit_history_state_fails():
    """Test that IMPLICIT/INFERRED history state is REJECTED"""
    
    mermaid_code = """
stateDiagram-v2
    [*] --> Idle
    
    state Composite {
        [*] --> SubState1
        SubState1 --> SubState2: event1
        SubState2 --> SubState1: event2
    }
    
    Idle --> Composite: start
    Composite --> Paused: pause
    Paused --> Composite: resume
    
    note right of Paused: this is a history state
    """
    
    print("\nTesting IMPLICIT history state (should FAIL with error)...")
    try:
        states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(mermaid_code)
        print("  ✗ FAIL: Parser should have rejected implicit history state!")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "explicitly mentioned" in error_msg.lower() or "explicit" in error_msg.lower():
            print("  ✓ PASS: Parser correctly rejected implicit history state")
            print(f"  Error message: {error_msg}")
            return True
        else:
            print(f"  ✗ FAIL: Wrong error type: {error_msg}")
            return False
    except Exception as e:
        print(f"  ✗ FAIL: Unexpected error: {e}")
        return False


def test_no_history_state_passes():
    """Test that diagrams WITHOUT history states work normally"""
    
    mermaid_code = """
stateDiagram-v2
    [*] --> Idle
    
    state Composite {
        [*] --> SubState1
        SubState1 --> SubState2: event1
        SubState2 --> SubState1: event2
    }
    
    Idle --> Composite: start
    Composite --> Idle: stop
    """
    
    print("\nTesting diagram WITHOUT history state (should PASS)...")
    try:
        states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(mermaid_code)
        print("  ✓ PASS: Diagram without history state accepted")
        
        # Verify NO H was added
        for state in states:
            if isinstance(state, dict):
                if 'H' in state.get('children', []):
                    print(f"  ✗ FAIL: H pseudo-state incorrectly added to {state.get('name')}")
                    return False
        
        print("  ✓ No H pseudo-states added (correct)")
        return True
    except Exception as e:
        print(f"  ✗ FAIL: Should have accepted diagram without history state")
        print(f"  Error: {e}")
        return False


if __name__ == "__main__":
    print("="*80)
    print("HISTORY STATE VALIDATION TEST SUITE")
    print("="*80)
    print("\nThis test verifies that the parser:")
    print("1. Accepts EXPLICIT history state mentions: 'returns to StateName history state'")
    print("2. REJECTS implicit/inferred history states")
    print("3. Works normally for diagrams without history states")
    print("="*80)
    
    results = []
    
    # Test 1: Explicit mention should pass
    results.append(("Explicit History State", test_explicit_history_state_passes()))
    
    # Test 2: Implicit mention should fail
    results.append(("Implicit History State Rejection", test_implicit_history_state_fails()))
    
    # Test 3: No history state should pass
    results.append(("No History State", test_no_history_state_passes()))
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*80)
    if all_passed:
        print("\n✓ ALL TESTS PASSED - Parser correctly requires explicit history state mentions")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
