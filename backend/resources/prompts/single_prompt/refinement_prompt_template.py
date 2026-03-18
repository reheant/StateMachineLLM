"""
Refinement prompt template for the Two-Shot State Machine Framework.

This is a self-contained single-turn prompt — it does not rely on any
conversation history from shot 1. The LLM receives only what it needs to
review and correct the generated diagram: the system description, the
full custom Mermaid syntax rules, the previously generated Mermaid code,
and the error checklist.

Follows the same Claude prompting best practices as single_prompt_template:
- XML tags to delimit each section unambiguously
- "Why" motivation behind every rule: explains the parser consequence so
  the model treats each check as mandatory, not advisory
- <example> tags with descriptive type attributes for inline examples
- Numbered task steps with explicit self-verify gate before writing output
- Positive-framing output instructions (state what to do, not what to avoid)
- No-preamble constraint: first character of the response must be `<`
- Scoped modification guard: only add/change what the error checks require;
  states may not be added or removed, but missing transitions, guards, and
  actions grounded in the system description may be added
"""


def build_refinement_prompt(
    first_shot_mermaid: str, system_prompt: str, mermaid_syntax: str
) -> str:
    """
    Build the self-contained refinement prompt for the 2-shot second call.

    This is sent as a fresh single-turn request — no conversation history
    is included. It gives the LLM exactly what it needs to review and
    correct the diagram: the original system description (so it can judge
    whether the diagram is semantically complete), the full custom Mermaid
    syntax rules (so corrections stay valid under the project's parser),
    the previously generated Mermaid code, and a targeted error checklist.

    Args:
        first_shot_mermaid: The Mermaid code extracted from the LLM's first
            response (output of mermaidCodeSearch on shot 1).
        system_prompt: The original system description that was given to the
            LLM in shot 1.
        mermaid_syntax: The full custom Mermaid syntax and modeling rules
            string (same value passed to build_single_prompt in shot 1).

    Returns:
        str: The fully assembled refinement prompt, ready to be sent as a
            standalone user message to the LLM.
    """
    return f"""<instructions>
The diagram in <previous_output> is your first attempt at modeling the system \
in <system_description>. First drafts commonly have structural gaps: \
multi-step processes collapsed into single transitions, states that should be \
grouped into composites left flat, missing history states, and incomplete \
transition labels. Treat the previous output as a starting point, not a \
finished product. Use <system_description> as your ground truth — if any \
described behavior is not fully and accurately captured in the diagram, \
restructure it until it is. The checklist in <common_errors> identifies the \
most common failure patterns; work through each one critically. The diagram \
you output must also conform to the syntax rules in <mermaid_syntax>, which \
the downstream parser enforces mechanically.
</instructions>

<system_description>
{system_prompt}
</system_description>

<mermaid_syntax>
{mermaid_syntax}
</mermaid_syntax>

<previous_output>
{first_shot_mermaid}
</previous_output>

<common_errors>
Each entry below names an error, explains WHY it causes a problem, and \
shows the correct pattern. Check your output against each one in order.

<error id="1" name="Missing history states for composite states that can be interrupted and resumed">
When a composite state can be interrupted by an external event and later \
re-entered, a history state (`state H` declared inside the composite) must \
be present so the machine resumes the last active substate rather than \
restarting from the initial pseudostate. Re-entry from outside the composite \
should target H directly. If the system description implies \
interrupted-and-resumed behavior for a composite state and your diagram \
omits the history state, add it.

Two legal patterns for targeting a history state:
- The composite state itself transitions to its history state on re-entry:
  `CompositeState --> H : reenter`
- A state outside the composite transitions directly to H:
  `OutsideState --> H : reenter`

<examples>
<example type="incorrect – composite interrupted but no history state">
    state Active {{
        state Step1
        state Step2
        [*] --> Step1
        Step1 --> Step2 : next
    }}
    state Suspended
    Active --> Suspended : interrupt
    Suspended --> Active : resume    ← resumes from Step1 every time, ignoring prior progress
</example>

<example type="correct – history state preserves last active substate">
    state Active {{
        state Step1
        state Step2
        state H
        [*] --> Step1
        Step1 --> Step2 : next
    }}
    state Suspended
    Active --> Suspended : interrupt
    Suspended --> H : resume    ← resumes from whichever substate was active
</example>
</examples>
</error>

<error id="2" name="Missing transitions implied by the system description">
Re-read the system description and compare every event, condition, or \
behavioral path it describes against the transitions in your diagram. A \
transition is missing when the description clearly states that one state \
can lead to another under some event or condition but no corresponding \
`SourceState --> TargetState : event` line exists in the diagram. Missing \
transitions cause the machine to get stuck or behave incorrectly at runtime \
— the parser accepts the diagram but the modeled behavior is wrong. Add \
every transition that is grounded in the system description and absent from \
your output.

<examples>
<example type="incorrect – error recovery transition omitted">
    state Processing
    state Done
    state Error
    [*] --> Processing
    Processing --> Done : success
    ← description says errors can be retried, but Processing --> Error and Error --> Processing are missing
</example>

<example type="correct – all described transitions present">
    state Processing
    state Done
    state Error
    [*] --> Processing
    Processing --> Done : success
    Processing --> Error : failure
    Error --> Processing : retry
</example>
</examples>
</error>

<error id="3" name="Incomplete transition labels — missing guards or actions described in the system">
Re-read the system description for each transition in your diagram. A \
guard is missing when the description states a condition that must be true \
for the transition to fire but no `[condition]` appears on that transition \
line. An action is missing when the description states that an activity \
occurs when a transition fires but no `/ action` appears on that line. \
Omitting guards makes the machine fire unconditionally where it should not; \
omitting actions loses behavior that the system requires. Add every guard \
and action that is explicitly described and absent from your output.

<examples>
<example type="incorrect – guard and action omitted">
    Idle --> Active : start
    ← description says transition only fires when authorized, and door must lock on entry
</example>

<example type="correct – guard and action present">
    Idle --> Active : start [authorized] / lockDoor()
</example>
</examples>
</error>

<error id="4" name="Multi-step behavioral sequences collapsed into a single transition">
When the system description describes a behavior that unfolds in multiple \
distinct phases — where the system waits for input, waits for a timer, or \
offers a cancellable intermediate step — each phase must be a separate state. \
Collapsing these phases into a single transition loses intermediate behavior \
that the model must capture.

Signs that a process needs intermediate states:
- The description uses "then" between distinct phases of a process.
- A phase exists where the system waits for the user to act before proceeding.
- A timed waiting phase exists (the system waits X seconds before something fires).
- A step can be cancelled or reversed before the process completes.

Re-read every described process and verify that each distinct phase is \
represented as a state, not folded into a guard or event label on a single \
transition.

<examples>
<example type="incorrect – multi-step process collapsed into one transition">
    state Active
    state Off
    Active --> Off : triggerAction [after5s]
    ← description says: user triggers action → system enters a waiting phase \
with a confirmation message → user confirms → completes (cancellable during the wait)
</example>

<example type="correct – intermediate waiting phase modeled as its own state">
    state Active
    state PendingConfirmation
    state Off
    Active --> PendingConfirmation : triggerAction
    PendingConfirmation --> Off : confirmed
    PendingConfirmation --> Active : cancel
</example>
</examples>
</error>

<error id="5" name="Flat structure where composite states are implied">
When a set of states all share the same external transitions (every state in \
the group exits on the same event to the same target), or when the description \
refers to them collectively as a named process or mode, they belong inside a \
composite state. Leaving them flat duplicates the shared transitions on every \
state and loses the hierarchical structure the description implies.

Signs that states should be grouped into a composite:
- Multiple states all exit on the same event to the same target state.
- The description names a process or operational mode that contains several \
  internal phases.
- A group of states all represent sub-steps of a single described operation.

Group the states into a composite, declare a single shared external transition \
on the composite, and declare an initial pseudostate inside it.

<examples>
<example type="incorrect – substates flat, each repeating the same shared exit">
    state StepA
    state StepB
    state StepC
    [*] --> StepA
    StepA --> StepB : next
    StepB --> StepC : next
    StepA --> Idle : interrupt
    StepB --> Idle : interrupt
    StepC --> Idle : interrupt
</example>

<example type="correct – substates grouped in a composite with one shared exit">
    state Process {{
        state StepA
        state StepB
        state StepC
        [*] --> StepA
        StepA --> StepB : next
        StepB --> StepC : next
    }}
    Process --> Idle : interrupt
</example>
</examples>
</error>
<error id="6" name="History state naming or usage violations">
History states must always be named exactly `H` — never with suffixes like \
`H_Mode`, `H_TK`, `H_Alarm`, etc. An underscore in a state name like \
`H_Mode` causes the parser to interpret it as a composite state `H` \
containing a child state `Mode`, producing a broken diagram. History states \
are locally scoped to their parent composite, so every composite that needs \
one simply declares `state H` inside its own block.

Additionally, every declared `state H` must be targeted by at least one \
transition originating from outside its parent composite. Declaring a \
history state without wiring transitions to it is a common mistake — \
especially when adding history states during refinement. After declaring \
`state H` inside a composite, you must also update the transitions that \
re-enter that composite so they target `H` instead of the composite itself.

<examples>
<example type="incorrect – suffixed history state name">
    state Running {{{{
        state PhaseA
        state PhaseB
        state H_Run
        [*] --> PhaseA
    }}}}
    Paused --> H_Run : continue
    ← parser breaks: H_Run becomes composite H with child Run
</example>

<example type="incorrect – history state declared but no transition targets it">
    state Running {{{{
        state PhaseA
        state PhaseB
        state H
        [*] --> PhaseA
    }}}}
    Paused --> Running : continue
    ← H is declared but the re-entry transition still targets Running, not H
</example>

<example type="correct – history state declared and re-entry targets H">
    state Running {{{{
        state PhaseA
        state PhaseB
        state H
        [*] --> PhaseA
    }}}}
    Paused --> H : continue    ← re-entry now targets H inside Running
</example>
</examples>
</error>
</common_errors>

<task>
Work through the following steps in order. Place your review in <thinking> \
tags, then write the corrected diagram in step 3.

1. Check your previous output against each error in <common_errors> in order \
   (errors 1, 2, 3, 4, 5, 6). For each error, state explicitly whether it is \
   present and, if so, identify every affected state or transition.
2. List every correction and addition you will make. If no errors are found, \
   state that explicitly and confirm the diagram is correct as-is.
3. Output the corrected (or confirmed-correct) diagram using the exact \
   tags shown — nothing else may appear after the closing tag:
   <mermaid_code_solution>YOUR_MERMAID_CODE_HERE</mermaid_code_solution>
</task>

<output_instructions>
- Begin your response immediately with `<thinking>` tags — the very first \
  character of your response must be `<`. Any text before `<thinking>` is \
  a violation.
- Place your review (steps 1–2) inside <thinking>...</thinking> tags.
- Write plain Mermaid code inside the solution tags — no markdown fences \
  (```), no comments, no extra text.
- Nothing may appear after the closing </mermaid_code_solution> tag.
- You may add states, intermediate phases, composite structures, transitions, \
  guards, and actions whenever they are grounded in the system description. \
  Do not invent behavior that has no basis in the description.
</output_instructions>
"""
