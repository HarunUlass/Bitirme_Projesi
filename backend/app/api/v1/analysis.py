from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisOut
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/{doc_id}/start", response_model=AnalysisOut, status_code=202)
async def start_analysis(
    doc_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Tamamlanmış analizi sıfırlayıp yeniden çalıştır"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_doc_or_404(doc_id, current_user.id, db)

    if doc.status not in ("uploaded", "text_extracted"):
        raise HTTPException(400, f"Doküman durumu analiz için uygun değil: {doc.status}")

    existing = await db.execute(select(Analysis).where(Analysis.document_id == doc_id))
    analysis = existing.scalar_one_or_none()

    if analysis and analysis.status == "running":
        raise HTTPException(409, "Analiz zaten devam ediyor")

    # Tamamlanmış analiz varsa; force=True ise sıfırla, değilse olduğu gibi dön
    if analysis and analysis.status == "completed":
        if not force:
            await db.refresh(analysis)
            return analysis
        # force=True: tüm alanları temizle ve yeniden çalıştır
        analysis.summary = None
        analysis.document_type = None
        analysis.parties = None
        analysis.key_dates = None
        analysis.clauses = None
        analysis.risk_flags = None
        analysis.similar_contracts = None
        analysis.compliance_score = None
        analysis.overall_risk_level = None
        analysis.recommendations = None
        analysis.error_message = None

    if not analysis:
        analysis = Analysis(document_id=doc_id, status="pending")
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

    analysis.status = "running"
    analysis.error_message = None
    await db.commit()
    await db.refresh(analysis)

    background_tasks.add_task(AnalysisService.run_analysis, doc_id)

    return analysis


@router.get("/{doc_id}", response_model=AnalysisOut)
async def get_analysis(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_doc_or_404(doc_id, current_user.id, db)
    result = await db.execute(select(Analysis).where(Analysis.document_id == doc_id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analiz bulunamadı")

    # Silinen veya henüz indexlenmemiş referans sözleşmeleri similar_contracts'tan filtrele
    if analysis.similar_contracts:
        similar = analysis.similar_contracts
        if similar:
            # DB'de hâlâ mevcut ve indexed olan referans sözleşme ID'lerini al
            doc_ids = []
            for c in similar:
                try:
                    doc_ids.append(int(c.get("doc_id", 0)))
                except (ValueError, TypeError):
                    pass
            if doc_ids:
                valid_result = await db.execute(
                    select(Document.id).where(
                        Document.id.in_(doc_ids),
                        Document.is_reference == True,
                        Document.status == "indexed",
                    )
                )
                valid_ids = {str(row[0]) for row in valid_result.all()}
                analysis.similar_contracts = [
                    c for c in similar if str(c.get("doc_id", "")) in valid_ids
                ]

    return analysis


@router.delete("/{doc_id}", status_code=204)
async def delete_analysis(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_doc_or_404(doc_id, current_user.id, db)
    result = await db.execute(select(Analysis).where(Analysis.document_id == doc_id))
    analysis = result.scalar_one_or_none()
    if analysis:
        await db.delete(analysis)
        await db.commit()


async def _get_doc_or_404(doc_id: int, user_id: int, db: AsyncSession) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Doküman bulunamadı")
    return doc
