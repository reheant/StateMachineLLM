#!/usr/bin/env python3
"""
Test printer state machine to debug duplicate history state issue
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from resources.mermaid_to_sherpa_parser import parse_mermaid_with_library

mermaid_code = """stateDiagram-v2
    [*] --> Off
    
    Off --> On : switchOn
    
    state On {
        [*] --> LoggedOut
        
        On --> Off : switchOff
        
        state LoggedOut
        LoggedOut --> LoggedOut : tapCard [!authorized] / showLoginError
        LoggedOut --> LoggedIn : tapCard [authorized]
        
        state LoggedIn {
            [*] --> Idle
            
            state Idle
            Idle --> Busy : choosePrint, start [queueNotEmpty]
            Idle --> Idle : choosePrint, start [queueEmpty] / showError
            Idle --> Busy : chooseScan, start [documentDetected]
            Idle --> Idle : chooseScan, start [!documentDetected] / showError
            Idle --> LoggedOut : logoff
            
            state Busy {
                [*] --> Print
                
                state Print
                Print --> Idle : done
                Print --> Idle : stop
                Print --> PaperJamSuspended : paperJam
                Print --> OutOfPaperSuspended : outOfPaper
                
                state Scan
                Scan --> Idle : done
                Scan --> Idle : stop
                Scan --> PaperJamSuspended : paperJam
            }
        }
        
        state PaperJamSuspended
        PaperJamSuspended --> Busy : resume
        PaperJamSuspended --> Idle : cancel
        
        note right of PaperJamSuspended
            resume returns to Busy history state
        end note
        
        state OutOfPaperSuspended
        OutOfPaperSuspended --> Busy : resume
        OutOfPaperSuspended --> Idle : cancel
        
        note right of OutOfPaperSuspended
            resume returns to Busy history state
        end note
    }
"""

print("=" * 80)
print("PRINTER STATE MACHINE - Debug Duplicate History State")
print("=" * 80)

states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(mermaid_code)

print("\n" + "=" * 80)
print("PARSED STATES:")
print("=" * 80)
import json
print(json.dumps(states, indent=2))

print("\n" + "=" * 80)
print("CHECKING FOR DUPLICATE 'H' PSEUDO-STATES:")
print("=" * 80)

def find_h_states(states, path=""):
    """Recursively find all H pseudo-states"""
    h_locations = []
    
    for state in states:
        if isinstance(state, dict):
            state_name = state.get('name', '?')
            current_path = f"{path}/{state_name}" if path else state_name
            children = state.get('children', [])
            
            # Check if 'H' is in children
            h_count = children.count('H')
            if h_count > 0:
                h_locations.append((current_path, h_count))
            
            # Recursively check children
            child_dicts = [c for c in children if isinstance(c, dict)]
            if child_dicts:
                h_locations.extend(find_h_states(child_dicts, current_path))
    
    return h_locations

h_locations = find_h_states(states)

if h_locations:
    print("\nFound H pseudo-states:")
    for location, count in h_locations:
        status = "✓ OK" if count == 1 else f"❌ DUPLICATE (count={count})"
        print(f"  {location}: {status}")
else:
    print("\n✓ No H pseudo-states found")

print("\n" + "=" * 80)
