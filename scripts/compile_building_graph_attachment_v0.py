#!/usr/bin/env python3
"""Compile Building Graph Attachment v0.

Buildings are local subgraphs attached to measured-aware map sockets. The map
keeps only the baked footprint, entrance, and semantic summary; building-local
floor/wall/foundation/internal asset records remain discardable after bake.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILED_MAP_PATH = (
    ROOT
    / "goal"
    / "architecture"
    / "map_templates_v1"
    / "measured_asset_aware"
    / "compiled"
    / "measured_asset_aware_hex_map_template_v1_compiled.json"
)
SEMANTIC_GRAPH_PATH = (
    ROOT
    / "goal"
    / "architecture"
    / "map_templates_v1"
    / "measured_asset_aware"
    / "gameplay_surface_semantics"
    / "measured_asset_aware_hex_map_template_v1_gameplay_surface_semantics_graph.json"
)
REFINED_GRAPH_PATH = (
    ROOT
    / "goal"
    / "architecture"
    / "map_templates_v1"
    / "measured_asset_aware"
    / "road_plot_refined"
    / "measured_asset_aware_hex_map_template_v1_road_plot_refined_graph.json"
)
MEASURED_PLACEMENT_PATH = (
    ROOT
    / "goal"
    / "architecture"
    / "map_templates_v1"
    / "measured_asset_aware"
    / "measured_asset_placement"
    / "measured_asset_placement_v1.json"
)
MEASURED_INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v1" / "asset_mill_measured_index_v1.json"
OUT_DIR = ROOT / "goal" / "architecture" / "building_graph_attachment_v0"
ATTACHMENT_PATH = OUT_DIR / "building_graph_attachment_v0.json"
REPORT_PATH = OUT_DIR / "building_graph_attachment_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "building_graph_attachment_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}

BUILDING_CONFIGS: dict[str, dict[str, Any]] = {
    "measured_gatehouse_plot": {
        "building_graph_id": "gatehouse_graph_v0",
        "primary_socket_id": "gatehouse_measured_portal_socket",
        "graph_kind": "gatehouse",
        "wall_height_m": 2.7,
        "roof_kind": "upper_cap_placeholder",
        "semantic_tags": ["building_pad", "entrance", "cover_candidate", "line_of_sight_breaker"],
    },
    "measured_watch_plot": {
        "building_graph_id": "watch_graph_v0",
        "primary_socket_id": "watch_measured_arch_socket",
        "graph_kind": "watch",
        "wall_height_m": 2.45,
        "roof_kind": "lookout_cap_placeholder",
        "semantic_tags": ["building_pad", "vertical_transition", "cover_candidate", "line_of_sight_breaker"],
    },
    "measured_octagon_shrine_plot": {
        "building_graph_id": "shrine_graph_v0",
        "primary_socket_id": "shrine_measured_oculus_socket",
        "graph_kind": "shrine",
        "wall_height_m": 2.35,
        "roof_kind": "octagon_cap_placeholder",
        "semantic_tags": ["building_pad", "ornament_panel", "cover_candidate", "line_of_sight_breaker"],
    },
}

BASE_OFFSET_M = -0.15
FOUNDATION_OVERLAP_M = 0.25
FOUNDATION_TOP_ABOVE_CONTACT_M = 0.02
FOUNDATION_MARGIN_M = 0.34
FLOOR_SLAB_HEIGHT_M = 0.18
WALL_THICKNESS_M = 0.34
ROOF_CAP_HEIGHT_M = 0.22


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


def normalize3(values: list[float] | tuple[float, float, float]) -> list[float]:
    length = math.sqrt(sum(float(value) * float(value) for value in values))
    if length <= 1e-9:
        return [0.0, 0.0, 1.0]
    return [round6(float(value) / length) for value in values]


def dot2(a: list[float], b: list[float]) -> float:
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1])


def dot3(a: list[float], b: list[float]) -> float:
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])


def sub3(a: list[float], b: list[float]) -> list[float]:
    return [float(a[0]) - float(b[0]), float(a[1]) - float(b[1]), float(a[2]) - float(b[2])]


def horizontal_basis(frame: dict[str, Any]) -> dict[str, list[float]]:
    forward = [float(value) for value in frame.get("forward", [0.0, -1.0, 0.0])]
    right = [float(value) for value in frame.get("right", [-1.0, 0.0, 0.0])]
    forward_xy = normalize3([forward[0], forward[1], 0.0])
    if abs(forward_xy[0]) + abs(forward_xy[1]) <= 1e-6:
        forward_xy = [0.0, -1.0, 0.0]
    right_xy = normalize3([right[0], right[1], 0.0])
    if abs(dot3(forward_xy, right_xy)) > 0.08:
        right_xy = normalize3([forward_xy[1], -forward_xy[0], 0.0])
    return {"right": right_xy, "forward": forward_xy, "up": [0.0, 0.0, 1.0]}


def polygon_center(polygon: list[list[float]]) -> list[float]:
    return [
        round6(sum(float(point[0]) for point in polygon) / len(polygon)),
        round6(sum(float(point[1]) for point in polygon) / len(polygon)),
    ]


def projected_footprint(polygon: list[list[float]], center_xy: list[float], basis: dict[str, list[float]]) -> dict[str, Any]:
    right_values: list[float] = []
    forward_values: list[float] = []
    for x, y in polygon:
        rel = [float(x) - center_xy[0], float(y) - center_xy[1]]
        right_values.append(dot2(rel, basis["right"]))
        forward_values.append(dot2(rel, basis["forward"]))
    return {
        "width_m": round6(max(right_values) - min(right_values)),
        "depth_m": round6(max(forward_values) - min(forward_values)),
        "local_bounds": {
            "min_x": round6(min(right_values)),
            "max_x": round6(max(right_values)),
            "min_y": round6(min(forward_values)),
            "max_y": round6(max(forward_values)),
        },
    }


def cell_height_lookup(refined_graph: dict[str, Any]) -> dict[str, float]:
    return {
        plot["cell_id"]: float(plot.get("refined_center_height_m", plot.get("profiled_center_height_m", plot.get("height_m", 0.0))))
        for plot in refined_graph["hex_plots"]
    }


def terrain_contact_for_plot(plot: dict[str, Any], refined_graph: dict[str, Any]) -> dict[str, Any]:
    heights = cell_height_lookup(refined_graph)
    values = [heights[cell_id] for cell_id in plot.get("occupied_cells", []) if cell_id in heights]
    if not values:
        values = [float(point[2]) for point in (plot.get("anchor_frame", {}).get("position", [0.0, 0.0, 0.0]),)]
    return {
        "terrain_contact_z_m": round6(sum(values) / len(values)),
        "min_contact_z_m": round6(min(values)),
        "max_contact_z_m": round6(max(values)),
        "sample_count": len(values),
        "flat_pad_height_tolerance_m": round6(max(values) - min(values)),
    }


def cardinal_from_forward(forward: list[float]) -> str:
    x, y = float(forward[0]), float(forward[1])
    if abs(x) > abs(y):
        return "east" if x > 0.0 else "west"
    return "north" if y > 0.0 else "south"


def local_point(world_position: list[float], origin: list[float], basis: dict[str, list[float]]) -> list[float]:
    rel = sub3(world_position, origin)
    return [round6(dot3(rel, basis["right"])), round6(dot3(rel, basis["forward"])), round6(dot3(rel, basis["up"]))]


def socket_edge(local_pos: list[float], footprint: dict[str, Any]) -> str:
    bounds = footprint["local_bounds"]
    distances = {
        "east": abs(float(local_pos[0]) - float(bounds["max_x"])),
        "west": abs(float(local_pos[0]) - float(bounds["min_x"])),
        "north": abs(float(local_pos[1]) - float(bounds["max_y"])),
        "south": abs(float(local_pos[1]) - float(bounds["min_y"])),
    }
    return min(distances, key=distances.get)


def component_box(
    component_id: str,
    component_type: str,
    center: list[float],
    dimensions: list[float],
    semantic_tags: list[str],
    material_role: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "component_type": component_type,
        "primitive": "box",
        "local_center_m": [round6(value) for value in center],
        "dimensions_m": [round6(value) for value in dimensions],
        "semantic_tags": semantic_tags,
        "material_role": material_role,
        **extra,
    }


def wall_segments(footprint: dict[str, Any], wall_height: float, entrance_edge: str, entrance_width: float, base_z: float) -> list[dict[str, Any]]:
    bounds = footprint["local_bounds"]
    min_x = float(bounds["min_x"])
    max_x = float(bounds["max_x"])
    min_y = float(bounds["min_y"])
    max_y = float(bounds["max_y"])
    width = max_x - min_x
    depth = max_y - min_y
    wall_center_z = base_z + wall_height * 0.5
    parts: list[dict[str, Any]] = []

    def add_long(edge: str, y: float) -> None:
        if edge == entrance_edge:
            gap = min(entrance_width, width * 0.62)
            side_w = max(0.18, (width - gap) * 0.5)
            parts.append(
                component_box(
                    f"outer_wall_{edge}_left_of_entrance",
                    "outer_wall",
                    [min_x + side_w * 0.5, y, wall_center_z],
                    [side_w, WALL_THICKNESS_M, wall_height],
                    ["wall", "blocked", "line_of_sight_breaker"],
                    "wall",
                )
            )
            parts.append(
                component_box(
                    f"outer_wall_{edge}_right_of_entrance",
                    "outer_wall",
                    [max_x - side_w * 0.5, y, wall_center_z],
                    [side_w, WALL_THICKNESS_M, wall_height],
                    ["wall", "blocked", "line_of_sight_breaker"],
                    "wall",
                )
            )
            return
        parts.append(
            component_box(
                f"outer_wall_{edge}",
                "outer_wall",
                [(min_x + max_x) * 0.5, y, wall_center_z],
                [width + WALL_THICKNESS_M, WALL_THICKNESS_M, wall_height],
                ["wall", "blocked", "line_of_sight_breaker"],
                "wall",
            )
        )

    def add_short(edge: str, x: float) -> None:
        if edge == entrance_edge:
            gap = min(entrance_width, depth * 0.62)
            side_d = max(0.18, (depth - gap) * 0.5)
            parts.append(
                component_box(
                    f"outer_wall_{edge}_left_of_entrance",
                    "outer_wall",
                    [x, min_y + side_d * 0.5, wall_center_z],
                    [WALL_THICKNESS_M, side_d, wall_height],
                    ["wall", "blocked", "line_of_sight_breaker"],
                    "wall",
                )
            )
            parts.append(
                component_box(
                    f"outer_wall_{edge}_right_of_entrance",
                    "outer_wall",
                    [x, max_y - side_d * 0.5, wall_center_z],
                    [WALL_THICKNESS_M, side_d, wall_height],
                    ["wall", "blocked", "line_of_sight_breaker"],
                    "wall",
                )
            )
            return
        parts.append(
            component_box(
                f"outer_wall_{edge}",
                "outer_wall",
                [x, (min_y + max_y) * 0.5, wall_center_z],
                [WALL_THICKNESS_M, depth + WALL_THICKNESS_M, wall_height],
                ["wall", "blocked", "line_of_sight_breaker"],
                "wall",
            )
        )

    add_long("north", max_y)
    add_long("south", min_y)
    add_short("east", max_x)
    add_short("west", min_x)
    return parts


def local_asset_socket(placement: dict[str, Any], origin: list[float], basis: dict[str, list[float]], footprint: dict[str, Any]) -> dict[str, Any]:
    frame = placement["anchor_frame"]
    local_pos = local_point([float(value) for value in frame["position"]], origin, basis)
    local_forward = [
        round6(dot3([float(value) for value in frame["forward"]], basis["right"])),
        round6(dot3([float(value) for value in frame["forward"]], basis["forward"])),
        round6(dot3([float(value) for value in frame["forward"]], basis["up"])),
    ]
    local_right = [
        round6(dot3([float(value) for value in frame["right"]], basis["right"])),
        round6(dot3([float(value) for value in frame["right"]], basis["forward"])),
        round6(dot3([float(value) for value in frame["right"]], basis["up"])),
    ]
    local_up = [
        round6(dot3([float(value) for value in frame["up"]], basis["right"])),
        round6(dot3([float(value) for value in frame["up"]], basis["forward"])),
        round6(dot3([float(value) for value in frame["up"]], basis["up"])),
    ]
    return {
        "socket_id": f"building_local_{placement['socket_id']}",
        "source_map_socket_id": placement["socket_id"],
        "source_asset_ref": placement["source_asset_ref"],
        "measured_asset_id": placement["measured_asset_id"],
        "socket_type": placement["source_socket_type"],
        "local_position_m": local_pos,
        "local_frame": {"forward": local_forward, "right": local_right, "up": local_up},
        "edge": socket_edge(local_pos, footprint),
        "asset_placement_status": placement["status"],
        "asset_placement_reasons": placement["reasons"],
        "placement_space": "building_graph_local",
    }


def compile_building_graphs() -> dict[str, Any]:
    compiled = load_json(COMPILED_MAP_PATH)
    semantic_graph = load_json(SEMANTIC_GRAPH_PATH)
    refined_graph = load_json(REFINED_GRAPH_PATH)
    placements_data = load_json(MEASURED_PLACEMENT_PATH)
    measured_index = load_json(MEASURED_INDEX_PATH)
    measured_dims = {asset["asset_id"]: asset["dimensions_m"] for asset in measured_index["assets"]}
    plots_by_id = {plot["plot_id"]: plot for plot in compiled["building_plots"]}
    placements_by_socket = {placement["socket_id"]: placement for placement in placements_data["placements"]}
    placements_by_anchor: dict[str, list[dict[str, Any]]] = {}
    for placement in placements_data["placements"]:
        placements_by_anchor.setdefault(str(placement.get("anchor_ref")), []).append(placement)

    building_graphs: list[dict[str, Any]] = []
    baked_buildings: list[dict[str, Any]] = []
    for plot_id, config in BUILDING_CONFIGS.items():
        plot = plots_by_id[plot_id]
        primary = placements_by_socket[config["primary_socket_id"]]
        basis = horizontal_basis(primary["anchor_frame"])
        center_xy = polygon_center(plot["polygon"])
        contact = terrain_contact_for_plot(plot, refined_graph)
        terrain_contact_z = float(contact["terrain_contact_z_m"])
        origin = [center_xy[0], center_xy[1], round6(terrain_contact_z + BASE_OFFSET_M)]
        footprint = projected_footprint(plot["polygon"], center_xy, basis)
        entrance_edge = socket_edge(local_point(primary["world_position"], origin, basis), footprint)
        entrance_world_cardinal = cardinal_from_forward(basis["forward"])
        floor_bottom_local_z = terrain_contact_z - origin[2]
        floor_center_z = floor_bottom_local_z + FLOOR_SLAB_HEIGHT_M * 0.5
        foundation_bottom_z = terrain_contact_z - FOUNDATION_OVERLAP_M
        foundation_top_z = terrain_contact_z + FOUNDATION_TOP_ABOVE_CONTACT_M
        foundation_center_local_z = ((foundation_bottom_z + foundation_top_z) * 0.5) - origin[2]
        foundation_height = foundation_top_z - foundation_bottom_z
        wall_base_z = floor_bottom_local_z + FLOOR_SLAB_HEIGHT_M
        wall_height = float(config["wall_height_m"])
        roof_center_z = wall_base_z + wall_height + ROOF_CAP_HEIGHT_M * 0.5
        local_sockets = [
            local_asset_socket(placement, origin, basis, footprint)
            for placement in placements_by_anchor.get(plot_id, [])
            if placement.get("measured_asset_id")
        ]
        child_assets = [
            {
                "child_asset_instance_id": f"{config['building_graph_id']}_{socket['source_map_socket_id']}_asset",
                "measured_asset_id": socket["measured_asset_id"],
                "local_socket_id": socket["socket_id"],
                "source_map_socket_id": socket["source_map_socket_id"],
                "placement_space": "building_graph_local",
                "freeze_with_building_bake": True,
            }
            for socket in local_sockets
        ]
        components = [
            component_box(
                "foundation_skirt",
                "foundation",
                [0.0, 0.0, foundation_center_local_z],
                [
                    float(footprint["width_m"]) + FOUNDATION_MARGIN_M * 2.0,
                    float(footprint["depth_m"]) + FOUNDATION_MARGIN_M * 2.0,
                    foundation_height,
                ],
                ["foundation", "foundation_edge", "hidden_terrain_building_seam"],
                "foundation",
                bottom_world_z_m=round6(foundation_bottom_z),
                terrain_contact_z_m=round6(terrain_contact_z),
                skirt_sinks_below_terrain=True,
            ),
            component_box(
                "floor_slab",
                "floor",
                [0.0, 0.0, floor_center_z],
                [float(footprint["width_m"]), float(footprint["depth_m"]), FLOOR_SLAB_HEIGHT_M],
                ["floor", "walkable", "building_pad"],
                "floor",
            ),
            *wall_segments(footprint, wall_height, entrance_edge, float(primary["chosen_fit"]["asset_width_m"]), wall_base_z),
            component_box(
                "roof_upper_cap_placeholder",
                "roof_placeholder",
                [0.0, 0.0, roof_center_z],
                [float(footprint["width_m"]) + 0.22, float(footprint["depth_m"]) + 0.22, ROOF_CAP_HEIGHT_M],
                ["roof_placeholder", "blocked", "line_of_sight_breaker"],
                "roof",
                roof_kind=config["roof_kind"],
            ),
        ]
        graph = {
            "building_graph_id": config["building_graph_id"],
            "graph_kind": config["graph_kind"],
            "attach_socket_id": primary["socket_id"],
            "attach_plot_id": plot_id,
            "origin": origin,
            "orientation": "from_map_anchor",
            "orientation_basis": basis,
            "footprint": {
                "width": footprint["width_m"],
                "depth": footprint["depth_m"],
                "source": "compiled_building_plot_projected_into_map_anchor_frame",
            },
            "base_offset_m": BASE_OFFSET_M,
            "foundation_overlap_m": FOUNDATION_OVERLAP_M,
            "terrain_contact": contact,
            "building_base_z_m": origin[2],
            "foundation_skirt_bottom_z_m": round6(foundation_bottom_z),
            "entrance_edge": entrance_world_cardinal,
            "local_entrance_edge": entrance_edge,
            "seam_hide_strategy": "foundation_skirt_extends_below_terrain_contact_surface",
            "freeze_after_bake": True,
            "live_graph_discardable_after_bake": True,
            "components": components,
            "internal_asset_sockets": local_sockets,
            "child_asset_instances": child_assets,
            "semantic_tags": config["semantic_tags"],
            "no_claims": NO_CLAIMS,
        }
        building_graphs.append(graph)
        baked_buildings.append(
            {
                "baked_building_id": f"baked_{config['building_graph_id']}",
                "building_graph_id": config["building_graph_id"],
                "source_live_graph_retained_for_debug": True,
                "map_visible_contract_only": True,
                "attach_socket_id": primary["socket_id"],
                "attach_plot_id": plot_id,
                "origin": origin,
                "orientation_basis": basis,
                "footprint": graph["footprint"],
                "entrance_edge": entrance_world_cardinal,
                "local_entrance_edge": entrance_edge,
                "terrain_contact_z_m": round6(terrain_contact_z),
                "foundation_overlap_m": FOUNDATION_OVERLAP_M,
                "foundation_skirt_bottom_z_m": round6(foundation_bottom_z),
                "semantic_tags": sorted(set(config["semantic_tags"] + ["asset_socket"])),
                "asset_socket_count": len(local_sockets),
                "freeze_after_bake": True,
                "live_graph_discardable_after_bake": True,
            }
        )

    validation = validate(building_graphs, baked_buildings, semantic_graph, placements_data)
    return {
        "schema": "building_graph_attachment_v0",
        "created_at_utc": now_iso(),
        "source_files": {
            "compiled_map": str(COMPILED_MAP_PATH.relative_to(ROOT)),
            "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
            "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
            "measured_asset_placement": str(MEASURED_PLACEMENT_PATH.relative_to(ROOT)),
            "measured_asset_index": str(MEASURED_INDEX_PATH.relative_to(ROOT)),
        },
        "attachment_rules": {
            "buildings_are_local_subgraphs": True,
            "map_contract_fields": ["origin", "orientation", "footprint", "entrance_edge", "ground_contact_band", "allowed_height_range"],
            "base_offset_m": BASE_OFFSET_M,
            "foundation_overlap_m": FOUNDATION_OVERLAP_M,
            "terrain_building_mesh_welding_required": False,
            "seam_hidden_by": ["foundation_skirt", "plinth", "retaining_edge", "curb", "stair", "trim", "buried_wall"],
            "child_assets_place_relative_to_building_graph": True,
            "freeze_after_bake": True,
        },
        "building_graphs": building_graphs,
        "baked_map_buildings": baked_buildings,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def validate(
    building_graphs: list[dict[str, Any]],
    baked_buildings: list[dict[str, Any]],
    semantic_graph: dict[str, Any],
    placements_data: dict[str, Any],
) -> dict[str, Any]:
    semantic_sockets = {socket["socket_id"] for socket in semantic_graph["map_template_overlays"]["asset_sockets"]}
    plot_bound_placements = [
        placement
        for placement in placements_data["placements"]
        if str(placement.get("anchor_ref")) in BUILDING_CONFIGS and placement.get("measured_asset_id")
    ]
    graph_socket_sources = {
        socket["source_map_socket_id"]
        for graph in building_graphs
        for socket in graph["internal_asset_sockets"]
    }
    foundation_checks = [
        float(graph["foundation_skirt_bottom_z_m"]) < float(graph["terrain_contact"]["terrain_contact_z_m"])
        and float(graph["foundation_overlap_m"]) > 0.0
        for graph in building_graphs
    ]
    component_bounds_nonzero = [
        all(float(value) > 0.0 for value in component["dimensions_m"])
        for graph in building_graphs
        for component in graph["components"]
        if component.get("primitive") == "box"
    ]
    validation = {
        "building_graph_count": len(building_graphs),
        "baked_building_count": len(baked_buildings),
        "building_graph_attaches_to_map_socket": all(graph["attach_socket_id"] in semantic_sockets for graph in building_graphs),
        "foundation_skirt_sinks_below_terrain": all(foundation_checks),
        "no_visible_dead_space_at_terrain_building_contact": all(
            graph["seam_hide_strategy"] == "foundation_skirt_extends_below_terrain_contact_surface"
            and float(graph["foundation_overlap_m"]) >= 0.1
            for graph in building_graphs
        ),
        "building_assets_place_relative_to_building_graph": all(
            socket["placement_space"] == "building_graph_local"
            for graph in building_graphs
            for socket in graph["internal_asset_sockets"]
        ),
        "all_plot_bound_assets_absorbed_into_building_graphs": graph_socket_sources
        == {placement["socket_id"] for placement in plot_bound_placements},
        "map_graph_sees_final_building_contract_only": all(item["map_visible_contract_only"] for item in baked_buildings),
        "baked_output_can_discard_live_building_graph": all(
            item["freeze_after_bake"] and item["live_graph_discardable_after_bake"] for item in baked_buildings
        ),
        "component_bounds_nonzero": all(component_bounds_nonzero),
        "plot_bound_asset_count": len(plot_bound_placements),
        "building_local_asset_socket_count": len(graph_socket_sources),
        "map_level_asset_socket_count_retained": len(placements_data["placements"]) - len(plot_bound_placements),
        "map_level_asset_examples": [
            placement["socket_id"]
            for placement in placements_data["placements"]
            if str(placement.get("anchor_ref")) not in BUILDING_CONFIGS
        ],
        "no_claims": NO_CLAIMS,
    }
    required = [
        "building_graph_attaches_to_map_socket",
        "foundation_skirt_sinks_below_terrain",
        "no_visible_dead_space_at_terrain_building_contact",
        "building_assets_place_relative_to_building_graph",
        "all_plot_bound_assets_absorbed_into_building_graphs",
        "map_graph_sees_final_building_contract_only",
        "baked_output_can_discard_live_building_graph",
        "component_bounds_nonzero",
    ]
    failed = [key for key in required if not validation[key]]
    if failed:
        fail(f"building graph attachment validation failed: {failed}")
    return validation


def write_report(data: dict[str, Any]) -> None:
    lines = [
        "# Building Graph Attachment v0 Report",
        "",
        "Buildings are compiled as local subgraphs attached to measured-aware map sockets, then summarized as baked map-facing contracts.",
        "",
        "## Summary",
        "",
        f"- building_graph_count: {data['validation']['building_graph_count']}",
        f"- baked_building_count: {data['validation']['baked_building_count']}",
        f"- plot_bound_asset_count: {data['validation']['plot_bound_asset_count']}",
        f"- building_local_asset_socket_count: {data['validation']['building_local_asset_socket_count']}",
        f"- map_level_asset_socket_count_retained: {data['validation']['map_level_asset_socket_count_retained']}",
        "",
        "## Building Graphs",
        "",
    ]
    for graph in data["building_graphs"]:
        lines.extend(
            [
                f"### {graph['building_graph_id']}",
                "",
                f"- attach_socket_id: {graph['attach_socket_id']}",
                f"- attach_plot_id: {graph['attach_plot_id']}",
                f"- origin: {graph['origin']}",
                f"- footprint: {graph['footprint']['width']}m x {graph['footprint']['depth']}m",
                f"- terrain_contact_z_m: {graph['terrain_contact']['terrain_contact_z_m']}",
                f"- base_offset_m: {graph['base_offset_m']}",
                f"- foundation_overlap_m: {graph['foundation_overlap_m']}",
                f"- foundation_skirt_bottom_z_m: {graph['foundation_skirt_bottom_z_m']}",
                f"- entrance_edge: {graph['entrance_edge']} ({graph['local_entrance_edge']} in building-local frame)",
                f"- child_asset_instances: {len(graph['child_asset_instances'])}",
                f"- freeze_after_bake: {graph['freeze_after_bake']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Validation",
            "",
        ]
    )
    for key, value in data["validation"].items():
        if key == "no_claims":
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Claim Limits",
            "",
            "- no production approval",
            "- no structural safety claim",
            "- no fabrication readiness claim",
            "- no historical accuracy claim",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "schema": "building_graph_attachment_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "attachment_graph": str(ATTACHMENT_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": {
            "building_graph_attaches_to_map_socket": validation["building_graph_attaches_to_map_socket"],
            "foundation_skirt_sinks_below_terrain": validation["foundation_skirt_sinks_below_terrain"],
            "no_visible_dead_space_at_terrain_building_contact": validation["no_visible_dead_space_at_terrain_building_contact"],
            "building_assets_place_relative_to_building_graph": validation["building_assets_place_relative_to_building_graph"],
            "map_graph_only_sees_final_building_contract": validation["map_graph_sees_final_building_contract_only"],
            "baked_output_can_discard_live_building_graph": validation["baked_output_can_discard_live_building_graph"],
        },
        "counts": {
            "building_graph_count": validation["building_graph_count"],
            "plot_bound_asset_count": validation["plot_bound_asset_count"],
            "building_local_asset_socket_count": validation["building_local_asset_socket_count"],
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = compile_building_graphs()
    ATTACHMENT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {ATTACHMENT_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "building_graphs={building_graph_count} local_asset_sockets={building_local_asset_socket_count} "
        "foundation_overlap_ok={foundation_skirt_sinks_below_terrain}".format(**data["validation"])
    )


if __name__ == "__main__":
    main()
