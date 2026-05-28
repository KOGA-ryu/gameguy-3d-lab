#!/usr/bin/env python3
"""Realize compiled architectural module graphs in Blender.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_architectural_module_proof_v0.py

This is a visual proof for the multi-face construction grammar. It consumes
compiled_architectural_module_v0 JSON and creates an octagonal floor, support
columns, wall bay prisms, and pointed arch ribs with shared connector points.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "goal" / "architecture" / "architectural_modules_v0" / "modules"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
DEFAULT_MODULE_ID = "octagonal_arch_room_v0"


def selected_module_path() -> Path:
    module_id = os.environ.get("ARCH_MODULE_ID", DEFAULT_MODULE_ID).strip() or DEFAULT_MODULE_ID
    path = MODULE_DIR / f"{module_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"compiled architectural module not found: {path}")
    return path


def output_paths(module_id: str) -> tuple[Path, Path, Path]:
    prefix = os.environ.get("ARCH_MODULE_OUTPUT_PREFIX", f"{module_id}_proof_v0").strip() or f"{module_id}_proof_v0"
    return (
        OUT_DIR / f"{prefix}.blend",
        OUT_DIR / f"{prefix}_workbench.png",
        OUT_DIR / f"{prefix}_report.json",
    )


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


def create_empty(name: str, custom_props: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.45
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def make_mesh_object(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    material: bpy.types.Material,
    parent: bpy.types.Object | None,
    custom_props: dict[str, Any],
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    if parent is not None:
        obj.parent = parent
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def regular_points(center: list[float], radius: float, count: int, z: float) -> list[tuple[float, float, float]]:
    cx, cy = float(center[0]), float(center[1])
    return [
        (
            cx + math.cos(math.tau * index / count + math.radians(22.5)) * radius,
            cy + math.sin(math.tau * index / count + math.radians(22.5)) * radius,
            z,
        )
        for index in range(count)
    ]


def make_prism(
    name: str,
    bottom: list[tuple[float, float, float]],
    top_z: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    custom_props: dict[str, Any],
) -> bpy.types.Object:
    count = len(bottom)
    vertices = list(bottom) + [(x, y, top_z) for x, y, _z in bottom]
    faces: list[tuple[int, ...]] = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    return make_mesh_object(name, vertices, faces, material, parent, custom_props)


def make_floor(module: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> bpy.types.Object:
    bottom = [(float(p["position"][0]), float(p["position"][1]), 0.0) for p in module["plan"]["vertices"]]
    return make_prism(
        f"{module['module_id']}.octagonal_floor_slab",
        bottom,
        float(module["measurements"]["floor_thickness"]),
        material,
        parent,
        {"mesh_role": "octagonal_floor_slab", "shape_ref": module["plan"]["shape_ref"]},
    )


def make_column_parts(column: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> list[bpy.types.Object]:
    center = column["center"]
    base_height = float(column["base_height"])
    cap_height = float(column["cap_height"])
    height = float(column["height"])
    shaft_bottom = base_height
    shaft_top = max(height - cap_height, shaft_bottom)
    objects = [
        make_prism(
            f"{column['column_id']}.base",
            regular_points(center, float(column["base_radius"]), 8, 0.0),
            base_height,
            materials["column_base"],
            parent,
            {"mesh_role": "column_base", "column_id": column["column_id"]},
        ),
        make_prism(
            f"{column['column_id']}.shaft",
            regular_points(center, float(column["radius"]), 8, shaft_bottom),
            shaft_top,
            materials["column"],
            parent,
            {"mesh_role": "column_shaft", "column_id": column["column_id"]},
        ),
        make_prism(
            f"{column['column_id']}.cap",
            regular_points(center, float(column["cap_radius"]), 8, shaft_top),
            height,
            materials["column_cap"],
            parent,
            {"mesh_role": "column_cap", "column_id": column["column_id"]},
        ),
    ]
    return objects


def make_wall_panel(panel: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> bpy.types.Object:
    c = panel["corners"]
    order = [
        "front_left_bottom",
        "front_right_bottom",
        "front_right_top",
        "front_left_top",
        "back_left_bottom",
        "back_right_bottom",
        "back_right_top",
        "back_left_top",
    ]
    vertices = [tuple(float(v) for v in c[key]) for key in order]
    faces = [
        (0, 1, 2, 3),
        (5, 4, 7, 6),
        (0, 4, 5, 1),
        (3, 2, 6, 7),
        (1, 5, 6, 2),
        (4, 0, 3, 7),
    ]
    return make_mesh_object(
        panel["wall_panel_id"],
        vertices,
        faces,
        material,
        parent,
        {"mesh_role": "quad_wall_panel", "bay_id": panel["bay_id"], "shape_ref": panel["shape_ref"]},
    )


def make_arch_curve(arch: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{arch['arch_id']}_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = float(arch["rib_radius"])
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    points = arch["curve_points"]
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points, strict=True):
        point.co = (float(coord[0]), float(coord[1]), float(coord[2]), 1.0)
    obj = bpy.data.objects.new(arch["arch_id"], curve)
    obj.data.materials.append(material)
    obj.parent = parent
    obj["mesh_role"] = "pointed_arch_rib_curve"
    obj["bend_law"] = arch["bend_law"]
    obj["span"] = arch["span"]
    obj["curve_radius"] = arch["curve_radius"]
    obj["apex_z"] = arch["apex_z"]
    bpy.context.collection.objects.link(obj)
    return obj


def make_connection_markers(module: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for column in module["columns"]:
        x, y, z = [float(v) for v in column["connectors"]["springline_cap"]]
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.075, location=(x, y, z))
        marker = bpy.context.object
        marker.name = f"{column['column_id']}.springline_marker"
        marker.data.materials.append(material)
        marker.parent = parent
        marker["mesh_role"] = "shared_endpoint_marker"
        marker["connector_type"] = "column_cap_arch_springline"
        objects.append(marker)
    return objects


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    if not objs:
        return mathutils.Vector((0, 0, 0)), mathutils.Vector((1, 1, 1))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mins = mathutils.Vector((1e9, 1e9, 1e9))
    maxs = mathutils.Vector((-1e9, -1e9, -1e9))
    for obj in objs:
        eval_obj = obj.evaluated_get(depsgraph)
        for corner in eval_obj.bound_box:
            world = eval_obj.matrix_world @ mathutils.Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)
    return mins, maxs


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.76, 0.77, 0.76)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -6.0, 10.0))
    light = bpy.context.object
    light.name = "architectural_module_area_light"
    light.data.energy = 700.0
    light.data.size = 8.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((8.5, -11.0, 7.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.22
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    module = load_json(selected_module_path())
    blend_path, render_path, report_path = output_paths(module["module_id"])
    materials = {
        "floor": make_material("mat_octagonal_floor", (0.42, 0.48, 0.43, 1.0)),
        "wall": make_material("mat_wall_panel", (0.62, 0.58, 0.48, 1.0)),
        "column": make_material("mat_column_shaft", (0.55, 0.53, 0.46, 1.0)),
        "column_base": make_material("mat_column_base", (0.43, 0.40, 0.34, 1.0)),
        "column_cap": make_material("mat_column_cap", (0.72, 0.64, 0.42, 1.0)),
        "arch": make_material("mat_pointed_arch_rib", (0.78, 0.66, 0.36, 1.0)),
        "marker": make_material("mat_shared_endpoint_marker", (0.96, 0.55, 0.16, 1.0)),
    }
    root = create_empty(
        module["module_id"],
        {
            "module_id": module["module_id"],
            "source_recipe": module["source_recipe"],
            "proof": "architectural_module_proof_v0",
        },
    )
    created: list[bpy.types.Object] = [root]
    created.append(make_floor(module, materials["floor"], root))
    for panel in module["wall_panels"]:
        created.append(make_wall_panel(panel, materials["wall"], root))
    for column in module["columns"]:
        created.extend(make_column_parts(column, materials, root))
    for arch in module["arch_bays"]:
        created.append(make_arch_curve(arch, materials["arch"], root))
    created.extend(make_connection_markers(module, materials["marker"], root))

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    curve_count = sum(1 for obj in created if obj.type == "CURVE")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    report = {
        "schema": "architectural_module_blender_proof_v0",
        "module_id": module["module_id"],
        "source_module": str(selected_module_path().relative_to(ROOT)),
        "blend_path": str(blend_path.relative_to(ROOT)),
        "render_path": str(render_path.relative_to(ROOT)),
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "empty_object_count": empty_count,
        "validation_summary": module["validation_summary"],
        "measurements": module["measurements"],
        "rules": {
            "proof_scene_only": True,
            "multi_face_geometry": True,
            "arch_springlines_match_column_caps": module["validation_summary"]["all_arch_springlines_match_column_caps"],
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True,
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {blend_path.relative_to(ROOT)}")
    print(f"wrote {render_path.relative_to(ROOT)}")
    print(f"wrote {report_path.relative_to(ROOT)}")
    print(f"objects_created={len(created)} mesh={mesh_count} curve={curve_count} empty={empty_count}")


if __name__ == "__main__":
    main()
