from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

try:
    from document_templates import (
        DOCUMENT_TYPES,
        DocumentRecord,
        build_document,
        get_document_date,
        get_document_number,
        get_document_type,
        get_render_sections,
    )
    from ground_truth import generate_ground_truth
    from image_degradation import save_quality_variants
    from utils import ensure_dir, seed_everything
except ImportError:
    from src.document_templates import (
        DOCUMENT_TYPES,
        DocumentRecord,
        build_document,
        get_document_date,
        get_document_number,
        get_document_type,
        get_render_sections,
    )
    from src.ground_truth import generate_ground_truth
    from src.image_degradation import save_quality_variants
    from src.utils import ensure_dir, seed_everything


HEADER_COLOR = "#1F4E78"
SECTION_COLOR = "#D9EAF7"
SUBHEADER_COLOR = "#F2F2F2"
TEXT_COLOR = "#222222"
LINE_COLOR = "#D0D7DE"


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def ensure_dataset_dirs(output_dir: Path) -> dict[str, Path]:
    return {
        "root": ensure_dir(output_dir),
        "pdfs": ensure_dir(output_dir / "01_pdfs"),
        "clean_images": ensure_dir(output_dir / "02_images_clean"),
        "degraded_images": ensure_dir(output_dir / "03_images_degraded"),
        "ground_truth": ensure_dir(output_dir / "04_ground_truth"),
        "benchmark": ensure_dir(output_dir / "05_benchmark"),
    }


def render_pdf(document: DocumentRecord, pdf_path: Path) -> None:
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    page_width, page_height = A4

    document_type = get_document_type(document)
    document_number = get_document_number(document)
    document_date = get_document_date(document)

    pdf.setFillColor(colors.HexColor(HEADER_COLOR))
    pdf.rect(0, page_height - 35 * mm, page_width, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(18 * mm, page_height - 16 * mm, f"DOCUMENTO SINTETICO - {document_type}")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        18 * mm,
        page_height - 24 * mm,
        "Uso exclusivo para benchmark de OCR. Sem valor fiscal, aduaneiro ou operacional.",
    )

    pdf.setFillColor(colors.HexColor(SUBHEADER_COLOR))
    pdf.rect(15 * mm, page_height - 50 * mm, page_width - 30 * mm, 10 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor(TEXT_COLOR))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(18 * mm, page_height - 46 * mm, f"Numero: {document_number}")
    pdf.drawRightString(page_width - 18 * mm, page_height - 46 * mm, f"Data: {document_date}")

    current_y = page_height - 64 * mm
    for section_title, rows in get_render_sections(document):
        pdf.setFillColor(colors.HexColor(SECTION_COLOR))
        pdf.rect(15 * mm, current_y - 6 * mm, page_width - 30 * mm, 8 * mm, fill=1, stroke=0)
        pdf.setFillColor(colors.HexColor(HEADER_COLOR))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(18 * mm, current_y - 3.5 * mm, section_title)
        current_y -= 13 * mm

        pdf.setFillColor(colors.HexColor(TEXT_COLOR))
        for label, value in rows:
            pdf.setStrokeColor(colors.HexColor(LINE_COLOR))
            pdf.line(18 * mm, current_y - 2 * mm, page_width - 18 * mm, current_y - 2 * mm)
            pdf.setFont("Helvetica-Bold", 8.5)
            pdf.drawString(20 * mm, current_y, f"{label}:")
            pdf.setFont("Helvetica", 8.5)
            pdf.drawString(70 * mm, current_y, str(value))
            current_y -= 8 * mm
        current_y -= 5 * mm

    pdf.setFillColor(colors.HexColor("#777777"))
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawCentredString(
        page_width / 2,
        18 * mm,
        "DOCUMENTO ARTIFICIAL GERADO PARA TESTE DE OCR - NAO REPRESENTA DOCUMENTO REAL",
    )
    pdf.save()


