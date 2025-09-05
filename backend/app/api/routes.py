import io
import logging
import os
import time
import uuid
import tempfile
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile

from app.core.firebase import firebase_user
from app.schemas.document import (
    DocumentCreate,
    ExportFormat,
    GenerateRequest,
    SelectQuestionsRequest,
)
from app.services.export_service import (
    build_markdown_from_exam,
    compile_pdf,
    compile_docx,
)
from app.services.firestore_service import (
    create_document,
    get_document,
    list_user_documents,
    list_generated_exam,
    list_generated_exams,
    list_original_questions,
    create_generated_exam,
    init_generated_exam_questions,
    delete_document,
    delete_generated_exam,
)
from app.services.storage_service import upload_file
from app.workers.queues import enqueue_generate_questions, enqueue_ocr

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_documents(user=Depends(firebase_user)):
    """List all documents for the authenticated user"""
    documents = list_user_documents(user["uid"])
    return {"documents": documents}


@router.post("")
async def upload_document(file: UploadFile = File(...), user=Depends(firebase_user)):
    content = await file.read()
    doc_id = str(uuid.uuid4())
    storage_path = f"documents/{user['uid']}/{doc_id}/{file.filename}"
    tmp_path = f"/tmp/{doc_id}_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(content)
    upload_file(tmp_path, storage_path, file.content_type or "application/octet-stream")
    os.remove(tmp_path)
    create_document(
        doc_id,
        {
            "id": doc_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "storage_path": storage_path,
            "created_by": user["uid"],
            "ocr_status": "pending",
            "extract_status": "pending",
        },
    )
    job_id = enqueue_ocr(doc_id, storage_path)
    return {"id": doc_id, "job_id": job_id}


@router.get("/{doc_id}")
def get_doc(doc_id: str, user=Depends(firebase_user)):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    return doc


@router.get("/{doc_id}/questions")
def get_extracted_questions(doc_id: str, user=Depends(firebase_user)):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    return {"questions": list_original_questions(doc_id)}


@router.post("/{doc_id}/generate")
def start_generation(doc_id: str, body: GenerateRequest, user=Depends(firebase_user)):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    base = list_original_questions(doc_id)
    id_set = set(body.selected_ids)
    selected = [q for q in base if q.get("id") in id_set]
    if not selected:
        raise HTTPException(400, "No valid questions selected")
    gen_id = str(uuid.uuid4())
    total = min(len(selected), body.target_count)
    create_generated_exam(
        doc_id, gen_id, {"title": f"Generated Exam {gen_id}"}, total=total
    )
    # Initialize question placeholders with status=pending so UI can display immediately
    init_generated_exam_questions(doc_id, gen_id, selected[:total])
    job_ids = enqueue_generate_questions(doc_id, gen_id, selected, body.target_count)
    return {"generated_exam_id": gen_id, "job_ids": job_ids, "total": total}


@router.get("/{doc_id}/exams/{gen_id}")
def get_generated_exam(doc_id: str, gen_id: str, user=Depends(firebase_user)):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    return list_generated_exam(doc_id, gen_id)


@router.get("/{doc_id}/exams/{gen_id}/export")
def export_exam(
    doc_id: str, gen_id: str, format: str = "markdown", user=Depends(firebase_user)
):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    exam = list_generated_exam(doc_id, gen_id)
    markdown = build_markdown_from_exam(exam)
    if format == "markdown":
        return Response(content=markdown, media_type="text/markdown")
    elif format == "pdf":
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, f"{gen_id}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            pdf_path = compile_pdf(md_path)
            with open(pdf_path, "rb") as f:
                data = f.read()
            headers = {"Content-Disposition": f"attachment; filename={gen_id}.pdf"}
            return Response(content=data, media_type="application/pdf", headers=headers)
    elif format == "docx":
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, f"{gen_id}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            docx_path = compile_docx(md_path)
            with open(docx_path, "rb") as f:
                data = f.read()
            headers = {"Content-Disposition": f"attachment; filename={gen_id}.docx"}
            return Response(
                content=data,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers=headers,
            )
    else:
        raise HTTPException(400, "Unsupported format")


@router.get("/{doc_id}/exams")
def list_document_exams(doc_id: str, user=Depends(firebase_user)):
    """List all generated exams for a document"""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    exams = list_generated_exams(doc_id)
    return {"exams": exams}


@router.delete("/{doc_id}")
def delete_doc(doc_id: str, user=Depends(firebase_user)):
    """Delete a document and all its data"""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    delete_document(doc_id)
    return {"message": "Document deleted successfully"}


@router.delete("/{doc_id}/exams/{gen_id}")
def delete_exam(doc_id: str, gen_id: str, user=Depends(firebase_user)):
    """Delete a generated exam"""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.get("created_by") != user["uid"]:
        raise HTTPException(403, "Forbidden")
    delete_generated_exam(doc_id, gen_id)
    return {"message": "Generated exam deleted successfully"}
