from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, default=0)
    file_type = Column(String)  # pdf | docx | doc
    status = Column(String, default="uploaded")  # uploaded | processing | analyzed | error
    extracted_text = Column(String)
    page_count = Column(Integer, default=0)
    is_reference = Column(Boolean, default=False)  # Admin tarafından eklenen referans sözleşme
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="documents")
    analysis = relationship("Analysis", back_populates="document", uselist=False, cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="document", cascade="all, delete-orphan")
