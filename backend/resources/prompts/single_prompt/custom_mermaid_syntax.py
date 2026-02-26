mermaid_syntax = """
<state_declaration>
Declare every state explicitly before referencing it anywhere in the diagram, the parser
resolves names top-to-bottom, so an undeclared name causes a hard failure.

Syntax: `state StateName`
</state_declaration>

<initial_state>
Every diagram and every composite/parallel region must have exactly one initial pseudostate.
Declare the target state BEFORE the initial transition; because the parser reads declarations
top-to-bottom, a state that appears in a transition before its `state` line causes a hard failure.

Syntax: `[*] --> StateName`

<examples>
<example type="correct">
    stateDiagram-v2
    state Off
    state On
    [*] --> Off
    Off --> On : powerOn
    On --> Off : powerOff
</example>

<example type="incorrect state referenced before its declaration">
    stateDiagram-v2
    [*] --> Off          ← Off is used here but has not been declared yet
    state On
    Off --> On : powerOn
    On --> Off : powerOff
</example>
</examples>
</initial_state>

<transitions>
Declare every transition explicitly. Include both source and target state names on every line.

Syntax - use the most specific form that applies:
- Event, Guard, and Action: `SourceState --> TargetState : event [guard] / action`
- Event and Action:         `SourceState --> TargetState : event / action`
- Event and Guard:          `SourceState --> TargetState : event [guard]`
- Event only:               `SourceState --> TargetState : event`
</transitions>

<guards>
A guard is a boolean condition that must evaluate to true for the transition to fire.
Enclose the guard in square brackets immediately after the event label so the parser
can distinguish it from the action.

Syntax: `SourceState --> TargetState : event [guard]`
</guards>

<actions>
<transition_actions>
Purpose: describe activities executed when a transition fires (e.g., sending a signal,
updating a variable). Actions run only when the transition is taken AND any guard
evaluates to true.

Syntax: `Source --> Target : event [guard] / action`

Action labels use imperative style and may include arguments: `lockDoor()`, `startTimer(10s)`.
When multiple actions must occur on the same logical event, place them on separate transitions
or document them in a `note` block for clarity.
</transition_actions>

<state_actions>
Purpose:
- `entry` - executes once when the state is entered.
- `exit`  - executes once when the state is exited.
- `do`    - executes continuously while the system remains in the state.

Declare state actions in a `note right of` block placed AFTER the state or composite-state
declaration - the parser expects the note to follow its target state.

Syntax:
    note right of StateName
        entry / actionOnEntry()
        exit / actionOnExit()
        do: ongoingAction()
    end note

<example>
    state WashCycle {{
        [*] --> WaterIntake
        WaterIntake --> Washing : tankFull
    }}

    note right of WashCycle
        entry / lockDoor()
        exit / unlockDoor()
        do: monitorWaterLevel()
    end note
</example>
</state_actions>
</actions>

<events>
An event is the trigger that causes a transition to fire.
Declare it after the colon on the transition line.

Syntax: `SourceState --> TargetState : event`
</events>

<parallel_regions>
Use parallel regions to model concurrent activities that proceed independently.
Separate regions with `--` inside a parent composite state.
Each region is self-contained: declare its own states and its own initial pseudostate
(`[*] --> Substate`) - missing either causes a parse error for that region.
Cross-region transitions must reference explicit substate names.

Parallel regions may contain composite states; apply the composite-state rules inside
each region exactly as you would at the top level.

<example>
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
</example>
</parallel_regions>

<composite_states>
Purpose: group related substates under a named parent to model internal phases while
keeping the same external interface.
Use a composite state when:
- A state has multiple internal phases or steps.
- Substates share external transitions or entry/exit behavior.
- Re-entry must resume the last active substate (pair with a history state).
- The flat model becomes too complex to read.

Syntax: `state CompositeName {{ ... }}`
Declare substates and an initial pseudostate inside the braces.

Typically, a composite state will have a history state to enable resuming the last active substate on re-entry, but this is not strictly required if the system's behavior does not demand it. If a history state is included, follow the rules in the <history_states> section.

Rules - each violation causes a parse or semantic error:
1. Declare the composite state before referencing it in any transition.
2. The composite block must contain an initial pseudostate (`[*] --> Substate`).
3. Place entry/exit/do `note` blocks AFTER the composite declaration, outside the braces.
4. If a history state is declared inside the composite, it is exclusively for external
   re-entry; substates must not transition directly to it. The two valid use cases for a history state are:
   a) The composite state itself transitions to its history state on re-entry:
        `Composite --> H : reenter / resumeAction`
    b) An external state transitions directly to the history state:
        `Outside --> H : reenter`
   Any other usage is a violation that causes incorrect behavior or parse errors.

<example>
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
</example>
</composite_states>

<history_states>
Purpose: when a composite state is re-entered from outside, a history state causes the
machine to resume the last active substate instead of restarting from the initial pseudostate.

Rules - violations produce incorrect re-entry behavior or parse errors:
1. Declare history states inside the composite state's block.
2. Target a history state only from a transition that originates OUTSIDE the composite,
   or from the composite state itself (e.g., `Composite --> H : reenter / resumeAction`
   or `Outside --> H : reenter`).
3. Substates inside the same composite must NEVER transition directly to the history state.
4. History states are exclusively for external re-entry; do not use them for internal
   navigation, sequencing, or normal state flow.

<examples>
<example type="correct - composite transitions to its own history state">
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
</example>

<example type="correct - external state transitions directly to history state">
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
</example>

<example type="incorrect - substate transitions directly to history state">
    stateDiagram-v2
    [*] --> Outside
    Outside --> Composite : enter
    state Composite {{
        state A
        state H
        [*] --> A
        A --> H : illegal / bad    ← substates must never target the history state
    }}
</example>
</examples>
</history_states>
"""