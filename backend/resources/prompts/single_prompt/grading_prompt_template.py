def build_grading_prompt(
    student_mermaid_code: str,
    ground_truth_csv: str,
    system_description: str,
) -> str:
    """Build the automatic grading prompt for a generated Mermaid state machine."""
    return f"""<role>
You are a professor who specializes in state machine modeling and evaluation.
</role>

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
</documents>

<instructions>
Your task is to complete the provided ground-truth grading sheet CSV.

1. Keep the CSV structure exactly the same:
     - Same header
     - Same row order
     - Same values in non-grading columns

2. Fill only the grading column and notes/justification column for each row.

3. For rows where Element is "additional elements" (case-insensitive):
     - Use integers only in the grading column: 0, 1, 2, 3, ...
     - Add 1 only when an element in that category should fundamentally not be modeled at all.
     - Do not add values for style preferences, optimization opportunities, or simplifications.

4. For all other rows, grading must be one of: 0, 0.5, 1.
     - 1: The concept is correctly represented.
     - 0.5: The concept is partially represented.
     - 0: The concept is not represented.

5. Use semantic equivalence, not exact naming or syntax. Ground grading in the system description as source-of-truth behavior.

6. Keep notes concise and concrete.

7. Return CSV only. Do not include XML, markdown fences, commentary, or any text before/after the CSV.
</instructions>
"""
