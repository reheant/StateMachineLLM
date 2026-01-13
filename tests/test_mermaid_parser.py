#!/usr/bin/env python3
"""Test script to explore mermaid-parser-py output format"""

from mermaid_parser import MermaidParser
import json

# Simple test case
simple_mermaid = """stateDiagram-v2
    [*] --> Off
    Off --> On : on
    On --> Off : off
"""

# More complex test with hierarchical states and guards
complex_mermaid = """stateDiagram-v2
    [*] --> Off
    Off --> On : on

    state On {
        [*] --> Idle
        On --> Off : off

        Idle --> Idle : login(cardID) [!idAuthorized(cardID)]
        Idle --> Ready : login(cardID) [idAuthorized(cardID)] / {action="none"}

        Ready --> Idle : logoff
        Ready --> Ready : start [action=="scan" && !originalLoaded()]
    }
"""

parser = MermaidParser()

print("=" * 80)
print("SIMPLE MERMAID TEST")
print("=" * 80)
print(simple_mermaid)
print("\nPARSED OUTPUT:")
simple_result = parser.parse(simple_mermaid)
print(json.dumps(simple_result, indent=2))

print("\n" + "=" * 80)
print("COMPLEX MERMAID TEST")
print("=" * 80)
print(complex_mermaid)
print("\nPARSED OUTPUT:")
complex_result = parser.parse(complex_mermaid)
print(json.dumps(complex_result, indent=2))
