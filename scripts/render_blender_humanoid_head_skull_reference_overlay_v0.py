#!/usr/bin/env python3
"""Blender overlay adapter for a compiled humanoid head recipe and skull reference GLTF."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import export_blender_humanoid_head_blockout_v0 as head_adapter

DEFAULT_SKULL_GLTF = Path(
    "/Users/kogaryu/dev/maps/sprite_pipeline/runs/human-skull-source-v1/skull_source/human-skull-source.gltf"
)
DEFAULT_OUT = Path("/tmp/gameguy_humanoid_head_skull_reference_overlay_v0")
EXPECTED_SCHEMA = "humanoid_head_geometry_v0"


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


def rounded(value: float) -> float:
    return round(float(value), 6)


def recipe_bounds(recipe: dict[str, Any]) -> dict[str, list[float]]:
    vertices = [vertex for part in recipe["parts"] for vertex in part["mesh"]["vertices_m"]]
    return {
        axis: [rounded(min(vertex[index] for vertex in vertices)), rounded(max(vertex[index] for vertex in vertices))]
        for index, axis in enumerate(("x", "y", "z"))
    }


def bounds_center(bounds: dict[str, list[float]]) -> tuple[float, float, float]:
    return tuple((bounds[axis][0] + bounds[axis][1]) / 2.0 for axis in ("x", "y", "z"))


def bounds_size(bounds: dict[str, list[float]]) -> dict[str, float]:
    return {axis: rounded(bounds[axis][1] - bounds[axis][0]) for axis in ("x", "y", "z")}


def render_overlay(
    *,
    recipe_path: Path,
    skull_gltf: Path,
    out_root: Path,
    view_id: str,
    render: bool,
    json_report: Path | None,
) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Blender overlay requires Blender Python.")

    if not skull_gltf.exists():
        fail(f"missing skull GLTF: {skull_gltf}")
    recipe = load_json_object(recipe_path)
    validation = head_adapter.validate_recipe(recipe, recipe_path)
    out_root.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collections = {
        "head_parts": head_adapter.ensure_collection(bpy, "head_blockout_parts"),
        "skull_reference": head_adapter.ensure_collection(bpy, "skull_reference_ghost"),
        "guides": head_adapter.ensure_collection(bpy, "head_skull_reference_guides"),
    }
    materials = head_adapter.make_materials(bpy, recipe)
    skull_material = make_skull_reference_material(bpy)

    head_objects = []
    for part in recipe["parts"]:
        head_objects.append(head_adapter.create_part_object(bpy, part, materials, collections["head_parts"]))

    imported = import_skull_reference(bpy, skull_gltf, collections["skull_reference"], skull_material)
    target_bounds = recipe_bounds(recipe)
    source_bounds = object_bounds(imported, mathutils)
    transform_report = align_objects_to_target_bounds(imported, mathutils, source_bounds, target_bounds)

    head_adapter.create_measurement_guides(bpy, mathutils, recipe, materials, collections["guides"])
    create_overlay_label(bpy, recipe, materials, collections["guides"], view_id)
    head_adapter.add_scene_context(bpy, mathutils, view_id)

    blend_path = out_root / "humanoid_head_skull_reference_overlay_v0.blend"
    report_path = json_report if json_report is not None else out_root / "humanoid_head_skull_reference_overlay_v0_report.json"
    report = {
        "schema": "humanoid_head_skull_reference_overlay_blender_report_v0",
        "adapter": "scripts/render_blender_humanoid_head_skull_reference_overlay_v0.py",
        "source_recipe": str(recipe_path),
        "recipe_schema": recipe["schema"],
        "asset_id": recipe["asset_id"],
        "skull_gltf": str(skull_gltf),
        "view_id": view_id,
        "view_role": head_adapter.VIEW_SPECS[view_id]["role"],
        "part_count": validation["part_count"],
        "head_mesh_object_count": len(head_objects),
        "skull_mesh_object_count": len(imported),
        "generated_outputs_created": True,
        "render_requested": render,
        "rules": {
            "consumes_compiled_geometry": True,
            "imports_external_skull_reference": True,
            "external_skull_reference_only": True,
            "source_design_logic_in_blender_adapter": False,
            "no_join_pass": True,
        },
        "target_head_bounds_m": target_bounds,
        "target_head_bounds_size_m": bounds_size(target_bounds),
        "skull_source_bounds_m": transform_report["source_bounds_m"],
        "skull_overlay_transform": transform_report,
        "blend_path": str(blend_path),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if render:
        render_path = out_root / f"humanoid_head_skull_reference_overlay_v0_{view_id}_workbench.png"
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS humanoid head skull reference overlay: view={view_id} out={out_root}")


def make_skull_reference_material(bpy: Any) -> Any:
    material = bpy.data.materials.new("skull_reference_ghost_blue")
    material.diffuse_color = (0.28, 0.58, 0.9, 0.42)
    material.use_nodes = True
    material.blend_method = "BLEND"
    material.show_transparent_back = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = (0.28, 0.58, 0.9, 0.42)
        shader.inputs["Alpha"].default_value = 0.42
        shader.inputs["Roughness"].default_value = 0.8
    return material


def link_to_collection(obj: Any, collection: Any) -> None:
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    for source in list(obj.users_collection):
        if source != collection:
            source.objects.unlink(obj)


def import_skull_reference(bpy: Any, skull_gltf: Path, collection: Any, material: Any) -> list[Any]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(skull_gltf))
    imported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not imported:
        fail(f"skull GLTF imported no mesh objects: {skull_gltf}")
    for obj in imported:
        obj.name = f"skull_reference__{obj.name}"
        obj.data.materials.clear()
        obj.data.materials.append(material)
        obj["reference_role"] = "external_skull_projection_target"
        obj["source_gltf"] = str(skull_gltf)
        link_to_collection(obj, collection)
    return imported


def object_bounds(objects: list[Any], mathutils: Any) -> dict[str, list[float]]:
    points = []
    for obj in objects:
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ mathutils.Vector(corner))
    return {
        axis: [rounded(min(getattr(point, axis) for point in points)), rounded(max(getattr(point, axis) for point in points))]
        for axis in ("x", "y", "z")
    }


def align_objects_to_target_bounds(
    objects: list[Any],
    mathutils: Any,
    source_bounds: dict[str, list[float]],
    target_bounds: dict[str, list[float]],
) -> dict[str, Any]:
    source_size = bounds_size(source_bounds)
    target_size = bounds_size(target_bounds)
    scale = target_size["z"] / source_size["z"]
    source_center = mathutils.Vector(bounds_center(source_bounds))
    target_center = mathutils.Vector(bounds_center(target_bounds))
    transform = mathutils.Matrix.Translation(target_center) @ mathutils.Matrix.Diagonal((scale, scale, scale, 1.0)) @ mathutils.Matrix.Translation(-source_center)
    for obj in objects:
        obj.matrix_world = transform @ obj.matrix_world
    fitted_bounds = object_bounds(objects, mathutils)
    return {
        "policy_id": "bbox_height_fit_centered_v0",
        "scale": rounded(scale),
        "source_center_m": [rounded(value) for value in source_center],
        "target_center_m": [rounded(value) for value in target_center],
        "source_bounds_m": source_bounds,
        "source_bounds_size_m": source_size,
        "fitted_bounds_m": fitted_bounds,
        "fitted_bounds_size_m": bounds_size(fitted_bounds),
    }


def create_overlay_label(bpy: Any, recipe: dict[str, Any], materials: dict[str, Any], collection: Any, view_id: str) -> None:
    bpy.ops.object.text_add(location=(-0.145, 0.08, 0.285), rotation=(math.radians(78), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = "label__humanoid_head_skull_reference_overlay_v0"
    obj.data.body = f"HEAD + SKULL REFERENCE {view_id}"
    obj.data.align_x = "LEFT"
    obj.data.size = 0.008
    obj.data.align_y = "CENTER"
    obj.data.materials.append(materials["label"])
    obj["asset_id"] = recipe["asset_id"]
    obj["view_id"] = view_id
    link_to_collection(obj, collection)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", type=Path, required=True, help="Compiled humanoid head variant recipe JSON")
    parser.add_argument("--skull-gltf", type=Path, default=DEFAULT_SKULL_GLTF, help="External skull source GLTF")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Overlay output directory")
    parser.add_argument("--view", choices=sorted(head_adapter.VIEW_SPECS), default="front", help="Named camera view")
    parser.add_argument("--json-report", type=Path, default=None, help="Optional overlay report JSON path")
    parser.add_argument("--render", action="store_true", help="Render workbench PNG")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv if argv is None else ["script"] + argv
    script_argv = raw_argv[raw_argv.index("--") + 1 :] if "--" in raw_argv else raw_argv[1:]
    args = parse_args(script_argv)
    render_overlay(
        recipe_path=args.recipe,
        skull_gltf=args.skull_gltf,
        out_root=args.out,
        view_id=args.view,
        render=args.render,
        json_report=args.json_report,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
