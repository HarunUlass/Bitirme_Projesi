from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.analysis import Analysis
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/{doc_id}/pdf")
async def download_pdf_report(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current_user.id)
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Doküman bulunamadı")

    analysis_result = await db.execute(select(Analysis).where(Analysis.document_id == doc_id))
    analysis = analysis_result.scalar_one_or_none()
    if not analysis or analysis.status != "completed":
        raise HTTPException(400, "Analiz henüz tamamlanmadı")

    pdf_bytes = ReportService.generate_pdf(doc, analysis, current_user)
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in (doc.original_filename or str(doc_id)))
    safe_name = safe_name.rsplit(".", 1)[0]  # strip original extension
    filename = f"analiz_{safe_name}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
