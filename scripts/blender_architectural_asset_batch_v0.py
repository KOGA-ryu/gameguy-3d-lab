#!/usr/bin/env python3
"""Build a new compound architecture asset batch in Blender.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_architectural_asset_batch_v0.py

This creates visual blockout assets from simple deterministic geometry. It is a
review batch, not production art, structural validation, or fabrication output.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "architectural_asset_batch_v0.json"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "architectural_asset_batch_v0.blend"
RENDER_PATH = OUT_DIR / "architectural_asset_batch_v0_workbench.png"
REPORT_PATH = OUT_DIR / "architectural_asset_batch_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def add_cube(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    material: bpy.types.Material,
    parent: bpy.types.Object,
    props: dict[str, Any] | None = None,
    rotation_z: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=(0.0, 0.0, math.radians(rotation_z)))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    for key, value in (props or {}).items():
        obj[key] = value
    return obj


def add_cylinder(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    vertices: int,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    props: dict[str, Any] | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    obj.parent = parent
    for key, value in (props or {}).items():
        obj[key] = value
    return obj


def add_curve(
    name: str,
    points: list[tuple[float, float, float]],
    bevel_depth: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    props: dict[str, Any] | None = None,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points, strict=True):
        point.co = (coord[0], coord[1], coord[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    obj.parent = parent
    for key, value in (props or {}).items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_group(name: str, offset: tuple[float, float, float], metadata: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.45
    obj.location = offset
    for key, value in metadata.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def arch_points(span: float, spring_z: float, rise: float, y: float = 0.0, segments: int = 14) -> list[tuple[float, float, float]]:
    half = span * 0.5
    pts: list[tuple[float, float, float]] = []
    for index in range(segments + 1):
        t = index / segments
        x = -half + half * t
        z = spring_z + rise * (1.0 - (1.0 - t) ** 2)
        pts.append((x, y, z))
    for index in range(1, segments + 1):
        t = index / segments
        x = half * t
        z = spring_z + rise * (1.0 - t**2)
        pts.append((x, y, z))
    return pts


def build_pointed_arch_bay(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    for x in (-0.9, 0.9):
        add_cube("arch_bay_column_base", (x, 0, 0.1), (0.36, 0.36, 0.2), mats["stone_dark"], parent)
        add_cylinder("arch_bay_oct_column", (x, 0, 0.9), 0.16, 1.6, 8, mats["stone_gold"], parent)
        add_cube("arch_bay_column_cap", (x, 0, 1.72), (0.42, 0.42, 0.16), mats["stone_dark"], parent)
    add_curve("arch_bay_pointed_rib", arch_points(1.8, 1.68, 1.0), 0.045, mats["rib"], parent, {"bend_law": "pointed_arch_polyline_v0"})
    add_cube("arch_bay_low_wall_left", (-1.18, 0, 0.78), (0.26, 0.18, 1.15), mats["stone"], parent)
    add_cube("arch_bay_low_wall_right", (1.18, 0, 0.78), (0.26, 0.18, 1.15), mats["stone"], parent)


def build_buttress_seed(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("buttress_wall_anchor", (-0.55, 0, 0.85), (0.3, 0.34, 1.7), mats["stone"], parent)
    add_cube("buttress_foot", (0.75, 0, 0.16), (0.85, 0.48, 0.32), mats["stone_dark"], parent)
    add_cube("buttress_slope_strut", (0.18, 0, 0.78), (1.35, 0.24, 0.22), mats["rib"], parent, rotation_z=0.0)
    bpy.context.object.rotation_euler[1] = math.radians(-27.0)
    add_cube("buttress_top_cap", (-0.55, 0, 1.74), (0.48, 0.42, 0.16), mats["stone_dark"], parent)


def build_ribbed_column_cluster(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cylinder("cluster_core_oct_column", (0, 0, 1.05), 0.24, 2.1, 8, mats["stone_gold"], parent)
    for angle in (0, 90, 180, 270):
        x = math.cos(math.radians(angle)) * 0.31
        y = math.sin(math.radians(angle)) * 0.31
        add_cylinder("cluster_outer_rib", (x, y, 1.03), 0.055, 2.06, 8, mats["rib"], parent)
    add_cylinder("cluster_base_ring", (0, 0, 0.12), 0.38, 0.24, 12, mats["stone_dark"], parent)
    add_cylinder("cluster_cap_ring", (0, 0, 2.18), 0.38, 0.24, 12, mats["stone_dark"], parent)


def build_bridge_segment(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("bridge_deck", (0, 0, 0.12), (2.4, 0.8, 0.24), mats["walkable"], parent)
    for x in (-1.0, 1.0):
        for y in (-0.48, 0.48):
            add_cube("bridge_post", (x, y, 0.68), (0.16, 0.16, 1.1), mats["stone_gold"], parent)
    for y in (-0.48, 0.48):
        add_cube("bridge_rail", (0, y, 1.08), (2.35, 0.09, 0.12), mats["barrier"], parent)


def build_wall_socket_panel(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("socket_wall_backer", (0, 0, 0.85), (2.2, 0.18, 1.7), mats["stone"], parent)
    add_cube("socket_inner_panel", (0, -0.105, 0.92), (1.25, 0.06, 0.95), mats["recess"], parent)
    add_cube("socket_top_trim", (0, -0.16, 1.48), (1.55, 0.08, 0.12), mats["rib"], parent)
    add_cube("socket_bottom_trim", (0, -0.16, 0.36), (1.55, 0.08, 0.12), mats["rib"], parent)
    for x in (-0.82, 0.82):
        add_cube("socket_side_trim", (x, -0.16, 0.92), (0.1, 0.08, 1.1), mats["rib"], parent)


def build_stepped_plinth(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("plinth_step_0", (0, 0, 0.08), (1.7, 1.2, 0.16), mats["stone_dark"], parent)
    add_cube("plinth_step_1", (0, 0, 0.25), (1.25, 0.88, 0.18), mats["stone"], parent)
    add_cube("plinth_step_2", (0, 0, 0.46), (0.78, 0.54, 0.24), mats["stone_gold"], parent)


def build_stair_landing(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    for i in range(4):
        add_cube("landing_stair_step", (-0.65 + i * 0.32, 0, 0.09 + i * 0.13), (0.32, 0.95, 0.18), mats["stone"], parent)
    add_cube("landing_top", (0.95, 0, 0.63), (0.9, 0.95, 0.22), mats["walkable"], parent)
    add_cube("landing_side_trim_l", (0.16, -0.55, 0.4), (1.85, 0.08, 0.16), mats["rib"], parent)
    add_cube("landing_side_trim_r", (0.16, 0.55, 0.4), (1.85, 0.08, 0.16), mats["rib"], parent)


def build_roof_joist_frame(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("roof_frame_left", (-0.95, 0, 0.08), (0.12, 1.7, 0.16), mats["rib"], parent)
    add_cube("roof_frame_right", (0.95, 0, 0.08), (0.12, 1.7, 0.16), mats["rib"], parent)
    add_cube("roof_frame_top", (0, 0.8, 0.08), (2.0, 0.12, 0.16), mats["rib"], parent)
    add_cube("roof_frame_bottom", (0, -0.8, 0.08), (2.0, 0.12, 0.16), mats["rib"], parent)
    for x in (-0.45, 0.0, 0.45):
        add_cube("roof_joist", (x, 0, 0.16), (0.08, 1.7, 0.14), mats["stone_gold"], parent)


def build_window_tracery_panel(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("tracery_backer", (0, 0, 0.8), (2.0, 0.16, 1.6), mats["stone"], parent)
    for x in (-0.45, 0.45):
        add_curve("tracery_pointed_arch", [(px + x, py - 0.11, pz - 0.1) for px, py, pz in arch_points(0.65, 0.55, 0.65, segments=10)], 0.028, mats["rib"], parent)
        add_cube("tracery_mullion_l", (x - 0.32, -0.13, 0.48), (0.05, 0.07, 0.72), mats["rib"], parent)
        add_cube("tracery_mullion_r", (x + 0.32, -0.13, 0.48), (0.05, 0.07, 0.72), mats["rib"], parent)
    add_cube("tracery_center_mullion", (0, -0.13, 0.78), (0.07, 0.08, 1.28), mats["rib"], parent)


def build_corner_pier(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("corner_pier_vertical_a", (-0.18, 0, 0.8), (0.36, 0.32, 1.6), mats["stone_gold"], parent)
    add_cube("corner_pier_vertical_b", (0.16, 0.18, 0.8), (0.32, 0.36, 1.6), mats["stone_gold"], parent)
    add_cube("corner_pier_base", (0, 0, 0.12), (0.72, 0.72, 0.24), mats["stone_dark"], parent)
    add_cube("corner_pier_cap", (0, 0, 1.68), (0.78, 0.78, 0.2), mats["stone_dark"], parent)


BUILDERS: dict[str, Callable[[bpy.types.Object, dict[str, bpy.types.Material]], None]] = {
    "pointed_arch_bay": build_pointed_arch_bay,
    "buttress_seed": build_buttress_seed,
    "ribbed_column_cluster": build_ribbed_column_cluster,
    "bridge_segment": build_bridge_segment,
    "wall_socket_panel": build_wall_socket_panel,
    "stepped_plinth": build_stepped_plinth,
    "stair_landing": build_stair_landing,
    "roof_joist_frame": build_roof_joist_frame,
    "window_tracery_panel": build_window_tracery_panel,
    "corner_pier": build_corner_pier,
}


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    if not objs:
        return mathutils.Vector((0, 0, 0)), mathutils.Vector((1, 1, 1))
    corners: list[mathutils.Vector] = []
    for obj in objs:
        for corner in obj.bound_box:
            corners.append(obj.matrix_world @ mathutils.Vector(corner))
    mins = mathutils.Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    maxs = mathutils.Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return mins, maxs


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(2.0, -8.0, 8.0))
    light = bpy.context.object
    light.name = "architectural_asset_batch_area_light"
    light.data.energy = 650.0
    light.data.size = 7.0
    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((8.5, -12.0, 8.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.32
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    recipe = load_json(RECIPE_PATH)
    mats = {
        "stone": make_material("mat_warm_stone", (0.55, 0.51, 0.42, 1.0)),
        "stone_dark": make_material("mat_dark_stone", (0.36, 0.35, 0.31, 1.0)),
        "stone_gold": make_material("mat_old_limestone", (0.72, 0.64, 0.41, 1.0)),
        "rib": make_material("mat_rib_highlight", (0.84, 0.74, 0.48, 1.0)),
        "barrier": make_material("mat_blue_barrier", (0.28, 0.48, 0.64, 1.0)),
        "walkable": make_material("mat_green_walkable", (0.30, 0.58, 0.38, 1.0)),
        "recess": make_material("mat_recess_shadow", (0.24, 0.23, 0.21, 1.0)),
    }
    created_assets: list[dict[str, Any]] = []
    cols = 5
    spacing_x = 3.1
    spacing_y = 3.0
    for index, asset in enumerate(recipe["assets"]):
        col = index % cols
        row = index // cols
        offset = ((col - 2) * spacing_x, (1 - row) * spacing_y, 0.0)
        parent = add_group(asset["asset_id"], offset, {
            "asset_id": asset["asset_id"],
            "architectural_role": asset["architectural_role"],
            "builder_kind": asset["builder_kind"],
            "semantic_tags": ",".join(asset["semantic_tags"]),
            "no_structural_claims": True,
            "no_production_approval": True,
        })
        BUILDERS[asset["builder_kind"]](parent, mats)
        created_assets.append({
            "asset_id": asset["asset_id"],
            "builder_kind": asset["builder_kind"],
            "architectural_role": asset["architectural_role"],
            "semantic_tags": asset["semantic_tags"],
        })

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    empty_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "EMPTY")
    report = {
        "schema": "architectural_asset_batch_blender_report_v0",
        "source_recipe": str(RECIPE_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "asset_count": len(created_assets),
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "empty_object_count": empty_count,
        "assets": created_assets,
        "rules": {
            "new_visual_batch": True,
            "proof_scene_only": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True
        }
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"assets={len(created_assets)} mesh={mesh_count} curves={curve_count} empties={empty_count}")


if __name__ == "__main__":
    main()
