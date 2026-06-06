#!/usr/bin/env python3
"""Compile skull-reference conform recommendations for humanoid head variants."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import generate_humanoid_head_control_variants_v0 as variant_generator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFORM_SOURCE = ROOT / "data/characters/head_construction/humanoid_head_skull_reference_conform_v0.json"
DEFAULT_TAXONOMY = ROOT / "data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json"
DEFAULT_VARIANTS = ROOT / "data/characters/head_construction/humanoid_head_control_variants_v0.json"
DEFAULT_OUT_ROOT = Path("/tmp/gameguy_humanoid_head_skull_reference_conform_v0")
DEFAULT_REPORT = DEFAULT_OUT_ROOT / "humanoid_head_skull_reference_conform_v0_report.json"
CONFORM_SCHEMA = "humanoid_head_skull_reference_conform_v0"
REPORT_SCHEMA = "humanoid_head_skull_reference_conform_report_v0"


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


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def validate_conform_source(source: dict[str, Any]) -> dict[str, Any]:
    if source.get("schema") != CONFORM_SCHEMA:
        fail(f"conform source schema must be {CONFORM_SCHEMA}")
    rules = require_object(source.get("rules"), "conform.rules")
    for key in (
        "reference_only",
        "external_asset_not_copied",
        "source_provenance_required",
        "compiler_emits_conform_recommendations",
        "blender_overlay_consumes_compiled_geometry",
        "no_join_pass",
        "no_skull_as_final_skin",
    ):
        if rules.get(key) is not True:
            fail(f"conform.rules.{key} must be true")

    skull_source = require_object(source.get("external_skull_source"), "external_skull_source")
    required_paths = [
        "gltf_path",
        "bin_path",
        "build_report_path",
        "registry_path",
        "approval_path",
        "contact_sheet_path",
    ]
    for key in required_paths:
        path = Path(require_string(skull_source.get(key), f"external_skull_source.{key}"))
        if not path.exists():
            fail(f"external_skull_source.{key} does not exist: {path}")

    overlay_views = require_list(source.get("overlay_views"), "overlay_views")
    if not overlay_views or not all(isinstance(view, str) and view for view in overlay_views):
        fail("overlay_views must contain non-empty strings")
    targets = require_list(source.get("conform_recommendation_targets"), "conform_recommendation_targets")
    if not targets or not all(isinstance(target, str) and target for target in targets):
        fail("conform_recommendation_targets must contain non-empty strings")
    return skull_source


def skull_reference_summary(conform_source: dict[str, Any]) -> dict[str, Any]:
    skull_source = validate_conform_source(conform_source)
    build_report = load_json_object(Path(skull_source["build_report_path"]))
    registry = load_json_object(Path(skull_source["registry_path"]))
    approval_text = Path(skull_source["approval_path"]).read_text(encoding="utf-8")

    if build_report.get("phase_role") != "source_of_truth":
        fail("skull build report must declare phase_role=source_of_truth")
    if build_report.get("active_seam_id") != skull_source.get("active_seam_id"):
        fail("skull active seam mismatch between conform source and build report")
    if "- front" not in approval_text or "- side" not in approval_text:
        fail("skull approval must include front and side views")

    truth_objects = require_list(build_report.get("truth_object_metadata"), "build_report.truth_object_metadata")
    if len(truth_objects) != 1:
        fail("skull build report must have one truth object")
    truth = require_object(truth_objects[0], "truth_object_metadata[0]")
    bbox = require_object(truth.get("bbox"), "truth_object_metadata[0].bbox")
    bbox_min = [require_number(value, f"skull_bbox.min[{index}]") for index, value in enumerate(require_list(bbox.get("min"), "bbox.min"))]
    bbox_max = [require_number(value, f"skull_bbox.max[{index}]") for index, value in enumerate(require_list(bbox.get("max"), "bbox.max"))]
    bbox_dimensions = [
        require_number(value, f"skull_bbox.dimensions[{index}]", minimum=0.0001)
        for index, value in enumerate(require_list(bbox.get("dimensions"), "bbox.dimensions"))
    ]

    skull_region = (
        require_object(
            require_object(registry.get("region_dimension_bundle"), "registry.region_dimension_bundle").get("regions"),
            "registry.region_dimension_bundle.regions",
        )
        .get("skull")
    )
    if not isinstance(skull_region, dict):
        fail("registry must contain region_dimension_bundle.regions.skull")
    skull_dimensions = require_object(skull_region.get("dimensions"), "registry.skull.dimensions")
    landmark_spans = require_object(skull_region.get("landmark_spans"), "registry.skull.landmark_spans")

    center = [rounded((bbox_min[index] + bbox_max[index]) / 2.0) for index in range(3)]
    return {
        "source_id": skull_source["source_id"],
        "plain_name": skull_source["plain_name"],
        "phase_role": build_report["phase_role"],
        "active_seam_id": build_report["active_seam_id"],
        "source_paths": {
            "gltf_path": skull_source["gltf_path"],
            "build_report_path": skull_source["build_report_path"],
            "registry_path": skull_source["registry_path"],
            "approval_path": skull_source["approval_path"],
            "contact_sheet_path": skull_source["contact_sheet_path"],
            "upstream_vendor_obj": skull_source["upstream_vendor_obj"],
        },
        "upstream_license_note": skull_source["upstream_license_note"],
        "truth_object": {
            "object_name": truth.get("object_name"),
            "chunk_ids": truth.get("source_chunk_ids", []),
            "vertex_count": build_report.get("study_vertex_count"),
            "triangle_count": build_report.get("study_triangle_count"),
            "bbox_m": {
                "min": [rounded(value) for value in bbox_min],
                "max": [rounded(value) for value in bbox_max],
                "center": center,
                "dimensions": [rounded(value) for value in bbox_dimensions],
            },
        },
        "dimension_bundle_m": skull_dimensions,
        "landmark_spans_m": landmark_spans,
        "coarse_landmarks": coarse_landmarks(bbox_min, bbox_max, skull_dimensions, landmark_spans),
    }


def coarse_landmarks(
    bbox_min: list[float],
    bbox_max: list[float],
    skull_dimensions: dict[str, Any],
    landmark_spans: dict[str, Any],
) -> list[dict[str, Any]]:
    center_x = (bbox_min[0] + bbox_max[0]) / 2.0
    center_y = (bbox_min[1] + bbox_max[1]) / 2.0
    top_z = bbox_max[2]
    bottom_z = bbox_min[2]
    brow_z = top_z - require_number(landmark_spans["brow_to_occiput_span_m"], "brow_to_occiput_span_m")
    orbit_z = brow_z - require_number(landmark_spans["brow_to_orbit_drop_m"], "brow_to_orbit_drop_m")
    jaw_z = orbit_z - require_number(landmark_spans["orbit_to_jaw_drop_m"], "orbit_to_jaw_drop_m")
    zygoma_half_width = require_number(skull_dimensions["zygoma_width_m"], "zygoma_width_m") / 2.0
    jaw_half_width = require_number(skull_dimensions["jaw_width_m"], "jaw_width_m") / 2.0
    nasal_half_width = require_number(skull_dimensions["nasal_bridge_width_m"], "nasal_bridge_width_m") / 2.0
    return [
        {"landmark_id": "cranial_vault_top", "estimated_source_m": [rounded(center_x), rounded(center_y), rounded(top_z)]},
        {"landmark_id": "chin_mandible_bottom", "estimated_source_m": [rounded(center_x), rounded(bbox_min[1]), rounded(bottom_z)]},
        {
            "landmark_id": "left_zygoma_width",
            "estimated_source_m": [rounded(-zygoma_half_width), rounded(bbox_min[1] * 0.45), rounded(orbit_z)],
        },
        {
            "landmark_id": "right_zygoma_width",
            "estimated_source_m": [rounded(zygoma_half_width), rounded(bbox_min[1] * 0.45), rounded(orbit_z)],
        },
        {"landmark_id": "brow_band_center", "estimated_source_m": [rounded(center_x), rounded(bbox_min[1] * 0.55), rounded(brow_z)]},
        {
            "landmark_id": "nasal_bridge_width",
            "estimated_source_m": [rounded(nasal_half_width), rounded(bbox_min[1]), rounded((brow_z + orbit_z) / 2.0)],
        },
        {
            "landmark_id": "left_mandible_width",
            "estimated_source_m": [rounded(-jaw_half_width), rounded(center_y), rounded(jaw_z)],
        },
        {
            "landmark_id": "right_mandible_width",
            "estimated_source_m": [rounded(jaw_half_width), rounded(center_y), rounded(jaw_z)],
        },
    ]


def bounds_center(bounds: dict[str, list[float]]) -> list[float]:
    return [rounded((bounds[axis][0] + bounds[axis][1]) / 2.0) for axis in ("x", "y", "z")]


def recipe_part_index(recipe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {part["part_id"]: part for part in recipe["parts"]}


def part_bounds(part: dict[str, Any]) -> dict[str, list[float]]:
    vertices = part["mesh"]["vertices_m"]
    return {
        axis: [rounded(min(vertex[index] for vertex in vertices)), rounded(max(vertex[index] for vertex in vertices))]
        for index, axis in enumerate(("x", "y", "z"))
    }


def transformed_skull_dimensions(skull_dims: list[float], variant_size: dict[str, float]) -> tuple[float, dict[str, float]]:
    scale = variant_size["z"] / skull_dims[2]
    return rounded(scale), {
        "x": rounded(skull_dims[0] * scale),
        "y": rounded(skull_dims[1] * scale),
        "z": rounded(skull_dims[2] * scale),
    }


def compare_variant_to_skull(
    variant_record: dict[str, Any],
    recipe: dict[str, Any],
    qc: dict[str, Any],
    skull: dict[str, Any],
    conform_targets: list[str],
) -> dict[str, Any]:
    skull_dims = skull["truth_object"]["bbox_m"]["dimensions"]
    variant_size = qc["bounds_size_m"]
    variant_bounds = qc["bounds_m"]
    scale, fitted_skull_dims = transformed_skull_dimensions(skull_dims, variant_size)
    dimension_delta = {
        axis: rounded(variant_size[axis] - fitted_skull_dims[axis])
        for axis in ("x", "y", "z")
    }
    dimension_ratio = {
        axis: rounded(variant_size[axis] / fitted_skull_dims[axis])
        for axis in ("x", "y", "z")
    }
    profile_depth_status = (
        "shallower_than_reference_skull"
        if dimension_delta["y"] < -0.012
        else "near_reference_depth"
        if abs(dimension_delta["y"]) <= 0.012
        else "deeper_than_reference_skull"
    )
    width_status = (
        "wider_than_reference_skull"
        if dimension_delta["x"] > 0.012
        else "near_reference_width"
        if abs(dimension_delta["x"]) <= 0.012
        else "narrower_than_reference_skull"
    )

    skull_center = skull["truth_object"]["bbox_m"]["center"]
    variant_center = bounds_center(variant_bounds)
    overlay_transform = {
        "policy_id": "bbox_height_fit_centered_v0",
        "scale": scale,
        "source_center_m": skull_center,
        "target_center_m": variant_center,
        "source_bbox_dimensions_m": skull_dims,
        "fitted_skull_dimensions_m": fitted_skull_dims,
    }

    parts = recipe_part_index(recipe)
    recommendations = conform_recommendations(parts, conform_targets, fitted_skull_dims, dimension_delta, profile_depth_status)
    missing_targets = sorted(
        set(conform_targets) - set(parts)
    )
    return {
        "variant_id": variant_record["variant_id"],
        "plain_name": variant_record["plain_name"],
        "recipe_path": variant_record["recipe_path"],
        "qc_report_path": variant_record["qc_report_path"],
        "geometry_signature": variant_record["geometry_signature"],
        "variant_bounds_size_m": variant_size,
        "fitted_skull_dimensions_m": fitted_skull_dims,
        "dimension_delta_variant_minus_fitted_skull_m": dimension_delta,
        "dimension_ratio_variant_to_fitted_skull": dimension_ratio,
        "profile_depth_status": profile_depth_status,
        "width_status": width_status,
        "overlay_transform": overlay_transform,
        "missing_conform_targets": missing_targets,
        "conform_recommendations": recommendations,
        "join_readiness_status": "blocked_until_skull_conform_visual_review",
    }


def conform_recommendations(
    parts: dict[str, dict[str, Any]],
    target_parts: list[str],
    fitted_skull_dims: dict[str, float],
    dimension_delta: dict[str, float],
    profile_depth_status: str,
) -> list[dict[str, Any]]:
    rows = []
    for part_id in target_parts:
        if part_id not in parts:
            continue
        bounds = part_bounds(parts[part_id])
        y_thickness = rounded(bounds["y"][1] - bounds["y"][0])
        reason = "separate plate should be conformed toward skull-reference volume before joining"
        if part_id in {"face_mask_plane", "cheek_plane_L", "cheek_plane_R"}:
            operation = "curve_and_sink_plate_edges_to_skull_side_reference"
        elif part_id in {"brow_ridge", "eye_socket_rim_L", "eye_socket_rim_R"}:
            operation = "project_orbital_band_toward_brow_orbit_reference"
        elif part_id == "nose_wedge":
            operation = "align_nose_root_to_nasal_aperture_reference_then_keep_stylized_tip"
            reason = "nose should use skull aperture/root as anchor but remain stylized surface volume"
        elif part_id in {"chin_mass", "jaw_side_plane_L", "jaw_side_plane_R"}:
            operation = "conform_lower_face_to_mandible_reference"
        else:
            operation = "sink_relief_into_parent_surface"
        rows.append(
            {
                "part_id": part_id,
                "part_y_thickness_m": y_thickness,
                "recommended_operation": operation,
                "profile_depth_status": profile_depth_status,
                "variant_depth_minus_reference_depth_m": dimension_delta["y"],
                "reference_depth_m": fitted_skull_dims["y"],
                "reason": reason,
            }
        )
    return rows


def compile_conform_report(
    *,
    conform_source_path: Path,
    taxonomy_path: Path,
    variant_source_path: Path,
    out_root: Path,
    json_report: Path,
) -> dict[str, Any]:
    conform_source = load_json_object(conform_source_path)
    skull = skull_reference_summary(conform_source)
    conform_targets = list(require_list(conform_source["conform_recommendation_targets"], "conform_recommendation_targets"))
    variant_root = out_root / "compiled_variants"
    variant_report_path = variant_root / "humanoid_head_control_variants_v0_report.json"
    variant_report = variant_generator.generate_variants(
        taxonomy_path=taxonomy_path,
        variant_source_path=variant_source_path,
        out_root=variant_root,
        json_report=variant_report_path,
        render=False,
        blender_path=variant_generator.DEFAULT_BLENDER,
    )

    variants = []
    for variant_record in variant_report["variants"]:
        recipe = load_json_object(Path(variant_record["recipe_path"]))
        qc = load_json_object(Path(variant_record["qc_report_path"]))
        variants.append(compare_variant_to_skull(variant_record, recipe, qc, skull, conform_targets))

    report = {
        "schema": REPORT_SCHEMA,
        "conform_source": str(conform_source_path),
        "base_taxonomy": str(taxonomy_path),
        "variant_source": str(variant_source_path),
        "out_root": str(out_root),
        "compiled_variant_report": str(variant_report_path),
        "rules": {
            "reference_only": True,
            "external_asset_not_copied": True,
            "no_join_pass": True,
            "no_skull_as_final_skin": True,
            "compiler_emits_conform_recommendations": True,
        },
        "skull_reference": skull,
        "variant_count": len(variants),
        "overlay_views": conform_source["overlay_views"],
        "validation": {
            "skull_reference_loaded": True,
            "all_variant_numeric_qc_passed": variant_report["validation"]["all_qc_passed"],
            "all_geometry_signatures_unique": variant_report["validation"]["all_geometry_signatures_unique"],
            "all_conform_targets_present": all(not variant["missing_conform_targets"] for variant in variants),
            "all_join_blocked_until_conform_review": all(
                variant["join_readiness_status"] == "blocked_until_skull_conform_visual_review" for variant in variants
            ),
        },
        "variants": variants,
    }
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["validation"]["all_variant_numeric_qc_passed"]:
        fail("one or more variants failed numeric QC")
    if not report["validation"]["all_conform_targets_present"]:
        fail("one or more variants are missing conform target parts")
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conform-source", type=Path, default=DEFAULT_CONFORM_SOURCE, help="Skull reference conform source JSON")
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY, help="Base humanoid head taxonomy JSON")
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS, help="Head control variants source JSON")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Output directory for generated conform reports")
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT, help="Output conform summary JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = compile_conform_report(
        conform_source_path=args.conform_source,
        taxonomy_path=args.taxonomy,
        variant_source_path=args.variants,
        out_root=args.out_root,
        json_report=args.json_report,
    )
    print(
        "PASS humanoid head skull reference conform compile: "
        f"variants={report['variant_count']} skull={report['skull_reference']['source_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
