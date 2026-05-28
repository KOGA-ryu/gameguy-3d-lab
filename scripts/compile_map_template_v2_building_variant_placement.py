#!/usr/bin/env python3
"""Compile Map Template v2: Building Variant Placement.

Selects compact/standard/tall local building graph variants for the measured
asset aware map plots, attaches them to the map, and emits map-friendly baked
summaries. Building detail remains in local building graphs.
"""

from __future__ import annotations

import json
import math
import copy
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_building_graph_attachment_v0 as attachment_compile  # noqa: E402
import compile_building_graph_variation_rules_v0 as variation_compile  # noqa: E402


COMPILED_MAP_PATH = attachment_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = attachment_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = attachment_compile.REFINED_GRAPH_PATH
VARIATION_GRAPH_PATH = variation_compile.VARIATION_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v2" / "building_variant_placement"
PLACEMENT_PATH = OUT_DIR / "map_template_v2_building_variant_placement.json"
REPORT_PATH = OUT_DIR / "map_template_v2_building_variant_placement_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "map_template_v2_building_variant_placement.receipt.json"

NO_CLAIMS = attachment_compile.NO_CLAIMS
PLOT_TO_SOURCE_GRAPH = {
    "measured_gatehouse_plot": "gatehouse_graph_v0",
    "measured_watch_plot": "watch_graph_v0",
    "measured_octagon_shrine_plot": "shrine_graph_v0",
}
SMALL_PLOT_AREA_M2 = 30.0
ENTRANCE_ROAD_CONNECT_TOLERANCE_M = 2.0


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


def polygon_area(polygon: list[list[float]]) -> float:
    area = 0.0
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1], strict=False):
        area += float(x1) * float(y2) - float(x2) * float(y1)
    return abs(area) * 0.5


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx = bx - ax
    dy = by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-9:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    qx = ax + dx * t
    qy = ay + dy * t
    return math.hypot(px - qx, py - qy)


def point_to_polyline_distance(px: float, py: float, points: list[list[float]]) -> float:
    return min(
        distance_to_segment(px, py, float(ax), float(ay), float(bx), float(by))
        for (ax, ay), (bx, by) in zip(points, points[1:], strict=False)
    )


def nearest_road(compiled: dict[str, Any], world_xy: list[float]) -> dict[str, Any]:
    px, py = float(world_xy[0]), float(world_xy[1])
    candidates = []
    for road in compiled["roads"]:
        distance = point_to_polyline_distance(px, py, road["points"])
        candidates.append({"road_id": road["road_id"], "distance_m": round6(distance), "width_m": float(road["width_m"])})
    candidates.sort(key=lambda row: row["distance_m"])
    return candidates[0]


def transform_local_to_world(local: list[float], origin: list[float], basis: dict[str, list[float]]) -> list[float]:
    right = basis["right"]
    forward = basis["forward"]
    up = basis["up"]
    return [
        round6(float(origin[0]) + float(local[0]) * float(right[0]) + float(local[1]) * float(forward[0]) + float(local[2]) * float(up[0])),
        round6(float(origin[1]) + float(local[0]) * float(right[1]) + float(local[1]) * float(forward[1]) + float(local[2]) * float(up[1])),
        round6(float(origin[2]) + float(local[0]) * float(right[2]) + float(local[1]) * float(forward[2]) + float(local[2]) * float(up[2])),
    ]


def edge_position(edge: str, bounds: dict[str, float]) -> list[float]:
    if edge == "north":
        return [0.0, float(bounds["max_y"])]
    if edge == "south":
        return [0.0, float(bounds["min_y"])]
    if edge == "east":
        return [float(bounds["max_x"]), 0.0]
    return [float(bounds["min_x"]), 0.0]


