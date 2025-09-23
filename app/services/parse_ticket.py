import re

DOW = r"(?:LUN|LÚN|MAR|MIÉ|MIE|JUE|VIE|SÁB|SAB|DOM)"
MON = r"(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SET|SEP|OCT|NOV|DIC)"

DATE_RX = re.compile(rf"\b{DOW},?\s*\d{{1,2}}\s*{MON}\s*\d{{4}}\b", re.IGNORECASE)
DATE_COMPACT_RX = re.compile(r"^\s*(?:%s,?\s*)?(\d{1,2})([A-Z0-9]{3})(\d{4})\s*$" % DOW, re.IGNORECASE)
DATE_SLASH_RX = re.compile(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$")
TIME_RX = re.compile(
    r"\b(\d{1,2})[:\-\.](\d{2})\b(?:\s*(?:a|p)[^a-zA-Z0-9]{0,2}m\.?)?",
    re.IGNORECASE,
)
TICKET_RX = re.compile(
    r"(?:N|NO|N[°º]|NP|N[P°ºo])?\s*R[ .:]*\s*([0-9]{6,12})",
    re.IGNORECASE,
)

PLACA_RX  = re.compile(r"\b([A-Z]{3}-[A-Z0-9]{3,4})\b")

PESONETO_TAG_RX = re.compile(r"(?i)(peso\s*neto|neto)")
NUMKG_RX = re.compile(r"([0-9]{1,3}(?:[.,\s][0-9]{3})*(?:[.,][0-9]{2})?)\s*(?:kg)?", re.IGNORECASE)

MON_MAP = {"ENE":1,"FEB":2,"MAR":3,"ABR":4,"MAY":5,"JUN":6,"JUL":7,"AGO":8,"SET":9,"SEP":9,"OCT":10,"NOV":11,"DIC":12}

def _first_group(rx, text):
    m = rx.search(text)
    return m.group(1) if m else None

def _fix_month_token(tok: str) -> str | None:
    t = (tok or "").upper()
    t = t.replace("0","O").replace("4","A").replace("6","G")
    # a veces OCR mete puntitos
    t = re.sub(r"[^A-Z]", "", t)
    # normalizar SET/SEP
    if t == "SET": t = "SEP"
    return t if t in MON_MAP else None

def _normalize_date_token(s: str) -> str | None:
    if not s: return None
    s = s.replace(".", "").replace(",", ",")
    if DATE_RX.search(s):
        return DATE_RX.search(s).group(0)
    m = DATE_SLASH_RX.match(s)
    if m:
        dd, mm, yyyy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # construir con mes en texto si quieres, pero devolvemos tal cual
        return f"{dd:02d}/{mm:02d}/{yyyy}"
    m2 = DATE_COMPACT_RX.match(s)
    if m2:
        dd = int(m2.group(1))
        mon = _fix_month_token(m2.group(2))
        yyyy = int(m2.group(3))
        if mon:
            # devolvemos en forma `DIA,DDMESAAAA` si había DOW; si no, solo `DDMESAAAA`
            dow = None
            m_dow = re.match(rf"^\s*({DOW})", s, re.IGNORECASE)
            if m_dow: dow = m_dow.group(1).upper().replace("Í","I").replace("Á","A").replace("Ú","U")
            body = f"{dd:02d}{mon}{yyyy}"
            return f"{dow},{body}" if dow else body
    # último intento: quitar "Fecha:" y espacios, volver a intentar
    t = re.sub(r"(?i)fecha[:\s]*", "", s).strip()
    if t != s:
        return _normalize_date_token(t)
    return None

def _normalize_time_token(s: str) -> str | None:
    if not s:
        return None
    s1 = re.sub(r"(?i)\b([ap])\s*m\b", r"\1m", s)  # "p m" -> "pm", "a m" -> "am"
    s2 = s1.replace("-", ":").replace(".", ":")    # "-" y "." -> ":"

    low = s2.lower().replace(" ", "")
    ampm = ""
    if "pm" in low or "p.m" in low:   # acepta "pm", "p.m", "p m", etc.
        ampm = "p.m"
    elif "am" in low or "a.m" in low:
        ampm = "a.m"

    m = re.search(r"(\d{1,2}):(\d{2})", s2)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return f"{hh:02d}:{mm:02d}" + (f" {ampm}" if ampm else "")



def _time_to_minutes(txt):
    if not txt:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})", txt)
    if not m:
        return None
    hh = int(m.group(1)); mm = int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    low = (txt or "").lower().replace(" ", "")
    if "pm" in low or "p.m" in low:
        if hh < 12:
            hh += 12
    elif "am" in low or "a.m" in low:
        if hh == 12:
            hh = 0
    return hh * 60 + mm


