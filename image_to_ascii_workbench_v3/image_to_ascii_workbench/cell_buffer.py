"""Cell buffer data model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .sampling import sample_cells


@dataclass(frozen=True)
class CellBuffer:
    luminance: np.ndarray

    @property
    def rows(self) -> int:
        return int(self.luminance.shape[0])

    @property
    def columns(self) -> int:
        return int(self.luminance.shape[1])


def build_cell_buffer(luminance: np.ndarray, mode: str) -> CellBuffer:
    rows, columns = luminance.shape
    return CellBuffer(sample_cells(luminance, rows, columns, mode))
