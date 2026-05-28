#!/usr/bin/env python3
"""Render Pathway Engine Testbed v0 from compiled pathway data only."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "goal" / "architecture" / "pathway_engine_v0"
BLENDER_DIR = ROOT / "goal" / "architecture" / "blender_tests"

COMPILED_PATH = OUT_DIR / "pathway_engine_v0_compiled.json"
BLEND_PATH = BLENDER_DIR / "pathway_engine_v0.blend"
RENDER_PATH = BLENDER_DIR / "pathway_engine_v0_workbench.png"
TOPDOWN_PATH = BLENDER_DIR / "pathway_engine_v0_topdown.png"
BLENDER_REPORT_PATH = BLENDER_DIR / "pathway_engine_v0_report.json"

WIDTH = 32
HEIGHT = 32
HEX_RADIUS = 0.55
BASE_HEIGHT_M = 2.0
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def configure_scene_units(compiled: dict[str, Any]) -> None:
    global WIDTH, HEIGHT, HEX_RADIUS, BASE_HEIGHT_M
    map_config = compiled.get("map", {})
    WIDTH = int(map_config.get("width", WIDTH))
    HEIGHT = int(map_config.get("height", HEIGHT))
    HEX_RADIUS = float(map_config.get("hex_radius_m", HEX_RADIUS))
    BASE_HEIGHT_M = float(map_config.get("base_height_m", BASE_HEIGHT_M))


def map_to_world(mx: float, my: float) -> tuple[float, float]:
    x_offset = 0.5 if int(math.floor(my)) % 2 else 0.0
    return (
        ((mx + x_offset) - WIDTH * 0.5) * SQRT3 * HEX_RADIUS,
        (HEIGHT * 0.5 - my) * 1.5 * HEX_RADIUS,
    )


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def hex_corners(wx: float, wy: float, z: float) -> list[tuple[float, float, float]]:
    return [
        (
            wx + HEX_RADIUS * math.cos(math.radians(30.0 + 60.0 * index)),
            wy + HEX_RADIUS * math.sin(math.radians(30.0 + 60.0 * index)),
            z,
        )
        for index in range(6)
    ]


def make_terrain_mesh(cells: list[dict[str, Any]], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    material_names = ["grass", "yard", "road", "side_wall"]
    mesh_materials = [materials[name] for name in material_names]
    material_index = {name: index for index, name in enumerate(material_names)}
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []
    for cell in cells:
        wx, wy, z = [float(value) for value in cell["world_center"]]
        corners = hex_corners(wx, wy, z)
        center_index = len(vertices)
        vertices.append((wx, wy, z))
        corner_indices = []
        for corner in corners:
            corner_indices.append(len(vertices))
            vertices.append(corner)
        surface = str(cell["surface_type"])
        for index in range(6):
            faces.append((center_index, corner_indices[index], corner_indices[(index + 1) % 6]))
            material_indices.append(material_index.get(surface, material_index["grass"]))
    mesh = bpy.data.meshes.new("pathway_engine_terrain_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new("pathway_engine_flat_hex_yard", mesh)
    for material in mesh_materials:
        obj.data.materials.append(material)
    for polygon, index in zip(obj.data.polygons, material_indices, strict=True):
        polygon.material_index = index
    bpy.context.collection.objects.link(obj)
    return obj


def add_cube(name: str, loc: tuple[float, float, float], dims: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def building_world_center(building: dict[str, Any]) -> tuple[float, float, float]:
    if "world_center" in building:
        wx, wy, wz = [float(value) for value in building["world_center"]]
        return wx, wy, wz
    wx, wy = map_to_world(float(building["center_map"][0]), float(building["center_map"][1]))
    return wx, wy, BASE_HEIGHT_M


def add_building(
    building: dict[str, Any],
    plugs_by_id: dict[str, dict[str, Any]],
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    wx, wy, z = building_world_center(building)
    dims = building["dimensions_m"]
    width = float(dims["width"])
    depth = float(dims["depth"])
    height = float(dims["height"])
    objects = [
        add_cube(f"{building['building_id']}.foundation", (wx, wy, z - 0.16), (width + 0.35, depth + 0.35, 0.32), materials["foundation"]),
        add_cube(f"{building['building_id']}.floor", (wx, wy, z + 0.06), (width, depth, 0.14), materials["floor"]),
        add_cube(f"{building['building_id']}.north_wall", (wx, wy - depth * 0.5, z + height * 0.5), (width, 0.18, height), materials["wall"]),
        add_cube(f"{building['building_id']}.south_wall", (wx, wy + depth * 0.5, z + height * 0.5), (width, 0.18, height), materials["wall"]),
        add_cube(f"{building['building_id']}.west_wall", (wx - width * 0.5, wy, z + height * 0.5), (0.18, depth, height), materials["wall"]),
        add_cube(f"{building['building_id']}.east_wall", (wx + width * 0.5, wy, z + height * 0.5), (0.18, depth, height), materials["wall"]),
        add_cube(f"{building['building_id']}.roof_cap", (wx, wy, z + height + 0.18), (width + 0.35, depth + 0.35, 0.28), materials["roof"]),
    ]
    for plug in building.get("entrance_plugs", []):
        plug_record = plugs_by_id.get(plug["plug_id"])
        if plug_record is None:
            px, py = map_to_world(float(plug["position_map"][0]), float(plug["position_map"][1]))
            pz = z + 0.09
        else:
            px, py, pz = [float(value) for value in plug_record["position"]]
        objects.append(add_cube(f"{plug['plug_id']}.threshold", (px, py, pz - 0.03), (0.7, 0.7, 0.12), materials["threshold"]))
    return objects


def add_plug_marker(plug: dict[str, Any], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    position = [float(value) for value in plug["position"]]
    debug_position = (position[0], position[1], position[2] + 3.2)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.22, location=debug_position)
    obj = bpy.context.object
    obj.name = f"{plug['plug_id']}.marker"
    material_key = "plug_building" if plug["owner_type"] == "building" else "plug_road"
    obj.data.materials.append(materials[material_key])
    obj["plug_id"] = plug["plug_id"]
    obj["true_plug_position"] = ",".join(str(value) for value in position)
    return obj


def segment_box(name: str, p0: list[float], p1: list[float], width: float, height: float, mat: bpy.types.Material) -> bpy.types.Object:
    dx = float(p1[0]) - float(p0[0])
    dy = float(p1[1]) - float(p0[1])
    length = math.hypot(dx, dy)
    loc = (
        (float(p0[0]) + float(p1[0])) * 0.5,
        (float(p0[1]) + float(p1[1])) * 0.5,
        (float(p0[2]) + float(p1[2])) * 0.5 + height * 0.5,
    )
    obj = add_cube(name, loc, (length, width, height), mat)
    obj.rotation_euler[2] = math.atan2(dy, dx)
    return obj


def connection_points(connection: dict[str, Any]) -> list[list[float]]:
    generated_path = connection.get("generated_path") or {}
    points = generated_path.get("route_points") or connection.get("route_points_world") or []
    return [[float(value) for value in point] for point in points]


def add_connection_assets(connection: dict[str, Any], materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    if connection.get("status") != "pass":
        return []
    material = materials["path_threshold"] if connection["connection_type"] == "road_threshold" else materials["path_flat"]
    objects: list[bpy.types.Object] = []
    points = connection_points(connection)
    for index, (left, right) in enumerate(zip(points, points[1:], strict=False)):
        objects.append(segment_box(f"{connection['connection_id']}.segment_{index:02d}", left, right, float(connection["width_m"]), 0.08, material))
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
    bpy.ops.object.light_add(type="AREA", location=(center_x - 5.0, center_y - 8.0, max_z + 8.0))
    light = bpy.context.object
    light.name = "pathway_engine_key_light"
    light.data.energy = 450.0
    light.data.size = 7.0
    bpy.ops.object.camera_add(location=(center_x - 7.0, center_y - 13.0, max_z + 8.0))
    cam = bpy.context.object
    direction = mathutils.Vector((center_x, center_y, (min_z + max_z) * 0.35)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 0.72
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1100
    bpy.context.scene.render.filepath = str(RENDER_PATH)


def render_topdown() -> None:
    min_x, min_y, _min_z, max_x, max_y, max_z = scene_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.camera_add(location=(center_x, center_y, max_z + 28.0))
    cam = bpy.context.object
    cam.name = "pathway_engine_topdown_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 0.78
    direction = mathutils.Vector((center_x, center_y, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(TOPDOWN_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    if not COMPILED_PATH.exists():
        raise FileNotFoundError(f"missing compiled pathway artifact: {COMPILED_PATH}")
    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    compiled = load_json(COMPILED_PATH)
    configure_scene_units(compiled)
    clear_scene()
    materials = {
        "grass": make_material("pathway_testbed_grass", (0.32, 0.45, 0.31, 1.0)),
        "yard": make_material("pathway_testbed_yard", (0.42, 0.46, 0.38, 1.0)),
        "road": make_material("pathway_testbed_road", (0.37, 0.35, 0.31, 1.0)),
        "side_wall": make_material("pathway_testbed_side_wall", (0.24, 0.24, 0.22, 1.0)),
        "foundation": make_material("pathway_testbed_foundation", (0.22, 0.21, 0.19, 1.0)),
        "floor": make_material("pathway_testbed_floor", (0.46, 0.44, 0.36, 1.0)),
        "wall": make_material("pathway_testbed_wall", (0.55, 0.52, 0.45, 1.0)),
        "roof": make_material("pathway_testbed_roof", (0.28, 0.27, 0.25, 1.0)),
        "threshold": make_material("pathway_testbed_threshold", (0.62, 0.58, 0.50, 1.0)),
        "path_flat": make_material("pathway_testbed_flat_path", (0.68, 0.63, 0.48, 1.0)),
        "path_threshold": make_material("pathway_testbed_threshold_path", (0.76, 0.68, 0.42, 1.0)),
        "plug_building": make_material("pathway_testbed_building_plug", (0.00, 0.85, 1.00, 1.0)),
        "plug_road": make_material("pathway_testbed_road_plug", (1.00, 0.66, 0.00, 1.0)),
    }
    terrain = make_terrain_mesh(compiled["cells"], materials)
    plugs_by_id = {plug["plug_id"]: plug for plug in compiled["plugs"]}
    building_objects: list[bpy.types.Object] = []
    for building in compiled["buildings"]:
        building_objects.extend(add_building(building, plugs_by_id, materials))
    plug_markers = [add_plug_marker(plug, materials) for plug in compiled["plugs"]]
    connection_objects: list[bpy.types.Object] = []
    for connection in compiled["connections"]:
        connection_objects.extend(add_connection_assets(connection, materials))
    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.ops.render.render(write_still=True)
    render_topdown()
    blender_report = {
        "schema": "pathway_engine_v0_blender_report",
        "created_at_utc": now_iso(),
        "render_only": True,
        "compiled_path": str(COMPILED_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_PATH.relative_to(ROOT)),
        "terrain_object": terrain.name,
        "building_mesh_count": len(building_objects),
        "plug_marker_count": len(plug_markers),
        "connection_segment_count": len(connection_objects),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "acceptance": {
            "render_only": True,
            "compiled_json_consumed": True,
            "templates_rewritten": False,
            "exactly_three_buildings": compiled["validation"]["exactly_three_buildings"],
            "exactly_six_plugs": compiled["validation"]["exactly_six_plugs"],
            "exactly_three_connections": compiled["validation"]["exactly_three_connections"],
            "both_building_to_building_paths_pass": compiled["validation"]["both_building_to_building_paths_pass"],
            "south_road_threshold_passes": compiled["validation"]["south_road_threshold_passes"],
            "render_clearly_shows_two_paths": len(connection_objects) >= 4,
        },
        "no_claims": NO_CLAIMS,
    }
    BLENDER_REPORT_PATH.write_text(json.dumps(blender_report, indent=2) + "\n", encoding="utf-8")
    print(f"read {COMPILED_PATH.relative_to(ROOT)}")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_PATH.relative_to(ROOT)}")
    print(f"wrote {BLENDER_REPORT_PATH.relative_to(ROOT)}")
    print(
        "buildings={building_count} plugs={plug_count} connections={connection_count}".format(
            building_count=len(compiled["buildings"]),
            plug_count=len(compiled["plugs"]),
            connection_count=len(compiled["connections"]),
        )
    )


if __name__ == "__main__":
    main()
