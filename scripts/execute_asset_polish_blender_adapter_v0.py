#!/usr/bin/env python3
"""Execute the first supported asset_polish_tool_plan_v0 Blender slice.

This adapter consumes a compiled polish plan plus deterministic gameguy_asset_v0
JSON. It does not read source recipes or decide new polish operations.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_asset_polish_blender_adapter_v0 import (
    DEFAULT_PLAN,
    DEFAULT_TOOL_DICTIONARY,
    SUPPORTED_OPERATIONS,
    SUPPORTED_TOOLS,
    adapter_status,
    load_json,
    load_tool_dictionary,
    validate_plan,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET = Path("/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json")
DEFAULT_OUT = Path("/tmp/gameguy_asset_polish_blender_execution_v0")
DEFAULT_REPORT = Path("/tmp/gameguy_asset_polish_blender_executor_validate_only_v0.json")
REPORT_SCHEMA = "asset_polish_blender_execution_report_v0"
SUPPORTED_TOOL_FAMILIES = {
    "modifier_bevel",
    "material_assign_by_part",
    "modifier_weighted_normal",
}
MATERIAL_COLORS: dict[str, tuple[float, float, float, float]] = {
    "base": (0.40, 0.38, 0.32, 1.0),
    "panel": (0.34, 0.33, 0.28, 1.0),
    "trim": (0.63, 0.59, 0.49, 1.0),
    "socket_shadow": (0.12, 0.13, 0.14, 1.0),
    "cap": (0.57, 0.54, 0.45, 1.0),
    "stone": (0.49, 0.47, 0.39, 1.0),
    "default": (0.50, 0.48, 0.42, 1.0),
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


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


def require_list(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    if not allow_empty and not value:
        fail(f"{field} must not be empty")
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


def validate_mesh_part(part: dict[str, Any], field: str, vertex_count: int, face_count: int) -> dict[str, Any]:
    part_id = require_string(part.get("part_id"), f"{field}.part_id")
    require_string(part.get("source_primitive"), f"{field}.source_primitive")
    vertex_range = require_list(part.get("vertex_range"), f"{field}.vertex_range")
    face_range = require_list(part.get("face_range"), f"{field}.face_range")
    if len(vertex_range) != 2 or not all(isinstance(value, int) and not isinstance(value, bool) for value in vertex_range):
        fail(f"{field}.vertex_range must contain two integer indexes")
    if len(face_range) != 2 or not all(isinstance(value, int) and not isinstance(value, bool) for value in face_range):
        fail(f"{field}.face_range must contain two integer indexes")
    if vertex_range[0] < 0 or vertex_range[0] > vertex_range[1] or vertex_range[1] >= vertex_count:
        fail(f"{field}.vertex_range is outside mesh vertices")
    if face_range[0] < 0 or face_range[0] > face_range[1] or face_range[1] >= face_count:
        fail(f"{field}.face_range is outside mesh faces")
    return {
        "part_id": part_id,
        "source_primitive": part["source_primitive"],
        "vertex_range": vertex_range,
        "face_range": face_range,
        "material_role": str(part.get("material_role", "stone")),
    }


def validate_asset(asset: dict[str, Any], asset_path: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    if asset.get("schema") != "gameguy_asset_v0":
        fail(f"{asset_path} schema must be gameguy_asset_v0")
    asset_id = require_string(asset.get("asset_id"), "asset.asset_id")
    expected_asset_id = require_object(plan.get("source_asset"), "plan.source_asset").get("asset_id")
    if asset_id != expected_asset_id:
        fail(f"asset_id `{asset_id}` must match plan source asset `{expected_asset_id}`")
    mesh = require_object(asset.get("mesh"), f"{asset_id}.mesh")
    if mesh.get("coordinate_space") != "local_xyz_m":
        fail(f"{asset_id}.mesh.coordinate_space must be local_xyz_m")
    vertices = require_list(mesh.get("vertices"), f"{asset_id}.mesh.vertices")
    faces = require_list(mesh.get("faces"), f"{asset_id}.mesh.faces")
    for index, vertex in enumerate(vertices):
        require_vector(vertex, f"{asset_id}.mesh.vertices[{index}]")
    for face_index, face_value in enumerate(faces):
        face = require_list(face_value, f"{asset_id}.mesh.faces[{face_index}]")
        if len(face) < 3:
            fail(f"{asset_id}.mesh.faces[{face_index}] must contain at least three indexes")
        for index, value in enumerate(face):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= len(vertices):
                fail(f"{asset_id}.mesh.faces[{face_index}][{index}] is not a valid vertex index")
    parts = require_list(mesh.get("parts"), f"{asset_id}.mesh.parts")
    result = [validate_mesh_part(require_object(item, f"{asset_id}.mesh.parts[{index}]"), f"{asset_id}.mesh.parts[{index}]", len(vertices), len(faces)) for index, item in enumerate(parts)]
    return result


def target_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {target["target_id"]: target for target in require_list(plan.get("targets"), "plan.targets")}


def material_slot_map(plan: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for index, slot in enumerate(require_list(plan.get("material_slots"), "plan.material_slots")):
        slot_id = require_string(require_object(slot, f"material_slots[{index}]").get("slot_id"), f"material_slots[{index}].slot_id")
        result[slot_id] = index
    return result


def source_role_to_polish_role(role: str) -> str:
    if role == "base":
        return "base"
    if role == "cap":
        return "cap"
    if role == "socket":
        return "socket_shadow"
    return "stone"


def supported_steps(plan: dict[str, Any]) -> list[dict[str, Any]]:
    steps = []
    for step in require_list(plan.get("steps"), "plan.steps"):
        item = require_object(step, "plan.steps[]")
        if adapter_status(str(item.get("operation", "")), str(item.get("tool_id", ""))) == "supported":
            steps.append(item)
    return steps


def skipped_future_steps(plan: dict[str, Any]) -> list[dict[str, Any]]:
    skipped = []
    for step in require_list(plan.get("steps"), "plan.steps"):
        item = require_object(step, "plan.steps[]")
        if adapter_status(str(item.get("operation", "")), str(item.get("tool_id", ""))) == "future":
            skipped.append(
                {
                    "step_id": item["step_id"],
                    "operation": item["operation"],
                    "tool_id": item["tool_id"],
                    "reason": "recognized_future_operation_not_in_first_execution_slice",
                }
            )
    return skipped


def make_execution_report(
    plan_path: Path,
    asset_path: Path,
    plan: dict[str, Any],
    asset: dict[str, Any],
    validation_report: dict[str, Any],
    parts: list[dict[str, Any]],
    *,
    generated: bool,
) -> dict[str, Any]:
    supported = supported_steps(plan)
    skipped = skipped_future_steps(plan)
    unique_tools = sorted({step["tool_id"] for step in supported})
    return {
        "schema": REPORT_SCHEMA,
        "adapter": "scripts/execute_asset_polish_blender_adapter_v0.py",
        "source_plan": str(plan_path),
        "source_asset": str(asset_path),
        "plan_schema": plan["schema"],
        "asset_schema": asset["schema"],
        "plan_id": plan["plan_id"],
        "source_recipe_id": plan["source_recipe_id"],
        "source_asset_id": plan["source_asset"]["asset_id"],
        "asset_id": asset["asset_id"],
        "step_count": len(plan["steps"]),
        "supported_step_count": validation_report["supported_step_count"],
        "future_step_count": validation_report["future_step_count"],
        "executed_step_count": 0,
        "skipped_future_step_count": len(skipped),
        "unique_tool_count": len(unique_tools),
        "unique_tools": unique_tools,
        "mesh_part_count": len(parts),
        "generated_outputs_created": generated,
        "validation_warnings": validation_report["warnings"],
        "executed_steps": [],
        "skipped_steps": skipped,
        "modifier_applications": [],
        "material_assignment": {},
        "weighted_normals": {},
        "quality_pass": {
            "supported_polish_steps_executed": False,
            "future_steps_skipped": len(skipped) == validation_report["future_step_count"],
            "source_asset_preserved": True,
            "source_recipe_not_read": True,
        },
        "rules": {
            "consumes_asset_polish_tool_plan_v0": True,
            "consumes_gameguy_asset_v0": True,
            "reads_source_recipe": False,
            "runs_asset_pump": False,
            "executes_only_supported_deterministic_steps": True,
            "skips_future_operations": True,
            "source_design_logic": False,
            "mutates_source_asset_json": False,
        },
    }


def create_materials(bpy: Any, plan: dict[str, Any]) -> tuple[list[Any], dict[str, int]]:
    materials = []
    slot_indexes: dict[str, int] = {}
    for index, slot in enumerate(plan["material_slots"]):
        slot_id = slot["slot_id"]
        role = slot["material_role"]
        material = bpy.data.materials.new(slot_id)
        material.diffuse_color = MATERIAL_COLORS.get(role, MATERIAL_COLORS["default"])
        materials.append(material)
        slot_indexes[slot_id] = index
    return materials, slot_indexes


def remap_part_mesh(asset: dict[str, Any], part: dict[str, Any]) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    mesh = asset["mesh"]
    face_start, face_end = part["face_range"]
    used_indexes: list[int] = []
    for face in mesh["faces"][face_start : face_end + 1]:
        for value in face:
            if value not in used_indexes:
                used_indexes.append(value)
    remap = {old: new for new, old in enumerate(used_indexes)}
    vertices = [tuple(float(value) for value in mesh["vertices"][old]) for old in used_indexes]
    faces = [tuple(remap[index] for index in face) for face in mesh["faces"][face_start : face_end + 1]]
    return vertices, faces


def create_part_objects(bpy: Any, asset: dict[str, Any], parts: list[dict[str, Any]], materials: list[Any]) -> dict[str, Any]:
    objects: dict[str, Any] = {}
    for part in parts:
        vertices, faces = remap_part_mesh(asset, part)
        mesh = bpy.data.meshes.new(f"{asset['asset_id']}_{part['part_id']}_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update(calc_edges=True)
        obj = bpy.data.objects.new(part["part_id"], mesh)
        for material in materials:
            obj.data.materials.append(material)
        obj["asset_id"] = asset["asset_id"]
        obj["source_part_id"] = part["part_id"]
        obj["source_primitive"] = part["source_primitive"]
        obj["source_material_role"] = part["material_role"]
        bpy.context.collection.objects.link(obj)
        objects[part["part_id"]] = obj
    return objects


def target_objects(step: dict[str, Any], targets: dict[str, dict[str, Any]], objects: dict[str, Any]) -> list[Any]:
    target_id = require_string(step.get("target"), f"{step['step_id']}.target")
    target = targets.get(target_id)
    if target is None:
        fail(f"{step['step_id']} references unknown target `{target_id}`")
    result = []
    for part_id in target["source_part_ids"]:
        obj = objects.get(part_id)
        if obj is not None:
            result.append(obj)
    if not result:
        fail(f"{step['step_id']} target `{target_id}` resolved no source part objects")
    return result


def apply_bevel(bpy: Any, step: dict[str, Any], objects: list[Any]) -> dict[str, Any]:
    params = step["params"]
    target_names = []
    width = float(params["width_m"])
    segments = int(params["segments"])
    profile = float(params.get("profile", 0.5))
    for obj in objects:
        target_names.append(obj.name)
        modifier = obj.modifiers.new(name=step["step_id"], type="BEVEL")
        modifier.width = width
        modifier.segments = segments
        modifier.profile = profile
        if hasattr(modifier, "harden_normals"):
            modifier.harden_normals = bool(params.get("harden_normals", True))
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return {
        "step_id": step["step_id"],
        "tool_id": step["tool_id"],
        "modifier_type": "BEVEL",
        "target_objects": target_names,
        "width_m": width,
        "segments": segments,
        "applied": True,
    }


def assign_materials_by_part(plan: dict[str, Any], asset_parts: list[dict[str, Any]], objects: dict[str, Any], slot_indexes: dict[str, int], step: dict[str, Any]) -> dict[str, Any]:
    material_map = step["params"]["material_map"]
    assigned_parts: dict[str, list[str]] = {}
    assigned_faces_by_slot: dict[str, int] = {}
    for part in asset_parts:
        part_id = part["part_id"]
        obj = objects[part_id]
        polish_role = source_role_to_polish_role(part["material_role"])
        slot_id = material_map.get(polish_role, material_map.get("stone"))
        if slot_id not in slot_indexes:
            fail(f"{step['step_id']} material slot `{slot_id}` is not declared")
        slot_index = slot_indexes[slot_id]
        for polygon in obj.data.polygons:
            polygon.material_index = slot_index
        obj["polish_material_role"] = polish_role
        assigned_parts.setdefault(polish_role, []).append(part_id)
        assigned_faces_by_slot[slot_id] = assigned_faces_by_slot.get(slot_id, 0) + len(obj.data.polygons)
    return {
        "step_id": step["step_id"],
        "tool_id": step["tool_id"],
        "assigned_parts_by_role": assigned_parts,
        "assigned_faces_by_slot": assigned_faces_by_slot,
        "material_slot_count": len(plan["material_slots"]),
    }


def add_weighted_normals(step: dict[str, Any], objects: list[Any]) -> dict[str, Any]:
    target_names = []
    for obj in objects:
        target_names.append(obj.name)
        modifier = obj.modifiers.new(name=step["step_id"], type="WEIGHTED_NORMAL")
        if hasattr(modifier, "keep_sharp"):
            modifier.keep_sharp = bool(step["params"].get("keep_sharp", True))
        if hasattr(modifier, "weight"):
            modifier.weight = int(step["params"].get("weight", 50))
    return {
        "step_id": step["step_id"],
        "tool_id": step["tool_id"],
        "modifier_type": "WEIGHTED_NORMAL",
        "target_objects": target_names,
        "applied": False,
    }


def add_scene_context(bpy: Any, mathutils: Any, render_path: Path | None) -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(3.2, -4.8, 4.2))
    light = bpy.context.object
    light.name = "asset_polish_area_light"
    light.data.energy = 360.0
    light.data.size = 3.5
    objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if objs:
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
    else:
        mins = mathutils.Vector((-0.5, -0.5, 0.0))
        maxs = mathutils.Vector((0.5, 0.5, 1.0))
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z, 1.0)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((2.2, -3.2, 2.4)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.45
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    if render_path is not None:
        bpy.context.scene.render.filepath = str(render_path)


def run_blender_execution(
    plan_path: Path,
    asset_path: Path,
    plan: dict[str, Any],
    asset: dict[str, Any],
    validation_report: dict[str, Any],
    parts: list[dict[str, Any]],
    out_root: Path,
    *,
    render: bool,
) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Asset polish execution requires Blender Python. Use --validate-only with normal Python.")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    materials, slot_indexes = create_materials(bpy, plan)
    objects = create_part_objects(bpy, asset, parts, materials)
    targets = target_map(plan)
    report = make_execution_report(plan_path, asset_path, plan, asset, validation_report, parts, generated=True)
    report["executed_steps"] = []
    report["modifier_applications"] = []
    material_assignment: dict[str, Any] = {}
    weighted_normals: dict[str, Any] = {}

    for step in plan["steps"]:
        status = adapter_status(step["operation"], step["tool_id"])
        if status != "supported":
            continue
        if step["tool_id"] == "modifier_bevel":
            application = apply_bevel(bpy, step, target_objects(step, targets, objects))
            report["modifier_applications"].append(application)
        elif step["tool_id"] == "material_assign_by_part":
            material_assignment = assign_materials_by_part(plan, parts, objects, slot_indexes, step)
            report["material_assignment"] = material_assignment
        elif step["tool_id"] == "modifier_weighted_normal":
            weighted_normals = add_weighted_normals(step, target_objects(step, targets, objects))
            report["weighted_normals"] = weighted_normals
            report["modifier_applications"].append(weighted_normals)
        else:
            fail(f"{step['step_id']} uses unsupported execution tool `{step['tool_id']}`")
        report["executed_steps"].append(
            {
                "step_id": step["step_id"],
                "operation": step["operation"],
                "tool_id": step["tool_id"],
                "target": step["target"],
            }
        )

    render_path = out_root / "asset_polish_execution_v0_workbench.png" if render else None
    add_scene_context(bpy, mathutils, render_path)
    if render_path is not None:
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    blend_path = out_root / "asset_polish_execution_v0.blend"
    report_path = out_root / "asset_polish_execution_report_v0.json"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    report["blend_path"] = str(blend_path)
    report["object_count"] = len(bpy.context.scene.objects)
    report["mesh_object_count"] = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    report["part_object_count"] = len(objects)
    report["executed_step_count"] = len(report["executed_steps"])
    report["material_assignment"] = material_assignment
    report["weighted_normals"] = weighted_normals
    report["quality_pass"] = {
        "supported_polish_steps_executed": report["executed_step_count"] == report["supported_step_count"],
        "future_steps_skipped": report["skipped_future_step_count"] == report["future_step_count"],
        "source_asset_preserved": True,
        "source_recipe_not_read": True,
        "material_assignment_applied": bool(material_assignment),
        "bevels_applied": sum(1 for item in report["modifier_applications"] if item["modifier_type"] == "BEVEL") == 2,
        "weighted_normals_added": bool(weighted_normals),
    }
    write_json(report_path, report)
    print(
        "PASS asset polish Blender execution: "
        f"executed={report['executed_step_count']} skipped_future={report['skipped_future_step_count']} out={out_root}"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Execute supported asset polish Blender steps from compiled JSON.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--asset", type=Path, default=DEFAULT_ASSET)
    parser.add_argument("--tool-dictionary", type=Path, default=DEFAULT_TOOL_DICTIONARY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--render", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
    asset_path = args.asset if args.asset.is_absolute() else ROOT / args.asset
    dictionary_path = args.tool_dictionary if args.tool_dictionary.is_absolute() else ROOT / args.tool_dictionary
    tool_map, stage_order = load_tool_dictionary(dictionary_path)
    plan = load_json(plan_path)
    validation_report = validate_plan(plan, tool_map, stage_order)
    if validation_report["validation_status"] == "fail":
        write_json(args.json_report if args.json_report.is_absolute() else ROOT / args.json_report, validation_report)
        fail("asset polish plan validation failed; execution aborted")
    asset = load_json(asset_path)
    parts = validate_asset(asset, asset_path, plan)
    report = make_execution_report(plan_path, asset_path, plan, asset, validation_report, parts, generated=False)

    if args.validate_only:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        write_json(report_path, report)
        print(
            "PASS asset polish Blender executor validation: "
            f"supported={report['supported_step_count']} future={report['future_step_count']} asset={asset['asset_id']}"
        )
        return 0

    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    run_blender_execution(plan_path, asset_path, plan, asset, validation_report, parts, out_root, render=args.render)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
