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
    extract_exam_from_markdown,
    generate_mcq_from_example,
    generate_short_answer_from_example,
    generate_true_false_from_example,
)
from app.services.ocr_service import ocr_document_to_markdown
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

        # Create a shared temp directory that persists for OCR tasks
        import os

        shared_temp_dir = f"/tmp/ocr_{doc_id}"
        os.makedirs(shared_temp_dir, exist_ok=True)

        try:
            local_path = os.path.join(shared_temp_dir, os.path.basename(storage_path))
            download_file(storage_path, local_path)

            # Get the number of pages first
            from app.services.ocr_service import convert_to_pdf, pdf_to_images

            if local_path.lower().endswith(".pdf"):
                pdf_path = local_path
            else:
                pdf_path = convert_to_pdf(local_path, shared_temp_dir)

            if not pdf_path:
                raise Exception("Failed to convert document to PDF")

            # Convert to images ONCE and store in shared temp directory
            prefix = os.path.join(shared_temp_dir, "page")
            images = pdf_to_images(pdf_path, prefix)
            total_pages = len(images)

            if total_pages == 0:
                raise Exception("No pages found in document")

            # Update document with OCR progress tracking and temp directory path
            update_document(
                doc_id,
                {
                    "ocr_total": total_pages,
                    "ocr_completed": 0,
                    "ocr_pages": {},  # Will store results per page
                    "temp_dir": shared_temp_dir,  # Store temp directory path for cleanup
                },
            )

            # Enqueue parallel OCR jobs for each page with local image paths
            from app.workers.queues import enqueue_ocr_pages

            enqueue_ocr_pages(doc_id, images)

        except Exception as e:
            # Clean up temp directory on error
            import shutil

            if os.path.exists(shared_temp_dir):
                shutil.rmtree(shared_temp_dir, ignore_errors=True)
            raise e

    except Exception as e:  # noqa: BLE001
        logger.exception("OCR initialization failed")
        update_document(
            doc_id, {"ocr_status": "error", "extract_status": "error", "error": str(e)}
        )


def ocr_single_page(doc_id: str, image_local_path: str, page_index: int) -> None:
    """OCR a single page from local image file"""
    _ensure_init()
    try:
        from app.services.ocr_service import image_to_markdown

        logger.info(
            "Starting OCR for doc %s, page %d, image: %s",
            doc_id,
            page_index,
            image_local_path,
        )

        # Check if image file exists
        import os

        if not os.path.exists(image_local_path):
            raise Exception(f"Image file not found: {image_local_path}")

        # OCR the specific page
        markdown = image_to_markdown(
            image_local_path,
            os.getenv("OPENROUTER_API_KEY", ""),
            os.getenv("OCR_MODEL_NAME"),
        )

        if not markdown:
            markdown = "% ERROR: OCR failed on page"

        logger.info(
            "OCR completed for doc %s, page %d, storing result", doc_id, page_index
        )

        # Store the result and update progress
        from app.services.firestore_service import update_ocr_page_result

        update_ocr_page_result(doc_id, page_index, markdown)

        logger.info("OCR result stored for doc %s, page %d", doc_id, page_index)

    except Exception as e:  # noqa: BLE001
        logger.exception("OCR page %d failed for doc %s", page_index, doc_id)
        # Store error result
        from app.services.firestore_service import update_ocr_page_result

        update_ocr_page_result(doc_id, page_index, f"% ERROR: {str(e)}")


def extract_after_ocr(doc_id: str) -> None:
    """Extract exam structure after all OCR pages are complete"""
    _ensure_init()
    try:
        update_document(doc_id, {"extract_status": "processing"})

        # Get all OCR results
        from app.services.firestore_service import get_ocr_pages_results

        pages = get_ocr_pages_results(doc_id)

        if not pages:
            raise Exception("No OCR results found")

        # Extract exam structure
        exam = extract_exam_from_markdown(pages)
        save_original_exam(doc_id, exam)
        update_document(doc_id, {"extract_status": "done"})

        # Clean up temporary directory
        from app.services.firestore_service import cleanup_temp_directory

        cleanup_temp_directory(doc_id)

    except Exception as e:  # noqa: BLE001
        logger.exception("Extract failed for doc %s", doc_id)
        update_document(doc_id, {"extract_status": "error", "error": str(e)})
        # Still try to clean up on error
        try:
            from app.services.firestore_service import cleanup_temp_directory

            cleanup_temp_directory(doc_id)
        except:
            pass  # Don't fail extraction due to cleanup issues


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
