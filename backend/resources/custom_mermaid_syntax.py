mermaid_syntax = """
    STATE DECLARATION:
    - Declare every state explicitly 
    - Syntax: `state StateName`
    
    INITIAL STATE:
    - The initial state must be declared using the pattern `[*] --> StateName`
    - The state referenced in the initial transition must be declared as a state before it is referenced. 

    Valid Example:
        stateDiagram-v2
        state Off
        state On
        [*] --> Off
        Off --> On : powerOn
        On --> Off : powerOff

    Invalid Example:
        stateDiagram-v2
        [*] --> Off
        state On
        Off --> On : powerOn
        On --> Off : powerOff
    
    TRANSITIONS:
    - Declare all transitions explicitly, including both source and target states.

    - Syntax:
        - Transition with Event, Guard, and Action: `SourceState --> TargetState : event [guard] / action`
        - Transition with Event and Action: `SourceState --> TargetState : event / action`
        - Transition with Event and Guard: `SourceState --> TargetState : event [guard]`
        - Transition with Event only: `SourceState --> TargetState : event`
    
    GUARDS: 
    - Guards are conditions that must be true for a transition to occur. 
    - Syntax: `SourceState --> TargetState : event [guard]`
    
    ACTIONS:
        1) Action on transitions:
        - Purpose: describe activities that occur when a transition fires (e.g., sending a signal, updating a variable).
        - Syntax (Mermaid): Source --> Target : event [guard] / action
        - If multiple actions occur, separate them on different transitions or use a note block to list them clearly. 
        - Actions are labels (imperative style), optionally with parentheses for arguments: lockDoor(), startTimer(10s)
        - Actions execute only when the transition is taken and any guard evaluates to true.
        
        2) Entry / Exit / Do actions (actions attached to states)
        - Purpose: entry executes once when entering the state; exit executes once when leaving; do executes continuously while inside the state (ongoing activity).
        - Must be declared in a note block placed AFTER the state declaration:
            note right of StateName
                entry / actionOnEntry()
                exit / actionOnExit()
                do: ongoingAction()
            end note
        - Example:
            state WashCycle {{
                [*] --> WaterIntake
                WaterIntake --> Washing : tankFull
            }}

            note right of WashCycle
                entry / lockDoor()
                exit / unlockDoor()
            end note

    EVENT: 
    - Events are triggers that cause transitions between states. They are declared after the colon in the transition declaration (e.g., `: event`).
    - Syntax: `SourceState --> TargetState : event`
    
    PARALLEL REGIONS: 
    - Use parallel regions to represent concurrent states or activities that can occur simultaneously. Each region has its own set of states and transitions.
    - It is possible that parallel regions contain composite states. To model this, simply declare a composite state within a parallel region following the syntax and rules for composite states.
    - Syntax: separate parallel regions with `--` and declare states within each region as usual.
    - Rules: each region must declare its own states and an initial pseudostate (`[*] --> Substate`). Cross-region transitions must reference explicit substates.
    - Example:
        stateDiagram-v2
        [*] --> ParallelController
        state ParallelController {{
            state RegionA {{
                state Substate1
                state Substate2
                [*] --> Substate1
                Substate1 --> Substate2 : event1
            }}
            --
            state RegionWithComposite {{
                [*] --> CompositeState
                state CompositeState {{
                    state Substate3
                    state Substate4
                    [*] --> Substate3
                    Substate3 --> Substate4 : event2
                }}
            }}
        }}
        
    HIERARCHICAL/COMPOSITE STATES:
    - Purpose: group related substates under a named parent so the system can show internal phases while keeping the same external interface.
    - When to use:
        - A state contains multiple internal phases or steps.
        - Substates share external transitions or entry/exit behavior.
        - Re-entry should resume the last active substate (use history state).
        - The flat model is too complex to read.
    - Syntax: `state CompositeState {{ ... }}`. Declare substates and an initial pseudostate (`[*] --> Substate`) inside the braces.
    - Rules:
        - Declare the composite state before referencing it in transitions.
        - Place entry/exit/do note blocks AFTER the composite declaration (outside the braces).
        - History states must be declared inside the composite and may only be targeted from a state outside the composite or from the composite itself; substates MUST NOT transition directly to the history state. If a history state is declared, it is exclusively for external re-entry behavior and must not be used for internal navigation or state flow.
    - Example:
        stateDiagram-v2
        [*] --> Device
        state Device {{
            state Idle
            state Active {{
                state Step1
                state Step2
                [*] --> Step1
                Step1 --> Step2 : next
            }}
            Idle --> Active : start
        }}

        note right of Active
            entry / startTimer()
            exit / stopTimer()
        end note  
    
    HISTORY STATES:
    - Purpose: record the last active substate in a composite state so upon re-entry in that composite state, the state machine can automatically resume that substate instead of the initial substate.
    - Rules: 
        - Always declare history states inside a composite state's block.
        - Reference history states only for re-entry transitions originating from OUTSIDE the composite state or from the composite state itself (e.g., `CompositeState --> HistoryStateName : reenter / resumeAction` or `Outside --> HistoryStateName : reenter`).
        - Substates within the same composite state must never transition directly to the history state.
        - History states are used exclusively for external re-entry behavior and must not be used for internal navigation, sequencing, or state flow.
        - If the specification requires returning to the last active substate upon re-entry, the transition must originate from outside the composite state or from the composite state itself, and the history state must be declared inside the composite to enable this behavior.

    - Examples:
        - Valid (composite -> history):
            stateDiagram-v2
            [*] --> Outside
            state Outside
            state Composite
            state Composite {{
                state A
                state B
                state H
                [*] --> A
                A --> B : toB
            }}
            Composite --> H : reenter / resumeAction
            Outside --> Composite : enter

        - Valid (external state -> history):
            stateDiagram-v2
            [*] --> Outside
            state Outside
            state Composite
            state Composite {{
                state A
                state B
                state H
                [*] --> A
                A --> B : toB
            }}
            Outside --> H : reenter
            Outside --> Composite : enter

        - Invalid (substate -> history):
            stateDiagram-v2
            [*] --> Outside
            Outside --> Composite : enter
            state Composite {{
                state A
                state H
                [*] --> A
                A --> H : illegal / bad
            }}
    """
    