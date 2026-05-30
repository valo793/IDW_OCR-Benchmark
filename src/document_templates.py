from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Union

try:
    from utils import (
        random_bl,
        random_cnpj,
        random_container,
        random_date,
        random_mercosul_plate,
        random_money,
        random_weight,
    )
except ImportError:
    from src.utils import (
        random_bl,
        random_cnpj,
        random_container,
        random_date,
        random_mercosul_plate,
        random_money,
        random_weight,
    )


DOCUMENT_TYPES = ["DI", "DUIMP", "DDI", "CTAC"]
QUALITY_VARIANTS = [
    "clean",
    "low_resolution",
    "blur",
    "heavy_compression",
    "skew_shadow_noise",
]
OCR_ENGINES_TEMPLATE = [
    "Tesseract",
    "EasyOCR",
    "PaddleOCR",
    "Azure_Document_Intelligence",
]

IMPORTER_NAMES = [
    "ALFA COMERCIO INTERNACIONAL LTDA",
    "BRAVO IMPORTADORA DE PECAS LTDA",
    "COSTA AZUL TRADING S A",
    "DELTA LOGISTICA E IMPORTACAO LTDA",
    "NOVA ROTA COMERCIO EXTERIOR LTDA",
    "ATLANTICO SUL INDUSTRIA E COMERCIO LTDA",
]

TRANSPORTER_NAMES = [
    "TRANSPORTES FICTICIOS DO ATLANTICO LTDA",
    "RODOLOG SINTETICA BRASIL LTDA",
    "NOVA VIA CARGAS INTERNACIONAIS LTDA",
]

DRIVER_NAMES = [
    "CARLOS SILVA",
    "JOAO OLIVEIRA",
    "PEDRO SANTOS",
    "MARCOS LIMA",
    "RAFAEL COSTA",
]

COUNTRIES = [
    "CHINA",
    "ALEMANHA",
    "ESTADOS UNIDOS",
    "INDIA",
    "MEXICO",
    "ITALIA",
    "COREIA DO SUL",
]

TERMINALS = [
    "RECINTO ALFANDEGADO MODELO",
    "TERMINAL PORTUARIO SINTETICO 01",
    "PORTO DEMONSTRATIVO LESTE",
    "UNIDADE ADUANEIRA EXPERIMENTAL",
]

MERCHANDISE_DESCRIPTIONS = [
    "PECAS DE MAQUINARIO INDUSTRIAL",
    "COMPONENTES ELETRONICOS DIVERSOS",
    "MATERIAIS PLASTICOS DE ENGENHARIA",
    "EQUIPAMENTOS DE INFORMATICA",
    "INSUMOS QUIMICOS NAO PERIGOSOS",
]

DOCUMENT_STATUSES = [
    "REGULAR",
    "PENDENTE CONFERENCIA",
    "EM ANALISE",
    "LIBERADO",
]

NCM_CODES = [
    "84713012",
    "87089990",
    "39269090",
    "85044040",
    "73181500",
    "94036000",
    "85371090",
    "40169300",
]

FIELD_LABELS = {
    "DI": {
        "numero_di": "Numero DI",
        "data_registro": "Data de Registro",
        "cnpj_importador": "CNPJ Importador",
        "nome_importador": "Nome Importador",
        "ncm": "NCM",
        "descricao_mercadoria": "Descricao da Mercadoria",
        "peso_bruto_kg": "Peso Bruto KG",
        "valor_aduaneiro_usd": "Valor Aduaneiro USD",
        "numero_bl": "Numero BL",
        "container": "Container",
        "recinto_alfandegado": "Recinto Alfandegado",
        "pais_origem": "Pais de Origem",
    },
    "DUIMP": {
        "numero_duimp": "Numero DUIMP",
        "data_registro": "Data de Registro",
        "cnpj_importador": "CNPJ Importador",
        "nome_importador": "Nome Importador",
        "ncm": "NCM",
        "descricao_item": "Descricao do Item",
        "peso_liquido_kg": "Peso Liquido KG",
        "valor_aduaneiro_usd": "Valor Aduaneiro USD",
        "numero_bl": "Numero BL",
        "container": "Container",
        "unidade_despacho": "Unidade de Despacho",
        "pais_aquisicao": "Pais de Aquisicao",
    },
    "DDI": {
        "numero_ddi": "Numero DDI",
        "data_emissao": "Data de Emissao",
        "cnpj_declarante": "CNPJ Declarante",
        "nome_declarante": "Nome Declarante",
        "numero_di_referenciada": "Numero DI Referenciada",
        "recinto": "Recinto",
        "container": "Container",
        "peso_manifestado_kg": "Peso Manifestado KG",
        "situacao_documental": "Situacao Documental",
    },
    "CTAC": {
        "numero_ctac": "Numero CTAC",
        "data_emissao": "Data de Emissao",
        "transportador": "Transportador",
        "cnpj_transportador": "CNPJ Transportador",
        "placa_cavalo": "Placa Cavalo",
        "placa_carreta": "Placa Carreta",
        "container": "Container",
        "peso_bruto_kg": "Peso Bruto KG",
        "origem": "Origem",
        "destino": "Destino",
        "motorista": "Motorista",
    },
}

