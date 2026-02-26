"""
Prompt template for the Single Prompt State Machine Framework.

Follows Claude prompting best practices:
- Explicit role definition with motivation (why correctness matters)
- XML tags to clearly delimit each section of the prompt
- Long-form reference data (syntax rules, examples) placed before the query
  so the model ingests all context before seeing the specific task
  (query-last pattern can improve response quality by up to 30%)
- Per-example <example> tags so the model distinguishes examples from instructions
- Step-by-step numbered task at the very end, with a self-verification step
  before the final output to catch errors reliably
- Explicit CoT guidance via <thinking> tags (manual chain-of-thought)
- Positive-framing output instructions (tell Claude what to do, not what NOT to do)
- No-preamble enforced via positive constraint (first character must be `<`)
- Anti-hallucination guard: only model what is grounded in the problem description
"""


def build_single_prompt(
    mermaid_syntax: str,
    n_shot_examples_str: str,
    system_prompt: str,
) -> str:
    """
    Build the full single-prompt for state machine generation.

    The structure follows the Claude prompting best practice of placing
    long-form reference data (syntax rules, examples) near the top of the
    prompt and the specific query (problem description + task steps) at the
    end, which can improve response quality by up to 30% on complex inputs.

    Args:
        mermaid_syntax: The full custom Mermaid syntax and modeling rules string.
        n_shot_examples_str: Pre-formatted string of N-shot examples produced by
            get_n_shot_examples(..., ["system_description", "mermaid_code_solution"]).
        system_prompt: The natural-language description of the system to model.

    Returns:
        str: The fully assembled prompt ready to be sent to the LLM.
    """
    return f"""<role>
You are an expert state machine engineer. Your specialty is translating \
naturally-language system descriptions into precise, syntactically-valid \
state machine diagrams in a strict, custom Mermaid stateDiagram-v2 syntax. \
The diagram you produce will be fed directly into an automated parser, so \
even a single syntax error will break the pipeline — correctness is not \
optional.
</role>

<mermaid_syntax_rules>
The rules below define the ONLY valid syntax accepted by the downstream parser. \
Any deviation — including extra whitespace, wrong keyword casing, or an \
undeclared state — will cause a hard failure. Study them before you begin.

{mermaid_syntax}
</mermaid_syntax_rules>

<examples>
Each example below shows a real system description paired with its correct \
Mermaid solution. They demonstrate the expected level of detail, naming \
conventions, and syntax patterns. Treat them as the gold standard for your output.

{n_shot_examples_str}
</examples>

<problem_description>
{system_prompt}
</problem_description>

<task>
Work through the following steps in order. Place your analysis for steps 1–7 \
inside <thinking> tags so it is clearly separated from the final diagram. \
Then write the diagram in step 8.

1. Derive implicit knowledge — list facts that are implied but not stated \
   explicitly (e.g., default values, symmetric behaviours, unstated \
   termination conditions).
2. Extract states — identify every distinct state and justify each one.
3. Extract transitions — identify every event, guard, and action; explain \
   your reasoning for each.
4. Extract hierarchical states — identify composite states, their substates, \
   and the parent-child relationships.
5. Extract concurrent regions — identify parallel regions and explain how \
   they are separated.
6. Extract history states — identify where re-entry must resume the last \
   active substate and where history connectors are required.
7. Self-verify — before writing any code, go through your findings from \
   steps 1–6 and confirm: every state is declared before it is referenced; \
   transitions to a history state (H) occur only from the composite state \
   itself or from states outside the composite when the history state is \
   defined for external re-entry; every composite \
   state has an initial pseudostate; no syntax rule from \
   <mermaid_syntax_rules> is violated. Correct any issues you find.
8. Assemble the final Mermaid diagram using the verified information from \
   steps 1–7. Enclose the diagram code in the exact tags shown — nothing \
   else may appear after the closing tag:
   <mermaid_code_solution>YOUR_MERMAID_CODE_HERE</mermaid_code_solution>
</task>

<output_instructions>
- Begin your response immediately with `<thinking>` tags — the very first \
  character of your response must be `<`. Any text before the opening \
  `<thinking>` tag is a violation.
- Place your analysis (steps 1–7) inside <thinking>...</thinking> tags.
- The Mermaid code inside <mermaid_code_solution> must follow every rule \
  in <mermaid_syntax_rules> and match the patterns in <examples>.
- Write plain Mermaid code inside the solution tags — no markdown fences \
  (```), no comments, no extra text.
- Nothing may appear after the closing </mermaid_code_solution> tag.
- Only model states, transitions, and behaviors that are explicitly stated \
  in or clearly implied by <problem_description>. Do not invent states, \
  events, guards, or actions that have no basis in the description.
</output_instructions>
"""