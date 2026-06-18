from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: Optional[str]
    status: str
    page_count: Optional[int] = 0
    is_reference: bool
    created_at: datetime
    has_analysis: bool = False
    file_url: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    size: int


class AnnotationCreate(BaseModel):
    page_number: int = 1
    content: str
    annotation_type: str = "note"
    color: str = "#FFEB3B"
    position: Optional[dict] = None
    selected_text: Optional[str] = None


class AnnotationOut(BaseModel):
    id: int
    page_number: int
    content: str
    annotation_type: str
    color: str
    position: Optional[dict]
    selected_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
