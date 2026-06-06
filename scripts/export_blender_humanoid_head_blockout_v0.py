#!/usr/bin/env python3
"""Blender adapter for compiled humanoid head blockout geometry.

The geometry recipe owns the facial parts, vertices, faces, materials, source
layers, and bevel widths. This adapter validates the recipe and builds a Blender
preview from it. It does not decide the face shape.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPE = ROOT / "data/characters/head_construction/humanoid_head_blockout_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_humanoid_head_blockout_v0")
EXPECTED_SCHEMA = "humanoid_head_geometry_v0"
CRITICAL_LAYERS = {"skull_envelope", "brow_eye_band", "nose_wedge", "chin_jaw_mass"}


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


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if not finite_number(value):
        fail(f"{field} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        fail(f"{field} must be >= {minimum}")
    return number


def require_vector(value: Any, field: str, length: int = 3) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    result = []
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")
        result.append(round(float(item), 6))
    return result


def require_hex_color(value: Any, field: str) -> str:
    text = require_string(value, field)
    if len(text) != 7 or not text.startswith("#"):
        fail(f"{field} must be #RRGGBB")
    try:
        int(text[1:], 16)
    except ValueError:
        fail(f"{field} must be #RRGGBB")
    return text


def validate_recipe(recipe: dict[str, Any], recipe_path: Path) -> dict[str, Any]:
    if recipe.get("schema") != EXPECTED_SCHEMA:
        fail(f"{recipe_path} schema must be {EXPECTED_SCHEMA}")
    asset_id = require_string(recipe.get("asset_id"), "asset_id")
    require_string(recipe.get("asset_family"), "asset_family")
    require_string(recipe.get("style"), "style")
    rules = require_object(recipe.get("rules"), "rules")
    for key in (
        "source_taxonomy_owns_design",
        "compiler_emits_vertices_faces",
        "blender_adapter_consumes_geometry",
        "blender_adapter_must_not_invent_facial_features",
        "largest_forms_first",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")

    materials = require_list(recipe.get("material_palette"), "material_palette")
    material_ids: set[str] = set()
    for index, material in enumerate(materials):
        row = require_object(material, f"material_palette[{index}]")
        material_id = require_string(row.get("material_id"), f"material_palette[{index}].material_id")
        if material_id in material_ids:
            fail(f"duplicate material_id {material_id}")
        material_ids.add(material_id)
        require_hex_color(row.get("color_hex"), f"{material_id}.color_hex")
        require_string(row.get("role"), f"{material_id}.role")

    layers = require_list(recipe.get("construction_layers"), "construction_layers")
    layer_ids: set[str] = set()
    previous_sequence = -1
    for index, layer in enumerate(layers):
        row = require_object(layer, f"construction_layers[{index}]")
        layer_id = require_string(row.get("layer_id"), f"construction_layers[{index}].layer_id")
        sequence = row.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= previous_sequence:
            fail(f"{layer_id}.sequence must be strictly increasing")
        previous_sequence = sequence
        layer_ids.add(layer_id)

    parts = require_list(recipe.get("parts"), "parts")
    part_ids: set[str] = set()
    layer_ids_used: set[str] = set()
    vertex_count = 0
    face_count = 0
    for index, part in enumerate(parts):
        row = require_object(part, f"parts[{index}]")
        part_id = require_string(row.get("part_id"), f"parts[{index}].part_id")
        if part_id in part_ids:
            fail(f"duplicate part_id {part_id}")
        part_ids.add(part_id)
        layer_id = require_string(row.get("layer_id"), f"{part_id}.layer_id")
        if layer_id not in layer_ids:
            fail(f"{part_id}.layer_id unknown: {layer_id}")
        layer_ids_used.add(layer_id)
        material_id = require_string(row.get("material_id"), f"{part_id}.material_id")
        if material_id not in material_ids:
            fail(f"{part_id}.material_id unknown: {material_id}")
        require_string(row.get("facial_part"), f"{part_id}.facial_part")
        for field in ("shape_terms", "operation_terms", "blender_tool_ids"):
            values = require_list(row.get(field), f"{part_id}.{field}")
            if not all(isinstance(value, str) and value for value in values):
                fail(f"{part_id}.{field} must contain non-empty strings")
        require_number(row.get("bevel_m", 0.0), f"{part_id}.bevel_m", minimum=0.0)
        shade = require_string(row.get("shade"), f"{part_id}.shade")
        if shade not in {"flat", "smooth"}:
            fail(f"{part_id}.shade must be flat or smooth")
        mesh = require_object(row.get("mesh"), f"{part_id}.mesh")
        if mesh.get("type") != "mesh_from_pydata":
            fail(f"{part_id}.mesh.type must be mesh_from_pydata")
        vertices = require_list(mesh.get("vertices_m"), f"{part_id}.mesh.vertices_m")
        faces = require_list(mesh.get("faces"), f"{part_id}.mesh.faces")
        if len(vertices) < 3 or not faces:
            fail(f"{part_id}.mesh must have at least three vertices and one face")
        for vertex_index, vertex in enumerate(vertices):
            require_vector(vertex, f"{part_id}.mesh.vertices_m[{vertex_index}]")
        for face_index, face in enumerate(faces):
            if not isinstance(face, list) or len(face) < 3:
                fail(f"{part_id}.mesh.faces[{face_index}] must contain at least three vertex indexes")
            for vertex_ref in face:
                if not isinstance(vertex_ref, int) or isinstance(vertex_ref, bool) or vertex_ref < 0 or vertex_ref >= len(vertices):
                    fail(f"{part_id}.mesh.faces[{face_index}] references an invalid vertex")
        vertex_count += len(vertices)
        face_count += len(faces)

    missing_critical = sorted(CRITICAL_LAYERS - layer_ids_used)
    if missing_critical:
        fail(f"parts missing critical construction layers: {missing_critical}")

    return {
        "asset_id": asset_id,
        "part_count": len(parts),
        "layer_count": len(layer_ids),
        "material_count": len(material_ids),
        "vertex_count": vertex_count,
        "face_count": face_count,
    }


def make_report(recipe_path: Path, recipe: dict[str, Any], validation: dict[str, Any], *, generated: bool, render: bool) -> dict[str, Any]:
    return {
        "schema": "humanoid_head_blockout_blender_report_v0",
        "adapter": "scripts/export_blender_humanoid_head_blockout_v0.py",
        "source_recipe": str(recipe_path),
        "recipe_schema": recipe["schema"],
        "asset_id": recipe["asset_id"],
        "asset_family": recipe["asset_family"],
        "style": recipe["style"],
        "part_count": validation["part_count"],
        "layer_count": validation["layer_count"],
        "material_count": validation["material_count"],
        "vertex_count": validation["vertex_count"],
        "face_count": validation["face_count"],
        "generated_outputs_created": generated,
        "render_requested": render,
        "rules": {
            "consumes_compiled_geometry": True,
            "imports_blender": generated,
            "executes_blender": generated,
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
        "head_parts": ensure_collection(bpy, "head_blockout_parts"),
        "guides": ensure_collection(bpy, "head_blockout_guides"),
    }
    materials = make_materials(bpy, recipe)
    objects = []
    for part in recipe["parts"]:
        obj = create_part_object(bpy, part, materials, collections["head_parts"])
        objects.append(obj)
    create_measurement_guides(bpy, mathutils, recipe, materials, collections["guides"])
    create_title_label(bpy, recipe, materials, collections["guides"])
    add_scene_context(bpy, mathutils)

    blend_path = out_root / "humanoid_head_blockout_v0.blend"
    report_path = json_report if json_report is not None else out_root / "humanoid_head_blockout_v0_report.json"
    report = make_report(recipe_path, recipe, validation, generated=True, render=render)
    report.update(
        {
            "blend_path": str(blend_path),
            "object_count": len(bpy.context.scene.objects),
            "mesh_object_count": len(objects),
        }
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if render:
        render_path = out_root / "humanoid_head_blockout_v0_workbench.png"
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS humanoid head blockout export: parts={len(objects)} out={out_root}")


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


def make_material(bpy: Any, name: str, color: tuple[float, float, float, float], roughness: float = 0.66) -> Any:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = roughness
    return material


def make_materials(bpy: Any, recipe: dict[str, Any]) -> dict[str, Any]:
    materials: dict[str, Any] = {}
    for row in recipe["material_palette"]:
        materials[row["material_id"]] = make_material(bpy, f"head_{row['material_id']}", hex_to_rgba(row["color_hex"]), 0.7)
    materials["outline"] = make_material(bpy, "head_outline_dark", (0.035, 0.04, 0.045, 1.0), 0.75)
    materials["label"] = make_material(bpy, "head_label_light", (0.86, 0.88, 0.9, 1.0), 0.8)
    return materials


def create_part_object(bpy: Any, part: dict[str, Any], materials: dict[str, Any], collection: Any) -> Any:
    mesh_data = part["mesh"]
    vertices = [tuple(vertex) for vertex in mesh_data["vertices_m"]]
    faces = [tuple(face) for face in mesh_data["faces"]]
    mesh = bpy.data.meshes.new(f"{part['part_id']}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(part["part_id"], mesh)
    obj.data.materials.append(materials[part["material_id"]])
    obj["layer_id"] = part["layer_id"]
    obj["facial_part"] = part["facial_part"]
    obj["shape_terms"] = ",".join(part["shape_terms"])
    obj["operation_terms"] = ",".join(part["operation_terms"])
    link_to_collection(obj, collection)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if part["shade"] == "smooth":
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()
    bevel_width = float(part.get("bevel_m", 0.0))
    if bevel_width > 0:
        bevel = obj.modifiers.new("source_bevel", "BEVEL")
        bevel.width = bevel_width
        bevel.segments = 1 if "chamfer" in part["shape_terms"] else 2
        bevel.affect = "EDGES"
        weighted = obj.modifiers.new("source_weighted_normals", "WEIGHTED_NORMAL")
        weighted.keep_sharp = True
    obj.select_set(False)
    return obj


def create_measurement_guides(bpy: Any, mathutils: Any, recipe: dict[str, Any], materials: dict[str, Any], collection: Any) -> None:
    derived = recipe["measurement_profile"]["derived_dimensions_m"]
    dimensions = recipe["measurement_profile"]["dimensions_m"]
    head_breadth = float(dimensions["head_breadth"])
    head_height = float(derived["head_height"])
    guide_y = 0.075
    create_curve_line(
        bpy,
        "guide_head_width",
        [(-head_breadth / 2.0, guide_y, head_height + 0.015), (head_breadth / 2.0, guide_y, head_height + 0.015)],
        materials["guide_blue"],
        collection,
        0.0012,
    )
    for z_name in ("brow_z", "eye_z", "subnasale_z", "mouth_z", "chin_z"):
        z = float(derived[z_name])
        create_curve_line(
            bpy,
            f"guide_{z_name}",
            [(-head_breadth * 0.62, guide_y, z), (head_breadth * 0.62, guide_y, z)],
            materials["guide_blue"],
            collection,
            0.00055,
        )


def create_curve_line(bpy: Any, name: str, points: list[tuple[float, float, float]], material: Any, collection: Any, bevel_depth: float) -> Any:
    curve = bpy.data.curves.new(f"{name}_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 0
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for index, p in enumerate(points):
        spline.points[index].co = (p[0], p[1], p[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    return obj


def create_title_label(bpy: Any, recipe: dict[str, Any], materials: dict[str, Any], collection: Any) -> None:
    bpy.ops.object.text_add(location=(-0.145, 0.08, 0.28), rotation=(math.radians(78), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = "label__humanoid_head_blockout_v0"
    obj.data.body = "HUMANOID HEAD BLOCKOUT v0"
    obj.data.align_x = "LEFT"
    obj.data.size = 0.01
    obj.data.align_y = "CENTER"
    obj.data.materials.append(materials["label"])
    obj["asset_id"] = recipe["asset_id"]
    link_to_collection(obj, collection)


def add_scene_context(bpy: Any, mathutils: Any) -> None:
    bpy.ops.object.light_add(type="AREA", location=(-0.35, -0.75, 0.62))
    key = bpy.context.object
    key.name = "key_area_light"
    key.data.energy = 520
    key.data.size = 0.5
    bpy.ops.object.camera_add(location=(0.0, -0.72, 0.13), rotation=(math.radians(90), 0.0, 0.0))
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    camera.name = "camera__front_low_compute_head"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.36
    camera.data.dof.use_dof = False

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1400
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.world = bpy.data.worlds.new("head_blockout_world") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world.color = (0.035, 0.038, 0.043)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE, help="Compiled humanoid head geometry recipe JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory for Blender files and reports")
    parser.add_argument("--json-report", type=Path, default=None, help="Optional report path")
    parser.add_argument("--validate-only", action="store_true", help="Validate recipe without importing Blender")
    parser.add_argument("--render", action="store_true", help="Render a workbench PNG after building the scene")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv if argv is None else ["script"] + argv
    script_argv = raw_argv[raw_argv.index("--") + 1 :] if "--" in raw_argv else raw_argv[1:]
    args = parse_args(script_argv)
    recipe = load_json_object(args.recipe)
    validation = validate_recipe(recipe, args.recipe)
    if args.validate_only:
        report_path = args.json_report or (args.out / "humanoid_head_blockout_v0_validate_report.json")
        report = make_report(args.recipe, recipe, validation, generated=False, render=False)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS humanoid head blockout geometry validation: "
            f"parts={validation['part_count']} vertices={validation['vertex_count']} faces={validation['face_count']}"
        )
        return 0
    run_blender_export(recipe, args.recipe, validation, args.out, args.render, args.json_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
