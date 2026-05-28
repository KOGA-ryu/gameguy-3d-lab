#!/usr/bin/env python3
"""Create the fresh Hillwatch Ravine integrated map scene v0."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from create_tiled_map_template_fixture_v0 import clamp, distance_to_segment, make_object, prop


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 32
HEIGHT = 32
TEMPLATE_ID = "hillwatch_ravine_integrated_map_scene_v0"
TEMPLATE_PATH = ROOT / "data" / "architecture" / "map_templates" / "integrated_map_scene_v0.json"
MEASURED_INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v1" / "asset_mill_measured_index_v1.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}

ASSET_TO_MEASURED = {
    "pointed_arch_doorway_v1": "measured_pointed_arch_doorway_v1",
    "narrow_lancet_window_v1": "measured_lancet_window_bay_v1",
    "columned_arch_portal_v1": "measured_round_arch_bay_v1",
    "oculus_arch_bay_v1": "measured_round_arch_bay_v1",
    "stair_landing_asset_v0": "measured_stair_block_run_v1",
    "bridge_segment_asset_v0": "measured_floor_slab_v1",
}

# Tiled authoring coordinates. This is a fresh layout, not derived from the
# measured-asset-aware v1 template.
GATEHOUSE_RECT = (3.0, 10.0, 7.0, 6.0)
WATCH_RECT = (21.0, 5.0, 8.0, 6.0)
SHRINE_POLY = [(19.0, 20.0), (21.4, 18.9), (24.2, 20.1), (25.1, 22.7), (23.2, 25.0), (20.1, 24.6), (18.6, 22.4)]
MAIN_ROAD = [(1.0, 9.6), (6.6, 9.3), (12.8, 8.5), (18.8, 6.5), (25.0, 4.6), (31.0, 5.0)]
SHRINE_SPUR_ROAD = [(12.8, 8.5), (15.8, 13.2), (18.6, 17.2), (21.7, 22.0), (24.0, 24.2)]
RAVINE = [(2.0, 25.0), (8.0, 23.0), (14.0, 22.2), (20.0, 25.0), (30.0, 27.8)]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def point_to_polyline_distance(px: float, py: float, points: list[tuple[float, float]]) -> float:
    return min(distance_to_segment(px, py, ax, ay, bx, by) for (ax, ay), (bx, by) in zip(points, points[1:], strict=False))


def inside_rect(cx: float, cy: float, rect: tuple[float, float, float, float]) -> bool:
    x, y, width, height = rect
    return x <= cx <= x + width and y <= cy <= y + height


def inside_poly(cx: float, cy: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if ((yi > cy) != (yj > cy)) and (cx < (xj - xi) * (cy - yi) / ((yj - yi) or 1e-6) + xi):
            inside = not inside
        j = i
    return inside


def measured_dims() -> dict[str, dict[str, float]]:
    index = load_json(MEASURED_INDEX_PATH)
    return {row["asset_id"]: {key: float(value) for key, value in row["dimensions_m"].items()} for row in index["assets"]}


def footprint_props(asset_ref: str, dims: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    measured_id = ASSET_TO_MEASURED[asset_ref]
    dim = dims[measured_id]
    margin_w, margin_d, margin_h = (0.15, 0.15, 0.2) if asset_ref == "bridge_segment_asset_v0" else (0.2, 0.16, 0.25)
    return [
        prop("measured_asset_ref", measured_id),
        prop("footprint_source", "measured_asset_bounds_plus_clearance_v1"),
        prop("footprint_width_m", round(dim["width"] + margin_w, 6)),
        prop("footprint_depth_m", round(dim["depth"] + margin_d, 6)),
        prop("footprint_height_m", round(dim["height"] + margin_h, 6)),
        prop("footprint_clearance_margin_width_m", margin_w),
        prop("footprint_clearance_margin_depth_m", margin_d),
        prop("footprint_clearance_margin_height_m", margin_h),
    ]


def make_height_data() -> list[int]:
    data: list[int] = []
    hilltop = (25.0, 8.0)
    ridge_a = (21.0, 3.5)
    ridge_b = (31.0, 8.0)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cx = x + 0.5
            cy = y + 0.5
            ravine_distance = point_to_polyline_distance(cx, cy, RAVINE)
            road_distance = point_to_polyline_distance(cx, cy, MAIN_ROAD)
            spur_distance = point_to_polyline_distance(cx, cy, SHRINE_SPUR_ROAD)
            hill = max(0.0, 1.0 - math.hypot(cx - hilltop[0], cy - hilltop[1]) / 12.0)
            ridge = max(0.0, 1.0 - distance_to_segment(cx, cy, ridge_a[0], ridge_a[1], ridge_b[0], ridge_b[1]) / 4.0)

            level = 2 + round(hill * 4.0) + round(ridge * 2.0)
            if road_distance < 1.8:
                t = max(0.0, min(1.0, (cx - 4.0) / 22.0))
                level = round(2.0 + t * 4.0)
            if spur_distance < 1.6:
                level = max(level, 3)
            if 13.0 <= cx <= 20.5 and 14.0 <= cy <= 20.5:
                level = max(level, 4 + int((cy - 14.0) // 2.2))
            if ravine_distance < 0.9:
                level = 0
            elif ravine_distance < 1.8:
                level = min(level, 1)
            elif ravine_distance < 2.6:
                level = min(level, 2)

            if 28.0 <= cx <= 31.5 and 3.5 <= cy <= 9.5:
                level = max(level, 7)
            if 29.0 <= cx <= 31.5 and 1.0 <= cy <= 3.5:
                level = 8
            if inside_rect(cx, cy, GATEHOUSE_RECT):
                level = 2
            # The compiled hex footprint samples one column beyond the authored
            # rectangle, so flatten the full projected plateau footprint.
            if 20.0 <= cx <= 29.0 and 5.0 <= cy <= 11.0:
                level = 6
            if inside_poly(cx, cy, SHRINE_POLY):
                level = 3
            data.append(int(clamp(level, 0, 8)))
    return data


def make_surface_data(height_data: list[int]) -> list[int]:
    data: list[int] = []
    for index, level in enumerate(height_data):
        x = index % WIDTH
        y = index // WIDTH
        cx = x + 0.5
        cy = y + 0.5
        surface = 3 if level >= 5 else 1
        if any(point_to_polyline_distance(cx, cy, road) <= 1.35 for road in (MAIN_ROAD, SHRINE_SPUR_ROAD)):
            surface = 2
        if point_to_polyline_distance(cx, cy, RAVINE) <= 1.15:
            surface = 4
        if inside_rect(cx, cy, GATEHOUSE_RECT) or inside_rect(cx, cy, WATCH_RECT) or inside_poly(cx, cy, SHRINE_POLY):
            surface = 5
        data.append(surface)
    return data


def socket_object(object_id: int, name: str, x: float, y: float, asset_ref: str, socket_type: str, anchor_kind: str, anchor_ref: str, orientation: float, dims: dict[str, dict[str, float]]) -> dict[str, Any]:
    return make_object(
        object_id=object_id,
        name=name,
        x=x,
        y=y,
        obj_type="asset_socket",
        properties=[
            prop("asset_ref", asset_ref),
            prop("socket_type", socket_type),
            prop("anchor_kind", anchor_kind),
            prop("anchor_ref", anchor_ref),
            prop("orientation_degrees", orientation),
            *footprint_props(asset_ref, dims),
        ],
    )


def build_template() -> dict[str, Any]:
    dims = measured_dims()
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
            prop("template_id", TEMPLATE_ID),
            prop("map_cube_id", "standard_32m_cube_v0"),
            prop("cell_size_m", 1.0),
            prop("hex_radius_m", 0.55),
            prop("vertical_step_m", 1.0),
            prop("z_levels", 9),
            prop("source_family", "fresh_hillwatch_ravine_hex_node_map_v0"),
            prop("proof_only", True),
            prop("not_derived_from_measured_asset_aware_template_v1", True),
            prop("socket_footprints_from_measured_bounds", True),
            prop("movement_simulation_included", False),
            prop("asset_geometry_changed", False),
            prop("silent_asset_scaling", False),
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "name": "hillwatch_ravine_debug_tiles_v0",
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
            {"id": 1, "name": "terrain_height", "type": "tilelayer", "width": WIDTH, "height": HEIGHT, "x": 0, "y": 0, "data": height_data, "properties": [prop("value_meaning", "height_level_m"), prop("vertical_step_m", 1.0)]},
            {"id": 2, "name": "terrain_surface", "type": "tilelayer", "width": WIDTH, "height": HEIGHT, "x": 0, "y": 0, "data": surface_data, "properties": [prop("value_meaning", "surface_tile_gid")]},
            {
                "id": 3,
                "name": "roads_paths",
                "type": "objectgroup",
                "objects": [
                    make_object(object_id=1, name="main_measured_road", x=MAIN_ROAD[0][0], y=MAIN_ROAD[0][1], obj_type="road_path", polyline=[{"x": x - MAIN_ROAD[0][0], "y": y - MAIN_ROAD[0][1]} for x, y in MAIN_ROAD], properties=[prop("width_m", 2.5), prop("movement_tag", "route"), prop("surface_type", "stone_road")]),
                    make_object(object_id=2, name="shrine_spur_road", x=SHRINE_SPUR_ROAD[0][0], y=SHRINE_SPUR_ROAD[0][1], obj_type="road_path", polyline=[{"x": x - SHRINE_SPUR_ROAD[0][0], "y": y - SHRINE_SPUR_ROAD[0][1]} for x, y in SHRINE_SPUR_ROAD], properties=[prop("width_m", 1.8), prop("movement_tag", "route"), prop("surface_type", "stone_road")]),
                ],
            },
            {
                "id": 4,
                "name": "building_plots",
                "type": "objectgroup",
                "objects": [
                    make_object(object_id=3, name="measured_gatehouse_plot", x=GATEHOUSE_RECT[0], y=GATEHOUSE_RECT[1], width=GATEHOUSE_RECT[2], height=GATEHOUSE_RECT[3], obj_type="building_plot", properties=[prop("floor_plan_ref", "hillwatch_gatehouse_plot_v0"), prop("plot_role", "threshold_building"), prop("recommended_asset_kit", "asset_mill_measured_v1")]),
                    make_object(object_id=4, name="measured_watch_plot", x=WATCH_RECT[0], y=WATCH_RECT[1], width=WATCH_RECT[2], height=WATCH_RECT[3], obj_type="building_plot", properties=[prop("floor_plan_ref", "hillwatch_plateau_watch_plot_v0"), prop("plot_role", "high_ground_watch"), prop("recommended_asset_kit", "asset_mill_measured_v1")]),
                    make_object(object_id=5, name="measured_octagon_shrine_plot", x=0.0, y=0.0, obj_type="building_plot", polygon=[{"x": x, "y": y} for x, y in SHRINE_POLY], properties=[prop("floor_plan_ref", "hillwatch_ravine_shrine_plot_v0"), prop("plot_role", "ravine_edge_shrine"), prop("recommended_asset_kit", "asset_mill_measured_v1")]),
                ],
            },
            {
                "id": 5,
                "name": "hazard_edges",
                "type": "objectgroup",
                "objects": [
                    make_object(object_id=6, name="hillwatch_ravine_river_cut", x=RAVINE[0][0], y=RAVINE[0][1], obj_type="hazard_edge", polyline=[{"x": x - RAVINE[0][0], "y": y - RAVINE[0][1]} for x, y in RAVINE], properties=[prop("hazard_type", "fall_edge"), prop("severity", "high"), prop("movement_tag", "avoid")])
                ],
            },
            {
                "id": 6,
                "name": "asset_sockets",
                "type": "objectgroup",
                "objects": [
                    socket_object(7, "gatehouse_hillwatch_portal_socket", 6.5, 9.85, "pointed_arch_doorway_v1", "portal", "plot_edge", "measured_gatehouse_plot", 0.0, dims),
                    socket_object(8, "gatehouse_hillwatch_window_socket_a", 3.1, 13.0, "narrow_lancet_window_v1", "window", "plot_edge", "measured_gatehouse_plot", 270.0, dims),
                    socket_object(9, "gatehouse_hillwatch_window_socket_b", 9.9, 13.0, "narrow_lancet_window_v1", "window", "plot_edge", "measured_gatehouse_plot", 90.0, dims),
                    socket_object(10, "watch_hillwatch_stair_socket", 24.4, 11.0, "stair_landing_asset_v0", "vertical_transition", "height_seam", "measured_watch_plot", 180.0, dims),
                    socket_object(11, "watch_hillwatch_arch_socket", 25.0, 4.95, "columned_arch_portal_v1", "portal", "plot_edge", "measured_watch_plot", 0.0, dims),
                    socket_object(12, "shrine_hillwatch_oculus_socket", 22.0, 24.9, "oculus_arch_bay_v1", "ornament_panel", "plot_edge", "measured_octagon_shrine_plot", 180.0, dims),
                    socket_object(13, "ravine_hillwatch_bridge_socket", 17.0, 23.5, "bridge_segment_asset_v0", "route_bridge", "bridge_span", "hillwatch_ravine_river_cut", 60.0, dims),
                ],
            },
        ],
        "hillwatch_ravine_height_plan_v0": {
            "playable_elevation_range_m": [0.0, 8.0],
            "ravine_river_floor_m": 0.0,
            "ravine_banks_m": [1.0, 2.0],
            "lower_road_approach_m": 2.0,
            "mid_hill_slope_m": [3.0, 5.0],
            "hilltop_building_pad_m": 6.0,
            "cliff_lip_lookout_m": 6.5,
            "highest_ridge_detail_m": [7.0, 8.0],
            "watchhouse_plateau_m": 6.0,
            "visible_cliff_drop_m": 6.0,
        },
        "integrated_scene_contract_v0": {
            "layout_source": "fresh Hillwatch Ravine hex-node map, not measured_asset_aware_hex_map_template_v1",
            "expected_connection_types": ["road_threshold", "ramp_pathway", "bridge_link"],
            "terrain_features": ["watchhouse plateau at +6m", "ravine river floor at 0m", "graded road from +2m to +6m", "cliff lip/lookout", "highest ridge detail"],
            "no_claims": NO_CLAIMS,
        },
        "no_claims": NO_CLAIMS,
    }


def main() -> None:
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH.write_text(json.dumps(build_template(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {TEMPLATE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
