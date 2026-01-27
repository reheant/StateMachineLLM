#!/usr/bin/env python3
"""Test history state inference from notes."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.resources.mermaid_to_sherpa_parser import parse_mermaid_with_library

dishwasher_history_test = """stateDiagram-v2
    [*] --> Running
    
    state Running {
        [*] --> Drying
        
        state Drying {
            [*] --> DryingActive
            
            state DryingActive
            DryingActive --> DryingPaused : doorOpen
            
            state DryingPaused
        }
        
        DryingPaused --> Drying : doorClose
        
        note right of DryingPaused
            doorClose returns to DryingActive history state
        end note
    }
"""

printer_history_test = """stateDiagram-v2
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

# Test case for unnamed history note (from dishwasher_winter_2019 example)
dishwasher_unnamed_history_test = """stateDiagram-v2
    [*] --> Running
    
    state Running {
        [*] --> Cleaning
        
        state Cleaning {
            [*] --> Washing
            state Washing
            state Rinsing
            Washing --> Rinsing : after(10)
            Rinsing --> Washing : repeat
        }
        
        Cleaning --> Cleaning : toggleDryingTime
        
        note right of Cleaning
            toggleDryingTime returns to history state
        end note
    }
"""

# Test case for unnamed history note (from spa_manager_winter_2018 example)
spa_manager_unnamed_history_test = """stateDiagram-v2
    [*] --> Jacuzzi
    
    state Jacuzzi {
        [*] --> JacuzziOff
        
        JacuzziOff --> JacuzziOn : on
        
        state JacuzziOn {
            [*] --> Level1
            
            Level1 --> Level2 : up
            Level2 --> Level1 : down
        }
        
        JacuzziOn --> JacuzziOff : off
        JacuzziOn --> JacuzziOn : setPattern
        
        note right of JacuzziOn
            setPattern transitions to history state
        end note
    }
"""

def test_dishwasher_history_state():
    """Test dishwasher example with history state from note."""
    print("=" * 80)
    print("TEST: Dishwasher History State from Note")
    print("=" * 80)
    print(dishwasher_history_test)
    
    states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(
        dishwasher_history_test
    )
    
    print("\nStates:")
    for s in states:
        print(f"  {s}")
    
    print("\nTransitions:")
    for t in transitions:
        print(f"  {t}")
    
    print("\n" + "=" * 50)
    print("Verification:")
    
    h_found_in_drying = False
    drying_state = None
    
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'Running':
            for child in s.get('children', []):
                if isinstance(child, dict) and child.get('name') == 'Drying':
                    drying_state = child
                    if 'H' in child.get('children', []):
                        h_found_in_drying = True
                        print(f"  ✓ PASS: Found 'H' pseudo-state inside Drying composite")
                        print(f"    Drying children: {child.get('children')}")
                    else:
                        print(f"  ✗ FAIL: 'H' pseudo-state NOT found in Drying children")
                        print(f"    Drying children: {child.get('children')}")
                    break
    
    if not drying_state:
        print("  ✗ FAIL: Could not find Drying composite state")
    
    external_h_state = False
    for s in states:
        if isinstance(s, str) and '_H' in s:
            external_h_state = True
            print(f"  ✗ FAIL: Found external H state: {s}")
        elif isinstance(s, dict) and '_H' in s.get('name', ''):
            external_h_state = True
            print(f"  ✗ FAIL: Found external H state: {s.get('name')}")
    
    if not external_h_state and h_found_in_drying:
        print(f"  ✓ PASS: No external H states found")
    
    history_trans = [t for t in transitions if '_H' in t.get('dest', '')]
    if history_trans:
        print(f"  ✓ PASS: Found {len(history_trans)} transition(s) to history state:")
        for t in history_trans:
            print(f"    {t['source']} --{t['trigger']}--> {t['dest']}")
            if t['dest'].endswith('_H') and 'Drying' in t['dest']:
                print(f"    ✓ PASS: Correct destination format!")
            else:
                print(f"    ✗ FAIL: Unexpected destination format: {t['dest']}")
    else:
        print("  ℹ INFO: No transitions to history state (expected for note-only diagrams)")
    
    return h_found_in_drying and not external_h_state


