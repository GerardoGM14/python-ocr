from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class OcrBlockOut(BaseModel):
    text: Optional[str]
    confidence: Optional[float]
    bbox: Optional[Any]

    class Config:
        from_attributes = True

class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    storage_path: Optional[str]
    status: str
    full_text: Optional[str]
    created_at: datetime
    blocks: List[OcrBlockOut] = []

    class Config:
        from_attributes = True

class DocumentListOut(BaseModel):
    items: List[DocumentOut]
    total: int

class OcrItemOut(BaseModel):
    filename: str
    success: bool
    error: Optional[str] = None
    document: Optional[DocumentOut] = None

class BatchOut(BaseModel):
    items: List[OcrItemOut]
    total: int
    succeeded: int
    failed: int
