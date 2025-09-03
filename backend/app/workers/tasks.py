import json
import logging
import os
import tempfile
from typing import Any, Dict, List

from app.core.firebase import init_firebase
from app.services.firestore_service import (
    append_generated_question,
    create_generated_exam,
    increment_generated_exam_progress,
    set_generated_question_status,
    save_original_exam,
    set_generated_exam_status,
    update_document,
)
from app.services.langchain_service import (
    extract_exam_from_latex,
    generate_mcq_from_example,
    generate_short_answer_from_example,
    generate_true_false_from_example,
)
from app.services.ocr_service import ocr_document_to_latex
from app.services.storage_service import download_file

logger = logging.getLogger(__name__)


def _ensure_init():
    # RQ worker process needs Firebase initialized
    init_firebase()


def ocr_and_extract(doc_id: str, storage_path: str) -> None:
    _ensure_init()
    try:
        update_document(
            doc_id, {"ocr_status": "processing", "extract_status": "pending"}
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, os.path.basename(storage_path))
            download_file(storage_path, local_path)
            pages = ocr_document_to_latex(
                local_path,
                os.getenv("OPENROUTER_API_KEY", ""),
                os.getenv("OCR_MODEL_NAME"),
            )
            update_document(doc_id, {"ocr_status": "done"})
            update_document(doc_id, {"extract_status": "processing"})
            exam = extract_exam_from_latex(pages)
            save_original_exam(doc_id, exam)
            update_document(doc_id, {"extract_status": "done"})
    except Exception as e:  # noqa: BLE001
        logger.exception("OCR/Extract failed")
        update_document(
            doc_id, {"ocr_status": "error", "extract_status": "error", "error": str(e)}
        )


def generate_from_selected(
    doc_id: str,
    gen_id: str,
    selected_questions: List[Dict[str, Any]],
    target_count: int,
) -> None:
    _ensure_init()
    total = min(len(selected_questions), target_count)
    create_generated_exam(
        doc_id, gen_id, {"title": f"Generated Exam {gen_id}"}, total=total
    )
    try:
        for i, q in enumerate(selected_questions[:target_count]):
            qtype = q.get("type")
            try:
                if qtype == "multiple_choice":
                    new_q = generate_mcq_from_example(q)
                elif qtype == "true_false":
                    new_q = generate_true_false_from_example(q)
                else:
                    new_q = generate_short_answer_from_example(q)
                # Add original_id to the generated question
                new_q["original_id"] = q.get("id")
                append_generated_question(doc_id, gen_id, i, new_q)
                increment_generated_exam_progress(doc_id, gen_id)
            except Exception as inner:
                logger.exception("Generation failed for a question: %s", inner)
        set_generated_exam_status(doc_id, gen_id, "done")
    except Exception as e:  # noqa: BLE001
        logger.exception("Generate job failed")
        set_generated_exam_status(doc_id, gen_id, "error")


def generate_one_question(
    doc_id: str, gen_id: str, q: Dict[str, Any], question_index: int
) -> None:
    _ensure_init()
    try:
        set_generated_question_status(doc_id, gen_id, str(question_index), "processing")
        qtype = q.get("type")
        if qtype == "multiple_choice":
            new_q = generate_mcq_from_example(q)
        elif qtype == "true_false":
            new_q = generate_true_false_from_example(q)
        else:
            new_q = generate_short_answer_from_example(q)
        # Add original_id to the generated question
        new_q["original_id"] = q.get("id")
        append_generated_question(doc_id, gen_id, question_index, new_q)
        increment_generated_exam_progress(doc_id, gen_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("generate_one_question failed: %s", e)
        set_generated_question_status(
            doc_id, gen_id, str(question_index), "error", {"error": str(e)}
        )
