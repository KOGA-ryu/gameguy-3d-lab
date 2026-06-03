#!/usr/bin/env python3
"""Compile high-level asset intent into deterministic Blender tool-plan JSON.

This compiler does not import bpy and does not execute Blender. It produces a
source-side plan that a later Blender adapter can consume.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "tool_plan_recipes" / "banister_post_tool_plan_recipe_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_blender_tool_plan_v0")
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


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


def validate_false_claims(value: Any, field: str) -> dict[str, bool]:
    claims = require_object(value, field)
    if claims != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")
    return claims


def validate_tool_dictionary(dictionary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if dictionary.get("schema") != "blender_tool_dictionary_v0":
        fail("tool dictionary schema must be blender_tool_dictionary_v0")
    stages = [require_string(item, f"stages[{index}]") for index, item in enumerate(require_list(dictionary.get("stages"), "stages"))]
    if len(stages) != len(set(stages)):
        fail("stages must be unique")
    lanes = [require_string(item, f"execution_lanes[{index}]") for index, item in enumerate(require_list(dictionary.get("execution_lanes"), "execution_lanes"))]
    if len(lanes) != len(set(lanes)):
        fail("execution_lanes must be unique")
    tools = require_list(dictionary.get("tools"), "tools")
    if dictionary.get("tool_count") != len(tools):
        fail("tool_count must match tools length")

    tool_map: dict[str, dict[str, Any]] = {}
    for tool_index, item in enumerate(tools):
        tool = require_object(item, f"tools[{tool_index}]")
        tool_id = require_string(tool.get("tool_id"), f"tools[{tool_index}].tool_id")
        if tool_id in tool_map:
            fail(f"duplicate tool_id: {tool_id}")
        stage = require_string(tool.get("stage"), f"{tool_id}.stage")
        if stage not in stages:
            fail(f"{tool_id}.stage uses unknown stage `{stage}`")
        lane = require_string(tool.get("execution_lane"), f"{tool_id}.execution_lane")
        if lane not in lanes:
            fail(f"{tool_id}.execution_lane uses unknown lane `{lane}`")
        require_string(tool.get("category"), f"{tool_id}.category")
        if not isinstance(tool.get("deterministic"), bool):
            fail(f"{tool_id}.deterministic must be boolean")
        for list_field in ("blender_api", "inputs", "outputs", "preconditions", "postconditions", "asset_families"):
            values = require_list(tool.get(list_field), f"{tool_id}.{list_field}")
            if not values:
                fail(f"{tool_id}.{list_field} must not be empty")
            for value_index, value in enumerate(values):
                require_string(value, f"{tool_id}.{list_field}[{value_index}]")
        tool_map[tool_id] = tool
    return tool_map


def validate_recipe_bundle(bundle: dict[str, Any], stages: list[str]) -> list[dict[str, Any]]:
    if bundle.get("schema") != "asset_mill_tool_plan_recipe_bundle_v0":
        fail("recipe bundle schema must be asset_mill_tool_plan_recipe_bundle_v0")
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("asset_count must match assets length")
    result: list[dict[str, Any]] = []
    seen_asset_ids: set[str] = set()
    for asset_index, item in enumerate(assets):
        asset = require_object(item, f"assets[{asset_index}]")
        asset_id = require_string(asset.get("asset_id"), f"assets[{asset_index}].asset_id")
        if asset_id in seen_asset_ids:
            fail(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        require_string(asset.get("asset_family"), f"{asset_id}.asset_family")
        require_string(asset.get("style"), f"{asset_id}.style")
        require_string(asset.get("detail_level"), f"{asset_id}.detail_level")
        if not require_list(asset.get("features"), f"{asset_id}.features"):
            fail(f"{asset_id}.features must not be empty")
        for stage_index, stage in enumerate(require_list(asset.get("required_stage_coverage"), f"{asset_id}.required_stage_coverage")):
            stage_id = require_string(stage, f"{asset_id}.required_stage_coverage[{stage_index}]")
            if stage_id not in stages:
                fail(f"{asset_id}.required_stage_coverage uses unknown stage `{stage_id}`")
        validate_false_claims(asset.get("no_claims"), f"{asset_id}.no_claims")
        result.append(asset)
    return result


def style_params(asset: dict[str, Any]) -> dict[str, Any]:
    return require_object(asset.get("style_parameters", {}), f"{asset['asset_id']}.style_parameters")


def feature_steps(asset: dict[str, Any], feature: str) -> list[dict[str, Any]]:
    params = style_params(asset)
    if feature == "stepped_square_base":
        return [
            {"step_id": "create_base_foot", "tool_id": "primitive_cube_add", "purpose": "Create the bottom square foot block.", "params": {"size_m": [0.52, 0.52, 0.10], "location_m": [0.0, 0.0, 0.05]}},
            {"step_id": "create_base_mid_step", "tool_id": "primitive_cube_add", "purpose": "Create the middle stepped plinth block.", "params": {"size_m": [0.44, 0.44, 0.06], "location_m": [0.0, 0.0, 0.13]}},
            {"step_id": "create_base_top_step", "tool_id": "primitive_cube_add", "purpose": "Create the top base transition block.", "params": {"size_m": [0.34, 0.34, 0.06], "location_m": [0.0, 0.0, 0.19], "base_step_count": params.get("base_step_count", 3)}},
            {"step_id": "create_cap_neck", "tool_id": "primitive_cube_add", "purpose": "Create the upper necking block under the cap.", "params": {"size_m": [0.34, 0.34, 0.07], "location_m": [0.0, 0.0, 1.17]}},
            {"step_id": "create_cap_top", "tool_id": "primitive_cube_add", "purpose": "Create the square top cap block.", "params": {"size_m": [0.50, 0.50, 0.13], "location_m": [0.0, 0.0, 1.285]}},
        ]
    if feature == "ribbed_post_core":
        return [
            {"step_id": "create_post_core", "tool_id": "primitive_cube_add", "purpose": "Create the central square post core.", "params": {"size_m": [0.24, 0.24, 0.96], "location_m": [0.0, 0.0, 0.67]}},
            {"step_id": "create_single_rib_source", "tool_id": "primitive_cube_add", "purpose": "Create one narrow rib source block before radial duplication.", "params": {"size_m": [params.get("rib_depth_m", 0.025), 0.035, 0.90], "location_m": [0.145, 0.0, 0.68]}},
            {"step_id": "duplicate_ribs_radially", "tool_id": "object_duplicate_radial", "purpose": "Duplicate the rib source around the post core.", "params": {"count": params.get("rib_count", 12), "axis": "z", "radius_m": 0.145}},
        ]
    if feature == "east_west_rail_sockets":
        return [
            {"step_id": "create_east_socket_cutter", "tool_id": "primitive_cube_add", "purpose": "Create the east rail socket cutter volume.", "params": {"size_m": [0.16, 0.22, params.get("rail_socket_height_m", 0.26)], "location_m": [0.18, 0.0, 0.70]}},
            {"step_id": "create_west_socket_cutter", "tool_id": "primitive_cube_add", "purpose": "Create the west rail socket cutter volume.", "params": {"size_m": [0.16, 0.22, params.get("rail_socket_height_m", 0.26)], "location_m": [-0.18, 0.0, 0.70]}},
            {
                "step_id": "boolean_cut_rail_sockets",
                "tool_id": "modifier_boolean",
                "purpose": "Cut east and west rail sockets into the post body.",
                "params": {
                    "operation": "DIFFERENCE",
                    "solver": "EXACT",
                    "cutters": ["east_socket_cutter", "west_socket_cutter"],
                    "targets": ["post_core"],
                    "cleanup_cutters": True,
                    "socket_shadow_panels": {
                        "enabled": True,
                        "material_role": "socket_shadow",
                        "thickness_m": 0.014,
                        "surface_x_m": 0.12,
                        "surface_offset_m": 0.003,
                        "scale_y": 0.88,
                        "scale_z": 0.88,
                    },
                },
            },
            {"step_id": "join_visible_post_parts", "tool_id": "join_objects", "purpose": "Join visible body pieces after socket planning.", "params": {"objects": ["base", "post_core", "ribs", "cap", "socket_shadows"]}},
        ]
    if feature == "hard_edge_bevels":
        return [
            {"step_id": "add_hard_edge_bevels", "tool_id": "modifier_bevel", "purpose": "Add small bevels so block edges catch light.", "params": {"width_m": params.get("bevel_width_m", 0.018), "segments": 2, "affect": "ANGLE"}},
            {"step_id": "mark_primary_sharp_edges", "tool_id": "mark_sharp", "purpose": "Preserve important silhouette edges after beveling.", "params": {"selection_policy": "outer_silhouette_and_socket_edges"}},
        ]
    if feature == "weighted_normals":
        return [
            {"step_id": "apply_weighted_normals", "tool_id": "modifier_weighted_normal", "purpose": "Improve hard-surface shading without changing source proportions.", "params": {"keep_sharp": true_or_false(True)}},
        ]
    if feature == "stone_surface_material":
        return [
            {"step_id": "add_stone_displacement", "tool_id": "modifier_displace", "purpose": "Add restrained procedural stone surface variation.", "params": {"strength_m": 0.006, "texture": "stone_noise"}},
            {"step_id": "create_stone_material", "tool_id": "material_principled_shader", "purpose": "Create the base gothic stone material.", "params": {"base_color": [0.48, 0.46, 0.39], "roughness": 0.82, "metallic": 0.0}},
            {"step_id": "add_stone_noise_texture", "tool_id": "procedural_noise_texture", "purpose": "Add deterministic stone color and roughness variation.", "params": {"scale": params.get("stone_noise_scale", 38.0), "detail": 9, "roughness": 0.58, "seed": 19}},
            {"step_id": "add_stone_bump_map", "tool_id": "procedural_bump_map", "purpose": "Connect subtle bump detail for close views.", "params": {"height_source": "stone_noise", "strength": 0.07}},
            {"step_id": "assign_material_regions", "tool_id": "material_assign_by_part", "purpose": "Assign material indexes by generated part role.", "params": {"material_map": {"base": "gothic_stone_dark", "cap": "gothic_stone_cap", "shaft": "gothic_stone", "rib": "gothic_stone_highlight", "socket": "gothic_stone_shadow", "socket_shadow": "gothic_stone_shadow"}}},
        ]
    if feature == "smart_uvs":
        return [
            {"step_id": "mark_uv_seams", "tool_id": "mark_seam", "purpose": "Mark predictable seams along back and underside edges.", "params": {"selection_policy": "hidden_back_edges_and_bottom"}},
            {"step_id": "smart_project_uvs", "tool_id": "uv_smart_project", "purpose": "Generate deterministic UV islands for the blocky post.", "params": {"angle_limit_degrees": 66.0, "island_margin": params.get("uv_margin", 0.02)}},
            {"step_id": "pack_uv_islands", "tool_id": "uv_pack_islands", "purpose": "Pack UV islands with stable margin.", "params": {"margin": params.get("uv_margin", 0.02)}},
        ]
    if feature == "collision_and_lod_proxy":
        return [
            {"step_id": "weld_close_vertices", "tool_id": "modifier_weld", "purpose": "Run a deterministic weld pass without merging loose block parts until union cleanup is source-planned.", "params": {"merge_distance_m": params.get("weld_merge_distance_m", 0.0)}},
            {"step_id": "limited_dissolve_cleanup", "tool_id": "dissolve_limited", "purpose": "Remove unneeded coplanar cleanup edges.", "params": {"angle_limit_degrees": 1.0}},
            {"step_id": "recalculate_normals", "tool_id": "recalc_normals", "purpose": "Ensure normals are consistently outward before export.", "params": {"inside": False}},
            {"step_id": "calculate_asset_bounds", "tool_id": "calculate_bounds", "purpose": "Calculate bounds used by connectors, preview framing, and validation.", "params": {"units": "abstract_meter"}},
            {"step_id": "validate_topology_non_manifold", "tool_id": "validate_non_manifold", "purpose": "Report non-manifold geometry before export.", "params": {"fail_on_non_manifold": True, "cleanup_merge_distance_m": 0.0, "cleanup_fill_hole_sides": 0}},
            {"step_id": "create_simple_collision_proxy", "tool_id": "create_collision_proxy", "purpose": "Create a simple collision proxy from asset bounds and socket extents.", "params": {"proxy_policy": "box_stack_low_poly"}},
            {"step_id": "create_lod1_variant", "tool_id": "create_lod_variant", "purpose": "Create a lower-cost display variant for distance views.", "params": {"decimate_ratio": params.get("lod_decimate_ratio", 0.55)}},
        ]
    if feature == "preview_and_export_plan":
        return [
            {"step_id": "render_workbench_asset_preview", "tool_id": "render_workbench_preview", "purpose": "Render a neutral preview after execution.", "params": {"resolution": [1600, 1100], "hide_connectors": False}},
            {"step_id": "export_game_ready_glb", "tool_id": "export_gltf", "purpose": "Export the executed asset as GLB when export is requested.", "params": {"format": "GLB", "apply_modifiers": True}},
        ]
    fail(f"{asset['asset_id']} uses unknown feature `{feature}`")


def true_or_false(value: bool) -> bool:
    return bool(value)


def annotate_step(order: int, source_step: dict[str, Any], tool_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tool_id = require_string(source_step.get("tool_id"), f"steps[{order}].tool_id")
    if tool_id not in tool_map:
        fail(f"step `{source_step.get('step_id', '<unknown>')}` uses unknown tool_id `{tool_id}`")
    tool = tool_map[tool_id]
    return {
        "order": order,
        "step_id": require_string(source_step.get("step_id"), f"steps[{order}].step_id"),
        "stage": tool["stage"],
        "tool_id": tool_id,
        "category": tool["category"],
        "execution_lane": tool["execution_lane"],
        "deterministic": tool["deterministic"],
        "blender_api": tool["blender_api"],
        "purpose": require_string(source_step.get("purpose"), f"steps[{order}].purpose"),
        "params": require_object(source_step.get("params", {}), f"steps[{order}].params"),
        "inputs": tool["inputs"],
        "outputs": tool["outputs"],
        "preconditions": tool["preconditions"],
        "postconditions": tool["postconditions"],
    }


def validate_stage_order(steps: list[dict[str, Any]], stage_order: list[str]) -> None:
    stage_indexes = {stage: index for index, stage in enumerate(stage_order)}
    previous = -1
    for step in steps:
        current = stage_indexes[step["stage"]]
        if current < previous:
            fail(f"step `{step['step_id']}` is out of stage order")
        previous = current


def compile_asset_plan(asset: dict[str, Any], tool_map: dict[str, dict[str, Any]], dictionary: dict[str, Any], recipe_path: Path) -> dict[str, Any]:
    raw_steps: list[dict[str, Any]] = []
    for feature_index, feature in enumerate(require_list(asset.get("features"), f"{asset['asset_id']}.features")):
        feature_id = require_string(feature, f"{asset['asset_id']}.features[{feature_index}]")
        raw_steps.extend(feature_steps(asset, feature_id))

    stage_order = require_list(dictionary.get("stages"), "dictionary.stages")
    stage_indexes = {str(stage): index for index, stage in enumerate(stage_order)}
    staged_steps: list[tuple[int, int, dict[str, Any]]] = []
    for source_index, raw_step in enumerate(raw_steps, start=1):
        step = annotate_step(source_index, raw_step, tool_map)
        staged_steps.append((stage_indexes[step["stage"]], source_index, step))

    seen_step_ids: set[str] = set()
    steps = []
    for order, (_, _, step) in enumerate(sorted(staged_steps), start=1):
        if step["step_id"] in seen_step_ids:
            fail(f"{asset['asset_id']} duplicate step_id: {step['step_id']}")
        seen_step_ids.add(step["step_id"])
        step["order"] = order
        steps.append(step)

    validate_stage_order(steps, [str(stage) for stage in stage_order])
    actual_stages = []
    for step in steps:
        if step["stage"] not in actual_stages:
            actual_stages.append(step["stage"])
    for stage in require_list(asset.get("required_stage_coverage"), f"{asset['asset_id']}.required_stage_coverage"):
        if stage not in actual_stages:
            fail(f"{asset['asset_id']} required stage `{stage}` was not covered by compiled steps")

    execution_lanes = []
    for step in steps:
        if step["execution_lane"] not in execution_lanes:
            execution_lanes.append(step["execution_lane"])
    unique_tools = sorted({step["tool_id"] for step in steps})
    return {
        "schema": "gameguy_tool_plan_v0",
        "plan_id": f"{asset['asset_id']}_compiled",
        "source_schema": "asset_mill_tool_plan_recipe_bundle_v0",
        "source_recipe": repo_display_path(recipe_path),
        "tool_dictionary": dictionary["dictionary_id"],
        "asset_id": asset["asset_id"],
        "asset_family": asset["asset_family"],
        "style": asset["style"],
        "detail_level": asset["detail_level"],
        "target_readiness": asset.get("target_readiness", "procedural_asset"),
        "dimensions_m": require_object(asset.get("dimensions_m"), f"{asset['asset_id']}.dimensions_m"),
        "features": require_list(asset.get("features"), f"{asset['asset_id']}.features"),
        "style_parameters": style_params(asset),
        "stage_order": stage_order,
        "steps": steps,
        "summary": {
            "step_count": len(steps),
            "unique_tool_count": len(unique_tools),
            "unique_tools": unique_tools,
            "covered_stages": actual_stages,
            "execution_lanes": execution_lanes,
            "non_deterministic_step_count": sum(1 for step in steps if not step["deterministic"]),
        },
        "rules": {
            "compiler_imports_bpy": False,
            "compiler_executes_blender": False,
            "writes_generated_media_or_mesh": False,
            "blender_adapter_must_consume_plan": True,
            "tool_ids_validated": True,
            "stage_order_validated": True,
        },
        "no_claims": validate_false_claims(asset.get("no_claims"), f"{asset['asset_id']}.no_claims"),
    }


def write_outputs(plans: list[dict[str, Any]], out_root: Path, recipe_path: Path) -> None:
    plan_dir = out_root / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    manifest_plans = []
    for plan in plans:
        path = plan_dir / f"{plan['plan_id']}.json"
        path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        manifest_plans.append(
            {
                "plan_id": plan["plan_id"],
                "path": str(path.relative_to(out_root)),
                "asset_family": plan["asset_family"],
                "style": plan["style"],
                "step_count": plan["summary"]["step_count"],
                "unique_tool_count": plan["summary"]["unique_tool_count"],
                "covered_stages": plan["summary"]["covered_stages"],
            }
        )
    manifest = {
        "schema": "gameguy_tool_plan_manifest_v0",
        "source_recipe": repo_display_path(recipe_path),
        "source_schema": "asset_mill_tool_plan_recipe_bundle_v0",
        "plan_schema": "gameguy_tool_plan_v0",
        "plan_count": len(plans),
        "plans": manifest_plans,
        "rules": {
            "no_blender_execution": True,
            "no_media": True,
            "no_mesh_export_files": True,
            "tool_dictionary_enforced": True,
            "stage_order_enforced": True,
        },
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile source intent into deterministic Blender tool-plan JSON.")
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true", help="Delete the output folder before writing. Refuses to clean outside /tmp.")
    parser.add_argument("--validate-only", action="store_true", help="Validate dictionary and recipe without writing output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dictionary_path = args.dictionary if args.dictionary.is_absolute() else ROOT / args.dictionary
    recipe_path = args.recipe if args.recipe.is_absolute() else ROOT / args.recipe
    out_root = args.out
    if args.clean:
        resolved = out_root.resolve()
        if not (str(resolved).startswith("/tmp/") or str(resolved).startswith("/private/tmp/")):
            fail("--clean only deletes output folders under /tmp")
        shutil.rmtree(resolved, ignore_errors=True)
    if not args.validate_only and out_root.exists() and any(out_root.iterdir()):
        fail(f"output folder is not empty: {out_root}. Use --clean for /tmp outputs or choose a new folder.")

    dictionary = load_json(dictionary_path)
    recipe = load_json(recipe_path)
    tool_map = validate_tool_dictionary(dictionary)
    assets = validate_recipe_bundle(recipe, [str(stage) for stage in require_list(dictionary.get("stages"), "dictionary.stages")])
    plans = [compile_asset_plan(asset, tool_map, dictionary, recipe_path) for asset in assets]
    if not args.validate_only:
        write_outputs(plans, out_root, recipe_path)
    total_steps = sum(plan["summary"]["step_count"] for plan in plans)
    print(f"compiled tool plans={len(plans)} steps={total_steps} tools={len(tool_map)} out={out_root if not args.validate_only else '<validate-only>'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
