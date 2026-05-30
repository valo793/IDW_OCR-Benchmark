from __future__ import annotations

import time
from pathlib import Path
from typing import Callable


def _run_mock(image_path: str) -> dict[str, object]:
    return {
        "text": "",
        "confidence": 0.0,
        "processing_time_seconds": 0.0,
        "engine": "mock",
        "note": f"No OCR engine configured for '{Path(image_path).name}'.",
    }


def _run_tesseract(image_path: str) -> dict[str, object]:
    import pytesseract  # type: ignore[import-untyped]
    from PIL import Image

    start_time = time.perf_counter()
    image = Image.open(image_path)

    text = pytesseract.image_to_string(image, lang="por+eng")
    data = pytesseract.image_to_data(image, lang="por+eng", output_type=pytesseract.Output.DICT)
    confidences = [
        int(conf)
        for conf in data.get("conf", [])
        if str(conf).lstrip("-").isdigit() and int(conf) >= 0
    ]

    average_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
    return {
        "text": text.strip(),
        "confidence": round(average_confidence, 4),
        "processing_time_seconds": round(time.perf_counter() - start_time, 4),
    }


def _run_easyocr(image_path: str) -> dict[str, object]:
    import easyocr  # type: ignore[import-untyped]

    start_time = time.perf_counter()
    reader = easyocr.Reader(["pt", "en"], gpu=False, verbose=False)
    results = reader.readtext(image_path)

    text_chunks = [result[1] for result in results]
    confidences = [float(result[2]) for result in results]
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "text": "\n".join(text_chunks).strip(),
        "confidence": round(average_confidence, 4),
        "processing_time_seconds": round(time.perf_counter() - start_time, 4),
    }


def _run_paddleocr(image_path: str) -> dict[str, object]:
    from paddleocr import PaddleOCR  # type: ignore[import-untyped]

    start_time = time.perf_counter()
    reader = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
    raw_result = reader.ocr(image_path, cls=True)

    text_chunks: list[str] = []
    confidences: list[float] = []
    if raw_result and raw_result[0]:
        for line in raw_result[0]:
            recognized_text, confidence = line[1]
            text_chunks.append(recognized_text)
            confidences.append(float(confidence))

    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return {
        "text": "\n".join(text_chunks).strip(),
        "confidence": round(average_confidence, 4),
        "processing_time_seconds": round(time.perf_counter() - start_time, 4),
    }


ENGINE_REGISTRY: dict[str, Callable[[str], dict[str, object]]] = {
    "mock": _run_mock,
    "tesseract": _run_tesseract,
    "easyocr": _run_easyocr,
    "paddleocr": _run_paddleocr,
    "azure_document_intelligence": _run_mock,
}


def run_ocr(image_path: str, engine: str = "mock") -> dict[str, object]:
    engine_key = engine.strip().lower()
    handler = ENGINE_REGISTRY.get(engine_key)

    if handler is None:
        result = _run_mock(image_path)
        result["note"] = f"Unknown OCR engine '{engine}'. Falling back to mock."
        return result

    try:
        result = handler(image_path)
    except ImportError as exc:
        result = _run_mock(image_path)
        result["note"] = f"Dependency missing for '{engine}': {exc}."
    except Exception as exc:  # pragma: no cover - defensive fallback
        result = _run_mock(image_path)
        result["note"] = f"OCR engine '{engine}' failed: {exc}."

    result["engine"] = engine_key
    return result


def list_available_engines() -> list[str]:
    available = ["mock", "azure_document_intelligence"]

    try:
        import pytesseract  # type: ignore[import-untyped]  # noqa: F401

        available.append("tesseract")
    except ImportError:
        pass

    try:
        import easyocr  # type: ignore[import-untyped]  # noqa: F401

        available.append("easyocr")
    except ImportError:
        pass

    try:
        from paddleocr import PaddleOCR  # type: ignore[import-untyped]  # noqa: F401

        available.append("paddleocr")
    except ImportError:
        pass

    return available
