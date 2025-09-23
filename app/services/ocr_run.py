import time
from typing import List, Tuple, Dict, Any
import numpy as np
import cv2
from .preprocess import build_variants
from .ocr_reader import read_ndarray

def _ensure_rgb(img):
    if img is None:
        return None
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return img

def _mean_conf(blocks):
    vals = [b[2] for b in blocks if b and len(b) == 3]
    if not vals:
        return 0.0
    return float(np.mean(vals))

def _to_blocks(blocks):
    out = []
    for b in blocks:
        bbox, text, conf = b
        out.append({"bbox": bbox, "text": text, "confidence": float(conf)})
    return out

def run_ocr(image_bytes: bytes) -> Dict[str, Any]:
    variants, angle = build_variants(image_bytes)
    best = None
    metrics: List[Tuple[str, float, float]] = []
    results: Dict[str, Any] = {}
    for name, img in variants:
        rgb = _ensure_rgb(img)
        t0 = time.perf_counter()
        ocr_blocks = read_ndarray(rgb)
        dt = (time.perf_counter() - t0) * 1000.0
        conf = _mean_conf(ocr_blocks)
        metrics.append((name, conf, dt))
        if best is None or conf > best[1] or (abs(conf - best[1]) < 1e-9 and dt < best[2]):
            best = (name, conf, dt)
            results = {
                "best_preset": name,
                "rotation_deg": float(angle),
                "confidence_mean": conf,
                "blocks": _to_blocks(ocr_blocks),
                "full_text": "\n".join([b[1] for b in ocr_blocks if b and len(b) == 3]).strip()
            }
    results["variant_metrics"] = [{"preset": n, "confidence_mean": float(c), "time_ms": float(t)} for n, c, t in metrics]
    return results
