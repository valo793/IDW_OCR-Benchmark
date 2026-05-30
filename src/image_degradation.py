from __future__ import annotations

import io
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

try:
    from document_templates import QUALITY_VARIANTS
except ImportError:
    from src.document_templates import QUALITY_VARIANTS


VARIANT_EXTENSIONS = {
    "clean": "png",
    "low_resolution": "png",
    "blur": "png",
    "heavy_compression": "jpg",
    "skew_shadow_noise": "png",
}


def build_variant_filename(document_id: str, quality_variant: str) -> str:
    extension = VARIANT_EXTENSIONS[quality_variant]
    return f"{document_id}__{quality_variant}.{extension}"


def apply_clean(image: Image.Image) -> Image.Image:
    return image.copy().convert("RGB")


def apply_low_resolution(image: Image.Image) -> Image.Image:
    original_size = image.size
    reduced_size = (
        max(1, original_size[0] // 2),
        max(1, original_size[1] // 2),
    )
    reduced = image.resize(reduced_size, Image.Resampling.BILINEAR)
    return reduced.resize(original_size, Image.Resampling.BILINEAR)


def apply_blur(image: Image.Image, radius: float = 2.2) -> Image.Image:
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_heavy_compression(image: Image.Image, quality: int = 24) -> Image.Image:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    compressed = Image.open(buffer).convert("RGB").copy()
    buffer.close()
    return compressed


def _add_shadow(image: Image.Image) -> Image.Image:
    result = image.convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = result.size
    shadow_alpha = random.randint(45, 85)
    shadow_points = [
        (0, int(height * 0.45)),
        (int(width * 0.55), 0),
        (width, 0),
        (width, height),
        (0, height),
    ]
    draw.polygon(shadow_points, fill=(0, 0, 0, shadow_alpha))
    return Image.alpha_composite(result, overlay).convert("RGB")


def _add_noise(image: Image.Image, sigma: float = 12.0) -> Image.Image:
    array = np.asarray(image).astype(np.float32)
    noise = np.random.normal(0, sigma, array.shape)
    noisy = np.clip(array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy, mode="RGB")


def apply_skew_shadow_noise(image: Image.Image) -> Image.Image:
    rotated = image.rotate(
        random.uniform(-3.5, 3.5),
        resample=Image.Resampling.BILINEAR,
        expand=False,
        fillcolor="white",
    )
    shadowed = _add_shadow(rotated)
    noisy = _add_noise(shadowed, sigma=12.0)
    contrasted = ImageEnhance.Contrast(noisy).enhance(0.86)
    return contrasted.filter(ImageFilter.GaussianBlur(radius=0.4))


VARIANT_FUNCTIONS = {
    "clean": apply_clean,
    "low_resolution": apply_low_resolution,
    "blur": apply_blur,
    "heavy_compression": apply_heavy_compression,
    "skew_shadow_noise": apply_skew_shadow_noise,
}


def save_quality_variants(clean_image_path: Path, output_dir: Path, document_id: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_image = Image.open(clean_image_path).convert("RGB")
    saved_files: dict[str, Path] = {}

    for quality_variant in QUALITY_VARIANTS:
        processed_image = VARIANT_FUNCTIONS[quality_variant](source_image)
        output_path = output_dir / build_variant_filename(document_id, quality_variant)
        if VARIANT_EXTENSIONS[quality_variant] == "jpg":
            processed_image.save(output_path, format="JPEG", quality=24)
        else:
            processed_image.save(output_path, format="PNG")
        saved_files[quality_variant] = output_path

    return saved_files
