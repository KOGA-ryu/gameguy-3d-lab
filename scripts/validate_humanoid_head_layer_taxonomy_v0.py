#!/usr/bin/env python3
"""Validate the humanoid head construction layer taxonomy."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = REPO_ROOT / "data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json"
TOOL_DICTIONARY_PATH = REPO_ROOT / "data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json"
DOC_PATH = REPO_ROOT / "docs/research/character_head_construction_v0/humanoid_head_layer_taxonomy_v0.md"


def fail(message: str) -> None:
    print(f"FAIL humanoid head layer taxonomy validation: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - CLI defensive detail
        raise SystemExit(f"FAIL could not parse {path}: {exc}") from exc


def geometry_operation_terms() -> set[str]:
    return {path.stem for path in (REPO_ROOT / "geometry_dictionary/operations").glob("*.json")}


def require_string(item: dict[str, Any], item_id: str, field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        fail(f"{item_id}.{field} must be a non-empty string")
    return value


def require_list(item: dict[str, Any], item_id: str, field: str) -> list[Any]:
    value = item.get(field)
    if not isinstance(value, list) or not value:
        fail(f"{item_id}.{field} must be a non-empty list")
    return value


def validate_unique_rows(rows: list[Any], row_name: str, id_field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            fail(f"{row_name} rows must be objects")
        row_id = require_string(row, row_name, id_field)
        if row_id in result:
            fail(f"duplicate {id_field}: {row_id}")
        result[row_id] = row
    return result


def validate_refs(item_id: str, field: str, values: list[Any], known: set[str]) -> None:
    if not all(isinstance(value, str) and value for value in values):
        fail(f"{item_id}.{field} must contain non-empty strings")
    unknown = sorted(set(values) - known)
    if unknown:
        fail(f"{item_id}.{field} unknown: {unknown}")


def validate_sources(sources: list[Any]) -> None:
    for source in sources:
        if not isinstance(source, dict):
            fail("source_support entries must be objects")
        url = source.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            fail("source_support.url must be an https URL")
        for field in ("label", "support_summary"):
            if not isinstance(source.get(field), str) or not source[field]:
                fail(f"source_support.{field} must be non-empty")


def validate_measurement_profile(profile: dict[str, Any]) -> set[str]:
    if not isinstance(profile, dict):
        fail("measurement_profile must be an object")
    require_string(profile, "measurement_profile", "profile_id")
    require_string(profile, "measurement_profile", "plain_name")
    if profile.get("units") != "m":
        fail("measurement_profile.units must be m")
    dimensions = profile.get("dimensions_m")
    if not isinstance(dimensions, dict) or not dimensions:
        fail("measurement_profile.dimensions_m must be a non-empty object")
    for dimension_id, value in dimensions.items():
        if not isinstance(dimension_id, str) or not dimension_id:
            fail("measurement dimension keys must be non-empty strings")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            fail(f"measurement_profile.dimensions_m.{dimension_id} must be a positive number")
    derived = profile.get("derived_ratios")
    if not isinstance(derived, dict) or not derived:
        fail("measurement_profile.derived_ratios must be a non-empty object")
    for ratio_id, value in derived.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            fail(f"measurement_profile.derived_ratios.{ratio_id} must be a positive number")
    return set(dimensions)


def validate_knobs(layer_id: str, knobs: list[Any]) -> None:
    for knob in knobs:
        if not isinstance(knob, dict):
            fail(f"{layer_id}.edit_knobs entries must be objects")
        knob_id = require_string(knob, f"{layer_id}.edit_knobs", "knob_id")
        require_string(knob, knob_id, "units")
        require_string(knob, knob_id, "meaning")
        value = knob.get("default")
        allowed_range = knob.get("allowed_range")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            fail(f"{layer_id}.{knob_id}.default must be numeric")
        if not isinstance(allowed_range, list) or len(allowed_range) != 2:
            fail(f"{layer_id}.{knob_id}.allowed_range must be [min, max]")
        lower, upper = allowed_range
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)) or lower >= upper:
            fail(f"{layer_id}.{knob_id}.allowed_range must be ascending numbers")
        if not lower <= value <= upper:
            fail(f"{layer_id}.{knob_id}.default must sit inside allowed_range")


def validate_refinement_controls(controls: list[Any], layer_ids: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for control in controls:
        if not isinstance(control, dict):
            fail("shape_refinement_controls entries must be objects")
        control_id = require_string(control, "shape_refinement_controls", "control_id")
        if control_id in result:
            fail(f"duplicate shape_refinement_controls.control_id: {control_id}")
        require_string(control, control_id, "plain_name")
        require_string(control, control_id, "meaning")
        target_layers = require_list(control, control_id, "target_layers")
        validate_refs(control_id, "target_layers", target_layers, layer_ids)
        source_field_mapping = require_list(control, control_id, "source_field_mapping")
        if not all(isinstance(value, str) and value for value in source_field_mapping):
            fail(f"{control_id}.source_field_mapping must contain non-empty strings")
        value = control.get("default")
        allowed_range = control.get("allowed_range")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            fail(f"{control_id}.default must be numeric")
        if not isinstance(allowed_range, list) or len(allowed_range) != 2:
            fail(f"{control_id}.allowed_range must be [min, max]")
        lower, upper = allowed_range
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)) or lower >= upper:
            fail(f"{control_id}.allowed_range must be ascending numbers")
        if not lower <= value <= upper:
            fail(f"{control_id}.default must sit inside allowed_range")
        result[control_id] = control
    for required_control in (
        "brow_arc_ratio",
        "eye_socket_slant_ratio",
        "nose_bridge_blend_ratio",
        "cheek_wrap_ratio",
        "jaw_taper_ratio",
        "feature_embed_overlap_m",
    ):
        if required_control not in result:
            fail(f"shape_refinement_controls must include {required_control}")
    return result


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    tool_dictionary = load_json(TOOL_DICTIONARY_PATH)

    if taxonomy.get("schema") != "humanoid_head_layer_taxonomy_v0":
        fail("schema must be humanoid_head_layer_taxonomy_v0")
    if not DOC_PATH.exists():
        fail(f"missing human documentation: {DOC_PATH}")

    rules = taxonomy.get("rules")
    if not isinstance(rules, dict) or not rules.get("source_recipe_only") or not rules.get("largest_forms_first"):
        fail("rules must declare source_recipe_only and largest_forms_first")

    validate_sources(require_list(taxonomy, "taxonomy", "source_support"))
    dimension_ids = validate_measurement_profile(taxonomy.get("measurement_profile"))

    known_tool_ids = {tool["tool_id"] for tool in tool_dictionary.get("tools", []) if isinstance(tool, dict)}
    known_operation_terms = geometry_operation_terms()

    facial_parts = validate_unique_rows(require_list(taxonomy, "taxonomy", "facial_parts"), "facial_parts", "part_id")
    for part_id, part in facial_parts.items():
        for field in ("plain_name", "construction_role", "read_goal"):
            require_string(part, part_id, field)
        require_list(part, part_id, "anatomy_terms")

    shape_terms = validate_unique_rows(require_list(taxonomy, "taxonomy", "shape_terms"), "shape_terms", "shape_term_id")
    for shape_term_id, shape_term in shape_terms.items():
        for field in ("plain_name", "meaning"):
            require_string(shape_term, shape_term_id, field)
        validate_refs(shape_term_id, "operation_terms", require_list(shape_term, shape_term_id, "operation_terms"), known_operation_terms)
        validate_refs(shape_term_id, "blender_tool_ids", require_list(shape_term, shape_term_id, "blender_tool_ids"), known_tool_ids)

    contour_roles = validate_unique_rows(require_list(taxonomy, "taxonomy", "contour_roles"), "contour_roles", "contour_role_id")
    for contour_role_id, contour_role in contour_roles.items():
        for field in ("plain_name", "purpose"):
            require_string(contour_role, contour_role_id, field)
        validate_refs(
            contour_role_id,
            "compatible_shape_terms",
            require_list(contour_role, contour_role_id, "compatible_shape_terms"),
            set(shape_terms),
        )

    layers = require_list(taxonomy, "taxonomy", "construction_layers")
    layer_rows = validate_unique_rows(layers, "construction_layers", "layer_id")
    refinement_controls = validate_refinement_controls(
        require_list(taxonomy, "taxonomy", "shape_refinement_controls"),
        set(layer_rows),
    )
    previous_sequence = -1
    for layer_id, layer in layer_rows.items():
        sequence = layer.get("sequence")
        if not isinstance(sequence, int) or sequence <= previous_sequence:
            fail(f"{layer_id}.sequence must be a strictly increasing integer")
        previous_sequence = sequence
        rank = layer.get("largest_to_smallest_rank")
        if not isinstance(rank, int) or rank < 1:
            fail(f"{layer_id}.largest_to_smallest_rank must be a positive integer")
        require_string(layer, layer_id, "priority")
        validate_refs(layer_id, "facial_parts", require_list(layer, layer_id, "facial_parts"), set(facial_parts))
        validate_refs(layer_id, "source_dimensions", require_list(layer, layer_id, "source_dimensions"), dimension_ids)
        validate_refs(layer_id, "contour_roles", require_list(layer, layer_id, "contour_roles"), set(contour_roles))
        validate_refs(layer_id, "shape_terms", require_list(layer, layer_id, "shape_terms"), set(shape_terms))
        validate_refs(layer_id, "operation_terms", require_list(layer, layer_id, "operation_terms"), known_operation_terms)
        validate_refs(layer_id, "blender_tool_ids", require_list(layer, layer_id, "blender_tool_ids"), known_tool_ids)
        for field in ("source_fields_needed", "output_contract", "validation_checks"):
            if not all(isinstance(value, str) and value for value in require_list(layer, layer_id, field)):
                fail(f"{layer_id}.{field} must contain non-empty strings")
        validate_knobs(layer_id, require_list(layer, layer_id, "edit_knobs"))

    critical_layers = require_list(taxonomy, "taxonomy", "critical_read_layers")
    validate_refs("critical_read_layers", "layer_ids", critical_layers, set(layer_rows))
    for required_layer in ("skull_envelope", "brow_eye_band", "nose_wedge", "chin_jaw_mass"):
        if required_layer not in critical_layers:
            fail(f"critical_read_layers must include {required_layer}")

    compiler_contract = taxonomy.get("future_compiler_contract")
    if not isinstance(compiler_contract, dict):
        fail("future_compiler_contract must be an object")
    for field in ("input", "output", "adapter_rule"):
        require_string(compiler_contract, "future_compiler_contract", field)

    print(
        "PASS humanoid head layer taxonomy validation: "
        f"parts={len(facial_parts)} shape_terms={len(shape_terms)} contour_roles={len(contour_roles)} "
        f"layers={len(layer_rows)} controls={len(refinement_controls)} dimensions={len(dimension_ids)} tools={len(known_tool_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
