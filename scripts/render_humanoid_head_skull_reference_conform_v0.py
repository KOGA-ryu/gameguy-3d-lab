#!/usr/bin/env python3
"""Render skull-reference conform overlays for all humanoid head variants."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import compile_humanoid_head_skull_reference_conform_v0 as conform_compile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFORM_SOURCE = ROOT / "data/characters/head_construction/humanoid_head_skull_reference_conform_v0.json"
DEFAULT_TAXONOMY = ROOT / "data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json"
DEFAULT_VARIANTS = ROOT / "data/characters/head_construction/humanoid_head_control_variants_v0.json"
DEFAULT_OUT_ROOT = Path("/tmp/gameguy_humanoid_head_skull_reference_conform_v0")
DEFAULT_BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
REPORT_SCHEMA = "humanoid_head_skull_reference_conform_render_report_v0"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def run_blender_overlay(
    *,
    blender_path: Path,
    recipe_path: Path,
    skull_gltf: Path,
    view_id: str,
    out_dir: Path,
) -> dict[str, Any]:
    if not blender_path.exists():
        fail(f"missing Blender executable: {blender_path}")
    report_path = out_dir / "overlay_report.json"
    command = [
        str(blender_path),
        "--background",
        "--python",
        str(ROOT / "scripts/render_blender_humanoid_head_skull_reference_overlay_v0.py"),
        "--",
        "--recipe",
        str(recipe_path),
        "--skull-gltf",
        str(skull_gltf),
        "--out",
        str(out_dir),
        "--view",
        view_id,
        "--render",
        "--json-report",
        str(report_path),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return load_json_object(report_path)


def render_conform_overlays(
    *,
    conform_source_path: Path,
    taxonomy_path: Path,
    variant_source_path: Path,
    out_root: Path,
    json_report: Path,
    render: bool,
    blender_path: Path,
) -> dict[str, Any]:
    conform_report_path = out_root / "humanoid_head_skull_reference_conform_v0_report.json"
    conform_report = conform_compile.compile_conform_report(
        conform_source_path=conform_source_path,
        taxonomy_path=taxonomy_path,
        variant_source_path=variant_source_path,
        out_root=out_root,
        json_report=conform_report_path,
    )
    skull_gltf = Path(conform_report["skull_reference"]["source_paths"]["gltf_path"])
    overlay_views = list(conform_report["overlay_views"])

    variants = []
    all_overlay_records = []
    for variant in conform_report["variants"]:
        variant_id = variant["variant_id"]
        view_records = []
        for view_id in overlay_views:
            view_dir = out_root / "overlays" / variant_id / view_id
            view_dir.mkdir(parents=True, exist_ok=True)
            overlay_report = None
            if render:
                overlay_report = run_blender_overlay(
                    blender_path=blender_path,
                    recipe_path=Path(variant["recipe_path"]),
                    skull_gltf=skull_gltf,
                    view_id=view_id,
                    out_dir=view_dir,
                )
            view_record = {
                "view_id": view_id,
                "view_output_dir": str(view_dir),
                "render_path": overlay_report.get("render_path") if overlay_report else None,
                "blend_path": overlay_report.get("blend_path") if overlay_report else None,
                "overlay_report_path": str(view_dir / "overlay_report.json") if overlay_report else None,
                "status": "rendered" if overlay_report else "planned_not_rendered",
            }
            view_records.append(view_record)
            all_overlay_records.append(view_record)
        variants.append(
            {
                "variant_id": variant_id,
                "plain_name": variant["plain_name"],
                "recipe_path": variant["recipe_path"],
                "profile_depth_status": variant["profile_depth_status"],
                "width_status": variant["width_status"],
                "dimension_delta_variant_minus_fitted_skull_m": variant["dimension_delta_variant_minus_fitted_skull_m"],
                "join_readiness_status": variant["join_readiness_status"],
                "conform_recommendation_count": len(variant["conform_recommendations"]),
                "overlay_view_count": len(view_records),
                "all_overlay_views_rendered": all(record["render_path"] for record in view_records) if render else False,
                "views": view_records,
            }
        )

    report = {
        "schema": REPORT_SCHEMA,
        "conform_source": str(conform_source_path),
        "conform_report": str(conform_report_path),
        "out_root": str(out_root),
        "skull_gltf": str(skull_gltf),
        "variant_count": len(variants),
        "overlay_view_count": len(overlay_views),
        "total_overlay_records": len(all_overlay_records),
        "render_requested": render,
        "rules": {
            "reference_only": True,
            "external_asset_not_copied": True,
            "overlay_consumes_compiled_geometry": True,
            "no_join_pass": True,
            "no_skull_as_final_skin": True,
        },
        "validation": {
            "conform_compile_passed": True,
            "all_variant_numeric_qc_passed": conform_report["validation"]["all_variant_numeric_qc_passed"],
            "all_join_blocked_until_conform_review": conform_report["validation"]["all_join_blocked_until_conform_review"],
            "all_variants_have_all_overlay_views": all(variant["overlay_view_count"] == len(overlay_views) for variant in variants),
            "all_requested_overlays_rendered": (not render) or all(record["render_path"] for record in all_overlay_records),
        },
        "variants": variants,
    }
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if render and not report["validation"]["all_requested_overlays_rendered"]:
        fail("one or more skull reference overlay renders failed")
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conform-source", type=Path, default=DEFAULT_CONFORM_SOURCE, help="Skull reference conform source JSON")
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY, help="Base humanoid head taxonomy JSON")
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS, help="Head control variants source JSON")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Output directory for conform reports and overlays")
    parser.add_argument("--json-report", type=Path, default=None, help="Output render summary JSON")
    parser.add_argument("--render", action="store_true", help="Render every skull-reference overlay")
    parser.add_argument("--blender", type=Path, default=DEFAULT_BLENDER, help="Blender executable path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report_path = args.json_report or (args.out_root / "humanoid_head_skull_reference_conform_render_v0_report.json")
    report = render_conform_overlays(
        conform_source_path=args.conform_source,
        taxonomy_path=args.taxonomy,
        variant_source_path=args.variants,
        out_root=args.out_root,
        json_report=report_path,
        render=args.render,
        blender_path=args.blender,
    )
    print(
        "PASS humanoid head skull reference conform render: "
        f"variants={report['variant_count']} views={report['overlay_view_count']} "
        f"render_requested={report['render_requested']} "
        f"all_requested_overlays_rendered={report['validation']['all_requested_overlays_rendered']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
