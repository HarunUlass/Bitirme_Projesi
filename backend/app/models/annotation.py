from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    annotation_type = Column(String, default="note")  # note | highlight | flag
    color = Column(String, default="#FFEB3B")
    position = Column(JSON)   # {"x": ..., "y": ..., "width": ..., "height": ...}
    selected_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    document = relationship("Document", back_populates="annotations")
    user = relationship("User", back_populates="annotations")
