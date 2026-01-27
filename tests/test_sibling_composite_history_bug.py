#!/usr/bin/env python3
"""Test case to reproduce the sibling composite history state bug."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.resources.mermaid_to_sherpa_parser import parse_mermaid_with_library

# This is the bug scenario: Print and Scan are sibling composites
# Only Print should get history, but the current implementation adds it to both
printer_with_scan_sibling = """stateDiagram-v2
    [*] --> Idle
    
    state PaperJam
    
    state Print {
        [*] --> Printing
        Printing --> PrintPaused : pause
        PrintPaused --> Printing : resume
    }
    
    state Scan {
        [*] --> Scanning
        Scanning --> ScanPaused : pause
        ScanPaused --> Scanning : resume
    }
    
    Idle --> Print : startPrint
    Idle --> Scan : startScan
    
    Print --> PaperJam : jam
    Scan --> PaperJam : jam
    
    PaperJam --> Print : resume
    PaperJam --> Scan : resume
    
    note right of PaperJam
        resume returns to Print history state
    end note
"""


def test_sibling_composite_bug():
    """Test that demonstrates the sibling composite bug.
    
    Expected:
    - Only Print composite should have 'H' child
    - Scan composite should NOT have 'H' child
    - PaperJam --> Print transition should go to Print_H
    - PaperJam --> Scan transition should go to Scan (not Scan_H)
    
    Actual (BUG):
    - Both Print AND Scan get 'H' children
    - Both transitions incorrectly go to history states
    """
    print("=" * 80)
    print("TEST: Sibling Composite History State Bug")
    print("=" * 80)
    print(printer_with_scan_sibling)
    
    states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(
        printer_with_scan_sibling
    )
    
    print("\nStates:")
    for s in states:
        print(f"  {s}")
    
    print("\nTransitions:")
    for t in transitions:
        print(f"  {t}")
    
    print("\n" + "=" * 50)
    print("Verification:")
    
    # Check Print composite for H
    print_has_h = False
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'Print':
            if 'H' in s.get('children', []):
                print_has_h = True
                print(f"  ✓ EXPECTED: Print composite has 'H' pseudo-state")
                print(f"    Print children: {s.get('children')}")
            else:
                print(f"  ✗ FAIL: Print composite missing 'H' pseudo-state")
                print(f"    Print children: {s.get('children')}")
            break
    
    # Check Scan composite for H
    scan_has_h = False
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'Scan':
            if 'H' in s.get('children', []):
                scan_has_h = True
                print(f"  ✗ BUG: Scan composite incorrectly has 'H' pseudo-state")
                print(f"    Scan children: {s.get('children')}")
            else:
                print(f"  ✓ EXPECTED: Scan composite does NOT have 'H' pseudo-state")
                print(f"    Scan children: {s.get('children')}")
            break
    
    # Check transitions from PaperJam
    paperjam_to_print = None
    paperjam_to_scan = None
    
    for t in transitions:
        if t['source'] == 'PaperJam' and 'Print' in t['dest']:
            paperjam_to_print = t
        elif t['source'] == 'PaperJam' and 'Scan' in t['dest']:
            paperjam_to_scan = t
    
    print("\n  Transition Analysis:")
    if paperjam_to_print:
        if paperjam_to_print['dest'] == 'Print_H':
            print(f"  ✓ EXPECTED: PaperJam --> Print_H (goes to history)")
        else:
            print(f"  ✗ FAIL: PaperJam --> {paperjam_to_print['dest']} (should be Print_H)")
    else:
        print(f"  ✗ FAIL: No transition from PaperJam to Print found")
    
    if paperjam_to_scan:
        if paperjam_to_scan['dest'] == 'Scan':
            print(f"  ✓ EXPECTED: PaperJam --> Scan (goes to composite, not history)")
        elif paperjam_to_scan['dest'] == 'Scan_H':
            print(f"  ✗ BUG: PaperJam --> Scan_H (should go to Scan, not history!)")
        else:
            print(f"  ? UNEXPECTED: PaperJam --> {paperjam_to_scan['dest']}")
    else:
        print(f"  ✗ FAIL: No transition from PaperJam to Scan found")
    
    # Determine pass/fail
    bug_present = scan_has_h or (paperjam_to_scan and paperjam_to_scan['dest'] == 'Scan_H')
    expected_behavior = print_has_h and not scan_has_h
    
    if expected_behavior and paperjam_to_print and paperjam_to_print['dest'] == 'Print_H' and paperjam_to_scan and paperjam_to_scan['dest'] == 'Scan':
        print("\n  ✓✓✓ TEST PASSED - Bug is FIXED! ✓✓✓")
        return True
    elif bug_present:
        print("\n  ✗✗✗ TEST FAILED - BUG STILL PRESENT ✗✗✗")
        print("  The parser incorrectly adds history state to sibling composite (Scan)")
        print("  when the note only mentions Print.")
        return False
    else:
        print("\n  ? UNEXPECTED STATE")
        return False


if __name__ == "__main__":
    print("Reproducing the sibling composite history state bug...\n")
    
    passed = test_sibling_composite_bug()
    
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    
    if passed:
        print("✓ The bug has been fixed!")
        sys.exit(0)
    else:
        print("✗ The bug is still present. The parser needs to be fixed to:")
        print("  1. Only add 'H' to composites explicitly mentioned in notes")
        print("  2. Only convert transitions to history when they match the note context")
        print("  3. Not apply history state inference globally to all similar transitions")
        sys.exit(1)
