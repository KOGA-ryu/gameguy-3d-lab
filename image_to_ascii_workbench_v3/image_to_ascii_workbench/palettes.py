"""Character palette selection and normalization."""

from __future__ import annotations

from collections.abc import Iterable

from .cp437 import (
    BINARY_RAMP,
    CLASSIC_ASCII_RAMP,
    CP437_BLOCK_RAMP,
    CP437_DENSE_RAMP,
    CP437_SHADE_RAMP,
)


BUILTIN_PALETTES = {
    "cp437-shade": CP437_SHADE_RAMP,
    "dense": CP437_DENSE_RAMP,
    "classic": CLASSIC_ASCII_RAMP,
    "blocks": CP437_BLOCK_RAMP,
    "binary": BINARY_RAMP,
}


def unique_chars(chars: Iterable[str]) -> str:
    seen: set[str] = set()
    result: list[str] = []
    for ch in chars:
        if ch not in seen:
            seen.add(ch)
            result.append(ch)
    return "".join(result)


def get_palette(
    name: str,
    *,
    custom_palette: str | None = None,
    measured_palette: str | None = None,
    invert: bool = False,
) -> str:
    if measured_palette:
        palette = measured_palette
    elif name == "custom":
        if not custom_palette:
            raise ValueError("custom palette requires --custom-palette")
        palette = custom_palette
    else:
        try:
            palette = BUILTIN_PALETTES[name]
        except KeyError as exc:
            raise ValueError(f"unknown palette: {name}") from exc
    palette = unique_chars(palette)
    if len(palette) < 2:
        raise ValueError("palette must contain at least two unique characters")
    return palette[::-1] if invert else palette
