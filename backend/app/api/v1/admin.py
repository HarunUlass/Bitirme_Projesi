import os
import uuid
import threading
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_admin, get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentOut, DocumentListResponse
from app.schemas.user import UserOut
from app.services.document_service import DocumentService

router = APIRouter()

# TTK indeksleme durumunu tutan module-level state
_ttk_state: dict = {
    "is_running": False,
    "indexed": 0,
    "total": 0,
    "skipped": 0,
    "error": None,
    "completed": False,
}
_ttk_lock = threading.Lock()

# TTK PDF belleğe yükleme durumu
_ttk_load_state: dict = {
    "is_running": False,
    "error": None,
    "completed": False,
}
_ttk_load_lock = threading.Lock()


def _update_ttk(**kwargs):
    with _ttk_lock:
        _ttk_state.update(kwargs)


def _update_ttk_load(**kwargs):
    with _ttk_load_lock:
        _ttk_load_state.update(kwargs)


def _run_ttk_indexing():
    import sys
    import os as _os
    from dotenv import load_dotenv
    import logging

    logger = logging.getLogger(__name__)
    load_dotenv(override=False)

    ai_path = _os.environ.get(
        "AI_MODULE_PATH",
        _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "../../../../ai-module")),
    )
    if ai_path not in sys.path:
        sys.path.insert(0, ai_path)

    from legal_knowledge_base import LegalKnowledgeBase

    kb = LegalKnowledgeBase.get()
    if not kb.is_loaded():
        _update_ttk(is_running=False, error="TTK PDF belleğe yüklenmemiş. Sunucuyu yeniden başlatın.")
        return

    kb._indexed = False  # Yeniden indekslemeye izin ver

    def on_progress(indexed: int, total: int, skipped: int):
        _update_ttk(indexed=indexed, total=total, skipped=skipped)

    try:
        kb.index_to_vectorstore(on_progress=on_progress)
        _update_ttk(is_running=False, completed=True)
        logger.info("TTK indeksleme admin panelinden tamamlandı.")
    except Exception as e:
        _update_ttk(is_running=False, error=str(e))
        logger.error("TTK indeksleme hatası: %s", e)


@router.post("/ttk/load", status_code=202)
async def load_ttk_pdf(_: User = Depends(get_current_admin)):
    """TTK PDF'ini belleğe yükle (maddelere ayır)."""
    with _ttk_load_lock:
        if _ttk_load_state["is_running"]:
            raise HTTPException(409, "PDF yükleme zaten devam ediyor.")
        _ttk_load_state.update({
            "is_running": True,
            "error": None,
            "completed": False,
        })

    thread = threading.Thread(target=_run_ttk_load, daemon=True)
    thread.start()
    return {"message": "TTK PDF belleğe yükleme başlatıldı."}


def _run_ttk_load():
    """PDF'i oku ve maddelere ayır (senkron, arka plan thread)."""
    import sys
    import os as _os
    import logging

    logger = logging.getLogger(__name__)

    ai_path = _os.environ.get(
        "AI_MODULE_PATH",
        _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "../../../../ai-module")),
    )
    if ai_path not in sys.path:
        sys.path.insert(0, ai_path)

    from legal_knowledge_base import LegalKnowledgeBase
    from app.core.config import settings

    kb = LegalKnowledgeBase.get()
    pdf_path = _os.getenv("LEGAL_REFERENCE_PDF", settings.LEGAL_REFERENCE_PDF)

    if not _os.path.isabs(pdf_path):
        _this_dir = _os.path.dirname(_os.path.abspath(__file__))
        pdf_path = _os.path.normpath(_os.path.join(_this_dir, pdf_path))

    logger.info("TTK PDF belleğe yükleniyor (admin panel): %s", pdf_path)

    try:
        kb.load_pdf(pdf_path, force=True)
        if kb.is_loaded():
            _update_ttk_load(is_running=False, completed=True, error=None)
            logger.info("TTK PDF belleğe yüklendi — %d madde, %d sayfa.", kb.get_article_count(), kb.get_page_count())
        else:
            _update_ttk_load(is_running=False, error="PDF yüklenemedi — dosya bulunamadı veya okunamadı.")
    except Exception as e:
        _update_ttk_load(is_running=False, error=str(e))
        logger.error("TTK PDF yükleme hatası: %s", e)


@router.get("/ttk/status")
async def get_ttk_status(_: User = Depends(get_current_admin)):
    """TTK bilgi tabanı durumunu döndür."""
    import sys
    import os as _os

    ai_path = _os.environ.get(
        "AI_MODULE_PATH",
        _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "../../../../ai-module")),
    )
    if ai_path not in sys.path:
        sys.path.insert(0, ai_path)

    from legal_knowledge_base import LegalKnowledgeBase
    from rag.vector_store import VectorStore

    kb = LegalKnowledgeBase.get()
    store = VectorStore(collection_name="ttk_articles")

    with _ttk_lock:
        state = dict(_ttk_state)
    with _ttk_load_lock:
        load_state = dict(_ttk_load_state)

    return {
        **state,
        "pdf_loaded": kb.is_loaded(),
        "article_count": kb.get_article_count(),
        "page_count": kb.get_page_count(),
        "db_indexed_count": store.count(),
        "load_state": load_state,
    }


