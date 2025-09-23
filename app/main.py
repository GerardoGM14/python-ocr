from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .routers.ocr import router as ocr_router

app = FastAPI(title="OCR API (EasyOCR)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(ocr_router)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env, "port": settings.port, "version": "1.0.0"}
