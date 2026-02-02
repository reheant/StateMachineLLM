#!/usr/bin/env python3
"""
Test image generation from Mermaid diagrams using Sherpa/GraphViz pipeline.
This test validates the dishwasher state machine and generates visual output.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.resources.mermaid_to_sherpa_parser import parse_mermaid_with_library
from backend.resources.util import create_single_prompt_gsm_diagram_with_sherpa

# Dishwasher Mermaid code
DISHWASHER_MERMAID = """stateDiagram-v2
    [*] --> Idle
    
    state Idle {
        [*] --> ProgramSelection
        state ProgramSelection
        ProgramSelection --> ProgramSelection : selectProgram
        ProgramSelection --> ProgramSelection : adjustDryingTime [dryingNotStarted]
    }

    Idle --> Running : start [doorClosed]

    state Running {
        [*] --> WashCycle

        state WashCycle {
            [*] --> Filling
            Filling --> Washing : tankFull
            Washing --> Draining : after(10min)
            Draining --> Filling : [cyclesRemaining]
            Draining --> Drying : [cyclesComplete]
        }

        state Drying {
            [*] --> DryingActive
            DryingActive --> DryingPaused : doorOpen
            DryingPaused --> DryingActive : doorClose [timeOpen<5min]
            DryingPaused --> Complete : [timeOpen>=5min]
            DryingActive --> Complete : after(dryingTime)
        }

        state Complete
    }

    Running --> Idle : programComplete

    note right of Running
        entry / lockDoor
        exit / unlockDoor
    end note

    note right of DryingPaused
        doorClose returns to DryingActive history state
    end note
"""


def test_dishwasher_image_generation():
    """Generate image from dishwasher Mermaid diagram"""
    print("=" * 80)
    print("DISHWASHER STATE MACHINE - Image Generation")
    print("=" * 80)
    
    # Create test output directory
    test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(test_output_dir, exist_ok=True)
    
    output_image_path = os.path.join(test_output_dir, 'dishwasher_diagram')
    
    # Generate image
    print("\nGenerating image using Sherpa/GraphViz pipeline...")
    try:
        success = create_single_prompt_gsm_diagram_with_sherpa(
            mermaid_code=DISHWASHER_MERMAID,
            diagram_file_path=output_image_path
        )
        
        if success:
            print(f"\n✓ Image generated successfully!")
            print(f"  Location: {output_image_path}.png")
            return True
        else:
            print(f"\n✗ Image generation failed")
            return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parser_validation():
    """Validate parser correctness"""
    print("\n" + "=" * 80)
    print("PARSER VALIDATION")
    print("=" * 80)
    
    states, transitions, hierarchical, initial, parallel, annotations = parse_mermaid_with_library(
        DISHWASHER_MERMAID
    )
    
    passed = True
    
    # Check history state in DryingActive
    print("\nValidation: History state detection")
    history_found = False
    
    for s in states:
        if isinstance(s, dict) and s.get('name') == 'Running':
            for child in s.get('children', []):
                if isinstance(child, dict) and child.get('name') == 'Drying':
                    for drying_child in child.get('children', []):
                        if isinstance(drying_child, dict) and drying_child.get('name') == 'DryingActive':
                            if 'H' in drying_child.get('children', []):
                                history_found = True
                                print(f"  ✓ PASS: H pseudo-state found in DryingActive")
                                print(f"    Structure: {drying_child}")
                            else:
                                print(f"  ✗ FAIL: No H in DryingActive: {drying_child}")
                                passed = False
    
    if not history_found:
        print(f"  ✗ FAIL: DryingActive history state not found")
        passed = False
    
    # Check history transition
    print("\nValidation: History transition")
    history_trans = [t for t in transitions if 'DryingActive_H' in t.get('dest', '')]
    
    if history_trans:
        print(f"  ✓ PASS: Found history transition:")
        for t in history_trans:
            print(f"    {t['source']} --{t['trigger']}--> {t['dest']}")
    else:
        print(f"  ✗ FAIL: No transition to DryingActive_H")
        passed = False
    
    return passed


if __name__ == "__main__":
    print("\nDISHWASHER STATE MACHINE - TEST SUITE")
    print("=" * 80)
    
    image_ok = test_dishwasher_image_generation()
    parser_ok = test_parser_validation()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Image Generation: {'✓ PASSED' if image_ok else '✗ FAILED'}")
    print(f"Parser Validation: {'✓ PASSED' if parser_ok else '✗ FAILED'}")
    
    test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    print(f"\nOutput: {test_output_dir}/dishwasher_diagram.png")
    
    sys.exit(0 if (image_ok and parser_ok) else 1)
