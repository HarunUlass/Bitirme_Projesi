import sys
import os
import logging

# ai-module'ü Python path'e ekle
_ai_module_path = os.environ.get(
    "AI_MODULE_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "ai-module")),
)
if _ai_module_path not in sys.path:
    sys.path.insert(0, _ai_module_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Zararsız ama gürültülü logları kapat
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
logging.getLogger("onnxruntime").setLevel(logging.CRITICAL)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, documents, analysis, reports, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _create_default_admin()
    await _reset_stuck_analyses()
    # Arka planda: daha önce indekslenmiş TTK varsa otomatik yükle
    import asyncio
    asyncio.create_task(_auto_restore_ttk())
    yield


async def _auto_restore_ttk():
    """ChromaDB'de TTK verisi varsa PDF'i belleğe yükle ve indexed olarak işaretle."""
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _auto_restore_ttk_sync)


def _auto_restore_ttk_sync():
    """Önceki indeksleme verisini kontrol et; varsa PDF'i yükleyip _indexed=True yap."""
    logger = logging.getLogger(__name__)

    try:
        from rag.vector_store import VectorStore

        store = VectorStore(collection_name="ttk_articles")
        count = store.count()

        if count == 0:
            logger.info("ChromaDB'de TTK verisi yok — admin panelden manuel başlatılabilir.")
            return

        logger.info("ChromaDB'de %d TTK maddesi bulundu, PDF belleğe yükleniyor...", count)

        from legal_knowledge_base import LegalKnowledgeBase

        kb = LegalKnowledgeBase.get()
        pdf_path = os.getenv("LEGAL_REFERENCE_PDF", settings.LEGAL_REFERENCE_PDF)

        if not os.path.isabs(pdf_path):
            _this_dir = os.path.dirname(os.path.abspath(__file__))
            pdf_path = os.path.normpath(os.path.join(_this_dir, pdf_path))

        kb.load_pdf(pdf_path)

        if kb.is_loaded():
            kb._indexed = True
            logger.info(
                "TTK otomatik yüklendi — %d madde bellekte, %d madde ChromaDB'de hazır.",
                kb.get_article_count(), count,
            )
        else:
            logger.warning("TTK PDF otomatik yüklenemedi, admin panelden manuel yükleme gerekli.")
    except Exception as e:
        logger.error("TTK otomatik yükleme hatası: %s", e)


async def _reset_stuck_analyses():
    """Sunucu yeniden başlarken yarım kalan analizleri hata olarak işaretle."""
    from app.core.database import AsyncSessionLocal
    from app.models.analysis import Analysis
    from sqlalchemy import update

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Analysis)
            .where(Analysis.status.in_(["running", "pending"]))
            .values(status="error", error_message="Sunucu yeniden başlatıldı, analizi tekrar çalıştırın")
        )
        await db.commit()


async def _create_default_admin():
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@legaldoc.com"))
        if not result.scalar_one_or_none():
            admin_user = User(
                email="admin@legaldoc.com",
                hashed_password=get_password_hash("Admin123!"),
                full_name="Admin",
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            await db.commit()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
