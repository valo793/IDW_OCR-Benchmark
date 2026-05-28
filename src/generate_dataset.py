"""
Gerador de dataset sintético para benchmark de OCR em documentos de importação.

Gera documentos fake de DI, DUIMP, DDI e CTAC com campos estruturados,
PDFs, imagens limpas, imagens degradadas e arquivos de ground truth.

Uso:
    python src/generate_dataset.py --docs-per-type 20 --output ./dataset
"""

from __future__ import annotations

import argparse
import random
import string
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


DOCUMENT_TYPES = ["DI", "DUIMP", "DDI", "CTAC"]
QUALITY_TYPES = ["clean", "low_resolution", "blur", "heavy_compression", "skew_shadow_noise"]
OCR_ENGINES_TEMPLATE = ["Tesseract", "EasyOCR", "PaddleOCR", "Azure_Document_Intelligence"]

FIELDS = [
    "document_type",
    "document_number",
    "registration_date",
    "importer_name",
    "importer_cnpj",
    "declarant_cnpj",
    "ncm",
    "container_number",
    "gross_weight_kg",
    "bl_number",
    "country_origin",
    "customs_value_brl",
    "port_terminal",
]

IMPORTER_NAMES = [
    "ALFA COMERCIO INTERNACIONAL LTDA",
    "BRAVO IMPORTADORA DE PECAS LTDA",
    "COSTA AZUL TRADING S A",
    "DELTA LOGISTICA E IMPORTACAO LTDA",
    "NOVA ROTA COMERCIO EXTERIOR LTDA",
    "ATLANTICO SUL INDUSTRIA E COMERCIO LTDA",
]

COUNTRIES = ["CHINA", "ALEMANHA", "ESTADOS UNIDOS", "INDIA", "MEXICO", "ITALIA", "COREIA DO SUL"]
TERMINALS = ["TERMINAL PORTUARIO SINTETICO 01", "RECINTO ALFANDEGADO MODELO", "PORTO DEMONSTRATIVO"]
NCM_LIST = ["84713012", "87089990", "39269090", "85044040", "73181500", "94036000", "85371090", "40169300"]


@dataclass
class SyntheticDocument:
    doc_id: str
    document_type: str
    document_number: str
    registration_date: str
    importer_name: str
    importer_cnpj: str
    declarant_cnpj: str
    ncm: str
    container_number: str
    gross_weight_kg: str
    bl_number: str
    country_origin: str
    customs_value_brl: str
    port_terminal: str


def only_digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def format_cnpj(digits: str) -> str:
    digits = digits[:14].zfill(14)
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def random_cnpj() -> str:
    # CNPJ fake apenas para simulação visual. Não valida dígitos verificadores.
    return format_cnpj("".join(random.choices(string.digits, k=14)))


def random_container() -> str:
    # Formato visual ISO: 4 letras + 7 dígitos. Dígito final não é validado.
    owner = "".join(random.choices(string.ascii_uppercase, k=4))
    number = "".join(random.choices(string.digits, k=7))
    return owner + number


def random_bl() -> str:
    prefix = random.choice(["HBL", "MBL", "SUDU", "MSCU", "ONEY", "COSU"])
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=9))
    return f"{prefix}{suffix}"


def random_date() -> str:
    start = date(2025, 1, 1)
    end = date(2026, 5, 1)
    delta_days = (end - start).days
    d = start + timedelta(days=random.randint(0, delta_days))
    return d.strftime("%d/%m/%Y")


def random_money() -> str:
    value = random.uniform(10_000, 950_000)
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def random_weight() -> str:
    value = random.uniform(2_000, 30_000)
    return f"{value:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")


def random_doc_number(document_type: str) -> str:
    if document_type == "DI":
        return f"{random.randint(25, 26)}/{random.randint(1000000, 9999999)}-{random.randint(0, 9)}"
    if document_type == "DUIMP":
        return f"BR{random.randint(25, 26)}{random.randint(1000000000, 9999999999)}"
    if document_type == "DDI":
        return f"DDI-{random.randint(2025, 2026)}-{random.randint(100000, 999999)}"
    if document_type == "CTAC":
        return f"CTAC-{random.randint(2025, 2026)}-{random.randint(10000, 99999)}"
    raise ValueError(f"Tipo de documento desconhecido: {document_type}")


