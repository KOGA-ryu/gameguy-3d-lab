#!/usr/bin/env python3
"""Generate humanoid head control variants and deterministic QC reports."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import compile_humanoid_head_blockout_v0 as compiler
import export_blender_humanoid_head_blockout_v0 as blender_adapter


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY = ROOT / "data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json"
DEFAULT_VARIANTS = ROOT / "data/characters/head_construction/humanoid_head_control_variants_v0.json"
DEFAULT_OUT_ROOT = Path("/tmp/gameguy_humanoid_head_control_variants_v0")
DEFAULT_BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
VARIANT_SCHEMA = "humanoid_head_control_variants_v0"
REPORT_SCHEMA = "humanoid_head_control_variants_report_v0"


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


def require_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        fail(f"{field} must be >= {minimum}")
    return number


def rounded(value: float) -> float:
    return round(float(value), 6)


def control_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    controls = require_list(taxonomy.get("shape_refinement_controls"), "taxonomy.shape_refinement_controls")
    result: dict[str, dict[str, Any]] = {}
    for index, control in enumerate(controls):
        row = require_object(control, f"taxonomy.shape_refinement_controls[{index}]")
        control_id = require_string(row.get("control_id"), f"taxonomy.shape_refinement_controls[{index}].control_id")
        if control_id in result:
            fail(f"duplicate taxonomy control_id {control_id}")
        allowed_range = require_list(row.get("allowed_range"), f"{control_id}.allowed_range")
        if len(allowed_range) != 2:
            fail(f"{control_id}.allowed_range must be [min, max]")
        lower = require_number(allowed_range[0], f"{control_id}.allowed_range[0]")
        upper = require_number(allowed_range[1], f"{control_id}.allowed_range[1]")
        if lower >= upper:
            fail(f"{control_id}.allowed_range must be ascending")
        result[control_id] = row
    return result


def validate_variant_source(variant_source: dict[str, Any], taxonomy: dict[str, Any]) -> list[dict[str, Any]]:
    if variant_source.get("schema") != VARIANT_SCHEMA:
        fail(f"variant source schema must be {VARIANT_SCHEMA}")
    rules = require_object(variant_source.get("rules"), "variant_source.rules")
    for key in (
        "source_variants_only",
        "compiler_applies_overrides",
        "blender_adapter_consumes_compiled_geometry",
        "no_join_pass",
        "variant_qc_required",
    ):
        if rules.get(key) is not True:
            fail(f"variant_source.rules.{key} must be true")

    controls = control_index(taxonomy)
    dimensions = require_object(
        require_object(taxonomy.get("measurement_profile"), "taxonomy.measurement_profile").get("dimensions_m"),
        "taxonomy.measurement_profile.dimensions_m",
    )
    variants = require_list(variant_source.get("variants"), "variant_source.variants")
    expected_count = variant_source.get("variant_count")
    if not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count != len(variants):
        fail("variant_source.variant_count must match variants length")

    seen: set[str] = set()
    clean_variants: list[dict[str, Any]] = []
    for index, variant in enumerate(variants):
        row = require_object(variant, f"variants[{index}]")
        variant_id = require_string(row.get("variant_id"), f"variants[{index}].variant_id")
        if variant_id in seen:
            fail(f"duplicate variant_id {variant_id}")
        seen.add(variant_id)
        require_string(row.get("plain_name"), f"{variant_id}.plain_name")
        require_string(row.get("style"), f"{variant_id}.style")
        require_string(row.get("purpose"), f"{variant_id}.purpose")
        require_string(row.get("read_goal"), f"{variant_id}.read_goal")

        control_overrides = require_object(row.get("control_overrides"), f"{variant_id}.control_overrides")
        for control_id, value in control_overrides.items():
            if control_id not in controls:
                fail(f"{variant_id}.control_overrides references unknown control {control_id}")
            number = require_number(value, f"{variant_id}.control_overrides.{control_id}")
            lower, upper = [float(item) for item in controls[control_id]["allowed_range"]]
            if not lower <= number <= upper:
                fail(f"{variant_id}.control_overrides.{control_id} must sit inside allowed_range")

        measurement_overrides = require_object(row.get("measurement_overrides_m"), f"{variant_id}.measurement_overrides_m")
        for dimension_id, value in measurement_overrides.items():
            if dimension_id not in dimensions:
                fail(f"{variant_id}.measurement_overrides_m references unknown dimension {dimension_id}")
            require_number(value, f"{variant_id}.measurement_overrides_m.{dimension_id}", minimum=0.0001)
        clean_variants.append(row)
    return clean_variants


def taxonomy_with_variant(taxonomy: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    patched = copy.deepcopy(taxonomy)
    controls = {control["control_id"]: control for control in patched["shape_refinement_controls"]}
    for control_id, value in variant["control_overrides"].items():
        controls[control_id]["default"] = value

    profile = patched["measurement_profile"]
    old_profile_id = require_string(profile.get("profile_id"), "measurement_profile.profile_id")
    profile["profile_id"] = f"{old_profile_id}__{variant['variant_id']}"
    profile["variant_source_id"] = variant["variant_id"]
    dimensions = profile["dimensions_m"]
    for dimension_id, value in variant["measurement_overrides_m"].items():
        dimensions[dimension_id] = value
    return patched


def patch_geometry_for_variant(
    geometry: dict[str, Any],
    compiler_report: dict[str, Any],
    *,
    variant: dict[str, Any],
    taxonomy_path: Path,
    variant_source_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    geometry["asset_id"] = variant["variant_id"]
    geometry["style"] = variant["style"]
    geometry["purpose"] = variant["purpose"]
    geometry["source_reference"]["base_taxonomy"] = str(taxonomy_path)
    geometry["source_reference"]["variant_source"] = str(variant_source_path)
    geometry["source_reference"]["variant_id"] = variant["variant_id"]
    geometry["source_reference"]["variant_overrides"] = {
        "control_overrides": variant["control_overrides"],
        "measurement_overrides_m": variant["measurement_overrides_m"],
    }
    geometry["variant_metadata"] = {
        "variant_id": variant["variant_id"],
        "plain_name": variant["plain_name"],
        "read_goal": variant["read_goal"],
        "no_join_pass": True,
    }
    geometry["build_chain"] = geometry["build_chain"] + ["generate_humanoid_head_control_variants_v0"]

    compiler_report = copy.deepcopy(compiler_report)
    compiler_report["asset_id"] = variant["variant_id"]
    compiler_report["variant_id"] = variant["variant_id"]
    compiler_report["variant_source"] = str(variant_source_path)
    compiler_report["rules"]["uses_variant_source_overrides"] = True
    return geometry, compiler_report


def part_bounds(part: dict[str, Any]) -> dict[str, list[float]]:
    vertices = part["mesh"]["vertices_m"]
    return {
        axis: [rounded(min(vertex[index] for vertex in vertices)), rounded(max(vertex[index] for vertex in vertices))]
        for index, axis in enumerate(("x", "y", "z"))
    }


def global_bounds(parts: list[dict[str, Any]]) -> dict[str, list[float]]:
    vertices = [vertex for part in parts for vertex in part["mesh"]["vertices_m"]]
    return {
        axis: [rounded(min(vertex[index] for vertex in vertices)), rounded(max(vertex[index] for vertex in vertices))]
        for index, axis in enumerate(("x", "y", "z"))
    }


def bounds_size(bounds: dict[str, list[float]]) -> dict[str, float]:
    return {axis: rounded(values[1] - values[0]) for axis, values in bounds.items()}


def axis_gap_and_overlap(a: list[float], b: list[float]) -> tuple[float, float]:
    gap = max(0.0, max(a[0], b[0]) - min(a[1], b[1]))
    overlap = min(a[1], b[1]) - max(a[0], b[0])
    return rounded(gap), rounded(overlap)


def mirrored_vertices(vertices: list[list[float]]) -> list[tuple[float, float, float]]:
    return sorted((rounded(-x), rounded(y), rounded(z)) for x, y, z in vertices)


def sorted_vertices(vertices: list[list[float]]) -> list[tuple[float, float, float]]:
    return sorted((rounded(x), rounded(y), rounded(z)) for x, y, z in vertices)


def symmetry_qc(parts_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    pairs = []
    max_error = 0.0
    for part_id, left_part in sorted(parts_by_id.items()):
        if not part_id.endswith("_L"):
            continue
        base_id = part_id[:-2]
        right_id = f"{base_id}_R"
        if right_id not in parts_by_id:
            continue
        left_vertices = mirrored_vertices(left_part["mesh"]["vertices_m"])
        right_vertices = sorted_vertices(parts_by_id[right_id]["mesh"]["vertices_m"])
        pair_error = 0.0
        if len(left_vertices) != len(right_vertices):
            pair_error = 999.0
        else:
            for left, right in zip(left_vertices, right_vertices):
                pair_error = max(pair_error, max(abs(left[index] - right[index]) for index in range(3)))
        pair_error = rounded(pair_error)
        max_error = max(max_error, pair_error)
        pairs.append({"left_part_id": part_id, "right_part_id": right_id, "max_mirror_error_m": pair_error})
    return {
        "pair_count": len(pairs),
        "max_mirror_error_m": rounded(max_error),
        "all_pairs_symmetric": bool(pairs) and max_error <= 0.000001,
        "pairs": pairs,
    }


def connection_qc(recipe: dict[str, Any], parts_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_gap = 0.0
    min_overlap = 999.0
    all_contact = True
    for rule in recipe["connection_policy"]["rules"]:
        part_id = rule["part_id"]
        parent_id = rule["connects_to"]
        part_box = part_bounds(parts_by_id[part_id])
        parent_box = part_bounds(parts_by_id[parent_id])
        axis_rows: dict[str, dict[str, float]] = {}
        for axis in ("x", "y", "z"):
            gap, overlap = axis_gap_and_overlap(part_box[axis], parent_box[axis])
            axis_rows[axis] = {"gap_m": gap, "overlap_m": overlap}
            max_gap = max(max_gap, gap)
            min_overlap = min(min_overlap, overlap)
        contact = all(axis_rows[axis]["gap_m"] <= 0.000001 for axis in ("x", "y", "z"))
        all_contact = all_contact and contact
        rows.append(
            {
                "part_id": part_id,
                "connects_to": parent_id,
                "method": rule["method"],
                "source_overlap_m": rule["overlap_m"],
                "aabb_contact_or_overlap": contact,
                "axis_contact": axis_rows,
            }
        )
    missing_rules = sorted(set(parts_by_id) - {"skull_envelope"} - {row["part_id"] for row in rows})
    return {
        "rule_count": len(rows),
        "missing_rules": missing_rules,
        "all_non_base_parts_have_rules": not missing_rules,
        "all_connection_aabb_contact_or_overlap": all_contact,
        "max_connection_gap_m": rounded(max_gap),
        "minimum_axis_overlap_m": rounded(min_overlap if rows else 0.0),
        "rules": rows,
    }


def geometry_signature(recipe: dict[str, Any]) -> str:
    payload = {
        "measurement_profile": recipe["measurement_profile"],
        "shape_refinement_controls": recipe["shape_refinement_controls"],
        "parts": recipe["parts"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:20]


def variant_qc(recipe: dict[str, Any]) -> dict[str, Any]:
    parts = recipe["parts"]
    parts_by_id = {part["part_id"]: part for part in parts}
    bounds = global_bounds(parts)
    size = bounds_size(bounds)
    symmetry = symmetry_qc(parts_by_id)
    connections = connection_qc(recipe, parts_by_id)
    bounds_reasonable = (
        0.11 <= size["x"] <= 0.24
        and 0.13 <= size["y"] <= 0.29
        and 0.17 <= size["z"] <= 0.32
    )
    passed = (
        len(parts) == 18
        and symmetry["all_pairs_symmetric"]
        and connections["all_non_base_parts_have_rules"]
        and connections["all_connection_aabb_contact_or_overlap"]
        and bounds_reasonable
    )
    return {
        "part_count": len(parts),
        "bounds_m": bounds,
        "bounds_size_m": size,
        "bounds_reasonable": bounds_reasonable,
        "symmetry": symmetry,
        "connections": connections,
        "geometry_signature": geometry_signature(recipe),
        "passed": passed,
    }


def run_blender_render(blender_path: Path, recipe_path: Path, out_dir: Path) -> dict[str, Any]:
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
        "--json-report",
        str(report_path),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return load_json_object(report_path)


def generate_variants(
    *,
    taxonomy_path: Path,
    variant_source_path: Path,
    out_root: Path,
    json_report: Path,
    render: bool,
    blender_path: Path,
) -> dict[str, Any]:
    taxonomy = load_json_object(taxonomy_path)
    variant_source = load_json_object(variant_source_path)
    variants = validate_variant_source(variant_source, taxonomy)
    out_root.mkdir(parents=True, exist_ok=True)

    records = []
    signatures: dict[str, str] = {}
    for variant in variants:
        variant_id = variant["variant_id"]
        variant_dir = out_root / variant_id
        variant_dir.mkdir(parents=True, exist_ok=True)

        variant_taxonomy = taxonomy_with_variant(taxonomy, variant)
        geometry, compiler_report = compiler.compile_geometry(variant_taxonomy, taxonomy_path)
        geometry, compiler_report = patch_geometry_for_variant(
            geometry,
            compiler_report,
            variant=variant,
            taxonomy_path=taxonomy_path,
            variant_source_path=variant_source_path,
        )

        recipe_path = variant_dir / f"{variant_id}.json"
        compiler_report_path = variant_dir / "compiler_report.json"
        validate_report_path = variant_dir / "validate_report.json"
        qc_report_path = variant_dir / "qc_report.json"

        recipe_path.write_text(json.dumps(geometry, indent=2) + "\n", encoding="utf-8")
        compiler_report_path.write_text(json.dumps(compiler_report, indent=2) + "\n", encoding="utf-8")
        validation = blender_adapter.validate_recipe(geometry, recipe_path)
        validate_report = blender_adapter.make_report(recipe_path, geometry, validation, generated=False, render=False)
        validate_report_path.write_text(json.dumps(validate_report, indent=2) + "\n", encoding="utf-8")

        qc = variant_qc(geometry)
        qc_report_path.write_text(json.dumps(qc, indent=2) + "\n", encoding="utf-8")
        signatures[variant_id] = qc["geometry_signature"]

        blender_report: dict[str, Any] | None = None
        if render:
            blender_report = run_blender_render(blender_path, recipe_path, variant_dir)

        records.append(
            {
                "variant_id": variant_id,
                "plain_name": variant["plain_name"],
                "recipe_path": str(recipe_path),
                "compiler_report_path": str(compiler_report_path),
                "validate_report_path": str(validate_report_path),
                "qc_report_path": str(qc_report_path),
                "render_path": blender_report.get("render_path") if blender_report else None,
                "blend_path": blender_report.get("blend_path") if blender_report else None,
                "qc_passed": qc["passed"],
                "geometry_signature": qc["geometry_signature"],
                "bounds_size_m": qc["bounds_size_m"],
                "max_symmetry_error_m": qc["symmetry"]["max_mirror_error_m"],
                "max_connection_gap_m": qc["connections"]["max_connection_gap_m"],
            }
        )

    duplicate_signatures = len(set(signatures.values())) != len(signatures)
    report = {
        "schema": REPORT_SCHEMA,
        "variant_source": str(variant_source_path),
        "base_taxonomy": str(taxonomy_path),
        "out_root": str(out_root),
        "variant_count": len(records),
        "unique_geometry_signature_count": len(set(signatures.values())),
        "render_requested": render,
        "rules": {
            "source_variants_only": True,
            "compiler_applies_overrides": True,
            "blender_adapter_consumes_compiled_geometry": True,
            "no_join_pass": True,
            "qc_reports_written": True,
        },
        "validation": {
            "all_qc_passed": all(record["qc_passed"] for record in records),
            "all_geometry_signatures_unique": not duplicate_signatures,
            "all_variants_rendered": (not render) or all(record["render_path"] for record in records),
        },
        "variants": records,
    }
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["validation"]["all_qc_passed"]:
        fail("one or more head variants failed QC")
    if duplicate_signatures:
        fail("head variants did not produce unique geometry signatures")
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY, help="Base head layer taxonomy JSON")
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS, help="Head control variants source JSON")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Output directory for generated variant recipes and reports")
    parser.add_argument("--json-report", type=Path, default=None, help="Summary report path")
    parser.add_argument("--render", action="store_true", help="Render each generated variant through Blender")
    parser.add_argument("--blender", type=Path, default=DEFAULT_BLENDER, help="Blender executable path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report_path = args.json_report or (args.out_root / "humanoid_head_control_variants_v0_report.json")
    report = generate_variants(
        taxonomy_path=args.taxonomy,
        variant_source_path=args.variants,
        out_root=args.out_root,
        json_report=report_path,
        render=args.render,
        blender_path=args.blender,
    )
    print(
        "PASS humanoid head control variants: "
        f"variants={report['variant_count']} unique={report['unique_geometry_signature_count']} "
        f"render_requested={report['render_requested']} all_rendered={report['validation']['all_variants_rendered']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
