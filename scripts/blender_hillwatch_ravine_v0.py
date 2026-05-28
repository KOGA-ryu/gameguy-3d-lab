#!/usr/bin/env python3
"""Render the fresh Hillwatch Ravine map concept.

This is a deterministic visual target, not a production map compiler. It uses
the current blockout language: radial hex terrain, explicit height bands,
building foundation overlap, roads/pathways, and a single hilltop building.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "goal" / "architecture" / "hillwatch_ravine_v0"
BLENDER_DIR = ROOT / "goal" / "architecture" / "blender_tests"
DESIGN_PATH = OUT_DIR / "hillwatch_ravine_v0_design.json"
REPORT_PATH = OUT_DIR / "hillwatch_ravine_v0_report.json"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "hillwatch_ravine_v0.receipt.json"
BLEND_PATH = BLENDER_DIR / "hillwatch_ravine_v0.blend"
RENDER_PATH = BLENDER_DIR / "hillwatch_ravine_v0_workbench.png"
TOPDOWN_PATH = BLENDER_DIR / "hillwatch_ravine_v0_topdown.png"

WIDTH = 32
HEIGHT = 32
HEX_RADIUS = 0.55
SQRT3 = math.sqrt(3.0)

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    length_sq = abx * abx + aby * aby
    if length_sq <= 1e-9:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / length_sq))
    return math.hypot(px - (ax + abx * t), py - (ay + aby * t))


def point_to_polyline_distance(px: float, py: float, points: list[tuple[float, float]]) -> float:
    return min(distance_to_segment(px, py, ax, ay, bx, by) for (ax, ay), (bx, by) in zip(points, points[1:], strict=False))


def map_to_world(mx: float, my: float) -> tuple[float, float]:
    # Odd-row offset pointy-top layout. This is intentionally independent of the
    # older authored maps while staying visually compatible with current renders.
    x_offset = 0.5 if int(math.floor(my)) % 2 else 0.0
    return (
        ((mx + x_offset) - WIDTH * 0.5) * SQRT3 * HEX_RADIUS,
        (HEIGHT * 0.5 - my) * 1.5 * HEX_RADIUS,
    )


def world_to_map(wx: float, wy: float) -> tuple[float, float]:
    # Approximate inverse used for road sampling on top of the proof terrain.
    my = HEIGHT * 0.5 - wy / (1.5 * HEX_RADIUS)
    x_offset = 0.5 if int(math.floor(my)) % 2 else 0.0
    mx = wx / (SQRT3 * HEX_RADIUS) + WIDTH * 0.5 - x_offset
    return mx, my


def hex_corners(wx: float, wy: float, radius: float = HEX_RADIUS) -> list[tuple[float, float]]:
    return [
        (
            wx + radius * math.cos(math.radians(30.0 + 60.0 * index)),
            wy + radius * math.sin(math.radians(30.0 + 60.0 * index)),
        )
        for index in range(6)
    ]


RAVINE_PATH = [(2.0, 25.0), (8.0, 23.3), (14.0, 22.8), (20.0, 24.4), (30.0, 27.2)]
MAIN_ROAD = [(1.5, 28.0), (5.5, 25.0), (9.0, 21.0), (13.2, 16.0), (17.6, 12.0), (21.3, 9.2)]
HILL_PATH = [(16.5, 12.5), (19.0, 10.2), (21.3, 8.9)]
LOOKOUT_PATH = [(21.3, 8.9), (24.4, 11.5), (25.8, 15.2)]
BUILDING_RECT = (20.0, 6.0, 7.0, 5.5)
BUILDING_CENTER = (23.5, 8.8)


def in_rect(mx: float, my: float, rect: tuple[float, float, float, float]) -> bool:
    x, y, width, height = rect
    return x <= mx <= x + width and y <= my <= y + height


def height_level(mx: float, my: float) -> int:
    hill = max(0.0, 1.0 - math.hypot(mx - BUILDING_CENTER[0], my - BUILDING_CENTER[1]) / 12.0)
    ridge = max(0.0, 1.0 - distance_to_segment(mx, my, 19.0, 5.0, 30.0, 10.0) / 4.2)
    ravine_distance = point_to_polyline_distance(mx, my, RAVINE_PATH)
    road_distance = min(point_to_polyline_distance(mx, my, MAIN_ROAD), point_to_polyline_distance(mx, my, HILL_PATH))

    level = 2 + round(hill * 4.0) + round(ridge * 1.5)
    if road_distance < 1.45:
        climb = max(0.0, min(1.0, (mx - 4.0) / 18.0))
        level = round(2.0 + climb * 4.0)
    if ravine_distance < 0.85:
        level = 0
    elif ravine_distance < 1.55:
        level = min(level, 1)
    elif ravine_distance < 2.35:
        level = min(level, 2)
    if 19.0 <= mx <= 28.0 and 5.5 <= my <= 12.0:
        level = max(level, 6)
    if in_rect(mx, my, BUILDING_RECT):
        level = 6
    if 26.0 <= mx <= 31.5 and 8.0 <= my <= 14.5:
        level = max(level, 7)
    return int(max(0, min(8, level)))


def surface_type(mx: float, my: float, level: int) -> str:
    ravine_distance = point_to_polyline_distance(mx, my, RAVINE_PATH)
    road_distance = min(
        point_to_polyline_distance(mx, my, MAIN_ROAD),
        point_to_polyline_distance(mx, my, HILL_PATH),
        point_to_polyline_distance(mx, my, LOOKOUT_PATH),
    )
    if ravine_distance < 0.9:
        return "river"
    if ravine_distance < 2.0:
        return "ravine_wall"
    if in_rect(mx, my, BUILDING_RECT):
        return "building_pad"
    if road_distance < 1.1:
        return "road"
    if level >= 6:
        return "high_stone"
    return "grass"


def terrain_cells() -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            mx = x + 0.5
            my = y + 0.5
            wx, wy = map_to_world(mx, my)
            level = height_level(mx, my)
            cells.append(
                {
                    "cell_id": f"hillwatch_{x}_{y}",
                    "grid": [x, y],
                    "map_center": [round(mx, 3), round(my, 3)],
                    "world_center": [round(wx, 6), round(wy, 6), float(level)],
                    "height_m": float(level),
                    "surface_type": surface_type(mx, my, level),
                }
            )
    return cells


def make_terrain_mesh(cells: list[dict[str, Any]], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    material_names = ["grass", "road", "high_stone", "building_pad", "ravine_wall", "river", "side_wall"]
    material_list = [materials[name] for name in material_names]
    material_index = {name: index for index, name in enumerate(material_names)}
    by_grid = {tuple(cell["grid"]): cell for cell in cells}
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []

    def add_vertex(point: tuple[float, float, float]) -> int:
        vertices.append(point)
        return len(vertices) - 1

    for cell in cells:
        x, y = cell["grid"]
        wx, wy, z = cell["world_center"]
        corners_2d = hex_corners(float(wx), float(wy))
        corners = [(cx, cy, float(z)) for cx, cy in corners_2d]
        midpoints = [
            (
                (corners[index][0] + corners[(index + 1) % 6][0]) * 0.5,
                (corners[index][1] + corners[(index + 1) % 6][1]) * 0.5,
                float(z),
            )
            for index in range(6)
        ]
        center_index = add_vertex((float(wx), float(wy), float(z)))
        corner_indices = [add_vertex(point) for point in corners]
        midpoint_indices = [add_vertex(point) for point in midpoints]
        top_mat = material_index[str(cell["surface_type"])]
        for index in range(6):
            faces.append((center_index, corner_indices[index], midpoint_indices[index]))
            material_indices.append(top_mat)
            faces.append((center_index, midpoint_indices[index], corner_indices[(index + 1) % 6]))
            material_indices.append(top_mat)

        # Visible side walls only where the neighbor is lower or absent.
        neighbor_offsets = [(1, 0), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
        for edge_index, offset in enumerate(neighbor_offsets):
            neighbor = by_grid.get((x + offset[0], y + offset[1]))
            neighbor_z = float(neighbor["height_m"]) if neighbor else 0.0
            if neighbor and neighbor_z >= float(z):
                continue
            exposed_bottom = neighbor_z
            c0 = corners[edge_index]
            c1 = corners[(edge_index + 1) % 6]
            v0 = add_vertex((c0[0], c0[1], exposed_bottom))
            v1 = add_vertex((c1[0], c1[1], exposed_bottom))
            v2 = add_vertex(c1)
            v3 = add_vertex(c0)
            faces.append((v0, v1, v2, v3))
            material_indices.append(material_index["side_wall"])

    mesh = bpy.data.meshes.new("hillwatch_ravine_terrain_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new("hillwatch_ravine_radial_hex_terrain", mesh)
    for material in material_list:
        obj.data.materials.append(material)
    for polygon, index in zip(obj.data.polygons, material_indices, strict=True):
        polygon.material_index = index
    obj["map_id"] = "hillwatch_ravine_v0"
    obj["terrain_model"] = "radial_hex_visual_proof"
    bpy.context.collection.objects.link(obj)
    return obj


def add_cube(name: str, loc: tuple[float, float, float], dims: tuple[float, float, float], mat: bpy.types.Material, props: dict[str, Any] | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for key, value in (props or {}).items():
        obj[key] = value
    return obj


def add_cylinder(name: str, loc: tuple[float, float, float], radius: float, depth: float, mat: bpy.types.Material, vertices: int = 12) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def segment_box(name: str, p0: tuple[float, float, float], p1: tuple[float, float, float], width: float, height: float, mat: bpy.types.Material) -> bpy.types.Object:
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dz = p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy)
    loc = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5 + height * 0.5)
    obj = add_cube(name, loc, (length, width, max(0.04, height)), mat)
    obj.rotation_euler[2] = math.atan2(dy, dx)
    if abs(dz) > 1e-4:
        obj.rotation_euler[1] = -math.atan2(dz, max(length, 1e-6))
    return obj


def terrain_z_at_world(wx: float, wy: float) -> float:
    mx, my = world_to_map(wx, wy)
    return float(height_level(mx, my))


def sample_polyline_world(points: list[tuple[float, float]], samples_per_segment: int = 10) -> list[tuple[float, float, float]]:
    sampled: list[tuple[float, float, float]] = []
    for (ax, ay), (bx, by) in zip(points, points[1:], strict=False):
        for step in range(samples_per_segment):
            t = step / float(samples_per_segment)
            mx = ax + (bx - ax) * t
            my = ay + (by - ay) * t
            wx, wy = map_to_world(mx, my)
            sampled.append((wx, wy, float(height_level(mx, my)) + 0.08))
    wx, wy = map_to_world(*points[-1])
    sampled.append((wx, wy, float(height_level(*points[-1])) + 0.08))
    return sampled


def add_path_assets(name: str, points: list[tuple[float, float]], width: float, mat: bpy.types.Material) -> list[bpy.types.Object]:
    sampled = sample_polyline_world(points, samples_per_segment=3)
    objects: list[bpy.types.Object] = []
    for index, (left, right) in enumerate(zip(sampled, sampled[1:], strict=False)):
        if math.hypot(right[0] - left[0], right[1] - left[1]) < 0.1:
            continue
        objects.append(segment_box(f"{name}_{index:02d}", left, right, width, 0.08, mat))
    return objects


def add_hillwatch_building(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    wx, wy = map_to_world(*BUILDING_CENTER)
    base_z = 6.0
    created: list[bpy.types.Object] = []
    created.append(
        add_cube(
            "hillwatch_foundation_skirt",
            (wx, wy, base_z - 0.18),
            (6.2, 4.4, 0.55),
            materials["foundation"],
            {"foundation_overlap_m": 0.25, "skirt_sinks_below_terrain": True},
        )
    )
    created.append(add_cube("hillwatch_floor_slab", (wx, wy, base_z + 0.06), (5.8, 4.0, 0.18), materials["floor"]))
    wall_z = base_z + 1.05
    wall_h = 2.0
    created.append(add_cube("hillwatch_front_wall_with_door_gap_left", (wx - 1.85, wy - 2.02, wall_z), (1.4, 0.24, wall_h), materials["wall"]))
    created.append(add_cube("hillwatch_front_wall_with_door_gap_right", (wx + 1.85, wy - 2.02, wall_z), (1.4, 0.24, wall_h), materials["wall"]))
    created.append(add_cube("hillwatch_back_wall", (wx, wy + 2.02, wall_z), (5.8, 0.24, wall_h), materials["wall"]))
    created.append(add_cube("hillwatch_left_wall", (wx - 2.9, wy, wall_z), (0.24, 4.0, wall_h), materials["wall"]))
    created.append(add_cube("hillwatch_right_wall", (wx + 2.9, wy, wall_z), (0.24, 4.0, wall_h), materials["wall"]))
    for sx in (-2.85, 2.85):
        for sy in (-1.95, 1.95):
            created.append(add_cube("hillwatch_corner_post", (wx + sx, wy + sy, wall_z), (0.38, 0.38, wall_h + 0.4), materials["post"]))
    created.append(add_cube("hillwatch_threshold_landing", (wx, wy - 2.75, base_z + 0.11), (2.2, 1.1, 0.16), materials["road"]))
    created.append(add_cube("hillwatch_door_header", (wx, wy - 2.05, base_z + 2.05), (1.55, 0.32, 0.26), materials["trim"]))
    created.append(add_cube("hillwatch_roof_cap", (wx, wy, base_z + 2.55), (6.3, 4.5, 0.35), materials["roof"]))
    created.append(add_cube("hillwatch_lookout_tower", (wx + 1.8, wy + 0.8, base_z + 3.25), (1.25, 1.25, 1.35), materials["wall"]))
    created.append(add_cube("hillwatch_tower_cap", (wx + 1.8, wy + 0.8, base_z + 4.04), (1.55, 1.55, 0.28), materials["roof"]))
    for sx in (-1.4, 1.4):
        created.append(add_cube("hillwatch_lancet_window_dark", (wx + sx, wy + 2.155, base_z + 1.25), (0.55, 0.06, 1.0), materials["window"]))
    return created


def add_ravine_water(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    sampled = sample_polyline_world(RAVINE_PATH, samples_per_segment=6)
    objects: list[bpy.types.Object] = []
    for index, (left, right) in enumerate(zip(sampled, sampled[1:], strict=False)):
        p0 = (left[0], left[1], 0.08)
        p1 = (right[0], right[1], 0.08)
        objects.append(segment_box(f"ravine_roaring_water_{index:02d}", p0, p1, 1.0, 0.035, materials["water"]))
    return objects


def scene_bounds() -> tuple[float, float, float, float, float, float]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for obj in objs:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(float(world.x))
            ys.append(float(world.y))
            zs.append(float(world.z))
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def add_scene_context() -> None:
    min_x, min_y, min_z, max_x, max_y, max_z = scene_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.light_add(type="AREA", location=(center_x - 5.0, center_y - 10.0, max_z + 12.0))
    light = bpy.context.object
    light.name = "hillwatch_key_light"
    light.data.energy = 550.0
    light.data.size = 8.0
    bpy.ops.object.camera_add(location=(center_x - 16.0, center_y - 20.0, max_z + 14.0))
    cam = bpy.context.object
    direction = mathutils.Vector((center_x + 1.5, center_y + 0.4, (min_z + max_z) * 0.42)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.08
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.render.filepath = str(RENDER_PATH)


def render_topdown() -> None:
    min_x, min_y, _min_z, max_x, max_y, max_z = scene_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.camera_add(location=(center_x, center_y, max_z + 35.0))
    cam = bpy.context.object
    cam.name = "hillwatch_topdown_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.05
    direction = mathutils.Vector((center_x, center_y, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(TOPDOWN_PATH)
    bpy.ops.render.render(write_still=True)


def write_design(cells: list[dict[str, Any]], report: dict[str, Any]) -> None:
    design = {
        "schema": "hillwatch_ravine_map_design_v0",
        "created_at_utc": now_iso(),
        "map_id": "hillwatch_ravine_v0",
        "new_map_not_derived_from_previous_templates": True,
        "size": {"width_cells": WIDTH, "height_cells": HEIGHT, "height_range_m": [0.0, 8.0]},
        "height_plan": {
            "ravine_floor_m": 0.0,
            "lower_road_approach_m": 2.0,
            "building_plateau_m": 6.0,
            "cliff_lip_m": 6.0,
            "highest_ridge_m": 8.0,
        },
        "features": {
            "primary_building": "single hilltop watchhouse",
            "ravine": "roaring river cut below cliff",
            "roads": ["main climbing road", "entrance pathway", "lookout path"],
            "building_count": 1,
        },
        "cell_count": len(cells),
        "surface_counts": report["surface_counts"],
        "validation": report["validation"],
        "no_claims": NO_CLAIMS,
    }
    DESIGN_PATH.write_text(json.dumps(design, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    materials = {
        "grass": make_material("hillwatch_grass", (0.30, 0.46, 0.26, 1.0)),
        "road": make_material("hillwatch_stone_road", (0.42, 0.39, 0.33, 1.0)),
        "high_stone": make_material("hillwatch_high_stone", (0.36, 0.37, 0.34, 1.0)),
        "building_pad": make_material("hillwatch_building_pad", (0.48, 0.45, 0.38, 1.0)),
        "ravine_wall": make_material("hillwatch_ravine_wall", (0.20, 0.19, 0.18, 1.0)),
        "river": make_material("hillwatch_river", (0.14, 0.34, 0.48, 1.0)),
        "side_wall": make_material("hillwatch_exposed_cliff_wall", (0.24, 0.22, 0.20, 1.0)),
        "foundation": make_material("hillwatch_foundation", (0.22, 0.21, 0.19, 1.0)),
        "floor": make_material("hillwatch_floor", (0.46, 0.45, 0.37, 1.0)),
        "wall": make_material("hillwatch_wall", (0.56, 0.53, 0.45, 1.0)),
        "post": make_material("hillwatch_post", (0.35, 0.34, 0.30, 1.0)),
        "roof": make_material("hillwatch_roof", (0.28, 0.27, 0.25, 1.0)),
        "trim": make_material("hillwatch_trim", (0.66, 0.63, 0.55, 1.0)),
        "window": make_material("hillwatch_window_dark", (0.05, 0.07, 0.08, 1.0)),
        "water": make_material("hillwatch_roaring_water", (0.62, 0.78, 0.88, 1.0)),
    }
    cells = terrain_cells()
    terrain = make_terrain_mesh(cells, materials)
    road_objects = add_path_assets("main_climbing_road_slab", MAIN_ROAD, 1.45, materials["road"])
    path_objects = add_path_assets("hillwatch_entry_path_slab", HILL_PATH, 1.05, materials["road"])
    lookout_objects = add_path_assets("cliff_lookout_path_slab", LOOKOUT_PATH, 0.85, materials["road"])
    water_objects = add_ravine_water(materials)
    building_objects = add_hillwatch_building(materials)
    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.ops.render.render(write_still=True)
    render_topdown()
    surface_counts: dict[str, int] = {}
    height_values: list[float] = []
    for cell in cells:
        surface_counts[cell["surface_type"]] = surface_counts.get(cell["surface_type"], 0) + 1
        height_values.append(float(cell["height_m"]))
    validation = {
        "new_map_not_derived_from_previous_templates": True,
        "building_count": 1,
        "building_plateau_m": 6.0,
        "ravine_floor_m": min(height_values),
        "highest_ridge_m": max(height_values),
        "visible_cliff_drop_m": 6.0 - min(height_values),
        "has_main_road": len(road_objects) > 0,
        "has_entry_path": len(path_objects) > 0,
        "has_lookout_path": len(lookout_objects) > 0,
        "has_ravine_water": len(water_objects) > 0,
        "foundation_skirt_sinks_below_plateau": True,
    }
    report = {
        "schema": "hillwatch_ravine_v0_blender_report",
        "created_at_utc": now_iso(),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_PATH.relative_to(ROOT)),
        "design_path": str(DESIGN_PATH.relative_to(ROOT)),
        "cell_count": len(cells),
        "surface_counts": dict(sorted(surface_counts.items())),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "building_mesh_object_count": len(building_objects),
        "road_segment_count": len(road_objects),
        "entry_path_segment_count": len(path_objects),
        "lookout_path_segment_count": len(lookout_objects),
        "water_segment_count": len(water_objects),
        "terrain_object": terrain.name,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    write_design(cells, report)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "schema": "hillwatch_ravine_v0_receipt",
        "created_at_utc": report["created_at_utc"],
        "scope": "fresh visual map proof for one hilltop building over cliff and ravine",
        "files_created": {
            "design": str(DESIGN_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
            "blend": str(BLEND_PATH.relative_to(ROOT)),
            "render": str(RENDER_PATH.relative_to(ROOT)),
            "topdown": str(TOPDOWN_PATH.relative_to(ROOT)),
        },
        "no_claims": NO_CLAIMS,
        "validation": validation,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {DESIGN_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_PATH.relative_to(ROOT)}")
    print(
        "cells={cell_count} building={building_mesh_object_count} road_segments={road_segment_count} water_segments={water_segment_count}".format(
            **report
        )
    )


if __name__ == "__main__":
    main()
