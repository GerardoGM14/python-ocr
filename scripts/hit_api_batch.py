# scripts/hit_api_batch.py
import argparse, json, os, sys
from pathlib import Path
import requests

def iter_images(folder: Path):
    exts = {".jpg",".jpeg",".png",".bmp",".tif",".tiff",".webp"}
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower() in exts and p.is_file():
            yield p

def main():
    ap = argparse.ArgumentParser(description="Enviar imágenes a la API /ocr y mostrar el JSON resultante.")
    ap.add_argument("--input", required=True, help="Carpeta con imágenes")
    ap.add_argument("--url", default="http://127.0.0.1:8000/ocr", help="URL del endpoint /ocr")
    ap.add_argument("--save", help="Ruta de salida para NDJSON (opcional, 1 JSON por línea)")
    args = ap.parse_args()

    folder = Path(args.input)
    if not folder.exists() or not folder.is_dir():
        print(f"[ERROR] Carpeta no válida: {folder}", file=sys.stderr)
        sys.exit(1)

    out_f = open(args.save, "w", encoding="utf-8") if args.save else None
    session = requests.Session()

    total = 0
    ok = 0
    for img_path in iter_images(folder):
        total += 1
        try:
            with open(img_path, "rb") as f:
                files = {"file": (img_path.name, f, "image/*")}
                r = session.post(args.url, files=files, timeout=120)
            if r.status_code == 200:
                data = r.json()
                ok += 1
                # imprime bonito en consola
                print(f"\n=== {img_path.name} ===")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                # guarda NDJSON si se pidió
                if out_f:
                    out_f.write(json.dumps({"file": img_path.name, "result": data}, ensure_ascii=False) + "\n")
            else:
                print(f"\n=== {img_path.name} ===")
                print(f"[ERROR {r.status_code}] {r.text}")
        except Exception as e:
            print(f"\n=== {img_path.name} ===")
            print(f"[EXCEPTION] {e}")

    if out_f:
        out_f.close()

    print(f"\nResumen: {ok}/{total} procesadas con éxito.")

if __name__ == "__main__":
    main()
