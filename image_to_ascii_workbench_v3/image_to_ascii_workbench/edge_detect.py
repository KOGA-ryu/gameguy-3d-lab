"""Sobel edge detection and directional glyph mapping."""

from __future__ import annotations

import math

import numpy as np


SOBEL_X = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
SOBEL_Y = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)


def _convolve3(values: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    padded = np.pad(values, 1, mode="edge")
    out = np.zeros_like(values, dtype=np.float32)
    rows, columns = values.shape
    for row in range(rows):
        for col in range(columns):
            window = padded[row : row + 3, col : col + 3]
            out[row, col] = float(np.sum(window * kernel))
    return out


def sobel(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gx = _convolve3(values, SOBEL_X)
    gy = _convolve3(values, SOBEL_Y)
    magnitude = np.sqrt(gx * gx + gy * gy)
    max_value = float(np.max(magnitude))
    if max_value > 0:
        magnitude = magnitude / max_value
    angle = np.arctan2(gy, gx)
    return magnitude.astype(np.float32), angle.astype(np.float32)


def edge_char(angle: float) -> str:
    degrees = (math.degrees(angle) + 180.0) % 180.0
    if degrees < 22.5 or degrees >= 157.5:
        return "│"
    if degrees < 67.5:
        return "/"
    if degrees < 112.5:
        return "─"
    return "\\"
