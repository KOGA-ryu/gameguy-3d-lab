#!/usr/bin/env python3
"""Compile Plug-Based Connection Graph v0.

Entrances, roads, and plots expose named plugs. Connections are developer
declared plug pairs, then validated and converted into deterministic connector
geometry. The compiler does not guess new routes for bad declarations.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_map_template_v2_building_variant_placement as map_v2_compile  # noqa: E402


MAP_V2_PLACEMENT_PATH = map_v2_compile.PLACEMENT_PATH
COMPILED_MAP_PATH = map_v2_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = map_v2_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = map_v2_compile.REFINED_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v2" / "plug_connection_graph"
GRAPH_PATH = OUT_DIR / "plug_based_connection_graph_v0.json"
REPORT_PATH = OUT_DIR / "plug_based_connection_graph_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "plug_based_connection_graph_v0.receipt.json"

NO_CLAIMS = map_v2_compile.NO_CLAIMS
SUPPORTED_CONNECTION_TYPES = ["road_threshold", "flat_pathway", "ramp_pathway", "stepped_pathway", "bridge_link"]
CONNECTION_POLICY_PATH = ROOT / "data" / "architecture" / "map_templates" / "plug_connection_policy_v0.json"


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


def load_connection_policy(policy_path: Path = CONNECTION_POLICY_PATH) -> dict[str, Any]:
    policy = load_json(policy_path)
    if policy.get("schema") != "plug_connection_policy_v0":
        fail(f"{policy_path.relative_to(ROOT)} must use schema plug_connection_policy_v0")
    required = [
        "building_name_by_source_graph_id",
        "road_targets_by_building_plug",
        "active_connection_declarations",
        "rejected_connection_declarations",
    ]
    missing = [key for key in required if key not in policy]
    if missing:
        fail(f"{policy_path.relative_to(ROOT)} missing policy keys: {missing}")
    if not isinstance(policy["building_name_by_source_graph_id"], dict):
        fail("building_name_by_source_graph_id must be an object")
    if not isinstance(policy["road_targets_by_building_plug"], dict):
        fail("road_targets_by_building_plug must be an object")
    if not isinstance(policy["active_connection_declarations"], list):
        fail("active_connection_declarations must be a list")
    if not isinstance(policy["rejected_connection_declarations"], list):
        fail("rejected_connection_declarations must be a list")
    return policy


def round6(value: float) -> float:
    return round(float(value), 6)


def normalize2(x: float, y: float) -> list[float]:
    length = math.hypot(x, y)
    if length <= 1e-9:
        return [1.0, 0.0]
    return [round6(x / length), round6(y / length)]


def local_to_world(local: list[float], origin: list[float], basis: dict[str, list[float]]) -> list[float]:
    return map_v2_compile.transform_local_to_world(local, origin, basis)


def edge_direction_world(edge: str, basis: dict[str, list[float]]) -> list[float]:
    local = {
        "north": [0.0, 1.0],
        "south": [0.0, -1.0],
        "east": [1.0, 0.0],
        "west": [-1.0, 0.0],
    }[edge]
    x = float(local[0]) * float(basis["right"][0]) + float(local[1]) * float(basis["forward"][0])
    y = float(local[0]) * float(basis["right"][1]) + float(local[1]) * float(basis["forward"][1])
    return normalize2(x, y)


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, float, tuple[float, float]]:
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return math.hypot(px - ax, py - ay), 0.0, (ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    hit = (ax + dx * t, ay + dy * t)
    return math.hypot(px - hit[0], py - hit[1]), t, hit


def polyline_lengths(points: list[list[float]]) -> list[float]:
    lengths = [0.0]
    for left, right in zip(points, points[1:], strict=False):
        lengths.append(lengths[-1] + math.hypot(float(right[0]) - float(left[0]), float(right[1]) - float(left[1])))
    return lengths


def nearest_polyline_projection(px: float, py: float, points: list[list[float]]) -> dict[str, Any]:
    cumulative = polyline_lengths(points)
    best = {"distance_m": float("inf"), "station_m": 0.0, "position": [px, py], "tangent": [1.0, 0.0]}
    for index, (left, right) in enumerate(zip(points, points[1:], strict=False)):
        ax, ay = float(left[0]), float(left[1])
        bx, by = float(right[0]), float(right[1])
        distance, t, hit = distance_to_segment(px, py, ax, ay, bx, by)
        if distance < float(best["distance_m"]):
            segment_length = math.hypot(bx - ax, by - ay)
            tangent = (1.0, 0.0) if segment_length <= 1e-9 else ((bx - ax) / segment_length, (by - ay) / segment_length)
            best = {
                "distance_m": distance,
                "station_m": cumulative[index] + t * segment_length,
                "position": [hit[0], hit[1]],
                "tangent": [tangent[0], tangent[1]],
            }
    return best


def terrain_height(refined_graph: dict[str, Any], x: float, y: float) -> float:
    nearest = min(
        refined_graph["hex_plots"],
        key=lambda plot: math.hypot(float(plot["center"][0]) - x, float(plot["center"][1]) - y),
    )
    return float(nearest.get("refined_center_height_m", nearest.get("profiled_center_height_m", nearest.get("height_m", 0.0))))


def surface_semantics(semantic_graph: dict[str, Any], x: float, y: float) -> list[str]:
    cells = semantic_graph.get("semantic_surface_cells", [])
    if not cells:
        return []
    nearest = min(cells, key=lambda cell: math.hypot(float(cell["center"][0]) - x, float(cell["center"][1]) - y))
    return sorted(nearest.get("semantics", []))


def building_name(graph: dict[str, Any], policy: dict[str, Any]) -> str:
    source = str(graph.get("source_building_graph_id", ""))
    names = policy["building_name_by_source_graph_id"]
    if source in names:
        return str(names[source])
    variant_id = str(graph["building_graph_variant_id"])
    if "gatehouse" in variant_id:
        return "gatehouse"
    if "watch" in variant_id:
        return "watch"
    return "shrine"


def entrance_socket(graph: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        socket
        for socket in graph["exterior_sockets"]
        if "entrance" in socket.get("semantic_tags", []) or "road_connector" in socket.get("compatible_tags", [])
    ]
    if not candidates:
        fail(f"{graph['placed_building_graph_id']} has no entrance exterior socket")
    return candidates[0]


def entrance_door_component(graph: dict[str, Any]) -> dict[str, Any]:
    candidates = [component for component in graph["components"] if component["component_type"] == "door_bay"]
    if not candidates:
        fail(f"{graph['placed_building_graph_id']} has no door_bay")
    return candidates[0]


def door_measurement_rules(door: dict[str, Any]) -> dict[str, Any]:
    width, depth, height = [float(value) for value in door["dimensions_m"]]
    recommended_width = max(1.2, min(width - 0.4, 2.2))
    return {
        "source_component_id": door["component_id"],
        "measured_component_id": door.get("measured_component_id", ""),
        "door_width_m": round6(width),
        "door_depth_m": round6(depth),
        "door_clearance_m": round6(height),
        "recommended_connector_width_m": round6(recommended_width),
        "recommended_min_clearance_m": round6(max(2.0, height - 0.25)),
        "vertical_overbuild_margin_m": 0.45,
    }


def build_building_and_plot_plugs(
    map_v2: dict[str, Any],
    refined_graph: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    building_plugs: list[dict[str, Any]] = []
    plot_plugs: list[dict[str, Any]] = []
    for graph in map_v2["placed_building_graphs"]:
        name = building_name(graph, policy)
        socket = entrance_socket(graph)
        door = entrance_door_component(graph)
        local = list(socket["local_position_m"])
        xy_world = local_to_world([float(local[0]), float(local[1]), 0.0], graph["origin"], graph["orientation_basis"])
        z = terrain_height(refined_graph, xy_world[0], xy_world[1]) + 0.08
        direction = edge_direction_world(str(socket["edge"]), graph["orientation_basis"])
        rules = door_measurement_rules(door)
        width = min(1.4, max(1.0, float(door["dimensions_m"][0]) - 1.0))
        plug = {
            "plug_id": f"{name}.main_entry",
            "owner_id": graph["placed_building_graph_id"],
            "owner_type": "building_graph",
            "source_building_graph_variant_id": graph["building_graph_variant_id"],
            "plug_type": "entrance",
            "position": [round6(xy_world[0]), round6(xy_world[1]), round6(z)],
            "direction": [direction[0], direction[1], 0.0],
            "width_m": round6(width),
            "clearance_m": rules["door_clearance_m"],
            "allowed_connection_types": SUPPORTED_CONNECTION_TYPES,
            "priority": "primary",
            "local_socket_id": socket["socket_id"],
            "edge": socket["edge"],
            "door_measurement_rules": rules,
        }
        building_plugs.append(plug)
        plot_plugs.append(
            {
                "plug_id": f"{graph['map_plot_id']}.entry_zone",
                "owner_id": graph["map_plot_id"],
                "owner_type": "building_plot",
                "plug_type": "plot_access",
                "position": plug["position"],
                "direction": plug["direction"],
                "width_m": round6(width + 0.4),
                "clearance_m": 2.2,
                "allowed_connection_types": SUPPORTED_CONNECTION_TYPES,
                "priority": "primary",
                "source_building_plug_id": plug["plug_id"],
            }
        )
    return building_plugs, plot_plugs


def road_by_id(compiled: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {road["road_id"]: road for road in compiled["roads"]}


def target_road_for_plug(plug_id: str, policy: dict[str, Any]) -> tuple[str, str]:
    target = policy["road_targets_by_building_plug"].get(plug_id)
    if isinstance(target, dict) and target.get("road_id") and target.get("suffix"):
        return str(target["road_id"]), str(target["suffix"])
    fail(f"no target road declaration for {plug_id}")


def build_road_plugs(
    compiled: dict[str, Any],
    refined_graph: dict[str, Any],
    building_plugs: list[dict[str, Any]],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    roads = road_by_id(compiled)
    plugs: list[dict[str, Any]] = []
    for building_plug in building_plugs:
        road_id, suffix = target_road_for_plug(building_plug["plug_id"], policy)
        road = roads[road_id]
        projection = nearest_polyline_projection(float(building_plug["position"][0]), float(building_plug["position"][1]), road["points"])
        px, py = float(projection["position"][0]), float(projection["position"][1])
        z = terrain_height(refined_graph, px, py) + 0.08
        to_building = normalize2(float(building_plug["position"][0]) - px, float(building_plug["position"][1]) - py)
        plugs.append(
            {
                "plug_id": f"{road_id}.{suffix}",
                "owner_id": road_id,
                "owner_type": "road",
                "plug_type": "road_threshold",
                "position": [round6(px), round6(py), round6(z)],
                "direction": [to_building[0], to_building[1], 0.0],
                "width_m": round6(float(road["width_m"])),
                "clearance_m": 99.0,
                "allowed_connection_types": SUPPORTED_CONNECTION_TYPES,
                "priority": "candidate",
                "road_station_m": round6(float(projection["station_m"])),
                "road_tangent": [round6(float(projection["tangent"][0])), round6(float(projection["tangent"][1])), 0.0],
                "source_building_plug_id": building_plug["plug_id"],
            }
        )
    for road in compiled["roads"]:
        for index, point in enumerate((road["points"][0], road["points"][-1])):
            z = terrain_height(refined_graph, float(point[0]), float(point[1])) + 0.08
            plugs.append(
                {
                    "plug_id": f"{road['road_id']}.endpoint_{index}",
                    "owner_id": road["road_id"],
                    "owner_type": "road",
                    "plug_type": "road_endpoint",
                    "position": [round6(float(point[0])), round6(float(point[1])), round6(z)],
                    "direction": [1.0, 0.0, 0.0],
                    "width_m": round6(float(road["width_m"])),
                    "clearance_m": 99.0,
                    "allowed_connection_types": SUPPORTED_CONNECTION_TYPES,
                    "priority": "secondary",
                }
            )
    return plugs


def plug_lookup(plugs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {plug["plug_id"]: plug for plug in plugs}


def route_samples(start: list[float], end: list[float], count: int = 5) -> list[list[float]]:
    return [
        [
            round6(float(start[0]) + (float(end[0]) - float(start[0])) * index / (count - 1)),
            round6(float(start[1]) + (float(end[1]) - float(start[1])) * index / (count - 1)),
            round6(float(start[2]) + (float(end[2]) - float(start[2])) * index / (count - 1)),
        ]
        for index in range(count)
    ]


def inherited_connection_dimensions(declaration: dict[str, Any], from_plug: dict[str, Any], to_plug: dict[str, Any]) -> dict[str, float]:
    if declaration.get("dimension_source") != "door_measurement_rules":
        return {
            "width_m": float(declaration["width_m"]),
            "min_clearance_m": float(declaration["min_clearance_m"]),
            "vertical_overbuild_margin_m": float(declaration.get("union_policy", {}).get("vertical_overbuild_margin_m", 0.0)),
        }
    from_rules = from_plug.get("door_measurement_rules", {})
    to_rules = to_plug.get("door_measurement_rules", {})
    if not from_rules or not to_rules:
        return {
            "width_m": float(declaration["width_m"]),
            "min_clearance_m": float(declaration["min_clearance_m"]),
            "vertical_overbuild_margin_m": float(declaration.get("union_policy", {}).get("vertical_overbuild_margin_m", 0.0)),
        }
    width = min(float(from_rules["recommended_connector_width_m"]), float(to_rules["recommended_connector_width_m"]))
    clearance = min(float(from_rules["door_clearance_m"]), float(to_rules["door_clearance_m"]))
    margin = max(float(from_rules["vertical_overbuild_margin_m"]), float(to_rules["vertical_overbuild_margin_m"]))
    return {
        "width_m": width,
        "min_clearance_m": max(float(declaration["min_clearance_m"]), clearance - 0.25),
        "vertical_overbuild_margin_m": margin,
    }


def validate_and_generate_connection(
    declaration: dict[str, Any],
    plugs: dict[str, dict[str, Any]],
    semantic_graph: dict[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []
    if declaration["connection_type"] not in SUPPORTED_CONNECTION_TYPES:
        reasons.append(f"unsupported_connection_type:{declaration['connection_type']}")
    from_plug = plugs.get(declaration["from_plug"])
    to_plug = plugs.get(declaration["to_plug"])
    if from_plug is None:
        reasons.append(f"missing_from_plug:{declaration['from_plug']}")
    if to_plug is None:
        reasons.append(f"missing_to_plug:{declaration['to_plug']}")
    if from_plug is None or to_plug is None:
        return {**declaration, "status": "fail", "fail_reasons": reasons}
    if declaration["connection_type"] not in from_plug["allowed_connection_types"]:
        reasons.append("connection_type_not_allowed_by_from_plug")
    if declaration["connection_type"] not in to_plug["allowed_connection_types"]:
        reasons.append("connection_type_not_allowed_by_to_plug")
    inherited_dimensions = inherited_connection_dimensions(declaration, from_plug, to_plug)
    width = inherited_dimensions["width_m"]
    min_clearance_m = inherited_dimensions["min_clearance_m"]
    if width < float(declaration["min_width"]):
        reasons.append("width_below_min_width")
    door_clearance = min(float(from_plug["clearance_m"]), float(to_plug["clearance_m"]))
    if door_clearance < min_clearance_m:
        reasons.append("clearance_below_min_clearance")
    dx = float(to_plug["position"][0]) - float(from_plug["position"][0])
    dy = float(to_plug["position"][1]) - float(from_plug["position"][1])
    dz = float(to_plug["position"][2]) - float(from_plug["position"][2])
    horizontal_length = max(math.hypot(dx, dy), 1e-6)
    slope = abs(dz) / horizontal_length
    vertical_envelope_m = door_clearance + inherited_dimensions["vertical_overbuild_margin_m"]
    elevation_gap_m = abs(dz)
    if slope > float(declaration["max_slope"]):
        reasons.append(f"slope_exceeds_max:{round6(slope)}>{declaration['max_slope']}")
    samples = route_samples(from_plug["position"], to_plug["position"])
    sample_semantics = [surface_semantics(semantic_graph, sample[0], sample[1]) for sample in samples]
    if declaration.get("avoid_fall_hazard") and any("fall_hazard" in semantics for semantics in sample_semantics):
        reasons.append("route_intersects_fall_hazard")
    if declaration.get("avoid_blocked"):
        blocked_bad = any(
            "blocked" in semantics and "building_pad" not in semantics and "road" not in semantics for semantics in sample_semantics
        )
        if blocked_bad:
            reasons.append("route_intersects_blocked_surface")
    status = "fail" if reasons else "pass"
    path = {
        "path_id": f"{declaration['connection_id']}_path",
        "route_policy": declaration["deterministic_route_policy"],
        "route_points": samples,
        "surface": declaration["surface"],
        "width_m": round6(width),
        "horizontal_length_m": round6(horizontal_length),
        "elevation_gap_m": round6(elevation_gap_m),
        "slope": round6(slope),
        "vertical_envelope_m": round6(vertical_envelope_m),
        "vertical_overbuild_margin_m": round6(inherited_dimensions["vertical_overbuild_margin_m"]),
        "dimension_source": declaration.get("dimension_source", "declaration"),
        "door_measurement_rules_applied": declaration.get("dimension_source") == "door_measurement_rules",
        "sample_semantics": sample_semantics,
        "connector_geometry": {
            "primitive": "strip",
            "width_m": round6(width),
            "vertical_envelope_m": round6(vertical_envelope_m),
            "start_plug_position": from_plug["position"],
            "end_plug_position": to_plug["position"],
        },
    }
    return {
        **declaration,
        "status": status,
        "fail_reasons": reasons,
        "from_plug_record": from_plug,
        "to_plug_record": to_plug,
        "generated_path": path if status == "pass" else None,
        "validation": {
            "width_ok": width >= float(declaration["min_width"]),
            "slope_ok": slope <= float(declaration["max_slope"]),
            "clearance_ok": door_clearance >= min_clearance_m,
            "door_measurement_rules_inherited": declaration.get("dimension_source") != "door_measurement_rules"
            or (
                bool(from_plug.get("door_measurement_rules"))
                and bool(to_plug.get("door_measurement_rules"))
                and width > 0.0
                and vertical_envelope_m > door_clearance
            ),
            "length_and_elevation_gap_recorded": horizontal_length > 0.0 and elevation_gap_m >= 0.0,
            "avoid_fall_hazard_ok": "route_intersects_fall_hazard" not in reasons,
            "avoid_blocked_ok": "route_intersects_blocked_surface" not in reasons,
            "bad_connection_failed_with_reason": status == "fail" and bool(reasons),
        },
    }


def compile_graph() -> dict[str, Any]:
    if not MAP_V2_PLACEMENT_PATH.exists():
        map_v2_compile.main()
    policy = load_connection_policy()
    map_v2 = load_json(MAP_V2_PLACEMENT_PATH)
    compiled = load_json(COMPILED_MAP_PATH)
    semantic_graph = load_json(SEMANTIC_GRAPH_PATH)
    refined_graph = load_json(REFINED_GRAPH_PATH)
    active_declarations = policy["active_connection_declarations"]
    rejected_declarations = policy["rejected_connection_declarations"]
    building_plugs, plot_plugs = build_building_and_plot_plugs(map_v2, refined_graph, policy)
    road_plugs = build_road_plugs(compiled, refined_graph, building_plugs, policy)
    all_plugs = building_plugs + road_plugs + plot_plugs
    plugs_by_id = plug_lookup(all_plugs)
    active_connections = [
        validate_and_generate_connection(declaration, plugs_by_id, semantic_graph)
        for declaration in active_declarations
    ]
    rejected_connections = [
        validate_and_generate_connection(declaration, plugs_by_id, semantic_graph)
        for declaration in rejected_declarations
    ]
    validation = validate_graph(building_plugs, road_plugs, plot_plugs, active_connections, rejected_connections, semantic_graph, refined_graph)
    return {
        "schema": "plug_based_connection_graph_v0",
        "created_at_utc": now_iso(),
        "source_files": {
            "map_v2_building_variant_placement": str(MAP_V2_PLACEMENT_PATH.relative_to(ROOT)),
            "compiled_map": str(COMPILED_MAP_PATH.relative_to(ROOT)),
            "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
            "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
            "connection_policy": str(CONNECTION_POLICY_PATH.relative_to(ROOT)),
        },
        "supported_connection_types": SUPPORTED_CONNECTION_TYPES,
        "plug_sets": {
            "building_entrance_plugs": building_plugs,
            "road_plugs": road_plugs,
            "plot_plugs": plot_plugs,
        },
        "developer_declared_connections": active_declarations,
        "connections": active_connections,
        "rejected_connection_declarations": rejected_declarations,
        "rejected_connections": rejected_connections,
        "generated_connector_paths": [
            connection["generated_path"] for connection in active_connections if connection.get("generated_path")
        ],
        "placed_building_graphs": map_v2["placed_building_graphs"],
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def validate_graph(
    building_plugs: list[dict[str, Any]],
    road_plugs: list[dict[str, Any]],
    plot_plugs: list[dict[str, Any]],
    connections: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    semantic_graph: dict[str, Any],
    refined_graph: dict[str, Any],
) -> dict[str, Any]:
    validation = {
        "building_entrance_plug_count": len(building_plugs),
        "road_plug_count": len(road_plugs),
        "plot_plug_count": len(plot_plugs),
        "connection_count": len(connections),
        "every_building_has_named_entrance_plugs": len(building_plugs) == 3 and all("." in plug["plug_id"] for plug in building_plugs),
        "roads_expose_named_plug_candidates": len(road_plugs) >= 3 and all("." in plug["plug_id"] for plug in road_plugs),
        "plot_plugs_exposed": len(plot_plugs) == 3,
        "connections_are_declared_as_plug_pairs": all(conn.get("from_plug") and conn.get("to_plug") for conn in connections),
        "connection_type_is_configurable": all(conn["connection_type"] in SUPPORTED_CONNECTION_TYPES for conn in connections),
        "paths_generated_from_plug_contracts": all(conn["status"] == "pass" and conn.get("generated_path") for conn in connections),
        "paths_validate_width_slope_clearance": all(
            conn["validation"]["width_ok"] and conn["validation"]["slope_ok"] and conn["validation"]["clearance_ok"]
            for conn in connections
        ),
        "building_union_uses_door_plug_contracts": any(
            conn["status"] == "pass"
            and conn["connection_type"] == "bridge_link"
            and conn.get("union_policy", {}).get("endpoint_rule") == "use_building_door_plugs"
            and conn["from_plug_record"]["owner_type"] == "building_graph"
            and conn["to_plug_record"]["owner_type"] == "building_graph"
            and conn["validation"]["door_measurement_rules_inherited"]
            for conn in connections
        ),
        "building_union_records_length_and_elevation_gap": any(
            conn["status"] == "pass"
            and conn["connection_type"] == "bridge_link"
            and conn["generated_path"]["horizontal_length_m"] > 0.0
            and "elevation_gap_m" in conn["generated_path"]
            for conn in connections
        ),
        "building_union_vertical_envelope_overbuilt": any(
            conn["status"] == "pass"
            and conn["connection_type"] == "bridge_link"
            and conn["generated_path"]["vertical_envelope_m"]
            > min(float(conn["from_plug_record"]["clearance_m"]), float(conn["to_plug_record"]["clearance_m"]))
            for conn in connections
        ),
        "bad_connections_fail_with_reason": all(conn["status"] == "fail" and bool(conn["fail_reasons"]) for conn in rejected),
        "render_preview_note": "not_validated_by_compiler; Blender proof render must consume generated_connector_paths",
        "terrain_cracks_remain_zero": int(semantic_graph["validation"]["cracked_seam_count"]) == 0
        and int(refined_graph["validation"]["cracked_seam_count"]) == 0,
        "semantic_cracked_seam_count": semantic_graph["validation"]["cracked_seam_count"],
        "refined_cracked_seam_count": refined_graph["validation"]["cracked_seam_count"],
        "connection_status_counts": {
            "pass": sum(1 for conn in connections if conn["status"] == "pass"),
            "fail": sum(1 for conn in connections if conn["status"] == "fail"),
        },
        "rejected_status_counts": {
            "pass": sum(1 for conn in rejected if conn["status"] == "pass"),
            "fail": sum(1 for conn in rejected if conn["status"] == "fail"),
        },
        "no_claims": NO_CLAIMS,
    }
    required = [
        "every_building_has_named_entrance_plugs",
        "roads_expose_named_plug_candidates",
        "connections_are_declared_as_plug_pairs",
        "connection_type_is_configurable",
        "paths_generated_from_plug_contracts",
        "paths_validate_width_slope_clearance",
        "building_union_uses_door_plug_contracts",
        "building_union_records_length_and_elevation_gap",
        "building_union_vertical_envelope_overbuilt",
        "bad_connections_fail_with_reason",
        "terrain_cracks_remain_zero",
    ]
    failed = [key for key in required if not validation[key]]
    if failed:
        fail(f"plug based connection graph validation failed: {failed}")
    return validation


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Plug-Based Connection Graph v0 Report",
        "",
        "Entrances, roads, and plots expose named plugs. Connections are declared as plug pairs and only then solved into connector paths.",
        "",
        "## Summary",
        "",
        f"- building_entrance_plug_count: {validation['building_entrance_plug_count']}",
        f"- road_plug_count: {validation['road_plug_count']}",
        f"- plot_plug_count: {validation['plot_plug_count']}",
        f"- connection_count: {validation['connection_count']}",
        f"- connection_status_counts: {validation['connection_status_counts']}",
        f"- rejected_status_counts: {validation['rejected_status_counts']}",
        f"- terrain_cracks_remain_zero: {validation['terrain_cracks_remain_zero']}",
        f"- building_union_uses_door_plug_contracts: {validation['building_union_uses_door_plug_contracts']}",
        f"- building_union_vertical_envelope_overbuilt: {validation['building_union_vertical_envelope_overbuilt']}",
        "",
        "## Connections",
        "",
    ]
    for conn in data["connections"]:
        path = conn["generated_path"]
        lines.extend(
            [
                f"### {conn['connection_id']}",
                "",
                f"- from_plug: {conn['from_plug']}",
                f"- to_plug: {conn['to_plug']}",
                f"- connection_type: {conn['connection_type']}",
                f"- status: {conn['status']}",
                f"- width_m: {conn['width_m']}",
                f"- resolved_width_m: {path['width_m'] if path else 'n/a'}",
                f"- vertical_envelope_m: {path['vertical_envelope_m'] if path else 'n/a'}",
                f"- elevation_gap_m: {path['elevation_gap_m'] if path else 'n/a'}",
                f"- slope: {path['slope'] if path else 'n/a'}",
                f"- horizontal_length_m: {path['horizontal_length_m'] if path else 'n/a'}",
                "",
            ]
        )
    lines.extend(["## Rejected Declarations", ""])
    for conn in data["rejected_connections"]:
        lines.extend(
            [
                f"### {conn['connection_id']}",
                "",
                f"- status: {conn['status']}",
                f"- fail_reasons: {conn['fail_reasons']}",
                "",
            ]
        )
    lines.extend(["## Claim Limits", "", "- no production approval", "- no structural safety claim", "- no fabrication readiness claim", "- no historical accuracy claim", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "schema": "plug_based_connection_graph_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "connection_graph": str(GRAPH_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": {
            "every_building_has_named_entrance_plugs": validation["every_building_has_named_entrance_plugs"],
            "roads_expose_named_plug_candidates": validation["roads_expose_named_plug_candidates"],
            "connections_are_declared_as_plug_pairs": validation["connections_are_declared_as_plug_pairs"],
            "connection_type_is_configurable": validation["connection_type_is_configurable"],
            "paths_generated_from_plug_contracts": validation["paths_generated_from_plug_contracts"],
            "paths_validate_width_slope_clearance": validation["paths_validate_width_slope_clearance"],
            "building_union_uses_door_plug_contracts": validation["building_union_uses_door_plug_contracts"],
            "building_union_records_length_and_elevation_gap": validation["building_union_records_length_and_elevation_gap"],
            "building_union_vertical_envelope_overbuilt": validation["building_union_vertical_envelope_overbuilt"],
            "bad_connections_fail_with_reason": validation["bad_connections_fail_with_reason"],
            "terrain_cracks_remain_zero": validation["terrain_cracks_remain_zero"],
        },
        "non_acceptance_notes": {
            "render_preview": validation["render_preview_note"],
        },
        "counts": {
            "building_entrance_plug_count": validation["building_entrance_plug_count"],
            "road_plug_count": validation["road_plug_count"],
            "plot_plug_count": validation["plot_plug_count"],
            "connection_count": validation["connection_count"],
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = compile_graph()
    GRAPH_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {GRAPH_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "building_plugs={building_entrance_plug_count} road_plugs={road_plug_count} connections={connection_count}".format(
            **data["validation"]
        )
    )


if __name__ == "__main__":
    main()
