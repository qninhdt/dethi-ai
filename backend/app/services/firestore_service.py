import logging
import time
from typing import Any, Dict, List, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import get_firestore
from google.cloud.firestore_v1 import Increment

logger = logging.getLogger(__name__)

DOCS = "documents"
SUB_GENERATED = "generated_exams"
SUB_QUESTIONS = "questions"


def create_document(doc_id: str, payload: Dict[str, Any]) -> None:
    db = get_firestore()
    data = {**payload, "created_at": time.time()}
    db.collection(DOCS).document(doc_id).set(data)


def update_document(doc_id: str, patch: Dict[str, Any]) -> None:
    db = get_firestore()
    db.collection(DOCS).document(doc_id).set(patch, merge=True)


def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    db = get_firestore()
    snap = db.collection(DOCS).document(doc_id).get()
    return snap.to_dict() if snap.exists else None


def list_user_documents(user_id: str) -> List[Dict[str, Any]]:
    db = get_firestore()
    query = db.collection(DOCS).where(filter=FieldFilter("created_by", "==", user_id))
    docs = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        docs.append(data)
    return sorted(docs, key=lambda x: x.get("created_at", 0), reverse=True)


def save_original_exam(doc_id: str, exam: Dict[str, Any]) -> None:
    db = get_firestore()
    doc_ref = db.collection(DOCS).document(doc_id)
    doc_ref.collection(SUB_QUESTIONS).document("_meta").set({"type": "original"})

    # Extract only questions (not text elements) and use 0-based document IDs
    question_index = 0
    for el in exam.get("elements", []):
        if el.get("type") == "text":
            continue
        # Create question with 0-based document ID, no index field needed
        el_copy = {k: v for k, v in el.items()}
        doc_ref.collection(SUB_QUESTIONS).document(str(question_index)).set(el_copy)
        question_index += 1

    doc_ref.set({"original_exam": {"metadata": exam.get("metadata", {})}}, merge=True)


def list_original_questions(doc_id: str) -> List[Dict[str, Any]]:
    db = get_firestore()
    col = db.collection(DOCS).document(doc_id).collection(SUB_QUESTIONS)
    docs = []
    for d in col.stream():
        if d.id != "_meta":
            data = d.to_dict()
            data["id"] = d.id  # Document ID is now the 0-based index
            docs.append(data)
    # Sort by document ID (which is the 0-based index as string)
    return sorted(
        docs, key=lambda x: int(x["id"]) if x["id"].isdigit() else float("inf")
    )


def create_generated_exam(
    doc_id: str, gen_id: str, exam_meta: Dict[str, Any], total: int = 0
) -> None:
    db = get_firestore()
    db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id).set(
        {
            "metadata": exam_meta,
            "status": "processing" if total > 0 else "pending",
            "created_at": time.time(),
            "total": total,
            "completed": 0,
        }
    )


def append_generated_question(
    doc_id: str, gen_id: str, question_index: int, el: Dict[str, Any]
) -> None:
    db = get_firestore()
    doc_ref = (
        db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id)
    )
    # Update the pre-created question document using index as ID, no index field needed
    qref = doc_ref.collection(SUB_QUESTIONS).document(str(question_index))
    data = {**el, "status": "done", "updated_at": time.time()}
    qref.set(data, merge=True)


def list_generated_exam(doc_id: str, gen_id: str) -> Dict[str, Any]:
    db = get_firestore()
    base_ref = (
        db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id)
    )
    meta = base_ref.get().to_dict() or {}
    questions = []
    for d in base_ref.collection(SUB_QUESTIONS).stream():
        data = d.to_dict()
        data["id"] = d.id  # Add document ID
        questions.append(data)
    # Sort by document ID (which is the 0-based index as string)
    questions = sorted(
        questions, key=lambda x: int(x["id"]) if x["id"].isdigit() else float("inf")
    )

    # Include timestamps in metadata for frontend compatibility
    metadata = meta.get("metadata", {})
    if "created_at" in meta:
        metadata["created_at"] = meta["created_at"]
    if "updated_at" in meta:
        metadata["updated_at"] = meta["updated_at"]

    return {
        "metadata": metadata,
        "status": meta.get("status", "pending"),
        "total": meta.get("total", 0),
        "completed": meta.get("completed", 0),
        "elements": questions,
    }


def set_generated_exam_status(doc_id: str, gen_id: str, status: str) -> None:
    db = get_firestore()
    db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id).set(
        {"status": status, "updated_at": time.time()}, merge=True
    )


def increment_generated_exam_progress(doc_id: str, gen_id: str) -> Dict[str, Any]:
    db = get_firestore()
    ref = (
        db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id)
    )
    ref.set({"completed": Increment(1), "updated_at": time.time()}, merge=True)
    snap = ref.get().to_dict() or {}
    # Auto-finish when completed >= total
    if snap.get("total") and snap.get("completed", 0) >= snap.get("total"):
        ref.set({"status": "done", "updated_at": time.time()}, merge=True)
    return snap


def init_generated_exam_questions(
    doc_id: str, gen_id: str, selected_questions: List[Dict[str, Any]]
) -> None:
    db = get_firestore()
    base = (
        db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id)
    )
    batch = db.batch()
    now = time.time()

    for i, original_question in enumerate(selected_questions):
        # Use increasing index as document ID (0, 1, 2, ...), no index field needed
        qref = base.collection(SUB_QUESTIONS).document(str(i))
        batch.set(
            qref,
            {
                "original_id": original_question.get(
                    "id"
                ),  # Reference to original question
                "status": "pending",
                "created_at": now,
            },
            merge=True,
        )
    batch.commit()


