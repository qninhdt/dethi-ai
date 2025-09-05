from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

# ==============================================================================
# 1. Question Data Models
# These models define the structure for the 'data' field of different question types.
# ==============================================================================


class MultipleChoiceData(BaseModel):
    """Data model for a multiple-choice question."""

    options: List[str] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="A list of Markdown strings, each representing an option, without the leading label (e.g., 'A)', 'a.', etc).",
    )


class TrueFalseData(BaseModel):
    """Data model for a true/false question."""

    clauses: List[str] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="A list of Markdown strings for each clause, without the leading label (e.g., 'a)', 'b)', '1.', '2', etc).",
    )


# ==============================================================================
# 2. Element Models
# These models represent each component of the exam.
# We use a Discriminated Union based on the 'type' field.
# ==============================================================================


class TextElement(BaseModel):
    """Represents an instruction, or a heading in the exam."""

    type: Literal["text"] = "text"
    content: str = Field(..., description="The raw Markdown content of the text block.")


class BaseQuestionElement(BaseModel):
    """Base model for all question types."""

    content: str = Field(
        ...,
        description="The main body or stem of the question in Markdown format, without the question index (e.g., '1.', '2.', etc).",
    )


class MultipleChoiceQuestion(BaseQuestionElement):
    """Model for a multiple-choice question."""

    type: Literal["multiple_choice"] = "multiple_choice"
    data: MultipleChoiceData


class TrueFalseQuestion(BaseQuestionElement):
    """Model for a true/false question."""

    type: Literal["true_false"] = "true_false"
    data: TrueFalseData


class ShortAnswerQuestion(BaseQuestionElement):
    """Model for a short-answer or essay question (with no specific data structure)."""

    type: Literal["short_answer"] = "short_answer"
    data: None = None


# This Union allows Pydantic to automatically determine the correct model
# for an element based on the value of its 'type' field.
AnyElement = Union[
    TextElement, MultipleChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
]


class ExamMetadata(BaseModel):
    """Metadata for the exam."""

    title: str = Field(..., description="The title of the exam.")
    duration_minutes: Optional[int] = Field(
        None, description="The exam duration in minutes."
    )


class Exam(BaseModel):
    """Represents the entire structure of an exam."""

    metadata: ExamMetadata
    elements: List[AnyElement] = Field(
        ..., description="A list of the exam's components, ordered sequentially."
    )


class MultipleChoiceAnswer(BaseModel):
    """Model for the answer to a multiple-choice question."""

    selected_options: int = Field(
        ..., description="An integer (0-based) indicating the selected option."
    )

    explanation: str = Field(
        ...,
        description="A detailed explanation in Markdown format justifying why the selected options are correct.",
    )

    error_analysis: List[str] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="A list of explanations in Markdown format for each incorrect option, describing the common mistake that could lead a student to choose that option.",
    )


class TrueFalseAnswer(BaseModel):
    """Model for the answer to a true/false question."""

    clause_correctness: List[bool] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="A list of booleans indicating the correctness of each clause.",
    )

    general_explanation: Optional[str] = Field(
        None,
        description="An optional general step-by-step solution in Markdown format covering all necessary steps to determine the correctness of the clauses.",
    )

    explanations: List[str] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="A list of explanations in Markdown format for each clause, describing why it is true or false.",
    )


class ShortAnswerAnswer(BaseModel):
    """Model for the answer to a short-answer or essay question."""

    answer_text: str = Field(
        ...,
        description="A number, word, or phrase representing the answer in Markdown format.",
    )

    explanation: str = Field(
        ...,
        description="A detailed step-by-step solution in Markdown format explaining how to arrive at the answer.",
    )


class MultipleChoiceQuestionWithAnswer(MultipleChoiceQuestion):
    """Multiple-choice question model extended to include the answer."""

    answer: MultipleChoiceAnswer


class TrueFalseQuestionWithAnswer(TrueFalseQuestion):
    """True/false question model extended to include the answer."""

    answer: TrueFalseAnswer


class ShortAnswerQuestionWithAnswer(ShortAnswerQuestion):
    """Short-answer question model extended to include the answer."""

    answer: ShortAnswerAnswer


AnyElementWithAnswer = Union[
    TextElement,
    MultipleChoiceQuestionWithAnswer,
    TrueFalseQuestionWithAnswer,
    ShortAnswerQuestionWithAnswer,
]


class GeneratedExam(BaseModel):
    metadata: ExamMetadata
    elements: List[AnyElementWithAnswer]
