# --- bootstrap para que se pueda importar "app" al ejecutar desde scripts/ ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # carpeta del proyecto (..)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -----------------------------------------------------------------------------

# scripts/batch_cli.py
import os, re, json, time, argparse, mimetypes
from typing import List, Dict

# --- importa tus piezas existentes del proyecto ---
from app.database import SessionLocal
from app.config import settings
from app.utils.storage import save_bytes
from app.services.ocr_run import run_ocr
from app.services.parse_ticket import parse_ticket_text
from app import crud

# formateadores que ya usas en tu router
from app.utils.dates import format_ddmmyyyy, format_time_pmam

# -------- helpers de presentación (idénticos a los que te pasé) ----------
def _kg_to_int_str(s: str | None) -> str | None:
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    return str(int(digits)) if digits else None

def _combine_date_time(date_str: str | None, time_str: str | None) -> str | None:
    """
    date_str: 'dd/mm/yyyy'
    time_str: 'HH:MM' ó 'HH:MM a.m/p.m'
    return:  'dd-mm-yyyy HH:MM:00' (24h)
    """
    if not date_str or not time_str:
        return None

    # normaliza fecha a 'dd-mm-yyyy'
    ds = date_str.strip().replace("/", "-")

    # extrae hora y posible am/pm
    m = re.match(r"^\s*(\d{2}):(\d{2})(?:\s*([ap])\.?\s*m\.?)?\s*$", time_str, re.IGNORECASE)
    if not m:
        return None
    hh = int(m.group(1)); mm = int(m.group(2))
    ap = (m.group(3) or "").lower()

    # convierte a 24h si hay am/pm
    if ap == "p" and hh < 12: hh += 12
    if ap == "a" and hh == 12: hh = 0

    return f"{ds} {hh:02d}:{mm:02d}:00"

# -------- core: procesa un archivo exactamente como tu endpoint ----------
def process_file(path: str, db) -> Dict:
    with open(path, "rb") as f:
        raw = f.read()

    # content-type “best effort” por extensión
    ct = mimetypes.guess_type(path)[0] or "image/unknown"

    t0 = time.perf_counter()
    ocr = run_ocr(raw)

    # guarda archivo en tu carpeta de uploads (respetando settings.upload_dir)
    storage_path = save_bytes(settings.upload_dir, os.path.basename(path), raw)

    # guarda registro del documento (igual que el endpoint)
    doc = crud.create_document(
        db,
        filename=os.path.basename(path),
        content_type=ct,
        size_bytes=len(raw),
        storage_path=storage_path,
        full_text=ocr.get("full_text"),
        blocks=ocr.get("blocks", []),
    )

    # parseo
    parsed = parse_ticket_text(ocr.get("full_text") or "")

    # formatos finales (sin cambiar tu extracción)
    peso_fmt = _kg_to_int_str(parsed.get("peso_neto"))
    ingreso_fecha_fmt = format_ddmmyyyy(parsed.get("ingreso_fecha"))
    salida_fecha_fmt  = format_ddmmyyyy(parsed.get("salida_fecha"))
    ingreso_hora_fmt  = format_time_pmam(parsed.get("ingreso_hora"))
    salida_hora_fmt   = format_time_pmam(parsed.get("salida_hora"))

    ingreso_fecha_hora = _combine_date_time(ingreso_fecha_fmt, ingreso_hora_fmt)
    salida_fecha_hora  = _combine_date_time(salida_fecha_fmt,  salida_hora_fmt)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return {
        "document_id": doc.id,
        "ticket_num": parsed.get("ticket_num"),
        "placa": parsed.get("placa"),
        "peso_neto": peso_fmt,  # sin 'Kg'
        "ingreso_fecha_hora": ingreso_fecha_hora,  # 'DD-MM-YYYY HH:MM:00'
        "salida_fecha_hora":  salida_fecha_hora,   # 'DD-MM-YYYY HH:MM:00'
        "processing_time_ms": elapsed_ms,
        "debug": {
            "best_preset": ocr.get("best_preset"),
            "rotation_deg": ocr.get("rotation_deg"),
            "confidence_mean": ocr.get("confidence_mean"),
            "variant_metrics": ocr.get("variant_metrics"),
        },
    }

def find_images(input_dir: str) -> List[str]:
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")
    paths = []
    for root, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith(exts):
                paths.append(os.path.join(root, fn))
    return sorted(paths)

def main():
    parser = argparse.ArgumentParser(description="Batch OCR CLI")
    parser.add_argument("--input", "-i", required=True, help="Carpeta con imágenes")
    parser.add_argument("--output", "-o", help="Archivo JSON de salida (opcional)")
    args = parser.parse_args()

    imgs = find_images(args.input)
    if not imgs:
        print(json.dumps({"items": [], "total": 0}, ensure_ascii=False))
        return

    db = SessionLocal()
    results = []
    try:
        for p in imgs:
            try:
                res = process_file(p, db)
                results.append({"file": p, "success": True, "result": res})
            except Exception as e:
                results.append({"file": p, "success": False, "error": str(e)})
        payload = {"items": results, "total": len(results)}

        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"[OK] Resultados escritos en: {args.output}")
        else:
            # imprime a STDOUT
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    finally:
        db.close()

if __name__ == "__main__":
    main()