def _scan_block(lines, anchor_pattern, window=16):
    idx = None
    for i, l in enumerate(lines):
        if re.search(anchor_pattern, l):
            idx = i
            break
    if idx is None: return None, None
    date_txt = None; time_txt = None
    for j in range(idx, min(idx + 1 + window, len(lines))):
        lj = lines[j]
        if date_txt is None and (re.search(r"(?i)fecha", lj) or DATE_RX.search(lj) or DATE_SLASH_RX.search(lj) or DATE_COMPACT_RX.search(lj)):
            # “Fecha:” puede estar sola y la fecha en la misma o próxima línea
            date_txt = _normalize_date_token(lj) or _normalize_date_token(lines[j+1] if j + 1 < len(lines) else "")
        if time_txt is None and (re.search(r"(?i)hora", lj) or re.search(TIME_RX, lj)):
            time_txt = _normalize_time_token(lj) or _normalize_time_token(lines[j+1] if j + 1 < len(lines) else "")
        if date_txt and time_txt: break
    return date_txt, time_txt

def _collect_all_dates_times(lines):
    dates = []
    times = []
    for l in lines:
        d = _normalize_date_token(l)
        if d: dates.append(d)
        t = _normalize_time_token(l)
        if t: times.append(t)
    return dates, times

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

    # Ticket: patrón principal y fallback por número suelto en cabecera (evita línea de RUC)
    ticket_num = _first_group(TICKET_RX, text)

    if not ticket_num:
        # Busca un número (6–12 dígitos) en las primeras ~80 líneas, evitando RUC
        for ln in lines[:80]:
            if re.search(r"(?i)\bRUC\b", ln):
                continue
            mnum = re.search(r"(?<!\d)(\d{6,12})(?!\d)", ln)
            if mnum:
                ticket_num = mnum.group(1)
                break

    if not ticket_num:
        # Último intento: primero 6–12 dígitos que no vengan tras "Kg" ni "Neto/Bruto/Tara"
        for ln in lines:
            if re.search(r"(?i)(kg|neto|bruto|tara)", ln):
                continue
            mnum = re.search(r"(?<!\d)(\d{6,12})(?!\d)", ln)
            if mnum:
                ticket_num = mnum.group(1)
                break


    # Placa
    placa = _first_group(PLACA_RX, text)

    # Fechas y horas por bloque (Peso Previo / Último Peso)
    ingreso_fecha, ingreso_hora = _scan_block(lines, r"(?i)peso\s*previo|previo", window=20)
    salida_fecha,  salida_hora  = _scan_block(lines, r"(?i)último\s*peso|ultimo\s*peso", window=20)

    # Fallback: usar todas las fechas/horas visibles y asignar menor→ingreso, mayor→salida
    if not (ingreso_fecha and ingreso_hora) or not (salida_fecha and salida_hora):
        dates, times = _collect_all_dates_times(lines)
        mins = [(t, _time_to_minutes(t)) for t in times if _time_to_minutes(t) is not None]
        mins.sort(key=lambda x: x[1])
        if not ingreso_hora and mins:
            ingreso_hora = mins[0][0]
        if not salida_hora and mins:
            salida_hora = mins[-1][0]
        if dates:
            if not ingreso_fecha:
                ingreso_fecha = dates[0]
            if not salida_fecha:
                salida_fecha = dates[-1] if len(dates) > 1 else dates[0]

    # Si a alguna hora le falta a.m/p.m pero la otra lo tiene, copia el meridiano
    def _meridian(h: str | None) -> str | None:
        if not h:
            return None
        return "a.m" if "a" in h.lower() else ("p.m" if "p" in h.lower() else None)

    in_mer = _meridian(ingreso_hora)
    out_mer = _meridian(salida_hora)
    if ingreso_hora and not in_mer and out_mer:
        ingreso_hora = f"{ingreso_hora} {out_mer}"
    if salida_hora and not out_mer and in_mer:
        salida_hora = f"{salida_hora} {in_mer}"

    # Peso neto
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
        "salida_hora": salida_hora,
    }

