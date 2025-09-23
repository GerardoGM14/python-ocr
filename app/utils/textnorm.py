import re

_SPACES_RX = re.compile(r"\s+")
_OCR_FIXES = {
    "O": "0",
    "o": "0",
    "I": "1",
    "l": "1",
    "Z": "2",
    "S": "5",
    "B": "8"
}

def normalize_spaces(s: str) -> str:
    return _SPACES_RX.sub(" ", (s or "").strip())

def fix_ocr_digits(s: str) -> str:
    if not s:
        return s
    out = []
    for ch in s:
        out.append(_OCR_FIXES.get(ch, ch))
    return "".join(out)

def standardize_decimal(s: str) -> str:
    if not s:
        return s
    t = s.replace(" ", "")
    t = t.replace(".", "")
    t = t.replace(",", ".")
    return t

def normalize_plate(s: str) -> str:
    if not s:
        return s
    t = normalize_spaces(s).upper()
    t = t.replace(" ", "").replace("_", "-")
    t = re.sub(r"[^A-Z0-9\-]", "", t)
    m = re.search(r"[A-Z]{3}-[A-Z0-9]{3,4}", t)
    return m.group(0) if m else None

def normalize_weight_kg_text(s: str) -> str:
    if not s:
        return s
    m = re.search(r"([0-9]{1,3}(?:[.\s][0-9]{3})*(?:,[0-9]{2})?)\s*kg", s, re.IGNORECASE)
    if not m:
        return None
    num = standardize_decimal(m.group(1))
    return f"{num} Kg"