def build_document(document_type: str, sequence: int) -> SyntheticDocument:
    doc_id = f"{document_type.lower()}_{sequence:04d}"
    return SyntheticDocument(
        doc_id=doc_id,
        document_type=document_type,
        document_number=random_doc_number(document_type),
        registration_date=random_date(),
        importer_name=random.choice(IMPORTER_NAMES),
        importer_cnpj=random_cnpj(),
        declarant_cnpj=random_cnpj(),
        ncm=random.choice(NCM_LIST),
        container_number=random_container(),
        gross_weight_kg=random_weight(),
        bl_number=random_bl(),
        country_origin=random.choice(COUNTRIES),
        customs_value_brl=random_money(),
        port_terminal=random.choice(TERMINALS),
    )


def ensure_dirs(output: Path) -> Dict[str, Path]:
    paths = {
        "pdfs": output / "01_pdfs",
        "images_clean": output / "02_images_clean",
        "images_degraded": output / "03_images_degraded",
        "ground_truth": output / "04_ground_truth",
        "benchmark": output / "05_benchmark",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def draw_pdf(doc: SyntheticDocument, pdf_path: Path) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    # Cabeçalho
    c.setFillColor(colors.HexColor("#1F4E78"))
    c.rect(0, height - 34 * mm, width, 34 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(18 * mm, height - 16 * mm, f"DOCUMENTO SINTÉTICO - {doc.document_type}")
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, height - 24 * mm, "Uso exclusivo para benchmark de OCR. Sem valor fiscal, aduaneiro ou operacional.")

    # Tarja
    c.setFillColor(colors.HexColor("#F2F2F2"))
    c.rect(15 * mm, height - 48 * mm, width - 30 * mm, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18 * mm, height - 44 * mm, f"Número do Documento: {doc.document_number}")
    c.drawRightString(width - 18 * mm, height - 44 * mm, f"Registro: {doc.registration_date}")

    sections = [
        ("1. Identificação", [
            ("Tipo do Documento", doc.document_type),
            ("Número do Documento", doc.document_number),
            ("Data de Registro", doc.registration_date),
            ("Recinto / Terminal", doc.port_terminal),
        ]),
        ("2. Importador / Declarante", [
            ("Importador", doc.importer_name),
            ("CNPJ Importador", doc.importer_cnpj),
            ("CNPJ Declarante", doc.declarant_cnpj),
        ]),
        ("3. Dados da Carga", [
            ("NCM", doc.ncm),
            ("Container", doc.container_number),
            ("Peso Bruto KG", doc.gross_weight_kg),
            ("Conhecimento BL", doc.bl_number),
            ("País de Origem", doc.country_origin),
            ("Valor Aduaneiro BRL", doc.customs_value_brl),
        ]),
    ]

    y = height - 62 * mm
    for title, rows in sections:
        c.setFillColor(colors.HexColor("#D9EAF7"))
        c.rect(15 * mm, y - 6 * mm, width - 30 * mm, 8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#1F4E78"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(18 * mm, y - 3.5 * mm, title)
        y -= 13 * mm

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#222222"))
        for label, value in rows:
            c.setStrokeColor(colors.HexColor("#CCCCCC"))
            c.line(18 * mm, y - 2 * mm, width - 18 * mm, y - 2 * mm)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(20 * mm, y, f"{label}:")
            c.setFont("Helvetica", 8.5)
            c.drawString(70 * mm, y, value)
            y -= 8 * mm
        y -= 5 * mm

    # Rodapé / marca d'água textual
    c.setFillColor(colors.HexColor("#999999"))
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 18 * mm, "DOCUMENTO ARTIFICIAL GERADO PARA TESTE DE OCR - NÃO REPRESENTA DOCUMENTO REAL")

    c.save()


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_image(doc: SyntheticDocument, image_path: Path) -> None:
    # A4 aproximado em 150 DPI
    img = Image.new("RGB", (1240, 1754), "white")
    draw = ImageDraw.Draw(img)

    blue = (31, 78, 121)
    light_blue = (217, 234, 247)
    gray = (242, 242, 242)
    dark = (40, 40, 40)

    font_title = get_font(34, bold=True)
    font_subtitle = get_font(18)
    font_section = get_font(22, bold=True)
    font_label = get_font(18, bold=True)
    font_value = get_font(18)
    font_footer = get_font(16)

    draw.rectangle([0, 0, 1240, 190], fill=blue)
    draw.text((90, 55), f"DOCUMENTO SINTÉTICO - {doc.document_type}", fill="white", font=font_title)
    draw.text((90, 110), "Uso exclusivo para benchmark de OCR. Sem valor fiscal, aduaneiro ou operacional.", fill="white", font=font_subtitle)

    draw.rectangle([80, 230, 1160, 285], fill=gray)
    draw.text((100, 247), f"Número do Documento: {doc.document_number}", fill=dark, font=font_label)
    draw.text((840, 247), f"Registro: {doc.registration_date}", fill=dark, font=font_label)

    sections = [
        ("1. Identificação", [
            ("Tipo do Documento", doc.document_type),
            ("Número do Documento", doc.document_number),
            ("Data de Registro", doc.registration_date),
            ("Recinto / Terminal", doc.port_terminal),
        ]),
        ("2. Importador / Declarante", [
            ("Importador", doc.importer_name),
            ("CNPJ Importador", doc.importer_cnpj),
            ("CNPJ Declarante", doc.declarant_cnpj),
        ]),
        ("3. Dados da Carga", [
            ("NCM", doc.ncm),
            ("Container", doc.container_number),
            ("Peso Bruto KG", doc.gross_weight_kg),
            ("Conhecimento BL", doc.bl_number),
            ("País de Origem", doc.country_origin),
            ("Valor Aduaneiro BRL", doc.customs_value_brl),
        ]),
    ]

    y = 350
    for title, rows in sections:
        draw.rectangle([80, y, 1160, y + 42], fill=light_blue)
        draw.text((100, y + 8), title, fill=blue, font=font_section)
        y += 70

        for label, value in rows:
            draw.line([100, y + 26, 1140, y + 26], fill=(205, 205, 205), width=1)
            draw.text((115, y), f"{label}:", fill=dark, font=font_label)
            draw.text((430, y), value, fill=dark, font=font_value)
            y += 48
        y += 30

    draw.text((290, 1660), "DOCUMENTO ARTIFICIAL GERADO PARA TESTE DE OCR - NÃO REPRESENTA DOCUMENTO REAL", fill=(120, 120, 120), font=font_footer)

    img.save(image_path, quality=95)


def add_shadow(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = img.size
    # Sombra diagonal translúcida
    draw.polygon([(0, 0), (width * 0.55, 0), (width * 0.35, height), (0, height)], fill=(0, 0, 0, 35))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def add_noise(img: Image.Image, intensity: int = 18) -> Image.Image:
    pixels = img.load()
    width, height = img.size
    for _ in range(width * height // 35):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        r, g, b = pixels[x, y]
        delta = random.randint(-intensity, intensity)
        pixels[x, y] = (
            max(0, min(255, r + delta)),
            max(0, min(255, g + delta)),
            max(0, min(255, b + delta)),
        )
    return img


def degrade_image(clean_path: Path, output_dir: Path, doc_id: str) -> None:
    img = Image.open(clean_path).convert("RGB")

    # 1. Clean
    img.save(output_dir / f"{doc_id}__clean.png", quality=95)

    # 2. Low resolution
    low = img.resize((620, 877), Image.Resampling.BILINEAR).resize(img.size, Image.Resampling.BILINEAR)
    low.save(output_dir / f"{doc_id}__low_resolution.png", quality=85)

    # 3. Blur
    blur = img.filter(ImageFilter.GaussianBlur(radius=2.2))
    blur.save(output_dir / f"{doc_id}__blur.png", quality=90)

    # 4. Heavy compression
    compressed_path = output_dir / f"{doc_id}__heavy_compression.jpg"
    img.save(compressed_path, format="JPEG", quality=24, optimize=True)

    # 5. Skew + shadow + noise
    skew = img.rotate(random.uniform(-3.5, 3.5), expand=True, fillcolor="white")
    skew = skew.resize(img.size, Image.Resampling.BICUBIC)
    skew = add_shadow(skew)
    skew = add_noise(skew, intensity=22)
    skew = ImageEnhance.Contrast(skew).enhance(0.88)
    skew.save(output_dir / f"{doc_id}__skew_shadow_noise.png", quality=90)


def generate_dataset(docs_per_type: int, output: Path, seed: int) -> None:
    random.seed(seed)
    paths = ensure_dirs(output)

    docs: List[SyntheticDocument] = []
    for document_type in DOCUMENT_TYPES:
        for i in range(1, docs_per_type + 1):
            doc = build_document(document_type, i)
            docs.append(doc)

            pdf_path = paths["pdfs"] / f"{doc.doc_id}.pdf"
            clean_img_path = paths["images_clean"] / f"{doc.doc_id}.png"
            draw_pdf(doc, pdf_path)
            draw_image(doc, clean_img_path)
            degrade_image(clean_img_path, paths["images_degraded"], doc.doc_id)

    # Ground truth formato wide
    df_truth = pd.DataFrame([asdict(doc) for doc in docs])

    # Ground truth formato long, melhor para Power BI / avaliação
    truth_long_rows = []
    for doc in docs:
        values = asdict(doc)
        for field in FIELDS:
            truth_long_rows.append({
                "doc_id": doc.doc_id,
                "document_type": doc.document_type,
                "field_name": field,
                "expected_value": values[field],
            })
    df_truth_long = pd.DataFrame(truth_long_rows)

    # Template de benchmark: 1 linha por documento, qualidade, OCR e campo
    benchmark_rows = []
    for doc in docs:
        values = asdict(doc)
        for quality in QUALITY_TYPES:
            for engine in OCR_ENGINES_TEMPLATE:
                for field in FIELDS:
                    ext = "jpg" if quality == "heavy_compression" else "png"
                    image_file = f"{doc.doc_id}__{quality}.{ext}"
                    benchmark_rows.append({
                        "doc_id": doc.doc_id,
                        "document_type": doc.document_type,
                        "quality_type": quality,
                        "ocr_engine": engine,
                        "image_file": image_file,
                        "field_name": field,
                        "expected_value": values[field],
                        "extracted_value": "",
                        "confidence_score": "",
                        "processing_time_seconds": "",
                    })
    df_benchmark = pd.DataFrame(benchmark_rows)

    csv_truth = paths["ground_truth"] / "ground_truth_wide.csv"
    csv_truth_long = paths["ground_truth"] / "ground_truth_long.csv"
    xlsx_truth = paths["ground_truth"] / "ground_truth_workbook.xlsx"
    xlsx_benchmark = paths["benchmark"] / "benchmark_template.xlsx"

    df_truth.to_csv(csv_truth, index=False, encoding="utf-8-sig")
    df_truth_long.to_csv(csv_truth_long, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(xlsx_truth, engine="openpyxl") as writer:
        df_truth.to_excel(writer, sheet_name="GroundTruth_Wide", index=False)
        df_truth_long.to_excel(writer, sheet_name="GroundTruth_Long", index=False)

    with pd.ExcelWriter(xlsx_benchmark, engine="openpyxl") as writer:
        df_benchmark.to_excel(writer, sheet_name="Benchmark_Template", index=False)

    print("Dataset sintético gerado com sucesso.")
    print(f"Saída: {output.resolve()}")
    print(f"Documentos base: {len(docs)}")
    print(f"Imagens para OCR: {len(docs) * len(QUALITY_TYPES)}")
    print(f"Template benchmark: {xlsx_benchmark}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gerador de dataset sintético para OCR documental.")
    parser.add_argument("--docs-per-type", type=int, default=20, help="Quantidade de documentos por tipo. Default: 20")
    parser.add_argument("--output", type=str, default="./dataset", help="Diretório de saída. Default: ./dataset")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade. Default: 42")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_dataset(docs_per_type=args.docs_per_type, output=Path(args.output), seed=args.seed)
