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
Your task is to grade the student's state machine against the atomic components listed in the ground truth CSV.

1. Evaluate every row that is not part of the "additional elements" section using these scores only:
     - 1: The concept is correctly represented. Names/syntax may differ, but the same behavior is clearly present.
     - 0.5: The concept is partially represented (incomplete or only partly correct).
     - 0: The concept is not represented.

2. Use semantic equivalence, not exact naming or syntax. If the underlying behavior exists, score 1.

3. Evaluate rows that belong to "additional elements" differently:
     - Use integers only: 0, 1, 2, 3, ...
     - Add 1 only when an element in that category should fundamentally not be modeled at all.
     - Do not add values for style preferences, optimization opportunities, or simplifications.

4. Ground your grading in the system description as source-of-truth behavior.

5. Keep justifications concise and concrete.

6. Return output in this exact XML structure and do not add any preamble text:
<grading_report>
    <atomic_components>
        <item>
            <type>...</type>
            <element>...</element>
            <score>0|0.5|1</score>
            <justification>...</justification>
        </item>
        ...
    </atomic_components>
    <additional_elements>
        <item>
            <category>...</category>
            <score>0|1|2|...</score>
            <justification>...</justification>
        </item>
        ...
    </additional_elements>
</grading_report>
</instructions>
"""
