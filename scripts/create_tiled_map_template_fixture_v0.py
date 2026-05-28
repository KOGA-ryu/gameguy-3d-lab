#!/usr/bin/env python3
"""Create a deterministic Tiled-style map template fixture.

This is an authoring fixture, not a production map. It gives the map compiler a
single source that contains terrain heights, surfaces, roads, plots, hazards,
and asset sockets in a Tiled-like JSON shape.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "architecture" / "map_templates"
OUT_PATH = OUT_DIR / "tiled_hex_map_template_v0.json"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "tiled_hex_map_template_fixture_v0.receipt.json"


WIDTH = 32
HEIGHT = 32


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    length_sq = abx * abx + aby * aby
    if length_sq == 0.0:
        return math.hypot(px - ax, py - ay)
    t = clamp((apx * abx + apy * aby) / length_sq, 0.0, 1.0)
    cx = ax + abx * t
    cy = ay + aby * t
    return math.hypot(px - cx, py - cy)


def point_to_polyline_distance(px: float, py: float, points: list[tuple[float, float]]) -> float:
    return min(
        distance_to_segment(px, py, ax, ay, bx, by)
        for (ax, ay), (bx, by) in zip(points, points[1:], strict=False)
    )


def inside_rect(cx: float, cy: float, rect: tuple[float, float, float, float]) -> bool:
    x, y, w, h = rect
    return x <= cx <= x + w and y <= cy <= y + h


def make_height_data() -> list[int]:
    data: list[int] = []
    hill_center = (22.0, 9.5)
    ravine_line = [(3.0, 25.5), (11.0, 22.0), (18.0, 22.5), (29.0, 27.0)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cx = x + 0.5
            cy = y + 0.5
            dist = math.hypot(cx - hill_center[0], cy - hill_center[1])
            hill = max(0.0, 1.0 - dist / 9.0)
            ravine = max(0.0, 1.0 - point_to_polyline_distance(cx, cy, ravine_line) / 2.8)
            level = 2 + round(hill * 5.0) - round(ravine * 2.0)

            if inside_rect(cx, cy, (5.0, 15.0, 6.0, 6.0)):
                level = 2
            if inside_rect(cx, cy, (19.0, 4.0, 6.0, 5.0)):
                level = 5
            if inside_rect(cx, cy, (20.0, 17.0, 7.0, 6.0)):
                level = 3

            data.append(int(clamp(level, 0, 7)))
    return data


def make_surface_data(height_data: list[int]) -> list[int]:
    roads = [
        [(2.0, 18.5), (11.0, 18.5), (16.0, 14.5), (30.0, 14.0)],
        [(16.0, 14.5), (20.0, 10.5), (23.0, 6.5)],
    ]
    hazard = [(3.0, 25.5), (11.0, 22.0), (18.0, 22.5), (29.0, 27.0)]
    data: list[int] = []
    for index, level in enumerate(height_data):
        x = index % WIDTH
        y = index // WIDTH
        cx = x + 0.5
        cy = y + 0.5
        surface = 1 if level <= 2 else 3
        if any(point_to_polyline_distance(cx, cy, road) <= 1.2 for road in roads):
            surface = 2
        if point_to_polyline_distance(cx, cy, hazard) <= 1.1:
            surface = 4
        if inside_rect(cx, cy, (5.0, 15.0, 6.0, 6.0)) or inside_rect(cx, cy, (19.0, 4.0, 6.0, 5.0)) or inside_rect(cx, cy, (20.0, 17.0, 7.0, 6.0)):
            surface = 5
        data.append(surface)
    return data


def prop(name: str, value: Any, kind: str | None = None) -> dict[str, Any]:
    if kind is None:
        if isinstance(value, bool):
            kind = "bool"
        elif isinstance(value, int):
            kind = "int"
        elif isinstance(value, float):
            kind = "float"
        else:
            kind = "string"
    return {"name": name, "type": kind, "value": value}


def make_object(
    *,
    object_id: int,
    name: str,
    x: float,
    y: float,
    width: float = 0.0,
    height: float = 0.0,
    obj_type: str = "",
    polyline: list[dict[str, float]] | None = None,
    polygon: list[dict[str, float]] | None = None,
    properties: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": object_id,
        "name": name,
        "type": obj_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "rotation": 0,
        "visible": True,
        "properties": properties or [],
    }
    if polyline is not None:
        data["polyline"] = polyline
    if polygon is not None:
        data["polygon"] = polygon
    return data


def build_template() -> dict[str, Any]:
    height_data = make_height_data()
    surface_data = make_surface_data(height_data)
    return {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.10.2",
        "orientation": "hexagonal",
        "renderorder": "right-down",
        "width": WIDTH,
        "height": HEIGHT,
        "tilewidth": 1,
        "tileheight": 1,
        "hexsidelength": 1,
        "staggeraxis": "y",
        "staggerindex": "odd",
        "infinite": False,
        "nextlayerid": 7,
        "nextobjectid": 18,
        "properties": [
            prop("template_id", "tiled_hex_map_template_v0"),
            prop("map_cube_id", "standard_32m_cube_v0"),
            prop("cell_size_m", 1.0),
            prop("hex_radius_m", 0.55),
            prop("vertical_step_m", 0.5),
            prop("z_levels", 8),
            prop("source_family", "tiled_style_json"),
            prop("proof_only", True),
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "name": "map_template_debug_tiles_v0",
                "tilewidth": 1,
                "tileheight": 1,
                "tilecount": 5,
                "columns": 5,
                "tiles": [
                    {"id": 0, "type": "grass", "properties": [prop("surface_type", "grass")]},
                    {"id": 1, "type": "road", "properties": [prop("surface_type", "road")]},
                    {"id": 2, "type": "stone", "properties": [prop("surface_type", "stone")]},
                    {"id": 3, "type": "hazard", "properties": [prop("surface_type", "ravine_edge")]},
                    {"id": 4, "type": "plot", "properties": [prop("surface_type", "building_plot")]},
                ],
            }
        ],
        "layers": [
            {
                "id": 1,
                "name": "terrain_height",
                "type": "tilelayer",
                "width": WIDTH,
                "height": HEIGHT,
                "x": 0,
                "y": 0,
                "data": height_data,
                "properties": [prop("value_meaning", "height_level"), prop("vertical_step_m", 0.5)],
            },
            {
                "id": 2,
                "name": "terrain_surface",
                "type": "tilelayer",
                "width": WIDTH,
                "height": HEIGHT,
                "x": 0,
                "y": 0,
                "data": surface_data,
                "properties": [prop("value_meaning", "surface_tile_gid")],
            },
            {
                "id": 3,
                "name": "roads_paths",
                "type": "objectgroup",
                "objects": [
                    make_object(
                        object_id=1,
                        name="main_ridge_road",
                        x=2.0,
                        y=18.5,
                        obj_type="road_path",
                        polyline=[{"x": 0.0, "y": 0.0}, {"x": 9.0, "y": 0.0}, {"x": 14.0, "y": -4.0}, {"x": 28.0, "y": -4.5}],
                        properties=[prop("width_m", 2.2), prop("movement_tag", "route"), prop("surface_type", "stone_road")],
                    ),
                    make_object(
                        object_id=2,
                        name="switchback_to_watch_post",
                        x=16.0,
                        y=14.5,
                        obj_type="road_path",
                        polyline=[{"x": 0.0, "y": 0.0}, {"x": 4.0, "y": -4.0}, {"x": 7.0, "y": -8.0}],
                        properties=[prop("width_m", 1.4), prop("movement_tag", "narrow_route"), prop("surface_type", "switchback")],
                    ),
                ],
            },
            {
                "id": 4,
                "name": "building_plots",
                "type": "objectgroup",
                "objects": [
                    make_object(
                        object_id=3,
                        name="gatehouse_plot",
                        x=5.0,
                        y=15.0,
                        width=6.0,
                        height=6.0,
                        obj_type="building_plot",
                        properties=[prop("floor_plan_ref", "simple_entry_room_v0"), prop("plot_role", "threshold_building"), prop("recommended_asset_kit", "arch_bay_kit_v1")],
                    ),
                    make_object(
                        object_id=4,
                        name="cliff_watch_plot",
                        x=19.0,
                        y=4.0,
                        width=6.0,
                        height=5.0,
                        obj_type="building_plot",
                        properties=[prop("floor_plan_ref", "raised_platform_stair_v0"), prop("plot_role", "high_ground_watch"), prop("recommended_asset_kit", "architectural_asset_batch_v0")],
                    ),
                    make_object(
                        object_id=5,
                        name="octagon_shrine_plot",
                        x=23.5,
                        y=20.0,
                        obj_type="building_plot",
                        polygon=[
                            {"x": 0.0, "y": -3.0},
                            {"x": 2.2, "y": -2.2},
                            {"x": 3.0, "y": 0.0},
                            {"x": 2.2, "y": 2.2},
                            {"x": 0.0, "y": 3.0},
                            {"x": -2.2, "y": 2.2},
                            {"x": -3.0, "y": 0.0},
                            {"x": -2.2, "y": -2.2},
                        ],
                        properties=[prop("floor_plan_ref", "courtyard_ring_v0"), prop("plot_role", "octagonal_shrine"), prop("recommended_asset_kit", "arch_bay_kit_v1")],
                    ),
                ],
            },
            {
                "id": 5,
                "name": "hazard_edges",
                "type": "objectgroup",
                "objects": [
                    make_object(
                        object_id=6,
                        name="ravine_drop_edge",
                        x=3.0,
                        y=25.5,
                        obj_type="hazard_edge",
                        polyline=[{"x": 0.0, "y": 0.0}, {"x": 8.0, "y": -3.5}, {"x": 15.0, "y": -3.0}, {"x": 26.0, "y": 1.5}],
                        properties=[prop("hazard_type", "fall_edge"), prop("severity", "high"), prop("movement_tag", "avoid")],
                    )
                ],
            },
            {
                "id": 6,
                "name": "asset_sockets",
                "type": "objectgroup",
                "objects": [
                    make_object(
                        object_id=7,
                        name="gatehouse_portal_socket",
                        x=8.0,
                        y=14.85,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "pointed_arch_doorway_v1"),
                            prop("socket_type", "portal"),
                            prop("anchor_kind", "plot_edge"),
                            prop("anchor_ref", "gatehouse_plot"),
                            prop("orientation_degrees", 0.0),
                            prop("footprint_width_m", 1.4),
                            prop("footprint_depth_m", 0.7),
                            prop("footprint_height_m", 2.6),
                        ],
                    ),
                    make_object(
                        object_id=8,
                        name="gatehouse_window_socket_a",
                        x=6.0,
                        y=18.2,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "narrow_lancet_window_v1"),
                            prop("socket_type", "window"),
                            prop("anchor_kind", "plot_edge"),
                            prop("anchor_ref", "gatehouse_plot"),
                            prop("orientation_degrees", 180.0),
                            prop("footprint_width_m", 0.9),
                            prop("footprint_depth_m", 0.45),
                            prop("footprint_height_m", 2.1),
                        ],
                    ),
                    make_object(
                        object_id=9,
                        name="gatehouse_window_socket_b",
                        x=10.0,
                        y=18.2,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "narrow_lancet_window_v1"),
                            prop("socket_type", "window"),
                            prop("anchor_kind", "plot_edge"),
                            prop("anchor_ref", "gatehouse_plot"),
                            prop("orientation_degrees", 180.0),
                            prop("footprint_width_m", 0.9),
                            prop("footprint_depth_m", 0.45),
                            prop("footprint_height_m", 2.1),
                        ],
                    ),
                    make_object(
                        object_id=10,
                        name="watch_stair_socket",
                        x=21.5,
                        y=8.7,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "stair_landing_asset_v0"),
                            prop("socket_type", "vertical_transition"),
                            prop("anchor_kind", "height_seam"),
                            prop("anchor_ref", "cliff_watch_plot"),
                            prop("orientation_degrees", 45.0),
                            prop("footprint_width_m", 1.7),
                            prop("footprint_depth_m", 1.2),
                            prop("footprint_height_m", 0.8),
                        ],
                    ),
                    make_object(
                        object_id=11,
                        name="watch_arch_socket",
                        x=22.0,
                        y=4.2,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "columned_arch_portal_v1"),
                            prop("socket_type", "portal"),
                            prop("anchor_kind", "plot_edge"),
                            prop("anchor_ref", "cliff_watch_plot"),
                            prop("orientation_degrees", 180.0),
                            prop("footprint_width_m", 2.1),
                            prop("footprint_depth_m", 0.9),
                            prop("footprint_height_m", 2.7),
                        ],
                    ),
                    make_object(
                        object_id=12,
                        name="shrine_oculus_socket",
                        x=23.5,
                        y=17.2,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "oculus_arch_bay_v1"),
                            prop("socket_type", "ornament_panel"),
                            prop("anchor_kind", "plot_edge"),
                            prop("anchor_ref", "octagon_shrine_plot"),
                            prop("orientation_degrees", 180.0),
                            prop("footprint_width_m", 1.3),
                            prop("footprint_depth_m", 0.55),
                            prop("footprint_height_m", 2.2),
                        ],
                    ),
                    make_object(
                        object_id=13,
                        name="bridge_segment_socket",
                        x=17.0,
                        y=22.3,
                        obj_type="asset_socket",
                        properties=[
                            prop("asset_ref", "bridge_segment_asset_v0"),
                            prop("socket_type", "route_bridge"),
                            prop("anchor_kind", "bridge_span"),
                            prop("anchor_ref", "ravine_drop_edge"),
                            prop("orientation_degrees", 12.0),
                            prop("footprint_width_m", 2.4),
                            prop("footprint_depth_m", 0.9),
                            prop("footprint_height_m", 0.8),
                        ],
                    ),
                ],
            },
        ],
        "no_claims": {
            "production_approval": False,
            "structural_safety": False,
            "fabrication_ready": False,
            "gym_museum_approval": False,
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    template = build_template()
    OUT_PATH.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "receipt_type": "tiled_hex_map_template_fixture_v0",
        "created_at_utc": now_iso(),
        "files_created": [str(OUT_PATH.relative_to(ROOT))],
        "source_model": "tiled_style_json",
        "template_id": "tiled_hex_map_template_v0",
        "no_images": True,
        "no_meshes": True,
        "no_production_approval": True,
        "no_gym_museum_approval": True,
        "summary": "Created one deterministic Tiled-style map template fixture with height, surface, road, plot, hazard, and asset socket layers.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
