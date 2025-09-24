# scripts/hit_api_batch.py
import argparse, json, sys, time
from pathlib import Path
import requests

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

def iter_images(folder: Path, recursive: bool):
    if recursive:
        it = folder.rglob("*")
    else:
        it = folder.glob("*")
    for p in sorted(it):
        if p.is_file() and p.suffix.lower() in EXTS:
            yield p

def fmt_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def main():
    ap = argparse.ArgumentParser(
        description="Enviar imágenes al endpoint /ocr de tu API y mostrar el JSON en consola."
    )
    ap.add_argument("--input", required=True, help="Carpeta con imágenes.")
    ap.add_argument("--url", default="http://127.0.0.1:8000/ocr", help="URL del endpoint /ocr.")
    ap.add_argument("--recursive", action="store_true", help="Buscar imágenes en subcarpetas.")
    ap.add_argument("--timeout", type=int, default=240, help="Timeout por imagen (seg).")
    ap.add_argument("--ndjson", help="Archivo NDJSON para guardar resultados (opcional).")
    ap.add_argument("--absolute", action="store_true", help="Imprimir rutas absolutas.")
    args = ap.parse_args()

    folder = Path(args.input)
    if not folder.exists() or not folder.is_dir():
        print(f"[ERROR] Carpeta no válida: {folder}", file=sys.stderr)
        sys.exit(1)

    imgs = list(iter_images(folder, args.recursive))
    if not imgs:
        print(f"[WARN] No se encontraron imágenes en: {folder}")
        sys.exit(0)

    nd = open(args.ndjson, "w", encoding="utf-8") if args.ndjson else None
    session = requests.Session()

    total = len(imgs)
    ok = 0

    print(f"[INFO] Endpoint: {args.url}")
    print(f"[INFO] Imágenes encontradas: {total}")
    print("-" * 80)

    errores_dir = Path(r"C:\Users\Soporte\Downloads\Errores")
    errores_dir.mkdir(parents=True, exist_ok=True)

    for idx, img_path in enumerate(imgs, start=1):
        display_path = str(img_path.resolve() if args.absolute else img_path)
        size = img_path.stat().st_size
        print(f"\n[{idx}/{total}] Archivo: {display_path}  (tamaño: {fmt_bytes(size)})")

        t0 = time.perf_counter()
        try:
            with open(img_path, "rb") as f:
                files = {"file": (img_path.name, f, "image/*")}
                resp = session.post(args.url, files=files, timeout=args.timeout)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            mover_a_errores = False
            if resp.status_code == 200:
                data = resp.json()
                # Verificar si el resultado es null en campos relevantes o si el peso/peso_neto tiene más de 5 dígitos
                if data is None:
                    mover_a_errores = True
                elif isinstance(data, dict):
                    campos_relevantes = ["placa", "ingreso_fecha_hora", "salida_fecha_hora"]
                    for campo in campos_relevantes:
                        if data.get(campo) is None:
                            mover_a_errores = True
                            break
                    peso = data.get("peso")
                    peso_neto = data.get("peso_neto")
                    if peso is not None and len(str(peso)) > 5:
                        mover_a_errores = True
                    elif peso_neto is not None and len(str(peso_neto)) > 5:
                        mover_a_errores = True
                ok += 1
                print(f"[OK] HTTP 200 en {elapsed_ms} ms")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                if nd:
                    nd.write(json.dumps({"file": display_path, "result": data}, ensure_ascii=False) + "\n")
                if mover_a_errores:
                    destino = errores_dir / img_path.name
                    try:
                        img_path.replace(destino)
                        print(f"[MOVIDO] Archivo movido a Errores: {destino}")
                    except Exception as err:
                        print(f"[ERROR] No se pudo mover el archivo: {err}")
            else:
                print(f"[ERROR] HTTP {resp.status_code} en {elapsed_ms} ms")
                try:
                    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
                except Exception:
                    print(resp.text)
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            print(f"[EXCEPTION] en {elapsed_ms} ms -> {e}")

    if nd:
        nd.close()

    print("\n" + "-" * 80)
    print(f"[RESUMEN] {ok}/{total} procesadas con éxito.")

if __name__ == "__main__":
    main()
