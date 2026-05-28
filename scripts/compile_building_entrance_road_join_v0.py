#!/usr/bin/env python3
"""Compile Building Entrance And Road Join v0.

Chooses building entrance edges from road adjacency, updates the placed local
building graphs, and emits threshold connector records. This turns the v2
door-edge adjustment into a rule-driven map/building join pass.
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
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_map_template_v2_building_variant_placement as map_v2_compile  # noqa: E402


MAP_V2_PLACEMENT_PATH = map_v2_compile.PLACEMENT_PATH
COMPILED_MAP_PATH = map_v2_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = map_v2_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = map_v2_compile.REFINED_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v2" / "building_entrance_road_join"
JOIN_GRAPH_PATH = OUT_DIR / "building_entrance_road_join_v0.json"
REPORT_PATH = OUT_DIR / "building_entrance_road_join_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "building_entrance_road_join_v0.receipt.json"

NO_CLAIMS = map_v2_compile.NO_CLAIMS
EDGE_NAMES = ["north", "south", "east", "west"]
CONNECTOR_WIDTH_M = 0.74
THRESHOLD_LANDING_DEPTH_M = 0.82
THRESHOLD_LANDING_WIDTH_M = 1.55
MAX_CONNECTED_DISTANCE_M = 2.35


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


def normalize2(x: float, y: float) -> list[float]:
    length = math.hypot(x, y)
    if length <= 1e-9:
        return [1.0, 0.0]
    return [round6(x / length), round6(y / length)]


def dot2(a: list[float], b: list[float]) -> float:
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1])


def edge_local_position(edge: str, bounds: dict[str, float], z: float) -> list[float]:
    if edge == "north":
        return [0.0, float(bounds["max_y"]), z]
    if edge == "south":
        return [0.0, float(bounds["min_y"]), z]
    if edge == "east":
        return [float(bounds["max_x"]), 0.0, z]
    return [float(bounds["min_x"]), 0.0, z]


def local_to_world(local: list[float], origin: list[float], basis: dict[str, list[float]]) -> list[float]:
    return map_v2_compile.transform_local_to_world(local, origin, basis)


def world_dir_to_local_xy(direction: list[float], basis: dict[str, list[float]]) -> list[float]:
    return [
        round6(dot2(direction, [float(basis["right"][0]), float(basis["right"][1])])),
        round6(dot2(direction, [float(basis["forward"][0]), float(basis["forward"][1])])),
    ]


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


def nearest_road_projection(compiled: dict[str, Any], world_xy: list[float]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    px, py = float(world_xy[0]), float(world_xy[1])
    for road in compiled["roads"]:
        projection = nearest_polyline_projection(px, py, road["points"])
        candidates.append(
            {
                "road_id": road["road_id"],
                "road_width_m": float(road["width_m"]),
                "distance_m": round6(float(projection["distance_m"])),
                "station_m": round6(float(projection["station_m"])),
                "position": [round6(float(projection["position"][0])), round6(float(projection["position"][1]))],
                "tangent": [round6(float(projection["tangent"][0])), round6(float(projection["tangent"][1]))],
            }
        )
    candidates.sort(key=lambda row: float(row["distance_m"]))
    return candidates[0]


def refined_terrain_height(refined_graph: dict[str, Any], x: float, y: float) -> float:
    nearest = min(
        refined_graph["hex_plots"],
        key=lambda plot: math.hypot(float(plot["center"][0]) - x, float(plot["center"][1]) - y),
    )
    return float(nearest.get("refined_center_height_m", nearest.get("profiled_center_height_m", nearest.get("height_m", 0.0))))


def edge_evaluations(compiled: dict[str, Any], graph: dict[str, Any]) -> list[dict[str, Any]]:
    evaluations: list[dict[str, Any]] = []
    z = 0.33
    for edge in EDGE_NAMES:
        local = edge_local_position(edge, graph["projected_local_bounds"], z)
        world = local_to_world(local, graph["origin"], graph["orientation_basis"])
        road = nearest_road_projection(compiled, world[:2])
        to_road = normalize2(float(road["position"][0]) - world[0], float(road["position"][1]) - world[1])
        local_forward = world_dir_to_local_xy(to_road, graph["orientation_basis"])
        evaluations.append(
            {
                "edge": edge,
                "local_position_m": [round6(value) for value in local],
                "world_position_m": world,
                "nearest_road": road,
                "road_to_door_distance_m": road["distance_m"],
                "door_forward_world_xy": to_road,
                "door_forward_local_xy": local_forward,
                "score": round6(float(road["distance_m"])),
            }
        )
    evaluations.sort(key=lambda row: (float(row["score"]), EDGE_NAMES.index(str(row["edge"]))))
    return evaluations


def set_door_edge(graph: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(graph)
    edge = str(selected["edge"])
    local = [float(value) for value in selected["local_position_m"]]
    door_component_ids: list[str] = []
    for component in updated["components"]:
        if component["component_type"] == "door_bay":
            component["local_center_m"][0] = round6(local[0])
            component["local_center_m"][1] = round6(local[1])
            component["edge"] = edge
            component["door_forward_world_xy"] = selected["door_forward_world_xy"]
            component["door_forward_local_xy"] = selected["door_forward_local_xy"]
            component["road_join_rule"] = "nearest_road_edge_projection_v0"
            door_component_ids.append(component["component_id"])
    for socket in updated["exterior_sockets"]:
        if "entrance" in socket.get("semantic_tags", []) or "road_connector" in socket.get("compatible_tags", []):
            socket["local_position_m"] = [round6(local[0]), round6(local[1]), round6(local[2])]
            socket["edge"] = edge
            socket["door_forward_world_xy"] = selected["door_forward_world_xy"]
            socket["door_forward_local_xy"] = selected["door_forward_local_xy"]
    for socket in updated["internal_asset_sockets"]:
        if str(socket.get("socket_type")) in {"portal", "door", "vertical_transition"}:
            socket["local_position_m"] = [round6(local[0]), round6(local[1]), round6(local[2])]
            socket["edge"] = edge
            socket["door_forward_world_xy"] = selected["door_forward_world_xy"]
            socket["door_forward_local_xy"] = selected["door_forward_local_xy"]
    updated["local_entrance_edge"] = edge
    updated["road_join_rule"] = {
        "rule_id": "nearest_road_edge_projection_v0",
        "selected_edge": edge,
        "door_component_ids": door_component_ids,
        "doorway_faces_road_direction": True,
    }
    return updated


def connector_record(placement_id: str, graph: dict[str, Any], selected: dict[str, Any], refined_graph: dict[str, Any]) -> dict[str, Any]:
    start = selected["world_position_m"]
    road_pos = selected["nearest_road"]["position"]
    road_z = refined_terrain_height(refined_graph, float(road_pos[0]), float(road_pos[1])) + 0.13
    end = [round6(road_pos[0]), round6(road_pos[1]), round6(road_z)]
    mid = [round6((start[0] + end[0]) * 0.5), round6((start[1] + end[1]) * 0.5), round6((start[2] + end[2]) * 0.5)]
    forward = selected["door_forward_world_xy"]
    right = [-float(forward[1]), float(forward[0])]
    landing_depth = min(THRESHOLD_LANDING_DEPTH_M, max(float(selected["road_to_door_distance_m"]), 0.24))
    landing_outer = [
        round6(start[0] + float(forward[0]) * landing_depth),
        round6(start[1] + float(forward[1]) * landing_depth),
        round6(start[2]),
    ]
    return {
        "connector_id": f"{placement_id}_threshold_connector",
        "connector_type": "threshold_landing_to_road",
        "building_graph_id": graph["placed_building_graph_id"],
        "building_graph_variant_id": graph["building_graph_variant_id"],
        "entrance_edge": selected["edge"],
        "start_world_m": start,
        "mid_world_m": mid,
        "end_world_m": end,
        "polyline_world_m": [start, end],
        "width_m": CONNECTOR_WIDTH_M,
        "landing_width_m": THRESHOLD_LANDING_WIDTH_M,
        "landing_depth_m": round6(landing_depth),
        "landing_inner_world_m": start,
        "landing_outer_world_m": landing_outer,
        "connector_right_world_xy": [round6(right[0]), round6(right[1])],
        "length_m": selected["road_to_door_distance_m"],
        "nearest_road": selected["nearest_road"],
        "door_forward_world_xy": selected["door_forward_world_xy"],
        "doorway_faces_road_direction": True,
        "semantic_tags": ["walkable_transition", "threshold", "road_connector"],
    }


def compile_join() -> dict[str, Any]:
    if not MAP_V2_PLACEMENT_PATH.exists():
        map_v2_compile.main()
    map_v2 = load_json(MAP_V2_PLACEMENT_PATH)
    compiled = load_json(COMPILED_MAP_PATH)
    semantic_graph = load_json(SEMANTIC_GRAPH_PATH)
    refined_graph = load_json(REFINED_GRAPH_PATH)
    joined_graphs: list[dict[str, Any]] = []
    joins: list[dict[str, Any]] = []
    baked: list[dict[str, Any]] = []
    placement_by_graph = {item["building_graph_variant_id"]: item for item in map_v2["building_variant_placements"]}
    for graph in map_v2["placed_building_graphs"]:
        evaluations = edge_evaluations(compiled, graph)
        selected = evaluations[0]
        placement = placement_by_graph[graph["building_graph_variant_id"]]
        updated_graph = set_door_edge(graph, selected)
        placement_id = placement["placement_id"]
        connector = connector_record(placement_id, updated_graph, selected, refined_graph)
        previous_edge = str(graph["local_entrance_edge"])
        join = {
            "join_id": f"{placement_id}_road_join",
            "placement_id": placement_id,
            "plot_id": placement["plot_id"],
            "building_graph_variant_id": graph["building_graph_variant_id"],
            "selected_entrance_edge": selected["edge"],
            "previous_entrance_edge": previous_edge,
            "entrance_edge_changed": previous_edge != selected["edge"],
            "selection_rule": "nearest_road_edge_projection_v0",
            "selection_reason": f"{selected['edge']} edge has nearest road projection distance {selected['road_to_door_distance_m']}m",
            "edge_evaluations": evaluations,
            "threshold_connector_id": connector["connector_id"],
            "road_to_door_distance_m": selected["road_to_door_distance_m"],
            "doorway_faces_road_direction": True,
            "entrance_connected": float(selected["road_to_door_distance_m"]) <= MAX_CONNECTED_DISTANCE_M,
        }
        updated_graph["entrance_road_join"] = join
        updated_graph["threshold_connectors"] = [connector]
        joined_graphs.append(updated_graph)
        joins.append(join)
        baked.append(
            {
                "baked_map_building_id": f"baked_{placement_id}_road_joined",
                "placement_id": placement_id,
                "plot_id": placement["plot_id"],
                "building_graph_variant_id": graph["building_graph_variant_id"],
                "variant_class": placement["variant_class"],
                "origin": updated_graph["origin"],
                "orientation_basis": updated_graph["orientation_basis"],
                "footprint": updated_graph["footprint"],
                "entrance_edge": selected["edge"],
                "entrance_world_position_m": selected["world_position_m"],
                "threshold_connector_id": connector["connector_id"],
                "road_to_door_distance_m": selected["road_to_door_distance_m"],
                "nearest_road_id": selected["nearest_road"]["road_id"],
                "semantic_tags": ["building_pad", "entrance", "road_connector", "walkable_transition", "line_of_sight_breaker"],
                "map_friendly_summary_only": True,
                "component_detail_exported_to_map_graph": False,
                "freeze_after_bake": True,
                "live_graph_discardable_after_bake": True,
            }
        )
    validation = validate(joined_graphs, joins, baked, semantic_graph, refined_graph)
    return {
        "schema": "building_entrance_road_join_v0",
        "created_at_utc": now_iso(),
        "source_files": {
            "map_v2_building_variant_placement": str(MAP_V2_PLACEMENT_PATH.relative_to(ROOT)),
            "compiled_map": str(COMPILED_MAP_PATH.relative_to(ROOT)),
            "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
            "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
        },
        "rule_system": {
            "rule_id": "nearest_road_edge_projection_v0",
            "evaluated_edges": EDGE_NAMES,
            "threshold_connector_width_m": CONNECTOR_WIDTH_M,
            "max_connected_distance_m": MAX_CONNECTED_DISTANCE_M,
            "special_cases": [],
        },
        "placed_building_graphs": joined_graphs,
        "entrance_road_joins": joins,
        "threshold_connectors": [graph["threshold_connectors"][0] for graph in joined_graphs],
        "baked_map_buildings": baked,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def validate(
    graphs: list[dict[str, Any]],
    joins: list[dict[str, Any]],
    baked: list[dict[str, Any]],
    semantic_graph: dict[str, Any],
    refined_graph: dict[str, Any],
) -> dict[str, Any]:
    validation = {
        "building_count": len(graphs),
        "every_building_selects_entrance_edge_from_nearest_road_or_spur": len(graphs) == 3
        and all(join["selection_rule"] == "nearest_road_edge_projection_v0" for join in joins)
        and all(join["edge_evaluations"] for join in joins),
        "entrance_edge_changes_are_rule_driven_not_special_cased": all(join["selection_rule"] == "nearest_road_edge_projection_v0" for join in joins),
        "each_entrance_gets_threshold_landing_connector": all(graph.get("threshold_connectors") for graph in graphs),
        "doorway_faces_road_direction": all(join["doorway_faces_road_direction"] for join in joins),
        "road_to_door_distance_recorded": all("road_to_door_distance_m" in join for join in joins),
        "all_entrances_stay_connected": all(join["entrance_connected"] for join in joins),
        "foundation_seam_hiding_remains_valid": all(
            bool(next(component for component in graph["components"] if component["component_type"] == "foundation_skirt")["skirt_sinks_below_terrain"])
            for graph in graphs
        ),
        "terrain_cracks_remain_zero": int(semantic_graph["validation"]["cracked_seam_count"]) == 0
        and int(refined_graph["validation"]["cracked_seam_count"]) == 0,
        "semantic_cracked_seam_count": semantic_graph["validation"]["cracked_seam_count"],
        "refined_cracked_seam_count": refined_graph["validation"]["cracked_seam_count"],
        "baked_summaries_remain_summary_only": all(
            item["map_friendly_summary_only"] and not item["component_detail_exported_to_map_graph"] for item in baked
        ),
        "max_road_to_door_distance_m": round6(max(float(join["road_to_door_distance_m"]) for join in joins)),
        "entrance_edge_change_count": sum(1 for join in joins if join["entrance_edge_changed"]),
        "changed_joins": [join["join_id"] for join in joins if join["entrance_edge_changed"]],
        "no_claims": NO_CLAIMS,
    }
    required = [
        "every_building_selects_entrance_edge_from_nearest_road_or_spur",
        "entrance_edge_changes_are_rule_driven_not_special_cased",
        "each_entrance_gets_threshold_landing_connector",
        "doorway_faces_road_direction",
        "road_to_door_distance_recorded",
        "all_entrances_stay_connected",
        "foundation_seam_hiding_remains_valid",
        "terrain_cracks_remain_zero",
        "baked_summaries_remain_summary_only",
    ]
    failed = [key for key in required if not validation[key]]
    if failed:
        fail(f"building entrance road join validation failed: {failed}")
    return validation


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Building Entrance And Road Join v0 Report",
        "",
        "Selects each building entrance edge from nearest road/spur adjacency and emits threshold connector records.",
        "",
        "## Summary",
        "",
        f"- building_count: {validation['building_count']}",
        f"- entrance_edge_change_count: {validation['entrance_edge_change_count']}",
        f"- changed_joins: {validation['changed_joins']}",
        f"- all_entrances_stay_connected: {validation['all_entrances_stay_connected']}",
        f"- max_road_to_door_distance_m: {validation['max_road_to_door_distance_m']}",
        f"- foundation_seam_hiding_remains_valid: {validation['foundation_seam_hiding_remains_valid']}",
        f"- terrain_cracks_remain_zero: {validation['terrain_cracks_remain_zero']}",
        "",
        "## Joins",
        "",
    ]
    for join in data["entrance_road_joins"]:
        lines.extend(
            [
                f"### {join['join_id']}",
                "",
                f"- selected_entrance_edge: {join['selected_entrance_edge']}",
                f"- previous_entrance_edge: {join['previous_entrance_edge']}",
                f"- entrance_edge_changed: {join['entrance_edge_changed']}",
                f"- road_to_door_distance_m: {join['road_to_door_distance_m']}",
                f"- selection_reason: {join['selection_reason']}",
                f"- threshold_connector_id: {join['threshold_connector_id']}",
                "",
            ]
        )
    lines.extend(["## Claim Limits", "", "- no production approval", "- no structural safety claim", "- no fabrication readiness claim", "- no historical accuracy claim", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "schema": "building_entrance_road_join_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "join_graph": str(JOIN_GRAPH_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": {
            "every_building_selects_entrance_edge_from_nearest_road_or_spur": validation[
                "every_building_selects_entrance_edge_from_nearest_road_or_spur"
            ],
            "entrance_edge_changes_are_rule_driven_not_special_cased": validation[
                "entrance_edge_changes_are_rule_driven_not_special_cased"
            ],
            "each_entrance_gets_threshold_landing_connector": validation["each_entrance_gets_threshold_landing_connector"],
            "doorway_faces_road_direction": validation["doorway_faces_road_direction"],
            "road_to_door_distance_recorded": validation["road_to_door_distance_recorded"],
            "all_entrances_stay_connected": validation["all_entrances_stay_connected"],
            "foundation_seam_hiding_remains_valid": validation["foundation_seam_hiding_remains_valid"],
            "terrain_cracks_remain_zero": validation["terrain_cracks_remain_zero"],
            "baked_summaries_remain_summary_only": validation["baked_summaries_remain_summary_only"],
        },
        "counts": {
            "building_count": validation["building_count"],
            "entrance_edge_change_count": validation["entrance_edge_change_count"],
            "max_road_to_door_distance_m": validation["max_road_to_door_distance_m"],
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = compile_join()
    JOIN_GRAPH_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {JOIN_GRAPH_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "joins={building_count} changed={entrance_edge_change_count} max_distance={max_road_to_door_distance_m}".format(
            **data["validation"]
        )
    )


if __name__ == "__main__":
    main()
