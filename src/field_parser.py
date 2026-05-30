from __future__ import annotations

import re
from typing import Iterable

try:
    from document_templates import FIELD_LABELS
    from utils import collapse_whitespace, strip_accents
except ImportError:
    from src.document_templates import FIELD_LABELS
    from src.utils import collapse_whitespace, strip_accents


PATTERN_CNPJ = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")
PATTERN_NCM = re.compile(r"\b\d{8}\b")
PATTERN_CONTAINER = re.compile(r"\b[A-Z]{4}\d{7}\b")
PATTERN_DI = re.compile(r"\b\d{2}/\d{7}-\d\b")
PATTERN_DUIMP = re.compile(r"\bBR\d{12,}\b")
PATTERN_DDI = re.compile(r"\bDDI-\d{4}-\d{6}\b")
PATTERN_CTAC = re.compile(r"\bCTAC-\d{4}-\d{5}\b")
PATTERN_DATE = re.compile(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b")
PATTERN_BL = re.compile(r"\b(?:HBL|MBL|SUDU|MSCU|ONEY|COSU)[A-Z0-9]{5,}\b")
PATTERN_PLATE = re.compile(r"\b[A-Z]{3}\d[A-Z]\d{2}\b")


def preprocess_ocr_text(text: str) -> str:
    normalized = strip_accents(text or "").upper()
    normalized = normalized.replace("\r", "\n")
    normalized = re.sub(r"\n{2,}", "\n", normalized)
    return normalized


def _match_after_labels(text: str, labels: Iterable[str]) -> str | None:
    escaped_labels = [re.escape(strip_accents(label).upper()) for label in labels]
    label_pattern = "|".join(escaped_labels)
    pattern = re.compile(
        rf"(?:{label_pattern})\s*[:\-]\s*(?P<value>[^\n]+)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None
    return collapse_whitespace(match.group("value"))


def _search(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _first_cnpj(text: str) -> str | None:
    matches = PATTERN_CNPJ.findall(text)
    return matches[0] if matches else None


def _extract_document_number(text: str, document_type: str) -> str | None:
    patterns = {
        "DI": PATTERN_DI,
        "DUIMP": PATTERN_DUIMP,
        "DDI": PATTERN_DDI,
        "CTAC": PATTERN_CTAC,
    }
    pattern = patterns.get(document_type.upper())
    if pattern is None:
        return None
    return _search(pattern, text)


def extract_fields(text: str, document_type: str) -> dict[str, str | None]:
    prepared_text = preprocess_ocr_text(text)
    document_type = document_type.upper()
    labels = FIELD_LABELS.get(document_type, {})

    base_fields: dict[str, str | None] = {}

    if document_type == "DI":
        base_fields = {
            "numero_di": _extract_document_number(prepared_text, "DI"),
            "data_registro": _match_after_labels(prepared_text, [labels["data_registro"]]) or _search(PATTERN_DATE, prepared_text),
            "cnpj_importador": _match_after_labels(prepared_text, [labels["cnpj_importador"]]) or _first_cnpj(prepared_text),
            "nome_importador": _match_after_labels(prepared_text, [labels["nome_importador"]]),
            "ncm": _match_after_labels(prepared_text, [labels["ncm"]]) or _search(PATTERN_NCM, prepared_text),
            "descricao_mercadoria": _match_after_labels(prepared_text, [labels["descricao_mercadoria"]]),
            "peso_bruto_kg": _match_after_labels(prepared_text, [labels["peso_bruto_kg"]]),
            "valor_aduaneiro_usd": _match_after_labels(prepared_text, [labels["valor_aduaneiro_usd"]]),
            "numero_bl": _match_after_labels(prepared_text, [labels["numero_bl"]]) or _search(PATTERN_BL, prepared_text),
            "container": _match_after_labels(prepared_text, [labels["container"]]) or _search(PATTERN_CONTAINER, prepared_text),
            "recinto_alfandegado": _match_after_labels(prepared_text, [labels["recinto_alfandegado"]]),
            "pais_origem": _match_after_labels(prepared_text, [labels["pais_origem"]]),
        }
    elif document_type == "DUIMP":
        base_fields = {
            "numero_duimp": _extract_document_number(prepared_text, "DUIMP"),
            "data_registro": _match_after_labels(prepared_text, [labels["data_registro"]]) or _search(PATTERN_DATE, prepared_text),
            "cnpj_importador": _match_after_labels(prepared_text, [labels["cnpj_importador"]]) or _first_cnpj(prepared_text),
            "nome_importador": _match_after_labels(prepared_text, [labels["nome_importador"]]),
            "ncm": _match_after_labels(prepared_text, [labels["ncm"]]) or _search(PATTERN_NCM, prepared_text),
            "descricao_item": _match_after_labels(prepared_text, [labels["descricao_item"]]),
            "peso_liquido_kg": _match_after_labels(prepared_text, [labels["peso_liquido_kg"]]),
            "valor_aduaneiro_usd": _match_after_labels(prepared_text, [labels["valor_aduaneiro_usd"]]),
            "numero_bl": _match_after_labels(prepared_text, [labels["numero_bl"]]) or _search(PATTERN_BL, prepared_text),
            "container": _match_after_labels(prepared_text, [labels["container"]]) or _search(PATTERN_CONTAINER, prepared_text),
            "unidade_despacho": _match_after_labels(prepared_text, [labels["unidade_despacho"]]),
            "pais_aquisicao": _match_after_labels(prepared_text, [labels["pais_aquisicao"]]),
        }
    elif document_type == "DDI":
        base_fields = {
            "numero_ddi": _extract_document_number(prepared_text, "DDI"),
            "data_emissao": _match_after_labels(prepared_text, [labels["data_emissao"]]) or _search(PATTERN_DATE, prepared_text),
            "cnpj_declarante": _match_after_labels(prepared_text, [labels["cnpj_declarante"]]) or _first_cnpj(prepared_text),
            "nome_declarante": _match_after_labels(prepared_text, [labels["nome_declarante"]]),
            "numero_di_referenciada": _match_after_labels(prepared_text, [labels["numero_di_referenciada"]]) or _search(PATTERN_DI, prepared_text),
            "recinto": _match_after_labels(prepared_text, [labels["recinto"]]),
            "container": _match_after_labels(prepared_text, [labels["container"]]) or _search(PATTERN_CONTAINER, prepared_text),
            "peso_manifestado_kg": _match_after_labels(prepared_text, [labels["peso_manifestado_kg"]]),
            "situacao_documental": _match_after_labels(prepared_text, [labels["situacao_documental"]]),
        }
    elif document_type == "CTAC":
        base_fields = {
            "numero_ctac": _extract_document_number(prepared_text, "CTAC"),
            "data_emissao": _match_after_labels(prepared_text, [labels["data_emissao"]]) or _search(PATTERN_DATE, prepared_text),
            "transportador": _match_after_labels(prepared_text, [labels["transportador"]]),
            "cnpj_transportador": _match_after_labels(prepared_text, [labels["cnpj_transportador"]]) or _first_cnpj(prepared_text),
            "placa_cavalo": _match_after_labels(prepared_text, [labels["placa_cavalo"]]) or _search(PATTERN_PLATE, prepared_text),
            "placa_carreta": _match_after_labels(prepared_text, [labels["placa_carreta"]]),
            "container": _match_after_labels(prepared_text, [labels["container"]]) or _search(PATTERN_CONTAINER, prepared_text),
            "peso_bruto_kg": _match_after_labels(prepared_text, [labels["peso_bruto_kg"]]),
            "origem": _match_after_labels(prepared_text, [labels["origem"]]),
            "destino": _match_after_labels(prepared_text, [labels["destino"]]),
            "motorista": _match_after_labels(prepared_text, [labels["motorista"]]),
        }

    return base_fields
