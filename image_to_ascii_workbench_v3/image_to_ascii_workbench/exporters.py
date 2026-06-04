"""Export ASCII text, CP437 bytes, and PNG previews."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .glyph_measure import load_font


def save_text(path: str, text: str) -> None:
    Path(path).write_text(text + "\n", encoding="utf-8")


def save_cp437(path: str, text: str) -> None:
    Path(path).write_bytes((text + "\n").encode("cp437", errors="replace"))


def _parse_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("color must be a 6-digit hex value")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def save_png(
    path: str,
    text: str,
    *,
    font_path: str | None = None,
    font_size: int = 14,
    foreground: str = "#e8e8e8",
    background: str = "#111111",
) -> None:
    font = load_font(font_path, size=font_size)
    rows = text.splitlines()
    columns = max((len(row) for row in rows), default=1)
    probe = Image.new("RGB", (16, 16), _parse_color(background))
    draw = ImageDraw.Draw(probe)
    bbox = draw.textbbox((0, 0), "M", font=font)
    cell_w = max(1, bbox[2] - bbox[0])
    cell_h = max(1, bbox[3] - bbox[1] + 2)
    image = Image.new("RGB", (columns * cell_w, max(1, len(rows)) * cell_h), _parse_color(background))
    draw = ImageDraw.Draw(image)
    for row_index, row in enumerate(rows):
        draw.text((0, row_index * cell_h), row, fill=_parse_color(foreground), font=font)
    image.save(path)
