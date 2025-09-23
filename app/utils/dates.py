import re
from datetime import datetime, timezone, timedelta

_TZ = timezone(timedelta(hours=-5))
_DOW = r"(?:LUN|MAR|MIE|JUE|VIE|SAB|DOM)"
_MON_MAP = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12
}

_RX_COMPACT = re.compile(rf"(?:(?:{_DOW}),?\s*)?(\d{{1,2}})\s*([A-ZÁ]{3})\s*(\d{{4}})", re.IGNORECASE)
_RX_SLASH = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_RX_TIME = re.compile(r"(\d{1,2}):(\d{2})(?:\s*(a\.?m\.?|p\.?m\.?))?", re.IGNORECASE)

def _parse_time(t: str):
    m = _RX_TIME.search(t or "")
    if not m:
        return None, None
    hh = int(m.group(1))
    mm = int(m.group(2))
    ap = m.group(3).lower() if m.group(3) else None
    if ap:
        if "p" in ap and hh < 12:
            hh += 12
        if "a" in ap and hh == 12:
            hh = 0
    return hh, mm

def _month_from_token(tok: str):
    k = tok.strip().upper().replace("Á", "A")
    return _MON_MAP.get(k)

def parse_spanish_date(text: str):
    m = _RX_COMPACT.search(text or "")
    if m:
        dd = int(m.group(1))
        mon = _month_from_token(m.group(2))
        yyyy = int(m.group(3))
        if mon:
            return dd, mon, yyyy
    m2 = _RX_SLASH.search(text or "")
    if m2:
        dd = int(m2.group(1))
        mm = int(m2.group(2))
        yyyy = int(m2.group(3))
        return dd, mm, yyyy
    return None

def to_iso_lima(date_text: str, time_text: str | None = None):
    d = parse_spanish_date(date_text or "")
    if not d:
        return None
    dd, mm, yyyy = d
    if time_text:
        hh, mi = _parse_time(time_text)
    else:
        hh, mi = _parse_time(date_text)
    if hh is None:
        hh, mi = 0, 0
    try:
        dt = datetime(yyyy, mm, dd, hh, mi, tzinfo=_TZ)
        return dt.isoformat()
    except ValueError:
        return None
