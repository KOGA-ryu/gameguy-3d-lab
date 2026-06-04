"""
Command line driver.

Usage:
  python -m ascii_blender_dryrun.cli --demo --out out
  python -m ascii_blender_dryrun.cli --recipe examples/doric_column_recipe_v0.json --out out
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .ascii_backend import AsciiBackend
from .blender_backend import BlenderBackend
from .ops import load_ops, save_ops
from .recipes import doric_column_plan
from .validators import save_validation, validation_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Generate the built-in Doric demo recipe.")
    parser.add_argument("--recipe", help="Load recipe JSON instead of built-in demo.")
    parser.add_argument("--out", default="out", help="Output directory.")
    parser.add_argument("--width", type=int, default=96, help="ASCII preview width.")
    parser.add_argument("--height", type=int, default=72, help="ASCII preview height.")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.recipe:
        ops = load_ops(args.recipe)
    else:
        ops = doric_column_plan()

    save_ops(str(out / "compiled_recipe.json"), ops)
    save_validation(str(out / "validation_report.json"), ops)

    ascii_backend = AsciiBackend(width=args.width, height=args.height)
    for projection in ("front", "side", "top"):
        text = ascii_backend.render_projection(ops, projection)  # type: ignore[arg-type]
        (out / f"doric_{projection}_preview.txt").write_text(text, encoding="utf-8")

    blender_script = BlenderBackend().emit(ops)
    (out / "build_doric_column_v0.py").write_text(blender_script, encoding="utf-8")

    report = validation_report(ops)
    if not report["ok"]:
        print("Validation failed. Blender script was still emitted for inspection, but do not run it yet.")
        return 1

    print(f"Wrote dry-run outputs to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
