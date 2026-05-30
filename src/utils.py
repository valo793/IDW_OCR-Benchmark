from __future__ import annotations

import random
import re
import string
import unicodedata
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import numpy as np


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.upper() == "NAN"


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_generic(value: Any) -> str:
    if is_missing(value):
        return ""
    text = strip_accents(str(value)).upper()
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    return collapse_whitespace(text)


def normalize_identifier(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_generic(value))


def normalize_cnpj(value: Any) -> str:
    if is_missing(value):
        return ""
    return re.sub(r"\D", "", str(value))


def normalize_numeric(value: Any) -> str:
    if is_missing(value):
        return ""

    text = str(value).strip()
    sign = "-" if text.startswith("-") else ""
    text = text.lstrip("-")
    text = re.sub(r"[^0-9,.\-]", "", text)
    if not text:
        return ""

    last_dot = text.rfind(".")
    last_comma = text.rfind(",")
    last_separator = max(last_dot, last_comma)

    if last_separator == -1:
        normalized = re.sub(r"\D", "", text)
    else:
        integer_part = re.sub(r"\D", "", text[:last_separator])
        fractional_part = re.sub(r"\D", "", text[last_separator + 1 :])
        normalized = integer_part
        if fractional_part:
            normalized = f"{integer_part}.{fractional_part}"

    if not normalized:
        return ""

    try:
        decimal_value = Decimal(normalized)
    except InvalidOperation:
        return normalized

    normalized = format(decimal_value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    if normalized == "-0":
        normalized = "0"
    return f"{sign}{normalized}"


def normalize_for_field(field_name: str, value: Any) -> str:
    field_name = field_name.lower()

    if "cnpj" in field_name:
        return normalize_cnpj(value)

    if "data" in field_name:
        return re.sub(r"\D", "", str(value)) if not is_missing(value) else ""

    if (
        field_name.startswith("numero_")
        or field_name in {"container", "ncm", "placa_cavalo", "placa_carreta"}
    ):
        return normalize_identifier(value)

    if field_name.endswith("_kg") or field_name.endswith("_usd") or "peso" in field_name or "valor" in field_name:
        return normalize_numeric(value)

    return normalize_generic(value)


def safe_float(value: Any) -> float:
    normalized = normalize_numeric(value)
    if not normalized:
        return 0.0
    try:
        return float(normalized)
    except ValueError:
        return 0.0


def format_cnpj(digits: str) -> str:
    digits = re.sub(r"\D", "", digits)
    if len(digits) != 14:
        raise ValueError(f"CNPJ must have 14 digits, got {len(digits)}")
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def random_cnpj() -> str:
    digits = "".join(random.choices(string.digits, k=14))
    return format_cnpj(digits)


def random_container() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    numbers = "".join(random.choices(string.digits, k=7))
    return f"{letters}{numbers}"


def random_bl() -> str:
    prefix = random.choice(["HBL", "MBL", "SUDU", "MSCU", "ONEY", "COSU"])
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=9))
    return f"{prefix}{suffix}"


def random_date(start_year: int = 2025, end_year: int = 2026) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    random_day = start + timedelta(days=random.randint(0, (end - start).days))
    return random_day.strftime("%d/%m/%Y")


def format_brazilian_number(value: float, decimals: int) -> str:
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def random_money(min_value: int = 10000, max_value: int = 950000) -> str:
    return format_brazilian_number(random.uniform(min_value, max_value), decimals=2)


def random_weight(min_value: int = 2000, max_value: int = 30000) -> str:
    return format_brazilian_number(random.uniform(min_value, max_value), decimals=3)


def random_mercosul_plate() -> str:
    return (
        "".join(random.choices(string.ascii_uppercase, k=3))
        + str(random.randint(0, 9))
        + random.choice(string.ascii_uppercase)
        + f"{random.randint(0, 99):02d}"
    )
