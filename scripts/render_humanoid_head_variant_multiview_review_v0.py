#!/usr/bin/env python3
"""Render multi-view humanoid head variant review sheets before joining parts."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import export_blender_humanoid_head_blockout_v0 as blender_adapter
import generate_humanoid_head_control_variants_v0 as variant_generator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY = ROOT / "data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json"
DEFAULT_VARIANTS = ROOT / "data/characters/head_construction/humanoid_head_control_variants_v0.json"
DEFAULT_REVIEW = ROOT / "data/characters/head_construction/humanoid_head_multiview_review_v0.json"
DEFAULT_OUT_ROOT = Path("/tmp/gameguy_humanoid_head_variant_multiview_review_v0")
DEFAULT_BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
REVIEW_SCHEMA = "humanoid_head_multiview_review_v0"
REPORT_SCHEMA = "humanoid_head_variant_multiview_review_report_v0"


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


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_review_source(review: dict[str, Any]) -> list[dict[str, Any]]:
    if review.get("schema") != REVIEW_SCHEMA:
        fail(f"review schema must be {REVIEW_SCHEMA}")
    rules = require_object(review.get("rules"), "review.rules")
    for key in (
        "review_only",
        "no_geometry_design_decisions",
        "no_join_pass",
        "renders_consume_compiled_variant_recipes",
        "human_visual_review_still_required",
    ):
        if rules.get(key) is not True:
            fail(f"review.rules.{key} must be true")

    views = require_list(review.get("views"), "review.views")
    expected_count = review.get("view_count")
    if not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count != len(views):
        fail("review.view_count must match views length")

    seen: set[str] = set()
    result = []
    for index, view in enumerate(views):
        row = require_object(view, f"views[{index}]")
        view_id = require_string(row.get("view_id"), f"views[{index}].view_id")
        if view_id in seen:
            fail(f"duplicate view_id {view_id}")
        seen.add(view_id)
        require_string(row.get("plain_name"), f"{view_id}.plain_name")
        require_string(row.get("review_role"), f"{view_id}.review_role")
        adapter_view_id = require_string(row.get("adapter_view_id"), f"{view_id}.adapter_view_id")
        if adapter_view_id not in blender_adapter.VIEW_SPECS:
            fail(f"{view_id}.adapter_view_id is not supported by the Blender adapter")
        result.append(row)
    return result


def run_blender_view(blender_path: Path, recipe_path: Path, out_dir: Path, adapter_view_id: str) -> dict[str, Any]:
    if not blender_path.exists():
        fail(f"missing Blender executable: {blender_path}")
    report_path = out_dir / "blender_report.json"
    command = [
        str(blender_path),
        "--background",
        "--python",
        str(ROOT / "scripts/export_blender_humanoid_head_blockout_v0.py"),
        "--",
        "--recipe",
        str(recipe_path),
        "--out",
        str(out_dir),
        "--render",
        "--view",
        adapter_view_id,
        "--json-report",
        str(report_path),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return load_json_object(report_path)


def control_summary(recipe: dict[str, Any]) -> dict[str, Any]:
    overrides = require_object(
        require_object(recipe.get("source_reference"), "recipe.source_reference").get("variant_overrides"),
        "recipe.source_reference.variant_overrides",
    )
    return {
        "changed_controls": sorted(require_object(overrides.get("control_overrides"), "variant_overrides.control_overrides")),
        "changed_measurements": sorted(
            require_object(overrides.get("measurement_overrides_m"), "variant_overrides.measurement_overrides_m")
        ),
    }


def read_status(render_requested: bool, rendered_paths: list[str]) -> str:
    if not render_requested:
        return "planned_not_rendered"
    if rendered_paths:
        return "rendered_for_human_review"
    return "missing_render"


def join_readiness(qc: dict[str, Any], render_requested: bool, all_views_rendered: bool) -> str:
    if qc.get("passed") is True and ((not render_requested) or all_views_rendered):
        return "numeric_precheck_passed_visual_review_required"
    return "needs_fix_before_join"


def render_multiview_review(
    *,
    taxonomy_path: Path,
    variant_source_path: Path,
    review_path: Path,
    out_root: Path,
    json_report: Path,
    render: bool,
    blender_path: Path,
) -> dict[str, Any]:
    review = load_json_object(review_path)
    views = validate_review_source(review)
    compiled_root = out_root / "compiled_variants"
    variant_report_path = compiled_root / "humanoid_head_control_variants_v0_report.json"
    variant_report = variant_generator.generate_variants(
        taxonomy_path=taxonomy_path,
        variant_source_path=variant_source_path,
        out_root=compiled_root,
        json_report=variant_report_path,
        render=False,
        blender_path=blender_path,
    )

    variants = []
    all_view_records = []
    for variant in variant_report["variants"]:
        variant_id = variant["variant_id"]
        recipe_path = Path(variant["recipe_path"])
        qc_report_path = Path(variant["qc_report_path"])
        recipe = load_json_object(recipe_path)
        qc = load_json_object(qc_report_path)
        rendered_paths: list[str] = []
        view_records = []

        for view in views:
            view_id = view["view_id"]
            view_dir = out_root / "views" / variant_id / view_id
            view_dir.mkdir(parents=True, exist_ok=True)
            blender_report = None
            if render:
                blender_report = run_blender_view(blender_path, recipe_path, view_dir, view["adapter_view_id"])
                rendered_paths.append(blender_report["render_path"])
            view_record = {
                "view_id": view_id,
                "plain_name": view["plain_name"],
                "review_role": view["review_role"],
                "adapter_view_id": view["adapter_view_id"],
                "view_output_dir": str(view_dir),
                "render_path": blender_report.get("render_path") if blender_report else None,
                "blend_path": blender_report.get("blend_path") if blender_report else None,
                "adapter_report_path": str(view_dir / "blender_report.json") if blender_report else None,
                "status": "rendered" if blender_report else "planned_not_rendered",
            }
            view_records.append(view_record)
            all_view_records.append(view_record)

        all_views_rendered = all(record["render_path"] for record in view_records)
        controls = control_summary(recipe)
        variants.append(
            {
                "variant_id": variant_id,
                "plain_name": variant["plain_name"],
                "recipe_path": variant["recipe_path"],
                "qc_report_path": variant["qc_report_path"],
                "changed_controls": controls["changed_controls"],
                "changed_measurements": controls["changed_measurements"],
                "bounds_size_m": variant["bounds_size_m"],
                "max_symmetry_error_m": variant["max_symmetry_error_m"],
                "max_connection_gap_m": variant["max_connection_gap_m"],
                "front_read_status": read_status(render, [path for path in rendered_paths if "/front/" in path]),
                "profile_read_status": read_status(
                    render,
                    [path for path in rendered_paths if "/left_profile/" in path or "/right_profile/" in path],
                ),
                "join_readiness_status": join_readiness(qc, render, all_views_rendered),
                "view_count": len(view_records),
                "all_views_rendered": all_views_rendered if render else False,
                "views": view_records,
            }
        )

    report = {
        "schema": REPORT_SCHEMA,
        "review_source": str(review_path),
        "variant_source": str(variant_source_path),
        "base_taxonomy": str(taxonomy_path),
        "out_root": str(out_root),
        "compiled_variant_report": str(variant_report_path),
        "variant_count": len(variants),
        "view_count": len(views),
        "total_view_records": len(all_view_records),
        "render_requested": render,
        "rules": {
            "review_only": True,
            "no_join_pass": True,
            "blender_adapter_consumes_compiled_geometry": True,
            "human_visual_review_still_required": True,
        },
        "validation": {
            "all_numeric_qc_passed": variant_report["validation"]["all_qc_passed"],
            "all_geometry_signatures_unique": variant_report["validation"]["all_geometry_signatures_unique"],
            "all_variants_have_all_views": all(variant["view_count"] == len(views) for variant in variants),
            "all_requested_views_rendered": (not render) or all(record["render_path"] for record in all_view_records),
            "all_join_prechecks_passed": all(
                variant["join_readiness_status"] == "numeric_precheck_passed_visual_review_required" for variant in variants
            ),
        },
        "views": views,
        "variants": variants,
    }
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if not report["validation"]["all_numeric_qc_passed"]:
        fail("one or more compiled variants failed numeric QC")
    if render and not report["validation"]["all_requested_views_rendered"]:
        fail("one or more requested multiview renders failed")
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY, help="Base head layer taxonomy JSON")
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS, help="Head control variants source JSON")
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW, help="Multi-view review config JSON")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Output directory for recipes, reports, and views")
    parser.add_argument("--json-report", type=Path, default=None, help="Summary report path")
    parser.add_argument("--render", action="store_true", help="Render every variant from every configured view")
    parser.add_argument("--blender", type=Path, default=DEFAULT_BLENDER, help="Blender executable path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report_path = args.json_report or (args.out_root / "humanoid_head_variant_multiview_review_v0_report.json")
    report = render_multiview_review(
        taxonomy_path=args.taxonomy,
        variant_source_path=args.variants,
        review_path=args.review,
        out_root=args.out_root,
        json_report=report_path,
        render=args.render,
        blender_path=args.blender,
    )
    print(
        "PASS humanoid head variant multiview review: "
        f"variants={report['variant_count']} views={report['view_count']} "
        f"render_requested={report['render_requested']} "
        f"all_requested_views_rendered={report['validation']['all_requested_views_rendered']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
