from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import pandas as pd

try:
    from Levenshtein import distance as c_levenshtein_distance
except ImportError:  # pragma: no cover - optional accelerator
    c_levenshtein_distance = None

try:
    from utils import normalize_for_field
except ImportError:
    from src.utils import normalize_for_field


REQUIRED_COLUMNS = [
    "document_id",
    "document_type",
    "quality_variant",
    "ocr_engine",
    "field_name",
    "expected_value",
    "extracted_value",
]


def levenshtein_distance(left: str, right: str) -> int:
    if c_levenshtein_distance is not None:
        return c_levenshtein_distance(left, right)

    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous_row = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current_row = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insert_cost = previous_row[right_index] + 1
            delete_cost = current_row[right_index - 1] + 1
            replace_cost = previous_row[right_index - 1] + (left_char != right_char)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


def sequence_levenshtein(left: Sequence[str], right: Sequence[str]) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous_row = list(range(len(right) + 1))
    for left_index, left_token in enumerate(left, start=1):
        current_row = [left_index]
        for right_index, right_token in enumerate(right, start=1):
            insert_cost = previous_row[right_index] + 1
            delete_cost = current_row[right_index - 1] + 1
            replace_cost = previous_row[right_index - 1] + (left_token != right_token)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


def character_error_rate(expected: str, extracted: str) -> float:
    if expected == "":
        return 0.0 if extracted == "" else 1.0
    return levenshtein_distance(expected, extracted) / len(expected)


def word_error_rate(expected: str, extracted: str) -> float:
    expected_words = expected.split()
    extracted_words = extracted.split()
    if not expected_words:
        return 0.0 if not extracted_words else 1.0
    return sequence_levenshtein(expected_words, extracted_words) / len(expected_words)


def load_benchmark_sheet(input_path: Path) -> pd.DataFrame:
    workbook = pd.ExcelFile(input_path)
    sheet_name = "Benchmark_Template" if "Benchmark_Template" in workbook.sheet_names else workbook.sheet_names[0]
    return pd.read_excel(input_path, sheet_name=sheet_name)


def validate_columns(dataframe: pd.DataFrame) -> None:
    aliases = {
        "doc_id": "document_id",
        "quality_type": "quality_variant",
    }
    dataframe.rename(columns={key: value for key, value in aliases.items() if key in dataframe.columns}, inplace=True)
    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def enrich_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    enriched = dataframe.copy()
    for column in ("expected_value", "extracted_value", "ocr_engine", "quality_variant", "document_type", "field_name"):
        enriched[column] = enriched[column].fillna("").astype(str)

    enriched["normalized_expected"] = enriched.apply(
        lambda row: normalize_for_field(row["field_name"], row["expected_value"]),
        axis=1,
    )
    enriched["normalized_extracted"] = enriched.apply(
        lambda row: normalize_for_field(row["field_name"], row["extracted_value"]),
        axis=1,
    )
    enriched["exact_match"] = (
        enriched["normalized_expected"] == enriched["normalized_extracted"]
    ).astype(int)
    enriched["levenshtein_distance"] = enriched.apply(
        lambda row: levenshtein_distance(row["normalized_expected"], row["normalized_extracted"]),
        axis=1,
    )
    enriched["character_error_rate"] = enriched.apply(
        lambda row: character_error_rate(row["normalized_expected"], row["normalized_extracted"]),
        axis=1,
    )
    enriched["word_error_rate"] = enriched.apply(
        lambda row: word_error_rate(row["normalized_expected"], row["normalized_extracted"]),
        axis=1,
    )
    enriched["confidence_score"] = pd.to_numeric(enriched.get("confidence_score"), errors="coerce")
    enriched["processing_time_seconds"] = pd.to_numeric(
        enriched.get("processing_time_seconds"),
        errors="coerce",
    )
    enriched["has_extracted_value"] = enriched["extracted_value"].str.strip().ne("").astype(int)
    return enriched


