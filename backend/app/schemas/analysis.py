from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class RiskFlag(BaseModel):
    level: str  # critical | warning | info
    title: str
    description: str
    clause: Optional[str] = None
    legal_reference: Optional[str] = None


class SimilarContract(BaseModel):
    doc_id: Optional[int] = None
    filename: str
    score: float
    summary: Optional[str] = None


class Clause(BaseModel):
    title: str
    content: str
    analysis: Optional[str] = None
    risk_level: Optional[str] = None
    legal_reference: Optional[str] = None


class AnalysisOut(BaseModel):
    id: int
    document_id: int
    status: str
    summary: Optional[str] = None
    document_type: Optional[str] = None
    parties: Optional[List[Any]] = None
    key_dates: Optional[List[Any]] = None
    clauses: Optional[List[Any]] = None
    risk_flags: Optional[List[Any]] = None
    similar_contracts: Optional[List[Any]] = None
    compliance_score: Optional[float] = None
    overall_risk_level: Optional[str] = None
    recommendations: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