SECTION_LAYOUT = {
    "DI": [
        ("1. Identificacao", ["numero_di", "data_registro", "recinto_alfandegado"]),
        ("2. Importador", ["nome_importador", "cnpj_importador"]),
        (
            "3. Dados da Carga",
            [
                "ncm",
                "descricao_mercadoria",
                "container",
                "numero_bl",
                "peso_bruto_kg",
                "valor_aduaneiro_usd",
                "pais_origem",
            ],
        ),
    ],
    "DUIMP": [
        ("1. Identificacao", ["numero_duimp", "data_registro", "unidade_despacho"]),
        ("2. Importador", ["nome_importador", "cnpj_importador"]),
        (
            "3. Dados do Item",
            [
                "ncm",
                "descricao_item",
                "container",
                "numero_bl",
                "peso_liquido_kg",
                "valor_aduaneiro_usd",
                "pais_aquisicao",
            ],
        ),
    ],
    "DDI": [
        ("1. Identificacao", ["numero_ddi", "data_emissao"]),
        ("2. Declarante", ["nome_declarante", "cnpj_declarante"]),
        (
            "3. Dados da Declaracao",
            [
                "numero_di_referenciada",
                "recinto",
                "container",
                "peso_manifestado_kg",
                "situacao_documental",
            ],
        ),
    ],
    "CTAC": [
        ("1. Identificacao", ["numero_ctac", "data_emissao"]),
        ("2. Transportador", ["transportador", "cnpj_transportador", "motorista"]),
        (
            "3. Veiculo e Carga",
            [
                "placa_cavalo",
                "placa_carreta",
                "container",
                "peso_bruto_kg",
                "origem",
                "destino",
            ],
        ),
    ],
}


@dataclass
class DIDocument:
    doc_id: str
    numero_di: str
    data_registro: str
    cnpj_importador: str
    nome_importador: str
    ncm: str
    descricao_mercadoria: str
    peso_bruto_kg: str
    valor_aduaneiro_usd: str
    numero_bl: str
    container: str
    recinto_alfandegado: str
    pais_origem: str


@dataclass
class DUIMPDocument:
    doc_id: str
    numero_duimp: str
    data_registro: str
    cnpj_importador: str
    nome_importador: str
    ncm: str
    descricao_item: str
    peso_liquido_kg: str
    valor_aduaneiro_usd: str
    numero_bl: str
    container: str
    unidade_despacho: str
    pais_aquisicao: str


@dataclass
class DDIDocument:
    doc_id: str
    numero_ddi: str
    data_emissao: str
    cnpj_declarante: str
    nome_declarante: str
    numero_di_referenciada: str
    recinto: str
    container: str
    peso_manifestado_kg: str
    situacao_documental: str


@dataclass
class CTACDocument:
    doc_id: str
    numero_ctac: str
    data_emissao: str
    transportador: str
    cnpj_transportador: str
    placa_cavalo: str
    placa_carreta: str
    container: str
    peso_bruto_kg: str
    origem: str
    destino: str
    motorista: str


DocumentRecord = Union[DIDocument, DUIMPDocument, DDIDocument, CTACDocument]


def get_document_type(document: DocumentRecord) -> str:
    if isinstance(document, DIDocument):
        return "DI"
    if isinstance(document, DUIMPDocument):
        return "DUIMP"
    if isinstance(document, DDIDocument):
        return "DDI"
    if isinstance(document, CTACDocument):
        return "CTAC"
    raise TypeError(f"Unsupported document type: {type(document)!r}")


def document_to_dict(document: DocumentRecord, include_doc_id: bool = True) -> dict[str, str]:
    payload = asdict(document)
    if not include_doc_id:
        payload.pop("doc_id", None)
    return {key: str(value) for key, value in payload.items()}


def get_fields_dict(document: DocumentRecord) -> dict[str, str]:
    return document_to_dict(document, include_doc_id=False)


