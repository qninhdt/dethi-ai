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
    return sorted(docs, key=lambda x: int(x["id"]) if x["id"].isdigit() else float('inf'))


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


def append_generated_question(doc_id: str, gen_id: str, question_index: int, el: Dict[str, Any]) -> None:
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
    questions = sorted(questions, key=lambda x: int(x["id"]) if x["id"].isdigit() else float('inf'))

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


def init_generated_exam_questions(doc_id: str, gen_id: str, selected_questions: List[Dict[str, Any]]) -> None:
    db = get_firestore()
    base = (
        db.collection(DOCS).document(doc_id).collection(SUB_GENERATED).document(gen_id)
    )
    batch = db.batch()
    now = time.time()
    
    for i, original_question in enumerate(selected_questions):
        # Use increasing index as document ID (0, 1, 2, ...), no index field needed
        qref = base.collection(SUB_QUESTIONS).document(str(i))
        batch.set(qref, {
            "original_id": original_question.get("id"),  # Reference to original question
            "status": "pending", 
            "created_at": now
        }, merge=True)
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
