import asyncio
import sys
import os

_ai_module_path = os.environ.get(
    "AI_MODULE_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", "ai-module")),
)
if _ai_module_path not in sys.path:
    sys.path.insert(0, _ai_module_path)

from app.core.database import AsyncSessionLocal
from app.models.document import Document
from sqlalchemy import select


class DocumentService:
    @staticmethod
    async def extract_text(doc_id: int, file_path: str, ext: str):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            try:
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None, _extract_text_sync, file_path, ext
                )
                doc.extracted_text = text
                doc.status = "text_extracted"
                doc.page_count = _count_pages(file_path, ext)
            except Exception as e:
                doc.status = "error"
                doc.extracted_text = f"Hata: {str(e)}"

            await db.commit()

    @staticmethod
    async def extract_and_index_reference(doc_id: int, file_path: str, ext: str):
        """Referans sözleşmeyi çıkar ve RAG vektör deposuna ekle."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            try:
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(None, _extract_text_sync, file_path, ext)
                doc.extracted_text = text
                doc.status = "text_extracted"
                doc.page_count = _count_pages(file_path, ext)
                await db.commit()

                await loop.run_in_executor(
                    None,
                    _index_reference_sync,
                    str(doc_id),
                    text,
                    doc.original_filename,
                )
                doc.status = "indexed"
                await db.commit()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    "Referans sözleşme işleme hatası (doc %s): %s", doc_id, e
                )
                doc.status = "error"
                doc.error_message = str(e)[:500] if hasattr(doc, "error_message") else None
                await db.commit()


def _extract_text_sync(file_path: str, ext: str) -> str:
    from ocr.ocr_processor import OCRProcessor
    processor = OCRProcessor()
    return processor.extract(file_path, ext)


def _count_pages(file_path: str, ext: str) -> int:
    try:
        if ext == ".pdf":
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        return 1
    except Exception:
        return 1


def _index_reference_sync(doc_id: str, text: str, filename: str):
    import time
    import logging

    logger = logging.getLogger(__name__)

    from rag.pipeline import RAGPipeline
    from gemini.client import GeminiClient
    from gemini.prompts import QUICK_SUMMARY_PROMPT

    # 1) Özet üret — rate limit retry ile
    summary = None
    client = GeminiClient.get()
    for attempt in range(5):
        try:
            prompt = QUICK_SUMMARY_PROMPT.format(text=text[:8000])
            summary = client.generate(prompt).strip()
            break
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                wait = 10 * (2 ** attempt)  # 10, 20, 40, 80, 160 sn
                logger.warning(
                    "Özet üretme rate limit (doc %s) — %ds bekleniyor (deneme %d/5)...",
                    doc_id, wait, attempt + 1,
                )
                time.sleep(wait)
            else:
                logger.warning("Özet üretilemedi (doc %s): %s", doc_id, e)
                break  # rate limit dışı hata, özetsiz devam et

    # 2) RAG indeksleme — rate limit retry ile
    for attempt in range(5):
        try:
            rag = RAGPipeline()
            rag.add_document(
                doc_id=doc_id,
                text=text,
                metadata={"filename": filename, "type": "reference"},
                summary=summary,
            )
            logger.info("Referans sözleşme indekslendi (doc %s).", doc_id)
            return  # başarılı
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                wait = 10 * (2 ** attempt)  # 10, 20, 40, 80, 160 sn
                logger.warning(
                    "RAG indeksleme rate limit (doc %s) — %ds bekleniyor (deneme %d/5)...",
                    doc_id, wait, attempt + 1,
                )
                time.sleep(wait)
            else:
                logger.error("RAG indeksleme hatası (doc %s): %s", doc_id, e)
                raise  # rate limit dışı hata, yukarı fırlat

    # Tüm denemeler başarısız
    raise RuntimeError(f"Referans sözleşme indekslenemedi (doc {doc_id}) — rate limit aşılamadı.")
