"""ASCII renderer that combines density mapping, dithering, and edge glyphs."""

from __future__ import annotations

import numpy as np

from .cell_buffer import CellBuffer
from .dither import apply_dither
from .edge_detect import edge_char, sobel
from .render_params import RenderParams


def density_to_index(value: float, levels: int) -> int:
    return int(np.clip(round(value * (levels - 1)), 0, levels - 1))


def render_ascii(buffer: CellBuffer, palette: str, params: RenderParams) -> str:
    density = apply_dither(buffer.luminance, len(palette), params.dithering)
    chars = np.empty(buffer.luminance.shape, dtype="<U1")
    for row in range(buffer.rows):
        for col in range(buffer.columns):
            chars[row, col] = palette[density_to_index(float(density[row, col]), len(palette))]

    if params.edge_mode != "off":
        magnitude, angle = sobel(buffer.luminance)
        threshold = max(0.0, min(1.0, params.edge_threshold))
        for row in range(buffer.rows):
            for col in range(buffer.columns):
                if float(magnitude[row, col]) >= threshold:
                    ch = edge_char(float(angle[row, col]))
                    if params.edge_mode == "sobel":
                        chars[row, col] = ch
                    elif params.edge_mode == "sobel-hybrid":
                        edge_weight = float(magnitude[row, col]) * params.edge_strength
                        if edge_weight >= threshold:
                            chars[row, col] = ch

    return "\n".join("".join(chars[row, :]) for row in range(buffer.rows))
