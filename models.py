from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class QuestionDetailBase(BaseModel):
    """
    Question schema for extracting individual questions from question papers.
    Note: Gemini API does not support Field(default=...) in response_schema,
    so all optional fields use Optional[type] instead.
    """
    question_number: str = Field(
        description="The number/identifier of the question (e.g., '1', '2a', '10A', '10B'). For questions with sub-parts like 10A and 10B, keep them together as ONE question with clear sub-part mapping."
    )
    
    question_type: Literal["MCQ", "Subjective"] = Field(
        description="Classify as 'MCQ' if the question has multiple choice options (A/B/C/D) or 'Subjective' if it requires written answers."
    )
    
    question_text: str = Field(
        description="The complete text of the question in KaTeX-renderable LaTeX format. Use $ for inline math and $$ for display math. Include ALL parts (A, B, etc.) if they belong to the same question number. Preserve exact mathematical notation, symbols, and formatting."
    )
    
    marks: float = Field(
        description="The total marks allocated for this question. For questions with sub-parts, sum the marks of all parts."
    )
    
    is_choice_question: Optional[bool] = Field(
        description="Set to true if this is a choice question (e.g., 'Answer any 2 out of 3'). Otherwise false."
    )
    
    choice_instruction: Optional[str] = Field(
        description="Instructions for choice questions (e.g., 'Answer any two questions', 'Attempt all parts'). Empty string if not applicable."
    )
    
    diagram_description: Optional[str] = Field(
        description="Detailed description of any diagram, figure, graph, or image associated with this question. Include what the diagram shows, labels, and relevant details. Empty string if no diagram."
    )
    
    sub_parts_mapping: Optional[str] = Field(
        description="For questions with sub-parts (e.g., 10A and 10B, or parts i, ii, iii), clearly describe the structure. Example: 'Part A: 5 marks, Part B: 5 marks' or '(i) 2 marks (ii) 3 marks (iii) 5 marks'. Empty string if single-part question."
    )


class QuestionPaperBase(BaseModel):
    """
    Complete question paper schema containing all extracted questions.
    """
    questions: List[QuestionDetailBase] = Field(
        description="A list of all questions found in the question paper. Questions with sub-parts like 10A and 10B should be combined into a SINGLE question entry with detailed sub_parts_mapping."
    )
    
    total_max_marks: float = Field(
        description="The calculated total maximum marks for the entire question paper. Sum all question marks considering choice questions appropriately."
    )