def set_generated_question_status(
    doc_id: str,
    gen_id: str,
    question_id: str,
    status: str,
    patch: Optional[Dict[str, Any]] = None,
) -> None:
    db = get_firestore()
    qref = (
        db.collection(DOCS)
        .document(doc_id)
        .collection(SUB_GENERATED)
        .document(gen_id)
        .collection(SUB_QUESTIONS)
        .document(question_id)
    )
    data: Dict[str, Any] = {"status": status, "updated_at": time.time()}
    if patch:
        data.update(patch)
    qref.set(data, merge=True)


def list_generated_exams(doc_id: str) -> List[Dict[str, Any]]:
    """List all generated exams for a document"""
    db = get_firestore()
    col = db.collection(DOCS).document(doc_id).collection(SUB_GENERATED)
    exams = []
    for doc in col.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        exams.append(data)
    return sorted(exams, key=lambda x: x.get("created_at", 0), reverse=True)


def delete_document(doc_id: str) -> None:
    """Delete a document and all its subcollections"""
    db = get_firestore()
    doc_ref = db.collection(DOCS).document(doc_id)

    # Delete all generated exams
    for exam_doc in doc_ref.collection(SUB_GENERATED).stream():
        # Delete questions in each exam
        for question_doc in exam_doc.reference.collection(SUB_QUESTIONS).stream():
            question_doc.reference.delete()
        exam_doc.reference.delete()

    # Delete all original questions
    for question_doc in doc_ref.collection(SUB_QUESTIONS).stream():
        question_doc.reference.delete()

    # Delete the main document
    doc_ref.delete()


def delete_generated_exam(doc_id: str, gen_id: str) -> None:
    """Delete a generated exam and all its questions"""
    db = get_firestore()
    exam_ref = (
        db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id)
    )

    # Delete all questions in the exam
    for question_doc in exam_ref.collection(SUB_QUESTIONS).stream():
        question_doc.reference.delete()

    # Delete the exam document
    exam_ref.delete()


def update_ocr_page_result(doc_id: str, page_index: int, markdown_content: str) -> None:
    """Update OCR result for a specific page and check if all pages are complete"""
    db = get_firestore()
    doc_ref = db.collection(DOCS).document(doc_id)

    try:
        # Get current document to update ocr_pages properly
        doc_data = doc_ref.get().to_dict()
        if not doc_data:
            logger.error("Document %s not found", doc_id)
            return

        # Get current ocr_pages or initialize empty dict
        ocr_pages = doc_data.get("ocr_pages", {})
        ocr_pages[str(page_index)] = markdown_content  # Use string key for consistency

        # Update the document with new ocr_pages and increment counter
        doc_ref.set(
            {
                "ocr_pages": ocr_pages,
                "ocr_completed": Increment(1),
                "updated_at": time.time(),
            },
            merge=True,
        )

        logger.info("Updated OCR result for doc %s, page %d", doc_id, page_index)

        # Check if all pages are complete
        completed = doc_data.get("ocr_completed", 0) + 1  # Add 1 for current update
        total = doc_data.get("ocr_total", 0)
        logger.info("OCR progress for doc %s: %d/%d pages", doc_id, completed, total)

        if completed >= total and total > 0:
            # All OCR pages complete, update status and enqueue extraction
            doc_ref.set({"ocr_status": "done"}, merge=True)
            logger.info(
                "All OCR pages complete for doc %s, enqueuing extraction", doc_id
            )

            from app.workers.queues import enqueue_extract

            enqueue_extract(doc_id)
        else:
            logger.info(
                "OCR still in progress for doc %s: %d/%d", doc_id, completed, total
            )

    except Exception as e:
        logger.exception(
            "Failed to update OCR result for doc %s, page %d: %s", doc_id, page_index, e
        )
        raise


def get_ocr_pages_results(doc_id: str) -> List[str]:
    """Get all OCR page results in order"""
    db = get_firestore()
    doc_data = db.collection(DOCS).document(doc_id).get().to_dict()

    if not doc_data:
        logger.error("Document %s not found", doc_id)
        return []

    if "ocr_pages" not in doc_data:
        logger.error("No ocr_pages field in document %s", doc_id)
        return []

    ocr_pages = doc_data["ocr_pages"]
    total_pages = doc_data.get("ocr_total", 0)

    # Return pages in order
    pages = []
    for i in range(total_pages):
        page_key = str(i)  # Try string key first
        page_content = ocr_pages.get(page_key)

        if page_content is None:
            # Try integer key as fallback
            page_content = ocr_pages.get(i, "% ERROR: Page not found")
            logger.warning(
                "Page %d not found with string key for doc %s, tried int key", i, doc_id
            )

        pages.append(page_content)

    return pages


def cleanup_temp_directory(doc_id: str) -> None:
    """Clean up temporary directory after extraction is complete"""
    db = get_firestore()
    doc_data = db.collection(DOCS).document(doc_id).get().to_dict()

    if not doc_data or "temp_dir" not in doc_data:
        return

    temp_dir = doc_data.get("temp_dir")

    if temp_dir:
        # Delete temporary directory and all contents
        import shutil
        import os

        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info("Cleaned up temp directory: %s", temp_dir)
        except Exception as e:
            logger.warning("Failed to delete temp directory %s: %s", temp_dir, e)

    # Remove temp_dir from document
    db.collection(DOCS).document(doc_id).set({"temp_dir": None}, merge=True)
