"""Image loading and adjustment pipeline."""

from __future__ import annotations

import numpy as np
from PIL import Image

from .render_params import RenderParams


def target_size(image: Image.Image, params: RenderParams) -> tuple[int, int]:
    width = max(1, params.width)
    if params.height:
        return width, max(1, params.height)
    aspect = image.height / max(1, image.width)
    height = max(1, int(round(width * aspect * params.cell_aspect)))
    return width, height


def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def _resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    resampling = getattr(Image, "Resampling", Image).LANCZOS
    return image.resize(size, resampling)


def _apply_sepia(rgb: np.ndarray) -> np.ndarray:
    matrix = np.array(
        [
            [1.07, 0.28, 0.10],
            [0.23, 0.83, 0.08],
            [0.12, 0.24, 0.62],
        ],
        dtype=np.float32,
    )
    return np.clip(rgb @ matrix.T, 0.0, 1.0)


def preprocess_image(image: Image.Image, params: RenderParams) -> tuple[np.ndarray, np.ndarray]:
    resized = _resize(image, target_size(image, params))
    rgb = np.asarray(resized, dtype=np.float32) / 255.0
    rgb = (rgb - 0.5) * params.contrast + 0.5
    rgb = rgb * params.brightness
    rgb = np.clip(rgb, 0.0, 1.0)
    if params.black_point != 0.0 or params.white_point != 1.0:
        span = max(1e-6, params.white_point - params.black_point)
        rgb = np.clip((rgb - params.black_point) / span, 0.0, 1.0)
    if params.gamma != 1.0:
        rgb = np.power(np.clip(rgb, 0.0, 1.0), 1.0 / max(1e-6, params.gamma))
    if params.sepia:
        rgb = _apply_sepia(rgb)
    luminance = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
    if params.grayscale:
        rgb = np.repeat(luminance[..., None], 3, axis=2)
    if params.invert:
        rgb = 1.0 - rgb
        luminance = 1.0 - luminance
    return rgb.astype(np.float32), luminance.astype(np.float32)
