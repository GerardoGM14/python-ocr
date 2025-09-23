from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from . import models

def create_document(db: Session, *, filename: str, content_type: str, size_bytes: int, storage_path: Optional[str], full_text: Optional[str], blocks: List[dict]) -> models.Document:
    doc = models.Document(
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        storage_path=storage_path,
        status="processed",
        full_text=full_text,
    )
    db.add(doc)
    db.flush()
    for b in blocks:
        db.add(models.OcrBlock(
            document_id=doc.id,
            text=b.get("text"),
            confidence=b.get("confidence"),
            bbox=None if b.get("bbox") is None else str(b.get("bbox"))
        ))
    db.commit()
    db.refresh(doc)
    return doc

def get_document(db: Session, doc_id: int) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == doc_id).first()

def list_documents(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[models.Document], int]:
    q = db.query(models.Document).order_by(models.Document.id.desc())
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return items, total
