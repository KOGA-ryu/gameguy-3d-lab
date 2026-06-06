#!/usr/bin/env python3
"""Compile a compact brow/eye-region review sheet from skull slice evidence."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import measure_humanoid_skull_reference_v0 as skull_measure


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/characters/head_construction/humanoid_brow_eye_region_review_v0.json"
DEFAULT_OUT_ROOT = Path("/tmp/gameguy_humanoid_brow_eye_region_review_v0")
DEFAULT_JSON_REPORT = DEFAULT_OUT_ROOT / "humanoid_brow_eye_region_review_v0.json"
DEFAULT_MARKDOWN = DEFAULT_OUT_ROOT / "humanoid_brow_eye_region_review_v0.md"
SOURCE_SCHEMA = "humanoid_brow_eye_region_review_source_v0"
REPORT_SCHEMA = "humanoid_brow_eye_region_review_v0"


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


def write_json_object(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
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


def by_id(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = require_string(row.get(key), key)
        if row_id in index:
            fail(f"duplicate {key}: {row_id}")
        index[row_id] = row
    return index


def validate_source(source: dict[str, Any]) -> None:
    if source.get("schema") != SOURCE_SCHEMA:
        fail(f"source schema must be {SOURCE_SCHEMA}")
    rules = require_object(source.get("rules"), "rules")
    for key in (
        "region_only",
        "no_full_head_blockout_json_read",
        "no_raw_contour_points_in_report",
        "no_blender_execution",
        "no_join_pass",
        "source_decisions_stay_out_of_blender",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")
    if require_string(source.get("region_id"), "region_id") != "brow_eye_band":
        fail("region_id must be brow_eye_band")
    source_paths = require_object(source.get("source_paths"), "source_paths")
    for key in ("taxonomy", "skull_measurement_stack_source"):
        path = resolve_repo_path(require_string(source_paths.get(key), f"source_paths.{key}"))
        if not path.exists():
            fail(f"source_paths.{key} does not exist: {path}")
    if not require_list(source.get("skull_evidence_slices"), "skull_evidence_slices"):
        fail("skull_evidence_slices must not be empty")
    if not require_list(source.get("operation_sequence"), "operation_sequence"):
        fail("operation_sequence must not be empty")


def taxonomy_refs(taxonomy: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    refs = require_object(source.get("taxonomy_refs"), "taxonomy_refs")
    facial_parts = by_id([require_object(row, "facial_parts[]") for row in require_list(taxonomy.get("facial_parts"), "taxonomy.facial_parts")], "part_id")
    layers = by_id([require_object(row, "construction_layers[]") for row in require_list(taxonomy.get("construction_layers"), "taxonomy.construction_layers")], "layer_id")
    shape_terms = by_id([require_object(row, "shape_terms[]") for row in require_list(taxonomy.get("shape_terms"), "taxonomy.shape_terms")], "shape_term_id")

    required_layer_ids = [require_string(value, "required_layer_ids[]") for value in require_list(refs.get("required_layer_ids"), "taxonomy_refs.required_layer_ids")]
    required_part_ids = [require_string(value, "required_facial_part_ids[]") for value in require_list(refs.get("required_facial_part_ids"), "taxonomy_refs.required_facial_part_ids")]
    required_shape_terms = [require_string(value, "required_shape_terms[]") for value in require_list(refs.get("required_shape_terms"), "taxonomy_refs.required_shape_terms")]
    for layer_id in required_layer_ids:
        if layer_id not in layers:
            fail(f"required layer missing from taxonomy: {layer_id}")
    for part_id in required_part_ids:
        if part_id not in facial_parts:
            fail(f"required facial part missing from taxonomy: {part_id}")
    for term_id in required_shape_terms:
        if term_id not in shape_terms:
            fail(f"required shape term missing from taxonomy: {term_id}")

    return {
        "layers": [
            {
                "layer_id": layer_id,
                "priority": layers[layer_id].get("priority"),
                "operation_terms": layers[layer_id].get("operation_terms", []),
                "blender_tool_ids": layers[layer_id].get("blender_tool_ids", []),
                "validation_checks": layers[layer_id].get("validation_checks", []),
            }
            for layer_id in required_layer_ids
        ],
        "facial_parts": [
            {
                "part_id": part_id,
                "plain_name": facial_parts[part_id].get("plain_name"),
                "anatomy_terms": facial_parts[part_id].get("anatomy_terms", []),
                "read_goal": facial_parts[part_id].get("read_goal"),
            }
            for part_id in required_part_ids
        ],
        "shape_terms": [
            {
                "shape_term_id": term_id,
                "plain_name": shape_terms[term_id].get("plain_name"),
                "meaning": shape_terms[term_id].get("meaning"),
                "operation_terms": shape_terms[term_id].get("operation_terms", []),
                "blender_tool_ids": shape_terms[term_id].get("blender_tool_ids", []),
            }
            for term_id in required_shape_terms
        ],
    }


def dimension(bounds: dict[str, list[float]], axis: str) -> float:
    values = bounds[axis]
    return rounded(float(values[1]) - float(values[0]))


def summarize_slice(slice_row: dict[str, Any]) -> dict[str, Any]:
    bounds = require_object(slice_row.get("source_bounds_m"), "slice.source_bounds_m")
    summary_bounds = {
        axis: [rounded(float(values[0])), rounded(float(values[1]))]
        for axis, values in bounds.items()
    }
    return {
        "slice_id": slice_row["slice_id"],
        "family_id": slice_row["family_id"],
        "fixed_axis": slice_row["fixed_axis"],
        "project_axes": slice_row["project_axes"],
        "plane_m": slice_row["plane_m"],
        "anatomy_role": slice_row["anatomy_role"],
        "source_vertex_count": slice_row["source_vertex_count"],
        "contour_point_count": slice_row["contour_point_count"],
        "bounds_m": summary_bounds,
        "dimensions_m": {
            axis: dimension(summary_bounds, axis)
            for axis in ("x", "y", "z")
        },
    }


def selected_slice_summaries(source: dict[str, Any], measurement: dict[str, Any]) -> list[dict[str, Any]]:
    slices = by_id(
        [require_object(row, "measurement.slice_stack.slices[]") for row in require_list(measurement["slice_stack"].get("slices"), "measurement.slice_stack.slices")],
        "slice_id",
    )
    result: list[dict[str, Any]] = []
    for evidence in require_list(source.get("skull_evidence_slices"), "skull_evidence_slices"):
        row = require_object(evidence, "skull_evidence_slices[]")
        slice_id = require_string(row.get("slice_id"), "skull_evidence_slices.slice_id")
        if slice_id not in slices:
            fail(f"skull evidence slice missing from measurement output: {slice_id}")
        summary = summarize_slice(slices[slice_id])
        summary["region_use"] = require_string(row.get("use"), f"{slice_id}.use")
        result.append(summary)
    return result


def derive_region_metrics(slices: list[dict[str, Any]]) -> dict[str, Any]:
    index = by_id(slices, "slice_id")
    brow = index["xy_brow_band"]
    profile = index["yz_center_profile"]
    front = index["xz_front_face_surface"]
    orbit = index["xy_zygoma_orbit"]
    brow_bounds = brow["bounds_m"]
    profile_bounds = profile["bounds_m"]
    front_bounds = front["bounds_m"]
    orbit_bounds = orbit["bounds_m"]
    return {
        "brow_band_plane_z_m": brow["plane_m"],
        "brow_band_width_m": brow["dimensions_m"]["x"],
        "brow_band_depth_m": brow["dimensions_m"]["y"],
        "brow_front_y_m": brow_bounds["y"][0],
        "brow_rear_y_m": brow_bounds["y"][1],
        "center_profile_front_y_m": profile_bounds["y"][0],
        "center_profile_rear_y_m": profile_bounds["y"][1],
        "center_profile_depth_m": profile["dimensions_m"]["y"],
        "center_profile_height_m": profile["dimensions_m"]["z"],
        "front_face_surface_width_m": front["dimensions_m"]["x"],
        "front_face_surface_height_m": front["dimensions_m"]["z"],
        "lower_orbit_support_width_m": orbit["dimensions_m"]["x"],
        "lower_orbit_support_front_y_m": orbit_bounds["y"][0],
        "brow_to_lower_orbit_z_gap_m": rounded(brow["plane_m"] - orbit["plane_m"]),
    }


def existing_controls(taxonomy: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    controls = by_id(
        [require_object(row, "taxonomy.shape_refinement_controls[]") for row in require_list(taxonomy.get("shape_refinement_controls"), "taxonomy.shape_refinement_controls")],
        "control_id",
    )
    result = []
    for ref in require_list(source.get("existing_taxonomy_controls"), "existing_taxonomy_controls"):
        row = require_object(ref, "existing_taxonomy_controls[]")
        control_id = require_string(row.get("control_id"), "existing_taxonomy_controls.control_id")
        if control_id not in controls:
            fail(f"existing control missing from taxonomy: {control_id}")
        control = controls[control_id]
        result.append(
            {
                "control_id": control_id,
                "plain_name": control.get("plain_name"),
                "default": control.get("default"),
                "allowed_range": control.get("allowed_range"),
                "target_layers": control.get("target_layers", []),
                "meaning": control.get("meaning"),
                "region_use": row.get("use"),
            }
        )
    return result


def existing_layer_knobs(taxonomy: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    layers = by_id(
        [require_object(row, "taxonomy.construction_layers[]") for row in require_list(taxonomy.get("construction_layers"), "taxonomy.construction_layers")],
        "layer_id",
    )
    result = []
    for ref in require_list(source.get("existing_layer_knobs"), "existing_layer_knobs"):
        row = require_object(ref, "existing_layer_knobs[]")
        layer_id = require_string(row.get("layer_id"), "existing_layer_knobs.layer_id")
        knob_id = require_string(row.get("knob_id"), "existing_layer_knobs.knob_id")
        if layer_id not in layers:
            fail(f"existing layer knob references missing layer: {layer_id}")
        knobs = by_id(
            [require_object(knob, f"{layer_id}.edit_knobs[]") for knob in require_list(layers[layer_id].get("edit_knobs"), f"{layer_id}.edit_knobs")],
            "knob_id",
        )
        if knob_id not in knobs:
            fail(f"existing layer knob missing from taxonomy: {knob_id}")
        knob = knobs[knob_id]
        result.append(
            {
                "knob_id": knob_id,
                "layer_id": layer_id,
                "default": knob.get("default"),
                "allowed_range": knob.get("allowed_range"),
                "units": knob.get("units"),
                "meaning": knob.get("meaning"),
                "region_use": row.get("use"),
            }
        )
    return result


def proposed_controls(source: dict[str, Any], taxonomy_control_ids: set[str]) -> list[dict[str, Any]]:
    result = []
    for index, value in enumerate(require_list(source.get("proposed_region_controls"), "proposed_region_controls")):
        row = require_object(value, f"proposed_region_controls[{index}]")
        allowed_range = require_list(row.get("allowed_range"), f"proposed_region_controls[{index}].allowed_range")
        if len(allowed_range) != 2:
            fail("proposed control allowed_range must contain two values")
        default = require_number(row.get("default"), f"{row.get('control_id', 'control')}.default")
        low = require_number(allowed_range[0], "proposed_control.allowed_range[0]")
        high = require_number(allowed_range[1], "proposed_control.allowed_range[1]")
        if not low <= default <= high:
            fail(f"proposed control default outside allowed range: {row.get('control_id')}")
        result.append(
            {
                "control_id": require_string(row.get("control_id"), "proposed_control.control_id"),
                "units": require_string(row.get("units"), "proposed_control.units"),
                "default": default,
                "allowed_range": [low, high],
                "reason": require_string(row.get("reason"), "proposed_control.reason"),
                "promoted_to_taxonomy": require_string(row.get("control_id"), "proposed_control.control_id")
                in taxonomy_control_ids,
            }
        )
    return result


def compile_review(source: dict[str, Any], source_path: Path) -> dict[str, Any]:
    validate_source(source)
    source_paths = require_object(source.get("source_paths"), "source_paths")
    taxonomy_path = resolve_repo_path(require_string(source_paths["taxonomy"], "source_paths.taxonomy"))
    measurement_source_path = resolve_repo_path(
        require_string(source_paths["skull_measurement_stack_source"], "source_paths.skull_measurement_stack_source")
    )
    taxonomy = load_json_object(taxonomy_path)
    taxonomy_control_ids = {
        require_string(row.get("control_id"), "taxonomy.shape_refinement_controls.control_id")
        for row in require_list(taxonomy.get("shape_refinement_controls"), "taxonomy.shape_refinement_controls")
        if isinstance(row, dict)
    }
    measurement_source = load_json_object(measurement_source_path)
    measurement = skull_measure.build_measurement_stack(measurement_source)
    slices = selected_slice_summaries(source, measurement)
    region_metrics = derive_region_metrics(slices)
    report = {
        "schema": REPORT_SCHEMA,
        "bundle_id": source["bundle_id"],
        "region_id": source["region_id"],
        "plain_name": source["plain_name"],
        "purpose": source["purpose"],
        "input_sources": {
            "region_source": str(source_path),
            "taxonomy": str(taxonomy_path),
            "skull_measurement_stack_source": str(measurement_source_path),
            "compiled_head_blockout_read": False,
            "blender_executed": False,
        },
        "rules": source["rules"],
        "region_components": source["region_components"],
        "taxonomy_refs": taxonomy_refs(taxonomy, source),
        "skull_source_summary": {
            "source_id": measurement["source_provenance"]["source_id"],
            "mesh_bbox_m": measurement["mesh_summary"]["bbox_m"],
            "bbox_delta_max_abs_error_m": measurement["mesh_summary"]["bbox_delta_m"]["max_abs_error_m"],
            "gltf_position_vertex_count": measurement["mesh_summary"]["gltf_position_vertex_count"],
            "gltf_triangle_count": measurement["mesh_summary"]["gltf_triangle_count"],
        },
        "selected_skull_slice_summaries": slices,
        "region_metrics_m": region_metrics,
        "controls": {
            "existing_shape_controls": existing_controls(taxonomy, source),
            "existing_layer_knobs": existing_layer_knobs(taxonomy, source),
            "proposed_region_controls": proposed_controls(source, taxonomy_control_ids),
        },
        "operation_sequence": source["operation_sequence"],
        "manual_review_questions": source["manual_review_questions"],
        "blocked_scope": source["blocked_scope"],
        "next_compiler_edit_candidates": [
            "Separate brow forward projection from brow arc.",
            "Guarantee socket shadow setback relative to brow front.",
            "Shape glabella center before nose wedge work starts.",
            "Wrap brow wings independently from forehead wrap.",
        ],
        "validation": {
            "region_only": True,
            "compiled_head_blockout_not_read": True,
            "raw_contour_points_omitted": True,
            "all_evidence_slices_found": len(slices) == len(source["skull_evidence_slices"]),
            "taxonomy_refs_resolved": True,
            "skull_measurement_bbox_valid": measurement["validation"]["coordinate_map_matches_build_report_bbox"],
        },
    }
    return report


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def markdown_report(report: dict[str, Any]) -> str:
    metrics = report["region_metrics_m"]
    slice_rows = [
        [
            row["slice_id"],
            row["family_id"],
            row["plane_m"],
            row["source_vertex_count"],
            row["contour_point_count"],
            row["region_use"],
        ]
        for row in report["selected_skull_slice_summaries"]
    ]
    control_rows = [
        [row["control_id"], row["default"], row["allowed_range"], row["region_use"]]
        for row in report["controls"]["existing_shape_controls"]
    ]
    knob_rows = [
        [row["knob_id"], row["default"], row["allowed_range"], row["region_use"]]
        for row in report["controls"]["existing_layer_knobs"]
    ]
    proposed_rows = [
        [row["control_id"], row["default"], row["allowed_range"], row["reason"]]
        for row in report["controls"]["proposed_region_controls"]
    ]
    operation_rows = [
        [row["step"], row["operation"], ", ".join(row["blender_tool_ids_later"]), row["meaning"]]
        for row in report["operation_sequence"]
    ]
    questions = "\n".join(f"- {question}" for question in report["manual_review_questions"])
    blocked = "\n".join(f"- {item}" for item in report["blocked_scope"])
    return "\n\n".join(
        [
            f"# {report['plain_name']}",
            report["purpose"],
            "## Measured Region Metrics",
            markdown_table(
                ["Metric", "Value"],
                [
                    ["brow_band_width_m", metrics["brow_band_width_m"]],
                    ["brow_band_depth_m", metrics["brow_band_depth_m"]],
                    ["brow_front_y_m", metrics["brow_front_y_m"]],
                    ["brow_rear_y_m", metrics["brow_rear_y_m"]],
                    ["brow_to_lower_orbit_z_gap_m", metrics["brow_to_lower_orbit_z_gap_m"]],
                    ["center_profile_depth_m", metrics["center_profile_depth_m"]],
                    ["front_face_surface_width_m", metrics["front_face_surface_width_m"]],
                ],
            ),
            "## Skull Evidence Slices",
            markdown_table(["Slice", "Family", "Plane m", "Vertices", "Contour pts", "Use"], slice_rows),
            "## Existing Shape Controls",
            markdown_table(["Control", "Default", "Allowed", "Use"], control_rows),
            "## Existing Layer Knobs",
            markdown_table(["Knob", "Default", "Allowed", "Use"], knob_rows),
            "## Proposed Region Controls",
            markdown_table(["Control", "Default", "Allowed", "Reason"], proposed_rows),
            "## Operation Sequence",
            markdown_table(["Step", "Operation", "Future Blender tools", "Meaning"], operation_rows),
            "## Manual Review Questions",
            questions,
            "## Blocked Scope",
            blocked,
        ]
    ) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = load_json_object(args.source)
    report = compile_review(source, args.source)
    report["human_markdown_report_path"] = str(args.markdown)
    write_json_object(args.json_report, report)
    write_text(args.markdown, markdown_report(report))
    print(
        "PASS humanoid brow eye region review "
        f"slices={len(report['selected_skull_slice_summaries'])} "
        f"existing_controls={len(report['controls']['existing_shape_controls'])} "
        f"proposed_controls={len(report['controls']['proposed_region_controls'])} "
        f"out={args.json_report}"
    )


if __name__ == "__main__":
    main()
