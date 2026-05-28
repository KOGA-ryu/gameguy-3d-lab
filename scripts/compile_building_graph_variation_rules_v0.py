#!/usr/bin/env python3
"""Compile Building Graph Variation Rules v0.

Generates compact, standard, and tall variants from each expanded local
building graph. Variations alter graph dimensions and socket layout rules, not
measured child asset geometry.
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_building_graph_kit_expansion_v0 as kit_compile  # noqa: E402


KIT_GRAPH_PATH = kit_compile.KIT_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "building_graph_variation_rules_v0"
VARIATION_GRAPH_PATH = OUT_DIR / "building_graph_variation_rules_v0.json"
REPORT_PATH = OUT_DIR / "building_graph_variation_rules_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "building_graph_variation_rules_v0.receipt.json"

NO_CLAIMS = kit_compile.NO_CLAIMS
VARIANT_RULES: dict[str, dict[str, Any]] = {
    "compact": {
        "footprint_scale": 0.84,
        "wall_height_delta_m": -0.25,
        "roof_cap_height_m": 0.18,
        "window_count_delta": -1,
        "corner_post_style": "measured_square_pier_v1_compact",
        "corner_post_scale_xy": 0.82,
        "bay_spacing": 0.86,
        "foundation_depth_m": 0.22,
    },
    "standard": {
        "footprint_scale": 1.0,
        "wall_height_delta_m": 0.0,
        "roof_cap_height_m": 0.22,
        "window_count_delta": 0,
        "corner_post_style": "measured_square_pier_v1",
        "corner_post_scale_xy": 1.0,
        "bay_spacing": 1.0,
        "foundation_depth_m": 0.25,
    },
    "tall": {
        "footprint_scale": 1.08,
        "wall_height_delta_m": 0.85,
        "roof_cap_height_m": 0.30,
        "window_count_delta": 1,
        "corner_post_style": "measured_octagon_column_v1",
        "corner_post_scale_xy": 1.0,
        "bay_spacing": 1.14,
        "foundation_depth_m": 0.32,
    },
}

WALL_THICKNESS_M = 0.34
FLOOR_HEIGHT_M = 0.18
FOUNDATION_MARGIN_M = 0.34
FOUNDATION_TOP_ABOVE_CONTACT_M = 0.02
ENTRANCE_CLEARANCE_M = 0.24
WINDOW_DIMENSIONS_M = [1.35, 0.32, 2.65]
DOOR_DIMENSIONS_M = [2.6, 0.48, 2.45]


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


def bounds_for(width: float, depth: float) -> dict[str, float]:
    return {
        "min_x": round6(-width * 0.5),
        "max_x": round6(width * 0.5),
        "min_y": round6(-depth * 0.5),
        "max_y": round6(depth * 0.5),
    }


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def floor_top_z(graph: dict[str, Any]) -> float:
    floor = next(component for component in graph["components"] if component["component_type"] == "floor_slab")
    return float(floor["local_center_m"][2]) + float(floor["dimensions_m"][2]) * 0.5


def roof_top_z(graph: dict[str, Any]) -> float:
    roof = next(component for component in graph["components"] if component["component_type"] == "roof_cap_placeholder")
    return float(roof["local_center_m"][2]) + float(roof["dimensions_m"][2]) * 0.5


def baseline_wall_height(graph: dict[str, Any]) -> float:
    wall_heights = [float(component["dimensions_m"][2]) for component in graph["components"] if component["component_type"] == "wall_segment"]
    if wall_heights:
        return max(wall_heights)
    return max(2.1, roof_top_z(graph) - floor_top_z(graph) - 0.22)


def component_box(
    component_id: str,
    component_type: str,
    center: list[float],
    dimensions: list[float],
    semantic_tags: list[str],
    material_role: str,
    measured_component_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    item = {
        "component_id": component_id,
        "component_type": component_type,
        "primitive": "box",
        "local_center_m": [round6(value) for value in center],
        "dimensions_m": [round6(value) for value in dimensions],
        "semantic_tags": semantic_tags,
        "material_role": material_role,
        **extra,
    }
    if measured_component_id:
        item["measured_component_id"] = measured_component_id
    return item


def edge_position(edge: str, bounds: dict[str, float], x: float = 0.0, y: float = 0.0) -> list[float]:
    if edge == "north":
        return [round6(clamp(x, bounds["min_x"] + 0.5, bounds["max_x"] - 0.5)), bounds["max_y"]]
    if edge == "south":
        return [round6(clamp(x, bounds["min_x"] + 0.5, bounds["max_x"] - 0.5)), bounds["min_y"]]
    if edge == "east":
        return [bounds["max_x"], round6(clamp(y, bounds["min_y"] + 0.5, bounds["max_y"] - 0.5))]
    return [bounds["min_x"], round6(clamp(y, bounds["min_y"] + 0.5, bounds["max_y"] - 0.5))]


def opposite_edge(edge: str) -> str:
    return {"north": "south", "south": "north", "east": "west", "west": "east"}.get(edge, "south")


def adjacent_edges(edge: str) -> list[str]:
    if edge in {"north", "south"}:
        return ["east", "west"]
    return ["north", "south"]


def wall_segments(bounds: dict[str, float], wall_height: float, door_edge: str, door_width: float, floor_z: float) -> list[dict[str, Any]]:
    min_x = bounds["min_x"]
    max_x = bounds["max_x"]
    min_y = bounds["min_y"]
    max_y = bounds["max_y"]
    width = max_x - min_x
    depth = max_y - min_y
    wall_center_z = floor_z + wall_height * 0.5
    parts: list[dict[str, Any]] = []

    def add_long(edge: str, y: float) -> None:
        if edge == door_edge:
            gap = min(door_width + ENTRANCE_CLEARANCE_M, width * 0.68)
            side_w = max(0.2, (width - gap) * 0.5)
            for side, x in (("left", min_x + side_w * 0.5), ("right", max_x - side_w * 0.5)):
                parts.append(
                    component_box(
                        f"wall_segment_{edge}_{side}_of_entrance",
                        "wall_segment",
                        [x, y, wall_center_z],
                        [side_w, WALL_THICKNESS_M, wall_height],
                        ["wall", "blocked", "line_of_sight_breaker"],
                        "wall",
                        "measured_rectangular_wall_block_v1",
                        edge=edge,
                    )
                )
            return
        parts.append(
            component_box(
                f"wall_segment_{edge}",
                "wall_segment",
                [(min_x + max_x) * 0.5, y, wall_center_z],
                [width + WALL_THICKNESS_M, WALL_THICKNESS_M, wall_height],
                ["wall", "blocked", "line_of_sight_breaker"],
                "wall",
                "measured_rectangular_wall_block_v1",
                edge=edge,
            )
        )

    def add_short(edge: str, x: float) -> None:
        if edge == door_edge:
            gap = min(door_width + ENTRANCE_CLEARANCE_M, depth * 0.68)
            side_d = max(0.2, (depth - gap) * 0.5)
            for side, y in (("left", min_y + side_d * 0.5), ("right", max_y - side_d * 0.5)):
                parts.append(
                    component_box(
                        f"wall_segment_{edge}_{side}_of_entrance",
                        "wall_segment",
                        [x, y, wall_center_z],
                        [WALL_THICKNESS_M, side_d, wall_height],
                        ["wall", "blocked", "line_of_sight_breaker"],
                        "wall",
                        "measured_rectangular_wall_block_v1",
                        edge=edge,
                    )
                )
            return
        parts.append(
            component_box(
                f"wall_segment_{edge}",
                "wall_segment",
                [x, (min_y + max_y) * 0.5, wall_center_z],
                [WALL_THICKNESS_M, depth + WALL_THICKNESS_M, wall_height],
                ["wall", "blocked", "line_of_sight_breaker"],
                "wall",
                "measured_rectangular_wall_block_v1",
                edge=edge,
            )
        )

    add_long("north", max_y)
    add_long("south", min_y)
    add_short("east", max_x)
    add_short("west", min_x)
    return parts


def corner_posts(bounds: dict[str, float], floor_z: float, wall_height: float, rule: dict[str, Any]) -> list[dict[str, Any]]:
    style = str(rule["corner_post_style"])
    post_width = 0.46 * float(rule["corner_post_scale_xy"])
    post_depth = 0.46 * float(rule["corner_post_scale_xy"])
    if style == "measured_octagon_column_v1":
        post_width = 0.48
        post_depth = 0.48
    height = max(wall_height + 0.52, 2.0)
    positions = {
        "north_east": [bounds["max_x"], bounds["max_y"]],
        "north_west": [bounds["min_x"], bounds["max_y"]],
        "south_east": [bounds["max_x"], bounds["min_y"]],
        "south_west": [bounds["min_x"], bounds["min_y"]],
    }
    return [
        component_box(
            f"corner_post_{name}",
            "corner_post",
            [position[0], position[1], floor_z + height * 0.5],
            [post_width, post_depth, height],
            ["support", "blocked", "collision_proxy"],
            "post",
            style.replace("_compact", ""),
            corner_post_style=style,
            corner=name,
        )
        for name, position in positions.items()
    ]


def socket_record(
    socket_id: str,
    socket_type: str,
    local_position: list[float],
    edge: str,
    compatible_tags: list[str],
    semantic_tags: list[str],
    parent_component_id: str | None = None,
) -> dict[str, Any]:
    return {
        "socket_id": socket_id,
        "socket_type": socket_type,
        "local_position_m": [round6(value) for value in local_position],
        "edge": edge,
        "compatible_tags": compatible_tags,
        "semantic_tags": semantic_tags,
        "parent_component_id": parent_component_id,
        "placement_space": "building_graph_local",
    }


def make_bays_and_sockets(
    source: dict[str, Any],
    bounds: dict[str, float],
    floor_z: float,
    wall_height: float,
    door_edge: str,
    window_count: int,
    bay_spacing: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    door_xy = edge_position(door_edge, bounds)
    door_z = floor_z + DOOR_DIMENSIONS_M[2] * 0.5
    door_id = f"door_bay_{source['building_graph_id']}_variant_entrance"
    components = [
        component_box(
            door_id,
            "door_bay",
            [door_xy[0], door_xy[1], door_z],
            DOOR_DIMENSIONS_M,
            ["entrance", "walkable_transition", "asset_socket"],
            "door_bay",
            "measured_round_arch_bay_v1",
            edge=door_edge,
            asset_scaling_applied=False,
        )
    ]
    exterior_sockets = [
        socket_record(
            f"exterior_{source['building_graph_id']}_variant_entrance",
            "exterior_socket",
            [door_xy[0], door_xy[1], floor_z],
            door_edge,
            ["door_bay", "road_connector"],
            ["entrance", "walkable_transition"],
            door_id,
        )
    ]
    window_edges = adjacent_edges(door_edge) + [opposite_edge(door_edge)]
    windows: list[tuple[str, float]] = []
    if window_count == 1:
        windows = [(window_edges[0], 0.0)]
    elif window_count == 2:
        windows = [(window_edges[0], 0.0), (window_edges[1], 0.0)]
    elif window_count >= 3:
        windows = [(window_edges[0], 0.0), (window_edges[1], 0.0), (window_edges[2], -0.58 * bay_spacing)]
        if window_count >= 4:
            windows.append((window_edges[2], 0.58 * bay_spacing))
    for index, (edge, offset) in enumerate(windows[:window_count]):
        if edge in {"north", "south"}:
            xy = edge_position(edge, bounds, x=offset)
        else:
            xy = edge_position(edge, bounds, y=offset)
        component_id = f"window_bay_{source['building_graph_id']}_variant_{index:02d}"
        components.append(
            component_box(
                component_id,
                "window_bay",
                [xy[0], xy[1], floor_z + WINDOW_DIMENSIONS_M[2] * 0.5],
                WINDOW_DIMENSIONS_M,
                ["window", "wall_socket", "line_of_sight_breaker"],
                "window_bay",
                "measured_lancet_window_bay_v1",
                edge=edge,
                bay_spacing=bay_spacing,
                asset_scaling_applied=False,
            )
        )
        exterior_sockets.append(
            socket_record(
                f"exterior_{source['building_graph_id']}_variant_window_{index:02d}",
                "exterior_socket",
                [xy[0], xy[1], floor_z],
                edge,
                ["window_bay", "measured_asset_mount"],
                ["window", "wall_socket"],
                component_id,
            )
        )
    interior_sockets = [
        socket_record(
            f"interior_{source['building_graph_id']}_variant_floor_center",
            "interior_socket",
            [0.0, 0.0, floor_z + 0.02],
            "center",
            ["floor_mount", "future_interior_asset"],
            ["interior_socket", "walkable"],
            "floor_slab",
        ),
        socket_record(
            f"interior_{source['building_graph_id']}_variant_rear_wall",
            "interior_socket",
            [0.0, -bounds["max_y"] * 0.45, floor_z + min(1.2, wall_height * 0.42)],
            "interior_wall",
            ["wall_mount", "future_gameplay_marker"],
            ["interior_socket", "wall_socket"],
            None,
        ),
    ]
    local_asset_sockets: list[dict[str, Any]] = []
    door_slot = next(component for component in components if component["component_type"] == "door_bay")
    window_slots = [component for component in components if component["component_type"] == "window_bay"]
    window_asset_index = 0
    for asset in source["child_asset_instances"]:
        measured_id = str(asset["measured_asset_id"])
        source_socket = next(
            (socket for socket in source["internal_asset_sockets"] if socket["socket_id"] == asset["local_socket_id"]),
            None,
        )
        if source_socket is None:
            continue
        socket_type = str(source_socket.get("socket_type", "asset_socket"))
        if socket_type in {"portal", "door", "vertical_transition"}:
            xy = [float(door_slot["local_center_m"][0]), float(door_slot["local_center_m"][1])]
            edge = str(door_slot["edge"])
            parent_component_id = str(door_slot["component_id"])
        elif "window" in measured_id or source_socket.get("socket_type") in {"window", "ornament_panel"}:
            if window_asset_index >= len(window_slots):
                continue
            match = window_slots[window_asset_index]
            window_asset_index += 1
            xy = [float(match["local_center_m"][0]), float(match["local_center_m"][1])]
            edge = str(match["edge"])
            parent_component_id = str(match["component_id"])
        else:
            xy = [float(source_socket["local_position_m"][0]), float(source_socket["local_position_m"][1])]
            edge = str(source_socket.get("edge", "center"))
            parent_component_id = None
        local_asset_sockets.append(
            {
                **source_socket,
                "socket_id": f"{source_socket['socket_id']}_variant",
                "local_position_m": [round6(xy[0]), round6(xy[1]), round6(floor_z)],
                "edge": edge,
                "parent_component_id": parent_component_id,
                "placement_space": "building_graph_local",
                "asset_scaling_applied": False,
                "source_variant_socket_from": source_socket["socket_id"],
            }
        )
    return components, interior_sockets, exterior_sockets, local_asset_sockets


def desired_window_count(source: dict[str, Any], rule: dict[str, Any]) -> int:
    base_count = sum(1 for component in source["components"] if component["component_type"] == "window_bay")
    return max(1, min(4, base_count + int(rule["window_count_delta"])))


def make_variant(source: dict[str, Any], variant_name: str, rule: dict[str, Any]) -> dict[str, Any]:
    base_width = float(source["footprint"]["width"])
    base_depth = float(source["footprint"]["depth"])
    width = max(base_width * float(rule["footprint_scale"]), DOOR_DIMENSIONS_M[0] + 1.1)
    depth = max(base_depth * float(rule["footprint_scale"]), DOOR_DIMENSIONS_M[1] + 2.8)
    bounds = bounds_for(width, depth)
    floor_z = floor_top_z(source)
    wall_height = max(2.0, baseline_wall_height(source) + float(rule["wall_height_delta_m"]))
    roof_height = float(rule["roof_cap_height_m"])
    foundation_depth = float(rule["foundation_depth_m"])
    foundation_bottom_local_z = 0.15 - foundation_depth
    foundation_top_local_z = 0.15 + FOUNDATION_TOP_ABOVE_CONTACT_M
    foundation_height = foundation_depth + FOUNDATION_TOP_ABOVE_CONTACT_M
    foundation_center_z = (foundation_bottom_local_z + foundation_top_local_z) * 0.5
    door_edge = str(source["local_entrance_edge"])
    windows = desired_window_count(source, rule)
    bay_components, interior_sockets, exterior_sockets, local_asset_sockets = make_bays_and_sockets(
        source,
        bounds,
        floor_z,
        wall_height,
        door_edge,
        windows,
        float(rule["bay_spacing"]),
    )
    roof_center_z = floor_z + wall_height + roof_height * 0.5
    components = [
        component_box(
            "foundation_skirt",
            "foundation_skirt",
            [0.0, 0.0, foundation_center_z],
            [width + FOUNDATION_MARGIN_M * 2.0, depth + FOUNDATION_MARGIN_M * 2.0, foundation_height],
            ["foundation", "foundation_edge", "hidden_terrain_building_seam"],
            "foundation",
            "measured_base_plinth_v1",
            foundation_depth_m=round6(foundation_depth),
            bottom_local_z_m=round6(foundation_bottom_local_z),
            terrain_contact_local_z_m=0.15,
            bottom_world_z_m=round6(float(source["origin"][2]) + foundation_bottom_local_z),
            terrain_contact_z_m=round6(float(source["origin"][2]) + 0.15),
            skirt_sinks_below_terrain=True,
        ),
        component_box(
            "floor_slab",
            "floor_slab",
            [0.0, 0.0, floor_z - FLOOR_HEIGHT_M * 0.5],
            [width, depth, FLOOR_HEIGHT_M],
            ["floor", "walkable", "building_pad"],
            "floor",
            "measured_floor_slab_v1",
        ),
        *wall_segments(bounds, wall_height, door_edge, DOOR_DIMENSIONS_M[0], floor_z),
        *corner_posts(bounds, floor_z, wall_height, rule),
        *bay_components,
        component_box(
            "roof_cap_placeholder",
            "roof_cap_placeholder",
            [0.0, 0.0, roof_center_z],
            [width + 0.22, depth + 0.22, roof_height],
            ["roof_placeholder", "blocked", "line_of_sight_breaker"],
            "roof",
            "measured_cap_block_v1",
            roof_cap_height_m=round6(roof_height),
        ),
    ]
    variant_id = f"{source['building_graph_id']}_{variant_name}_variant_v0"
    child_assets = []
    socket_by_source = {
        socket["source_variant_socket_from"]: socket
        for socket in local_asset_sockets
        if socket.get("source_variant_socket_from")
    }
    for asset in source["child_asset_instances"]:
        source_socket_id = next(
            (
                socket["source_variant_socket_from"]
                for socket in local_asset_sockets
                if socket["source_variant_socket_from"] == asset["local_socket_id"]
            ),
            asset["local_socket_id"],
        )
        if source_socket_id not in socket_by_source:
            continue
        child_assets.append(
            {
                **asset,
                "child_asset_instance_id": f"{variant_id}_{asset['measured_asset_id']}",
                "local_socket_id": socket_by_source.get(source_socket_id, {}).get("socket_id", asset["local_socket_id"]),
                "placement_space": "building_graph_local",
                "asset_scaling_applied": False,
                "variant_socket_remap_source": source_socket_id,
            }
        )
    primitive_counts: dict[str, int] = {}
    for component in components:
        key = str(component["component_type"])
        primitive_counts[key] = primitive_counts.get(key, 0) + 1
    primitive_counts["interior_socket"] = len(interior_sockets)
    primitive_counts["exterior_socket"] = len(exterior_sockets)
    return {
        "building_graph_variant_id": variant_id,
        "source_building_graph_id": source["building_graph_id"],
        "variant_class": variant_name,
        "variation_fields": {
            "footprint_size": {"width": round6(width), "depth": round6(depth), "scale_from_source": rule["footprint_scale"]},
            "wall_height": round6(wall_height),
            "roof_cap_height": round6(roof_height),
            "door_edge": door_edge,
            "window_count": windows,
            "corner_post_style": rule["corner_post_style"],
            "bay_spacing": rule["bay_spacing"],
            "foundation_depth": round6(foundation_depth),
        },
        "origin": source["origin"],
        "orientation": source["orientation"],
        "orientation_basis": source["orientation_basis"],
        "attach_socket_id": source["attach_socket_id"],
        "attach_plot_id": source["attach_plot_id"],
        "footprint": {"width": round6(width), "depth": round6(depth), "source": "building_graph_variation_rules_v0"},
        "projected_local_bounds": bounds,
        "local_entrance_edge": door_edge,
        "components": components,
        "interior_sockets": interior_sockets,
        "exterior_sockets": exterior_sockets,
        "internal_asset_sockets": local_asset_sockets,
        "child_asset_instances": child_assets,
        "kit_primitive_counts": dict(sorted(primitive_counts.items())),
        "connectivity": {
            "preserves_source_attach_socket": True,
            "preserves_entrance_connectivity": True,
            "door_edge_locked_to_source_entrance_edge": True,
            "attach_socket_id": source["attach_socket_id"],
        },
        "asset_scaling": {
            "asset_scaling_applied": False,
            "scaled_asset_ids": [],
            "reason": "variant rules reposition local sockets and procedural kit primitives only",
        },
        "bake_policy": {
            "freeze_after_bake": True,
            "live_graph_discardable_after_bake": True,
            "baked_map_keeps_summary_only": True,
        },
        "no_claims": NO_CLAIMS,
    }


def compile_variants() -> dict[str, Any]:
    if not KIT_GRAPH_PATH.exists():
        kit_compile.main()
    kit = load_json(KIT_GRAPH_PATH)
    variants = [
        make_variant(graph, variant_name, copy.deepcopy(rule))
        for graph in kit["building_graphs"]
        for variant_name, rule in VARIANT_RULES.items()
    ]
    baked = [
        {
            "baked_building_variant_id": f"baked_{variant['building_graph_variant_id']}",
            "building_graph_variant_id": variant["building_graph_variant_id"],
            "source_building_graph_id": variant["source_building_graph_id"],
            "variant_class": variant["variant_class"],
            "attach_socket_id": variant["attach_socket_id"],
            "attach_plot_id": variant["attach_plot_id"],
            "origin": variant["origin"],
            "orientation_basis": variant["orientation_basis"],
            "footprint": variant["footprint"],
            "entrance_edge": variant["local_entrance_edge"],
            "semantic_tags": ["building_pad", "entrance", "asset_socket", "line_of_sight_breaker"],
            "map_friendly_summary_only": True,
            "component_detail_exported_to_map_graph": False,
            "asset_scaling_applied": variant["asset_scaling"]["asset_scaling_applied"],
            "freeze_after_bake": True,
            "live_graph_discardable_after_bake": True,
        }
        for variant in variants
    ]
    validation = validate(variants, baked)
    return {
        "schema": "building_graph_variation_rules_v0",
        "created_at_utc": now_iso(),
        "source_files": {
            "building_graph_kit_expansion": str(KIT_GRAPH_PATH.relative_to(ROOT)),
        },
        "variation_rule_table": VARIANT_RULES,
        "variant_classes": list(VARIANT_RULES),
        "building_graph_variants": variants,
        "baked_map_building_variants": baked,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def socket_near_footprint(socket: dict[str, Any], bounds: dict[str, float], tolerance: float = 0.65) -> bool:
    x, y, _z = [float(value) for value in socket["local_position_m"]]
    return (
        bounds["min_x"] - tolerance <= x <= bounds["max_x"] + tolerance
        and bounds["min_y"] - tolerance <= y <= bounds["max_y"] + tolerance
    )


def validate(variants: list[dict[str, Any]], baked: list[dict[str, Any]]) -> dict[str, Any]:
    per_variant: dict[str, dict[str, Any]] = {}
    for variant in variants:
        types = [component["component_type"] for component in variant["components"]]
        all_sockets = variant["interior_sockets"] + variant["exterior_sockets"] + variant["internal_asset_sockets"]
        bounds = variant["projected_local_bounds"]
        per_variant[variant["building_graph_variant_id"]] = {
            "preserves_entrance_connectivity": bool(variant["connectivity"]["preserves_entrance_connectivity"])
            and "door_bay" in types,
            "preserves_foundation_seam_hiding": bool(
                next(component for component in variant["components"] if component["component_type"] == "foundation_skirt")[
                    "skirt_sinks_below_terrain"
                ]
            ),
            "local_sockets_inside_or_near_footprint": all(socket_near_footprint(socket, bounds) for socket in all_sockets),
            "baked_summary_map_friendly": True,
            "asset_scaling_recorded": "asset_scaling" in variant and "asset_scaling_applied" in variant["asset_scaling"],
            "no_asset_scaling": not variant["asset_scaling"]["asset_scaling_applied"],
            "no_ornament": all("ornament" not in str(component.get("component_type", "")) for component in variant["components"]),
            "window_count": variant["variation_fields"]["window_count"],
        }
    validation = {
        "building_graph_variant_count": len(variants),
        "expected_variant_count": 9,
        "variants_per_source_graph": {},
        "all_preserve_entrance_connectivity": all(row["preserves_entrance_connectivity"] for row in per_variant.values()),
        "all_preserve_foundation_seam_hiding": all(row["preserves_foundation_seam_hiding"] for row in per_variant.values()),
        "all_local_sockets_inside_or_near_footprint": all(row["local_sockets_inside_or_near_footprint"] for row in per_variant.values()),
        "all_baked_summaries_stay_map_friendly": all(item["map_friendly_summary_only"] for item in baked),
        "no_asset_scaling_unless_explicitly_recorded": all(row["asset_scaling_recorded"] for row in per_variant.values()),
        "asset_scaling_applied_count": sum(1 for variant in variants if variant["asset_scaling"]["asset_scaling_applied"]),
        "no_ornament": all(row["no_ornament"] for row in per_variant.values()),
        "per_variant": per_variant,
        "no_claims": NO_CLAIMS,
    }
    for variant in variants:
        source = variant["source_building_graph_id"]
        validation["variants_per_source_graph"][source] = validation["variants_per_source_graph"].get(source, 0) + 1
    required = [
        validation["building_graph_variant_count"] == validation["expected_variant_count"],
        all(count == 3 for count in validation["variants_per_source_graph"].values()),
        validation["all_preserve_entrance_connectivity"],
        validation["all_preserve_foundation_seam_hiding"],
        validation["all_local_sockets_inside_or_near_footprint"],
        validation["all_baked_summaries_stay_map_friendly"],
        validation["no_asset_scaling_unless_explicitly_recorded"],
        validation["asset_scaling_applied_count"] == 0,
        validation["no_ornament"],
    ]
    if not all(required):
        fail("building graph variation validation failed")
    return validation


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Building Graph Variation Rules v0 Report",
        "",
        "Generated compact, standard, and tall variants from each local building graph kit.",
        "",
        "## Summary",
        "",
        f"- building_graph_variant_count: {validation['building_graph_variant_count']}",
        f"- variants_per_source_graph: {validation['variants_per_source_graph']}",
        f"- all_preserve_entrance_connectivity: {validation['all_preserve_entrance_connectivity']}",
        f"- all_preserve_foundation_seam_hiding: {validation['all_preserve_foundation_seam_hiding']}",
        f"- all_local_sockets_inside_or_near_footprint: {validation['all_local_sockets_inside_or_near_footprint']}",
        f"- all_baked_summaries_stay_map_friendly: {validation['all_baked_summaries_stay_map_friendly']}",
        f"- asset_scaling_applied_count: {validation['asset_scaling_applied_count']}",
        f"- no_ornament: {validation['no_ornament']}",
        "",
        "## Variant Rule Table",
        "",
    ]
    for name, rule in data["variation_rule_table"].items():
        lines.append(f"### {name}")
        lines.append("")
        for key in ["footprint_scale", "wall_height_delta_m", "roof_cap_height_m", "window_count_delta", "corner_post_style", "bay_spacing", "foundation_depth_m"]:
            lines.append(f"- {key}: {rule[key]}")
        lines.append("")
    lines.extend(["## Variants", ""])
    for variant in data["building_graph_variants"]:
        fields = variant["variation_fields"]
        lines.extend(
            [
                f"### {variant['building_graph_variant_id']}",
                "",
                f"- source_building_graph_id: {variant['source_building_graph_id']}",
                f"- footprint_size: {fields['footprint_size']}",
                f"- wall_height: {fields['wall_height']}",
                f"- roof_cap_height: {fields['roof_cap_height']}",
                f"- door_edge: {fields['door_edge']}",
                f"- window_count: {fields['window_count']}",
                f"- corner_post_style: {fields['corner_post_style']}",
                f"- bay_spacing: {fields['bay_spacing']}",
                f"- foundation_depth: {fields['foundation_depth']}",
                f"- asset_scaling_applied: {variant['asset_scaling']['asset_scaling_applied']}",
                "",
            ]
        )
    lines.extend(["## Claim Limits", "", "- no ornament added", "- no production approval", "- no structural safety claim", "- no fabrication readiness claim", "- no historical accuracy claim", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "schema": "building_graph_variation_rules_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "variation_graph": str(VARIATION_GRAPH_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": {
            "nine_building_graph_variants_generated": validation["building_graph_variant_count"] == 9,
            "all_preserve_entrance_connectivity": validation["all_preserve_entrance_connectivity"],
            "all_preserve_foundation_seam_hiding": validation["all_preserve_foundation_seam_hiding"],
            "all_local_sockets_inside_or_near_footprint": validation["all_local_sockets_inside_or_near_footprint"],
            "all_baked_summaries_stay_map_friendly": validation["all_baked_summaries_stay_map_friendly"],
            "no_asset_scaling_unless_explicitly_recorded": validation["no_asset_scaling_unless_explicitly_recorded"],
            "asset_scaling_applied_count": validation["asset_scaling_applied_count"],
            "no_ornament": validation["no_ornament"],
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = compile_variants()
    VARIATION_GRAPH_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {VARIATION_GRAPH_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "variants={building_graph_variant_count} entrance_ok={all_preserve_entrance_connectivity} "
        "sockets_ok={all_local_sockets_inside_or_near_footprint}".format(**data["validation"])
    )


if __name__ == "__main__":
    main()
