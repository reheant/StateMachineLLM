#!/usr/bin/env python3
"""Test script to validate the printer state machine parsing."""

import sys

sys.path.insert(
    0,
    "/Users/marc-antoinenadeau/Desktop/7th Semester/Capstone/Code/StateMachineLLM/backend/resources",
)

from mermaid_to_sherpa_parser import parse_mermaid_with_library

mermaid_code = """stateDiagram-v2
    
    state Off
    [*] --> Off
    Off --> On : on
    On --> Off : off
    
    state On {
        state Idle
        [*] --> Idle
        
        Idle --> Idle : login(cardID) [!idAuthorized(cardID)]
        state Ready
        Idle --> Ready : login(cardID) [idAuthorized(cardID)] / {action="none"}

        Ready --> Idle : logoff
        Ready --> Ready : start [action=="scan" && !originalLoaded()]
        Ready --> Ready : start [action=="print" && !documentInQueue()]
        Ready --> Ready : scan / {action="scan"}
        Ready --> Ready : print / {action="print"}

        state Busy {
            state ScanAndEmail

            state Print
            
            state HistoryState1
            
            ScanAndEmail --> Ready : stop
            ScanAndEmail --> Ready : done
            Print --> Ready : stop
            Print --> Ready : done
            Print --> Suspended : outOfPaper
        }
        
        Ready --> ScanAndEmail : start [action=="scan" && originalLoaded()]
        Ready --> Print : start [action=="print" && documentInQueue()]
       
        Busy --> Suspended : jam

        state Suspended
        Suspended --> Ready : cancel
        Suspended --> HistoryState1 : resume

    }"""

print("=== Mermaid Code ===")
print(mermaid_code)
print()

# First test the raw converter
from mermaid_parser.converters.state_diagram import StateDiagramConverter

converter = StateDiagramConverter()
result = converter.convert(mermaid_code)

print(f"=== Raw Converter Transitions ({len(result.transitions)}) ===")
for t in result.transitions[:10]:  # Show first 10
    from_id = getattr(t.from_state, "id_", "?") if hasattr(t, "from_state") else "?"
    to_id = getattr(t.to_state, "id_", "?") if hasattr(t, "to_state") else "?"
    label = getattr(t, "label", "")
    print(f"  {from_id} --> {to_id} : {label}")
print()

# Run the full parsing pipeline
from mermaid_to_sherpa_parser import parse_mermaid_with_library

states, transitions, hierarchical, initial, parallel, annotations = (
    parse_mermaid_with_library(mermaid_code)
)

print("=== Parsed States (hierarchical) ===")
import json

print(json.dumps(states, indent=2))
print()

print("=== Hierarchical Structure ===")
print(hierarchical)
print()

print("=== Parsed Transitions ===")
print(f"Number of transitions: {len(transitions)}")
for t in transitions:
    print(t)
