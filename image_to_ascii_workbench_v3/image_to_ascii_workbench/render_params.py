"""Render parameter contract for the headless ASCII workbench."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SamplingMode = Literal["center", "average", "median", "super2x", "super4x"]
DitherMode = Literal["none", "floyd-steinberg", "atkinson", "ordered", "random"]
EdgeMode = Literal["off", "sobel", "sobel-hybrid"]
PaletteMode = Literal["cp437-shade", "dense", "classic", "blocks", "binary", "custom"]


@dataclass(frozen=True)
class RenderParams:
    width: int = 160
    height: int | None = None
    cell_aspect: float = 0.5
    brightness: float = 1.0
    contrast: float = 1.0
    gamma: float = 1.0
    black_point: float = 0.0
    white_point: float = 1.0
    invert: bool = False
    grayscale: bool = False
    sepia: bool = False
    sampling: SamplingMode = "average"
    dithering: DitherMode = "none"
    edge_mode: EdgeMode = "off"
    edge_threshold: float = 0.35
    edge_strength: float = 1.0
    palette: PaletteMode = "cp437-shade"
    custom_palette: str | None = None
    measure_font: bool = False
    font_path: str | None = None
