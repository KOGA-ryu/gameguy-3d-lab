"""Sampling strategies for turning pixels into ASCII cells."""

from __future__ import annotations

import numpy as np


def _cell_bounds(index: int, count: int, source_count: int) -> tuple[int, int]:
    start = int(np.floor(index * source_count / count))
    end = int(np.floor((index + 1) * source_count / count))
    return start, max(start + 1, end)


def _sample_point(values: np.ndarray, row: float, col: float) -> float:
    r = int(np.clip(round(row), 0, values.shape[0] - 1))
    c = int(np.clip(round(col), 0, values.shape[1] - 1))
    return float(values[r, c])


def sample_cells(values: np.ndarray, rows: int, columns: int, mode: str) -> np.ndarray:
    if values.ndim != 2:
        raise ValueError("sample_cells expects a 2D luminance array")
    output = np.zeros((rows, columns), dtype=np.float32)
    height, width = values.shape
    for row in range(rows):
        y0, y1 = _cell_bounds(row, rows, height)
        for col in range(columns):
            x0, x1 = _cell_bounds(col, columns, width)
            block = values[y0:y1, x0:x1]
            if mode == "center":
                output[row, col] = _sample_point(values, (y0 + y1 - 1) / 2, (x0 + x1 - 1) / 2)
            elif mode == "median":
                output[row, col] = float(np.median(block))
            elif mode in {"super2x", "super4x"}:
                steps = 2 if mode == "super2x" else 4
                samples: list[float] = []
                for sy in range(steps):
                    for sx in range(steps):
                        yy = y0 + (sy + 0.5) * (y1 - y0) / steps
                        xx = x0 + (sx + 0.5) * (x1 - x0) / steps
                        samples.append(_sample_point(values, yy, xx))
                output[row, col] = float(np.mean(samples))
            elif mode == "average":
                output[row, col] = float(np.mean(block))
            else:
                raise ValueError(f"unknown sampling mode: {mode}")
    return output
