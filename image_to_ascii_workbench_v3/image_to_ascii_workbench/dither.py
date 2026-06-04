"""Dithering algorithms applied at ASCII-cell resolution."""

from __future__ import annotations

import numpy as np


BAYER_4X4 = np.array(
    [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
    ],
    dtype=np.float32,
) / 16.0


def _quantize(value: float, levels: int) -> float:
    if levels <= 1:
        return 0.0
    return round(np.clip(value, 0.0, 1.0) * (levels - 1)) / (levels - 1)


def _error_diffusion(values: np.ndarray, levels: int, kernel: list[tuple[int, int, float]]) -> np.ndarray:
    work = values.astype(np.float32).copy()
    rows, columns = work.shape
    for row in range(rows):
        for col in range(columns):
            old = float(work[row, col])
            new = _quantize(old, levels)
            work[row, col] = new
            error = old - new
            for dy, dx, weight in kernel:
                yy = row + dy
                xx = col + dx
                if 0 <= yy < rows and 0 <= xx < columns:
                    work[yy, xx] += error * weight
    return np.clip(work, 0.0, 1.0)


def apply_dither(luminance: np.ndarray, levels: int, mode: str) -> np.ndarray:
    density = 1.0 - np.clip(luminance.astype(np.float32), 0.0, 1.0)
    if mode == "none":
        return density
    if mode == "floyd-steinberg":
        return _error_diffusion(
            density,
            levels,
            [(0, 1, 7 / 16), (1, -1, 3 / 16), (1, 0, 5 / 16), (1, 1, 1 / 16)],
        )
    if mode == "atkinson":
        return _error_diffusion(
            density,
            levels,
            [(0, 1, 1 / 8), (0, 2, 1 / 8), (1, -1, 1 / 8), (1, 0, 1 / 8), (1, 1, 1 / 8), (2, 0, 1 / 8)],
        )
    if mode == "ordered":
        rows, columns = density.shape
        threshold = np.zeros_like(density)
        for row in range(rows):
            for col in range(columns):
                threshold[row, col] = BAYER_4X4[row % 4, col % 4]
        adjusted = np.clip(density + (threshold - 0.5) / max(2, levels), 0.0, 1.0)
        return np.vectorize(lambda v: _quantize(float(v), levels), otypes=[np.float32])(adjusted)
    if mode == "random":
        rng = np.random.default_rng(0)
        noise = rng.uniform(-0.5, 0.5, size=density.shape) / max(2, levels)
        adjusted = np.clip(density + noise, 0.0, 1.0)
        return np.vectorize(lambda v: _quantize(float(v), levels), otypes=[np.float32])(adjusted)
    raise ValueError(f"unknown dithering mode: {mode}")
