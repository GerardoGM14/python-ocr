from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=True)
    status = Column(String(50), default="processed", nullable=False)
    full_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    blocks = relationship("OcrBlock", back_populates="document", cascade="all, delete-orphan")

class OcrBlock(Base):
    __tablename__ = "ocr_blocks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    bbox = Column(Text, nullable=True)
    document = relationship("Document", back_populates="blocks")
