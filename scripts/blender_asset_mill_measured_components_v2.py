#!/usr/bin/env python3
"""Render Asset Mill Measured Components v2 review scene.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_asset_mill_measured_components_v2.py

This is a visual proof of local measured component recipes only. It is not
production art, structural validation, fabrication output, or historical
accuracy approval.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_asset_mill_measured_components_v2 as compiler  # noqa: E402


INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v2" / "asset_mill_measured_index_v2.json"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "asset_mill_measured_components_v2.blend"
RENDER_PATH = OUT_DIR / "asset_mill_measured_components_v2_workbench.png"
REPORT_PATH = OUT_DIR / "asset_mill_measured_components_v2_report.json"


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


def make_materials() -> dict[str, bpy.types.Material]:
    return {
        "stone": make_material("v2_measured_warm_stone", (0.56, 0.52, 0.44, 1.0)),
        "support": make_material("v2_measured_support_limestone", (0.72, 0.64, 0.40, 1.0)),
        "walkable": make_material("v2_measured_walkable_slab", (0.30, 0.56, 0.36, 1.0)),
        "rib": make_material("v2_measured_arch_rib", (0.82, 0.72, 0.48, 1.0)),
        "cap": make_material("v2_measured_cap_block", (0.62, 0.58, 0.50, 1.0)),
        "rail": make_material("v2_measured_rail_barrier", (0.30, 0.46, 0.62, 1.0)),
        "trim": make_material("v2_measured_trim_strip", (0.46, 0.52, 0.60, 1.0)),
        "socket": make_material("v2_measured_socket_marker", (0.12, 0.40, 0.86, 1.0)),
    }


def material_for(part: dict[str, Any], materials: dict[str, bpy.types.Material]) -> bpy.types.Material:
    role = str(part.get("material_role", "stone"))
    return materials.get(role, materials["stone"])


def add_group(asset: dict[str, Any], offset: tuple[float, float, float]) -> bpy.types.Object:
    obj = bpy.data.objects.new(asset["asset_id"], None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.32
    obj.location = offset
    obj["asset_id"] = asset["asset_id"]
    obj["source_recipe"] = asset["recipe_path"]
    obj["no_production_claim"] = True
    obj["no_structural_claim"] = True
    obj["no_fabrication_claim"] = True
    obj["no_historical_accuracy_claim"] = True
    bpy.context.collection.objects.link(obj)
    return obj


def parent_local(obj: bpy.types.Object, parent: bpy.types.Object) -> None:
    obj.parent = parent
    obj.matrix_parent_inverse.identity()


def add_cube(part: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    loc = tuple(float(value) for value in part["location_m"])
    dims = tuple(float(value) for value in part["dimensions_m"])
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = f"{parent.name}.{part['name']}"
    obj.dimensions = dims
    obj.data.materials.append(material_for(part, materials))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parent_local(obj, parent)
    obj["asset_id"] = parent.name
    obj["proof_primitive"] = part["primitive"]
    return obj


def add_cylinder(part: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    loc = tuple(float(value) for value in part["location_m"])
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=int(part["vertices"]),
        radius=float(part["radius_m"]),
        depth=float(part["depth_m"]),
        location=loc,
    )
    obj = bpy.context.object
    obj.name = f"{parent.name}.{part['name']}"
    obj.data.materials.append(material_for(part, materials))
    parent_local(obj, parent)
    obj["asset_id"] = parent.name
    obj["proof_primitive"] = part["primitive"]
    return obj


def pointed_arch_points(span: float, spring_z: float, rise: float, y: float, segments: int = 18) -> list[tuple[float, float, float]]:
    half = span * 0.5
    points: list[tuple[float, float, float]] = []
    for index in range(segments + 1):
        t = index / segments
        x = -half + half * t
        z = spring_z + rise * (1.0 - (1.0 - t) ** 2)
        points.append((x, y, z))
    for index in range(1, segments + 1):
        t = index / segments
        x = half * t
        z = spring_z + rise * (1.0 - t**2)
        points.append((x, y, z))
    return points


def round_arch_points(span: float, spring_z: float, y: float, segments: int = 28) -> list[tuple[float, float, float]]:
    radius = span * 0.5
    return [
        (
            math.cos(math.pi - math.pi * index / segments) * radius,
            y,
            spring_z + math.sin(math.pi - math.pi * index / segments) * radius,
        )
        for index in range(segments + 1)
    ]


def add_curve(part: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    if part["curve_kind"] == "round":
        points = round_arch_points(float(part["span_m"]), float(part["spring_z_m"]), float(part["y_m"]))
    else:
        points = pointed_arch_points(float(part["span_m"]), float(part["spring_z_m"]), float(part["rise_m"]), float(part["y_m"]))
    curve = bpy.data.curves.new(f"{parent.name}.{part['name']}_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = float(part["bevel_depth_m"])
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points, strict=True):
        point.co = (coord[0], coord[1], coord[2], 1.0)
    obj = bpy.data.objects.new(f"{parent.name}.{part['name']}", curve)
    obj.data.materials.append(material_for(part, materials))
    parent_local(obj, parent)
    obj["asset_id"] = parent.name
    obj["proof_primitive"] = part["primitive"]
    bpy.context.collection.objects.link(obj)
    return obj


def add_socket_markers(asset: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for item in asset["sockets"]:
        loc = tuple(float(value) for value in item["position_m"])
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.055, location=loc)
        obj = bpy.context.object
        obj.name = f"{parent.name}.{item['socket_id']}"
        obj.data.materials.append(materials["socket"])
        parent_local(obj, parent)
        obj["asset_id"] = parent.name
        obj["socket_id"] = item["socket_id"]
        obj["connector_term"] = item["connector_term"]
        obj["socket_role"] = item["role"]
        objects.append(obj)
    return objects


def create_asset(asset: dict[str, Any], materials: dict[str, bpy.types.Material], offset: tuple[float, float, float]) -> list[bpy.types.Object]:
    parent = add_group(asset, offset)
    created: list[bpy.types.Object] = [parent]
    for part in asset["proof_primitives"]:
        primitive = part["primitive"]
        if primitive == "cube":
            created.append(add_cube(part, materials, parent))
        elif primitive == "cylinder":
            created.append(add_cylinder(part, materials, parent))
        elif primitive == "curve":
            created.append(add_curve(part, materials, parent))
        else:
            raise ValueError(f"{asset['asset_id']} unsupported proof primitive {primitive}")
    created.extend(add_socket_markers(asset, materials, parent))
    return created


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    if not objs:
        return mathutils.Vector((0.0, 0.0, 0.0)), mathutils.Vector((1.0, 1.0, 1.0))
    mins = mathutils.Vector(
        (
            min((obj.matrix_world @ mathutils.Vector(corner)).x for obj in objs for corner in obj.bound_box),
            min((obj.matrix_world @ mathutils.Vector(corner)).y for obj in objs for corner in obj.bound_box),
            min((obj.matrix_world @ mathutils.Vector(corner)).z for obj in objs for corner in obj.bound_box),
        )
    )
    maxs = mathutils.Vector(
        (
            max((obj.matrix_world @ mathutils.Vector(corner)).x for obj in objs for corner in obj.bound_box),
            max((obj.matrix_world @ mathutils.Vector(corner)).y for obj in objs for corner in obj.bound_box),
            max((obj.matrix_world @ mathutils.Vector(corner)).z for obj in objs for corner in obj.bound_box),
        )
    )
    return mins, maxs


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(4.0, -8.0, 8.0))
    light = bpy.context.object
    light.name = "asset_mill_measured_v2_area_light"
    light.data.energy = 560.0
    light.data.size = 6.0
    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((8.5, -12.0, 7.5)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.45
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
    if not INDEX_PATH.exists():
        compiler.main()
    clear_scene()
    index = load_json(INDEX_PATH)
    materials = make_materials()
    created: list[bpy.types.Object] = []
    cols = 5
    spacing_x = 3.4
    spacing_y = 3.9
    loaded_assets: list[dict[str, Any]] = []
    for asset_index, row in enumerate(index["assets"]):
        recipe = load_json(ROOT / row["recipe_path"])
        recipe["recipe_path"] = row["recipe_path"]
        loaded_assets.append(recipe)
        col = asset_index % cols
        grid_row = asset_index // cols
        created.extend(create_asset(recipe, materials, (col * spacing_x, grid_row * spacing_y, 0.0)))
    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    curve_count = sum(1 for obj in created if obj.type == "CURVE")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    asset_mesh_counts = {
        asset["asset_id"]: sum(1 for obj in created if obj.get("asset_id") == asset["asset_id"] and obj.type in {"MESH", "CURVE"})
        for asset in loaded_assets
    }
    report = {
        "schema": "asset_mill_measured_components_blender_report_v2",
        "source_index": str(INDEX_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "asset_count": len(loaded_assets),
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "empty_object_count": empty_count,
        "asset_mesh_counts": asset_mesh_counts,
        "every_mesh_exists": all(count > 0 for count in asset_mesh_counts.values()),
        "all_v2_assets_rendered": len(asset_mesh_counts) == int(index["asset_count"]) and all(count > 0 for count in asset_mesh_counts.values()),
        "socket_marker_count": sum(len(asset["sockets"]) for asset in loaded_assets),
        "rules": {
            "local_recipe_driven": True,
            "bridge_test_only": True,
            "web_search_used": False,
            "v1_catalog_left_untouched": True,
            "no_silent_scaling": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True,
            "no_historical_accuracy_claim": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"assets={len(loaded_assets)} mesh={mesh_count} curves={curve_count} empties={empty_count}")


if __name__ == "__main__":
    main()

