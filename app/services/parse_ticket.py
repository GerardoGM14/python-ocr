import re

DOW = r"(?:LUN|MAR|MIE|JUE|VIE|SAB|DOM)"
MON = r"(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SET|SEP|OCT|NOV|DIC)"
DATE_RX = re.compile(rf"\b{DOW},?\s*\d{{1,2}}{MON}\d{{4}}\b", re.IGNORECASE)
TICKET_RX = re.compile(r"(?:N[°º]?\s*R[:\-]?\s*)(\d{5,12})", re.IGNORECASE)
PLACA_RX = re.compile(r"\b([A-Z]{3}-[A-Z0-9]{3,4})\b")
PESONETO_TAG_RX = re.compile(r"(?i)(peso\s*neto|neto)")
NUMKG_RX = re.compile(r"([0-9]{1,3}(?:[.\s][0-9]{3})*(?:,[0-9]{2})?)\s*kg", re.IGNORECASE)

def _first_group(rx, text):
    m = rx.search(text)
    return m.group(1) if m else None

def _find_after_anchor(lines, anchor_rx, value_rx):
    for idx, line in enumerate(lines):
        if re.search(anchor_rx, line):
            for j in range(idx + 1, min(idx + 8, len(lines))):
                m = value_rx.search(lines[j])
                if m:
                    return m.group(0)
    return None

def _find_peso_neto(lines):
    for i, line in enumerate(lines):
        if PESONETO_TAG_RX.search(line):
            m = NUMKG_RX.search(line)
            if m:
                return m.group(0)
            for j in range(i + 1, min(i + 4, len(lines))):
                m2 = NUMKG_RX.search(lines[j])
                if m2:
                    return m2.group(0)
    imp_idx = None
    for i, line in enumerate(lines):
        if re.search(r"(?i)importe", line):
            imp_idx = i
            break
    if imp_idx is not None:
        for j in range(max(0, imp_idx - 6), imp_idx):
            m = NUMKG_RX.search(lines[j])
            if m:
                return m.group(0)
    return None

def parse_ticket_text(full_text: str):
    text = full_text or ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    ticket_num = _first_group(TICKET_RX, text)
    placa = _first_group(PLACA_RX, text)

    ingreso_fecha = _find_after_anchor(lines, r"(?i)peso\s*previo", DATE_RX)
    if ingreso_fecha is None:
        ingreso_fecha = _find_after_anchor(lines, r"(?i)previo", DATE_RX)

    salida_fecha = _find_after_anchor(lines, r"(?i)último\s*peso|ultimo\s*peso", DATE_RX)

    peso_neto = _find_peso_neto(lines)

    return {
        "ticket_num": ticket_num,
        "placa": placa,
        "peso_neto": peso_neto,
        "ingreso_fecha": ingreso_fecha,
        "salida_fecha": salida_fecha
    }