def best_road_facing_edge(compiled: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for edge in ["north", "south", "east", "west"]:
        local_xy = edge_position(edge, variant["projected_local_bounds"])
        local = [local_xy[0], local_xy[1], 0.33]
        world = transform_local_to_world(local, variant["origin"], variant["orientation_basis"])
        road = nearest_road(compiled, world[:2])
        candidates.append({"edge": edge, "local_position_m": local, "world_position_m": world, "road": road})
    candidates.sort(key=lambda row: float(row["road"]["distance_m"]))
    return candidates[0]


def apply_door_edge_override(variant: dict[str, Any], edge: str) -> dict[str, Any]:
    placed = copy.deepcopy(variant)
    bounds = placed["projected_local_bounds"]
    local_xy = edge_position(edge, bounds)
    placed["local_entrance_edge"] = edge
    placed["variation_fields"]["door_edge"] = edge
    placed["map_placement_door_edge_override"] = {
        "applied": True,
        "door_edge": edge,
        "reason": "selected_variant_default_entrance_did_not_connect_to_nearest_road",
    }
    for component in placed["components"]:
        if component["component_type"] == "door_bay":
            component["local_center_m"][0] = round6(local_xy[0])
            component["local_center_m"][1] = round6(local_xy[1])
            component["edge"] = edge
    for socket in placed["exterior_sockets"]:
        if "entrance" in socket.get("semantic_tags", []) or "road_connector" in socket.get("compatible_tags", []):
            socket["local_position_m"][0] = round6(local_xy[0])
            socket["local_position_m"][1] = round6(local_xy[1])
            socket["edge"] = edge
    for socket in placed["internal_asset_sockets"]:
        if str(socket.get("socket_type")) in {"portal", "door", "vertical_transition"}:
            socket["local_position_m"][0] = round6(local_xy[0])
            socket["local_position_m"][1] = round6(local_xy[1])
            socket["edge"] = edge
    return placed


def road_connection_for_entrance(compiled: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    entrance = entrance_socket(variant)
    entrance_world = transform_local_to_world(entrance["local_position_m"], variant["origin"], variant["orientation_basis"])
    road = nearest_road(compiled, entrance_world[:2])
    tolerance = max(ENTRANCE_ROAD_CONNECT_TOLERANCE_M, float(road["width_m"]) * 0.5 + 0.75)
    return {
        "entrance": entrance,
        "entrance_world": entrance_world,
        "road": road,
        "tolerance_m": round6(tolerance),
        "road_connected": float(road["distance_m"]) <= tolerance,
    }


def choose_variant_class(plot: dict[str, Any], semantic_graph: dict[str, Any]) -> tuple[str, str]:
    area = polygon_area(plot["polygon"])
    role = str(plot.get("plot_role", ""))
    terrain_context = plot_context(plot, semantic_graph)
    if area < SMALL_PLOT_AREA_M2:
        return "compact", f"small plot area {area:.2f}m2 below {SMALL_PLOT_AREA_M2:.2f}m2"
    if terrain_context["ravine_or_edge_plot"] and "high" not in role:
        return "standard", "ravine/edge-adjacent plot avoids tall variant"
    if "high" in role or "landmark" in role:
        return "tall", f"landmark/high plot role {role}"
    return "standard", f"normal plot area {area:.2f}m2"


def plot_context(plot: dict[str, Any], semantic_graph: dict[str, Any]) -> dict[str, Any]:
    cells = {cell["cell_id"]: cell for cell in semantic_graph.get("semantic_surface_cells", [])}
    semantics: set[str] = set()
    for cell_id in plot.get("occupied_cells", []):
        cell = cells.get(cell_id)
        if cell:
            semantics.update(cell.get("semantics", []))
    return {
        "semantic_tags": sorted(semantics),
        "ravine_or_edge_plot": bool({"fall_hazard", "ledge", "cliff"} & semantics),
    }


def entrance_socket(variant: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        socket
        for socket in variant["exterior_sockets"]
        if "entrance" in socket.get("semantic_tags", []) or "road_connector" in socket.get("compatible_tags", [])
    ]
    if not candidates:
        fail(f"{variant['building_graph_variant_id']} has no exterior entrance socket")
    candidates.sort(key=lambda socket: 0 if "entrance" in socket.get("semantic_tags", []) else 1)
    return candidates[0]


def compile_placements() -> dict[str, Any]:
    if not VARIATION_GRAPH_PATH.exists():
        variation_compile.main()
    compiled = load_json(COMPILED_MAP_PATH)
    semantic_graph = load_json(SEMANTIC_GRAPH_PATH)
    refined_graph = load_json(REFINED_GRAPH_PATH)
    variation_graph = load_json(VARIATION_GRAPH_PATH)
    variants_by_key = {
        (variant["source_building_graph_id"], variant["variant_class"]): variant
        for variant in variation_graph["building_graph_variants"]
    }
    placements: list[dict[str, Any]] = []
    baked_summaries: list[dict[str, Any]] = []
    placed_graphs: list[dict[str, Any]] = []
    for plot in compiled["building_plots"]:
        plot_id = plot["plot_id"]
        if plot_id not in PLOT_TO_SOURCE_GRAPH:
            continue
        source_graph_id = PLOT_TO_SOURCE_GRAPH[plot_id]
        variant_class, reason = choose_variant_class(plot, semantic_graph)
        selected_variant = variants_by_key[(source_graph_id, variant_class)]
        road_check = road_connection_for_entrance(compiled, selected_variant)
        door_edge_adjustment = {"applied": False, "reason": "selected_variant_entrance_already_connects_to_road"}
        variant = selected_variant
        if not road_check["road_connected"]:
            best = best_road_facing_edge(compiled, selected_variant)
            variant = apply_door_edge_override(selected_variant, str(best["edge"]))
            road_check = road_connection_for_entrance(compiled, variant)
            door_edge_adjustment = {
                "applied": True,
                "from_edge": selected_variant["local_entrance_edge"],
                "to_edge": best["edge"],
                "reason": "road-facing edge chosen from plot terrain/road context",
            }
        entrance = road_check["entrance"]
        entrance_world = road_check["entrance_world"]
        road = road_check["road"]
        road_connected = road_check["road_connected"]
        context = plot_context(plot, semantic_graph)
        placement_id = f"map_v2_place_{plot_id}_{variant_class}"
        placed_graph = {
            **variant,
            "placed_building_graph_id": f"placed_{variant['building_graph_variant_id']}",
            "map_variant_placement_id": placement_id,
            "map_plot_id": plot_id,
            "door_edge_adjustment": door_edge_adjustment,
        }
        placed_graphs.append(placed_graph)
        placements.append(
            {
                "placement_id": placement_id,
                "plot_id": plot_id,
                "plot_role": plot.get("plot_role"),
                "source_building_graph_id": source_graph_id,
                "building_graph_variant_id": variant["building_graph_variant_id"],
                "variant_class": variant_class,
                "variant_choice_reason": reason,
                "door_edge_adjustment": door_edge_adjustment,
                "terrain_context": context,
                "attach_socket_id": variant["attach_socket_id"],
                "origin": variant["origin"],
                "orientation_basis": variant["orientation_basis"],
                "footprint": variant["footprint"],
                "entrance": {
                    "socket_id": entrance["socket_id"],
                    "local_position_m": entrance["local_position_m"],
                    "world_position_m": entrance_world,
                    "edge": entrance["edge"],
                    "nearest_road_id": road["road_id"],
                    "nearest_road_distance_m": road["distance_m"],
                    "road_connection_tolerance_m": road_check["tolerance_m"],
                    "connects_to_road": road_connected,
                },
                "foundation_seam_hiding": {
                    "passes": next(component for component in variant["components"] if component["component_type"] == "foundation_skirt")[
                        "skirt_sinks_below_terrain"
                    ],
                    "foundation_depth_m": variant["variation_fields"]["foundation_depth"],
                },
                "asset_scaling": variant["asset_scaling"],
                "bake_policy": variant["bake_policy"],
                "no_claims": NO_CLAIMS,
            }
        )
        baked_summaries.append(
            {
                "baked_map_building_id": f"baked_{placement_id}",
                "placement_id": placement_id,
                "plot_id": plot_id,
                "building_graph_variant_id": variant["building_graph_variant_id"],
                "variant_class": variant_class,
                "origin": variant["origin"],
                "orientation_basis": variant["orientation_basis"],
                "footprint": variant["footprint"],
                "entrance_edge": entrance["edge"],
                "entrance_world_position_m": entrance_world,
                "semantic_tags": ["building_pad", "entrance", "line_of_sight_breaker", "asset_socket"],
                "map_friendly_summary_only": True,
                "component_detail_exported_to_map_graph": False,
                "freeze_after_bake": True,
                "live_graph_discardable_after_bake": True,
            }
        )
    validation = validate(placements, baked_summaries, semantic_graph, refined_graph)
    return {
        "schema": "map_template_v2_building_variant_placement",
        "created_at_utc": now_iso(),
        "source_files": {
            "compiled_map": str(COMPILED_MAP_PATH.relative_to(ROOT)),
            "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
            "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
            "building_graph_variants": str(VARIATION_GRAPH_PATH.relative_to(ROOT)),
        },
        "selection_rules": {
            "small_plot": "compact",
            "normal_plot": "standard",
            "landmark_or_high_plot": "tall",
            "ravine_or_edge_plot": "compact_or_standard_not_tall",
            "small_plot_area_threshold_m2": SMALL_PLOT_AREA_M2,
        },
        "placed_building_graphs": placed_graphs,
        "building_variant_placements": placements,
        "baked_map_buildings": baked_summaries,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def validate(placements: list[dict[str, Any]], baked: list[dict[str, Any]], semantic_graph: dict[str, Any], refined_graph: dict[str, Any]) -> dict[str, Any]:
    variant_classes = sorted({placement["variant_class"] for placement in placements})
    validation = {
        "map_plot_variant_placement_count": len(placements),
        "expected_plot_variant_placement_count": 3,
        "three_map_plots_receive_building_variants": len(placements) == 3,
        "variant_choice_recorded_with_reason": all(p.get("variant_choice_reason") for p in placements),
        "foundation_seam_hiding_still_passes": all(p["foundation_seam_hiding"]["passes"] for p in placements),
        "entrances_connect_to_roads": all(p["entrance"]["connects_to_road"] for p in placements),
        "max_entrance_road_distance_m": round6(max(float(p["entrance"]["nearest_road_distance_m"]) for p in placements)),
        "baked_summaries_remain_summary_only": all(
            item["map_friendly_summary_only"] and not item["component_detail_exported_to_map_graph"] for item in baked
        ),
        "terrain_cracks_remain_zero": int(semantic_graph["validation"]["cracked_seam_count"]) == 0
        and int(refined_graph["validation"]["cracked_seam_count"]) == 0,
        "semantic_cracked_seam_count": semantic_graph["validation"]["cracked_seam_count"],
        "refined_cracked_seam_count": refined_graph["validation"]["cracked_seam_count"],
        "render_has_visible_building_variation": len(variant_classes) >= 2,
        "variant_classes_used": variant_classes,
        "asset_scaling_applied_count": sum(1 for p in placements if p["asset_scaling"]["asset_scaling_applied"]),
        "no_claims": NO_CLAIMS,
    }
    required = [
        "three_map_plots_receive_building_variants",
        "variant_choice_recorded_with_reason",
        "foundation_seam_hiding_still_passes",
        "entrances_connect_to_roads",
        "baked_summaries_remain_summary_only",
        "terrain_cracks_remain_zero",
        "render_has_visible_building_variation",
    ]
    failed = [key for key in required if not validation[key]]
    if validation["asset_scaling_applied_count"] != 0:
        failed.append("asset_scaling_applied_count")
    if failed:
        fail(f"map template v2 building variant placement validation failed: {failed}")
    return validation


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Map Template v2: Building Variant Placement Report",
        "",
        "Places building graph variants onto the measured-asset-aware map and emits baked map-friendly summaries.",
        "",
        "## Summary",
        "",
        f"- map_plot_variant_placement_count: {validation['map_plot_variant_placement_count']}",
        f"- variant_classes_used: {validation['variant_classes_used']}",
        f"- foundation_seam_hiding_still_passes: {validation['foundation_seam_hiding_still_passes']}",
        f"- entrances_connect_to_roads: {validation['entrances_connect_to_roads']}",
        f"- max_entrance_road_distance_m: {validation['max_entrance_road_distance_m']}",
        f"- baked_summaries_remain_summary_only: {validation['baked_summaries_remain_summary_only']}",
        f"- terrain_cracks_remain_zero: {validation['terrain_cracks_remain_zero']}",
        f"- asset_scaling_applied_count: {validation['asset_scaling_applied_count']}",
        "",
        "## Placements",
        "",
    ]
    for placement in data["building_variant_placements"]:
        lines.extend(
            [
                f"### {placement['placement_id']}",
                "",
                f"- plot_id: {placement['plot_id']}",
                f"- building_graph_variant_id: {placement['building_graph_variant_id']}",
                f"- variant_class: {placement['variant_class']}",
                f"- variant_choice_reason: {placement['variant_choice_reason']}",
                f"- entrance_nearest_road_id: {placement['entrance']['nearest_road_id']}",
                f"- entrance_nearest_road_distance_m: {placement['entrance']['nearest_road_distance_m']}",
                f"- footprint: {placement['footprint']}",
                "",
            ]
        )
    lines.extend(["## Claim Limits", "", "- no production approval", "- no structural safety claim", "- no fabrication readiness claim", "- no historical accuracy claim", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "schema": "map_template_v2_building_variant_placement_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "placement_graph": str(PLACEMENT_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": {
            "three_map_plots_receive_building_variants": validation["three_map_plots_receive_building_variants"],
            "variant_choice_recorded_with_reason": validation["variant_choice_recorded_with_reason"],
            "foundation_seam_hiding_still_passes": validation["foundation_seam_hiding_still_passes"],
            "entrances_connect_to_roads": validation["entrances_connect_to_roads"],
            "baked_summaries_remain_summary_only": validation["baked_summaries_remain_summary_only"],
            "terrain_cracks_remain_zero": validation["terrain_cracks_remain_zero"],
            "render_has_visible_building_variation": validation["render_has_visible_building_variation"],
            "asset_scaling_applied_count": validation["asset_scaling_applied_count"],
        },
        "variant_classes_used": validation["variant_classes_used"],
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = compile_placements()
    PLACEMENT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {PLACEMENT_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "placements={map_plot_variant_placement_count} variants={variant_classes_used} cracks={semantic_cracked_seam_count}".format(
            **data["validation"]
        )
    )


if __name__ == "__main__":
    main()
