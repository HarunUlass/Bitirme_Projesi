import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.annotation import Annotation
from app.schemas.document import DocumentOut, DocumentListResponse, AnnotationCreate, AnnotationOut
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * size
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.analysis))
        .where(Document.user_id == current_user.id, Document.is_reference == False)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    docs = result.scalars().all()
    count_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.user_id == current_user.id, Document.is_reference == False
        )
    )
    total = count_result.scalar()

    items = []
    for d in docs:
        out = DocumentOut.model_validate(d)
        out.has_analysis = d.analysis is not None
        out.file_url = _build_file_url(d)
        items.append(out)

    return DocumentListResponse(items=items, total=total, page=page, size=size)


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Desteklenmeyen format: {ext}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(400, "Dosya çok büyük (max 50MB)")

    filename = f"{uuid.uuid4()}{ext}"
    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    doc = Document(
        user_id=current_user.id,
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=ext.lstrip("."),
        status="uploaded",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(DocumentService.extract_text, doc.id, file_path, ext)

    out = DocumentOut.model_validate(doc)
    out.file_url = _build_file_url(doc)
    return out


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_doc_or_404(doc_id, current_user.id, db, load_analysis=True)
    out = DocumentOut.model_validate(doc)
    out.has_analysis = doc.analysis is not None
    out.file_url = _build_file_url(doc)
    return out


@router.post("/{doc_id}/retry-extraction", response_model=DocumentOut, status_code=202)
async def retry_extraction(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_doc_or_404(doc_id, current_user.id, db)
    if doc.status not in ("error", "uploaded"):
        raise HTTPException(400, "Yalnızca hatalı dokümanlar yeniden işlenebilir")
    doc.status = "uploaded"
    doc.extracted_text = None
    doc.page_count = None
    await db.commit()
    await db.refresh(doc)
    ext = f".{doc.file_type}"
    background_tasks.add_task(DocumentService.extract_text, doc.id, doc.file_path, ext)
    out = DocumentOut.model_validate(doc)
    out.file_url = _build_file_url(doc)
    return out



@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_doc_or_404(doc_id, current_user.id, db)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.delete(doc)
    await db.commit()


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_doc_or_404(doc_id, current_user.id, db)
    return FileResponse(doc.file_path, filename=doc.original_filename)


# -- Annotations --

@router.get("/{doc_id}/annotations", response_model=list[AnnotationOut])
async def list_annotations(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_doc_or_404(doc_id, current_user.id, db)
    result = await db.execute(
        select(Annotation)
        .where(Annotation.document_id == doc_id, Annotation.user_id == current_user.id)
        .order_by(Annotation.created_at)
    )
    return result.scalars().all()


@router.post("/{doc_id}/annotations", response_model=AnnotationOut, status_code=201)
async def create_annotation(
    doc_id: int,
    payload: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_doc_or_404(doc_id, current_user.id, db)
    ann = Annotation(document_id=doc_id, user_id=current_user.id, **payload.model_dump())
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


@router.delete("/{doc_id}/annotations/{ann_id}", status_code=204)
async def delete_annotation(
    doc_id: int,
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Annotation).where(
            Annotation.id == ann_id,
            Annotation.document_id == doc_id,
            Annotation.user_id == current_user.id,
        )
    )
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(404, "Annotation bulunamadı")
    await db.delete(ann)
    await db.commit()


async def _get_doc_or_404(
    doc_id: int,
    user_id: int,
    db: AsyncSession,
    load_analysis: bool = False,
) -> Document:
    q = select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    if load_analysis:
        q = q.options(selectinload(Document.analysis))
    result = await db.execute(q)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Doküman bulunamadı")
    return doc


def _build_file_url(doc: Document) -> str:
    if doc.is_reference:
        return f"/uploads/references/{doc.filename}"
    return f"/uploads/{doc.user_id}/{doc.filename}"
