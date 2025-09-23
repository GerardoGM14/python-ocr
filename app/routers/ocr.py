from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import os, time, httpx

from ..database import SessionLocal
from ..config import settings
from ..utils.storage import save_bytes
from ..services.ocr_run import run_ocr
from ..services.parse_ticket import parse_ticket_text
from .. import crud
from .. import schemas

router = APIRouter()

class UrlIn(BaseModel):
    url: str

class IdIn(BaseModel):
    image_id: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _process(image_bytes: bytes, filename: str, content_type: str, db: Session):
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Tipo no válido")
    if len(image_bytes) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")
    t0 = time.perf_counter()
    ocr = run_ocr(image_bytes)
    storage_path = save_bytes(settings.upload_dir, filename, image_bytes)
    doc = crud.create_document(
        db,
        filename=filename,
        content_type=content_type,
        size_bytes=len(image_bytes),
        storage_path=storage_path,
        full_text=ocr.get("full_text"),
        blocks=ocr.get("blocks", []),
    )
    parsed = parse_ticket_text(ocr.get("full_text") or "")
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "document_id": doc.id,
        "ticket_num": parsed.get("ticket_num"),
        "placa": parsed.get("placa"),
        "peso_neto": parsed.get("peso_neto"),
        "ingreso_fecha": parsed.get("ingreso_fecha"),
        "ingreso_hora": parsed.get("ingreso_hora"),
        "salida_fecha": parsed.get("salida_fecha"),
        "salida_hora": parsed.get("salida_hora"),
        "processing_time_ms": elapsed_ms,
        "debug": {
            "best_preset": ocr.get("best_preset"),
            "rotation_deg": ocr.get("rotation_deg"),
            "confidence_mean": ocr.get("confidence_mean"),
            "variant_metrics": ocr.get("variant_metrics"),
        },
    }

@router.post("/ocr")
async def ocr_single(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    return _process(raw, file.filename, file.content_type or "image/unknown", db)

@router.post("/ocr/batch")
async def ocr_batch(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    items = []
    succeeded = 0
    failed = 0
    for f in files:
        try:
            raw = await f.read()
            res = _process(raw, f.filename, f.content_type or "image/unknown", db)
            items.append({"filename": f.filename, "success": True, "result": res})
            succeeded += 1
        except HTTPException as e:
            items.append({"filename": f.filename, "success": False, "error": e.detail})
            failed += 1
        except Exception as e:
            items.append({"filename": f.filename, "success": False, "error": str(e)})
            failed += 1
    return {"items": items, "total": len(items), "succeeded": succeeded, "failed": failed}

@router.post("/ocr/by-url")
async def ocr_by_url(payload: UrlIn, db: Session = Depends(get_db)):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(payload.url, follow_redirects=True)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar")
        ct = r.headers.get("content-type", "")
        raw = r.content
    return _process(raw, os.path.basename(payload.url.split("?")[0]) or "image", ct, db)

@router.post("/ocr/by-id")
async def ocr_by_id(payload: IdIn, db: Session = Depends(get_db)):
    base = settings.upload_dir
    if not base:
        raise HTTPException(status_code=400, detail="Upload deshabilitado")
    safe = payload.image_id.replace("..", "_").replace("\\", "_").replace("/", "_")
    path = os.path.join(base, safe)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No encontrado")
    with open(path, "rb") as f:
        raw = f.read()
    return _process(raw, safe, "image/unknown", db)

@router.get("/documents", response_model=schemas.DocumentListOut)
def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    items, total = crud.list_documents(db, skip=skip, limit=limit)
    return {"items": items, "total": total}

@router.get("/documents/{doc_id}", response_model=schemas.DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = crud.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="No encontrado")
    return doc
