from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    filename: str
    content_type: str
    size: int


class Document(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    storage_path: str
    ocr_status: str = Field(default="pending")
    extract_status: str = Field(default="pending")
    created_by: str
    created_at: float


class SelectQuestionsRequest(BaseModel):
    selected_ids: List[str] = Field(
        ..., description="IDs of original questions to base generation on"
    )


class GenerateRequest(BaseModel):
    selected_ids: List[str]
    target_count: int
    difficulty: Optional[str] = None


class ExportFormat(BaseModel):
    format: str  # markdown, pdf, or docx
