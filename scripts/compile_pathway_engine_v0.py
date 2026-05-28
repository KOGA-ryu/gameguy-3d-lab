#!/usr/bin/env python3
"""Compile Pathway Engine v0 from declared pathway templates.

This compiler owns pathway plug normalization, connection validation, generated
path records, and the pathway report/receipt. Blender consumes the compiled
artifact and renders it only.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "data" / "architecture" / "map_templates"
OUT_DIR = ROOT / "goal" / "architecture" / "pathway_engine_v0"
RECEIPT_DIR = ROOT / "goal" / "receipts"

ORIGINAL_TEMPLATE_PATH = TEMPLATE_DIR / "pathway_testbed_v0.json"
PROTECTED_TEMPLATE_PATH = TEMPLATE_DIR / "pathway_testbed_template_copy_do_not_rewrite_v0.json"
ENGINE_TEMPLATE_PATH = TEMPLATE_DIR / "pathway_engine_v0.json"
CONTRACT_PATH = ROOT / "contracts" / "pathway_connection_contract_v0.json"
COMPILED_PATH = OUT_DIR / "pathway_engine_v0_compiled.json"
REPORT_MD_PATH = OUT_DIR / "pathway_engine_v0_report.md"
RECEIPT_PATH = RECEIPT_DIR / "pathway_compiler_extraction_v0.receipt.json"

SQRT3 = math.sqrt(3.0)
ENDPOINT_ALIGNMENT_TOLERANCE_MAP = 0.001
MIN_SEGMENT_LENGTH_M = 0.01
SUPPORTED_CONNECTION_TYPES = [
    "road_threshold",
    "flat_pathway",
    "ramp_pathway",
    "stepped_pathway",
    "bridge_link",
]
UNIT_LENGTH_BY_CONNECTION_TYPE = {
    "flat_pathway": 1.2,
    "ramp_pathway": 1.2,
    "stepped_pathway": 1.0,
    "bridge_link": 1.2,
}
FLAT_TERRAIN_POLICIES = {"mostly_flat_pathway_logic_testbed"}
NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def round6(value: float) -> float:
    return round(float(value), 6)


def map_config(template: dict[str, Any]) -> dict[str, Any]:
    raw = template["map"]
    return {
        "width": int(raw["width"]),
        "height": int(raw["height"]),
        "hex_radius_m": float(raw["hex_radius_m"]),
        "base_height_m": float(raw["base_height_m"]),
        "terrain_policy": str(raw.get("terrain_policy", "")),
    }


def map_to_world(mx: float, my: float, config: dict[str, Any]) -> tuple[float, float]:
    x_offset = 0.5 if int(math.floor(my)) % 2 else 0.0
    return (
        ((mx + x_offset) - float(config["width"]) * 0.5) * SQRT3 * float(config["hex_radius_m"]),
        (float(config["height"]) * 0.5 - my) * 1.5 * float(config["hex_radius_m"]),
    )


def terrain_height(_mx: float, _my: float, config: dict[str, Any]) -> float:
    policy = str(config.get("terrain_policy", ""))
    if policy not in FLAT_TERRAIN_POLICIES:
        fail(f"pathway engine only supports flat terrain policies, got {policy!r}")
    return float(config["base_height_m"])


def point_distance_map(left: list[float], right: list[float]) -> float:
    return math.hypot(float(left[0]) - float(right[0]), float(left[1]) - float(right[1]))


def route_points_world(points: list[list[float]], config: dict[str, Any]) -> list[list[float]]:
    world: list[list[float]] = []
    for x, y in points:
        wx, wy = map_to_world(float(x), float(y), config)
        world.append([round6(wx), round6(wy), round6(terrain_height(float(x), float(y), config) + 0.1)])
    return world


def route_segment_lengths(points: list[list[float]], config: dict[str, Any]) -> list[float]:
    lengths: list[float] = []
    for left, right in zip(points, points[1:], strict=False):
        wx0, wy0 = map_to_world(float(left[0]), float(left[1]), config)
        wx1, wy1 = map_to_world(float(right[0]), float(right[1]), config)
        lengths.append(math.hypot(wx1 - wx0, wy1 - wy0))
    return lengths


def route_length(points: list[list[float]], config: dict[str, Any]) -> float:
    return sum(route_segment_lengths(points, config))


def route_max_slope(points: list[list[float]], config: dict[str, Any]) -> float:
    max_slope = 0.0
    for left, right in zip(points, points[1:], strict=False):
        wx0, wy0 = map_to_world(float(left[0]), float(left[1]), config)
        wx1, wy1 = map_to_world(float(right[0]), float(right[1]), config)
        dz = terrain_height(float(right[0]), float(right[1]), config) - terrain_height(float(left[0]), float(left[1]), config)
        horizontal = max(math.hypot(wx1 - wx0, wy1 - wy0), 1e-6)
        max_slope = max(max_slope, abs(dz) / horizontal)
    return max_slope


def normalized_direction(raw: dict[str, Any]) -> list[float]:
    direction = raw.get("direction_map", raw.get("direction", [1.0, 0.0, 0.0]))
    return [float(direction[0]), float(direction[1]), float(direction[2] if len(direction) > 2 else 0.0)]


def plug_record(raw: dict[str, Any], owner_id: str, owner_type: str, config: dict[str, Any]) -> dict[str, Any]:
    mx, my = [float(value) for value in raw["position_map"]]
    wx, wy = map_to_world(mx, my, config)
    return {
        "plug_id": raw["plug_id"],
        "owner_id": owner_id,
        "owner_type": owner_type,
        "plug_type": "entrance" if owner_type == "building" else raw.get("plug_type", owner_type),
        "position_map": [round6(mx), round6(my)],
        "position": [round6(wx), round6(wy), round6(terrain_height(mx, my, config) + 0.12)],
        "direction": normalized_direction(raw),
        "width_m": float(raw.get("width_m", 1.45)),
        "clearance_m": float(raw.get("clearance_m", 2.2)),
        "allowed_connection_types": raw.get("allowed_connection_types", ["flat_pathway", "road_threshold"]),
        "priority": raw.get("priority", "primary"),
    }


def normalize_plugs(template: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    plugs: list[dict[str, Any]] = []
    for building in template.get("buildings", []):
        for plug in building.get("entrance_plugs", []):
            plugs.append(plug_record(plug, building["building_id"], "building", config))
    for plug in template.get("road_plugs", []):
        plugs.append(plug_record(plug, plug["owner_id"], "road", config))
    for plug in template.get("pathway_plugs", []):
        plugs.append(plug_record(plug, plug["owner_id"], "pathway", config))
    return plugs


def terrain_cells(config: dict[str, Any]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    width = int(config["width"])
    height = int(config["height"])
    base_height = float(config["base_height_m"])
    for y in range(height):
        for x in range(width):
            mx = x + 0.5
            my = y + 0.5
            wx, wy = map_to_world(mx, my, config)
            is_road = 22.0 <= my <= 24.0 and 3.0 <= mx <= 29.0
            is_yard = 10.0 <= mx <= 22.0 and 12.0 <= my <= 20.0
            cells.append(
                {
                    "cell_id": f"pathway_{x}_{y}",
                    "grid": [x, y],
                    "map_center": [round(mx, 3), round(my, 3)],
                    "world_center": [round6(wx), round6(wy), round6(base_height)],
                    "height_m": round6(base_height),
                    "surface_type": "road" if is_road else "yard" if is_yard else "grass",
                }
            )
    return cells


def points_in_bounds(points: list[list[float]], config: dict[str, Any]) -> bool:
    return all(0.0 <= float(point[0]) <= float(config["width"]) and 0.0 <= float(point[1]) <= float(config["height"]) for point in points)


def connection_surface(connection_type: str) -> str:
    if connection_type == "road_threshold":
        return "threshold_stone"
    if connection_type == "bridge_link":
        return "bridge_deck"
    return "packed_stone"


def connection_unit_plan(connection_type: str, length_m: float) -> dict[str, Any]:
    if connection_type == "road_threshold":
        unit_length = length_m
        unit_count = 1
        leftover = 0.0
    else:
        unit_length = UNIT_LENGTH_BY_CONNECTION_TYPE.get(connection_type, 1.2)
        unit_count = max(1, int(length_m // unit_length)) if unit_length > 0 else 1
        leftover = max(0.0, length_m - unit_count * unit_length)
    return {
        "unit_length_m": round6(unit_length),
        "unit_count": unit_count,
        "leftover_gap_m": round6(leftover),
        "leftover_gap_warning": leftover > 0.05,
        "scale_applied": False,
        "fit_policy": "single_threshold_landing" if connection_type == "road_threshold" else "repeat_units_without_scaling",
    }


def min_width_for_connection(connection: dict[str, Any]) -> float:
    if "min_width" in connection:
        return float(connection["min_width"])
    if connection["connection_type"] == "road_threshold":
        return 1.0
    return 1.4


def compile_connection(connection: dict[str, Any], plugs_by_id: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    fail_reasons: list[str] = []
    connection_type = str(connection.get("connection_type", ""))
    if connection_type not in SUPPORTED_CONNECTION_TYPES:
        fail_reasons.append(f"unsupported_connection_type:{connection_type}")

    from_plug = plugs_by_id.get(str(connection.get("from_plug", "")))
    to_plug = plugs_by_id.get(str(connection.get("to_plug", "")))
    if from_plug is None:
        fail_reasons.append(f"missing_from_plug:{connection.get('from_plug')}")
    if to_plug is None:
        fail_reasons.append(f"missing_to_plug:{connection.get('to_plug')}")

    if from_plug is not None and connection_type not in from_plug["allowed_connection_types"]:
        fail_reasons.append("connection_type_not_allowed_by_from_plug")
    if to_plug is not None and connection_type not in to_plug["allowed_connection_types"]:
        fail_reasons.append("connection_type_not_allowed_by_to_plug")

    raw_points = connection.get("route_points_map", [])
    points = [[float(point[0]), float(point[1])] for point in raw_points if isinstance(point, list) and len(point) >= 2]
    if len(points) < 2:
        fail_reasons.append("route_has_fewer_than_two_points")

    route_shape_ok = len(points) >= 2
    route_bounds_ok = route_shape_ok and points_in_bounds(points, config)
    if route_shape_ok and not route_bounds_ok:
        fail_reasons.append("route_point_out_of_bounds")

    segment_lengths = route_segment_lengths(points, config) if route_shape_ok else []
    if route_shape_ok and any(length < MIN_SEGMENT_LENGTH_M for length in segment_lengths):
        fail_reasons.append("route_segment_too_short")

    start_alignment = False
    end_alignment = False
    if route_shape_ok and from_plug is not None:
        start_alignment = point_distance_map(points[0], from_plug["position_map"]) <= ENDPOINT_ALIGNMENT_TOLERANCE_MAP
        if not start_alignment:
            fail_reasons.append("route_start_not_at_from_plug")
    if route_shape_ok and to_plug is not None:
        end_alignment = point_distance_map(points[-1], to_plug["position_map"]) <= ENDPOINT_ALIGNMENT_TOLERANCE_MAP
        if not end_alignment:
            fail_reasons.append("route_end_not_at_to_plug")

    length_m = route_length(points, config) if route_shape_ok else 0.0
    max_slope = route_max_slope(points, config) if route_shape_ok else 0.0
    max_slope_allowed = float(connection.get("max_slope", 0.0))
    slope_ok = route_shape_ok and max_slope <= max_slope_allowed
    if route_shape_ok and not slope_ok:
        fail_reasons.append(f"slope_exceeds_max:{round6(max_slope)}>{max_slope_allowed}")

    min_width = min_width_for_connection(connection)
    connection_width = float(connection.get("width_m", 0.0))
    width_ok = connection_width >= min_width
    if not width_ok:
        fail_reasons.append("width_below_minimum")

    plug_width_ok = True
    if from_plug is not None and from_plug["width_m"] < min(connection_width, min_width):
        plug_width_ok = False
    if to_plug is not None and to_plug["width_m"] < min(connection_width, min_width):
        plug_width_ok = False
    if not plug_width_ok and connection_type != "road_threshold":
        fail_reasons.append("plug_width_below_connection_width")

    required_clearance = float(connection.get("min_clearance_m", 0.0))
    available_clearance = min(
        float(from_plug["clearance_m"]) if from_plug is not None else 0.0,
        float(to_plug["clearance_m"]) if to_plug is not None else 0.0,
    )
    clearance_ok = available_clearance >= required_clearance and required_clearance >= 2.0
    if not clearance_ok:
        fail_reasons.append("clearance_below_min_clearance")

    turn_radius = float(connection.get("turn_radius_m", connection.get("min_turn_radius", 0.0)))
    min_turn_radius = float(connection.get("min_turn_radius", 1.0))
    turn_radius_ok = turn_radius >= min_turn_radius
    if not turn_radius_ok:
        fail_reasons.append("turn_radius_below_minimum")

    policy = str(connection.get("deterministic_route_policy", ""))
    policy_ok = bool(policy)
    if not policy_ok:
        fail_reasons.append("unsupported_deterministic_route_policy")

    world_points = route_points_world(points, config) if route_shape_ok else []
    unit_plan = connection_unit_plan(connection_type, length_m)
    status = "fail" if fail_reasons else "pass"
    elevation_gap = 0.0
    if route_shape_ok:
        elevation_gap = abs(terrain_height(points[-1][0], points[-1][1], config) - terrain_height(points[0][0], points[0][1], config))

    generated_path = None
    if status == "pass":
        generated_path = {
            "path_id": f"{connection['connection_id']}_path",
            "route_policy": policy,
            "route_points": world_points,
            "route_points_map": [[round6(point[0]), round6(point[1])] for point in points],
            "surface": connection.get("surface", connection_surface(connection_type)),
            "width_m": round6(connection_width),
            "horizontal_length_m": round6(length_m),
            "elevation_gap_m": round6(elevation_gap),
            "slope": round6(max_slope),
            "vertical_envelope_m": round6(available_clearance),
            "vertical_overbuild_margin_m": 0.0,
            "dimension_source": connection.get("dimension_source", "declaration"),
            "door_measurement_rules_applied": False,
            "sample_semantics": [[] for _point in points],
            "connector_geometry": {
                "primitive": "polyline_strip",
                "width_m": round6(connection_width),
                "vertical_envelope_m": round6(available_clearance),
                "route_points": world_points,
                "start_plug_position": from_plug["position"],
                "end_plug_position": to_plug["position"],
            },
        }

    validation = {
        "plug_resolution_ok": from_plug is not None and to_plug is not None,
        "connection_type_supported": connection_type in SUPPORTED_CONNECTION_TYPES,
        "connection_type_allowed": (
            from_plug is not None
            and to_plug is not None
            and connection_type in from_plug["allowed_connection_types"]
            and connection_type in to_plug["allowed_connection_types"]
        ),
        "endpoint_alignment_ok": start_alignment and end_alignment,
        "route_shape_ok": route_shape_ok,
        "route_bounds_ok": route_bounds_ok,
        "width_ok": width_ok,
        "plug_width_ok": plug_width_ok or connection_type == "road_threshold",
        "slope_ok": slope_ok,
        "clearance_ok": clearance_ok,
        "turn_radius_ok": turn_radius_ok,
        "deterministic_route_policy_ok": policy_ok,
        "leftover_gap_explicit": "leftover_gap_m" in unit_plan and "leftover_gap_warning" in unit_plan,
        "generated_path_present": generated_path is not None,
        "bad_connection_failed_with_reason": status == "fail" and bool(fail_reasons),
    }

    return {
        **connection,
        "from_plug_record": from_plug,
        "to_plug_record": to_plug,
        "route_points_world": world_points,
        "segment_lengths_m": [round6(length) for length in segment_lengths],
        "length_m": round6(length_m),
        "slope_validation": {
            "max_slope_observed": round6(max_slope),
            "max_slope_allowed": max_slope_allowed,
            "status": "pass" if slope_ok else "fail",
        },
        "clearance_validation": {
            "available_clearance_m": round6(available_clearance),
            "min_clearance_m": required_clearance,
            "status": "pass" if clearance_ok else "fail",
        },
        "width_validation": {
            "width_m": round6(connection_width),
            "min_width_m": round6(min_width),
            "endpoint_widths_ok": plug_width_ok or connection_type == "road_threshold",
            "status": "pass" if width_ok and (plug_width_ok or connection_type == "road_threshold") else "fail",
        },
        "endpoint_alignment_validation": {
            "tolerance_map": ENDPOINT_ALIGNMENT_TOLERANCE_MAP,
            "start_aligned": start_alignment,
            "end_aligned": end_alignment,
            "status": "pass" if start_alignment and end_alignment else "fail",
        },
        "allowed_connection_type_validation": {
            "status": "pass" if validation["connection_type_allowed"] else "fail",
            "supported_connection_types": SUPPORTED_CONNECTION_TYPES,
        },
        "connector_unit_plan": unit_plan,
        "status": status,
        "fail_reasons": fail_reasons,
        "validation": validation,
        "generated_path": generated_path,
    }


def annotated_buildings(template: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    buildings = copy.deepcopy(template.get("buildings", []))
    for building in buildings:
        wx, wy = map_to_world(float(building["center_map"][0]), float(building["center_map"][1]), config)
        building["world_center"] = [round6(wx), round6(wy), round6(float(config["base_height_m"]))]
    return buildings


def validate_compiled(
    original: dict[str, Any],
    protected: dict[str, Any],
    engine: dict[str, Any],
    cells: list[dict[str, Any]],
    plugs: list[dict[str, Any]],
    connections: list[dict[str, Any]],
) -> dict[str, Any]:
    validation = {
        "three_design_json_files_exist": all(path.exists() for path in [ORIGINAL_TEMPLATE_PATH, PROTECTED_TEMPLATE_PATH, ENGINE_TEMPLATE_PATH]),
        "template_copy_marked_do_not_rewrite": protected.get("do_not_rewrite") is True,
        "pathway_engine_is_mutable": engine.get("mutable_working_copy") is True,
        "original_template_not_mutated_by_compiler": original.get("scene_id") == "pathway_testbed_v0",
        "protected_template_not_mutated_by_compiler": protected.get("scene_id") == "pathway_testbed_template_copy_do_not_rewrite_v0",
        "working_template_read_by_compiler": engine.get("scene_id") == "pathway_engine_v0",
        "exactly_three_buildings": len(engine.get("buildings", [])) == 3,
        "plug_count": len(plugs),
        "exactly_six_plugs": len(plugs) == 6,
        "named_building_entrance_plug_count": sum(1 for plug in plugs if plug["owner_type"] == "building"),
        "road_plug_count": sum(1 for plug in plugs if plug["owner_type"] == "road"),
        "connection_count": len(connections),
        "exactly_three_connections": len(connections) == 3,
        "central_building_connects_to_two_buildings": {
            connection["connection_id"]
            for connection in connections
            if connection["from_plug"].startswith("central_hall.") and connection["to_plug"].split(".")[0] in {"workshop", "storehouse"}
        }
        == {"central_to_workshop_path", "central_to_storehouse_path"},
        "both_building_to_building_paths_pass": all(
            connection["status"] == "pass"
            for connection in connections
            if connection["connection_id"] in {"central_to_workshop_path", "central_to_storehouse_path"}
        ),
        "south_road_threshold_passes": any(
            connection["connection_id"] == "central_to_yard_road_threshold" and connection["status"] == "pass"
            for connection in connections
        ),
        "all_connections_resolve": all(connection["status"] == "pass" for connection in connections),
        "every_connection_has_status_fail_reasons_validation_generated_path": all(
            all(key in connection for key in ["status", "fail_reasons", "validation", "generated_path"]) for connection in connections
        ),
        "connector_path_records_include_width_slope_clearance_validation": all(
            all(key in connection["validation"] for key in ["width_ok", "slope_ok", "clearance_ok"]) for connection in connections
        ),
        "leftover_slab_gaps_explicit_warnings": all(
            "leftover_gap_warning" in connection["connector_unit_plan"]
            for connection in connections
            if connection["connection_type"] != "road_threshold"
        )
        and any(
            connection["connector_unit_plan"]["leftover_gap_warning"]
            for connection in connections
            if connection["connection_type"] != "road_threshold"
        ),
        "terrain_is_mostly_flat": len({cell["height_m"] for cell in cells}) == 1,
        "json_contract_exists": CONTRACT_PATH.exists(),
        "web_search_used": False,
        "no_claims": NO_CLAIMS,
    }
    required = [
        "three_design_json_files_exist",
        "template_copy_marked_do_not_rewrite",
        "pathway_engine_is_mutable",
        "protected_template_not_mutated_by_compiler",
        "exactly_three_buildings",
        "exactly_six_plugs",
        "exactly_three_connections",
        "both_building_to_building_paths_pass",
        "south_road_threshold_passes",
        "all_connections_resolve",
        "every_connection_has_status_fail_reasons_validation_generated_path",
        "connector_path_records_include_width_slope_clearance_validation",
        "leftover_slab_gaps_explicit_warnings",
        "terrain_is_mostly_flat",
        "json_contract_exists",
    ]
    failed = [key for key in required if not validation[key]]
    if failed:
        fail(f"pathway compiler validation failed: {failed}")
    return validation


def compile_pathway_engine() -> dict[str, Any]:
    original = load_json(ORIGINAL_TEMPLATE_PATH)
    protected = load_json(PROTECTED_TEMPLATE_PATH)
    engine = load_json(ENGINE_TEMPLATE_PATH)
    config = map_config(engine)
    plugs = normalize_plugs(engine, config)
    plugs_by_id = {plug["plug_id"]: plug for plug in plugs}
    connections = [compile_connection(connection, plugs_by_id, config) for connection in engine.get("connections", [])]
    cells = terrain_cells(config)
    validation = validate_compiled(original, protected, engine, cells, plugs, connections)
    return {
        "schema": "pathway_engine_v0_compiled",
        "contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "created_at_utc": now_iso(),
        "source_templates": {
            "original": str(ORIGINAL_TEMPLATE_PATH.relative_to(ROOT)),
            "protected_copy": str(PROTECTED_TEMPLATE_PATH.relative_to(ROOT)),
            "working_copy": str(ENGINE_TEMPLATE_PATH.relative_to(ROOT)),
        },
        "map": config,
        "cells": cells,
        "buildings": annotated_buildings(engine, config),
        "plugs": plugs,
        "connections": connections,
        "generated_connector_paths": [connection["generated_path"] for connection in connections if connection["generated_path"]],
        "validation": validation,
        "scope_notes": {
            "terrain_scope": "flat_pathway_logic_testbed_only",
            "ravine_cliff_bridge_requirements": "not exercised by this template",
            "output_ownership": "compiler writes compiled JSON, report, and receipt paths from module configuration",
        },
        "no_claims": engine.get("no_claims", NO_CLAIMS),
    }


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Pathway Engine v0 Compiler Report",
        "",
        "Reusable compiler output for the flat pathway testbed. Blender now consumes this compiled artifact for rendering only.",
        "",
        "## Source Templates",
        "",
        f"- original: `{data['source_templates']['original']}`",
        f"- protected_copy: `{data['source_templates']['protected_copy']}`",
        f"- working_copy: `{data['source_templates']['working_copy']}`",
        f"- contract: `{data['contract']}`",
        "",
        "## Summary",
        "",
        f"- building_count: {len(data['buildings'])}",
        f"- plug_count: {len(data['plugs'])}",
        f"- connection_count: {len(data['connections'])}",
        f"- generated_path_count: {len(data['generated_connector_paths'])}",
        "",
        "## Connections",
        "",
    ]
    for connection in data["connections"]:
        plan = connection["connector_unit_plan"]
        lines.extend(
            [
                f"### {connection['connection_id']}",
                "",
                f"- from_plug: `{connection['from_plug']}`",
                f"- to_plug: `{connection['to_plug']}`",
                f"- connection_type: `{connection['connection_type']}`",
                f"- status: `{connection['status']}`",
                f"- fail_reasons: {connection['fail_reasons']}",
                f"- length_m: {connection['length_m']}",
                f"- slope_status: {connection['slope_validation']['status']}",
                f"- width_status: {connection['width_validation']['status']}",
                f"- clearance_status: {connection['clearance_validation']['status']}",
                f"- leftover_gap_m: {plan['leftover_gap_m']}",
                f"- leftover_gap_warning: {plan['leftover_gap_warning']}",
                f"- scale_applied: {plan['scale_applied']}",
                "",
            ]
        )
    lines.extend(["## Acceptance", ""])
    for key, value in validation.items():
        if key != "no_claims":
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Non-Acceptance Notes", ""])
    for key, value in data["scope_notes"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Blender Consumption",
            "",
            "- render script input: `goal/architecture/pathway_engine_v0/pathway_engine_v0_compiled.json`",
            "- render script must not rewrite pathway templates",
            "- render outputs remain under `goal/architecture/blender_tests/`",
            "",
            "No production, structural, fabrication, gym/museum approval, or historical accuracy claims.",
            "",
        ]
    )
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    receipt = {
        "schema": "pathway_compiler_extraction_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "purpose": "Move pathway template compilation and plug/connection validation out of Blender into a reusable compiler.",
        "outputs": {
            "contract": str(CONTRACT_PATH.relative_to(ROOT)),
            "compiled": str(COMPILED_PATH.relative_to(ROOT)),
            "report": str(REPORT_MD_PATH.relative_to(ROOT)),
            "receipt": str(RECEIPT_PATH.relative_to(ROOT)),
        },
        "acceptance": data["validation"],
        "non_acceptance_notes": data["scope_notes"],
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    data = compile_pathway_engine()
    COMPILED_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {COMPILED_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_MD_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "buildings={building_count} plugs={plug_count} connections={connection_count}".format(
            building_count=len(data["buildings"]),
            plug_count=len(data["plugs"]),
            connection_count=len(data["connections"]),
        )
    )


if __name__ == "__main__":
    main()