def test_printer_history_state():
    """Test printer example for backward compatibility."""
    print("\n\n" + "=" * 80)
    print("TEST: Printer History State from Note (Backward Compatibility)")
    print("=" * 80)
    print(printer_history_test)
    
    states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(
        printer_history_test
    )
    
    print("\nStates:")
    for s in states:
        print(f"  {s}")
    
    print("\nTransitions:")
    for t in transitions:
        print(f"  {t}")
    
    print("\n" + "=" * 50)
    print("Verification:")
    
    h_found = False
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'On':
            for child in s.get('children', []):
                if isinstance(child, dict) and child.get('name') == 'Busy':
                    if 'H' in child.get('children', []):
                        h_found = True
                        print(f"  ✓ PASS: Found 'H' pseudo-state inside Busy composite")
                    else:
                        print(f"  ✗ FAIL: 'H' NOT found in Busy children: {child.get('children')}")
                    break
    
    if not h_found:
        print("  ✗ FAIL: No history state found in Busy")
    
    history_trans = [t for t in transitions if '_H' in t.get('dest', '')]
    if history_trans:
        print(f"  ✓ PASS: Found {len(history_trans)} transition(s) to history state")
        for t in history_trans:
            print(f"    {t['source']} --{t['trigger']}--> {t['dest']}")
    else:
        print("  ℹ INFO: No transitions to history state (expected for note-only diagrams)")
    
    return h_found


def test_dishwasher_unnamed_history():
    """Test dishwasher example with unnamed history note (from dishwasher_winter_2019)."""
    print("\n\n" + "=" * 80)
    print("TEST: Dishwasher Unnamed History State Note")
    print("=" * 80)
    print(dishwasher_unnamed_history_test)
    
    states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(
        dishwasher_unnamed_history_test
    )
    
    print("\nStates:")
    for s in states:
        print(f"  {s}")
    
    print("\nTransitions:")
    for t in transitions:
        print(f"  {t}")
    
    print("\n" + "=" * 50)
    print("Verification:")
    
    h_found = False
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'Running':
            for child in s.get('children', []):
                if isinstance(child, dict) and child.get('name') == 'Cleaning':
                    if 'H' in child.get('children', []):
                        h_found = True
                        print(f"  ✓ PASS: Found 'H' pseudo-state inside Cleaning composite")
                        print(f"    Cleaning children: {child.get('children')}")
                    else:
                        print(f"  ✗ FAIL: 'H' NOT found in Cleaning children: {child.get('children')}")
                    break
    
    if not h_found:
        print("  ✗ FAIL: No history state found in Cleaning")
    
    return h_found


def test_spa_manager_unnamed_history():
    """Test spa manager example with unnamed history note (from spa_manager_winter_2018)."""
    print("\n\n" + "=" * 80)
    print("TEST: Spa Manager Unnamed History State Note")
    print("=" * 80)
    print(spa_manager_unnamed_history_test)
    
    states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(
        spa_manager_unnamed_history_test
    )
    
    print("\nStates:")
    for s in states:
        print(f"  {s}")
    
    print("\nTransitions:")
    for t in transitions:
        print(f"  {t}")
    
    print("\n" + "=" * 50)
    print("Verification:")
    
    h_found = False
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'Jacuzzi':
            for child in s.get('children', []):
                if isinstance(child, dict) and child.get('name') == 'JacuzziOn':
                    if 'H' in child.get('children', []):
                        h_found = True
                        print(f"  ✓ PASS: Found 'H' pseudo-state inside JacuzziOn composite")
                        print(f"    JacuzziOn children: {child.get('children')}")
                    else:
                        print(f"  ✗ FAIL: 'H' NOT found in JacuzziOn children: {child.get('children')}")
                    break
    
    if not h_found:
        print("  ✗ FAIL: No history state found in JacuzziOn")
    
    return h_found


if __name__ == "__main__":
    print("Testing history state inference from notes...")
    print("This validates the fix for the rendering bug\n")
    
    test1_passed = test_dishwasher_history_state()
    test2_passed = test_printer_history_state()
    test3_passed = test_dishwasher_unnamed_history()
    test4_passed = test_spa_manager_unnamed_history()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Dishwasher test (explicit state name): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Printer test (explicit state name): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    print(f"Dishwasher test (unnamed history): {'✓ PASSED' if test3_passed else '✗ FAILED'}")
    print(f"Spa Manager test (unnamed history): {'✓ PASSED' if test4_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("\n✓ All tests PASSED!")
        sys.exit(0)
    else:
        print("\n✗ Some tests FAILED!")
        sys.exit(1)
