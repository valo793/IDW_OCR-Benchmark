"""
Avalia os resultados preenchidos do benchmark de OCR.

Entrada esperada:
- Excel com aba Benchmark_Template
- Colunas principais:
  doc_id, document_type, quality_type, ocr_engine, field_name,
  expected_value, extracted_value, confidence_score, processing_time_seconds

Uso:
    python src/evaluate_benchmark.py --input ./dataset/05_benchmark/benchmark_template.xlsx --output ./dataset/05_benchmark/metrics_output.xlsx
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def normalize(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper().replace(" ", "")


def levenshtein(a: str, b: str) -> int:
    """Distância de Levenshtein sem dependências externas."""
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current_row = [i]
        for j, cb in enumerate(b, start=1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def cer(expected: str, extracted: str) -> float:
    """Character Error Rate."""
    expected_n = normalize(expected)
    extracted_n = normalize(extracted)
    if expected_n == "":
        return 0.0 if extracted_n == "" else 1.0
    return levenshtein(expected_n, extracted_n) / len(expected_n)


def word_error_rate(expected: str, extracted: str) -> float:
    expected_words = str(expected).strip().upper().split()
    extracted_words = str(extracted).strip().upper().split()
    if not expected_words:
        return 0.0 if not extracted_words else 1.0
    return levenshtein(" ".join(expected_words), " ".join(extracted_words)) / max(1, len(" ".join(expected_words)))


def evaluate(input_path: Path, output_path: Path) -> None:
    df = pd.read_excel(input_path, sheet_name="Benchmark_Template")

    required_cols = [
        "doc_id",
        "document_type",
        "quality_type",
        "ocr_engine",
        "field_name",
        "expected_value",
        "extracted_value",
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no arquivo: {missing}")

    df["expected_norm"] = df["expected_value"].apply(normalize)
    df["extracted_norm"] = df["extracted_value"].apply(normalize)
    df["exact_match"] = (df["expected_norm"] == df["extracted_norm"]).astype(int)
    df["levenshtein_distance"] = df.apply(lambda r: levenshtein(r["expected_norm"], r["extracted_norm"]), axis=1)
    df["cer"] = df.apply(lambda r: cer(r["expected_value"], r["extracted_value"]), axis=1)
    df["wer"] = df.apply(lambda r: word_error_rate(r["expected_value"], r["extracted_value"]), axis=1)

    # Métricas agregadas
    by_engine = (
        df.groupby("ocr_engine", dropna=False)
        .agg(
            rows=("doc_id", "count"),
            exact_match_accuracy=("exact_match", "mean"),
            avg_cer=("cer", "mean"),
            avg_levenshtein=("levenshtein_distance", "mean"),
        )
        .reset_index()
    )

    by_engine_quality = (
        df.groupby(["ocr_engine", "quality_type"], dropna=False)
        .agg(
            rows=("doc_id", "count"),
            exact_match_accuracy=("exact_match", "mean"),
            avg_cer=("cer", "mean"),
            avg_levenshtein=("levenshtein_distance", "mean"),
        )
        .reset_index()
    )

    by_field = (
        df.groupby(["ocr_engine", "field_name"], dropna=False)
        .agg(
            rows=("doc_id", "count"),
            exact_match_accuracy=("exact_match", "mean"),
            avg_cer=("cer", "mean"),
            avg_levenshtein=("levenshtein_distance", "mean"),
        )
        .reset_index()
    )

    by_document_type = (
        df.groupby(["ocr_engine", "document_type"], dropna=False)
        .agg(
            rows=("doc_id", "count"),
            exact_match_accuracy=("exact_match", "mean"),
            avg_cer=("cer", "mean"),
            avg_levenshtein=("levenshtein_distance", "mean"),
        )
        .reset_index()
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Detailed_Results", index=False)
        by_engine.to_excel(writer, sheet_name="By_Engine", index=False)
        by_engine_quality.to_excel(writer, sheet_name="By_Engine_Quality", index=False)
        by_field.to_excel(writer, sheet_name="By_Field", index=False)
        by_document_type.to_excel(writer, sheet_name="By_Document_Type", index=False)

    print("Avaliação concluída.")
    print(f"Arquivo gerado: {output_path.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avaliação de benchmark OCR.")
    parser.add_argument("--input", required=True, help="Arquivo benchmark_template.xlsx preenchido.")
    parser.add_argument("--output", required=True, help="Arquivo metrics_output.xlsx de saída.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    evaluate(Path(args.input), Path(args.output))
