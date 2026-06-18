from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    status = Column(String, default="pending")  # pending | running | completed | error

    summary = Column(Text)
    document_type = Column(String)
    parties = Column(JSON)        # [{"role": "...", "name": "..."}]
    key_dates = Column(JSON)      # [{"label": "...", "date": "..."}]
    clauses = Column(JSON)        # [{"title": "...", "content": "...", "analysis": "..."}]
    risk_flags = Column(JSON)     # [{"level": "critical|warning|info", "title": "...", "description": "...", "clause": "...", "legal_reference": "..."}]
    similar_contracts = Column(JSON)  # [{"doc_id": ..., "filename": ..., "score": ..., "summary": ...}]
    compliance_score = Column(Float)
    overall_risk_level = Column(String)  # low | medium | high | critical
    recommendations = Column(JSON)  # ["..."]
    raw_gemini_response = Column(Text)
    error_message = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    document = relationship("Document", back_populates="analysis")
