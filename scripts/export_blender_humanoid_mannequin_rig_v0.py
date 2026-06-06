#!/usr/bin/env python3
"""Blender adapter for the humanoid body mannequin rig recipe.

The recipe owns body regions, pivots, sockets, controls, and draw order. This
adapter consumes that source record and builds a Blender preview/rig scaffold.
It does not choose body parts or animation rules itself.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPE = ROOT / "data" / "characters" / "mannequin_rigs" / "humanoid_body_mannequin_rig_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_humanoid_body_mannequin_rig_v0")
EXPECTED_SCHEMA = "humanoid_body_mannequin_rig_recipe_v0"
EXPECTED_REGION_COUNT = 16


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_vector(value: Any, field: str, length: int = 3) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    result = []
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")
        result.append(round(float(item), 6))
    return result


def require_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if not finite_number(value):
        fail(f"{field} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        fail(f"{field} must be >= {minimum}")
    return number


def require_hex_color(value: Any, field: str) -> str:
    text = require_string(value, field)
    if len(text) != 7 or not text.startswith("#"):
        fail(f"{field} must be #RRGGBB")
    try:
        int(text[1:], 16)
    except ValueError:
        fail(f"{field} must be #RRGGBB")
    return text


def validate_shape(shape: dict[str, Any], field: str) -> None:
    shape_type = require_string(shape.get("type"), f"{field}.type")
    if shape_type == "ellipsoid":
        require_vector(shape.get("pivot_m"), f"{field}.pivot_m")
        require_vector(shape.get("center_m"), f"{field}.center_m")
        radii = require_vector(shape.get("radii_m"), f"{field}.radii_m")
        if any(radius <= 0 for radius in radii):
            fail(f"{field}.radii_m values must be positive")
    elif shape_type == "tapered_capsule":
        require_vector(shape.get("pivot_m"), f"{field}.pivot_m")
        require_vector(shape.get("start_m"), f"{field}.start_m")
        require_vector(shape.get("end_m"), f"{field}.end_m")
        for key in ("radius_start_m", "radius_end_m"):
            if not finite_number(shape.get(key)) or float(shape[key]) <= 0:
                fail(f"{field}.{key} must be a positive finite number")
    elif shape_type == "extruded_contour":
        require_string(shape.get("source_shape_family"), f"{field}.source_shape_family")
        require_vector(shape.get("pivot_m"), f"{field}.pivot_m")
        require_number(shape.get("depth_m"), f"{field}.depth_m", minimum=0.001)
        require_number(shape.get("bevel_m", 0.0), f"{field}.bevel_m", minimum=0.0)
        require_number(shape.get("outline_m", 0.0), f"{field}.outline_m", minimum=0.0)
        contour = require_list(shape.get("contour_xz_m"), f"{field}.contour_xz_m")
        if len(contour) < 3:
            fail(f"{field}.contour_xz_m must contain at least 3 points")
        for point_index, point in enumerate(contour):
            require_vector(point, f"{field}.contour_xz_m[{point_index}]", length=2)
    else:
        fail(f"{field}.type unsupported: {shape_type}")

    for key in ("segments", "rings"):
        if key in shape and (not isinstance(shape[key], int) or isinstance(shape[key], bool) or shape[key] < 4):
            fail(f"{field}.{key} must be an integer >= 4")


def validate_recipe(recipe: dict[str, Any], recipe_path: Path) -> dict[str, Any]:
    if recipe.get("schema") != EXPECTED_SCHEMA:
        fail(f"{recipe_path} schema must be {EXPECTED_SCHEMA}")
    asset_id = require_string(recipe.get("asset_id"), "asset_id")
    require_string(recipe.get("asset_family"), "asset_family")
    require_string(recipe.get("style"), "style")
    if recipe.get("origin") != "bottom_center":
        fail("origin must be bottom_center")
    if recipe.get("view") != "three_quarter_front":
        fail("view must be three_quarter_front")

    rules = require_object(recipe.get("rules"), "rules")
    for key in (
        "body_parts_are_rigid_segments",
        "segment_origins_are_pivots",
        "region_ids_drive_color_masks",
        "overlays_define_appearance",
        "blender_adapter_consumes_this_recipe",
        "blender_adapter_must_not_invent_regions",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")

    palette = require_list(recipe.get("region_palette"), "region_palette")
    regions = require_list(recipe.get("regions"), "regions")
    joints = require_list(recipe.get("joints"), "joints")
    sockets = require_list(recipe.get("sockets"), "sockets")
    controls = require_list(recipe.get("controls"), "controls")
    draw_order = [require_string(value, f"draw_order[{index}]") for index, value in enumerate(require_list(recipe.get("draw_order"), "draw_order"))]

    if len(palette) != EXPECTED_REGION_COUNT:
        fail(f"region_palette must contain {EXPECTED_REGION_COUNT} region IDs")
    if len(regions) != EXPECTED_REGION_COUNT:
        fail(f"regions must contain {EXPECTED_REGION_COUNT} rigid segments")

    palette_by_id: dict[int, dict[str, Any]] = {}
    for index, item in enumerate(palette):
        row = require_object(item, f"region_palette[{index}]")
        region_id = row.get("region_id")
        if not isinstance(region_id, int) or isinstance(region_id, bool) or region_id < 1:
            fail(f"region_palette[{index}].region_id must be a positive integer")
        if region_id in palette_by_id:
            fail(f"duplicate region_palette region_id {region_id}")
        require_string(row.get("name"), f"region_palette[{index}].name")
        require_hex_color(row.get("color_hex"), f"region_palette[{index}].color_hex")
        palette_by_id[region_id] = row
    expected_region_ids = set(range(1, EXPECTED_REGION_COUNT + 1))
    if set(palette_by_id) != expected_region_ids:
        fail(f"region_palette IDs must be 1..{EXPECTED_REGION_COUNT}")

    joint_ids: set[str] = set()
    joint_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(joints):
        joint = require_object(item, f"joints[{index}]")
        joint_id = require_string(joint.get("joint_id"), f"joints[{index}].joint_id")
        if joint_id in joint_ids:
            fail(f"duplicate joint_id {joint_id}")
        joint_ids.add(joint_id)
        joint_by_id[joint_id] = joint
        require_vector(joint.get("pivot_m"), f"{joint_id}.pivot_m")
        parent = joint.get("parent_joint")
        if parent is not None and not isinstance(parent, str):
            fail(f"{joint_id}.parent_joint must be null or string")
        require_string(joint.get("joint_type"), f"{joint_id}.joint_type")
    if "root" not in joint_ids:
        fail("joints must include root")
    for joint_id, joint in joint_by_id.items():
        parent = joint.get("parent_joint")
        if parent is not None and parent not in joint_ids:
            fail(f"{joint_id}.parent_joint references unknown joint {parent}")

    region_names: set[str] = set()
    region_ids: set[int] = set()
    draw_layers = set(draw_order)
    for index, item in enumerate(regions):
        region = require_object(item, f"regions[{index}]")
        region_id = region.get("region_id")
        if region_id not in palette_by_id:
            fail(f"regions[{index}].region_id has no palette row")
        if region_id in region_ids:
            fail(f"duplicate region_id {region_id}")
        region_ids.add(region_id)
        name = require_string(region.get("name"), f"regions[{index}].name")
        if name in region_names:
            fail(f"duplicate region name {name}")
        region_names.add(name)
        if palette_by_id[region_id]["name"] != name:
            fail(f"region {name} must match palette name for id {region_id}")
        pivot_joint = require_string(region.get("pivot_joint"), f"{name}.pivot_joint")
        if pivot_joint not in joint_ids:
            fail(f"{name}.pivot_joint references unknown joint {pivot_joint}")
        draw_layer = require_string(region.get("draw_layer"), f"{name}.draw_layer")
        if draw_layer not in draw_layers:
            fail(f"{name}.draw_layer must exist in draw_order")
        validate_shape(require_object(region.get("shape"), f"{name}.shape"), f"{name}.shape")

    for index, item in enumerate(sockets):
        socket = require_object(item, f"sockets[{index}]")
        require_string(socket.get("socket_id"), f"sockets[{index}].socket_id")
        joint_id = require_string(socket.get("joint_id"), f"sockets[{index}].joint_id")
        if joint_id not in joint_ids:
            fail(f"sockets[{index}].joint_id references unknown joint {joint_id}")
        require_vector(socket.get("position_m"), f"sockets[{index}].position_m")
        require_string(socket.get("role"), f"sockets[{index}].role")

    for index, item in enumerate(controls):
        control = require_object(item, f"controls[{index}]")
        require_string(control.get("control"), f"controls[{index}].control")
        require_string(control.get("type"), f"controls[{index}].type")
        require_vector(control.get("range"), f"controls[{index}].range", length=2)
        if not finite_number(control.get("default")):
            fail(f"controls[{index}].default must be a finite number")

    return {
        "asset_id": asset_id,
        "region_count": len(regions),
        "joint_count": len(joints),
        "socket_count": len(sockets),
        "control_count": len(controls),
        "draw_layer_count": len(draw_order),
        "pose_set_count": len(require_list(recipe.get("required_pose_sets"), "required_pose_sets")),
    }


def make_report(recipe_path: Path, recipe: dict[str, Any], validation: dict[str, Any], *, generated: bool, render: bool) -> dict[str, Any]:
    return {
        "schema": "humanoid_body_mannequin_rig_blender_report_v0",
        "adapter": "scripts/export_blender_humanoid_mannequin_rig_v0.py",
        "source_recipe": str(recipe_path),
        "recipe_schema": recipe["schema"],
        "asset_id": recipe["asset_id"],
        "asset_family": recipe["asset_family"],
        "style": recipe["style"],
        "origin": recipe["origin"],
        "view": recipe["view"],
        "region_count": validation["region_count"],
        "joint_count": validation["joint_count"],
        "socket_count": validation["socket_count"],
        "control_count": validation["control_count"],
        "draw_layer_count": validation["draw_layer_count"],
        "pose_set_count": validation["pose_set_count"],
        "generated_outputs_created": generated,
        "render_requested": render,
        "rules": {
            "consumes_source_recipe": True,
            "imports_blender": generated,
            "executes_blender": generated,
            "body_parts_are_rigid_segments": True,
            "segment_origins_are_pivots": True,
            "region_ids_drive_color_masks": True,
            "overlays_define_appearance": True,
            "source_design_logic_in_blender_adapter": False,
        },
    }


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    value = hex_color.lstrip("#")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
        alpha,
    )


def run_blender_export(recipe: dict[str, Any], recipe_path: Path, validation: dict[str, Any], out_root: Path, render: bool, json_report: Path | None) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Blender export requires Blender Python. Use --validate-only with normal Python.")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collections = {
        "segments": ensure_collection(bpy, "rig_body_segments"),
        "joints": ensure_collection(bpy, "rig_pivot_joints"),
        "sockets": ensure_collection(bpy, "rig_sockets"),
        "guides": ensure_collection(bpy, "rig_guides_labels"),
        "controls": ensure_collection(bpy, "rig_controls"),
    }

    materials = make_materials(bpy, recipe)
    joint_empties = create_joint_empties(bpy, mathutils, recipe, materials, collections["joints"])
    segment_objects = create_segments(bpy, mathutils, recipe, materials, joint_empties, collections["segments"])
    create_joint_markers_and_links(bpy, mathutils, recipe, materials, joint_empties, collections["joints"])
    create_socket_markers(bpy, recipe, materials, joint_empties, collections["sockets"])
    create_control_empties(bpy, recipe, materials, joint_empties, collections["controls"])
    armature = create_armature(bpy, mathutils, recipe, collections["guides"])
    create_legend_and_baseline(bpy, recipe, materials, collections["guides"])
    add_scene_context(bpy, mathutils, recipe)

    blend_path = out_root / "humanoid_body_mannequin_rig_v0.blend"
    report_path = json_report if json_report is not None else out_root / "humanoid_body_mannequin_rig_v0_report.json"
    report = make_report(recipe_path, recipe, validation, generated=True, render=render)
    report.update(
        {
            "blend_path": str(blend_path),
            "object_count": len(bpy.context.scene.objects),
            "segment_object_count": len(segment_objects),
            "armature": armature.name if armature else "",
        }
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if render:
        render_path = out_root / "humanoid_body_mannequin_rig_v0_workbench.png"
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS humanoid mannequin rig export: segments={len(segment_objects)} out={out_root}")


def ensure_collection(bpy: Any, name: str) -> Any:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def link_to_collection(obj: Any, collection: Any) -> None:
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    for source in list(obj.users_collection):
        if source != collection:
            source.objects.unlink(obj)


def make_material(bpy: Any, name: str, color: tuple[float, float, float, float], roughness: float = 0.65) -> Any:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = roughness
    return material


def make_materials(bpy: Any, recipe: dict[str, Any]) -> dict[str, Any]:
    materials: dict[str, Any] = {
        "pivot": make_material(bpy, "rig_pivot_red", (0.95, 0.08, 0.12, 1.0), 0.5),
        "socket": make_material(bpy, "rig_socket_blue", (0.05, 0.38, 0.95, 1.0), 0.45),
        "bone": make_material(bpy, "rig_bone_line", (0.55, 0.12, 0.10, 1.0), 0.6),
        "control": make_material(bpy, "rig_control_gold", (1.0, 0.72, 0.18, 1.0), 0.55),
        "outline": make_material(bpy, "rig_region_outline", (0.02, 0.025, 0.03, 1.0), 0.7),
        "baseline": make_material(bpy, "rig_baseline_shadow", (0.14, 0.14, 0.16, 0.35), 0.8),
        "label": make_material(bpy, "rig_label_light", (0.88, 0.90, 0.94, 1.0), 0.8),
    }
    for row in recipe["region_palette"]:
        materials[row["name"]] = make_material(
            bpy,
            f"region_{row['region_id']:02d}_{row['name']}",
            hex_to_rgba(row["color_hex"]),
            0.72,
        )
    return materials


def vector_from(value: list[float], mathutils: Any) -> Any:
    return mathutils.Vector((float(value[0]), float(value[1]), float(value[2])))


def create_mesh_object(
    bpy: Any,
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    location: tuple[float, float, float],
    material: Any,
    collection: Any,
    *,
    smooth: bool = True,
) -> Any:
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    if smooth:
        try:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.shade_smooth()
            obj.select_set(False)
        except Exception:
            pass
    return obj


def ellipsoid_mesh(shape: dict[str, Any], mathutils: Any) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]], tuple[float, float, float]]:
    pivot = vector_from(shape["pivot_m"], mathutils)
    center = vector_from(shape["center_m"], mathutils)
    radii = vector_from(shape["radii_m"], mathutils)
    segments = max(8, int(shape.get("segments", 12)))
    rings = max(5, int(shape.get("rings", 7)))
    local_center = center - pivot
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    vertices.append(tuple(local_center + mathutils.Vector((0.0, 0.0, radii.z))))
    ring_indexes: list[list[int]] = []
    for ring in range(1, rings):
        phi = math.pi * ring / rings
        row = []
        for segment in range(segments):
            theta = math.tau * segment / segments
            point = mathutils.Vector(
                (
                    radii.x * math.sin(phi) * math.cos(theta),
                    radii.y * math.sin(phi) * math.sin(theta),
                    radii.z * math.cos(phi),
                )
            )
            row.append(len(vertices))
            vertices.append(tuple(local_center + point))
        ring_indexes.append(row)
    bottom_index = len(vertices)
    vertices.append(tuple(local_center + mathutils.Vector((0.0, 0.0, -radii.z))))

    first = ring_indexes[0]
    for segment in range(segments):
        faces.append((0, first[(segment + 1) % segments], first[segment]))
    for row_index in range(len(ring_indexes) - 1):
        upper = ring_indexes[row_index]
        lower = ring_indexes[row_index + 1]
        for segment in range(segments):
            faces.append((upper[segment], upper[(segment + 1) % segments], lower[(segment + 1) % segments], lower[segment]))
    last = ring_indexes[-1]
    for segment in range(segments):
        faces.append((last[segment], last[(segment + 1) % segments], bottom_index))
    return vertices, faces, tuple(pivot)


def capsule_mesh(shape: dict[str, Any], mathutils: Any) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]], tuple[float, float, float]]:
    pivot = vector_from(shape["pivot_m"], mathutils)
    start = vector_from(shape["start_m"], mathutils)
    end = vector_from(shape["end_m"], mathutils)
    axis = end - start
    length = axis.length
    if length <= 1e-6:
        fail("capsule start/end length must be positive")
    direction = axis.normalized()
    ref = mathutils.Vector((0.0, 0.0, 1.0))
    if abs(direction.dot(ref)) > 0.92:
        ref = mathutils.Vector((1.0, 0.0, 0.0))
    normal = direction.cross(ref).normalized()
    binormal = direction.cross(normal).normalized()
    segments = max(8, int(shape.get("segments", 12)))
    rings = max(5, int(shape.get("rings", 7)))
    radius_start = float(shape["radius_start_m"])
    radius_end = float(shape["radius_end_m"])

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    start_cap = len(vertices)
    vertices.append(tuple(start - pivot - direction * radius_start * 0.25))
    ring_indexes: list[list[int]] = []
    for ring in range(rings + 1):
        t = ring / rings
        center = start + axis * t
        radius = radius_start + (radius_end - radius_start) * t
        cap_factor = 0.68 + 0.32 * math.sin(math.pi * t)
        row = []
        for segment in range(segments):
            theta = math.tau * segment / segments
            radial = normal * math.cos(theta) + binormal * math.sin(theta)
            row.append(len(vertices))
            vertices.append(tuple(center - pivot + radial * radius * cap_factor))
        ring_indexes.append(row)
    end_cap = len(vertices)
    vertices.append(tuple(end - pivot + direction * radius_end * 0.25))

    first = ring_indexes[0]
    for segment in range(segments):
        faces.append((start_cap, first[segment], first[(segment + 1) % segments]))
    for row_index in range(len(ring_indexes) - 1):
        upper = ring_indexes[row_index]
        lower = ring_indexes[row_index + 1]
        for segment in range(segments):
            faces.append((upper[segment], upper[(segment + 1) % segments], lower[(segment + 1) % segments], lower[segment]))
    last = ring_indexes[-1]
    for segment in range(segments):
        faces.append((last[segment], end_cap, last[(segment + 1) % segments]))
    return vertices, faces, tuple(pivot)


def extruded_contour_mesh(shape: dict[str, Any], mathutils: Any) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]], tuple[float, float, float]]:
    pivot = vector_from(shape["pivot_m"], mathutils)
    depth = float(shape["depth_m"])
    half_depth = depth / 2.0
    contour = [(float(point[0]), float(point[1])) for point in shape["contour_xz_m"]]
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    for x, z in contour:
        vertices.append((x - pivot.x, -half_depth, z - pivot.z))
    for x, z in contour:
        vertices.append((x - pivot.x, half_depth, z - pivot.z))

    count = len(contour)
    faces.append(tuple(range(count)))
    faces.append(tuple(range((count * 2) - 1, count - 1, -1)))
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, next_index + count, index + count))
    return vertices, faces, tuple(pivot)


def create_contour_outline(
    bpy: Any,
    shape: dict[str, Any],
    name: str,
    material: Any,
    collection: Any,
    mathutils: Any,
) -> Any | None:
    outline = float(shape.get("outline_m", 0.0))
    if outline <= 0:
        return None
    pivot = vector_from(shape["pivot_m"], mathutils)
    half_depth = float(shape["depth_m"]) / 2.0
    curve = bpy.data.curves.new(f"{name}_outline_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = outline
    curve.bevel_resolution = 0
    spline = curve.splines.new("POLY")
    contour = [(float(point[0]), float(point[1])) for point in shape["contour_xz_m"]]
    spline.points.add(len(contour))
    for index, (x, z) in enumerate(contour + [contour[0]]):
        spline.points[index].co = (x - pivot.x, -half_depth - outline, z - pivot.z, 1.0)
    obj = bpy.data.objects.new(f"{name}__outline", curve)
    obj.location = tuple(pivot)
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    return obj


def create_joint_empties(bpy: Any, mathutils: Any, recipe: dict[str, Any], materials: dict[str, Any], collection: Any) -> dict[str, Any]:
    created: dict[str, Any] = {}
    joint_rows = {joint["joint_id"]: joint for joint in recipe["joints"]}
    for joint in recipe["joints"]:
        loc = tuple(vector_from(joint["pivot_m"], mathutils))
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=loc)
        obj = bpy.context.object
        obj.name = f"pivot__{joint['joint_id']}"
        obj.empty_display_size = 0.045
        obj["joint_id"] = joint["joint_id"]
        obj["joint_type"] = joint["joint_type"]
        if joint.get("control"):
            obj["control"] = joint["control"]
        if joint.get("range_deg"):
            obj["range_deg"] = joint["range_deg"]
        link_to_collection(obj, collection)
        created[joint["joint_id"]] = obj
    for joint in recipe["joints"]:
        parent_id = joint.get("parent_joint")
        if parent_id and parent_id in created:
            child = created[joint["joint_id"]]
            parent = created[parent_id]
            child.parent = parent
            child.matrix_parent_inverse = parent.matrix_world.inverted()
    return created


def create_segments(bpy: Any, mathutils: Any, recipe: dict[str, Any], materials: dict[str, Any], joint_empties: dict[str, Any], collection: Any) -> list[Any]:
    objects = []
    for region in recipe["regions"]:
        shape = region["shape"]
        smooth = True
        outline = None
        if shape["type"] == "ellipsoid":
            vertices, faces, location = ellipsoid_mesh(shape, mathutils)
        elif shape["type"] == "tapered_capsule":
            vertices, faces, location = capsule_mesh(shape, mathutils)
        else:
            vertices, faces, location = extruded_contour_mesh(shape, mathutils)
            smooth = False
        name = f"region_{region['region_id']:02d}__{region['name']}"
        obj = create_mesh_object(bpy, name, vertices, faces, location, materials[region["name"]], collection, smooth=smooth)
        obj["asset_id"] = recipe["asset_id"]
        obj["region_id"] = region["region_id"]
        obj["region_name"] = region["name"]
        obj["pivot_joint"] = region["pivot_joint"]
        obj["draw_layer"] = region["draw_layer"]
        if "source_shape_family" in shape:
            obj["source_shape_family"] = shape["source_shape_family"]
        if "symmetry_role" in shape:
            obj["symmetry_role"] = shape["symmetry_role"]
        if shape["type"] == "extruded_contour":
            bevel_width = float(shape.get("bevel_m", 0.0))
            if bevel_width > 0:
                bevel = obj.modifiers.new("source_contour_bevel", "BEVEL")
                bevel.width = bevel_width
                bevel.segments = 1
                bevel.affect = "EDGES"
                normal = obj.modifiers.new("source_contour_weighted_normals", "WEIGHTED_NORMAL")
                normal.keep_sharp = True
            outline = create_contour_outline(bpy, shape, name, materials["outline"], collection, mathutils)
            if outline is not None:
                outline["region_id"] = region["region_id"]
                outline["region_name"] = region["name"]
        parent = joint_empties[region["pivot_joint"]]
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
        if outline is not None:
            outline.parent = parent
            outline.matrix_parent_inverse = parent.matrix_world.inverted()
        objects.append(obj)
    return objects


def create_marker_sphere(bpy: Any, location: tuple[float, float, float], radius: float, material: Any, name: str, collection: Any) -> Any:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    return obj


def create_curve_line(bpy: Any, name: str, start: Any, end: Any, material: Any, collection: Any, bevel_depth: float = 0.006) -> Any:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = bevel_depth
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (start.x, start.y, start.z, 1.0)
    spline.points[1].co = (end.x, end.y, end.z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    return obj


def create_joint_markers_and_links(bpy: Any, mathutils: Any, recipe: dict[str, Any], materials: dict[str, Any], joint_empties: dict[str, Any], collection: Any) -> None:
    joint_rows = {joint["joint_id"]: joint for joint in recipe["joints"]}
    for joint in recipe["joints"]:
        loc = vector_from(joint["pivot_m"], mathutils)
        marker = create_marker_sphere(bpy, tuple(loc), 0.014, materials["pivot"], f"pivot_marker__{joint['joint_id']}", collection)
        marker["joint_id"] = joint["joint_id"]
        parent_id = joint.get("parent_joint")
        if parent_id and parent_id in joint_rows:
            parent_loc = vector_from(joint_rows[parent_id]["pivot_m"], mathutils)
            line = create_curve_line(bpy, f"bone_link__{parent_id}__{joint['joint_id']}", parent_loc, loc, materials["bone"], collection, bevel_depth=0.0035)
            line["parent_joint"] = parent_id
            line["child_joint"] = joint["joint_id"]


def create_socket_markers(bpy: Any, recipe: dict[str, Any], materials: dict[str, Any], joint_empties: dict[str, Any], collection: Any) -> None:
    for socket in recipe["sockets"]:
        marker = create_marker_sphere(bpy, tuple(socket["position_m"]), 0.018, materials["socket"], f"socket__{socket['socket_id']}", collection)
        marker["socket_id"] = socket["socket_id"]
        marker["role"] = socket["role"]
        marker["joint_id"] = socket["joint_id"]
        parent = joint_empties[socket["joint_id"]]
        marker.parent = parent
        marker.matrix_parent_inverse = parent.matrix_world.inverted()


def create_control_empties(bpy: Any, recipe: dict[str, Any], materials: dict[str, Any], joint_empties: dict[str, Any], collection: Any) -> None:
    control_to_joint = {
        joint.get("control"): joint["joint_id"]
        for joint in recipe["joints"]
        if isinstance(joint.get("control"), str)
    }
    for control in recipe["controls"]:
        joint_id = control_to_joint.get(control["control"], "root")
        parent = joint_empties.get(joint_id, joint_empties["root"])
        bpy.ops.object.empty_add(type="CIRCLE", location=parent.matrix_world.translation)
        obj = bpy.context.object
        obj.name = f"CTRL__{control['control']}"
        obj.empty_display_size = 0.07
        obj["control"] = control["control"]
        obj["type"] = control["type"]
        obj["range"] = control["range"]
        obj["default"] = control["default"]
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
        link_to_collection(obj, collection)


def create_armature(bpy: Any, mathutils: Any, recipe: dict[str, Any], collection: Any) -> Any:
    joint_rows = {joint["joint_id"]: joint for joint in recipe["joints"]}
    bpy.ops.object.armature_add(enter_editmode=True, location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = "armature__humanoid_body_mannequin_rig_v0"
    armature.show_in_front = True
    armature.data.name = "humanoid_body_mannequin_armature"
    edit_bones = armature.data.edit_bones
    if "Bone" in edit_bones:
        edit_bones.remove(edit_bones["Bone"])
    created = {}
    for joint in recipe["joints"]:
        parent_id = joint.get("parent_joint")
        if not parent_id or parent_id not in joint_rows:
            continue
        parent_loc = vector_from(joint_rows[parent_id]["pivot_m"], mathutils)
        child_loc = vector_from(joint["pivot_m"], mathutils)
        if (child_loc - parent_loc).length <= 1e-5:
            child_loc = parent_loc + mathutils.Vector((0.0, 0.0, 0.05))
        bone = edit_bones.new(f"bone__{joint['joint_id']}")
        bone.head = parent_loc
        bone.tail = child_loc
        if parent_id in created:
            bone.parent = created[parent_id]
            bone.use_connect = False
        created[joint["joint_id"]] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    link_to_collection(armature, collection)
    return armature


def add_text_label(bpy: Any, text: str, location: tuple[float, float, float], size: float, material: Any, collection: Any) -> Any:
    bpy.ops.object.text_add(location=location, rotation=(math.radians(68), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = "label__" + text.lower().replace(" ", "_").replace("/", "_")
    obj.data.body = text
    obj.data.align_x = "LEFT"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    return obj


def create_legend_and_baseline(bpy: Any, recipe: dict[str, Any], materials: dict[str, Any], collection: Any) -> None:
    # Ground/baseline shadow.
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.01, -0.012))
    base = bpy.context.object
    base.name = "origin_baseline__bottom_center"
    base.scale = (0.72, 0.18, 0.01)
    base.data.materials.append(materials["baseline"])
    link_to_collection(base, collection)

    add_text_label(bpy, "HUMANOID BODY MANNEQUIN RIG v0", (-0.78, -0.65, 1.92), 0.055, materials["label"], collection)
    add_text_label(bpy, "Rigid segments + pivots + sockets", (-0.78, -0.65, 1.84), 0.032, materials["label"], collection)

    x = 0.78
    y = -0.28
    z = 1.72
    add_text_label(bpy, "Region ID map", (x, y, z + 0.10), 0.035, materials["label"], collection)
    for index, row in enumerate(recipe["region_palette"]):
        z_row = z - index * 0.055
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z_row))
        chip = bpy.context.object
        chip.name = f"legend_chip__{row['region_id']:02d}_{row['name']}"
        chip.scale = (0.025, 0.012, 0.018)
        chip.data.materials.append(materials[row["name"]])
        link_to_collection(chip, collection)
        add_text_label(bpy, f"{row['region_id']:02d} {row['name']}", (x + 0.045, y, z_row), 0.024, materials["label"], collection)


def add_scene_context(bpy: Any, mathutils: Any, recipe: dict[str, Any]) -> None:
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1100
    bpy.ops.object.light_add(type="AREA", location=(0.0, -3.0, 3.0))
    light = bpy.context.object
    light.name = "mannequin_rig_area_light"
    light.data.energy = 450
    light.data.size = 4.0
    bpy.ops.object.camera_add(location=(0.0, -4.5, 0.95))
    camera = bpy.context.object
    target = mathutils.Vector((0.0, -0.03, 0.95))
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.0
    bpy.context.scene.camera = camera

    bpy.context.scene["asset_id"] = recipe["asset_id"]
    bpy.context.scene["origin"] = recipe["origin"]
    bpy.context.scene["view"] = recipe["view"]
    bpy.context.scene["working_size_px"] = recipe["working_size_px"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = sys.argv[1:] if argv is None else argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Export the humanoid body mannequin rig v0 Blender scaffold.")
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    recipe_path = args.recipe if args.recipe.is_absolute() else ROOT / args.recipe
    recipe = load_json_object(recipe_path)
    validation = validate_recipe(recipe, recipe_path)
    report = make_report(recipe_path, recipe, validation, generated=False, render=args.render)

    if args.validate_only:
        if args.json_report:
            report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS humanoid mannequin rig recipe validation: "
            f"regions={validation['region_count']} joints={validation['joint_count']} sockets={validation['socket_count']}"
        )
        return 0

    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    report_path = None
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
    run_blender_export(recipe, recipe_path, validation, out_root, args.render, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
