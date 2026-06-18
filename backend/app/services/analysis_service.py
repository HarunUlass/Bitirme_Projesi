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
from app.models.analysis import Analysis
from sqlalchemy import select

ANALYSIS_TIMEOUT = 420  # seconds


class AnalysisService:
    @staticmethod
    async def run_analysis(doc_id: int):
        async with AsyncSessionLocal() as db:
            doc_result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = doc_result.scalar_one_or_none()

            analysis_result = await db.execute(select(Analysis).where(Analysis.document_id == doc_id))
            analysis = analysis_result.scalar_one_or_none()

            if not doc or not analysis:
                return

            try:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, _run_full_analysis_sync,
                        doc.extracted_text, doc.original_filename
                    ),
                    timeout=ANALYSIS_TIMEOUT,
                )

                analysis.status = "completed"
                analysis.summary = result.get("summary")
                analysis.document_type = result.get("document_type")
                analysis.parties = result.get("parties", [])
                analysis.key_dates = result.get("key_dates", [])
                analysis.clauses = result.get("clauses", [])
                analysis.risk_flags = result.get("risk_flags", [])
                analysis.similar_contracts = result.get("similar_contracts", [])
                analysis.compliance_score = result.get("compliance_score")
                analysis.overall_risk_level = result.get("overall_risk_level", "low")
                analysis.recommendations = result.get("recommendations", [])

            except asyncio.TimeoutError:
                analysis.status = "error"
                analysis.error_message = f"Analiz zaman aşımına uğradı ({ANALYSIS_TIMEOUT}s). Tekrar deneyin."
            except Exception as e:
                analysis.status = "error"
                analysis.error_message = str(e)

            await db.commit()


def _run_full_analysis_sync(text: str, filename: str) -> dict:
    import os
    from dotenv import load_dotenv
    load_dotenv(override=False)

    from agents.document_agent import DocumentAgent
    agent = DocumentAgent()
    return agent.analyze(text=text, filename=filename)
