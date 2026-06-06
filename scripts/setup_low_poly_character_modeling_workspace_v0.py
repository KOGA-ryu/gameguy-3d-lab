#!/usr/bin/env python3
"""Create a Blender workspace for manually modeling the low-poly mannequin.

This is intentionally separate from the rig/pose proof exporter. It creates an
artist-facing scene with editable parts, locked ghost parts, front/side
reference planes, guide lines, and cameras.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import export_blender_low_poly_character_mannequin_v0 as scene_exporter
import export_low_poly_character_mannequin_v0 as obj_exporter


DEFAULT_RECIPE = obj_exporter.DEFAULT_RECIPE
DEFAULT_OUT = Path("/tmp/gameguy_low_poly_character_modeling_workspace_v0")
DEFAULT_FRONT_REFERENCE = Path(
    "/tmp/gameguy_low_poly_character_mannequin_blender_v0/"
    "low_poly_character_mannequin_v0_neutral_front_workbench.png"
)
DEFAULT_SIDE_REFERENCE = Path(
    "/tmp/gameguy_low_poly_character_mannequin_blender_v0/"
    "low_poly_character_mannequin_v0_neutral_side_workbench.png"
)


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
    front_reference: Path,
    side_reference: Path,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "low_poly_character_modeling_workspace_report_v0",
        "adapter": "scripts/setup_low_poly_character_modeling_workspace_v0.py",
        "source_recipe": str(recipe_path),
        "recipe_schema": recipe["schema"],
        "asset_id": recipe["asset_id"],
        "editable_object_count": len(objects),
        "ghost_object_count": len(objects),
        "reference_plane_count": 2,
        "guide_collection_count": 1,
        "starter_armature_included": generated,
        "generated_outputs_created": generated,
        "render_requested": render,
        "front_reference": str(front_reference),
        "front_reference_exists": front_reference.exists(),
        "side_reference": str(side_reference),
        "side_reference_exists": side_reference.exists(),
        "workspace_notes": [
            "Edit objects in EDIT_ME_low_poly_parts.",
            "Ghost objects are locked wire guides in GHOST_reference_blockout.",
            "Reference planes sit behind the front and side views.",
            "The starter armature is a future rig guide, not bound to the editable parts.",
        ],
        "rules": {
            "consumes_source_recipe": True,
            "imports_blender": generated,
            "executes_blender": generated,
            "creates_editable_parts": generated,
            "creates_locked_ghost_parts": generated,
            "creates_front_side_reference_planes": generated,
            "keeps_parts_unparented_for_manual_modeling": generated,
        },
    }
    if out_root is not None:
        report["out_root"] = str(out_root)
        report["blend_path"] = str(out_root / f"{recipe['asset_id']}_modeling_workspace.blend")
        if render:
            report["preview_path"] = str(
                out_root / f"{recipe['asset_id']}_modeling_workspace_preview.png"
            )
    return report


def run_blender_workspace_export(
    recipe: dict[str, Any],
    recipe_path: Path,
    objects: list[obj_exporter.MeshObject],
    out_root: Path,
    render: bool,
    json_report: Path | None,
    front_reference: Path,
    side_reference: Path,
) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Workspace export requires Blender Python. Use --validate-only with normal Python.")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collections = {
        "editable": scene_exporter.ensure_collection(bpy, "EDIT_ME_low_poly_parts"),
        "ghost": scene_exporter.ensure_collection(bpy, "GHOST_reference_blockout"),
        "references": scene_exporter.ensure_collection(bpy, "REFERENCE_front_side_planes"),
        "guides": scene_exporter.ensure_collection(bpy, "GUIDES_height_centerline"),
        "rig": scene_exporter.ensure_collection(bpy, "RIG_GUIDE_do_not_bind_yet"),
    }
    materials = make_workspace_materials(bpy, recipe)
    create_editable_parts(bpy, recipe, objects, materials, collections["editable"])
    create_ghost_parts(bpy, recipe, objects, materials, collections["ghost"])
    create_reference_planes(
        bpy,
        front_reference,
        side_reference,
        materials,
        collections["references"],
    )
    create_workspace_guides(bpy, materials, collections["guides"])
    armature = scene_exporter.create_starter_armature(bpy, mathutils, collections["rig"])
    armature.name = "RIG_GUIDE__starter_armature_not_bound"
    armature.hide_select = True
    add_workspace_scene_context(bpy, mathutils, recipe)

    blend_path = out_root / f"{recipe['asset_id']}_modeling_workspace.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    report = make_report(
        recipe,
        recipe_path,
        objects,
        generated=True,
        out_root=out_root,
        render=render,
        front_reference=front_reference,
        side_reference=side_reference,
    )
    report["scene_object_count"] = len(bpy.context.scene.objects)
    if render:
        preview_path = out_root / f"{recipe['asset_id']}_modeling_workspace_preview.png"
        scene_exporter.render_camera_view(bpy, "camera__modeling_front", preview_path)
        report["preview_path"] = str(preview_path)

    report_path = json_report if json_report is not None else out_root / (
        f"{recipe['asset_id']}_modeling_workspace_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS low-poly mannequin modeling workspace export: "
        f"editable={len(objects)} ghost={len(objects)} out={out_root}"
    )


def make_workspace_materials(bpy: Any, recipe: dict[str, Any]) -> dict[str, Any]:
    materials = scene_exporter.make_materials(bpy, recipe)
    materials["editable_ivory"] = make_material(bpy, "EDITABLE_ivory", (0.92, 0.86, 0.74, 1.0))
    materials["ghost_wire"] = make_material(bpy, "GHOST_wire_gray", (0.18, 0.2, 0.22, 0.28))
    materials["reference_plane"] = make_material(
        bpy,
        "REFERENCE_plane_white",
        (1.0, 1.0, 1.0, 0.55),
    )
    return materials


def make_material(bpy: Any, name: str, color: tuple[float, float, float, float]) -> Any:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    material.blend_method = "BLEND"
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Alpha"].default_value = color[3]
        shader.inputs["Roughness"].default_value = 0.72
    return material


def create_part_object(
    bpy: Any,
    recipe: dict[str, Any],
    mesh_object: obj_exporter.MeshObject,
    part: dict[str, Any],
    material: Any,
    collection: Any,
    *,
    name_prefix: str,
) -> Any:
    origin = scene_exporter.part_origin(part, mesh_object)
    local_vertices = [
        (vertex[0] - origin[0], vertex[1] - origin[1], vertex[2] - origin[2])
        for vertex in mesh_object.vertices
    ]
    mesh = bpy.data.meshes.new(f"{name_prefix}{mesh_object.name}_mesh")
    mesh.from_pydata(local_vertices, [], mesh_object.faces)
    mesh.update()
    obj = bpy.data.objects.new(f"{name_prefix}{mesh_object.name}", mesh)
    obj.location = origin
    obj.data.materials.append(material)
    obj["asset_id"] = recipe["asset_id"]
    obj["source_part_name"] = mesh_object.name
    scene_exporter.link_to_collection(obj, collection)
    return obj


def create_editable_parts(
    bpy: Any,
    recipe: dict[str, Any],
    objects: list[obj_exporter.MeshObject],
    materials: dict[str, Any],
    collection: Any,
) -> None:
    parts_by_name = {part["name"]: part for part in recipe["parts"]}
    for mesh_object in objects:
        part = parts_by_name[mesh_object.name]
        material = materials.get(mesh_object.material, materials["editable_ivory"])
        obj = create_part_object(
            bpy,
            recipe,
            mesh_object,
            part,
            material,
            collection,
            name_prefix="EDIT__",
        )
        obj["modeling_role"] = "edit_this_part"
        obj["suggested_tools"] = "Edit Mode, proportional editing, bevel, loop cut, knife."
        scene_exporter.apply_blender_tool_hints(obj, part)


def create_ghost_parts(
    bpy: Any,
    recipe: dict[str, Any],
    objects: list[obj_exporter.MeshObject],
    materials: dict[str, Any],
    collection: Any,
) -> None:
    parts_by_name = {part["name"]: part for part in recipe["parts"]}
    for mesh_object in objects:
        part = parts_by_name[mesh_object.name]
        obj = create_part_object(
            bpy,
            recipe,
            mesh_object,
            part,
            materials["ghost_wire"],
            collection,
            name_prefix="GHOST__",
        )
        obj.display_type = "WIRE"
        obj.hide_select = True
        obj["modeling_role"] = "locked_reference_wire"


def create_reference_planes(
    bpy: Any,
    front_reference: Path,
    side_reference: Path,
    materials: dict[str, Any],
    collection: Any,
) -> None:
    create_image_plane(
        bpy,
        "REFERENCE__front_view",
        front_reference,
        vertices=[
            (-0.78, 0.48, -0.02),
            (0.78, 0.48, -0.02),
            (0.78, 0.48, 1.84),
            (-0.78, 0.48, 1.84),
        ],
        fallback_material=materials["reference_plane"],
        collection=collection,
    )
    create_image_plane(
        bpy,
        "REFERENCE__side_view",
        side_reference,
        vertices=[
            (-0.55, -0.72, -0.02),
            (-0.55, 0.72, -0.02),
            (-0.55, 0.72, 1.84),
            (-0.55, -0.72, 1.84),
        ],
        fallback_material=materials["reference_plane"],
        collection=collection,
    )


def create_image_plane(
    bpy: Any,
    name: str,
    image_path: Path,
    vertices: list[tuple[float, float, float]],
    fallback_material: Any,
    collection: Any,
) -> Any:
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    mesh.uv_layers.new(name="UVMap")
    uvs = mesh.uv_layers.active.data
    for loop, uv in zip(uvs, [(0, 0), (1, 0), (1, 1), (0, 1)], strict=False):
        loop.uv = uv
    obj = bpy.data.objects.new(name, mesh)
    obj.hide_select = True
    if image_path.exists():
        material = bpy.data.materials.new(f"{name}_material")
        material.diffuse_color = (1.0, 1.0, 1.0, 0.62)
        material.use_nodes = True
        material.blend_method = "BLEND"
        image = bpy.data.images.load(str(image_path))
        texture = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        texture.image = image
        shader = material.node_tree.nodes.get("Principled BSDF")
        if shader is not None:
            material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
            shader.inputs["Alpha"].default_value = 0.62
        obj.data.materials.append(material)
        obj["reference_image"] = str(image_path)
    else:
        obj.data.materials.append(fallback_material)
        obj["reference_image_missing"] = str(image_path)
    scene_exporter.link_to_collection(obj, collection)
    return obj


def create_workspace_guides(bpy: Any, materials: dict[str, Any], collection: Any) -> None:
    scene_exporter.create_guides(bpy, materials, collection)
    material = materials["guide_line"]
    scene_exporter.create_curve_line(
        bpy,
        "guide_side_depth_axis",
        (-0.55, -0.72, 0.0),
        (-0.55, 0.72, 0.0),
        material,
        collection,
    )


def add_workspace_scene_context(bpy: Any, mathutils: Any, recipe: dict[str, Any]) -> None:
    scene_exporter.add_scene_context(bpy, mathutils, recipe)
    front_camera = bpy.data.objects.get("camera__front_view")
    if front_camera is not None:
        front_camera.name = "camera__modeling_front"
        front_camera.data.ortho_scale = 2.25
    side_camera = bpy.data.objects.get("camera__side_view")
    if side_camera is not None:
        side_camera.name = "camera__modeling_side"
        side_camera.data.ortho_scale = 2.25
    bpy.context.scene["stage"] = "low_poly_character_manual_modeling_workspace_v0"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = sys.argv[1:] if argv is None else argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(
        description="Set up a Blender workspace for manually modeling the mannequin."
    )
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--front-reference", type=Path, default=DEFAULT_FRONT_REFERENCE)
    parser.add_argument("--side-reference", type=Path, default=DEFAULT_SIDE_REFERENCE)
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
    scene_exporter.validate_rig_parent_map(recipe)
    objects = obj_exporter.build_mesh_objects(recipe)
    front_reference = resolve_path(args.front_reference)
    side_reference = resolve_path(args.side_reference)

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
                front_reference=front_reference,
                side_reference=side_reference,
            )
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS low-poly mannequin modeling workspace validation: "
            f"editable={len(objects)} references=2"
        )
        return 0

    out_root = resolve_path(args.out)
    report_path = resolve_path(args.json_report) if args.json_report else None
    run_blender_workspace_export(
        recipe,
        recipe_path,
        objects,
        out_root,
        args.render,
        report_path,
        front_reference,
        side_reference,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
