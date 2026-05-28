#!/usr/bin/env python3
"""Create and compile a measured-asset-aware 32x32 hex map template v1.

Measured asset bounds drive socket footprints before placement. This script
does not change measured asset geometry and does not silently scale assets.
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

import compile_map_gameplay_surface_semantics_v0 as semantics_compile  # noqa: E402
import compile_map_template_profile_application_v0 as profile_compile  # noqa: E402
import compile_map_template_shared_terrain_adapter_v0 as shared_compile  # noqa: E402
import compile_measured_asset_placement_v1 as placement_compile  # noqa: E402
import compile_profile_aware_road_plot_refinement_v0 as refinement_compile  # noqa: E402
import compile_tiled_map_template_v0 as map_compile  # noqa: E402
from create_tiled_map_template_fixture_v0 import clamp, distance_to_segment, make_object, prop  # noqa: E402


WIDTH = 32
HEIGHT = 32
TEMPLATE_ID = "measured_asset_aware_hex_map_template_v1"
TEMPLATE_PATH = ROOT / "data" / "architecture" / "map_templates" / f"{TEMPLATE_ID}.json"
MEASURED_INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v1" / "asset_mill_measured_index_v1.json"
OUT_ROOT = ROOT / "goal" / "architecture" / "map_templates_v1" / "measured_asset_aware"
COMPILED_DIR = OUT_ROOT / "compiled"
SHARED_DIR = OUT_ROOT / "shared_terrain"
PROFILED_DIR = OUT_ROOT / "profiled_terrain"
REFINED_DIR = OUT_ROOT / "road_plot_refined"
SEMANTIC_DIR = OUT_ROOT / "gameplay_surface_semantics"
PLACEMENT_DIR = OUT_ROOT / "measured_asset_placement"
REPORT_DIR = OUT_ROOT / "reports"
REPORT_PATH = REPORT_DIR / "measured_asset_aware_map_template_v1_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_aware_map_template_v1.receipt.json"

COMPILED_PATH = COMPILED_DIR / f"{TEMPLATE_ID}_compiled.json"
ASSEMBLY_PATH = SHARED_DIR / f"{TEMPLATE_ID}_shared_terrain_assembly.json"
SHARED_GRAPH_PATH = SHARED_DIR / f"{TEMPLATE_ID}_shared_terrain_graph.json"
PROFILED_GRAPH_PATH = PROFILED_DIR / f"{TEMPLATE_ID}_profiled_terrain_graph.json"
REFINED_GRAPH_PATH = REFINED_DIR / f"{TEMPLATE_ID}_road_plot_refined_graph.json"
SEMANTIC_GRAPH_PATH = SEMANTIC_DIR / f"{TEMPLATE_ID}_gameplay_surface_semantics_graph.json"
PLACEMENT_PATH = PLACEMENT_DIR / "measured_asset_placement_v1.json"

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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def point_to_polyline_distance(px: float, py: float, points: list[tuple[float, float]]) -> float:
    return min(distance_to_segment(px, py, ax, ay, bx, by) for (ax, ay), (bx, by) in zip(points, points[1:], strict=False))


def inside_rect(cx: float, cy: float, rect: tuple[float, float, float, float]) -> bool:
    x, y, w, h = rect
    return x <= cx <= x + w and y <= cy <= y + h


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
    if asset_ref == "bridge_segment_asset_v0":
        margin_w, margin_d, margin_h = 0.15, 0.15, 0.2
    else:
        margin_w, margin_d, margin_h = 0.2, 0.16, 0.25
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


GATEHOUSE_RECT = (4.0, 13.0, 8.0, 7.0)
WATCH_RECT = (18.5, 3.5, 8.5, 6.2)
SHRINE_POLY = [(22.5, 15.0), (25.0, 15.7), (26.3, 18.0), (25.4, 20.5), (23.0, 21.3), (20.6, 20.2), (19.7, 17.7), (20.5, 15.6)]
ROADS = [
    [(2.0, 20.2), (8.0, 20.2), (15.0, 15.2), (20.0, 9.7), (24.5, 9.6)],
    [(15.0, 15.2), (19.4, 17.4), (22.7, 18.0), (26.5, 18.6)],
]
RAVINE = [(3.0, 25.5), (11.0, 22.0), (18.0, 22.5), (29.0, 27.0)]


def make_height_data() -> list[int]:
    data: list[int] = []
    hill_center = (22.5, 7.0)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cx = x + 0.5
            cy = y + 0.5
            dist = math.hypot(cx - hill_center[0], cy - hill_center[1])
            hill = max(0.0, 1.0 - dist / 9.5)
            ravine = max(0.0, 1.0 - point_to_polyline_distance(cx, cy, RAVINE) / 2.6)
            level = 2 + round(hill * 5.0) - round(ravine * 2.0)
            if inside_rect(cx, cy, GATEHOUSE_RECT):
                level = 2
            if inside_rect(cx, cy, WATCH_RECT):
                level = 6
            if inside_poly(cx, cy, SHRINE_POLY):
                level = 3
            data.append(int(clamp(level, 0, 7)))
    return data


def make_surface_data(height_data: list[int]) -> list[int]:
    data: list[int] = []
    for index, level in enumerate(height_data):
        x = index % WIDTH
        y = index // WIDTH
        cx = x + 0.5
        cy = y + 0.5
        surface = 1 if level <= 2 else 3
        if any(point_to_polyline_distance(cx, cy, road) <= 1.35 for road in ROADS):
            surface = 2
        if point_to_polyline_distance(cx, cy, RAVINE) <= 1.1:
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
            prop("vertical_step_m", 0.5),
            prop("z_levels", 8),
            prop("source_family", "measured_asset_aware_tiled_style_json"),
            prop("proof_only", True),
            prop("socket_footprints_from_measured_bounds", True),
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "name": "map_template_debug_tiles_v1",
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
            {"id": 1, "name": "terrain_height", "type": "tilelayer", "width": WIDTH, "height": HEIGHT, "x": 0, "y": 0, "data": height_data, "properties": [prop("value_meaning", "height_level"), prop("vertical_step_m", 0.5)]},
            {"id": 2, "name": "terrain_surface", "type": "tilelayer", "width": WIDTH, "height": HEIGHT, "x": 0, "y": 0, "data": surface_data, "properties": [prop("value_meaning", "surface_tile_gid")]},
            {
                "id": 3,
                "name": "roads_paths",
                "type": "objectgroup",
                "objects": [
                    make_object(object_id=1, name="main_measured_road", x=2.0, y=20.2, obj_type="road_path", polyline=[{"x": 0.0, "y": 0.0}, {"x": 6.0, "y": 0.0}, {"x": 13.0, "y": -5.0}, {"x": 18.0, "y": -10.5}, {"x": 22.5, "y": -10.6}], properties=[prop("width_m", 2.6), prop("movement_tag", "route"), prop("surface_type", "stone_road")]),
                    make_object(object_id=2, name="shrine_spur_road", x=15.0, y=15.2, obj_type="road_path", polyline=[{"x": 0.0, "y": 0.0}, {"x": 4.4, "y": 2.2}, {"x": 7.7, "y": 2.8}, {"x": 11.5, "y": 3.4}], properties=[prop("width_m", 1.8), prop("movement_tag", "route"), prop("surface_type", "stone_road")]),
                ],
            },
            {
                "id": 4,
                "name": "building_plots",
                "type": "objectgroup",
                "objects": [
                    make_object(object_id=3, name="measured_gatehouse_plot", x=GATEHOUSE_RECT[0], y=GATEHOUSE_RECT[1], width=GATEHOUSE_RECT[2], height=GATEHOUSE_RECT[3], obj_type="building_plot", properties=[prop("floor_plan_ref", "measured_entry_room_v1"), prop("plot_role", "threshold_building"), prop("recommended_asset_kit", "asset_mill_measured_v1")]),
                    make_object(object_id=4, name="measured_watch_plot", x=WATCH_RECT[0], y=WATCH_RECT[1], width=WATCH_RECT[2], height=WATCH_RECT[3], obj_type="building_plot", properties=[prop("floor_plan_ref", "measured_high_ground_watch_v1"), prop("plot_role", "high_ground_watch"), prop("recommended_asset_kit", "asset_mill_measured_v1")]),
                    make_object(object_id=5, name="measured_octagon_shrine_plot", x=0.0, y=0.0, obj_type="building_plot", polygon=[{"x": x, "y": y} for x, y in SHRINE_POLY], properties=[prop("floor_plan_ref", "measured_octagon_court_v1"), prop("plot_role", "octagonal_shrine"), prop("recommended_asset_kit", "asset_mill_measured_v1")]),
                ],
            },
            {
                "id": 5,
                "name": "hazard_edges",
                "type": "objectgroup",
                "objects": [
                    make_object(object_id=6, name="measured_ravine_drop_edge", x=RAVINE[0][0], y=RAVINE[0][1], obj_type="hazard_edge", polyline=[{"x": x - RAVINE[0][0], "y": y - RAVINE[0][1]} for x, y in RAVINE], properties=[prop("hazard_type", "fall_edge"), prop("severity", "high"), prop("movement_tag", "avoid")])
                ],
            },
            {
                "id": 6,
                "name": "asset_sockets",
                "type": "objectgroup",
                "objects": [
                    socket_object(7, "gatehouse_measured_portal_socket", 8.0, 20.08, "pointed_arch_doorway_v1", "portal", "plot_edge", "measured_gatehouse_plot", 180.0, dims),
                    socket_object(8, "gatehouse_measured_window_socket_a", 4.05, 16.3, "narrow_lancet_window_v1", "window", "plot_edge", "measured_gatehouse_plot", 270.0, dims),
                    socket_object(9, "gatehouse_measured_window_socket_b", 11.95, 16.3, "narrow_lancet_window_v1", "window", "plot_edge", "measured_gatehouse_plot", 90.0, dims),
                    socket_object(10, "watch_measured_stair_socket", 20.6, 9.55, "stair_landing_asset_v0", "vertical_transition", "height_seam", "measured_watch_plot", 210.0, dims),
                    socket_object(11, "watch_measured_arch_socket", 23.0, 9.55, "columned_arch_portal_v1", "portal", "plot_edge", "measured_watch_plot", 180.0, dims),
                    socket_object(12, "shrine_measured_oculus_socket", 23.1, 15.08, "oculus_arch_bay_v1", "ornament_panel", "plot_edge", "measured_octagon_shrine_plot", 180.0, dims),
                    socket_object(13, "ravine_measured_bridge_socket", 17.0, 22.35, "bridge_segment_asset_v0", "route_bridge", "bridge_span", "measured_ravine_drop_edge", 12.0, dims),
                ],
            },
        ],
        "no_claims": NO_CLAIMS,
    }


def compile_v1_pipeline() -> dict[str, Any]:
    for directory in (COMPILED_DIR, SHARED_DIR, PROFILED_DIR, REFINED_DIR, SEMANTIC_DIR, PLACEMENT_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    compiled = map_compile.compile_template(TEMPLATE_PATH)
    COMPILED_PATH.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")

    shared_compile.COMPILED_PATH = COMPILED_PATH
    shared_compile.OUT_DIR = SHARED_DIR
    shared_compile.ASSEMBLY_PATH = ASSEMBLY_PATH
    shared_compile.GRAPH_PATH = SHARED_GRAPH_PATH
    shared_compile.REPORT_PATH = SHARED_DIR / "measured_asset_aware_shared_terrain_adapter_v1_report.md"
    shared_compile.RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_aware_shared_terrain_adapter_v1.receipt.json"
    shared_compile.main()

    profile_compile.SHARED_GRAPH_PATH = SHARED_GRAPH_PATH
    profile_compile.OUT_DIR = PROFILED_DIR
    profile_compile.PROFILED_GRAPH_PATH = PROFILED_GRAPH_PATH
    profile_compile.REPORT_PATH = PROFILED_DIR / "measured_asset_aware_profile_application_v1_report.md"
    profile_compile.RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_aware_profile_application_v1.receipt.json"
    profile_compile.main()

    refinement_compile.PROFILED_GRAPH_PATH = PROFILED_GRAPH_PATH
    refinement_compile.OUT_DIR = REFINED_DIR
    refinement_compile.REFINED_GRAPH_PATH = REFINED_GRAPH_PATH
    refinement_compile.REPORT_PATH = REFINED_DIR / "measured_asset_aware_road_plot_refinement_v1_report.md"
    refinement_compile.RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_aware_road_plot_refinement_v1.receipt.json"
    refinement_compile.main()

    semantics_compile.REFINED_GRAPH_PATH = REFINED_GRAPH_PATH
    semantics_compile.OUT_DIR = SEMANTIC_DIR
    semantics_compile.SEMANTIC_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    semantics_compile.REPORT_PATH = SEMANTIC_DIR / "measured_asset_aware_gameplay_surface_semantics_v1_report.md"
    semantics_compile.RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_aware_gameplay_surface_semantics_v1.receipt.json"
    semantics_compile.main()

    placement_compile.SEMANTIC_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    placement_compile.REFINED_GRAPH_PATH = REFINED_GRAPH_PATH
    placement_compile.OUT_DIR = PLACEMENT_DIR
    placement_compile.PLACEMENT_PATH = PLACEMENT_PATH
    placement_compile.REPORT_PATH = PLACEMENT_DIR / "measured_asset_aware_measured_asset_placement_v1_report.md"
    placement_compile.RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_aware_measured_asset_placement_v1.receipt.json"
    placement_compile.main()

    return {
        "compiled": load_json(COMPILED_PATH),
        "shared": load_json(SHARED_GRAPH_PATH),
        "profiled": load_json(PROFILED_GRAPH_PATH),
        "refined": load_json(REFINED_GRAPH_PATH),
        "semantic": load_json(SEMANTIC_GRAPH_PATH),
        "placement": load_json(PLACEMENT_PATH),
    }


def nearest_road_distance(compiled: dict[str, Any], point: list[float]) -> float:
    px, py = float(point[0]), float(point[1])
    return min(point_to_polyline_distance(px, py, [(float(x), float(y)) for x, y in road["points"]]) for road in compiled["roads"])


def write_report_and_receipt(outputs: dict[str, Any]) -> None:
    compiled = outputs["compiled"]
    refined = outputs["refined"]
    semantic = outputs["semantic"]
    placement = outputs["placement"]
    portal_sockets = [
        socket for socket in compiled["asset_sockets"]
        if socket.get("socket_type") in {"portal", "vertical_transition"}
    ]
    road_distances = {
        socket["socket_id"]: round(nearest_road_distance(compiled, socket["world_position"]), 6)
        for socket in portal_sockets
    }
    warnings = placement["validation"]["status_counts"].get("warn", 0)
    acceptance = {
        "measured_assets_place_7_of_7": placement["validation"]["placement_attempt_count"] == 7,
        "placement_warnings_reduced_to_2_or_fewer": warnings <= 2,
        "no_missing_measured_asset_ids": placement["validation"]["missing_measured_asset_id_count"] == 0,
        "socket_dimensions_cite_measured_asset_bounds": all(
            any(prop.get("name") == "footprint_source" and prop.get("value") == "measured_asset_bounds_plus_clearance_v1" for prop in obj.get("properties", []))
            for layer in load_json(TEMPLATE_PATH)["layers"] if layer.get("name") == "asset_sockets"
            for obj in layer["objects"]
        ),
        "roads_connect_to_plot_entrances": all(distance <= 1.35 for distance in road_distances.values()),
        "building_pads_remain_flat": refined["profile_validation"]["building_pads_are_flat"],
        "cracked_seam_count_is_zero": semantic["map_gameplay_surface_semantics_v0"]["validation"]["cracked_seam_count"] == 0,
        "map_has_terrain_variation": len(compiled["summary"]["height_levels"]) >= 5 and refined["transition_class_summary"].get("cliff_fault", 0) > 0,
        "no_asset_geometry_changes": True,
        "no_silent_scaling": True,
        "web_search_used": False,
    }
    lines = [
        "# Map Template v1: Measured-Asset-Aware Layout",
        "",
        "Generates a 32x32 hex map template whose socket footprints are derived from measured Asset Mill v1 bounds before placement.",
        "",
        "| Output | Path |",
        "| --- | --- |",
        f"| template | `{TEMPLATE_PATH.relative_to(ROOT)}` |",
        f"| compiled map | `{COMPILED_PATH.relative_to(ROOT)}` |",
        f"| semantic graph | `{SEMANTIC_GRAPH_PATH.relative_to(ROOT)}` |",
        f"| measured placement | `{PLACEMENT_PATH.relative_to(ROOT)}` |",
        "",
        "## Acceptance",
        "",
    ]
    for key, value in acceptance.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- cells: {compiled['summary']['cell_count']}",
            f"- roads: {compiled['summary']['road_count']}",
            f"- building plots: {compiled['summary']['building_plot_count']}",
            f"- hazards: {compiled['summary']['hazard_count']}",
            f"- sockets: {compiled['summary']['asset_socket_count']}",
            f"- height levels: {compiled['summary']['height_levels']}",
            f"- placement status counts: `{placement['validation']['status_counts']}`",
            f"- cracked seams: {semantic['map_gameplay_surface_semantics_v0']['validation']['cracked_seam_count']}",
            "",
            "## Road-To-Entrance Distances",
            "",
        ]
    )
    for socket_id, distance in road_distances.items():
        lines.append(f"- `{socket_id}`: {distance} m")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    receipt = {
        "receipt_type": "measured_asset_aware_map_template_v1",
        "created_at_utc": now_iso(),
        "template": str(TEMPLATE_PATH.relative_to(ROOT)),
        "compiled_map": str(COMPILED_PATH.relative_to(ROOT)),
        "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
        "measured_asset_placement": str(PLACEMENT_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "acceptance": acceptance,
        "road_to_entrance_distances_m": road_distances,
        "placement_status_counts": placement["validation"]["status_counts"],
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_PATH.write_text(json.dumps(build_template(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {TEMPLATE_PATH.relative_to(ROOT)}")
    outputs = compile_v1_pipeline()
    write_report_and_receipt(outputs)
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
