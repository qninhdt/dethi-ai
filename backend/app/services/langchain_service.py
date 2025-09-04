import json
import logging
import os
from typing import Any, Dict, List

from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.schemas.exam import (
    Exam,
    MultipleChoiceQuestionWithAnswer,
    ShortAnswerQuestionWithAnswer,
    TrueFalseQuestionWithAnswer,
)

import json_repair

logger = logging.getLogger(__name__)


def wrapper_json_repair(input):
    content = input.content.strip()

    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]

    input.content = json.dumps(json_repair.loads(content))
    return input


json_repair_lambda = RunnableLambda(wrapper_json_repair)


def _build_llm(model_name: str, temperature: float = 0.2) -> ChatOpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
    return ChatOpenAI(
        model_name=model_name,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
    )


def extract_exam_from_latex(latex_pages: List[str]) -> Dict[str, Any]:
    model = os.getenv("OCR_MODEL_NAME")
    llm = _build_llm(model, temperature=0)
    parser = JsonOutputParser(pydantic_object=Exam)
    prompt = PromptTemplate(
        template=(
            open("./app/prompts/latex_to_json.txt", "r", encoding="utf-8").read()
        ),
        input_variables=["exam_content"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | json_repair_lambda | parser
    combined = "\n\\newpage\n".join(latex_pages)

    result = chain.invoke({"exam_content": combined})
    # The parser already returns a dictionary, so we can return it directly
    return result


def generate_mcq_from_example(example_json: Dict[str, Any]) -> Dict[str, Any]:
    model = os.getenv("GEN_MODEL_NAME")
    llm = _build_llm(model, temperature=0.5)
    parser = JsonOutputParser(pydantic_object=MultipleChoiceQuestionWithAnswer)
    prompt = PromptTemplate(
        template=open(
            "./app/prompts/generate_multiple_choice.txt", "r", encoding="utf-8"
        ).read(),
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | json_repair_lambda | parser
    out = chain.invoke({"question": json.dumps(example_json, ensure_ascii=False)})
    # The parser already returns a dictionary, so we can return it directly
    return out


def generate_true_false_from_example(example_json: Dict[str, Any]) -> Dict[str, Any]:
    model = os.getenv("GEN_MODEL_NAME")
    llm = _build_llm(model, temperature=0.5)
    parser = JsonOutputParser(pydantic_object=TrueFalseQuestionWithAnswer)
    prompt = PromptTemplate(
        template=open(
            "./app/prompts/generate_true_false.txt", "r", encoding="utf-8"
        ).read(),
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | json_repair_lambda | parser
    out = chain.invoke({"question": json.dumps(example_json, ensure_ascii=False)})
    # The parser already returns a dictionary, so we can return it directly
    return out


def generate_short_answer_from_example(example_json: Dict[str, Any]) -> Dict[str, Any]:
    model = os.getenv("GEN_MODEL_NAME")
    llm = _build_llm(model, temperature=0.5)
    parser = JsonOutputParser(pydantic_object=ShortAnswerQuestionWithAnswer)
    prompt = PromptTemplate(
        template=open(
            "./app/prompts/generate_short_answer.txt", "r", encoding="utf-8"
        ).read(),
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | json_repair_lambda | parser
    out = chain.invoke({"question": json.dumps(example_json, ensure_ascii=False)})
    # The parser already returns a dictionary, so we can return it directly
    return out
