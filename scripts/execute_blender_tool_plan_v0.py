#!/usr/bin/env python3
"""Execute deterministic gameguy_tool_plan_v0 plans in Blender.

This is an adapter: it consumes compiled tool-plan JSON and does not read the
source intent recipe or choose design steps itself.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = Path("/tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json")
DEFAULT_OUT = Path("/tmp/gameguy_blender_tool_plan_execution_v0")

SUPPORTED_TOOLS = {
    "calculate_bounds",
    "create_collision_proxy",
    "create_lod_variant",
    "dissolve_limited",
    "export_gltf",
    "join_objects",
    "mark_seam",
    "mark_sharp",
    "material_assign_by_part",
    "material_principled_shader",
    "modifier_bevel",
    "modifier_boolean",
    "modifier_displace",
    "modifier_weighted_normal",
    "modifier_weld",
    "object_duplicate_radial",
    "primitive_cube_add",
    "procedural_bump_map",
    "procedural_noise_texture",
    "recalc_normals",
    "render_workbench_preview",
    "uv_pack_islands",
    "uv_smart_project",
    "validate_non_manifold",
}


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


def require_vector(value: Any, field: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    result = []
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")
        result.append(round(float(item), 6))
    return result


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


def validate_plan(plan: dict[str, Any], plan_path: Path) -> list[dict[str, Any]]:
    if plan.get("schema") != "gameguy_tool_plan_v0":
        fail(f"{plan_path} schema must be gameguy_tool_plan_v0")
    require_string(plan.get("plan_id"), "plan_id")
    if plan.get("source_schema") != "asset_mill_tool_plan_recipe_bundle_v0":
        fail("source_schema must be asset_mill_tool_plan_recipe_bundle_v0")
    if plan.get("rules", {}).get("blender_adapter_must_consume_plan") is not True:
        fail("plan rules must require Blender adapter consumption")
    stage_order = [require_string(stage, f"stage_order[{index}]") for index, stage in enumerate(require_list(plan.get("stage_order"), "stage_order"))]
    stage_indexes = {stage: index for index, stage in enumerate(stage_order)}
    steps: list[dict[str, Any]] = []
    previous_stage = -1
    previous_order = 0
    for step_index, item in enumerate(require_list(plan.get("steps"), "steps")):
        step = require_object(item, f"steps[{step_index}]")
        order = step.get("order")
        if not isinstance(order, int) or isinstance(order, bool) or order <= previous_order:
            fail(f"steps[{step_index}].order must strictly increase")
        previous_order = order
        step_id = require_string(step.get("step_id"), f"steps[{step_index}].step_id")
        tool_id = require_string(step.get("tool_id"), f"{step_id}.tool_id")
        if tool_id not in SUPPORTED_TOOLS:
            fail(f"{step_id} uses unsupported tool_id `{tool_id}`")
        if step.get("deterministic") is not True:
            fail(f"{step_id} must be deterministic")
        stage = require_string(step.get("stage"), f"{step_id}.stage")
        if stage not in stage_indexes:
            fail(f"{step_id}.stage uses unknown stage `{stage}`")
        if stage_indexes[stage] < previous_stage:
            fail(f"{step_id} is out of stage order")
        previous_stage = stage_indexes[stage]
        require_object(step.get("params", {}), f"{step_id}.params")
        steps.append(step)
    summary = require_object(plan.get("summary"), "summary")
    if summary.get("step_count") != len(steps):
        fail("summary.step_count must match steps length")
    return steps


def make_report(plan_path: Path, plan: dict[str, Any], steps: list[dict[str, Any]], *, generated: bool, render: bool, export: bool) -> dict[str, Any]:
    unique_tools = sorted({step["tool_id"] for step in steps})
    return {
        "schema": "blender_tool_plan_execution_report_v0",
        "adapter": "scripts/execute_blender_tool_plan_v0.py",
        "source_plan": str(plan_path),
        "plan_schema": plan["schema"],
        "plan_id": plan["plan_id"],
        "asset_id": plan["asset_id"],
        "asset_family": plan["asset_family"],
        "style": plan["style"],
        "step_count": len(steps),
        "supported_step_count": len(steps),
        "unique_tool_count": len(unique_tools),
        "unique_tools": unique_tools,
        "generated_outputs_created": generated,
        "render_requested": render,
        "export_requested": export,
        "rules": {
            "consumes_gameguy_tool_plan_v0": True,
            "reads_source_intent_recipe": False,
            "runs_tool_plan_compiler": False,
            "imports_asset_pump": False,
            "executes_only_supported_deterministic_steps": True,
            "source_design_logic": False,
        },
    }


def alias_from_step_id(step_id: str) -> str:
    return step_id.removeprefix("create_")


def material_role_for_alias(alias: str) -> str:
    if alias.startswith("base_"):
        return "base"
    if alias.startswith("cap_"):
        return "cap"
    if alias in {"post_core"}:
        return "shaft"
    if "rib" in alias:
        return "rib"
    if "socket" in alias:
        return "socket"
    return "default"


def run_blender_execution(plan: dict[str, Any], steps: list[dict[str, Any]], out_root: Path, report: dict[str, Any], *, render: bool, export: bool) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Blender execution requires Blender Python. Use --validate-only with normal Python.")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    context: dict[str, Any] = {
        "objects": {},
        "groups": {
            "base": [],
            "cap": [],
            "ribs": [],
            "cutters": [],
            "visible": [],
        },
        "materials": {},
        "textures": {},
        "executed_steps": [],
        "skipped_steps": [],
        "validation": {},
        "bounds_m": None,
        "final_object": None,
    }
    create_default_materials(bpy, context)
    for step in steps:
        execute_step(bpy, mathutils, plan, step, context, out_root, render=render, export=export)

    final_obj = context.get("final_object")
    if final_obj is None:
        fail("tool plan execution did not create a final object")
    add_scene_context(bpy, mathutils)
    if context.get("render_path"):
        setup_render_from_params(bpy, context.get("render_params", {}), Path(context["render_path"]))
        bpy.ops.render.render(write_still=True)
    blend_path = out_root / "tool_plan_execution_v0.blend"
    report_path = out_root / "tool_plan_execution_v0_report.json"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report["generated_outputs_created"] = True
    report["blend_path"] = str(blend_path)
    report["object_count"] = len(bpy.context.scene.objects)
    report["mesh_object_count"] = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    report["executed_step_count"] = len(context["executed_steps"])
    report["skipped_step_count"] = len(context["skipped_steps"])
    report["executed_steps"] = context["executed_steps"]
    report["skipped_steps"] = context["skipped_steps"]
    report["bounds_m"] = context["bounds_m"]
    report["validation"] = context["validation"]
    if context.get("render_path"):
        report["render_path"] = context["render_path"]
    if context.get("export_path"):
        report["export_path"] = context["export_path"]
    report["final_object"] = {
        "name": final_obj.name,
        "vertex_count": len(final_obj.data.vertices),
        "edge_count": len(final_obj.data.edges),
        "face_count": len(final_obj.data.polygons),
        "material_slot_count": len(final_obj.material_slots),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS Blender tool-plan execution: steps={len(context['executed_steps'])} out={out_root}")


def create_default_materials(bpy: Any, context: dict[str, Any]) -> None:
    colors = {
        "default": (0.48, 0.46, 0.39, 1.0),
        "base": (0.38, 0.36, 0.31, 1.0),
        "cap": (0.55, 0.52, 0.44, 1.0),
        "shaft": (0.47, 0.45, 0.38, 1.0),
        "rib": (0.58, 0.55, 0.46, 1.0),
        "socket": (0.20, 0.22, 0.24, 1.0),
        "collision": (0.12, 0.35, 0.90, 0.25),
        "lod": (0.32, 0.46, 0.62, 1.0),
    }
    for name, color in colors.items():
        mat = bpy.data.materials.new(f"tool_plan_{name}")
        mat.diffuse_color = color
        context["materials"][name] = mat


def execute_step(bpy: Any, mathutils: Any, plan: dict[str, Any], step: dict[str, Any], context: dict[str, Any], out_root: Path, *, render: bool, export: bool) -> None:
    tool_id = step["tool_id"]
    if tool_id == "primitive_cube_add":
        execute_primitive_cube_add(bpy, step, context)
    elif tool_id == "object_duplicate_radial":
        execute_object_duplicate_radial(step, context)
    elif tool_id == "modifier_boolean":
        execute_modifier_boolean(bpy, step, context)
    elif tool_id == "join_objects":
        execute_join_objects(bpy, plan, step, context)
    elif tool_id == "modifier_bevel":
        add_modifier_to_final(bpy, step, context, "BEVEL", {"width": step["params"].get("width_m", 0.01), "segments": int(step["params"].get("segments", 1))}, apply=True)
    elif tool_id == "mark_sharp":
        mark_all_boundary_edges_sharp(context)
    elif tool_id == "modifier_weighted_normal":
        add_modifier_to_final(bpy, step, context, "WEIGHTED_NORMAL", {"keep_sharp": bool(step["params"].get("keep_sharp", True))}, apply=False)
    elif tool_id == "modifier_displace":
        execute_modifier_displace(bpy, step, context)
    elif tool_id == "modifier_weld":
        add_modifier_to_final(bpy, step, context, "WELD", {"merge_threshold": step["params"].get("merge_distance_m", 0.0005)}, apply=True)
    elif tool_id == "dissolve_limited":
        execute_dissolve_limited(bpy, step, context)
    elif tool_id == "recalc_normals":
        execute_recalc_normals(bpy, step, context)
    elif tool_id == "mark_seam":
        mark_back_edges_as_seams(context)
    elif tool_id == "uv_smart_project":
        execute_uv_smart_project(bpy, step, context)
    elif tool_id == "uv_pack_islands":
        execute_uv_pack_islands(bpy, step, context)
    elif tool_id == "material_principled_shader":
        execute_material_principled_shader(bpy, step, context)
    elif tool_id == "procedural_noise_texture":
        context["textures"]["stone_noise"] = step["params"]
    elif tool_id == "procedural_bump_map":
        context["textures"]["stone_bump"] = step["params"]
    elif tool_id == "material_assign_by_part":
        assign_stone_material_to_final(context)
    elif tool_id == "calculate_bounds":
        context["bounds_m"] = calculate_object_bounds(mathutils, require_final_object(context))
    elif tool_id == "validate_non_manifold":
        context["validation"]["non_manifold_edge_count"] = count_non_manifold_edges(require_final_object(context))
    elif tool_id == "create_collision_proxy":
        execute_create_collision_proxy(bpy, step, context)
    elif tool_id == "create_lod_variant":
        execute_create_lod_variant(bpy, step, context)
    elif tool_id == "render_workbench_preview":
        if render:
            render_path = out_root / "tool_plan_execution_v0_workbench.png"
            context["render_path"] = str(render_path)
            context["render_params"] = step["params"]
        else:
            context["skipped_steps"].append({"step_id": step["step_id"], "tool_id": tool_id, "reason": "render flag not set"})
            return
    elif tool_id == "export_gltf":
        if export:
            export_path = out_root / "tool_plan_execution_v0.glb"
            bpy.ops.export_scene.gltf(filepath=str(export_path), export_format="GLB", use_selection=False)
            context["export_path"] = str(export_path)
        else:
            context["skipped_steps"].append({"step_id": step["step_id"], "tool_id": tool_id, "reason": "export flag not set"})
            return
    else:
        fail(f"{step['step_id']} uses unsupported tool_id `{tool_id}`")
    context["executed_steps"].append({"order": step["order"], "step_id": step["step_id"], "tool_id": tool_id, "stage": step["stage"]})


def execute_primitive_cube_add(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    params = step["params"]
    size = require_vector(params.get("size_m"), f"{step['step_id']}.params.size_m", 3)
    location = require_vector(params.get("location_m"), f"{step['step_id']}.params.location_m", 3)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    alias = alias_from_step_id(step["step_id"])
    obj.name = alias
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    role = material_role_for_alias(alias)
    obj["tool_plan_step_id"] = step["step_id"]
    obj["tool_id"] = step["tool_id"]
    obj["material_role"] = role
    obj.data.materials.append(context["materials"].get(role, context["materials"]["default"]))
    context["objects"][alias] = obj
    if role == "base":
        context["groups"]["base"].append(alias)
    elif role == "cap":
        context["groups"]["cap"].append(alias)
    elif role == "rib":
        context["groups"]["ribs"].append(alias)
    elif role == "socket":
        context["groups"]["cutters"].append(alias)
        obj.hide_viewport = True
        obj.hide_render = True
    elif role == "shaft":
        context["objects"]["post_core"] = obj
    if role != "socket":
        context["groups"]["visible"].append(alias)


def execute_object_duplicate_radial(step: dict[str, Any], context: dict[str, Any]) -> None:
    source = context["objects"].get("single_rib_source")
    if source is None:
        fail("duplicate_ribs_radially requires single_rib_source")
    count = int(step["params"].get("count", 1))
    if count < 1:
        fail("duplicate_ribs_radially count must be positive")
    radius = float(step["params"].get("radius_m", source.location.x))
    z = source.location.z
    source.name = "rib_00"
    source["material_role"] = "rib"
    context["objects"]["rib_00"] = source
    context["groups"]["ribs"] = ["rib_00"]
    for index in range(1, count):
        angle = math.tau * index / count
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.name = f"rib_{index:02d}"
        duplicate.location.x = math.cos(angle) * radius
        duplicate.location.y = math.sin(angle) * radius
        duplicate.location.z = z
        duplicate.rotation_euler.z = angle
        duplicate["material_role"] = "rib"
        source.users_collection[0].objects.link(duplicate)
        context["objects"][duplicate.name] = duplicate
        context["groups"]["ribs"].append(duplicate.name)
        context["groups"]["visible"].append(duplicate.name)


def execute_modifier_boolean(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    cutters = [context["objects"].get(name) for name in step["params"].get("cutters", [])]
    cutters = [cutter for cutter in cutters if cutter is not None]
    targets = [context["objects"].get("post_core")]
    targets.extend(context["objects"].get(name) for name in context["groups"].get("ribs", []))
    for target in [obj for obj in targets if obj is not None]:
        for cutter in cutters:
            modifier = target.modifiers.new(name=f"{step['step_id']}_{cutter.name}", type="BOOLEAN")
            modifier.operation = step["params"].get("operation", "DIFFERENCE")
            modifier.object = cutter
            bpy.context.view_layer.objects.active = target
            target.select_set(True)
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except RuntimeError:
                target.modifiers.remove(modifier)
            target.select_set(False)


def execute_join_objects(bpy: Any, plan: dict[str, Any], step: dict[str, Any], context: dict[str, Any]) -> None:
    names: list[str] = []
    for group_name in step["params"].get("objects", []):
        if group_name in context["groups"]:
            names.extend(context["groups"][group_name])
        elif group_name in context["objects"]:
            names.append(group_name)
    objects = [context["objects"][name] for name in names if name in context["objects"] and not context["objects"][name].hide_viewport]
    if not objects:
        fail("join_visible_post_parts found no visible objects")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    final_obj = bpy.context.object
    final_obj.name = plan["asset_id"]
    final_obj["plan_id"] = plan["plan_id"]
    final_obj["asset_family"] = plan["asset_family"]
    final_obj["style"] = plan["style"]
    final_obj["adapter_only"] = True
    context["final_object"] = final_obj
    context["objects"][final_obj.name] = final_obj


def require_final_object(context: dict[str, Any]) -> Any:
    final_obj = context.get("final_object")
    if final_obj is None:
        fail("step requires final object")
    return final_obj


def add_modifier_to_final(bpy: Any, step: dict[str, Any], context: dict[str, Any], modifier_type: str, values: dict[str, Any], *, apply: bool) -> None:
    obj = require_final_object(context)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    modifier = obj.modifiers.new(name=step["step_id"], type=modifier_type)
    for key, value in values.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)
    if apply:
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except RuntimeError:
            obj.modifiers.remove(modifier)
    obj.select_set(False)


def mark_all_boundary_edges_sharp(context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    for edge in obj.data.edges:
        edge.use_edge_sharp = True


def mark_back_edges_as_seams(context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    for edge in obj.data.edges:
        verts = [obj.data.vertices[index].co for index in edge.vertices]
        if all(vertex.y <= 0.0 for vertex in verts):
            edge.use_seam = True


def execute_modifier_displace(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    texture = None
    if hasattr(bpy.data, "textures"):
        texture = bpy.data.textures.new(name="tool_plan_stone_noise", type="VORONOI")
        texture.noise_scale = 0.85
        texture.intensity = 0.18
    modifier = obj.modifiers.new(name=step["step_id"], type="DISPLACE")
    modifier.strength = float(step["params"].get("strength_m", 0.0))
    if texture is not None:
        modifier.texture = texture
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    except RuntimeError:
        obj.modifiers.remove(modifier)
    obj.select_set(False)


def execute_dissolve_limited(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(float(step["params"].get("angle_limit_degrees", 1.0))))
    except RuntimeError:
        pass
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def execute_recalc_normals(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=bool(step["params"].get("inside", False)))
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def execute_uv_smart_project(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(float(step["params"].get("angle_limit_degrees", 66.0))),
        island_margin=float(step["params"].get("island_margin", 0.02)),
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def execute_uv_pack_islands(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.uv.pack_islands(margin=float(step["params"].get("margin", 0.02)))
    except TypeError:
        bpy.ops.uv.pack_islands()
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def execute_material_principled_shader(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    params = step["params"]
    mat = bpy.data.materials.new("gothic_stone")
    mat.diffuse_color = tuple(require_vector(params.get("base_color", [0.48, 0.46, 0.39]), "base_color", 3) + [1.0])
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = mat.diffuse_color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = float(params.get("roughness", 0.82))
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = float(params.get("metallic", 0.0))
    context["materials"]["gothic_stone"] = mat


def assign_stone_material_to_final(context: dict[str, Any]) -> None:
    obj = require_final_object(context)
    material = context["materials"].get("gothic_stone", context["materials"]["default"])
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.material_index = 0


def calculate_object_bounds(mathutils: Any, obj: Any) -> dict[str, list[float]]:
    coords = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(getattr(coord, axis) for coord in coords), 6) for axis in ("x", "y", "z")],
        "max": [round(max(getattr(coord, axis) for coord in coords), 6) for axis in ("x", "y", "z")],
    }


def count_non_manifold_edges(obj: Any) -> int:
    obj.data.update(calc_edges=True)
    edge_use_counts: dict[tuple[int, int], int] = {}
    for polygon in obj.data.polygons:
        vertices = list(polygon.vertices)
        for index, start in enumerate(vertices):
            end = vertices[(index + 1) % len(vertices)]
            key = tuple(sorted((int(start), int(end))))
            edge_use_counts[key] = edge_use_counts.get(key, 0) + 1
    return sum(1 for count in edge_use_counts.values() if count != 2)


def execute_create_collision_proxy(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    bounds = context.get("bounds_m")
    if not isinstance(bounds, dict):
        fail("create_collision_proxy requires calculated bounds")
    min_v = bounds["min"]
    max_v = bounds["max"]
    size = [max_v[index] - min_v[index] for index in range(3)]
    location = [(min_v[index] + max_v[index]) * 0.5 for index in range(3)]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = "collision_proxy"
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(context["materials"]["collision"])
    obj.display_type = "WIRE"
    obj.hide_render = True
    obj["tool_plan_step_id"] = step["step_id"]


def execute_create_lod_variant(bpy: Any, step: dict[str, Any], context: dict[str, Any]) -> None:
    source = require_final_object(context)
    duplicate = source.copy()
    duplicate.data = source.data.copy()
    duplicate.name = f"{source.name}_LOD1"
    source.users_collection[0].objects.link(duplicate)
    duplicate.location.x += 0.72
    duplicate.data.materials.clear()
    duplicate.data.materials.append(context["materials"]["lod"])
    modifier = duplicate.modifiers.new(name=step["step_id"], type="DECIMATE")
    modifier.ratio = float(step["params"].get("decimate_ratio", 0.55))
    bpy.context.view_layer.objects.active = duplicate
    duplicate.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    except RuntimeError:
        duplicate.modifiers.remove(modifier)
    duplicate.select_set(False)


def setup_render_from_params(bpy: Any, params: dict[str, Any], render_path: Path) -> None:
    resolution = params.get("resolution", [1600, 1100])
    if isinstance(resolution, list) and len(resolution) == 2:
        bpy.context.scene.render.resolution_x = int(resolution[0])
        bpy.context.scene.render.resolution_y = int(resolution[1])
    bpy.context.scene.render.filepath = str(render_path)


def add_scene_context(bpy: Any, mathutils: Any) -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(4.0, -6.0, 6.0))
    light = bpy.context.object
    light.name = "tool_plan_area_light"
    light.data.energy = 500.0
    light.data.size = 5.0
    objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_viewport]
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
        mins = mathutils.Vector((0.0, 0.0, 0.0))
        maxs = mathutils.Vector((1.0, 1.0, 1.0))
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z, 1.0)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((3.0, -4.2, 2.8)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.65
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1100
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Execute deterministic gameguy_tool_plan_v0 JSON in Blender.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true", help="Validate the plan without importing bpy or writing outputs.")
    parser.add_argument("--render", action="store_true", help="Write a Workbench PNG render in Blender mode.")
    parser.add_argument("--export", action="store_true", help="Write a GLB export in Blender mode.")
    parser.add_argument("--json-report", type=Path, help="Optional validation report path for validate-only mode.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
    plan = load_json_object(plan_path)
    steps = validate_plan(plan, plan_path)
    report = make_report(plan_path, plan, steps, generated=False, render=args.render, export=args.export)
    if args.validate_only:
        if args.json_report:
            report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"PASS Blender tool-plan adapter validation: steps={len(steps)} tools={report['unique_tool_count']}")
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    run_blender_execution(plan, steps, out_root, report, render=args.render, export=args.export)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
