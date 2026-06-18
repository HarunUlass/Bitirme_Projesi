"""
Re-index all reference contracts that have extracted_text but status='error'.
Run inside the backend Docker container:
  docker compose exec backend python scripts/reindex_references.py
"""
import asyncio
import sys
import os

# Ensure ai-module is importable
_ai_module_path = os.environ.get(
    "AI_MODULE_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ai-module")),
)
if _ai_module_path not in sys.path:
    sys.path.insert(0, _ai_module_path)

# Make sure app package is importable (script lives inside /app)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import AsyncSessionLocal
from app.models.user import User  # noqa: F401
from app.models.analysis import Analysis  # noqa: F401
from app.models.annotation import Annotation  # noqa: F401
from app.models.document import Document
from sqlalchemy import select


def _index_reference_sync(doc_id: str, text: str, filename: str):
    from rag.pipeline import RAGPipeline
    from gemini.client import GeminiClient
    from gemini.prompts import QUICK_SUMMARY_PROMPT

    summary = None
    try:
        client = GeminiClient.get()
        prompt = QUICK_SUMMARY_PROMPT.format(text=text[:8000])
        summary = client.generate(prompt).strip()
        print(f"  [✓] AI özeti oluşturuldu ({len(summary)} karakter)")
    except Exception as e:
        print(f"  [!] AI özeti oluşturulamadı: {e}")

    rag = RAGPipeline()
    rag.add_document(
        doc_id=doc_id,
        text=text,
        metadata={"filename": filename, "type": "reference"},
        summary=summary,
    )


async def reindex_all():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.is_reference == True,
                Document.extracted_text.isnot(None),
                Document.extracted_text != "",
            )
        )
        docs = result.scalars().all()

    print(f"Toplam {len(docs)} referans sözleşme bulundu.")

    success = 0
    failed = 0

    for doc in docs:
        print(f"\n[{doc.id}] {doc.original_filename} (mevcut durum: {doc.status})")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                _index_reference_sync,
                str(doc.id),
                doc.extracted_text,
                doc.original_filename,
            )
            # Update status to indexed
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Document).where(Document.id == doc.id))
                d = result.scalar_one_or_none()
                if d:
                    d.status = "indexed"
                    await db.commit()
            print(f"  [✓] Başarıyla indekslendi → status=indexed")
            success += 1
        except Exception as e:
            print(f"  [✗] Hata: {e}")
            failed += 1

    print(f"\n--- Sonuç ---")
    print(f"Başarılı: {success}")
    print(f"Başarısız: {failed}")

    # Show final ChromaDB count
    try:
        if _ai_module_path not in sys.path:
            sys.path.insert(0, _ai_module_path)
        from rag.vector_store import VectorStore
        vs = VectorStore()
        print(f"ChromaDB toplam vektör sayısı: {vs.count()}")
    except Exception as e:
        print(f"ChromaDB sayısı alınamadı: {e}")


if __name__ == "__main__":
    asyncio.run(reindex_all())