def render_clean_image(document: DocumentRecord, image_path: Path) -> None:
    width, height = 1240, 1754
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_font = get_font(34, bold=True)
    subtitle_font = get_font(18)
    section_font = get_font(22, bold=True)
    label_font = get_font(18, bold=True)
    value_font = get_font(18)
    footer_font = get_font(16)

    document_type = get_document_type(document)
    document_number = get_document_number(document)
    document_date = get_document_date(document)

    draw.rectangle([0, 0, width, 190], fill=HEADER_COLOR)
    draw.text((90, 55), f"DOCUMENTO SINTETICO - {document_type}", fill="white", font=title_font)
    draw.text(
        (90, 110),
        "Uso exclusivo para benchmark de OCR. Sem valor fiscal.",
        fill="white",
        font=subtitle_font,
    )

    draw.rectangle([80, 230, 1160, 285], fill=SUBHEADER_COLOR)
    draw.text((100, 247), f"Numero: {document_number}", fill=TEXT_COLOR, font=label_font)
    draw.text((840, 247), f"Data: {document_date}", fill=TEXT_COLOR, font=label_font)

    current_y = 350
    for section_title, rows in get_render_sections(document):
        draw.rectangle([80, current_y, 1160, current_y + 42], fill=SECTION_COLOR)
        draw.text((100, current_y + 8), section_title, fill=HEADER_COLOR, font=section_font)
        current_y += 70

        for label, value in rows:
            draw.line([100, current_y + 26, 1140, current_y + 26], fill=LINE_COLOR, width=1)
            draw.text((115, current_y), f"{label}:", fill=TEXT_COLOR, font=label_font)
            draw.text((430, current_y), str(value), fill=TEXT_COLOR, font=value_font)
            current_y += 48
        current_y += 30

    draw.text(
        (160, 1660),
        "DOCUMENTO ARTIFICIAL GERADO PARA TESTE DE OCR - NAO REPRESENTA DOCUMENTO REAL",
        fill="#888888",
        font=footer_font,
    )
    image.save(image_path, format="PNG")


def generate_dataset(docs_per_type: int, output_dir: Path, seed: int) -> None:
    seed_everything(seed)
    paths = ensure_dataset_dirs(output_dir)
    generated_documents: list[DocumentRecord] = []

    total_documents = docs_per_type * len(DOCUMENT_TYPES)
    current_index = 0

    print("=" * 72)
    print("IDW synthetic dataset generator")
    print("=" * 72)
    print(f"Documents per type : {docs_per_type}")
    print(f"Document types     : {', '.join(DOCUMENT_TYPES)}")
    print(f"Output directory   : {paths['root'].resolve()}")
    print(f"Random seed        : {seed}")
    print("=" * 72)

    for document_type in DOCUMENT_TYPES:
        print(f"[DOC] Generating {document_type} documents...")
        for sequence in range(1, docs_per_type + 1):
            document = build_document(document_type, sequence)
            generated_documents.append(document)

            pdf_path = paths["pdfs"] / f"{document.doc_id}.pdf"
            clean_image_path = paths["clean_images"] / f"{document.doc_id}.png"

            render_pdf(document, pdf_path)
            render_clean_image(document, clean_image_path)
            save_quality_variants(clean_image_path, paths["degraded_images"], document.doc_id)

            current_index += 1
            progress = int((current_index / total_documents) * 100)
            sys.stdout.write(f"\r  Progress: {current_index}/{total_documents} ({progress}%)")
            sys.stdout.flush()
        print()

    print("[DATA] Building ground truth workbook and benchmark template...")
    generate_ground_truth(generated_documents, paths["root"])

    print("=" * 72)
    print("[OK] Dataset generation completed.")
    print(f"  Base documents   : {len(generated_documents)}")
    print(f"  Clean images     : {len(generated_documents)}")
    print(f"  Quality variants : {len(generated_documents) * 5}")
    print(f"  Dataset root     : {paths['root'].resolve()}")
    print("=" * 72)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic OCR benchmark dataset for import documentation.",
    )
    parser.add_argument(
        "--docs-per-type",
        type=int,
        default=20,
        help="Number of documents to generate for each document type.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./dataset",
        help="Output directory for the dataset artifacts.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for deterministic dataset generation.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    try:
        generate_dataset(
            docs_per_type=cli_args.docs_per_type,
            output_dir=Path(cli_args.output),
            seed=cli_args.seed,
        )
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[ERROR] {exc}")
        sys.exit(1)
