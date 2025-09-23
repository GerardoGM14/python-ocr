import re

DOW = r"(?:LUN|MAR|MIE|JUE|VIE|SAB|DOM)"
MON = r"(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SET|SEP|OCT|NOV|DIC)"

DATE_RX = re.compile(rf"\b{DOW},?\s*\d{{1,2}}\s*{MON}\s*\d{{4}}\b", re.IGNORECASE)
TIME_RX = re.compile(r"\b(\d{1,2}):(\d{2})\s*(a\.?\s*m\.?|p\.?\s*m\.?)?\b", re.IGNORECASE)

TICKET_RX = re.compile(r"(?:N|NO|N[°º])\s*R[:\-]?\s*([0-9]{5,12})", re.IGNORECASE)
PLACA_RX  = re.compile(r"\b([A-Z]{3}-[A-Z0-9]{3,4})\b")

PESONETO_TAG_RX = re.compile(r"(?i)(peso\s*neto|neto)")
NUMKG_RX = re.compile(r"([0-9]{1,3}(?:[.,\s][0-9]{3})*(?:[.,][0-9]{2})?)\s*(?:kg)?", re.IGNORECASE)

def _first_group(rx, text):
    m = rx.search(text)
    return m.group(1) if m else None

def _time_to_minutes(t):
    if not t:
        return None
    m = TIME_RX.search(t)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    ap = (m.group(3) or "").lower()
    if "p" in ap and hh < 12:
        hh += 12
    if "a" in ap and hh == 12:
        hh = 0
    return hh * 60 + mm

def _collect_date_time_pairs(lines):
    pairs = []
    for i, l in enumerate(lines):
        for dm in DATE_RX.finditer(l):
            date_txt = dm.group(0)
            tm = TIME_RX.search(l) or (TIME_RX.search(lines[i+1]) if i + 1 < len(lines) else None) or (TIME_RX.search(lines[i+2]) if i + 2 < len(lines) else None)
            time_txt = tm.group(0) if tm else None
            pairs.append({"idx": i, "date": date_txt, "time": time_txt, "minutes": _time_to_minutes(time_txt)})
    return pairs

def _index_of_anchor(lines, pattern):
    for i, l in enumerate(lines):
        if re.search(pattern, l):
            return i
    return None

def _nearest_after_pair(pairs, start_idx):
    for p in pairs:
        if p["idx"] >= start_idx:
            return p
    return None

def _find_peso_neto(lines):
    for i, line in enumerate(lines):
        if PESONETO_TAG_RX.search(line):
            m = NUMKG_RX.search(line)
            if m:
                val = m.group(1).strip()
                return val + (" Kg" if "kg" in line.lower() else " Kg")
            for j in range(i + 1, min(i + 6, len(lines))):
                m2 = NUMKG_RX.search(lines[j])
                if m2:
                    val = m2.group(1).strip()
                    return val + (" Kg" if "kg" in lines[j].lower() else " Kg")
    imp_idx = None
    for i, line in enumerate(lines):
        if re.search(r"(?i)importe", line):
            imp_idx = i
            break
    if imp_idx is not None:
        for j in range(max(0, imp_idx - 8), imp_idx):
            m = NUMKG_RX.search(lines[j])
            if m:
                return m.group(1).strip() + (" Kg" if "kg" in lines[j].lower() else " Kg")
    return None

def parse_ticket_text(full_text: str):
    text = full_text or ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    ticket_num = _first_group(TICKET_RX, text)
    if not ticket_num:
        m_any = re.search(r"(?:N|NO|N[°º])\s*R[:\-]?\s*([0-9\W]{5,})", text, re.IGNORECASE)
        if m_any:
            digits = re.sub(r"\D", "", m_any.group(1))[:12]
            ticket_num = digits if len(digits) >= 5 else None

    placa = _first_group(PLACA_RX, text)

    pairs = _collect_date_time_pairs(lines)
    prev_idx = _index_of_anchor(lines, r"(?i)peso\s*previo|previo")
    ult_idx  = _index_of_anchor(lines, r"(?i)último\s*peso|ultimo\s*peso")

    ingreso_fecha = None
    ingreso_hora = None
    salida_fecha = None
    salida_hora = None

    if prev_idx is not None:
        p = _nearest_after_pair(pairs, prev_idx)
        if p:
            ingreso_fecha = p["date"]
            ingreso_hora = p["time"]

    if ult_idx is not None:
        p = _nearest_after_pair(pairs, ult_idx)
        if p:
            salida_fecha = p["date"]
            salida_hora = p["time"]

    if not ingreso_hora or not salida_hora:
        if pairs:
            mins = [p for p in pairs if p["minutes"] is not None]
            if mins:
                mins.sort(key=lambda x: x["minutes"])
                if not ingreso_hora:
                    ingreso_fecha = ingreso_fecha or mins[0]["date"]
                    ingreso_hora = mins[0]["time"]
                if not salida_hora:
                    salida_fecha = salida_fecha or mins[-1]["date"]
                    salida_hora = mins[-1]["time"]
            else:
                if not ingreso_fecha:
                    ingreso_fecha = pairs[0]["date"]
                    ingreso_hora = pairs[0]["time"]
                if not salida_fecha:
                    salida_fecha = pairs[-1]["date"]
                    salida_hora = pairs[-1]["time"]

    peso_neto = _find_peso_neto(lines)
    if peso_neto and not peso_neto.lower().endswith("kg"):
        peso_neto = peso_neto.strip() + " Kg"

    return {
        "ticket_num": ticket_num,
        "placa": placa,
        "peso_neto": peso_neto,
        "ingreso_fecha": ingreso_fecha,
        "ingreso_hora": ingreso_hora,
        "salida_fecha": salida_fecha,
        "salida_hora": salida_hora
    }
