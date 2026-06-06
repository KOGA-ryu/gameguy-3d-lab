#!/usr/bin/env python3
"""Create a Blender scene for the low-poly character mannequin.

Normal Python can validate the source recipe. Blender Python builds the scene:
named mesh parts, OBJ/MTL sidecar export, reference sheet plane, camera,
lighting, and a starter armature for rig prep.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import export_low_poly_character_mannequin_v0 as obj_exporter


DEFAULT_RECIPE = obj_exporter.DEFAULT_RECIPE
DEFAULT_OUT = Path("/tmp/gameguy_low_poly_character_mannequin_blender_v0")
DEFAULT_BLENDER_BIN = Path("/Applications/Blender.app/Contents/MacOS/Blender")


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def make_report(
    recipe: dict[str, Any],
    recipe_path: Path,
    objects: list[obj_exporter.MeshObject],
    *,
    generated: bool,
    out_root: Path | None,
    render: bool,
) -> dict[str, Any]:
    source_reference = obj_exporter.require_object(
        recipe.get("source_reference"),
        "source_reference",
    )
    reference_path = ""
    source_image = source_reference.get("turnaround_sheet")
    if isinstance(source_image, str) and source_image:
        reference_path = str(ROOT / source_image)

    report: dict[str, Any] = {
        "schema": "low_poly_character_mannequin_blender_scene_report_v0",
        "adapter": "scripts/export_blender_low_poly_character_mannequin_v0.py",
        "source_recipe": str(recipe_path),
        "recipe_schema": recipe["schema"],
        "asset_id": recipe["asset_id"],
        "asset_family": recipe["asset_family"],
        "style": recipe["style"],
        "part_count": len(objects),
        "object_count": len(objects),
        "vertex_count": sum(len(obj.vertices) for obj in objects),
        "face_count": sum(len(obj.faces) for obj in objects),
        "reference_image": reference_path,
        "reference_image_exists": bool(reference_path and Path(reference_path).exists()),
        "armature_bone_count": len(starter_bones()),
        "beveled_part_count": count_beveled_parts(recipe),
        "weighted_normal_part_count": count_weighted_normal_parts(recipe),
        "blender_tool_passes": recipe.get("blender_tool_passes", {}),
        "generated_outputs_created": generated,
        "render_requested": render,
        "rules": {
            "consumes_source_recipe": True,
            "imports_blender": generated,
            "executes_blender": generated,
            "writes_obj_mtl_sidecars": generated,
            "creates_reference_sheet_plane": generated,
            "creates_starter_armature": generated,
            "applies_bevel_modifiers": generated,
            "applies_weighted_normals": generated,
            "source_design_logic_in_blender_adapter": False,
        },
    }
    if out_root is not None:
        report.update(
            {
                "out_root": str(out_root),
                "blend_path": str(out_root / f"{recipe['asset_id']}.blend"),
                "obj_path": str(out_root / f"{recipe['asset_id']}.obj"),
                "mtl_path": str(out_root / f"{recipe['asset_id']}.mtl"),
            }
        )
        if render:
            report["render_path"] = str(out_root / f"{recipe['asset_id']}_front_workbench.png")
            report["side_render_path"] = str(out_root / f"{recipe['asset_id']}_side_workbench.png")
    return report


def count_beveled_parts(recipe: dict[str, Any]) -> int:
    return sum(1 for part in recipe["parts"] if float(part.get("bevel_m", 0.0)) > 0.0)


def count_weighted_normal_parts(recipe: dict[str, Any]) -> int:
    return sum(1 for part in recipe["parts"] if part.get("weighted_normals") is True)


def starter_bones() -> list[dict[str, Any]]:
    def bone(
        name: str,
        parent: str | None,
        head: tuple[float, float, float],
        tail: tuple[float, float, float],
    ) -> dict[str, Any]:
        return {"name": name, "parent": parent, "head": head, "tail": tail}

    return [
        bone("root", None, (0.0, 0.0, 0.02), (0.0, 0.0, 0.76)),
        bone("spine", "root", (0.0, 0.0, 0.76), (0.0, 0.0, 1.25)),
        bone("neck_head", "spine", (0.0, 0.0, 1.25), (0.0, 0.0, 1.78)),
        bone("upper_arm_L", "spine", (-0.27, 0.0, 1.22), (-0.42, 0.0, 0.89)),
        bone("lower_arm_L", "upper_arm_L", (-0.42, 0.0, 0.89), (-0.51, 0.0, 0.54)),
        bone("upper_arm_R", "spine", (0.27, 0.0, 1.22), (0.42, 0.0, 0.89)),
        bone("lower_arm_R", "upper_arm_R", (0.42, 0.0, 0.89), (0.51, 0.0, 0.54)),
        bone("upper_leg_L", "root", (-0.11, 0.0, 0.74), (-0.15, 0.0, 0.34)),
        bone("lower_leg_L", "upper_leg_L", (-0.15, 0.0, 0.34), (-0.17, 0.0, 0.04)),
        bone("upper_leg_R", "root", (0.11, 0.0, 0.74), (0.15, 0.0, 0.34)),
        bone("lower_leg_R", "upper_leg_R", (0.15, 0.0, 0.34), (0.17, 0.0, 0.04)),
    ]


def run_blender_export(
    recipe: dict[str, Any],
    recipe_path: Path,
    objects: list[obj_exporter.MeshObject],
    out_root: Path,
    render: bool,
    json_report: Path | None,
) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail(
            "Blender scene export requires Blender Python. "
            "Use --validate-only with normal Python."
        )

    out_root.mkdir(parents=True, exist_ok=True)
    obj_path = out_root / f"{recipe['asset_id']}.obj"
    mtl_path = out_root / f"{recipe['asset_id']}.mtl"
    obj_exporter.write_mtl(recipe, mtl_path)
    obj_exporter.write_obj(recipe, objects, obj_path, mtl_path)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collections = {
        "parts": ensure_collection(bpy, "low_poly_mannequin_parts"),
        "reference": ensure_collection(bpy, "low_poly_reference_sheet"),
        "rig": ensure_collection(bpy, "starter_armature"),
        "guides": ensure_collection(bpy, "scene_guides"),
    }
    materials = make_materials(bpy, recipe)
    create_mesh_parts(bpy, recipe, objects, materials, collections["parts"])
    create_reference_sheet(bpy, recipe, materials, collections["reference"])
    armature = create_starter_armature(bpy, mathutils, collections["rig"])
    create_guides(bpy, materials, collections["guides"])
    add_scene_context(bpy, mathutils, recipe)

    blend_path = out_root / f"{recipe['asset_id']}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    report = make_report(
        recipe,
        recipe_path,
        objects,
        generated=True,
        out_root=out_root,
        render=render,
    )
    report["armature"] = armature.name
    report["scene_object_count"] = len(bpy.context.scene.objects)
    if render:
        front_render_path = out_root / f"{recipe['asset_id']}_front_workbench.png"
        side_render_path = out_root / f"{recipe['asset_id']}_side_workbench.png"
        render_camera_view(bpy, "camera__front_view", front_render_path)
        render_camera_view(bpy, "camera__side_view", side_render_path)
        report["render_path"] = str(front_render_path)
        report["side_render_path"] = str(side_render_path)

    if json_report is not None:
        report_path = json_report
    else:
        report_path = out_root / f"{recipe['asset_id']}_blender_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS low-poly mannequin Blender scene export: "
        f"objects={len(objects)} bones={report['armature_bone_count']} out={out_root}"
    )


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


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    r, g, b = obj_exporter.hex_to_rgb(hex_color)
    return (r, g, b, alpha)


def make_material(bpy: Any, name: str, color: tuple[float, float, float, float]) -> Any:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = 0.72
    return material


def make_materials(bpy: Any, recipe: dict[str, Any]) -> dict[str, Any]:
    materials = {
        row["name"]: make_material(bpy, row["name"], hex_to_rgba(row["color_hex"]))
        for row in recipe["materials"]
    }
    materials["guide_line"] = make_material(bpy, "guide_line", (0.16, 0.18, 0.20, 1.0))
    materials["reference_back"] = make_material(bpy, "reference_back", (1.0, 1.0, 1.0, 1.0))
    return materials


def part_origin(part: dict[str, Any], mesh: obj_exporter.MeshObject) -> tuple[float, float, float]:
    if part["primitive"] == "capsule":
        return tuple(obj_exporter.require_vector(part.get("start_m"), f"{part['name']}.start_m"))
    if "center_m" in part:
        return tuple(obj_exporter.require_vector(part.get("center_m"), f"{part['name']}.center_m"))
    count = len(mesh.vertices)
    return tuple(sum(vertex[index] for vertex in mesh.vertices) / count for index in range(3))


def create_mesh_parts(
    bpy: Any,
    recipe: dict[str, Any],
    objects: list[obj_exporter.MeshObject],
    materials: dict[str, Any],
    collection: Any,
) -> None:
    parts_by_name = {part["name"]: part for part in recipe["parts"]}
    for mesh_object in objects:
        part = parts_by_name[mesh_object.name]
        origin = part_origin(part, mesh_object)
        local_vertices = [
            (
                vertex[0] - origin[0],
                vertex[1] - origin[1],
                vertex[2] - origin[2],
            )
            for vertex in mesh_object.vertices
        ]
        mesh = bpy.data.meshes.new(f"{mesh_object.name}_mesh")
        mesh.from_pydata(local_vertices, [], mesh_object.faces)
        mesh.update()
        obj = bpy.data.objects.new(mesh_object.name, mesh)
        obj.location = origin
        obj.data.materials.append(materials[mesh_object.material])
        obj["asset_id"] = recipe["asset_id"]
        obj["part_name"] = mesh_object.name
        obj["part_material"] = mesh_object.material
        obj["rig_note"] = "Separate rigid part; parent to nearest bone after proportion review."
        apply_blender_tool_hints(obj, part)
        link_to_collection(obj, collection)


def apply_blender_tool_hints(obj: Any, part: dict[str, Any]) -> None:
    bevel_width = float(part.get("bevel_m", 0.0))
    if bevel_width > 0:
        bevel = obj.modifiers.new("recipe_bevel_modifier", "BEVEL")
        bevel.width = bevel_width
        bevel.segments = 1
        bevel.affect = "EDGES"
        obj["bevel_m"] = bevel_width
    if part.get("weighted_normals") is True:
        normal = obj.modifiers.new("recipe_weighted_normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
        obj["weighted_normals"] = True


def create_reference_sheet(
    bpy: Any,
    recipe: dict[str, Any],
    materials: dict[str, Any],
    collection: Any,
) -> None:
    source_reference = obj_exporter.require_object(
        recipe.get("source_reference"),
        "source_reference",
    )
    source_image = source_reference.get("turnaround_sheet")
    if not isinstance(source_image, str) or not source_image:
        return
    image_path = ROOT / source_image
    if not image_path.exists():
        return

    image = bpy.data.images.load(str(image_path))
    material = bpy.data.materials.new("turnaround_reference_sheet")
    material.use_nodes = True
    material.diffuse_color = (1.0, 1.0, 1.0, 1.0)
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    texture = nodes.new(type="ShaderNodeTexImage")
    texture.image = image
    if shader is not None:
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])

    width = 1.35
    height = 1.8
    y = 0.36
    z_mid = 0.9
    vertices = [
        (-width / 2.0, y, z_mid - height / 2.0),
        (width / 2.0, y, z_mid - height / 2.0),
        (width / 2.0, y, z_mid + height / 2.0),
        (-width / 2.0, y, z_mid + height / 2.0),
    ]
    mesh = bpy.data.meshes.new("turnaround_reference_sheet_mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    mesh.uv_layers.new(name="UVMap")
    uvs = mesh.uv_layers.active.data
    for loop, uv in zip(uvs, [(0, 0), (1, 0), (1, 1), (0, 1)], strict=False):
        loop.uv = uv
    obj = bpy.data.objects.new("turnaround_reference_sheet", mesh)
    obj.data.materials.append(material)
    obj["reference_image"] = str(image_path)
    link_to_collection(obj, collection)


def create_starter_armature(bpy: Any, mathutils: Any, collection: Any) -> Any:
    bpy.ops.object.armature_add(enter_editmode=True, location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = "armature__low_poly_character_mannequin_v0"
    armature.show_in_front = True
    armature.data.name = "low_poly_character_mannequin_starter_armature"
    edit_bones = armature.data.edit_bones
    if "Bone" in edit_bones:
        edit_bones.remove(edit_bones["Bone"])

    created = {}
    for bone_row in starter_bones():
        bone = edit_bones.new(bone_row["name"])
        bone.head = mathutils.Vector(bone_row["head"])
        bone.tail = mathutils.Vector(bone_row["tail"])
        parent_name = bone_row["parent"]
        if parent_name in created:
            bone.parent = created[parent_name]
            bone.use_connect = False
        created[bone_row["name"]] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    link_to_collection(armature, collection)
    return armature


def create_curve_line(
    bpy: Any,
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    material: Any,
    collection: Any,
) -> Any:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.002
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (start[0], start[1], start[2], 1.0)
    spline.points[1].co = (end[0], end[1], end[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    link_to_collection(obj, collection)
    return obj


def create_guides(bpy: Any, materials: dict[str, Any], collection: Any) -> None:
    material = materials["guide_line"]
    for z_value, name in [
        (0.0, "ground"),
        (0.34, "knees"),
        (0.76, "hips"),
        (1.22, "shoulders"),
        (1.78, "head_top"),
    ]:
        create_curve_line(
            bpy,
            f"guide_height__{name}",
            (-0.64, -0.24, z_value),
            (0.64, -0.24, z_value),
            material,
            collection,
        )
    create_curve_line(
        bpy,
        "guide_centerline",
        (0.0, -0.24, 0.0),
        (0.0, -0.24, 1.82),
        material,
        collection,
    )


def add_scene_context(bpy: Any, mathutils: Any, recipe: dict[str, Any]) -> None:
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1600
    bpy.context.scene.world.color = (0.96, 0.96, 0.96)

    bpy.ops.object.light_add(type="AREA", location=(0.0, -2.8, 3.0))
    light = bpy.context.object
    light.name = "low_poly_mannequin_area_light"
    light.data.energy = 420
    light.data.size = 4.0

    front_camera = add_ortho_camera(
        bpy,
        mathutils,
        "camera__front_view",
        (0.0, -4.0, 0.96),
        (0.0, 0.0, 0.92),
        2.15,
    )
    add_ortho_camera(
        bpy,
        mathutils,
        "camera__side_view",
        (4.0, 0.0, 0.96),
        (0.0, 0.0, 0.92),
        2.15,
    )
    bpy.context.scene.camera = front_camera
    bpy.context.scene["asset_id"] = recipe["asset_id"]
    bpy.context.scene["stage"] = "low_poly_character_mannequin_blender_scene_v0"


def add_ortho_camera(
    bpy: Any,
    mathutils: Any,
    name: str,
    location: tuple[float, float, float],
    target_location: tuple[float, float, float],
    ortho_scale: float,
) -> Any:
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.name = name
    target = mathutils.Vector(target_location)
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    return camera


def render_camera_view(bpy: Any, camera_name: str, render_path: Path) -> None:
    camera = bpy.data.objects.get(camera_name)
    if camera is None:
        fail(f"missing camera {camera_name}")
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = sys.argv[1:] if argv is None else argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(
        description="Export the low-poly character mannequin v0 Blender scene."
    )
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    recipe_path = resolve_path(args.recipe)
    recipe = obj_exporter.load_json_object(recipe_path)
    obj_exporter.validate_recipe(recipe, recipe_path)
    objects = obj_exporter.build_mesh_objects(recipe)

    if args.validate_only:
        if args.json_report:
            report_path = resolve_path(args.json_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report = make_report(
                recipe,
                recipe_path,
                objects,
                generated=False,
                out_root=None,
                render=args.render,
            )
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS low-poly mannequin Blender scene validation: "
            f"parts={len(objects)} bones={len(starter_bones())}"
        )
        return 0

    out_root = resolve_path(args.out)
    report_path = resolve_path(args.json_report) if args.json_report else None
    run_blender_export(recipe, recipe_path, objects, out_root, args.render, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
