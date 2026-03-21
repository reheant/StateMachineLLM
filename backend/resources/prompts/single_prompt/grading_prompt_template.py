def build_grading_prompt(
    student_mermaid_code: str,
    ground_truth_mermaid_code: str,
    ground_truth_csv: str,
    system_description: str,
) -> str:
    """Build the automatic grading prompt for a generated Mermaid state machine."""
    return f"""<role>
You are a professor specializing in state machine modeling and grading.
You evaluate student state machine submissions against the system description, the ground truth CSV, and the corresponding ground truth Mermaid code, and complete the grading CSV with high precision.
</role>

<context>
The system description is the source of truth.
The student submission and the ground truth Mermaid code are written in slightly modified Mermaid.
The grading sheet CSV already contains the rubric rows and must be preserved exactly except for the grading fields you are instructed to fill.
The ground truth Mermaid code is provided to help you understand how the rubric applies to the system description, but do not simply copy elements from the ground truth Mermaid code into the grading sheet.
</context>

<documents>
    <document index="1">
        <source>system_description</source>
        <document_content>
{system_description}
        </document_content>
    </document>
    <document index="2">
        <source>student_submission_mermaid</source>
        <document_content>
{student_mermaid_code}
        </document_content>
    </document>
    <document index="3">
        <source>ground_truth_grading_sheet_csv</source>
        <document_content>
{ground_truth_csv}
        </document_content>
    </document>
    <document index="4">
        <source>ground_truth_mermaid_code</source>
        <document_content>
{ground_truth_mermaid_code}
        </document_content>
    </document>
</documents>

<instructions>
Your task is to return the completed grading sheet CSV.

<rule_1>
Preserve the CSV structure exactly:
- keep the same header
- keep the same row order
- keep all existing values unchanged in every non-grading column
</rule_1>

<rule_2>
Modify only these two columns for each row:
- grading column
- notes/justification column

Do not edit, rename, reorder, remove, or add any other column or row.
</rule_2>

<rule_3>
Use the system description as the source of truth for expected behavior.
Use the student Mermaid diagram only to determine whether each rubric item is represented.
Judge semantic meaning, not exact wording, naming, or diagram syntax.
Accept reasonable equivalents when they capture the intended system behavior correctly.
</rule_3>

<rule_4>
For rows whose Element value is "additional elements" (case-insensitive):
- grading must be a non-negative integer only: 0, 1, 2, 3, ...
- add 1 only for an element that should fundamentally not be modeled at all
- do not count harmless extra detail, acceptable abstraction differences, stylistic choices, optimization opportunities, or reasonable modeling choices
- if an extra element is unnecessary but still reasonable, assign 0
</rule_4>

<rule_5>
For all other rows, grading must be exactly one of:
- 1
- 0.5
- 0

Use this scale:
- 1 = correctly represented, or represented by a reasonable equivalent that captures the intended system behavior (minor loss of meaning allowed)
- 0.5 = partially represented, incomplete, ambiguous, or only partly correct (but not fundamentally wrong)
- 0 = not represented, clearly incorrect, or contradicts the system description
</rule_5>


<rule_6>
Write notes/justification that are:
- concise
- concrete
- specific to the row being graded

Do not write generic comments.
Briefly explain why the score was assigned, referencing the student model behavior when useful.
</rule_6>

<rule_7>
Be strict about factual correctness, meaning the student’s submission must accurately reflect the system description and intended behavior. However, do not penalize superficial or stylistic differences when the underlying semantics are correct.

When evaluating the student submission, consider the following:
- accept structurally different but semantically equivalent representations
- treat additional elements (e.g., extra states, composite states, transitions) as correct if they preserve the intended behavior
- do not penalize alternative modeling approaches that are behaviorally equivalent to the expected solution
</rule_7>

<rule_8>
Before producing the final answer, verify all of the following:
- the output is valid CSV
- the header is unchanged
- the row count is unchanged
- the row order is unchanged
- the only modified columns are the grading and notes/justification columns
- only the grading and notes/justification columns were modified
- every "additional elements" row uses an integer grade only
- every other row uses only 0, 0.5, or 1
Not respecting any of these verification rules will be considered a failure to follow instructions and will result in a score of 0 for the entire grading task.
</rule_8>

<rule_9>
Do not copy any specific elements, names, or formatting from the ground truth Mermaid code into the grading sheet. Use the ground truth Mermaid code only to understand how the rubric applies to the system description and to help you determine whether the student submission is correct, partially correct, or incorrect for each rubric item.
</rule_9>

<output_requirement>
Return only the final CSV.
Do not include markdown.
Do not include code fences.
Do not include XML.
Do not include explanations before or after the CSV.
Not respecting the output requirement will be considered a failure to follow instructions and will result in a score of 0 for the entire grading task.
</output_requirement>
</instructions>
"""