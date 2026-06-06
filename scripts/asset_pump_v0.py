#!/usr/bin/env python3
"""Pump source asset recipes into deterministic geometry JSON.

This is the clean core of the 3D lab:

source recipe -> profile/operation compiler -> asset mesh JSON -> manifest

It intentionally does not write workflow reports, receipts, Blender files,
renders, or repo-local generated folders.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_asset_pump_v0")
DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SIMPLE_BUNDLE_SCHEMA = "asset_mill_recipe_bundle_v0"
MEASURED_BUNDLE_SCHEMA = "asset_mill_measured_component_bundle_v0"
SECTION_STACK_BUNDLE_SCHEMA = "asset_mill_section_stack_bundle_v0"
RADIAL_STACK_BUNDLE_SCHEMA = "asset_mill_radial_stack_bundle_v0"
PROFILE_REVOLVE_BUNDLE_SCHEMA = "asset_mill_profile_revolve_bundle_v0"
BLOCKY_COLUMN_BUNDLE_SCHEMA = "asset_mill_blocky_column_bundle_v0"
BLOCKY_SHAPE_BUNDLE_SCHEMA = "asset_mill_blocky_shape_grammar_bundle_v0"
DECORATED_BALUSTRADE_BUNDLE_SCHEMA = "asset_mill_decorated_balustrade_bundle_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}


@dataclass(frozen=True)
class Mesh:
    vertices: list[list[float]]
    faces: list[list[int]]

    def translated(self, offset: list[float]) -> "Mesh":
        return Mesh(
            vertices=[
                [
                    round(vertex[0] + offset[0], 6),
                    round(vertex[1] + offset[1], 6),
                    round(vertex[2] + offset[2], 6),
                ]
                for vertex in self.vertices
            ],
            faces=[face[:] for face in self.faces],
        )


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def finite_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    return round(float(value), 6)


def positive_float(value: Any, field: str) -> float:
    number = finite_float(value, field)
    if number <= 0.0:
        fail(f"{field} must be positive")
    return number


def integer_at_least(value: Any, minimum: int, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        fail(f"{field} must be an integer")
    if value < minimum:
        fail(f"{field} must be >= {minimum}")
    return value


def ratio_less_than_one(value: Any, field: str) -> float:
    number = finite_float(value, field)
    if number < 0.0 or number >= 1.0:
        fail(f"{field} must be >= 0 and < 1")
    return number


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def finite_vector(value: Any, field: str, length: int = 3) -> list[float]:
    items = require_list(value, field)
    if len(items) != length:
        fail(f"{field} must contain {length} numbers")
    return [finite_float(item, f"{field}[{index}]") for index, item in enumerate(items)]


def positive_vector(value: Any, field: str, length: int = 3) -> list[float]:
    items = finite_vector(value, field, length)
    for index, item in enumerate(items):
        if item <= 0.0:
            fail(f"{field}[{index}] must be positive")
    return items


def increasing_range(value: Any, field: str) -> list[float]:
    items = finite_vector(value, field, 2)
    if items[0] >= items[1]:
        fail(f"{field} must increase")
    return items


def require_false_claims(value: Any, field: str, required_keys: set[str]) -> dict[str, bool]:
    claims = require_object(value, field)
    for key in required_keys:
        if claims.get(key) is not False:
            fail(f"{field}.{key} must be false")
    for key, claim in claims.items():
        if not isinstance(key, str) or not isinstance(claim, bool):
            fail(f"{field} must contain boolean claim flags")
        if claim is not False:
            fail(f"{field}.{key} must be false")
    return claims


def validate_claims(asset: dict[str, Any]) -> None:
    if asset.get("no_claims") != FALSE_CLAIMS:
        fail(f"{asset.get('asset_id', '<unknown>')} no_claims must exactly match false claim flags")


def load_geometry_terms() -> dict[str, set[str]]:
    terms = {
        "profile_primitive": set(),
        "mesh_operation": set(),
        "composition_operation": set(),
        "transform": set(),
        "connector": set(),
        "semantic_geometry": set(),
        "measurement": set(),
        "validation_term": set(),
    }
    for path in sorted(DICTIONARY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = term.get("term_id")
        category = term.get("category")
        if not isinstance(term_id, str) or not term_id:
            fail(f"{repo_display_path(path)} term_id must be a non-empty string")
        if category in terms:
            if term_id in terms[category]:
                fail(f"duplicate geometry dictionary term `{term_id}` in category `{category}`")
            terms[category].add(term_id)
    for category, ids in terms.items():
        if not ids:
            fail(f"geometry dictionary category `{category}` has no terms")
    return terms


def operation_terms(terms: dict[str, set[str]]) -> set[str]:
    return terms["mesh_operation"] | terms["composition_operation"] | terms["transform"]


def all_terms(terms: dict[str, set[str]]) -> set[str]:
    values: set[str] = set()
    for ids in terms.values():
        values.update(ids)
    return values


def require_known_terms(values: Any, known: set[str], field: str) -> list[str]:
    items = require_list(values, field)
    result: list[str] = []
    for index, item in enumerate(items):
        term_id = require_string(item, f"{field}[{index}]")
        if term_id not in known:
            fail(f"{field}[{index}] uses unknown geometry dictionary term `{term_id}`")
        result.append(term_id)
    return result


def validate_dimensions_object(value: Any, field: str) -> dict[str, float]:
    dims = require_object(value, field)
    return {axis: positive_float(dims.get(axis), f"{field}.{axis}") for axis in ("width", "depth", "height")}


def validate_bounds_object(value: Any, field: str) -> dict[str, list[float]]:
    bounds_m = require_object(value, field)
    min_values = finite_vector(bounds_m.get("min"), f"{field}.min")
    max_values = finite_vector(bounds_m.get("max"), f"{field}.max")
    for axis, (min_value, max_value) in enumerate(zip(min_values, max_values, strict=True)):
        if min_value >= max_value:
            fail(f"{field} axis {axis} min must be less than max")
    return {"min": min_values, "max": max_values}


def validate_bounds_match_dimensions(bounds_m: dict[str, list[float]], dims: dict[str, float], field: str) -> None:
    expected = {
        "width": round(bounds_m["max"][0] - bounds_m["min"][0], 6),
        "depth": round(bounds_m["max"][1] - bounds_m["min"][1], 6),
        "height": round(bounds_m["max"][2] - bounds_m["min"][2], 6),
    }
    if expected != dims:
        fail(f"{field}.bounds_m span must match dimensions_m")


def validate_unit_direction(value: Any, field: str) -> list[float]:
    direction = finite_vector(value, field)
    length = math.sqrt(sum(item * item for item in direction))
    if not math.isclose(length, 1.0, rel_tol=0.0, abs_tol=1e-6):
        fail(f"{field} must be normalized")
    return direction


def validate_profile_terms(profile: Any, terms: dict[str, set[str]], field: str) -> None:
    profile_obj = require_object(profile, field)
    profile_type = require_string(profile_obj.get("type"), f"{field}.type")
    if profile_type not in terms["profile_primitive"]:
        fail(f"{field}.type uses unknown geometry dictionary profile `{profile_type}`")
    require_object(profile_obj.get("params", {}), f"{field}.params")


def validate_recipe_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)

        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")

        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")

        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")

        if operation == "extrude":
            validate_profile_terms(asset.get("profile"), terms, f"{asset_id}.profile")
        elif operation == "loft_sections":
            sections = require_list(asset.get("sections"), f"{asset_id}.sections")
            if len(sections) < 2:
                fail(f"{asset_id}.sections requires at least two sections")
            for section_index, section in enumerate(sections):
                section_obj = require_object(section, f"{asset_id}.sections[{section_index}]")
                validate_profile_terms(section_obj.get("profile"), terms, f"{asset_id}.sections[{section_index}].profile")
        elif operation == "compound_asset":
            components = require_list(asset.get("components"), f"{asset_id}.components")
            if not components:
                fail(f"{asset_id}.components must not be empty")
            for component_index, component in enumerate(components):
                component_obj = require_object(component, f"{asset_id}.components[{component_index}]")
                ref = require_string(component_obj.get("asset_ref"), f"{asset_id}.components[{component_index}].asset_ref")
                if ref not in seen_asset_ids:
                    fail(f"{asset_id} references unknown or later asset_ref `{ref}`")


def validate_section_stack_rings(stack: Any, terms: dict[str, set[str]], field: str) -> None:
    stack_obj = require_object(stack, field)
    axis = require_string(stack_obj.get("axis"), f"{field}.axis")
    if axis != "z":
        fail(f"{field}.axis only supports z in v0")
    rings = require_list(stack_obj.get("rings"), f"{field}.rings")
    if len(rings) < 2:
        fail(f"{field}.rings requires at least two rings")
    seen_ring_ids: set[str] = set()
    previous_at: float | None = None
    ring_size: int | None = None
    for ring_index, ring in enumerate(rings):
        ring_obj = require_object(ring, f"{field}.rings[{ring_index}]")
        ring_id = require_string(ring_obj.get("ring_id"), f"{field}.rings[{ring_index}].ring_id")
        if ring_id in seen_ring_ids:
            fail(f"{field}.rings duplicate ring_id: {ring_id}")
        seen_ring_ids.add(ring_id)
        at = finite_float(ring_obj.get("at"), f"{field}.rings[{ring_index}].at")
        if previous_at is not None and at <= previous_at:
            fail(f"{field}.rings[{ring_index}].at must increase")
        previous_at = at
        profile = require_object(ring_obj.get("profile"), f"{field}.rings[{ring_index}].profile")
        validate_profile_terms(profile, terms, f"{field}.rings[{ring_index}].profile")
        points = profile_points(profile)
        if ring_size is None:
            ring_size = len(points)
        elif len(points) != ring_size:
            fail(f"{field}.rings must have matching vertex counts")


def validate_section_stack_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    known_terms = all_terms(terms)
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation != "section_stack":
            fail(f"{asset_id}.operation must be section_stack")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")
        validate_section_stack_rings(asset.get("section_stack"), terms, f"{asset_id}.section_stack")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")
        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")
        validate_claims(asset)


def validate_radial_stack_ring(value: Any, field: str) -> str:
    ring = require_object(value, field)
    ring_id = require_string(ring.get("ring_id"), f"{field}.ring_id")
    finite_float(ring.get("at"), f"{field}.at")
    positive_float(ring.get("radius_m"), f"{field}.radius_m")
    if "material_role" in ring:
        require_string(ring.get("material_role"), f"{field}.material_role")
    return ring_id


def validate_radial_stack_source(value: Any, field: str) -> None:
    stack = require_object(value, field)
    axis = require_string(stack.get("axis"), f"{field}.axis")
    if axis not in {"x", "y", "z"}:
        fail(f"{field}.axis must be x, y, or z")
    integer_at_least(stack.get("segments"), 8, f"{field}.segments")

    rings = require_list(stack.get("rings"), f"{field}.rings")
    if len(rings) < 2:
        fail(f"{field}.rings requires at least two rings")
    seen_ring_ids: set[str] = set()
    previous_at: float | None = None
    for ring_index, item in enumerate(rings):
        ring = require_object(item, f"{field}.rings[{ring_index}]")
        ring_id = validate_radial_stack_ring(ring, f"{field}.rings[{ring_index}]")
        if ring_id in seen_ring_ids:
            fail(f"{field}.rings duplicate ring_id: {ring_id}")
        seen_ring_ids.add(ring_id)
        at = finite_float(ring.get("at"), f"{field}.rings[{ring_index}].at")
        if previous_at is not None and at <= previous_at:
            fail(f"{field}.rings[{ring_index}].at must increase")
        previous_at = at

    seen_part_ids = {"radial_stack_body"}
    radial_details = require_list(stack.get("radial_details", []), f"{field}.radial_details")
    for detail_index, item in enumerate(radial_details):
        detail = require_object(item, f"{field}.radial_details[{detail_index}]")
        detail_type = require_string(detail.get("detail_type"), f"{field}.radial_details[{detail_index}].detail_type")
        if detail_type != "radial_box_array":
            fail(f"{field}.radial_details[{detail_index}].detail_type unsupported: {detail_type}")
        validate_blocky_ribs(detail, f"{field}.radial_details[{detail_index}]")
        part_prefix = require_string(detail.get("part_prefix"), f"{field}.radial_details[{detail_index}].part_prefix")
        count = integer_at_least(detail.get("count"), 1, f"{field}.radial_details[{detail_index}].count")
        for rib_index in range(count):
            part_id = f"{part_prefix}_{rib_index:02d}"
            if part_id in seen_part_ids:
                fail(f"{field} duplicate expanded part_id: {part_id}")
            seen_part_ids.add(part_id)

    attachments = require_list(stack.get("attachments", []), f"{field}.attachments")
    for attachment_index, item in enumerate(attachments):
        attachment = require_object(item, f"{field}.attachments[{attachment_index}]")
        part_type = require_string(attachment.get("part_type"), f"{field}.attachments[{attachment_index}].part_type")
        if part_type != "box":
            fail(f"{field}.attachments[{attachment_index}].part_type unsupported: {part_type}")
        validate_blocky_box_part(attachment, f"{field}.attachments[{attachment_index}]")
        part_id = require_string(attachment.get("part_id"), f"{field}.attachments[{attachment_index}].part_id")
        if part_id in seen_part_ids:
            fail(f"{field} duplicate expanded part_id: {part_id}")
        seen_part_ids.add(part_id)


def profile_revolve_to_radial_stack(value: Any, field: str) -> dict[str, Any]:
    source = require_object(value, field)
    axis = require_string(source.get("axis"), f"{field}.axis")
    if axis not in {"x", "y", "z"}:
        fail(f"{field}.axis must be x, y, or z")
    segments = integer_at_least(source.get("segments"), 8, f"{field}.segments")
    side_profile = require_list(source.get("side_profile"), f"{field}.side_profile")
    if len(side_profile) < 2:
        fail(f"{field}.side_profile requires at least two profile points")

    rings: list[dict[str, Any]] = []
    seen_point_ids: set[str] = set()
    previous_at: float | None = None
    for point_index, item in enumerate(side_profile):
        point = require_object(item, f"{field}.side_profile[{point_index}]")
        point_id = require_string(point.get("point_id"), f"{field}.side_profile[{point_index}].point_id")
        if point_id in seen_point_ids:
            fail(f"{field}.side_profile duplicate point_id: {point_id}")
        seen_point_ids.add(point_id)
        at = finite_float(point.get("at"), f"{field}.side_profile[{point_index}].at")
        if previous_at is not None and at <= previous_at:
            fail(f"{field}.side_profile[{point_index}].at must increase")
        previous_at = at
        ring: dict[str, Any] = {
            "ring_id": point_id,
            "at": at,
            "radius_m": positive_float(point.get("radius_m"), f"{field}.side_profile[{point_index}].radius_m"),
        }
        if "material_role" in point:
            ring["material_role"] = require_string(point.get("material_role"), f"{field}.side_profile[{point_index}].material_role")
        rings.append(ring)

    return {
        "axis": axis,
        "segments": segments,
        "material_role": source.get("material_role", "body"),
        "rings": rings,
        "radial_details": require_list(source.get("radial_details", []), f"{field}.radial_details"),
        "attachments": require_list(source.get("attachments", []), f"{field}.attachments"),
    }


def validate_profile_revolve_source(value: Any, field: str) -> None:
    stack = profile_revolve_to_radial_stack(value, field)
    validate_radial_stack_source(stack, field)


def validate_profile_revolve_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    known_terms = all_terms(terms)
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation != "profile_revolve":
            fail(f"{asset_id}.operation must be profile_revolve")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")
        validate_profile_revolve_source(asset.get("profile_revolve"), f"{asset_id}.profile_revolve")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")
        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")
        validate_claims(asset)


def validate_radial_stack_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    known_terms = all_terms(terms)
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation != "radial_stack":
            fail(f"{asset_id}.operation must be radial_stack")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")
        validate_radial_stack_source(asset.get("radial_stack"), f"{asset_id}.radial_stack")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")
        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")
        validate_claims(asset)


def validate_decorated_box(value: Any, field: str) -> None:
    box = require_object(value, field)
    require_string(box.get("part_id"), f"{field}.part_id")
    finite_vector(box.get("center_m"), f"{field}.center_m")
    positive_vector(box.get("dimensions_m"), f"{field}.dimensions_m")
    require_string(box.get("material_role"), f"{field}.material_role")


def validate_balustrade_collar(value: Any, field: str) -> None:
    collar = require_object(value, field)
    require_string(collar.get("part_id"), f"{field}.part_id")
    finite_vector(collar.get("center_m"), f"{field}.center_m")
    positive_float(collar.get("width_m"), f"{field}.width_m")
    positive_float(collar.get("radius_m"), f"{field}.radius_m")
    integer_at_least(collar.get("segments"), 8, f"{field}.segments")
    require_string(collar.get("material_role"), f"{field}.material_role")


def validate_balustrade_arch(value: Any, field: str) -> None:
    arch = require_object(value, field)
    require_string(arch.get("part_id"), f"{field}.part_id")
    finite_float(arch.get("center_x_m"), f"{field}.center_x_m")
    positive_float(arch.get("span_m"), f"{field}.span_m")
    finite_float(arch.get("spring_z_m"), f"{field}.spring_z_m")
    positive_float(arch.get("rise_m"), f"{field}.rise_m")
    finite_float(arch.get("front_y_m"), f"{field}.front_y_m")
    positive_float(arch.get("bevel_depth_m"), f"{field}.bevel_depth_m")
    positive_float(arch.get("leg_width_m"), f"{field}.leg_width_m")
    finite_float(arch.get("leg_bottom_z_m"), f"{field}.leg_bottom_z_m")
    require_string(arch.get("material_role"), f"{field}.material_role")


def validate_balustrade_quatrefoil(value: Any, field: str) -> None:
    motif = require_object(value, field)
    require_string(motif.get("part_prefix"), f"{field}.part_prefix")
    finite_vector(motif.get("center_m"), f"{field}.center_m")
    positive_float(motif.get("lobe_radius_m"), f"{field}.lobe_radius_m")
    positive_float(motif.get("lobe_offset_m"), f"{field}.lobe_offset_m")
    positive_float(motif.get("center_boss_radius_m"), f"{field}.center_boss_radius_m")
    positive_float(motif.get("depth_m"), f"{field}.depth_m")
    integer_at_least(motif.get("segments"), 8, f"{field}.segments")
    require_string(motif.get("material_role"), f"{field}.material_role")


def validate_decorated_balustrade_source(value: Any, field: str) -> None:
    source = require_object(value, field)
    rail = require_object(source.get("rail"), f"{field}.rail")
    require_string(rail.get("part_id"), f"{field}.rail.part_id")
    finite_vector(rail.get("center_m"), f"{field}.rail.center_m")
    rail_stack = require_object(rail.get("radial_stack"), f"{field}.rail.radial_stack")
    validate_radial_stack_source(rail_stack, f"{field}.rail.radial_stack")
    if rail_stack.get("axis") != "x":
        fail(f"{field}.rail.radial_stack.axis must be x")

    posts = require_object(source.get("posts"), f"{field}.posts")
    x_positions = require_list(posts.get("x_positions_m"), f"{field}.posts.x_positions_m")
    if len(x_positions) < 2:
        fail(f"{field}.posts.x_positions_m requires at least two posts")
    for index, value in enumerate(x_positions):
        finite_float(value, f"{field}.posts.x_positions_m[{index}]")
    finite_float(posts.get("y_m"), f"{field}.posts.y_m")
    post_stack = require_object(posts.get("radial_stack"), f"{field}.posts.radial_stack")
    validate_radial_stack_source(post_stack, f"{field}.posts.radial_stack")
    if post_stack.get("axis") != "z":
        fail(f"{field}.posts.radial_stack.axis must be z")

    for collar_index, collar in enumerate(require_list(source.get("collars"), f"{field}.collars")):
        validate_balustrade_collar(collar, f"{field}.collars[{collar_index}]")
    infill = require_object(source.get("infill"), f"{field}.infill")
    for box_index, box in enumerate(require_list(infill.get("frame_boxes"), f"{field}.infill.frame_boxes")):
        validate_decorated_box(box, f"{field}.infill.frame_boxes[{box_index}]")
    for arch_index, arch in enumerate(require_list(infill.get("pointed_arches"), f"{field}.infill.pointed_arches")):
        validate_balustrade_arch(arch, f"{field}.infill.pointed_arches[{arch_index}]")
    for motif_index, motif in enumerate(require_list(infill.get("quatrefoils"), f"{field}.infill.quatrefoils")):
        validate_balustrade_quatrefoil(motif, f"{field}.infill.quatrefoils[{motif_index}]")


def validate_decorated_balustrade_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    known_terms = all_terms(terms)
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation != "decorated_balustrade":
            fail(f"{asset_id}.operation must be decorated_balustrade")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")
        validate_decorated_balustrade_source(asset.get("decorated_balustrade"), f"{asset_id}.decorated_balustrade")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")
        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")
        validate_claims(asset)


def validate_blocky_box_part(value: Any, field: str) -> None:
    part = require_object(value, field)
    require_string(part.get("part_id"), f"{field}.part_id")
    positive_vector(part.get("size_m"), f"{field}.size_m", 2)
    increasing_range(part.get("z_range"), f"{field}.z_range")
    if "center_xy" in part:
        finite_vector(part.get("center_xy"), f"{field}.center_xy", 2)
    if "material_role" in part:
        require_string(part.get("material_role"), f"{field}.material_role")


def validate_blocky_cylinder_part(value: Any, field: str) -> None:
    part = require_object(value, field)
    require_string(part.get("part_id"), f"{field}.part_id")
    positive_float(part.get("radius_m"), f"{field}.radius_m")
    integer_at_least(part.get("segments"), 3, f"{field}.segments")
    increasing_range(part.get("z_range"), f"{field}.z_range")
    if "center_xy" in part:
        finite_vector(part.get("center_xy"), f"{field}.center_xy", 2)
    if "material_role" in part:
        require_string(part.get("material_role"), f"{field}.material_role")


def validate_blocky_ribs(value: Any, field: str) -> None:
    ribs = require_object(value, field)
    require_string(ribs.get("part_prefix"), f"{field}.part_prefix")
    integer_at_least(ribs.get("count"), 1, f"{field}.count")
    positive_float(ribs.get("core_radius_m"), f"{field}.core_radius_m")
    positive_float(ribs.get("rib_depth_m"), f"{field}.rib_depth_m")
    positive_float(ribs.get("rib_width_m"), f"{field}.rib_width_m")
    increasing_range(ribs.get("z_range"), f"{field}.z_range")
    finite_float(ribs.get("start_angle_degrees", 0.0), f"{field}.start_angle_degrees")
    if "material_role" in ribs:
        require_string(ribs.get("material_role"), f"{field}.material_role")


def validate_blocky_column_source(value: Any, field: str) -> None:
    column = require_object(value, field)
    axis = require_string(column.get("axis"), f"{field}.axis")
    if axis != "z":
        fail(f"{field}.axis only supports z in v0")
    validate_blocky_box_part(column.get("base"), f"{field}.base")
    validate_blocky_cylinder_part(column.get("lower_collar"), f"{field}.lower_collar")
    validate_blocky_cylinder_part(column.get("shaft_core"), f"{field}.shaft_core")
    validate_blocky_ribs(column.get("ribs"), f"{field}.ribs")
    validate_blocky_cylinder_part(column.get("upper_collar"), f"{field}.upper_collar")
    validate_blocky_box_part(column.get("cap"), f"{field}.cap")


def validate_blocky_shape_part(value: Any, field: str) -> list[str]:
    part = require_object(value, field)
    part_type = require_string(part.get("part_type"), f"{field}.part_type")
    if part_type == "box":
        validate_blocky_box_part(part, field)
        return [require_string(part.get("part_id"), f"{field}.part_id")]
    if part_type == "cylinder":
        validate_blocky_cylinder_part(part, field)
        return [require_string(part.get("part_id"), f"{field}.part_id")]
    if part_type == "radial_box_array":
        validate_blocky_ribs(part, field)
        part_prefix = require_string(part.get("part_prefix"), f"{field}.part_prefix")
        count = integer_at_least(part.get("count"), 1, f"{field}.count")
        return [f"{part_prefix}_{index:02d}" for index in range(count)]
    fail(f"unsupported blocky_shape part_type `{part_type}` at {field}")


def validate_blocky_shape_source(value: Any, field: str) -> None:
    shape = require_object(value, field)
    axis = require_string(shape.get("axis"), f"{field}.axis")
    if axis != "z":
        fail(f"{field}.axis only supports z in v0")
    parts = require_list(shape.get("parts"), f"{field}.parts")
    if not parts:
        fail(f"{field}.parts must not be empty")
    seen_part_ids: set[str] = set()
    for part_index, item in enumerate(parts):
        for part_id in validate_blocky_shape_part(item, f"{field}.parts[{part_index}]"):
            if part_id in seen_part_ids:
                fail(f"{field}.parts duplicate expanded part_id: {part_id}")
            seen_part_ids.add(part_id)


def validate_blocky_column_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    known_terms = all_terms(terms)
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation != "blocky_column":
            fail(f"{asset_id}.operation must be blocky_column")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")
        validate_blocky_column_source(asset.get("blocky_column"), f"{asset_id}.blocky_column")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")
        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")
        validate_claims(asset)


def validate_blocky_shape_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    known_terms = all_terms(terms)
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        operation = require_string(asset.get("operation"), f"{asset_id}.operation")
        if operation != "blocky_shape":
            fail(f"{asset_id}.operation must be blocky_shape")
        if operation not in operation_terms(terms):
            fail(f"{asset_id}.operation uses unknown geometry dictionary operation `{operation}`")
        validate_blocky_shape_source(asset.get("blocky_shape"), f"{asset_id}.blocky_shape")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        for connector_index, connector in enumerate(require_list(asset.get("connectors"), f"{asset_id}.connectors")):
            connector_id = require_string(connector, f"{asset_id}.connectors[{connector_index}]")
            if connector_id not in terms["connector"]:
                fail(f"{asset_id}.connectors[{connector_index}] uses unknown geometry dictionary connector `{connector_id}`")
        for tag_index, tag in enumerate(require_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")):
            semantic_tag = require_string(tag, f"{asset_id}.semantic_tags[{tag_index}]")
            if semantic_tag not in terms["semantic_geometry"]:
                fail(f"{asset_id}.semantic_tags[{tag_index}] uses unknown geometry dictionary semantic tag `{semantic_tag}`")
        for slot_index, slot in enumerate(require_list(asset.get("child_slots"), f"{asset_id}.child_slots")):
            require_string(slot, f"{asset_id}.child_slots[{slot_index}]")
        validate_claims(asset)


def validate_measured_proof_primitive(part: Any, field: str) -> None:
    item = require_object(part, field)
    primitive = require_string(item.get("primitive"), f"{field}.primitive")
    require_string(item.get("name"), f"{field}.name")
    if primitive == "cube":
        finite_vector(item.get("location_m"), f"{field}.location_m")
        positive_vector(item.get("dimensions_m"), f"{field}.dimensions_m")
    elif primitive == "cylinder":
        finite_vector(item.get("location_m"), f"{field}.location_m")
        positive_float(item.get("radius_m"), f"{field}.radius_m")
        positive_float(item.get("depth_m"), f"{field}.depth_m")
        vertices = item.get("vertices")
        if not isinstance(vertices, int) or isinstance(vertices, bool) or vertices < 3:
            fail(f"{field}.vertices must be an integer >= 3")
    elif primitive == "curve":
        positive_float(item.get("span_m"), f"{field}.span_m")
        finite_float(item.get("spring_z_m"), f"{field}.spring_z_m")
        finite_float(item.get("rise_m"), f"{field}.rise_m")
        finite_float(item.get("y_m"), f"{field}.y_m")
        positive_float(item.get("bevel_depth_m"), f"{field}.bevel_depth_m")
        curve_kind = item.get("curve_kind", "pointed")
        if curve_kind not in {"pointed", "round"}:
            fail(f"{field}.curve_kind unsupported: {curve_kind}")
    else:
        fail(f"{field}.primitive unsupported: {primitive}")


def validate_measured_bundle_terms(bundle: dict[str, Any], terms: dict[str, set[str]]) -> None:
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    seen_asset_ids: set[str] = set()
    known_terms = all_terms(terms)
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)

        source_version = require_string(asset.get("source_version"), f"{asset_id}.source_version")
        if source_version not in {"v1", "v2"}:
            fail(f"{asset_id}.source_version must be v1 or v2")
        if "source_script" in asset:
            fail(f"{asset_id}.source_script is retired; use legacy_source_script for provenance")
        require_string(asset.get("legacy_source_script"), f"{asset_id}.legacy_source_script")
        dims = validate_dimensions_object(asset.get("dimensions_m"), f"{asset_id}.dimensions_m")
        bounds_m = validate_bounds_object(asset.get("bounds_m"), f"{asset_id}.bounds_m")
        validate_bounds_match_dimensions(bounds_m, dims, asset_id)

        if not require_list(asset.get("source_measurement_refs"), f"{asset_id}.source_measurement_refs"):
            fail(f"{asset_id}.source_measurement_refs must not be empty")
        require_known_terms(asset.get("geometry_terms_used"), known_terms, f"{asset_id}.geometry_terms_used")
        require_known_terms(asset.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_terms")
        require_known_terms(asset.get("operations"), operation_terms(terms), f"{asset_id}.operations")
        require_known_terms(asset.get("semantic_roles"), terms["semantic_geometry"], f"{asset_id}.semantic_roles")

        sockets = require_list(asset.get("sockets"), f"{asset_id}.sockets")
        if not sockets:
            fail(f"{asset_id}.sockets must not be empty")
        seen_sockets: set[str] = set()
        for socket_index, socket in enumerate(sockets):
            socket_obj = require_object(socket, f"{asset_id}.sockets[{socket_index}]")
            socket_id = require_string(socket_obj.get("socket_id"), f"{asset_id}.sockets[{socket_index}].socket_id")
            if socket_id in seen_sockets:
                fail(f"{asset_id}.sockets duplicate socket_id: {socket_id}")
            seen_sockets.add(socket_id)
            connector_term = require_string(socket_obj.get("connector_term"), f"{asset_id}.sockets[{socket_index}].connector_term")
            if connector_term not in terms["connector"]:
                fail(f"{asset_id}.sockets[{socket_index}].connector_term uses unknown connector `{connector_term}`")
            finite_vector(socket_obj.get("position_m"), f"{asset_id}.sockets[{socket_index}].position_m")
            validate_unit_direction(socket_obj.get("direction"), f"{asset_id}.sockets[{socket_index}].direction")
            require_string(socket_obj.get("role"), f"{asset_id}.sockets[{socket_index}].role")

        primitives = require_list(asset.get("proof_primitives"), f"{asset_id}.proof_primitives")
        if not primitives:
            fail(f"{asset_id}.proof_primitives must not be empty")
        for primitive_index, part in enumerate(primitives):
            validate_measured_proof_primitive(part, f"{asset_id}.proof_primitives[{primitive_index}]")

        require_false_claims(
            asset.get("no_claims"),
            f"{asset_id}.no_claims",
            {"production_approval", "structural_safety", "fabrication_ready", "gym_museum_approval", "historical_accuracy"},
        )


def polygon_points(sides: int, radius: float) -> list[list[float]]:
    if sides < 3:
        fail("polygon sides must be >= 3")
    return [
        [
            round(math.cos(math.tau * index / sides) * radius, 6),
            round(math.sin(math.tau * index / sides) * radius, 6),
        ]
        for index in range(sides)
    ]


def capsule_points(length: float, radius: float, segments: int) -> list[list[float]]:
    if segments < 6:
        fail("capsule segments must be >= 6")
    half_straight = max(length * 0.5 - radius, 0.001)
    half_segments = max(segments // 2, 3)
    points: list[list[float]] = []
    for index in range(half_segments + 1):
        angle = -math.pi * 0.5 + math.pi * index / half_segments
        points.append([round(half_straight + math.cos(angle) * radius, 6), round(math.sin(angle) * radius, 6)])
    for index in range(half_segments + 1):
        angle = math.pi * 0.5 + math.pi * index / half_segments
        points.append([round(-half_straight + math.cos(angle) * radius, 6), round(math.sin(angle) * radius, 6)])
    return points


def ellipse_point(angle: float, radius_x: float, radius_y: float) -> list[float]:
    return [round(math.cos(angle) * radius_x, 6), round(math.sin(angle) * radius_y, 6)]


def star_polygon_points(point_count: int, outer_radius_x: float, outer_radius_y: float, inner_radius_x: float, inner_radius_y: float, flat_edge_ratio: float) -> list[list[float]]:
    if inner_radius_x >= outer_radius_x:
        fail("profile.params.inner_radius_x must be less than outer_radius_x")
    if inner_radius_y >= outer_radius_y:
        fail("profile.params.inner_radius_y must be less than outer_radius_y")

    step = math.tau / point_count
    half_step = step * 0.5
    points: list[list[float]] = []
    if flat_edge_ratio == 0.0:
        for index in range(point_count):
            angle = step * index
            points.append(ellipse_point(angle, outer_radius_x, outer_radius_y))
            points.append(ellipse_point(angle + half_step, inner_radius_x, inner_radius_y))
        return points

    flat_half_angle = half_step * flat_edge_ratio
    for index in range(point_count):
        angle = step * index
        points.append(ellipse_point(angle - flat_half_angle, outer_radius_x, outer_radius_y))
        points.append(ellipse_point(angle + flat_half_angle, outer_radius_x, outer_radius_y))
        points.append(ellipse_point(angle + half_step, inner_radius_x, inner_radius_y))
    return points


def profile_points(profile: dict[str, Any]) -> list[list[float]]:
    profile_type = require_string(profile.get("type"), "profile.type")
    params = require_object(profile.get("params", {}), "profile.params")
    if profile_type == "rectangle":
        half_width = positive_float(params.get("width"), "profile.params.width") * 0.5
        half_depth = positive_float(params.get("depth"), "profile.params.depth") * 0.5
        return [[-half_width, -half_depth], [half_width, -half_depth], [half_width, half_depth], [-half_width, half_depth]]
    if profile_type == "square":
        half_size = positive_float(params.get("size"), "profile.params.size") * 0.5
        return [[-half_size, -half_size], [half_size, -half_size], [half_size, half_size], [-half_size, half_size]]
    if profile_type == "circle":
        return polygon_points(int(params.get("segments", 24)), positive_float(params.get("radius"), "profile.params.radius"))
    if profile_type == "triangle":
        half_width = positive_float(params.get("width"), "profile.params.width") * 0.5
        half_depth = positive_float(params.get("depth"), "profile.params.depth") * 0.5
        return [[-half_width, -half_depth], [half_width, -half_depth], [0.0, half_depth]]
    if profile_type == "trapezoid":
        bottom = positive_float(params.get("bottom_width"), "profile.params.bottom_width") * 0.5
        top = positive_float(params.get("top_width"), "profile.params.top_width") * 0.5
        half_depth = positive_float(params.get("depth"), "profile.params.depth") * 0.5
        return [[-bottom, -half_depth], [bottom, -half_depth], [top, half_depth], [-top, half_depth]]
    if profile_type == "regular_polygon":
        return polygon_points(int(params.get("sides")), positive_float(params.get("radius"), "profile.params.radius"))
    if profile_type == "octagon":
        return polygon_points(8, positive_float(params.get("radius"), "profile.params.radius"))
    if profile_type == "capsule":
        return capsule_points(
            positive_float(params.get("length"), "profile.params.length"),
            positive_float(params.get("radius"), "profile.params.radius"),
            int(params.get("segments", 12)),
        )
    if profile_type == "star_polygon":
        result = star_polygon_points(
            integer_at_least(params.get("points"), 3, "profile.params.points"),
            positive_float(params.get("outer_radius_x"), "profile.params.outer_radius_x"),
            positive_float(params.get("outer_radius_y"), "profile.params.outer_radius_y"),
            positive_float(params.get("inner_radius_x"), "profile.params.inner_radius_x"),
            positive_float(params.get("inner_radius_y"), "profile.params.inner_radius_y"),
            ratio_less_than_one(params.get("flat_edge_ratio", 0.0), "profile.params.flat_edge_ratio"),
        )
        winding = params.get("winding", "counter_clockwise")
        if winding not in {"clockwise", "counter_clockwise"}:
            fail("profile.params.winding must be clockwise or counter_clockwise")
        if winding == "clockwise":
            result = list(reversed(result))
        return result
    if profile_type == "custom_polygon":
        points = require_list(params.get("points"), "profile.params.points")
        if len(points) < 3:
            fail("profile.params.points requires at least 3 points")
        winding = params.get("winding", "counter_clockwise")
        if winding not in {"clockwise", "counter_clockwise"}:
            fail("profile.params.winding must be clockwise or counter_clockwise")
        result = [finite_vector(point, f"profile.params.points[{index}]", 2) for index, point in enumerate(points)]
        if winding == "clockwise":
            result = list(reversed(result))
        return result
    fail(f"unsupported profile type: {profile_type}")


def extrude_mesh(points: list[list[float]], height: float) -> Mesh:
    if len(points) < 3:
        fail("extrude requires at least 3 profile points")
    bottom = [[round(x, 6), round(y, 6), 0.0] for x, y in points]
    top = [[round(x, 6), round(y, 6), round(height, 6)] for x, y in points]
    vertices = bottom + top
    count = len(points)
    faces: list[list[int]] = [list(reversed(range(count))), list(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append([index, nxt, nxt + count, index + count])
    return Mesh(vertices=vertices, faces=faces)


def box_mesh(location: list[float], size: list[float]) -> Mesh:
    cx, cy, cz = location
    half_x, half_y, half_z = [value * 0.5 for value in size]
    min_x, max_x = round(cx - half_x, 6), round(cx + half_x, 6)
    min_y, max_y = round(cy - half_y, 6), round(cy + half_y, 6)
    min_z, max_z = round(cz - half_z, 6), round(cz + half_z, 6)
    return Mesh(
        vertices=[
            [min_x, min_y, min_z],
            [max_x, min_y, min_z],
            [max_x, max_y, min_z],
            [min_x, max_y, min_z],
            [min_x, min_y, max_z],
            [max_x, min_y, max_z],
            [max_x, max_y, max_z],
            [min_x, max_y, max_z],
        ],
        faces=[
            [3, 2, 1, 0],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [1, 2, 6, 5],
            [2, 3, 7, 6],
            [3, 0, 4, 7],
        ],
    )


def cylinder_mesh(location: list[float], radius: float, depth: float, segments: int) -> Mesh:
    if segments < 3:
        fail("cylinder segments must be >= 3")
    mesh = extrude_mesh(polygon_points(segments, radius), depth)
    return mesh.translated([location[0], location[1], round(location[2] - depth * 0.5, 6)])


def oriented_box_mesh(center: list[float], radial_axis: list[float], tangent_axis: list[float], size: list[float]) -> Mesh:
    cx, cy, cz = center
    half_radial = size[0] * 0.5
    half_tangent = size[1] * 0.5
    half_z = size[2] * 0.5
    bottom: list[list[float]] = []
    top: list[list[float]] = []
    for radial_sign, tangent_sign in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)):
        x = cx + radial_axis[0] * radial_sign * half_radial + tangent_axis[0] * tangent_sign * half_tangent
        y = cy + radial_axis[1] * radial_sign * half_radial + tangent_axis[1] * tangent_sign * half_tangent
        bottom.append([round(x, 6), round(y, 6), round(cz - half_z, 6)])
        top.append([round(x, 6), round(y, 6), round(cz + half_z, 6)])
    return Mesh(
        vertices=bottom + top,
        faces=[
            [3, 2, 1, 0],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [1, 2, 6, 5],
            [2, 3, 7, 6],
            [3, 0, 4, 7],
        ],
    )


def measured_curve_points(part: dict[str, Any]) -> list[list[float]]:
    span = positive_float(part.get("span_m"), "curve.span_m")
    spring_z = finite_float(part.get("spring_z_m"), "curve.spring_z_m")
    rise = finite_float(part.get("rise_m"), "curve.rise_m")
    y = finite_float(part.get("y_m"), "curve.y_m")
    points: list[list[float]] = []
    if part.get("curve_kind") == "round":
        radius = span * 0.5
        for index in range(29):
            angle = math.pi - math.pi * index / 28
            points.append([round(math.cos(angle) * radius, 6), y, round(spring_z + math.sin(angle) * radius, 6)])
    else:
        half = span * 0.5
        for index in range(19):
            t = index / 18
            points.append([round(-half + half * t, 6), y, round(spring_z + rise * (1.0 - (1.0 - t) ** 2), 6)])
        for index in range(1, 19):
            t = index / 18
            points.append([round(half * t, 6), y, round(spring_z + rise * (1.0 - t**2), 6)])
    return points


def curve_strip_mesh(part: dict[str, Any]) -> Mesh:
    points = measured_curve_points(part)
    bevel = positive_float(part.get("bevel_depth_m"), "curve.bevel_depth_m")
    boxes: list[Mesh] = []
    for start, end in zip(points, points[1:], strict=False):
        min_x, max_x = min(start[0], end[0]), max(start[0], end[0])
        min_z, max_z = min(start[2], end[2]), max(start[2], end[2])
        center = [
            round((min_x + max_x) * 0.5, 6),
            start[1],
            round((min_z + max_z) * 0.5, 6),
        ]
        size = [
            round(max(max_x - min_x, bevel * 2.0), 6),
            round(bevel * 2.0, 6),
            round(max(max_z - min_z, bevel * 2.0), 6),
        ]
        boxes.append(box_mesh(center, size))
    return merged_mesh(boxes)


def xz_profile_extrude_mesh(points: list[list[float]], center: list[float], depth_y: float) -> Mesh:
    if len(points) < 3:
        fail("xz profile extrusion requires at least 3 profile points")
    cx, cy, cz = center
    half_depth = depth_y * 0.5
    front = [[round(cx + x, 6), round(cy - half_depth, 6), round(cz + z, 6)] for x, z in points]
    back = [[round(cx + x, 6), round(cy + half_depth, 6), round(cz + z, 6)] for x, z in points]
    vertices = front + back
    count = len(points)
    faces: list[list[int]] = [list(reversed(range(count))), list(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append([index, nxt, nxt + count, index + count])
    return Mesh(vertices=vertices, faces=faces)


def circle_xz_profile_points(radius: float, segments: int) -> list[list[float]]:
    return polygon_points(segments, radius)


def loft_mesh(sections: list[dict[str, Any]]) -> Mesh:
    if len(sections) < 2:
        fail("loft_sections requires at least two sections")
    rings: list[list[list[float]]] = []
    for index, section in enumerate(sections):
        at = finite_float(section.get("at"), f"sections[{index}].at")
        points = profile_points(require_object(section.get("profile"), f"sections[{index}].profile"))
        rings.append([[round(x, 6), round(y, 6), round(at, 6)] for x, y in points])
    ring_size = len(rings[0])
    if any(len(ring) != ring_size for ring in rings):
        fail("loft_sections requires matching profile vertex counts")
    vertices = [vertex for ring in rings for vertex in ring]
    faces: list[list[int]] = [list(reversed(range(ring_size)))]
    last_start = (len(rings) - 1) * ring_size
    faces.append(list(range(last_start, last_start + ring_size)))
    for ring_index in range(len(rings) - 1):
        start = ring_index * ring_size
        next_start = (ring_index + 1) * ring_size
        for vertex_index in range(ring_size):
            nxt = (vertex_index + 1) % ring_size
            faces.append([start + vertex_index, start + nxt, next_start + nxt, next_start + vertex_index])
    return Mesh(vertices=vertices, faces=faces)


def section_stack_mesh(stack: dict[str, Any]) -> tuple[Mesh, dict[str, Any], list[dict[str, Any]]]:
    axis = require_string(stack.get("axis"), "section_stack.axis")
    if axis != "z":
        fail("section_stack.axis only supports z in v0")
    rings_source = require_list(stack.get("rings"), "section_stack.rings")
    if len(rings_source) < 2:
        fail("section_stack.rings requires at least two rings")

    rings: list[dict[str, Any]] = []
    vertices: list[list[float]] = []
    ring_size: int | None = None
    previous_at: float | None = None
    for ring_index, ring in enumerate(rings_source):
        ring_obj = require_object(ring, f"section_stack.rings[{ring_index}]")
        ring_id = require_string(ring_obj.get("ring_id"), f"section_stack.rings[{ring_index}].ring_id")
        at = finite_float(ring_obj.get("at"), f"section_stack.rings[{ring_index}].at")
        if previous_at is not None and at <= previous_at:
            fail(f"section_stack.rings[{ring_index}].at must increase")
        previous_at = at
        points = profile_points(require_object(ring_obj.get("profile"), f"section_stack.rings[{ring_index}].profile"))
        if ring_size is None:
            ring_size = len(points)
        elif len(points) != ring_size:
            fail("section_stack.rings requires matching profile vertex counts")
        start = len(vertices)
        vertices.extend([[round(x, 6), round(y, 6), at] for x, y in points])
        rings.append(
            {
                "ring_id": ring_id,
                "at": at,
                "profile_type": require_string(require_object(ring_obj.get("profile"), f"section_stack.rings[{ring_index}].profile").get("type"), f"section_stack.rings[{ring_index}].profile.type"),
                "vertex_range": [start, len(vertices) - 1],
            }
        )

    assert ring_size is not None
    last_start = (len(rings) - 1) * ring_size
    bottom_center_index = len(vertices)
    vertices.append(ring_center(vertices[0:ring_size]))
    top_center_index = len(vertices)
    vertices.append(ring_center(vertices[last_start : last_start + ring_size]))
    faces: list[list[int]] = []
    for vertex_index in range(ring_size):
        nxt = (vertex_index + 1) % ring_size
        faces.append([bottom_center_index, nxt, vertex_index])
    for vertex_index in range(ring_size):
        nxt = (vertex_index + 1) % ring_size
        faces.append([top_center_index, last_start + vertex_index, last_start + nxt])
    for ring_index in range(len(rings) - 1):
        start = ring_index * ring_size
        next_start = (ring_index + 1) * ring_size
        for vertex_index in range(ring_size):
            nxt = (vertex_index + 1) % ring_size
            faces.append([start + vertex_index, start + nxt, next_start + nxt, next_start + vertex_index])

    parts = [
        {
            "part_id": "section_stack_body",
            "source_primitive": "section_stack",
            "vertex_range": [0, len(vertices) - 1],
            "face_range": [0, len(faces) - 1],
        }
    ]
    metadata = {
        "axis": axis,
        "ring_count": len(rings),
        "rings": rings,
        "cap_triangulation": "center_fan",
        "bottom_center_vertex": bottom_center_index,
        "top_center_vertex": top_center_index,
    }
    return Mesh(vertices=vertices, faces=faces), metadata, parts


def radial_stack_body_mesh(stack: dict[str, Any]) -> tuple[Mesh, dict[str, Any]]:
    axis = require_string(stack.get("axis"), "radial_stack.axis")
    if axis not in {"x", "y", "z"}:
        fail("radial_stack.axis must be x, y, or z")
    segments = integer_at_least(stack.get("segments"), 8, "radial_stack.segments")
    rings_source = require_list(stack.get("rings"), "radial_stack.rings")
    if len(rings_source) < 2:
        fail("radial_stack.rings requires at least two rings")

    vertices: list[list[float]] = []
    rings: list[dict[str, Any]] = []
    previous_at: float | None = None
    for ring_index, item in enumerate(rings_source):
        ring = require_object(item, f"radial_stack.rings[{ring_index}]")
        ring_id = require_string(ring.get("ring_id"), f"radial_stack.rings[{ring_index}].ring_id")
        at = finite_float(ring.get("at"), f"radial_stack.rings[{ring_index}].at")
        if previous_at is not None and at <= previous_at:
            fail(f"radial_stack.rings[{ring_index}].at must increase")
        previous_at = at
        radius = positive_float(ring.get("radius_m"), f"radial_stack.rings[{ring_index}].radius_m")
        start = len(vertices)
        for segment_index in range(segments):
            angle = math.tau * segment_index / segments
            vertices.append(radial_stack_vertex(axis, at, radius, angle))
        ring_record: dict[str, Any] = {
            "ring_id": ring_id,
            "at": at,
            "radius_m": radius,
            "vertex_range": [start, len(vertices) - 1],
        }
        if isinstance(ring.get("material_role"), str) and ring["material_role"]:
            ring_record["material_role"] = ring["material_role"]
        rings.append(ring_record)

    last_start = (len(rings) - 1) * segments
    bottom_center_index = len(vertices)
    vertices.append(ring_center(vertices[0:segments]))
    top_center_index = len(vertices)
    vertices.append(ring_center(vertices[last_start : last_start + segments]))

    faces: list[list[int]] = []
    for segment_index in range(segments):
        nxt = (segment_index + 1) % segments
        faces.append([bottom_center_index, nxt, segment_index])
    for segment_index in range(segments):
        nxt = (segment_index + 1) % segments
        faces.append([top_center_index, last_start + segment_index, last_start + nxt])
    for ring_index in range(len(rings) - 1):
        start = ring_index * segments
        next_start = (ring_index + 1) * segments
        for segment_index in range(segments):
            nxt = (segment_index + 1) % segments
            faces.append([start + segment_index, start + nxt, next_start + nxt, next_start + segment_index])

    metadata = {
        "axis": axis,
        "grammar": "radial_stack_v0",
        "segments": segments,
        "ring_count": len(rings),
        "rings": rings,
        "cap_triangulation": "center_fan",
        "bottom_center_vertex": bottom_center_index,
        "top_center_vertex": top_center_index,
    }
    return Mesh(vertices=vertices, faces=faces), metadata


def radial_stack_vertex(axis: str, at: float, radius: float, angle: float) -> list[float]:
    first = round(math.cos(angle) * radius, 6)
    second = round(math.sin(angle) * radius, 6)
    if axis == "x":
        return [at, first, second]
    if axis == "y":
        return [first, at, second]
    if axis == "z":
        return [first, second, at]
    fail("radial_stack.axis must be x, y, or z")


def append_radial_stack_attachment(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], attachment: dict[str, Any], field: str) -> dict[str, Any]:
    part_type = require_string(attachment.get("part_type"), f"{field}.part_type")
    if part_type != "box":
        fail(f"{field}.part_type unsupported: {part_type}")
    part_id = require_string(attachment.get("part_id"), f"{field}.part_id")
    append_mesh_part(parts_mesh, mesh_parts, part_id, "box", attachment.get("material_role"), blocky_box_part_mesh(attachment, field))
    return {
        "part_type": "box",
        "part_id": part_id,
        "z_range": increasing_range(attachment.get("z_range"), f"{field}.z_range"),
        "center_xy": part_center_xy(attachment, field),
    }


def radial_stack_mesh(stack: dict[str, Any]) -> tuple[Mesh, dict[str, Any], list[dict[str, Any]]]:
    body_mesh, body_metadata = radial_stack_body_mesh(stack)
    parts_mesh: list[Mesh] = []
    mesh_parts: list[dict[str, Any]] = []
    append_mesh_part(parts_mesh, mesh_parts, "radial_stack_body", "radial_stack", stack.get("material_role", "body"), body_mesh)

    radial_details: list[dict[str, Any]] = []
    for detail_index, item in enumerate(require_list(stack.get("radial_details", []), "radial_stack.radial_details")):
        detail = require_object(item, f"radial_stack.radial_details[{detail_index}]")
        detail_type = require_string(detail.get("detail_type"), f"radial_stack.radial_details[{detail_index}].detail_type")
        if detail_type != "radial_box_array":
            fail(f"radial_stack.radial_details[{detail_index}].detail_type unsupported: {detail_type}")
        radial_details.append({"detail_type": detail_type, **append_radial_box_array(parts_mesh, mesh_parts, detail, f"radial_stack.radial_details[{detail_index}]")})

    attachments: list[dict[str, Any]] = []
    for attachment_index, item in enumerate(require_list(stack.get("attachments", []), "radial_stack.attachments")):
        attachment = require_object(item, f"radial_stack.attachments[{attachment_index}]")
        attachments.append(append_radial_stack_attachment(parts_mesh, mesh_parts, attachment, f"radial_stack.attachments[{attachment_index}]"))

    metadata = {
        **body_metadata,
        "assembly": "revolved_body_with_named_detail_parts",
        "body_part_id": "radial_stack_body",
        "radial_detail_count": len(radial_details),
        "radial_details": radial_details,
        "attachment_count": len(attachments),
        "attachments": attachments,
        "part_count": len(mesh_parts),
    }
    return merged_mesh(parts_mesh), metadata, mesh_parts


def profile_revolve_mesh(source: dict[str, Any]) -> tuple[Mesh, dict[str, Any], list[dict[str, Any]]]:
    stack = profile_revolve_to_radial_stack(source, "profile_revolve")
    mesh, stack_metadata, mesh_parts = radial_stack_mesh(stack)
    for part in mesh_parts:
        if part.get("part_id") == "radial_stack_body":
            part["part_id"] = "profile_revolve_body"
            part["source_primitive"] = "profile_revolve"
    profile_points_metadata = []
    for point, ring in zip(require_list(source.get("side_profile"), "profile_revolve.side_profile"), stack_metadata["rings"], strict=True):
        point_obj = require_object(point, "profile_revolve.side_profile[]")
        profile_points_metadata.append(
            {
                "point_id": require_string(point_obj.get("point_id"), "profile_revolve.side_profile[].point_id"),
                "at": ring["at"],
                "radius_m": ring["radius_m"],
                "vertex_range": ring["vertex_range"],
            }
        )
    metadata = {
        **stack_metadata,
        "grammar": "profile_revolve_v0",
        "source_math": "surface_of_revolution",
        "side_profile_coordinate_model": "axis_position_and_radius_m",
        "profile_point_count": len(profile_points_metadata),
        "side_profile": profile_points_metadata,
        "body_part_id": "profile_revolve_body",
        "radial_stack_compatible": True,
    }
    return mesh, metadata, mesh_parts


def append_decorated_radial_stack_part(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], part_id: str, stack: dict[str, Any], center: list[float], material_role: Any) -> None:
    mesh, _, _ = radial_stack_mesh(stack)
    append_mesh_part(parts_mesh, mesh_parts, part_id, "radial_stack", material_role, mesh.translated(center))


def append_balustrade_collar(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], collar: dict[str, Any], field: str) -> None:
    width = positive_float(collar.get("width_m"), f"{field}.width_m")
    radius = positive_float(collar.get("radius_m"), f"{field}.radius_m")
    stack = {
        "axis": "x",
        "segments": integer_at_least(collar.get("segments"), 8, f"{field}.segments"),
        "rings": [
            {"ring_id": "collar_start", "at": round(width * -0.5, 6), "radius_m": radius},
            {"ring_id": "collar_end", "at": round(width * 0.5, 6), "radius_m": radius},
        ],
    }
    append_decorated_radial_stack_part(
        parts_mesh,
        mesh_parts,
        require_string(collar.get("part_id"), f"{field}.part_id"),
        stack,
        finite_vector(collar.get("center_m"), f"{field}.center_m"),
        collar.get("material_role"),
    )


def append_balustrade_arch(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], arch: dict[str, Any], field: str) -> int:
    part_id = require_string(arch.get("part_id"), f"{field}.part_id")
    center_x = finite_float(arch.get("center_x_m"), f"{field}.center_x_m")
    span = positive_float(arch.get("span_m"), f"{field}.span_m")
    spring_z = finite_float(arch.get("spring_z_m"), f"{field}.spring_z_m")
    leg_bottom = finite_float(arch.get("leg_bottom_z_m"), f"{field}.leg_bottom_z_m")
    if spring_z <= leg_bottom:
        fail(f"{field}.spring_z_m must be above leg_bottom_z_m")
    y = finite_float(arch.get("front_y_m"), f"{field}.front_y_m")
    bevel = positive_float(arch.get("bevel_depth_m"), f"{field}.bevel_depth_m")
    material_role = arch.get("material_role")
    arch_mesh = curve_strip_mesh(
        {
            "span_m": span,
            "spring_z_m": spring_z,
            "rise_m": positive_float(arch.get("rise_m"), f"{field}.rise_m"),
            "y_m": y,
            "bevel_depth_m": bevel,
            "curve_kind": "pointed",
        }
    ).translated([center_x, 0.0, 0.0])
    append_mesh_part(parts_mesh, mesh_parts, f"{part_id}_curve", "pointed_arch_profile", material_role, arch_mesh)

    leg_width = positive_float(arch.get("leg_width_m"), f"{field}.leg_width_m")
    leg_height = round(spring_z - leg_bottom, 6)
    for side, sign in (("left", -1.0), ("right", 1.0)):
        append_mesh_part(
            parts_mesh,
            mesh_parts,
            f"{part_id}_{side}_jamb",
            "box",
            material_role,
            box_mesh(
                [round(center_x + sign * span * 0.5, 6), y, round((spring_z + leg_bottom) * 0.5, 6)],
                [leg_width, round(bevel * 2.0, 6), leg_height],
            ),
        )
    return 3


def append_balustrade_quatrefoil(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], motif: dict[str, Any], field: str) -> int:
    prefix = require_string(motif.get("part_prefix"), f"{field}.part_prefix")
    center = finite_vector(motif.get("center_m"), f"{field}.center_m")
    radius = positive_float(motif.get("lobe_radius_m"), f"{field}.lobe_radius_m")
    offset = positive_float(motif.get("lobe_offset_m"), f"{field}.lobe_offset_m")
    boss_radius = positive_float(motif.get("center_boss_radius_m"), f"{field}.center_boss_radius_m")
    depth = positive_float(motif.get("depth_m"), f"{field}.depth_m")
    segments = integer_at_least(motif.get("segments"), 8, f"{field}.segments")
    material_role = motif.get("material_role")
    lobe_points = circle_xz_profile_points(radius, segments)
    lobe_offsets = [
        ("north", [0.0, 0.0, offset]),
        ("east", [offset, 0.0, 0.0]),
        ("south", [0.0, 0.0, -offset]),
        ("west", [-offset, 0.0, 0.0]),
    ]
    for label, local in lobe_offsets:
        append_mesh_part(
            parts_mesh,
            mesh_parts,
            f"{prefix}_{label}_lobe",
            "quatrefoil_lobe",
            material_role,
            xz_profile_extrude_mesh(lobe_points, [round(center[0] + local[0], 6), center[1], round(center[2] + local[2], 6)], depth),
        )
    append_mesh_part(
        parts_mesh,
        mesh_parts,
        f"{prefix}_center_boss",
        "rosette_boss",
        material_role,
        xz_profile_extrude_mesh(circle_xz_profile_points(boss_radius, segments), center, depth),
    )
    return 5


def decorated_balustrade_mesh(source: dict[str, Any]) -> tuple[Mesh, dict[str, Any], list[dict[str, Any]]]:
    parts_mesh: list[Mesh] = []
    mesh_parts: list[dict[str, Any]] = []

    rail = require_object(source.get("rail"), "decorated_balustrade.rail")
    rail_stack = require_object(rail.get("radial_stack"), "decorated_balustrade.rail.radial_stack")
    append_decorated_radial_stack_part(
        parts_mesh,
        mesh_parts,
        require_string(rail.get("part_id"), "decorated_balustrade.rail.part_id"),
        rail_stack,
        finite_vector(rail.get("center_m"), "decorated_balustrade.rail.center_m"),
        rail_stack.get("material_role", rail.get("material_role", "rail")),
    )

    posts = require_object(source.get("posts"), "decorated_balustrade.posts")
    post_stack = require_object(posts.get("radial_stack"), "decorated_balustrade.posts.radial_stack")
    y_m = finite_float(posts.get("y_m"), "decorated_balustrade.posts.y_m")
    post_positions = [finite_float(value, f"decorated_balustrade.posts.x_positions_m[{index}]") for index, value in enumerate(require_list(posts.get("x_positions_m"), "decorated_balustrade.posts.x_positions_m"))]
    for post_index, x_m in enumerate(post_positions):
        append_decorated_radial_stack_part(
            parts_mesh,
            mesh_parts,
            f"post_{post_index:02d}_body",
            post_stack,
            [x_m, y_m, 0.0],
            post_stack.get("material_role", posts.get("material_role", "post")),
        )

    for collar_index, collar in enumerate(require_list(source.get("collars"), "decorated_balustrade.collars")):
        append_balustrade_collar(parts_mesh, mesh_parts, require_object(collar, f"decorated_balustrade.collars[{collar_index}]"), f"decorated_balustrade.collars[{collar_index}]")

    infill = require_object(source.get("infill"), "decorated_balustrade.infill")
    for box_index, box in enumerate(require_list(infill.get("frame_boxes"), "decorated_balustrade.infill.frame_boxes")):
        item = require_object(box, f"decorated_balustrade.infill.frame_boxes[{box_index}]")
        append_mesh_part(
            parts_mesh,
            mesh_parts,
            require_string(item.get("part_id"), f"decorated_balustrade.infill.frame_boxes[{box_index}].part_id"),
            "box",
            item.get("material_role"),
            box_mesh(
                finite_vector(item.get("center_m"), f"decorated_balustrade.infill.frame_boxes[{box_index}].center_m"),
                positive_vector(item.get("dimensions_m"), f"decorated_balustrade.infill.frame_boxes[{box_index}].dimensions_m"),
            ),
        )

    arch_part_count = 0
    for arch_index, arch in enumerate(require_list(infill.get("pointed_arches"), "decorated_balustrade.infill.pointed_arches")):
        arch_part_count += append_balustrade_arch(parts_mesh, mesh_parts, require_object(arch, f"decorated_balustrade.infill.pointed_arches[{arch_index}]"), f"decorated_balustrade.infill.pointed_arches[{arch_index}]")

    quatrefoil_part_count = 0
    for motif_index, motif in enumerate(require_list(infill.get("quatrefoils"), "decorated_balustrade.infill.quatrefoils")):
        quatrefoil_part_count += append_balustrade_quatrefoil(parts_mesh, mesh_parts, require_object(motif, f"decorated_balustrade.infill.quatrefoils[{motif_index}]"), f"decorated_balustrade.infill.quatrefoils[{motif_index}]")

    metadata = {
        "grammar": "decorated_balustrade_v0",
        "assembly": "named_radial_stack_and_front_profile_parts",
        "rail_axis": "x",
        "rail_part_id": require_string(rail.get("part_id"), "decorated_balustrade.rail.part_id"),
        "post_count": len(post_positions),
        "collar_count": len(require_list(source.get("collars"), "decorated_balustrade.collars")),
        "frame_box_count": len(require_list(infill.get("frame_boxes"), "decorated_balustrade.infill.frame_boxes")),
        "pointed_arch_count": len(require_list(infill.get("pointed_arches"), "decorated_balustrade.infill.pointed_arches")),
        "pointed_arch_part_count": arch_part_count,
        "quatrefoil_count": len(require_list(infill.get("quatrefoils"), "decorated_balustrade.infill.quatrefoils")),
        "quatrefoil_part_count": quatrefoil_part_count,
        "part_count": len(mesh_parts),
    }
    return merged_mesh(parts_mesh), metadata, mesh_parts


def ring_center(ring: list[list[float]]) -> list[float]:
    if not ring:
        fail("cannot calculate center for empty ring")
    return [
        round(sum(vertex[axis] for vertex in ring) / len(ring), 6)
        for axis in range(3)
    ]


def bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    if not vertices:
        fail("cannot calculate bounds for empty mesh")
    return {
        "min": [round(min(vertex[axis] for vertex in vertices), 6) for axis in range(3)],
        "max": [round(max(vertex[axis] for vertex in vertices), 6) for axis in range(3)],
    }


def dimensions(bounds_m: dict[str, list[float]]) -> dict[str, float]:
    return {
        "width": round(bounds_m["max"][0] - bounds_m["min"][0], 6),
        "depth": round(bounds_m["max"][1] - bounds_m["min"][1], 6),
        "height": round(bounds_m["max"][2] - bounds_m["min"][2], 6),
    }


def connector_points(bounds_m: dict[str, list[float]], names: list[str]) -> list[dict[str, Any]]:
    min_x, min_y, min_z = bounds_m["min"]
    max_x, max_y, max_z = bounds_m["max"]
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    cz = (min_z + max_z) * 0.5
    table = {
        "north": ([cx, max_y, cz], [0.0, 1.0, 0.0]),
        "south": ([cx, min_y, cz], [0.0, -1.0, 0.0]),
        "east": ([max_x, cy, cz], [1.0, 0.0, 0.0]),
        "west": ([min_x, cy, cz], [-1.0, 0.0, 0.0]),
        "floor": ([cx, cy, min_z], [0.0, 0.0, -1.0]),
        "ceiling": ([cx, cy, max_z], [0.0, 0.0, 1.0]),
        "radial": ([cx, cy, cz], [0.0, 0.0, 1.0]),
    }
    connectors: list[dict[str, Any]] = []
    for name in names:
        if name not in table:
            fail(f"unsupported pump connector: {name}")
        position, direction = table[name]
        connectors.append(
            {
                "connector_id": name,
                "position_m": [round(value, 6) for value in position],
                "direction": direction,
            }
        )
    return connectors


def merged_mesh(parts: list[Mesh]) -> Mesh:
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for part in parts:
        offset = len(vertices)
        vertices.extend(part.vertices)
        faces.extend([[index + offset for index in face] for face in part.faces])
    return Mesh(vertices=vertices, faces=faces)


def z_range_height(z_range: list[float]) -> float:
    return round(z_range[1] - z_range[0], 6)


def z_range_center(z_range: list[float]) -> float:
    return round((z_range[0] + z_range[1]) * 0.5, 6)


def append_mesh_part(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], part_id: str, source_primitive: str, material_role: Any, mesh: Mesh) -> None:
    vertex_start = sum(len(part.vertices) for part in parts_mesh)
    face_start = sum(len(part.faces) for part in parts_mesh)
    parts_mesh.append(mesh)
    mesh_parts.append(
        mesh_part_record(
            part_id,
            source_primitive,
            material_role,
            vertex_start,
            vertex_start + len(mesh.vertices) - 1,
            face_start,
            face_start + len(mesh.faces) - 1,
        )
    )


def part_center_xy(part: dict[str, Any], field: str) -> list[float]:
    if "center_xy" not in part:
        return [0.0, 0.0]
    return finite_vector(part.get("center_xy"), f"{field}.center_xy", 2)


def blocky_box_part_mesh(part: dict[str, Any], field: str) -> Mesh:
    size_xy = positive_vector(part.get("size_m"), f"{field}.size_m", 2)
    z_range = increasing_range(part.get("z_range"), f"{field}.z_range")
    center_xy = part_center_xy(part, field)
    return box_mesh([center_xy[0], center_xy[1], z_range_center(z_range)], [size_xy[0], size_xy[1], z_range_height(z_range)])


def blocky_cylinder_part_mesh(part: dict[str, Any], field: str) -> Mesh:
    z_range = increasing_range(part.get("z_range"), f"{field}.z_range")
    center_xy = part_center_xy(part, field)
    return cylinder_mesh(
        [center_xy[0], center_xy[1], z_range_center(z_range)],
        positive_float(part.get("radius_m"), f"{field}.radius_m"),
        z_range_height(z_range),
        integer_at_least(part.get("segments"), 3, f"{field}.segments"),
    )


def z_overlap(left: list[float], right: list[float]) -> list[float] | None:
    start = round(max(left[0], right[0]), 6)
    end = round(min(left[1], right[1]), 6)
    if start >= end:
        return None
    return [start, end]


def append_radial_box_array(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], ribs: dict[str, Any], field: str) -> dict[str, Any]:
    rib_count = integer_at_least(ribs.get("count"), 1, f"{field}.count")
    rib_depth = positive_float(ribs.get("rib_depth_m"), f"{field}.rib_depth_m")
    rib_width = positive_float(ribs.get("rib_width_m"), f"{field}.rib_width_m")
    core_radius = positive_float(ribs.get("core_radius_m"), f"{field}.core_radius_m")
    rib_z_range = increasing_range(ribs.get("z_range"), f"{field}.z_range")
    rib_center_radius = round(core_radius + rib_depth * 0.5, 6)
    start_angle = finite_float(ribs.get("start_angle_degrees", 0.0), f"{field}.start_angle_degrees")
    part_prefix = require_string(ribs.get("part_prefix"), f"{field}.part_prefix")
    for rib_index in range(rib_count):
        angle = math.radians(start_angle + 360.0 * rib_index / rib_count)
        radial = [math.cos(angle), math.sin(angle), 0.0]
        tangent = [-math.sin(angle), math.cos(angle), 0.0]
        center = [
            round(radial[0] * rib_center_radius, 6),
            round(radial[1] * rib_center_radius, 6),
            z_range_center(rib_z_range),
        ]
        append_mesh_part(
            parts_mesh,
            mesh_parts,
            f"{part_prefix}_{rib_index:02d}",
            "oriented_box",
            ribs.get("material_role"),
            oriented_box_mesh(center, radial, tangent, [rib_depth, rib_width, z_range_height(rib_z_range)]),
        )
    return {
        "part_prefix": part_prefix,
        "count": rib_count,
        "core_radius_m": core_radius,
        "rib_depth_m": rib_depth,
        "rib_width_m": rib_width,
        "rib_center_radius_m": rib_center_radius,
        "z_range": rib_z_range,
        "start_angle_degrees": start_angle,
    }


def append_blocky_shape_part(parts_mesh: list[Mesh], mesh_parts: list[dict[str, Any]], part: dict[str, Any], field: str) -> dict[str, Any]:
    part_type = require_string(part.get("part_type"), f"{field}.part_type")
    if part_type == "box":
        part_id = require_string(part.get("part_id"), f"{field}.part_id")
        append_mesh_part(parts_mesh, mesh_parts, part_id, "box", part.get("material_role"), blocky_box_part_mesh(part, field))
        return {
            "part_type": "box",
            "part_id": part_id,
            "z_range": increasing_range(part.get("z_range"), f"{field}.z_range"),
            "center_xy": part_center_xy(part, field),
        }
    if part_type == "cylinder":
        part_id = require_string(part.get("part_id"), f"{field}.part_id")
        append_mesh_part(parts_mesh, mesh_parts, part_id, "cylinder", part.get("material_role"), blocky_cylinder_part_mesh(part, field))
        return {
            "part_type": "cylinder",
            "part_id": part_id,
            "z_range": increasing_range(part.get("z_range"), f"{field}.z_range"),
            "center_xy": part_center_xy(part, field),
            "segments": integer_at_least(part.get("segments"), 3, f"{field}.segments"),
        }
    if part_type == "radial_box_array":
        array = append_radial_box_array(parts_mesh, mesh_parts, part, field)
        return {"part_type": "radial_box_array", **array}
    fail(f"unsupported blocky_shape part_type `{part_type}` at {field}")


def blocky_shape_mesh(shape: dict[str, Any]) -> tuple[Mesh, dict[str, Any], list[dict[str, Any]]]:
    axis = require_string(shape.get("axis"), "blocky_shape.axis")
    if axis != "z":
        fail("blocky_shape.axis only supports z in v0")

    parts_source = require_list(shape.get("parts"), "blocky_shape.parts")
    if not parts_source:
        fail("blocky_shape.parts must not be empty")

    parts_mesh: list[Mesh] = []
    mesh_parts: list[dict[str, Any]] = []
    source_parts: list[dict[str, Any]] = []
    radial_arrays: list[dict[str, Any]] = []
    part_types: list[str] = []
    for part_index, item in enumerate(parts_source):
        part = require_object(item, f"blocky_shape.parts[{part_index}]")
        part_type = require_string(part.get("part_type"), f"blocky_shape.parts[{part_index}].part_type")
        part_types.append(part_type)
        compiled_part = append_blocky_shape_part(parts_mesh, mesh_parts, part, f"blocky_shape.parts[{part_index}]")
        source_parts.append(compiled_part)
        if part_type == "radial_box_array":
            radial_arrays.append(compiled_part)

    metadata = {
        "axis": axis,
        "grammar": "blocky_shape_v0",
        "assembly": "ordered_simple_parts",
        "source_part_count": len(parts_source),
        "expanded_part_count": len(mesh_parts),
        "part_types": part_types,
        "radial_arrays": radial_arrays,
        "source_parts": source_parts,
    }
    return merged_mesh(parts_mesh), metadata, mesh_parts


def blocky_column_mesh(column: dict[str, Any]) -> tuple[Mesh, dict[str, Any], list[dict[str, Any]]]:
    axis = require_string(column.get("axis"), "blocky_column.axis")
    if axis != "z":
        fail("blocky_column.axis only supports z in v0")

    base = require_object(column.get("base"), "blocky_column.base")
    lower_collar = require_object(column.get("lower_collar"), "blocky_column.lower_collar")
    shaft_core = require_object(column.get("shaft_core"), "blocky_column.shaft_core")
    ribs = require_object(column.get("ribs"), "blocky_column.ribs")
    upper_collar = require_object(column.get("upper_collar"), "blocky_column.upper_collar")
    cap = require_object(column.get("cap"), "blocky_column.cap")

    parts_mesh: list[Mesh] = []
    mesh_parts: list[dict[str, Any]] = []
    append_mesh_part(
        parts_mesh,
        mesh_parts,
        require_string(base.get("part_id"), "blocky_column.base.part_id"),
        "box",
        base.get("material_role"),
        blocky_box_part_mesh(base, "blocky_column.base"),
    )
    append_mesh_part(
        parts_mesh,
        mesh_parts,
        require_string(lower_collar.get("part_id"), "blocky_column.lower_collar.part_id"),
        "cylinder",
        lower_collar.get("material_role"),
        blocky_cylinder_part_mesh(lower_collar, "blocky_column.lower_collar"),
    )
    append_mesh_part(
        parts_mesh,
        mesh_parts,
        require_string(shaft_core.get("part_id"), "blocky_column.shaft_core.part_id"),
        "cylinder",
        shaft_core.get("material_role"),
        blocky_cylinder_part_mesh(shaft_core, "blocky_column.shaft_core"),
    )

    rib_z_range = increasing_range(ribs.get("z_range"), "blocky_column.ribs.z_range")
    rib_metadata = append_radial_box_array(parts_mesh, mesh_parts, ribs, "blocky_column.ribs")

    append_mesh_part(
        parts_mesh,
        mesh_parts,
        require_string(upper_collar.get("part_id"), "blocky_column.upper_collar.part_id"),
        "cylinder",
        upper_collar.get("material_role"),
        blocky_cylinder_part_mesh(upper_collar, "blocky_column.upper_collar"),
    )
    append_mesh_part(
        parts_mesh,
        mesh_parts,
        require_string(cap.get("part_id"), "blocky_column.cap.part_id"),
        "box",
        cap.get("material_role"),
        blocky_box_part_mesh(cap, "blocky_column.cap"),
    )

    base_z = increasing_range(base.get("z_range"), "blocky_column.base.z_range")
    lower_z = increasing_range(lower_collar.get("z_range"), "blocky_column.lower_collar.z_range")
    shaft_z = increasing_range(shaft_core.get("z_range"), "blocky_column.shaft_core.z_range")
    upper_z = increasing_range(upper_collar.get("z_range"), "blocky_column.upper_collar.z_range")
    cap_z = increasing_range(cap.get("z_range"), "blocky_column.cap.z_range")
    seam_pairs = [
        ("square_plinth_to_lower_collar", base_z, lower_z),
        ("lower_collar_to_ribs", lower_z, rib_z_range),
        ("lower_collar_to_shaft_core", lower_z, shaft_z),
        ("ribs_to_upper_collar", rib_z_range, upper_z),
        ("shaft_core_to_upper_collar", shaft_z, upper_z),
        ("upper_collar_to_square_abacus", upper_z, cap_z),
    ]
    covered_seams = [
        {"seam_id": seam_id, "overlap_z": overlap}
        for seam_id, left, right in seam_pairs
        if (overlap := z_overlap(left, right)) is not None
    ]
    metadata = {
        "axis": axis,
        "assembly": "simple_parts",
        "part_count": len(mesh_parts),
        "rib_count": rib_metadata["count"],
        "rib_depth_m": rib_metadata["rib_depth_m"],
        "rib_width_m": rib_metadata["rib_width_m"],
        "rib_center_radius_m": rib_metadata["rib_center_radius_m"],
        "shaft_core_radius_m": positive_float(shaft_core.get("radius_m"), "blocky_column.shaft_core.radius_m"),
        "covered_seams": covered_seams,
    }
    return merged_mesh(parts_mesh), metadata, mesh_parts


def source_profile_terms(asset: dict[str, Any]) -> list[str]:
    operation = asset.get("operation")
    if operation == "extrude":
        profile = require_object(asset.get("profile"), f"{asset.get('asset_id', '<unknown>')}.profile")
        return [require_string(profile.get("type"), "profile.type")]
    if operation == "loft_sections":
        terms: list[str] = []
        for section in require_list(asset.get("sections"), f"{asset.get('asset_id', '<unknown>')}.sections"):
            profile = require_object(require_object(section, "section").get("profile"), "section.profile")
            profile_type = require_string(profile.get("type"), "section.profile.type")
            if profile_type not in terms:
                terms.append(profile_type)
        return terms
    if operation == "section_stack":
        terms = []
        stack = require_object(asset.get("section_stack"), f"{asset.get('asset_id', '<unknown>')}.section_stack")
        for ring in require_list(stack.get("rings"), f"{asset.get('asset_id', '<unknown>')}.section_stack.rings"):
            profile = require_object(require_object(ring, "ring").get("profile"), "ring.profile")
            profile_type = require_string(profile.get("type"), "ring.profile.type")
            if profile_type not in terms:
                terms.append(profile_type)
        return terms
    if operation == "radial_stack":
        return ["circle", "rectangle"]
    if operation == "profile_revolve":
        return ["circle"]
    if operation == "decorated_balustrade":
        return ["circle", "pointed_arch_profile", "rectangle", "custom_polygon"]
    if operation == "blocky_column":
        return ["square", "circle", "rectangle"]
    if operation == "blocky_shape":
        return ["square", "circle", "rectangle"]
    return []


def base_source_terms(asset: dict[str, Any]) -> dict[str, list[str]]:
    operation = require_string(asset.get("operation"), f"{asset.get('asset_id', '<unknown>')}.operation")
    geometry_terms = [
        require_string(term, f"{asset.get('asset_id', '<unknown>')}.geometry_terms_used[]")
        for term in require_list(asset.get("geometry_terms_used", []), f"{asset.get('asset_id', '<unknown>')}.geometry_terms_used")
    ]
    profile_terms_source = asset.get("profile_terms", source_profile_terms(asset))
    profile_terms = [
        require_string(term, f"{asset.get('asset_id', '<unknown>')}.profile_terms[]")
        for term in require_list(profile_terms_source, f"{asset.get('asset_id', '<unknown>')}.profile_terms")
    ]
    operation_terms_source = asset.get("operations", [operation])
    operator_terms = [
        require_string(term, f"{asset.get('asset_id', '<unknown>')}.operations[]")
        for term in require_list(operation_terms_source, f"{asset.get('asset_id', '<unknown>')}.operations")
    ]
    return {
        "geometry": geometry_terms,
        "profiles": profile_terms,
        "operators": operator_terms,
    }


def mesh_part_record(part_id: str, source_primitive: str, material_role: Any, vertex_start: int, vertex_end: int, face_start: int, face_end: int) -> dict[str, Any]:
    record: dict[str, Any] = {
        "part_id": part_id,
        "source_primitive": source_primitive,
        "vertex_range": [vertex_start, vertex_end],
        "face_range": [face_start, face_end],
    }
    if isinstance(material_role, str) and material_role:
        record["material_role"] = material_role
    return record


def proof_primitive_mesh(asset_id: str, part: dict[str, Any], field: str) -> Mesh:
    primitive = require_string(part.get("primitive"), f"{field}.primitive")
    if primitive == "cube":
        return box_mesh(finite_vector(part.get("location_m"), f"{field}.location_m"), positive_vector(part.get("dimensions_m"), f"{field}.dimensions_m"))
    if primitive == "cylinder":
        vertices = part.get("vertices")
        if not isinstance(vertices, int) or isinstance(vertices, bool):
            fail(f"{field}.vertices must be an integer")
        return cylinder_mesh(
            finite_vector(part.get("location_m"), f"{field}.location_m"),
            positive_float(part.get("radius_m"), f"{field}.radius_m"),
            positive_float(part.get("depth_m"), f"{field}.depth_m"),
            vertices,
        )
    if primitive == "curve":
        return curve_strip_mesh(part)
    fail(f"{asset_id} unsupported proof primitive: {primitive}")


def proof_primitives_mesh(asset_id: str, primitives: list[Any]) -> tuple[Mesh, list[dict[str, Any]]]:
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    parts: list[dict[str, Any]] = []
    for part_index, item in enumerate(primitives):
        part = require_object(item, f"{asset_id}.proof_primitives[{part_index}]")
        part_id = require_string(part.get("name"), f"{asset_id}.proof_primitives[{part_index}].name")
        source_primitive = require_string(part.get("primitive"), f"{asset_id}.proof_primitives[{part_index}].primitive")
        part_mesh = proof_primitive_mesh(asset_id, part, f"{asset_id}.proof_primitives[{part_index}]")
        vertex_start = len(vertices)
        face_start = len(faces)
        vertices.extend(part_mesh.vertices)
        faces.extend([[index + vertex_start for index in face] for face in part_mesh.faces])
        parts.append(
            mesh_part_record(
                part_id,
                source_primitive,
                part.get("material_role"),
                vertex_start,
                len(vertices) - 1,
                face_start,
                len(faces) - 1,
            )
        )
    return Mesh(vertices=vertices, faces=faces), parts


def measured_connectors(asset_id: str, sockets: list[Any]) -> list[dict[str, Any]]:
    connectors: list[dict[str, Any]] = []
    for socket_index, socket in enumerate(sockets):
        item = require_object(socket, f"{asset_id}.sockets[{socket_index}]")
        connectors.append(
            {
                "connector_id": require_string(item.get("socket_id"), f"{asset_id}.sockets[{socket_index}].socket_id"),
                "connector_term": require_string(item.get("connector_term"), f"{asset_id}.sockets[{socket_index}].connector_term"),
                "position_m": finite_vector(item.get("position_m"), f"{asset_id}.sockets[{socket_index}].position_m"),
                "direction": validate_unit_direction(item.get("direction"), f"{asset_id}.sockets[{socket_index}].direction"),
                "role": require_string(item.get("role"), f"{asset_id}.sockets[{socket_index}].role"),
            }
        )
    return connectors


def bounds_mismatch_warnings(asset_id: str, declared_bounds: dict[str, list[float]], mesh_bounds: dict[str, list[float]]) -> list[dict[str, Any]]:
    if declared_bounds == mesh_bounds:
        return []
    return [
        {
            "code": "proof_primitive_bounds_differ_from_declared_bounds",
            "message": f"{asset_id} proof primitive mesh bounds differ from source bounds_m; source bounds_m remain placement extents.",
            "declared_bounds_m": declared_bounds,
            "mesh_bounds_m": mesh_bounds,
        }
    ]


def require_asset_core(asset: dict[str, Any]) -> None:
    for field in (
        "asset_id",
        "asset_kind",
        "operation",
        "architectural_role",
        "generation_use",
        "semantic_tags",
        "connectors",
        "child_slots",
        "no_claims",
    ):
        if field not in asset:
            fail(f"{asset.get('asset_id', '<unknown>')} missing {field}")
    validate_claims(asset)


def compile_asset(asset: dict[str, Any], compiled: dict[str, dict[str, Any]], source_schema: str = SIMPLE_BUNDLE_SCHEMA) -> dict[str, Any]:
    require_asset_core(asset)
    asset_id = require_string(asset["asset_id"], "asset_id")
    operation = require_string(asset["operation"], f"{asset_id}.operation")
    components: list[dict[str, Any]] = []
    mesh_parts: list[dict[str, Any]] = []
    mesh_extra: dict[str, Any] = {}
    if operation == "extrude":
        mesh = extrude_mesh(profile_points(require_object(asset.get("profile"), f"{asset_id}.profile")), positive_float(asset.get("height"), f"{asset_id}.height"))
    elif operation == "loft_sections":
        mesh = loft_mesh(require_list(asset.get("sections"), f"{asset_id}.sections"))
    elif operation == "section_stack":
        mesh, stack_metadata, mesh_parts = section_stack_mesh(require_object(asset.get("section_stack"), f"{asset_id}.section_stack"))
        mesh_extra["section_stack"] = stack_metadata
    elif operation == "radial_stack":
        mesh, stack_metadata, mesh_parts = radial_stack_mesh(require_object(asset.get("radial_stack"), f"{asset_id}.radial_stack"))
        mesh_extra["radial_stack"] = stack_metadata
    elif operation == "profile_revolve":
        mesh, revolve_metadata, mesh_parts = profile_revolve_mesh(require_object(asset.get("profile_revolve"), f"{asset_id}.profile_revolve"))
        mesh_extra["profile_revolve"] = revolve_metadata
    elif operation == "decorated_balustrade":
        mesh, balustrade_metadata, mesh_parts = decorated_balustrade_mesh(require_object(asset.get("decorated_balustrade"), f"{asset_id}.decorated_balustrade"))
        mesh_extra["decorated_balustrade"] = balustrade_metadata
    elif operation == "blocky_column":
        mesh, column_metadata, mesh_parts = blocky_column_mesh(require_object(asset.get("blocky_column"), f"{asset_id}.blocky_column"))
        mesh_extra["blocky_column"] = column_metadata
    elif operation == "blocky_shape":
        mesh, shape_metadata, mesh_parts = blocky_shape_mesh(require_object(asset.get("blocky_shape"), f"{asset_id}.blocky_shape"))
        mesh_extra["blocky_shape"] = shape_metadata
    elif operation == "compound_asset":
        parts: list[Mesh] = []
        for component in require_list(asset.get("components"), f"{asset_id}.components"):
            component = require_object(component, f"{asset_id}.component")
            ref = require_string(component.get("asset_ref"), f"{asset_id}.component.asset_ref")
            if ref not in compiled:
                fail(f"{asset_id} references unknown or later asset: {ref}")
            translation = [finite_float(value, f"{asset_id}.{ref}.translation") for value in component.get("translation", [0.0, 0.0, 0.0])]
            source_mesh = compiled[ref]["mesh"]
            part = Mesh(vertices=source_mesh["vertices"], faces=source_mesh["faces"]).translated(translation)
            parts.append(part)
            components.append(
                {
                    "instance_id": require_string(component.get("instance_id"), f"{asset_id}.component.instance_id"),
                    "asset_ref": ref,
                    "translation_m": [round(value, 6) for value in translation],
                }
            )
        mesh = merged_mesh(parts)
    else:
        fail(f"{asset_id} unsupported operation: {operation}")

    bounds_m = bounds(mesh.vertices)
    return {
        "schema": "gameguy_asset_v0",
        "asset_id": asset_id,
        "source_schema": source_schema,
        "source_operation": operation,
        "asset_kind": asset["asset_kind"],
        "architectural_role": asset["architectural_role"],
        "generation_use": asset["generation_use"],
        "semantic_tags": asset["semantic_tags"],
        "child_slots": asset["child_slots"],
        "connectors": connector_points(bounds_m, require_list(asset["connectors"], f"{asset_id}.connectors")),
        "components": components,
        "bounds_m": bounds_m,
        "dimensions_m": dimensions(bounds_m),
        "mesh": {
            "coordinate_space": "local_xyz_m",
            "parts": mesh_parts,
            **mesh_extra,
            "vertices": mesh.vertices,
            "faces": mesh.faces,
        },
        "source_refs": [],
        "source_terms": base_source_terms(asset),
        "validation_expectations": require_object(asset.get("validation_expectations", {}), f"{asset_id}.validation_expectations"),
        "no_claims": asset["no_claims"],
    }


def role_from_asset_id(asset_id: str, source_version: str) -> str:
    suffix = f"_{source_version}"
    name = asset_id
    if name.startswith("measured_"):
        name = name[len("measured_") :]
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name.replace("_", " ")


def measured_architectural_role(asset: dict[str, Any]) -> str:
    ratio_basis = asset.get("ratio_basis")
    if isinstance(ratio_basis, dict) and isinstance(ratio_basis.get("module"), str) and ratio_basis["module"]:
        return ratio_basis["module"]
    return role_from_asset_id(require_string(asset.get("asset_id"), "asset_id"), require_string(asset.get("source_version"), "source_version"))


def compile_measured_asset(asset: dict[str, Any], source_schema: str) -> dict[str, Any]:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    source_version = require_string(asset.get("source_version"), f"{asset_id}.source_version")
    dims = validate_dimensions_object(asset.get("dimensions_m"), f"{asset_id}.dimensions_m")
    declared_bounds = validate_bounds_object(asset.get("bounds_m"), f"{asset_id}.bounds_m")
    primitives = require_list(asset.get("proof_primitives"), f"{asset_id}.proof_primitives")
    mesh, parts = proof_primitives_mesh(asset_id, primitives)
    mesh_bounds = bounds(mesh.vertices)
    warnings = bounds_mismatch_warnings(asset_id, declared_bounds, mesh_bounds)

    generated: dict[str, Any] = {
        "schema": "gameguy_asset_v0",
        "asset_id": asset_id,
        "source_schema": source_schema,
        "source_operation": "proof_primitives",
        "asset_kind": "measured_component",
        "architectural_role": measured_architectural_role(asset),
        "generation_use": ["measured_component_blockout"],
        "semantic_tags": require_list(asset.get("semantic_roles"), f"{asset_id}.semantic_roles"),
        "child_slots": [],
        "connectors": measured_connectors(asset_id, require_list(asset.get("sockets"), f"{asset_id}.sockets")),
        "components": [],
        "bounds_m": declared_bounds,
        "dimensions_m": dims,
        "mesh": {
            "coordinate_space": "local_xyz_m",
            "parts": parts,
            "bounds_m": mesh_bounds,
            "vertices": mesh.vertices,
            "faces": mesh.faces,
        },
        "source_refs": require_list(asset.get("source_measurement_refs"), f"{asset_id}.source_measurement_refs"),
        "source_terms": {
            "geometry": require_list(asset.get("geometry_terms_used"), f"{asset_id}.geometry_terms_used"),
            "profiles": require_list(asset.get("profile_terms"), f"{asset_id}.profile_terms"),
            "operators": require_list(asset.get("operations"), f"{asset_id}.operations"),
        },
        "validation_expectations": require_object(asset.get("validation_expectations", {}), f"{asset_id}.validation_expectations"),
        "no_claims": require_false_claims(
            asset.get("no_claims"),
            f"{asset_id}.no_claims",
            {"production_approval", "structural_safety", "fabrication_ready", "gym_museum_approval", "historical_accuracy"},
        ),
        "source_version": source_version,
        "source_provenance": {
            "source_version": source_version,
            "legacy_source_script": require_string(asset.get("legacy_source_script"), f"{asset_id}.legacy_source_script"),
            "legacy_source_script_removed": True,
        },
    }
    for optional_field in ("ratio_basis", "uncertainty", "notes"):
        if optional_field in asset:
            generated[optional_field] = asset[optional_field]
    if warnings:
        generated["validation_warnings"] = warnings
    return generated


def load_bundle(path: Path) -> dict[str, Any]:
    bundle = load_json(path)
    supported_schemas = {
        SIMPLE_BUNDLE_SCHEMA,
        MEASURED_BUNDLE_SCHEMA,
        SECTION_STACK_BUNDLE_SCHEMA,
        RADIAL_STACK_BUNDLE_SCHEMA,
        PROFILE_REVOLVE_BUNDLE_SCHEMA,
        DECORATED_BALUSTRADE_BUNDLE_SCHEMA,
        BLOCKY_COLUMN_BUNDLE_SCHEMA,
        BLOCKY_SHAPE_BUNDLE_SCHEMA,
    }
    if bundle.get("schema") not in supported_schemas:
        fail(f"bundle schema must be one of: {', '.join(sorted(supported_schemas))}")
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    return bundle


def write_outputs(compiled: dict[str, dict[str, Any]], out_root: Path, source_bundle: Path, source_bundle_schema: str) -> None:
    asset_dir = out_root / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    manifest_assets = []
    for asset_id, asset in compiled.items():
        path = asset_dir / f"{asset_id}.json"
        path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
        manifest_assets.append(
            {
                "asset_id": asset_id,
                "path": str(path.relative_to(out_root)),
                "asset_kind": asset["asset_kind"],
                "architectural_role": asset["architectural_role"],
                "dimensions_m": asset["dimensions_m"],
                "vertex_count": len(asset["mesh"]["vertices"]),
                "face_count": len(asset["mesh"]["faces"]),
            }
        )
    manifest = {
        "schema": "gameguy_asset_pump_manifest_v0",
        "source_bundle": repo_display_path(source_bundle),
        "source_bundle_schema": source_bundle_schema,
        "asset_schema": "gameguy_asset_v0",
        "asset_count": len(compiled),
        "assets": manifest_assets,
        "rules": {
            "no_reports": True,
            "no_receipts": True,
            "no_blender": True,
            "no_media": True,
            "no_mesh_export_files": True,
            "geometry_dictionary_terms_enforced": True,
        },
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def repo_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pump source asset recipes into deterministic geometry JSON.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true", help="Delete the output folder before writing. Refuses to clean outside /tmp.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    out_root = args.out
    if args.clean:
        resolved = out_root.resolve()
        if not (str(resolved).startswith("/tmp/") or str(resolved).startswith("/private/tmp/")):
            fail("--clean only deletes output folders under /tmp")
        shutil.rmtree(resolved, ignore_errors=True)
    if out_root.exists() and any(out_root.iterdir()):
        fail(f"output folder is not empty: {out_root}. Use --clean for /tmp outputs or choose a new folder.")

    bundle = load_bundle(bundle_path)
    source_schema = require_string(bundle.get("schema"), "bundle.schema")
    geometry_terms = load_geometry_terms()
    if source_schema == SIMPLE_BUNDLE_SCHEMA:
        validate_recipe_terms(bundle, geometry_terms)
    elif source_schema == MEASURED_BUNDLE_SCHEMA:
        validate_measured_bundle_terms(bundle, geometry_terms)
    elif source_schema == SECTION_STACK_BUNDLE_SCHEMA:
        validate_section_stack_bundle_terms(bundle, geometry_terms)
    elif source_schema == RADIAL_STACK_BUNDLE_SCHEMA:
        validate_radial_stack_bundle_terms(bundle, geometry_terms)
    elif source_schema == PROFILE_REVOLVE_BUNDLE_SCHEMA:
        validate_profile_revolve_bundle_terms(bundle, geometry_terms)
    elif source_schema == DECORATED_BALUSTRADE_BUNDLE_SCHEMA:
        validate_decorated_balustrade_bundle_terms(bundle, geometry_terms)
    elif source_schema == BLOCKY_COLUMN_BUNDLE_SCHEMA:
        validate_blocky_column_bundle_terms(bundle, geometry_terms)
    elif source_schema == BLOCKY_SHAPE_BUNDLE_SCHEMA:
        validate_blocky_shape_bundle_terms(bundle, geometry_terms)
    else:
        fail(f"unsupported bundle schema: {source_schema}")
    compiled: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for asset in require_list(bundle["assets"], "assets"):
        asset = require_object(asset, "asset")
        asset_id = require_string(asset.get("asset_id"), "asset.asset_id")
        if asset_id in seen:
            fail(f"duplicate asset_id: {asset_id}")
        seen.add(asset_id)
        if source_schema in {
            SIMPLE_BUNDLE_SCHEMA,
            SECTION_STACK_BUNDLE_SCHEMA,
            RADIAL_STACK_BUNDLE_SCHEMA,
            PROFILE_REVOLVE_BUNDLE_SCHEMA,
            DECORATED_BALUSTRADE_BUNDLE_SCHEMA,
            BLOCKY_COLUMN_BUNDLE_SCHEMA,
            BLOCKY_SHAPE_BUNDLE_SCHEMA,
        }:
            compiled[asset_id] = compile_asset(asset, compiled, source_schema)
        else:
            compiled[asset_id] = compile_measured_asset(asset, source_schema)

    write_outputs(compiled, out_root, bundle_path, source_schema)
    total_vertices = sum(len(asset["mesh"]["vertices"]) for asset in compiled.values())
    total_faces = sum(len(asset["mesh"]["faces"]) for asset in compiled.values())
    print(f"pumped assets={len(compiled)} vertices={total_vertices} faces={total_faces} out={out_root}")


if __name__ == "__main__":
    main()
