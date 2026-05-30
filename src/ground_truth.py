from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

try:
    from document_templates import (
        OCR_ENGINES_TEMPLATE,
        QUALITY_VARIANTS,
        DocumentRecord,
        get_document_type,
        get_fields_dict,
    )
    from image_degradation import build_variant_filename
except ImportError:
    from src.document_templates import (
        OCR_ENGINES_TEMPLATE,
        QUALITY_VARIANTS,
        DocumentRecord,
        get_document_type,
        get_fields_dict,
    )
    from src.image_degradation import build_variant_filename


def build_documents_sheet(documents: list[DocumentRecord]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for document in documents:
        document_type = get_document_type(document)
        for quality_variant in QUALITY_VARIANTS:
            rows.append(
                {
                    "document_id": document.doc_id,
                    "document_type": document_type,
                    "pdf_path": f"01_pdfs/{document.doc_id}.pdf",
                    "clean_image_path": f"02_images_clean/{document.doc_id}.png",
                    "degraded_image_path": f"03_images_degraded/{build_variant_filename(document.doc_id, quality_variant)}",
                    "quality_variant": quality_variant,
                }
            )
    return pd.DataFrame(rows)


def build_ground_truth_sheet(documents: list[DocumentRecord]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for document in documents:
        document_type = get_document_type(document)
        for field_name, expected_value in get_fields_dict(document).items():
            rows.append(
                {
                    "document_id": document.doc_id,
                    "document_type": document_type,
                    "field_name": field_name,
                    "expected_value": str(expected_value),
                }
            )
    return pd.DataFrame(rows)


def build_benchmark_template(documents: list[DocumentRecord]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for document in documents:
        document_type = get_document_type(document)
        fields = get_fields_dict(document)
        for quality_variant in QUALITY_VARIANTS:
            image_path = f"03_images_degraded/{build_variant_filename(document.doc_id, quality_variant)}"
            for ocr_engine in OCR_ENGINES_TEMPLATE:
                for field_name, expected_value in fields.items():
                    rows.append(
                        {
                            "document_id": document.doc_id,
                            "document_type": document_type,
                            "quality_variant": quality_variant,
                            "ocr_engine": ocr_engine,
                            "image_path": image_path,
                            "field_name": field_name,
                            "expected_value": str(expected_value),
                            "extracted_value": "",
                            "confidence_score": "",
                            "processing_time_seconds": "",
                        }
                    )
    return pd.DataFrame(rows)


def build_wide_ground_truth(documents: list[DocumentRecord]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for document in documents:
        payload = asdict(document)
        payload["document_type"] = get_document_type(document)
        rows.append({key: str(value) for key, value in payload.items()})
    return pd.DataFrame(rows)


def generate_ground_truth(documents: list[DocumentRecord], dataset_root: Path) -> None:
    ground_truth_dir = dataset_root / "04_ground_truth"
    benchmark_dir = dataset_root / "05_benchmark"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    documents_sheet = build_documents_sheet(documents)
    ground_truth_sheet = build_ground_truth_sheet(documents)
    benchmark_template = build_benchmark_template(documents)
    ground_truth_wide = build_wide_ground_truth(documents)

    workbook_path = ground_truth_dir / "ground_truth_workbook.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        documents_sheet.to_excel(writer, sheet_name="Documents", index=False)
        ground_truth_sheet.to_excel(writer, sheet_name="GroundTruth", index=False)
        benchmark_template.to_excel(writer, sheet_name="Benchmark_Template", index=False)

    benchmark_path = benchmark_dir / "benchmark_template.xlsx"
    with pd.ExcelWriter(benchmark_path, engine="openpyxl") as writer:
        benchmark_template.to_excel(writer, sheet_name="Benchmark_Template", index=False)

    ground_truth_wide.to_csv(
        ground_truth_dir / "ground_truth_wide.csv",
        index=False,
        encoding="utf-8-sig",
    )
    ground_truth_sheet.to_csv(
        ground_truth_dir / "ground_truth_long.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"  Ground truth workbook : {workbook_path}")
    print(f"  Benchmark template    : {benchmark_path}")
