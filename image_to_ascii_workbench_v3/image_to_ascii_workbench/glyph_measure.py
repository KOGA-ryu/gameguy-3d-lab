"""Measure glyph density with Pillow to build font-aware ramps."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class GlyphDensity:
    glyph: str
    density: float


def load_font(font_path: str | None, size: int = 18) -> ImageFont.ImageFont:
    if font_path:
        return ImageFont.truetype(font_path, size=size)
    try:
        return ImageFont.truetype("Menlo.ttc", size=size)
    except OSError:
        return ImageFont.load_default()


def measure_glyph_density(glyph: str, font: ImageFont.ImageFont, *, padding: int = 3) -> GlyphDensity:
    probe = Image.new("L", (64, 64), 255)
    draw = ImageDraw.Draw(probe)
    bbox = draw.textbbox((0, 0), glyph, font=font)
    width = max(1, bbox[2] - bbox[0] + padding * 2)
    height = max(1, bbox[3] - bbox[1] + padding * 2)
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    draw.text((padding - bbox[0], padding - bbox[1]), glyph, fill=0, font=font)
    values = np.asarray(image, dtype=np.float32) / 255.0
    density = float(np.mean(1.0 - values))
    return GlyphDensity(glyph=glyph, density=density)


def measured_ramp(chars: str, font_path: str | None = None, *, font_size: int = 18) -> str:
    font = load_font(font_path, size=font_size)
    densities = [measure_glyph_density(ch, font) for ch in chars]
    densities.sort(key=lambda item: item.density)
    return "".join(item.glyph for item in densities)
