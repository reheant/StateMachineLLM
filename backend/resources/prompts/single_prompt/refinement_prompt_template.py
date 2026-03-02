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
You previously generated a Mermaid stateDiagram-v2 state machine for the \
system description below. Review your output against the syntax rules in \
<mermaid_syntax> and the checklist in <common_errors>. The parser that \
consumes your output enforces each rule mechanically — any violation causes \
a hard failure regardless of how semantically correct the diagram is. \
Correct every issue you find, then output the final diagram.
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

</common_errors>

<task>
Work through the following steps in order. Place your review in <thinking> \
tags, then write the corrected diagram in step 3.

1. Check your previous output against each error in <common_errors> in order \
   (errors 1, 2, 3). For each error, state explicitly whether it is present \
   and, if so, identify every affected state or transition.
2. List every correction you will make. If no errors are found, state \
   that explicitly and confirm the diagram is correct as-is.
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
- Do not add, remove, or rename states beyond what error 1 requires. \
  You may add missing transitions, guards, and actions when they are \
  explicitly grounded in the system description (errors 2 and 3).
</output_instructions>
"""