def build_aggregate(dataframe: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
    aggregated = (
        dataframe.groupby(group_by, dropna=False)
        .agg(
            rows=("field_name", "count"),
            filled_rows=("has_extracted_value", "sum"),
            field_level_accuracy=("exact_match", "mean"),
            average_levenshtein=("levenshtein_distance", "mean"),
            average_character_error_rate=("character_error_rate", "mean"),
            average_word_error_rate=("word_error_rate", "mean"),
            average_processing_time=("processing_time_seconds", "mean"),
            average_confidence_score=("confidence_score", "mean"),
        )
        .reset_index()
    )
    aggregated["fill_rate"] = aggregated["filled_rows"] / aggregated["rows"]
    return aggregated


def build_document_accuracy(dataframe: pd.DataFrame) -> pd.DataFrame:
    document_accuracy = (
        dataframe.groupby(
            ["document_id", "document_type", "quality_variant", "ocr_engine"],
            dropna=False,
        )
        .agg(
            total_fields=("field_name", "count"),
            correct_fields=("exact_match", "sum"),
            average_processing_time=("processing_time_seconds", "mean"),
            average_confidence_score=("confidence_score", "mean"),
        )
        .reset_index()
    )
    document_accuracy["document_level_accuracy"] = (
        document_accuracy["correct_fields"] / document_accuracy["total_fields"]
    )
    return document_accuracy


def build_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metric": "rows_evaluated", "value": len(dataframe)},
            {"metric": "exact_match_accuracy", "value": dataframe["exact_match"].mean()},
            {"metric": "average_levenshtein", "value": dataframe["levenshtein_distance"].mean()},
            {"metric": "average_character_error_rate", "value": dataframe["character_error_rate"].mean()},
            {"metric": "average_word_error_rate", "value": dataframe["word_error_rate"].mean()},
            {"metric": "average_processing_time", "value": dataframe["processing_time_seconds"].mean()},
            {"metric": "average_confidence_score", "value": dataframe["confidence_score"].mean()},
            {"metric": "fill_rate", "value": dataframe["has_extracted_value"].mean()},
        ]
    )


def evaluate(input_path: Path, output_dir: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input workbook not found: {input_path}")

    print("=" * 72)
    print("IDW OCR benchmark evaluation")
    print("=" * 72)
    print(f"Input workbook : {input_path.resolve()}")
    print(f"Output folder  : {output_dir.resolve()}")
    print("=" * 72)

    benchmark_df = load_benchmark_sheet(input_path)
    validate_columns(benchmark_df)

    if benchmark_df["extracted_value"].fillna("").astype(str).str.strip().eq("").all():
        print("[WARN] The benchmark template has no extracted values yet. Metrics will be zero.")

    detailed_results = enrich_metrics(benchmark_df)
    summary = build_summary(detailed_results)
    ranking = build_aggregate(detailed_results, ["ocr_engine"]).sort_values(
        by=["field_level_accuracy", "average_character_error_rate", "average_processing_time"],
        ascending=[False, True, True],
    )
    by_document_type = build_aggregate(detailed_results, ["ocr_engine", "document_type"])
    by_quality_variant = build_aggregate(detailed_results, ["ocr_engine", "quality_variant"])
    by_field = build_aggregate(detailed_results, ["ocr_engine", "field_name"])
    document_accuracy = build_document_accuracy(detailed_results)

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_output = output_dir / "metrics_output.xlsx"

    with pd.ExcelWriter(metrics_output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        detailed_results.to_excel(writer, sheet_name="Detailed_Results", index=False)
        ranking.to_excel(writer, sheet_name="OCR_Ranking", index=False)
        by_document_type.to_excel(writer, sheet_name="By_Document_Type", index=False)
        by_quality_variant.to_excel(writer, sheet_name="By_Quality_Variant", index=False)
        by_field.to_excel(writer, sheet_name="By_Field", index=False)
        document_accuracy.to_excel(writer, sheet_name="Document_Level", index=False)

    by_field.to_csv(output_dir / "field_accuracy.csv", index=False, encoding="utf-8-sig")
    document_accuracy.to_csv(output_dir / "document_accuracy.csv", index=False, encoding="utf-8-sig")
    ranking.to_csv(output_dir / "ocr_ranking.csv", index=False, encoding="utf-8-sig")

    print("[OK] Evaluation artifacts generated successfully.")
    print(f"  metrics_output.xlsx   : {metrics_output}")
    print(f"  field_accuracy.csv    : {output_dir / 'field_accuracy.csv'}")
    print(f"  document_accuracy.csv : {output_dir / 'document_accuracy.csv'}")
    print(f"  ocr_ranking.csv       : {output_dir / 'ocr_ranking.csv'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a completed OCR benchmark workbook for the IDW project.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to benchmark_template.xlsx or any workbook with a Benchmark_Template sheet.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory where the metrics files will be written.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        evaluate(Path(arguments.input), Path(arguments.output))
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[ERROR] {exc}")
        sys.exit(1)
