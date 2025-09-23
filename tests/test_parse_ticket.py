import re
from app.services.parse_ticket import parse_ticket_text
from app.utils.textnorm import normalize_plate, normalize_weight_kg_text
from app.utils.dates import to_iso_lima

def test_parse_basic_fields():
    sample = """
    EMPRESA X
    N° R: 65836559
    Placa: BZU-890
    Peso Previo
    SAB,23AGO2025 06:53 p. m.
    Último Peso
    SAB,23AGO2025 07:14 p. m.
    Resumen
    Peso Neto 41,510.00 Kg
    Importe S/ 0.00
    """
    parsed = parse_ticket_text(sample)
    assert parsed["ticket_num"] == "65836559"
    assert normalize_plate(parsed["placa"]) == "BZU-890"
    assert normalize_weight_kg_text(parsed["peso_neto"]) == "41510.00 Kg"
    assert parsed["ingreso_fecha"].startswith("SAB,23AGO2025")
    assert parsed["salida_fecha"].startswith("SAB,23AGO2025")
    assert to_iso_lima(parsed["ingreso_fecha"]) is not None
    assert to_iso_lima(parsed["salida_fecha"]) is not None

def test_parse_with_variations_and_noise():
    sample = """
    FF-0035487
    N° R: 006585195
    VEHICULO TEY-830
    Peso   Previo
    JUE,11SEP2025 12:57 p. m.
    Ultimo Peso
    JUE,11SEP2025 01:37 p. m.
    Neto: 35,600.00 kg
    Importe S/ 0.00
    """
    parsed = parse_ticket_text(sample)
    assert re.fullmatch(r"\d{6,9}", parsed["ticket_num"])
    assert normalize_plate(parsed["placa"]) == "TEY-830"
    assert normalize_weight_kg_text(parsed["peso_neto"]) == "35600.00 Kg"
    assert to_iso_lima(parsed["ingreso_fecha"]) is not None
    assert to_iso_lima(parsed["salida_fecha"]) is not None