@router.post("/ttk/index", status_code=202)
async def start_ttk_indexing(_: User = Depends(get_current_admin)):
    """TTK indekslemeyi arka planda başlat."""
    with _ttk_lock:
        if _ttk_state["is_running"]:
            raise HTTPException(409, "İndeksleme zaten devam ediyor.")
        _ttk_state.update({
            "is_running": True,
            "indexed": 0,
            "skipped": 0,
            "error": None,
            "completed": False,
        })

    thread = threading.Thread(target=_run_ttk_indexing, daemon=True)
    thread.start()
    return {"message": "TTK indeksleme başlatıldı."}


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/reference-contracts/diagnostics")
async def reference_contracts_diagnostics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Referans sözleşmelerin ChromaDB ve dosya durumunu kontrol et."""
    import sys
    import os as _os

    ai_path = _os.environ.get(
        "AI_MODULE_PATH",
        _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "../../../../ai-module")),
    )
    if ai_path not in sys.path:
        sys.path.insert(0, ai_path)

    from rag.vector_store import VectorStore
    store = VectorStore()  # legal_contracts collection

    # DB'deki tüm referans sözleşmeleri al
    result = await db.execute(
        select(Document).where(Document.is_reference == True)
    )
    docs = result.scalars().all()

    # ChromaDB'deki tüm ID'leri al
    chroma_ids = set()
    try:
        all_data = store.collection.get(include=[])
        chroma_ids = set(all_data["ids"])
    except Exception:
        pass

    items = []
    for doc in docs:
        doc_id = str(doc.id)
        in_chroma = doc_id in chroma_ids
        file_exists = _os.path.exists(doc.file_path) if doc.file_path else False
        items.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status,
            "file_path": doc.file_path,
            "file_exists": file_exists,
            "in_chroma": in_chroma,
            "usable_for_comparison": in_chroma,  # ChromaDB'de varsa karşılaştırma yapılabilir
        })

    return {
        "total_in_db": len(docs),
        "total_in_chroma": len(chroma_ids),
        "chroma_collection": store.collection.name,
        "items": items,
    }


@router.get("/reference-contracts", response_model=DocumentListResponse)
async def list_reference_contracts(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    offset = (page - 1) * size
    result = await db.execute(
        select(Document)
        .where(Document.is_reference == True)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    docs = result.scalars().all()
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.is_reference == True)
    )
    total = count_result.scalar()
    return DocumentListResponse(
        items=[DocumentOut.model_validate(d) for d in docs],
        total=total,
        page=page,
        size=size,
    )


@router.get("/reference-contracts/{doc_id}")
async def get_reference_contract_detail(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Referans sözleşmenin detay bilgilerini döndür (tüm giriş yapmış kullanıcılar erişebilir)."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.is_reference == True)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Referans sözleşme bulunamadı")

    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "extracted_text": doc.extracted_text,
        "file_url": f"/uploads/references/{doc.filename}",
    }


@router.get("/reference-contracts/{doc_id}/download")
async def download_reference_contract(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Referans sözleşmeyi indir (tüm giriş yapmış kullanıcılar erişebilir)."""
    from fastapi.responses import FileResponse
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.is_reference == True)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Referans sözleşme bulunamadı")
    return FileResponse(doc.file_path, filename=doc.original_filename)


@router.post("/reference-contracts", response_model=DocumentOut, status_code=201)
async def upload_reference_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Desteklenmeyen format: {ext}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(400, "Dosya çok büyük")

    filename = f"{uuid.uuid4()}{ext}"
    ref_dir = os.path.join(settings.UPLOAD_DIR, "references")
    os.makedirs(ref_dir, exist_ok=True)
    file_path = os.path.join(ref_dir, filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    doc = Document(
        user_id=admin.id,
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=ext.lstrip("."),
        status="uploaded",
        is_reference=True,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(DocumentService.extract_and_index_reference, doc.id, file_path, ext)

    return DocumentOut.model_validate(doc)


@router.post("/reference-contracts/{doc_id}/retry", response_model=DocumentOut, status_code=202)
async def retry_reference_contract(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Hatalı referans sözleşmeyi yeniden işle (metin çıkar + RAG indeksle)."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.is_reference == True)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Referans sözleşme bulunamadı")

    if doc.status not in ("error", "uploaded", "text_extracted"):
        raise HTTPException(400, f"Yalnızca hatalı veya bekleyen sözleşmeler yeniden işlenebilir (mevcut durum: {doc.status})")

    doc.status = "uploaded"
    doc.extracted_text = None
    doc.page_count = None
    await db.commit()
    await db.refresh(doc)

    ext = f".{doc.file_type}"
    background_tasks.add_task(DocumentService.extract_and_index_reference, doc.id, doc.file_path, ext)

    return DocumentOut.model_validate(doc)


@router.delete("/reference-contracts/{doc_id}", status_code=204)
async def delete_reference_contract(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.is_reference == True)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Referans sözleşme bulunamadı")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    from rag.pipeline import RAGPipeline
    rag = RAGPipeline()
    rag.remove_document(str(doc_id))

    # Mevcut analizlerdeki similar_contracts'tan silinen sözleşmeyi temizle
    from app.models.analysis import Analysis
    analyses_result = await db.execute(select(Analysis).where(Analysis.similar_contracts.isnot(None)))
    for analysis in analyses_result.scalars().all():
        if analysis.similar_contracts:
            filtered = [
                c for c in analysis.similar_contracts
                if str(c.get("doc_id", "")) != str(doc_id)
            ]
            if len(filtered) != len(analysis.similar_contracts):
                analysis.similar_contracts = filtered

    await db.delete(doc)
    await db.commit()