def get_document_number(document: DocumentRecord) -> str:
    for key in ("numero_di", "numero_duimp", "numero_ddi", "numero_ctac"):
        value = getattr(document, key, None)
        if value:
            return str(value)
    return document.doc_id


def get_document_date(document: DocumentRecord) -> str:
    for key in ("data_registro", "data_emissao"):
        value = getattr(document, key, None)
        if value:
            return str(value)
    return ""


def get_render_sections(document: DocumentRecord) -> list[tuple[str, list[tuple[str, str]]]]:
    document_type = get_document_type(document)
    labels = FIELD_LABELS[document_type]
    values = get_fields_dict(document)
    sections: list[tuple[str, list[tuple[str, str]]]] = []

    for section_title, field_names in SECTION_LAYOUT[document_type]:
        rows = [(labels[field_name], values.get(field_name, "")) for field_name in field_names]
        sections.append((section_title, rows))
    return sections


def build_di(sequence: int) -> DIDocument:
    return DIDocument(
        doc_id=f"DI_{sequence:06d}",
        numero_di=f"{random.randint(25, 26)}/{random.randint(1000000, 9999999)}-{random.randint(0, 9)}",
        data_registro=random_date(),
        cnpj_importador=random_cnpj(),
        nome_importador=random.choice(IMPORTER_NAMES),
        ncm=random.choice(NCM_CODES),
        descricao_mercadoria=random.choice(MERCHANDISE_DESCRIPTIONS),
        peso_bruto_kg=random_weight(),
        valor_aduaneiro_usd=random_money(),
        numero_bl=random_bl(),
        container=random_container(),
        recinto_alfandegado=random.choice(TERMINALS),
        pais_origem=random.choice(COUNTRIES),
    )


def build_duimp(sequence: int) -> DUIMPDocument:
    return DUIMPDocument(
        doc_id=f"DUIMP_{sequence:06d}",
        numero_duimp=f"BR{random.randint(25, 26)}{random.randint(1000000000, 9999999999)}",
        data_registro=random_date(),
        cnpj_importador=random_cnpj(),
        nome_importador=random.choice(IMPORTER_NAMES),
        ncm=random.choice(NCM_CODES),
        descricao_item=random.choice(MERCHANDISE_DESCRIPTIONS),
        peso_liquido_kg=random_weight(),
        valor_aduaneiro_usd=random_money(),
        numero_bl=random_bl(),
        container=random_container(),
        unidade_despacho=random.choice(TERMINALS),
        pais_aquisicao=random.choice(COUNTRIES),
    )


def build_ddi(sequence: int) -> DDIDocument:
    return DDIDocument(
        doc_id=f"DDI_{sequence:06d}",
        numero_ddi=f"DDI-{random.randint(2025, 2026)}-{random.randint(100000, 999999)}",
        data_emissao=random_date(),
        cnpj_declarante=random_cnpj(),
        nome_declarante=random.choice(IMPORTER_NAMES),
        numero_di_referenciada=f"{random.randint(25, 26)}/{random.randint(1000000, 9999999)}-{random.randint(0, 9)}",
        recinto=random.choice(TERMINALS),
        container=random_container(),
        peso_manifestado_kg=random_weight(),
        situacao_documental=random.choice(DOCUMENT_STATUSES),
    )


def build_ctac(sequence: int) -> CTACDocument:
    origin = random.choice(TERMINALS)
    destination_pool = [terminal for terminal in TERMINALS if terminal != origin]
    destination = random.choice(destination_pool or TERMINALS)
    return CTACDocument(
        doc_id=f"CTAC_{sequence:06d}",
        numero_ctac=f"CTAC-{random.randint(2025, 2026)}-{random.randint(10000, 99999)}",
        data_emissao=random_date(),
        transportador=random.choice(TRANSPORTER_NAMES),
        cnpj_transportador=random_cnpj(),
        placa_cavalo=random_mercosul_plate(),
        placa_carreta=random_mercosul_plate(),
        container=random_container(),
        peso_bruto_kg=random_weight(),
        origem=origin,
        destino=destination,
        motorista=random.choice(DRIVER_NAMES),
    )


def build_document(document_type: str, sequence: int) -> DocumentRecord:
    builders = {
        "DI": build_di,
        "DUIMP": build_duimp,
        "DDI": build_ddi,
        "CTAC": build_ctac,
    }
    try:
        return builders[document_type.upper()](sequence)
    except KeyError as exc:
        raise ValueError(
            f"Unknown document type '{document_type}'. Expected one of {DOCUMENT_TYPES}."
        ) from exc
