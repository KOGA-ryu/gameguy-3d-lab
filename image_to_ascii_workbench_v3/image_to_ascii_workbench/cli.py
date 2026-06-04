"""Command-line interface for the image-to-ASCII workbench."""

from __future__ import annotations

import argparse
import sys

from .ascii_renderer import render_ascii
from .cell_buffer import build_cell_buffer
from .exporters import save_cp437, save_png, save_text
from .glyph_measure import measured_ramp
from .image_pipeline import load_image, preprocess_image
from .palettes import BUILTIN_PALETTES, get_palette
from .render_params import RenderParams


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Headless high-detail image-to-ASCII workbench v3.")
    parser.add_argument("input", help="Input image path.")
    parser.add_argument("--width", type=int, default=160, help="Output width in characters.")
    parser.add_argument("--height", type=int, help="Output height in characters. Defaults from image aspect.")
    parser.add_argument("--cell-aspect", type=float, default=0.5, help="Character cell aspect correction.")
    parser.add_argument("--sampling", choices=["center", "average", "median", "super2x", "super4x"], default="average")
    parser.add_argument("--brightness", type=float, default=1.0)
    parser.add_argument("--contrast", type=float, default=1.0)
    parser.add_argument("--gamma", type=float, default=1.0)
    parser.add_argument("--black-point", type=float, default=0.0)
    parser.add_argument("--white-point", type=float, default=1.0)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--grayscale", action="store_true")
    parser.add_argument("--sepia", action="store_true")
    parser.add_argument("--dither", choices=["none", "floyd-steinberg", "atkinson", "ordered", "random"], default="none")
    parser.add_argument("--edge-mode", choices=["off", "sobel", "sobel-hybrid"], default="off")
    parser.add_argument("--edge-threshold", type=float, default=0.35)
    parser.add_argument("--edge-strength", type=float, default=1.0)
    parser.add_argument("--palette", choices=[*BUILTIN_PALETTES.keys(), "custom"], default="cp437-shade")
    parser.add_argument("--custom-palette")
    parser.add_argument("--measure-font", action="store_true")
    parser.add_argument("--font-path")
    parser.add_argument("--save-txt")
    parser.add_argument("--save-cp437")
    parser.add_argument("--save-png")
    parser.add_argument("--png-font-size", type=int, default=14)
    parser.add_argument("--foreground", default="#e8e8e8")
    parser.add_argument("--background", default="#111111")
    return parser.parse_args(argv)


def build_params(args: argparse.Namespace) -> RenderParams:
    return RenderParams(
        width=args.width,
        height=args.height,
        cell_aspect=args.cell_aspect,
        brightness=args.brightness,
        contrast=args.contrast,
        gamma=args.gamma,
        black_point=args.black_point,
        white_point=args.white_point,
        invert=args.invert,
        grayscale=args.grayscale,
        sepia=args.sepia,
        sampling=args.sampling,
        dithering=args.dither,
        edge_mode=args.edge_mode,
        edge_threshold=args.edge_threshold,
        edge_strength=args.edge_strength,
        palette=args.palette,
        custom_palette=args.custom_palette,
        measure_font=args.measure_font,
        font_path=args.font_path,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    params = build_params(args)
    image = load_image(args.input)
    _, luminance = preprocess_image(image, params)
    buffer = build_cell_buffer(luminance, params.sampling)
    measured = None
    if params.measure_font:
        base = args.custom_palette if args.palette == "custom" else BUILTIN_PALETTES[args.palette]
        measured = measured_ramp(base, params.font_path)
    palette = get_palette(args.palette, custom_palette=args.custom_palette, measured_palette=measured)
    text = render_ascii(buffer, palette, params)
    if args.save_txt:
        save_text(args.save_txt, text)
    if args.save_cp437:
        save_cp437(args.save_cp437, text)
    if args.save_png:
        save_png(
            args.save_png,
            text,
            font_path=args.font_path,
            font_size=args.png_font_size,
            foreground=args.foreground,
            background=args.background,
        )
    if not any([args.save_txt, args.save_cp437, args.save_png]):
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
