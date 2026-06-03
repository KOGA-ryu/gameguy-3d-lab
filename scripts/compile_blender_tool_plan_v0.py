#!/usr/bin/env python3
"""Compile high-level asset intent into deterministic Blender tool-plan JSON.

This compiler does not import bpy and does not execute Blender. It produces a
source-side plan that a later Blender adapter can consume.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_SEQUENCE_POLICY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "asset_family_tool_sequence_policy_v0.json"
DEFAULT_RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "tool_plan_recipes" / "architectural_tool_plan_recipes_v0.json"
DEFAULT_RAILING_DETAIL_PROFILES = ROOT / "data" / "architecture" / "asset_mill" / "profile_sources" / "railing_detail_profiles_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_blender_tool_plan_v0")
GEOMETRY_DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SEQUENCE_POLICY_SCHEMA = "asset_family_tool_sequence_policy_v0"
GUARD_PANEL_RAILING_DETAIL_PROFILE_IDS = [
    "railing_square_frame_block_v0",
    "railing_pointed_arch_recess_v0",
    "railing_capsule_vertical_slot_v0",
    "railing_circle_bead_strip_v0",
    "railing_ogee_molding_side_profile_v0",
    "railing_trapezoid_transition_collar_v0",
]
PROFILED_PLINTH_BASE_DETAIL_PROFILE_ID = "railing_plinth_ogee_base_side_profile_v0"
FINISH_FEATURE_TOOL_IDS = {
    "hard_edge_bevels": ["modifier_bevel", "mark_sharp"],
    "weighted_normals": ["modifier_weighted_normal"],
    "stone_surface_material": [
        "modifier_displace",
        "material_principled_shader",
        "procedural_noise_texture",
        "procedural_bump_map",
        "material_assign_by_part",
    ],
    "smart_uvs": ["mark_seam", "uv_smart_project", "uv_pack_islands"],
    "collision_and_lod_proxy": [
        "modifier_weld",
        "dissolve_limited",
        "recalc_normals",
        "calculate_bounds",
        "validate_non_manifold",
        "create_collision_proxy",
        "create_lod_variant",
    ],
    "preview_and_export_plan": ["render_workbench_preview", "export_gltf"],
}
FINISH_FEATURES = set(FINISH_FEATURE_TOOL_IDS)
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


def repo_relative_path(value: Any, field: str) -> Path:
    text = require_string(value, field)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        fail(f"{field} must be a relative repo path")
    return ROOT / path


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


def load_geometry_terms() -> dict[str, set[str]]:
    terms = {
        "profile_primitive": set(),
        "mesh_operation": set(),
        "composition_operation": set(),
        "transform": set(),
        "connector": set(),
        "semantic_geometry": set(),
        "measurement": set(),
        "validation_term": set(),
    }
    for path in sorted(GEOMETRY_DICTIONARY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = term.get("term_id")
        category = term.get("category")
        if not isinstance(term_id, str) or not term_id:
            fail(f"{repo_display_path(path)} term_id must be a non-empty string")
        if category in terms:
            if term_id in terms[category]:
                fail(f"duplicate geometry dictionary term `{term_id}` in category `{category}`")
            terms[category].add(term_id)
    for category, ids in terms.items():
        if not ids:
            fail(f"geometry dictionary category `{category}` has no terms")
    return terms


def operation_terms(terms: dict[str, set[str]]) -> set[str]:
    return terms["mesh_operation"] | terms["composition_operation"] | terms["transform"]


def all_geometry_terms(terms: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    for ids in terms.values():
        result.update(ids)
    return result


def require_known_terms(values: Any, known: set[str], field: str) -> list[str]:
    result = []
    for index, item in enumerate(require_list(values, field)):
        term_id = require_string(item, f"{field}[{index}]")
        if term_id not in known:
            fail(f"{field}[{index}] uses unknown geometry dictionary term `{term_id}`")
        result.append(term_id)
    return result


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{field} must be a boolean")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    result = []
    for index, item in enumerate(items):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def validate_false_claims(value: Any, field: str) -> dict[str, bool]:
    claims = require_object(value, field)
    if claims != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")
    return claims


def positive_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{field} must be a positive number")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        fail(f"{field} must be a positive number")
    return round(number, 6)


def finite_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        fail(f"{field} must be a finite number")
    return round(number, 6)


def finite_vector(value: Any, field: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    return [finite_number(item, f"{field}[{index}]") for index, item in enumerate(value)]


def positive_vector(value: Any, field: str, length: int) -> list[float]:
    vector = finite_vector(value, field, length)
    for index, item in enumerate(vector):
        if item <= 0.0:
            fail(f"{field}[{index}] must be positive")
    return vector


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


def validate_sequence_policy(policy: dict[str, Any], dictionary: dict[str, Any], tool_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if policy.get("schema") != SEQUENCE_POLICY_SCHEMA:
        fail(f"sequence policy schema must be {SEQUENCE_POLICY_SCHEMA}")
    if policy.get("tool_dictionary") != dictionary.get("dictionary_id"):
        fail("sequence policy tool_dictionary must match dictionary_id")
    if policy.get("no_claims") != FALSE_CLAIMS:
        fail("sequence policy no_claims must exactly match required false claim flags")
    rules = require_object(policy.get("rules"), "sequence_policy.rules")
    for key in (
        "source_policy_only",
        "compiler_enforces_policy",
        "validator_enforces_policy",
        "blender_adapter_reads_compiled_plan_only",
        "policy_does_not_execute_blender",
        "family_tools_must_exist_in_dictionary",
        "stage_order_must_match_dictionary",
    ):
        if require_bool(rules.get(key), f"sequence_policy.rules.{key}") is not True:
            fail(f"sequence_policy.rules.{key} must be true")
    stage_order = require_string_list(policy.get("stage_order"), "sequence_policy.stage_order")
    if stage_order != require_string_list(dictionary.get("stages"), "dictionary.stages"):
        fail("sequence policy stage_order must match tool dictionary stages")
    family_policies = require_list(policy.get("asset_family_policies"), "sequence_policy.asset_family_policies")
    if policy.get("asset_family_policy_count") != len(family_policies):
        fail("sequence policy asset_family_policy_count must match asset_family_policies length")

    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(family_policies):
        family_policy = require_object(item, f"sequence_policy.asset_family_policies[{index}]")
        asset_family = require_string(family_policy.get("asset_family"), f"sequence_policy.asset_family_policies[{index}].asset_family")
        if asset_family in result:
            fail(f"duplicate sequence policy asset_family `{asset_family}`")
        tags = set(require_string_list(family_policy.get("dictionary_family_tags"), f"{asset_family}.dictionary_family_tags"))
        allowed_features = set(require_string_list(family_policy.get("allowed_features"), f"{asset_family}.allowed_features"))
        required_stages = require_string_list(family_policy.get("required_stage_coverage"), f"{asset_family}.required_stage_coverage")
        for stage in required_stages:
            if stage not in stage_order:
                fail(f"{asset_family}.required_stage_coverage uses unknown stage `{stage}`")
        allowed_by_stage = require_object(family_policy.get("allowed_tools_by_stage"), f"{asset_family}.allowed_tools_by_stage")
        allowed_tools: set[str] = set()
        normalized_allowed_by_stage: dict[str, set[str]] = {}
        for stage, tools_value in allowed_by_stage.items():
            if stage not in stage_order:
                fail(f"{asset_family}.allowed_tools_by_stage uses unknown stage `{stage}`")
            tools = require_string_list(tools_value, f"{asset_family}.allowed_tools_by_stage.{stage}")
            normalized_allowed_by_stage[stage] = set(tools)
            for tool_id in tools:
                if tool_id not in tool_map:
                    fail(f"{asset_family}.allowed_tools_by_stage.{stage} uses unknown tool `{tool_id}`")
                tool = tool_map[tool_id]
                if tool["stage"] != stage:
                    fail(f"{asset_family}.allowed_tools_by_stage.{stage} includes `{tool_id}` from stage `{tool['stage']}`")
                tool_tags = set(require_string_list(tool.get("asset_families"), f"{tool_id}.asset_families"))
                if not tool_tags.intersection(tags):
                    fail(f"{asset_family}.allowed_tools_by_stage.{stage} includes `{tool_id}` without a matching dictionary family tag")
                allowed_tools.add(tool_id)
        required_tools = require_string_list(family_policy.get("required_tools", []), f"{asset_family}.required_tools", allow_empty=True)
        for tool_id in required_tools:
            if tool_id not in allowed_tools:
                fail(f"{asset_family}.required_tools includes `{tool_id}` outside allowed tools")
        forbidden_tools = require_string_list(family_policy.get("forbidden_tools", []), f"{asset_family}.forbidden_tools", allow_empty=True)
        for tool_id in forbidden_tools:
            if tool_id not in tool_map:
                fail(f"{asset_family}.forbidden_tools uses unknown tool `{tool_id}`")
            if tool_id in allowed_tools:
                fail(f"{asset_family}.forbidden_tools includes allowed tool `{tool_id}`")
        constraints = []
        for constraint_index, constraint_value in enumerate(require_list(family_policy.get("tool_order_constraints"), f"{asset_family}.tool_order_constraints")):
            constraint = require_object(constraint_value, f"{asset_family}.tool_order_constraints[{constraint_index}]")
            before = require_string(constraint.get("before"), f"{asset_family}.tool_order_constraints[{constraint_index}].before")
            after = require_string(constraint.get("after"), f"{asset_family}.tool_order_constraints[{constraint_index}].after")
            if before not in allowed_tools:
                fail(f"{asset_family}.tool_order_constraints[{constraint_index}].before is not allowed for the family")
            if after not in allowed_tools:
                fail(f"{asset_family}.tool_order_constraints[{constraint_index}].after is not allowed for the family")
            constraints.append({"before": before, "after": after})
        result[asset_family] = {
            "asset_family": asset_family,
            "allowed_features": allowed_features,
            "required_stage_coverage": required_stages,
            "allowed_tools_by_stage": normalized_allowed_by_stage,
            "required_tools": set(required_tools),
            "forbidden_tools": set(forbidden_tools),
            "tool_order_constraints": constraints,
        }
    return result


def validate_profile_operation_stack(asset: dict[str, Any], terms: dict[str, set[str]]) -> None:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    stack = require_object(asset.get("profile_operation_stack"), f"{asset_id}.profile_operation_stack")
    if stack.get("schema") != "profile_operation_stack_v0":
        fail(f"{asset_id}.profile_operation_stack.schema must be profile_operation_stack_v0")
    require_string(stack.get("grammar_id"), f"{asset_id}.profile_operation_stack.grammar_id")
    if require_string(stack.get("axis"), f"{asset_id}.profile_operation_stack.axis") != "z":
        fail(f"{asset_id}.profile_operation_stack.axis only supports z in v0")
    geometry_terms = require_known_terms(stack.get("geometry_terms_used"), all_geometry_terms(terms), f"{asset_id}.profile_operation_stack.geometry_terms_used")
    profile_terms = require_known_terms(stack.get("profile_terms"), terms["profile_primitive"], f"{asset_id}.profile_operation_stack.profile_terms")
    operations = require_known_terms(stack.get("operations"), operation_terms(terms), f"{asset_id}.profile_operation_stack.operations")
    if "profile_operation_stack" not in operations or "profile_operation_stack" not in geometry_terms:
        fail(f"{asset_id}.profile_operation_stack must declare profile_operation_stack operation term")
    parts = require_list(stack.get("parts"), f"{asset_id}.profile_operation_stack.parts")
    if not parts:
        fail(f"{asset_id}.profile_operation_stack.parts must not be empty")
    seen_part_ids: set[str] = set()
    seen_expanded_ids: set[str] = set()
    for part_index, item in enumerate(parts):
        part = require_object(item, f"{asset_id}.profile_operation_stack.parts[{part_index}]")
        part_id = require_string(part.get("part_id"), f"{asset_id}.profile_operation_stack.parts[{part_index}].part_id")
        if part_id in seen_part_ids:
            fail(f"{asset_id}.profile_operation_stack duplicate part_id `{part_id}`")
        seen_part_ids.add(part_id)
        profile = require_string(part.get("profile"), f"{asset_id}.profile_operation_stack.parts[{part_index}].profile")
        if profile not in profile_terms:
            fail(f"{asset_id}.profile_operation_stack.parts[{part_index}].profile must be declared in profile_terms")
        operation = require_string(part.get("operation"), f"{asset_id}.profile_operation_stack.parts[{part_index}].operation")
        if operation not in operations:
            fail(f"{asset_id}.profile_operation_stack.parts[{part_index}].operation must be declared in operations")
        if operation == "extrude":
            if profile in {"square", "rectangle"}:
                positive_vector(part.get("size_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].size_m", 3)
                finite_vector(part.get("location_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].location_m", 3)
            elif profile == "circle":
                int_value = part.get("vertices")
                if not isinstance(int_value, int) or isinstance(int_value, bool) or int_value < 4:
                    fail(f"{asset_id}.profile_operation_stack.parts[{part_index}].vertices must be an integer >= 4")
                positive_number(part.get("radius_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].radius_m")
                positive_number(part.get("depth_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].depth_m")
                finite_vector(part.get("location_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].location_m", 3)
            else:
                fail(f"{asset_id}.profile_operation_stack.parts[{part_index}] uses unsupported extrude profile `{profile}`")
            seen_expanded_ids.add(part_id)
        elif operation == "array_radial":
            source_part_id = require_string(part.get("source_part_id"), f"{asset_id}.profile_operation_stack.parts[{part_index}].source_part_id")
            if source_part_id in seen_expanded_ids:
                fail(f"{asset_id}.profile_operation_stack duplicate expanded source_part_id `{source_part_id}`")
            seen_expanded_ids.add(source_part_id)
            positive_vector(part.get("source_size_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].source_size_m", 3)
            finite_vector(part.get("source_location_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].source_location_m", 3)
            count = part.get("count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 2:
                fail(f"{asset_id}.profile_operation_stack.parts[{part_index}].count must be an integer >= 2")
            positive_number(part.get("radius_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].radius_m")
        else:
            fail(f"{asset_id}.profile_operation_stack.parts[{part_index}] uses unsupported operation `{operation}`")
        if "material_role" in part:
            require_string(part.get("material_role"), f"{asset_id}.profile_operation_stack.parts[{part_index}].material_role")
    join = require_object(stack.get("join"), f"{asset_id}.profile_operation_stack.join")
    require_string(join.get("step_id"), f"{asset_id}.profile_operation_stack.join.step_id")
    require_string_list(join.get("objects"), f"{asset_id}.profile_operation_stack.join.objects")
    require_string_list(join.get("profile_transition_sequence"), f"{asset_id}.profile_operation_stack.join.profile_transition_sequence")


def validate_finish_tool_stacks(
    bundle: dict[str, Any],
    geometry_terms: dict[str, set[str]],
    tool_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    stacks = require_list(bundle.get("finish_tool_stacks", []), "finish_tool_stacks")
    if "finish_tool_stack_count" in bundle and bundle["finish_tool_stack_count"] != len(stacks):
        fail("finish_tool_stack_count must match finish_tool_stacks length")
    result: dict[str, dict[str, Any]] = {}
    for stack_index, item in enumerate(stacks):
        stack = require_object(item, f"finish_tool_stacks[{stack_index}]")
        stack_id = require_string(stack.get("stack_id"), f"finish_tool_stacks[{stack_index}].stack_id")
        if stack_id in result:
            fail(f"duplicate finish_tool_stack stack_id `{stack_id}`")
        if stack.get("schema") != "finish_tool_stack_v0":
            fail(f"finish_tool_stacks[{stack_index}].schema must be finish_tool_stack_v0")
        require_string(stack.get("grammar_id"), f"finish_tool_stacks[{stack_index}].grammar_id")
        geometry = require_known_terms(stack.get("geometry_terms_used"), all_geometry_terms(geometry_terms), f"finish_tool_stacks[{stack_index}].geometry_terms_used")
        operations = require_known_terms(stack.get("operations"), operation_terms(geometry_terms), f"finish_tool_stacks[{stack_index}].operations")
        if "finish_tool_stack" not in geometry or "finish_tool_stack" not in operations:
            fail(f"finish_tool_stacks[{stack_index}] must declare finish_tool_stack operation term")
        if "preview" in stack:
            preview = require_object(stack.get("preview"), f"finish_tool_stacks[{stack_index}].preview")
            visibility = require_string(preview.get("visibility"), f"finish_tool_stacks[{stack_index}].preview.visibility")
            if visibility not in {"final_asset_only", "scene_with_validation_helpers"}:
                fail(f"finish_tool_stacks[{stack_index}].preview.visibility uses unsupported mode `{visibility}`")
            require_bool(preview.get("hide_validation_helpers"), f"finish_tool_stacks[{stack_index}].preview.hide_validation_helpers")
        sequence = require_list(stack.get("sequence"), f"finish_tool_stacks[{stack_index}].sequence")
        if not sequence:
            fail(f"finish_tool_stacks[{stack_index}].sequence must not be empty")
        for sequence_index, sequence_item in enumerate(sequence):
            entry = require_object(sequence_item, f"finish_tool_stacks[{stack_index}].sequence[{sequence_index}]")
            feature = require_string(entry.get("feature"), f"finish_tool_stacks[{stack_index}].sequence[{sequence_index}].feature")
            if feature not in FINISH_FEATURES:
                fail(f"finish_tool_stacks[{stack_index}].sequence[{sequence_index}].feature uses unknown finish feature `{feature}`")
            tool_ids = require_string_list(entry.get("tool_ids"), f"finish_tool_stacks[{stack_index}].sequence[{sequence_index}].tool_ids")
            expected_tool_ids = FINISH_FEATURE_TOOL_IDS[feature]
            if tool_ids != expected_tool_ids:
                fail(f"finish_tool_stacks[{stack_index}].sequence[{sequence_index}].tool_ids must match compiler expansion for `{feature}`")
            for tool_id in tool_ids:
                if tool_id not in tool_map:
                    fail(f"finish_tool_stacks[{stack_index}].sequence[{sequence_index}].tool_ids uses unknown tool `{tool_id}`")
        result[stack_id] = stack
    return result


def validate_railing_detail_profile_stack(asset: dict[str, Any], geometry_terms: dict[str, set[str]], tool_map: dict[str, dict[str, Any]]) -> None:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    params = style_params(asset)
    bundle_path = repo_relative_path(
        params.get("railing_detail_profile_bundle", repo_display_path(DEFAULT_RAILING_DETAIL_PROFILES)),
        f"{asset_id}.style_parameters.railing_detail_profile_bundle",
    )
    bundle = load_json(bundle_path)
    if bundle.get("schema") != "asset_mill_railing_detail_profile_bundle_v0":
        fail(f"{asset_id}.railing_detail_profile_bundle schema must be asset_mill_railing_detail_profile_bundle_v0")
    profiles = require_list(bundle.get("profiles"), f"{asset_id}.railing_detail_profile_bundle.profiles")
    if bundle.get("profile_count") != len(profiles):
        fail(f"{asset_id}.railing_detail_profile_bundle.profile_count must match profiles length")
    profile_map = {}
    for index, profile_value in enumerate(profiles):
        profile = require_object(profile_value, f"{asset_id}.railing_detail_profile_bundle.profiles[{index}]")
        profile_id = require_string(profile.get("profile_id"), f"{asset_id}.railing_detail_profile_bundle.profiles[{index}].profile_id")
        profile_map[profile_id] = profile
    selected = require_string_list(params.get("railing_detail_profile_ids"), f"{asset_id}.style_parameters.railing_detail_profile_ids")
    if asset.get("asset_family") == "guard_panel" and selected != GUARD_PANEL_RAILING_DETAIL_PROFILE_IDS:
        fail(f"{asset_id}.style_parameters.railing_detail_profile_ids must match guard-panel detail compiler profile order")
    for profile_id in selected:
        if profile_id not in profile_map:
            fail(f"{asset_id}.style_parameters.railing_detail_profile_ids references unknown profile `{profile_id}`")
        profile = profile_map[profile_id]
        shape = require_object(profile.get("source_2d_shape"), f"{profile_id}.source_2d_shape")
        shape_term = require_string(shape.get("term_id"), f"{profile_id}.source_2d_shape.term_id")
        if shape_term not in geometry_terms["profile_primitive"]:
            fail(f"{profile_id}.source_2d_shape.term_id must be a known profile primitive")
        require_known_terms(profile.get("geometry_terms_used"), all_geometry_terms(geometry_terms), f"{profile_id}.geometry_terms_used")
        require_known_terms(profile.get("profile_terms"), geometry_terms["profile_primitive"], f"{profile_id}.profile_terms")
        require_known_terms(profile.get("operations"), operation_terms(geometry_terms), f"{profile_id}.operations")
        has_guard_panel_placement = False
        for placement_index, placement_value in enumerate(require_list(profile.get("where_used"), f"{profile_id}.where_used")):
            placement = require_object(placement_value, f"{profile_id}.where_used[{placement_index}]")
            if placement.get("target_asset_family") == "guard_panel":
                has_guard_panel_placement = True
        if not has_guard_panel_placement and asset.get("asset_family") == "guard_panel":
            fail(f"{profile_id}.where_used must include a guard_panel placement")
        for step_index, step_value in enumerate(require_list(profile.get("blender_tool_sequence"), f"{profile_id}.blender_tool_sequence")):
            step = require_object(step_value, f"{profile_id}.blender_tool_sequence[{step_index}]")
            tool_id = require_string(step.get("tool_id"), f"{profile_id}.blender_tool_sequence[{step_index}].tool_id")
            if tool_id not in tool_map:
                fail(f"{profile_id}.blender_tool_sequence[{step_index}].tool_id uses unknown tool `{tool_id}`")


def profile_map_from_bundle(bundle: dict[str, Any], field: str) -> dict[str, dict[str, Any]]:
    profiles = require_list(bundle.get("profiles"), f"{field}.profiles")
    if bundle.get("profile_count") != len(profiles):
        fail(f"{field}.profile_count must match profiles length")
    profile_map = {}
    for index, profile_value in enumerate(profiles):
        profile = require_object(profile_value, f"{field}.profiles[{index}]")
        profile_id = require_string(profile.get("profile_id"), f"{field}.profiles[{index}].profile_id")
        profile_map[profile_id] = profile
    return profile_map


def validate_profiled_plinth_base_detail(asset: dict[str, Any], geometry_terms: dict[str, set[str]], tool_map: dict[str, dict[str, Any]]) -> None:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    params = style_params(asset)
    bundle_path = repo_relative_path(
        params.get("profiled_plinth_profile_bundle", repo_display_path(DEFAULT_RAILING_DETAIL_PROFILES)),
        f"{asset_id}.style_parameters.profiled_plinth_profile_bundle",
    )
    bundle = load_json(bundle_path)
    if bundle.get("schema") != "asset_mill_railing_detail_profile_bundle_v0":
        fail(f"{asset_id}.profiled_plinth_profile_bundle schema must be asset_mill_railing_detail_profile_bundle_v0")
    profile_id = require_string(
        params.get("profiled_plinth_profile_id", PROFILED_PLINTH_BASE_DETAIL_PROFILE_ID),
        f"{asset_id}.style_parameters.profiled_plinth_profile_id",
    )
    if profile_id != PROFILED_PLINTH_BASE_DETAIL_PROFILE_ID:
        fail(f"{asset_id}.style_parameters.profiled_plinth_profile_id must be {PROFILED_PLINTH_BASE_DETAIL_PROFILE_ID}")
    profile_map = profile_map_from_bundle(bundle, f"{asset_id}.profiled_plinth_profile_bundle")
    profile = require_object(profile_map.get(profile_id), f"{asset_id}.profiled_plinth_profile_bundle.{profile_id}")
    shape = require_object(profile.get("source_2d_shape"), f"{profile_id}.source_2d_shape")
    if require_string(shape.get("term_id"), f"{profile_id}.source_2d_shape.term_id") != "custom_polygon":
        fail(f"{profile_id}.source_2d_shape.term_id must be custom_polygon for the profiled plinth prototype")
    require_known_terms(profile.get("geometry_terms_used"), all_geometry_terms(geometry_terms), f"{profile_id}.geometry_terms_used")
    require_known_terms(profile.get("profile_terms"), geometry_terms["profile_primitive"], f"{profile_id}.profile_terms")
    require_known_terms(profile.get("operations"), operation_terms(geometry_terms), f"{profile_id}.operations")
    for step_index, step_value in enumerate(require_list(profile.get("blender_tool_sequence"), f"{profile_id}.blender_tool_sequence")):
        step = require_object(step_value, f"{profile_id}.blender_tool_sequence[{step_index}]")
        tool_id = require_string(step.get("tool_id"), f"{profile_id}.blender_tool_sequence[{step_index}].tool_id")
        if tool_id not in tool_map:
            fail(f"{profile_id}.blender_tool_sequence[{step_index}].tool_id uses unknown tool `{tool_id}`")
    positive_number(params.get("profiled_plinth_width_m", 0.62), f"{asset_id}.style_parameters.profiled_plinth_width_m")
    positive_number(params.get("profiled_plinth_depth_m", 0.32), f"{asset_id}.style_parameters.profiled_plinth_depth_m")
    positive_number(params.get("profiled_plinth_height_m", 0.22), f"{asset_id}.style_parameters.profiled_plinth_height_m")
    finite_number(params.get("profiled_plinth_base_z_m", 0.0), f"{asset_id}.style_parameters.profiled_plinth_base_z_m")


def resolve_finish_tool_stack(asset: dict[str, Any], finish_stack_map: dict[str, dict[str, Any]]) -> None:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    if "finish_tool_stack" not in require_list(asset.get("features"), f"{asset_id}.features"):
        return
    stack_id = require_string(asset.get("finish_tool_stack"), f"{asset_id}.finish_tool_stack")
    if stack_id not in finish_stack_map:
        fail(f"{asset_id}.finish_tool_stack references unknown stack `{stack_id}`")
    asset["_resolved_finish_tool_stack"] = finish_stack_map[stack_id]


def validate_recipe_bundle(
    bundle: dict[str, Any],
    stages: list[str],
    geometry_terms: dict[str, set[str]],
    tool_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if bundle.get("schema") != "asset_mill_tool_plan_recipe_bundle_v0":
        fail("recipe bundle schema must be asset_mill_tool_plan_recipe_bundle_v0")
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("assets must not be empty")
    if bundle.get("asset_count") != len(assets):
        fail("asset_count must match assets length")
    result: list[dict[str, Any]] = []
    seen_asset_ids: set[str] = set()
    finish_stack_map = validate_finish_tool_stacks(bundle, geometry_terms, tool_map)
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
        if "profile_operation_stack" in asset.get("features", []):
            validate_profile_operation_stack(asset, geometry_terms)
        if "railing_detail_profile_stack" in asset.get("features", []):
            validate_railing_detail_profile_stack(asset, geometry_terms, tool_map)
        if "profiled_plinth_base_detail" in asset.get("features", []):
            validate_profiled_plinth_base_detail(asset, geometry_terms, tool_map)
        if "finish_tool_stack" in asset.get("features", []):
            resolve_finish_tool_stack(asset, finish_stack_map)
        for stage_index, stage in enumerate(require_list(asset.get("required_stage_coverage"), f"{asset_id}.required_stage_coverage")):
            stage_id = require_string(stage, f"{asset_id}.required_stage_coverage[{stage_index}]")
            if stage_id not in stages:
                fail(f"{asset_id}.required_stage_coverage uses unknown stage `{stage_id}`")
        validate_false_claims(asset.get("no_claims"), f"{asset_id}.no_claims")
        result.append(asset)
    return result


def style_params(asset: dict[str, Any]) -> dict[str, Any]:
    return require_object(asset.get("style_parameters", {}), f"{asset['asset_id']}.style_parameters")


def dimensions(asset: dict[str, Any]) -> dict[str, float]:
    raw = require_object(asset.get("dimensions_m"), f"{asset['asset_id']}.dimensions_m")
    return {axis: positive_number(raw.get(axis), f"{asset['asset_id']}.dimensions_m.{axis}") for axis in ("width", "depth", "height")}


def number_param(params: dict[str, Any], name: str, default: float) -> float:
    value = params.get(name, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"style_parameters.{name} must be a number")
    return round(float(value), 6)


def int_param(params: dict[str, Any], name: str, default: int, *, minimum: int = 1) -> int:
    value = params.get(name, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"style_parameters.{name} must be an integer >= {minimum}")
    return value


def bool_param(params: dict[str, Any], name: str, default: bool) -> bool:
    value = params.get(name, default)
    if not isinstance(value, bool):
        fail(f"style_parameters.{name} must be a boolean")
    return value


def vector_param(params: dict[str, Any], name: str, default: list[float]) -> list[float]:
    value = params.get(name, default)
    if not isinstance(value, list) or len(value) != len(default):
        fail(f"style_parameters.{name} must be a {len(default)}-number list")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            fail(f"style_parameters.{name}[{index}] must be a number")
        result.append(round(float(item), 6))
    return result


def flat_profile_prism(profile_points_xz: list[list[float]], y_center: float, depth_y: float) -> dict[str, list[list[float]]]:
    if len(profile_points_xz) < 3:
        fail("flat profile prism requires at least three points")
    half_depth = depth_y * 0.5
    vertices = []
    for x, z in profile_points_xz:
        vertices.append([round(x, 6), round(y_center - half_depth, 6), round(z, 6)])
    for x, z in profile_points_xz:
        vertices.append([round(x, 6), round(y_center + half_depth, 6), round(z, 6)])
    point_count = len(profile_points_xz)
    faces: list[list[float]] = [list(range(point_count)), list(range(point_count * 2 - 1, point_count - 1, -1))]
    for index in range(point_count):
        next_index = (index + 1) % point_count
        faces.append([index, next_index, point_count + next_index, point_count + index])
    return {"vertices": vertices, "faces": faces}


def pointed_arch_points(center_x: float, width: float, base_z: float, shoulder_z: float, apex_z: float) -> list[list[float]]:
    half_width = width * 0.5
    return [
        [round(center_x - half_width, 6), round(base_z, 6)],
        [round(center_x + half_width, 6), round(base_z, 6)],
        [round(center_x + half_width, 6), round(shoulder_z, 6)],
        [round(center_x, 6), round(apex_z, 6)],
        [round(center_x - half_width, 6), round(shoulder_z, 6)],
    ]


def capsule_points(center_x: float, center_z: float, width: float, height: float) -> list[list[float]]:
    half_width = width * 0.5
    half_height = height * 0.5
    radius = min(half_width, half_height)
    straight_half = max(half_height - radius, 0.001)
    return [
        [round(center_x - half_width, 6), round(center_z - straight_half, 6)],
        [round(center_x - half_width * 0.72, 6), round(center_z - half_height, 6)],
        [round(center_x, 6), round(center_z - half_height, 6)],
        [round(center_x + half_width * 0.72, 6), round(center_z - half_height, 6)],
        [round(center_x + half_width, 6), round(center_z - straight_half, 6)],
        [round(center_x + half_width, 6), round(center_z + straight_half, 6)],
        [round(center_x + half_width * 0.72, 6), round(center_z + half_height, 6)],
        [round(center_x, 6), round(center_z + half_height, 6)],
        [round(center_x - half_width * 0.72, 6), round(center_z + half_height, 6)],
        [round(center_x - half_width, 6), round(center_z + straight_half, 6)],
    ]


def regular_profile_points(center_x: float, center_z: float, radius_x: float, radius_z: float, segments: int = 8) -> list[list[float]]:
    if segments < 4:
        fail("regular profile points require at least four segments")
    return [
        [
            round(center_x + math.cos(math.tau * index / segments) * radius_x, 6),
            round(center_z + math.sin(math.tau * index / segments) * radius_z, 6),
        ]
        for index in range(segments)
    ]


def trapezoid_points(center_x: float, center_z: float, bottom_width: float, top_width: float, height: float) -> list[list[float]]:
    half_bottom = bottom_width * 0.5
    half_top = top_width * 0.5
    half_height = height * 0.5
    return [
        [round(center_x - half_bottom, 6), round(center_z - half_height, 6)],
        [round(center_x + half_bottom, 6), round(center_z - half_height, 6)],
        [round(center_x + half_top, 6), round(center_z + half_height, 6)],
        [round(center_x - half_top, 6), round(center_z + half_height, 6)],
    ]


def ogee_points(center_x: float, center_z: float, width: float, height: float) -> list[list[float]]:
    half_width = width * 0.5
    half_height = height * 0.5
    return [
        [round(center_x - half_width, 6), round(center_z - half_height, 6)],
        [round(center_x - half_width * 0.70, 6), round(center_z - half_height, 6)],
        [round(center_x - half_width * 0.58, 6), round(center_z - half_height * 0.15, 6)],
        [round(center_x - half_width * 0.18, 6), round(center_z + half_height * 0.18, 6)],
        [round(center_x + half_width * 0.18, 6), round(center_z - half_height * 0.18, 6)],
        [round(center_x + half_width * 0.58, 6), round(center_z + half_height * 0.15, 6)],
        [round(center_x + half_width * 0.70, 6), round(center_z + half_height, 6)],
        [round(center_x + half_width, 6), round(center_z + half_height, 6)],
        [round(center_x + half_width, 6), round(center_z + half_height * 0.58, 6)],
        [round(center_x - half_width, 6), round(center_z - half_height * 0.58, 6)],
    ]


def profiled_plinth_base_points(center_x: float, base_z: float, width: float, height: float) -> list[list[float]]:
    half_width = width * 0.5
    z0 = base_z
    z1 = base_z + height * 0.22
    z2 = base_z + height * 0.36
    z3 = base_z + height * 0.58
    z4 = base_z + height * 0.78
    z5 = base_z + height
    return [
        [round(center_x - half_width, 6), round(z0, 6)],
        [round(center_x + half_width, 6), round(z0, 6)],
        [round(center_x + half_width, 6), round(z1, 6)],
        [round(center_x + half_width * 0.92, 6), round(z1, 6)],
        [round(center_x + half_width * 0.78, 6), round(z2, 6)],
        [round(center_x + half_width * 0.64, 6), round(z3, 6)],
        [round(center_x + half_width * 0.46, 6), round(z4, 6)],
        [round(center_x + half_width * 0.46, 6), round(z5, 6)],
        [round(center_x - half_width * 0.46, 6), round(z5, 6)],
        [round(center_x - half_width * 0.46, 6), round(z4, 6)],
        [round(center_x - half_width * 0.64, 6), round(z3, 6)],
        [round(center_x - half_width * 0.78, 6), round(z2, 6)],
        [round(center_x - half_width * 0.92, 6), round(z1, 6)],
        [round(center_x - half_width, 6), round(z1, 6)],
    ]


def rail_segment_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    params = style_params(asset)
    body_size = vector_param(params, "rail_body_size_m", [1.08, 0.16, 0.14])
    body_location = vector_param(params, "rail_body_location_m", [0.0, 0.0, 0.16])
    top_cap_size = vector_param(params, "rail_top_cap_size_m", [1.24, 0.22, 0.07])
    top_cap_location = vector_param(params, "rail_top_cap_location_m", [0.0, 0.0, 0.285])
    bottom_lip_size = vector_param(params, "rail_bottom_lip_size_m", [1.12, 0.14, 0.06])
    bottom_lip_location = vector_param(params, "rail_bottom_lip_location_m", [0.0, 0.0, 0.06])
    connector_size = vector_param(params, "rail_connector_tab_size_m", [0.12, 0.12, 0.18])
    connector_x = number_param(params, "rail_connector_tab_center_x_m", 0.63)
    connector_z = number_param(params, "rail_connector_tab_location_z_m", 0.16)
    raised_band_size = vector_param(params, "rail_raised_band_size_m", [0.82, 0.024, 0.07])
    raised_band_z = number_param(params, "rail_raised_band_location_z_m", 0.16)
    raised_band_y = number_param(params, "rail_raised_band_surface_y_m", 0.092)
    return [
        {
            "step_id": "create_rail_body",
            "tool_id": "primitive_cube_add",
            "purpose": "Create the long stone rail body block.",
            "params": {"size_m": body_size, "location_m": body_location, "material_role": "body"},
        },
        {
            "step_id": "create_rail_top_cap",
            "tool_id": "primitive_cube_add",
            "purpose": "Create the slightly wider top cap that reads as a stone coping.",
            "params": {"size_m": top_cap_size, "location_m": top_cap_location, "material_role": "cap"},
        },
        {
            "step_id": "create_rail_bottom_lip",
            "tool_id": "primitive_cube_add",
            "purpose": "Create the lower rail lip for a stepped stone profile.",
            "params": {"size_m": bottom_lip_size, "location_m": bottom_lip_location, "material_role": "base"},
        },
        {
            "step_id": "create_left_connector_tab",
            "tool_id": "primitive_cube_add",
            "purpose": "Create the left post-socket connector tab.",
            "params": {"size_m": connector_size, "location_m": [-connector_x, 0.0, connector_z], "material_role": "connector"},
        },
        {
            "step_id": "create_right_connector_tab",
            "tool_id": "primitive_cube_add",
            "purpose": "Create the right post-socket connector tab.",
            "params": {"size_m": connector_size, "location_m": [connector_x, 0.0, connector_z], "material_role": "connector"},
        },
        {
            "step_id": "create_front_raised_band",
            "tool_id": "primitive_cube_add",
            "purpose": "Create a simple raised front face band for blocky carved detail.",
            "params": {"size_m": raised_band_size, "location_m": [0.0, -raised_band_y, raised_band_z], "material_role": "rib"},
        },
        {
            "step_id": "create_rear_raised_band",
            "tool_id": "primitive_cube_add",
            "purpose": "Create a matching raised rear face band for reversible placement.",
            "params": {"size_m": raised_band_size, "location_m": [0.0, raised_band_y, raised_band_z], "material_role": "rib"},
        },
        {
            "step_id": "join_rail_segment_blocks",
            "tool_id": "join_objects",
            "purpose": "Join rail blocks and connector tabs into one deterministic modular segment.",
            "params": {
                "objects": [
                    "rail_body",
                    "rail_top_cap",
                    "rail_bottom_lip",
                    "left_connector_tab",
                    "right_connector_tab",
                    "front_raised_band",
                    "rear_raised_band",
                ],
                "connector_tab_span_m": round(connector_x * 2.0 + connector_size[0], 6),
                "socket_match_size_m": connector_size,
            },
        },
    ]


def gothic_panel_guard_mesh_step(
    step_id: str,
    purpose: str,
    points_xz: list[list[float]],
    *,
    y_center: float,
    depth_y: float,
    material_role: str,
    source_profile: str = "pointed_arch_profile",
    source_detail_profile: str | None = None,
    group: str | None = None,
) -> dict[str, Any]:
    mesh = flat_profile_prism(points_xz, y_center, depth_y)
    params = {
        "vertices": mesh["vertices"],
        "faces": mesh["faces"],
        "material_role": material_role,
        "source_profile": source_profile,
    }
    if source_detail_profile:
        params["source_detail_profile"] = source_detail_profile
    if group:
        params["group"] = group
    return {
        "step_id": step_id,
        "tool_id": "mesh_from_pydata",
        "purpose": purpose,
        "params": params,
    }


def profiled_plinth_base_detail_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    params = style_params(asset)
    width = number_param(params, "profiled_plinth_width_m", 0.62)
    depth = number_param(params, "profiled_plinth_depth_m", 0.32)
    height = number_param(params, "profiled_plinth_height_m", 0.22)
    base_z = number_param(params, "profiled_plinth_base_z_m", 0.0)
    y_center = number_param(params, "profiled_plinth_center_y_m", 0.0)
    profile_id = require_string(params.get("profiled_plinth_profile_id", PROFILED_PLINTH_BASE_DETAIL_PROFILE_ID), f"{asset['asset_id']}.style_parameters.profiled_plinth_profile_id")
    points = profiled_plinth_base_points(0.0, base_z, width, height)
    return [
        gothic_panel_guard_mesh_step(
            "create_profiled_plinth_base_detail",
            "Create one source-owned profiled plinth base detail from a low-point 2D custom polygon.",
            points,
            y_center=y_center,
            depth_y=depth,
            material_role="base",
            source_profile="custom_polygon",
            source_detail_profile=profile_id,
            group="base",
        ),
        {
            "step_id": "join_profiled_plinth_base_detail",
            "tool_id": "join_objects",
            "purpose": "Finalize the single profiled plinth mesh as an isolated detail prototype.",
            "params": {
                "objects": ["base"],
                "source_detail_profile": profile_id,
                "source_control_point_count": len(points),
                "profile_width_m": width,
                "profile_depth_m": depth,
                "profile_height_m": height,
            },
        },
    ]


def railing_detail_profile_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    params = style_params(asset)
    bundle_path = repo_display_path(
        repo_relative_path(
            params.get("railing_detail_profile_bundle", repo_display_path(DEFAULT_RAILING_DETAIL_PROFILES)),
            f"{asset['asset_id']}.style_parameters.railing_detail_profile_bundle",
        )
    )
    selected_profiles = require_string_list(params.get("railing_detail_profile_ids"), f"{asset['asset_id']}.style_parameters.railing_detail_profile_ids")
    detail_y = number_param(params, "center_panel_detail_surface_y_m", -0.083)
    cut_depth = number_param(params, "center_panel_arch_cut_depth_y_m", 0.18)
    arch_points = pointed_arch_points(
        0.0,
        number_param(params, "center_panel_arch_width_m", 0.34),
        number_param(params, "center_panel_arch_base_z_m", 0.42),
        number_param(params, "center_panel_arch_shoulder_z_m", 0.61),
        number_param(params, "center_panel_arch_apex_z_m", 0.72),
    )
    slot_x = number_param(params, "panel_capsule_slot_center_x_m", 0.36)
    slot_points = capsule_points(
        -slot_x,
        number_param(params, "panel_capsule_slot_center_z_m", 0.56),
        number_param(params, "panel_capsule_slot_width_m", 0.085),
        number_param(params, "panel_capsule_slot_height_m", 0.25),
    )
    bead_points = regular_profile_points(
        number_param(params, "lower_bead_center_x_m", -0.34),
        number_param(params, "lower_bead_center_z_m", 0.255),
        number_param(params, "lower_bead_radius_x_m", 0.026),
        number_param(params, "lower_bead_radius_z_m", 0.018),
        segments=8,
    )
    ogee_points_xz = ogee_points(
        0.0,
        number_param(params, "ogee_profile_center_z_m", 0.805),
        number_param(params, "ogee_profile_width_m", 0.92),
        number_param(params, "ogee_profile_height_m", 0.055),
    )
    trapezoid_x = number_param(params, "socket_trapezoid_center_x_m", 0.63)
    trapezoid_points_xz = trapezoid_points(
        -trapezoid_x,
        number_param(params, "socket_trapezoid_center_z_m", 0.55),
        number_param(params, "socket_trapezoid_width_bottom_m", 0.12),
        number_param(params, "socket_trapezoid_width_top_m", 0.075),
        number_param(params, "socket_trapezoid_height_m", 0.30),
    )
    slot_cut_depth = number_param(params, "panel_capsule_slot_cut_depth_y_m", 0.18)
    bead_count = int_param(params, "lower_bead_count", 9, minimum=1)
    bead_spacing = number_param(params, "lower_bead_spacing_x_m", 0.085)
    base_steps = [
        gothic_panel_guard_mesh_step(
            "create_center_panel_arch_cutter",
            "Create a pointed-arch cutter from the railing detail source profile.",
            arch_points,
            y_center=detail_y,
            depth_y=cut_depth,
            material_role="socket",
            source_profile="pointed_arch_profile",
            source_detail_profile="railing_pointed_arch_recess_v0",
        ),
        gothic_panel_guard_mesh_step(
            "create_center_panel_arch_recess_shadow",
            "Create a dark pointed-arch recess plate behind the panel cut.",
            arch_points,
            y_center=round(detail_y - cut_depth * 0.52, 6),
            depth_y=0.012,
            material_role="recess",
            source_profile="pointed_arch_profile",
            source_detail_profile="railing_pointed_arch_recess_v0",
            group="railing_detail_recesses",
        ),
        gothic_panel_guard_mesh_step(
            "create_left_panel_capsule_slot_cutter",
            "Create one capsule slot cutter from the railing detail source profile.",
            slot_points,
            y_center=detail_y,
            depth_y=slot_cut_depth,
            material_role="socket",
            source_profile="capsule",
            source_detail_profile="railing_capsule_vertical_slot_v0",
        ),
        gothic_panel_guard_mesh_step(
            "create_left_panel_capsule_slot_shadow",
            "Create one capsule slot shadow plate before mirroring.",
            slot_points,
            y_center=round(detail_y - slot_cut_depth * 0.52, 6),
            depth_y=0.012,
            material_role="recess",
            source_profile="capsule",
            source_detail_profile="railing_capsule_vertical_slot_v0",
            group="railing_detail_recesses",
        ),
        gothic_panel_guard_mesh_step(
            "create_lower_bead_source",
            "Create one circular bead source before linear array expansion.",
            bead_points,
            y_center=round(detail_y - 0.014, 6),
            depth_y=0.028,
            material_role="trim",
            source_profile="circle",
            source_detail_profile="railing_circle_bead_strip_v0",
            group="railing_detail_beads",
        ),
        gothic_panel_guard_mesh_step(
            "create_top_coping_ogee_front_profile",
            "Create a low-point ogee/cyma molding profile along the front coping rail.",
            ogee_points_xz,
            y_center=round(detail_y - 0.012, 6),
            depth_y=0.024,
            material_role="trim",
            source_profile="custom_polygon",
            source_detail_profile="railing_ogee_molding_side_profile_v0",
            group="railing_detail_trim",
        ),
        gothic_panel_guard_mesh_step(
            "create_left_socket_trapezoid_collar_trim",
            "Create one tapered socket-collar trim plate before mirroring.",
            trapezoid_points_xz,
            y_center=round(detail_y - 0.018, 6),
            depth_y=0.024,
            material_role="collar",
            source_profile="trapezoid",
            source_detail_profile="railing_trapezoid_transition_collar_v0",
            group="railing_detail_trim",
        ),
    ]
    return [
        *base_steps,
        {
            "step_id": "mirror_panel_capsule_slot_detail",
            "tool_id": "modifier_mirror",
            "purpose": "Mirror capsule slot cutter and shadow plate across the guard panel.",
            "params": {
                "axis": "x",
                "objects": [
                    {
                        "source_object": "left_panel_capsule_slot_cutter",
                        "mirrored_name": "right_panel_capsule_slot_cutter",
                        "group": "cutters",
                    },
                    {
                        "source_object": "left_panel_capsule_slot_shadow",
                        "mirrored_name": "right_panel_capsule_slot_shadow",
                        "group": "railing_detail_recesses",
                    },
                ],
                "source_detail_profile": "railing_capsule_vertical_slot_v0",
            },
        },
        {
            "step_id": "mirror_socket_trapezoid_collar_trim",
            "tool_id": "modifier_mirror",
            "purpose": "Mirror the tapered socket-collar trim to the other panel side.",
            "params": {
                "axis": "x",
                "objects": [
                    {
                        "source_object": "left_socket_trapezoid_collar_trim",
                        "mirrored_name": "right_socket_trapezoid_collar_trim",
                        "group": "railing_detail_trim",
                    }
                ],
                "source_detail_profile": "railing_trapezoid_transition_collar_v0",
            },
        },
        {
            "step_id": "boolean_cut_center_panel_detail_profiles",
            "tool_id": "modifier_boolean",
            "purpose": "Cut source-owned pointed-arch and capsule recesses into the center guard panel.",
            "params": {
                "operation": "DIFFERENCE",
                "solver": "EXACT",
                "cutters": ["center_panel_arch_cutter", "left_panel_capsule_slot_cutter", "right_panel_capsule_slot_cutter"],
                "targets": ["center_guard_panel"],
                "cleanup_cutters": True,
                "source_profile_bundle": bundle_path,
                "source_detail_profiles": selected_profiles,
            },
        },
        {
            "step_id": "array_lower_bead_strip",
            "tool_id": "modifier_array",
            "purpose": "Repeat the circular bead source across the lower molding strip.",
            "params": {
                "source_object": "lower_bead_source",
                "count": bead_count,
                "offset_m": [bead_spacing, 0.0, 0.0],
                "name_prefix": "lower_bead",
                "output_group": "railing_detail_beads",
                "source_detail_profile": "railing_circle_bead_strip_v0",
            },
        },
    ]


def gothic_panel_guard_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    params = style_params(asset)
    pier_x = number_param(params, "pier_center_x_m", 0.78)
    pier_core_size = vector_param(params, "pier_core_size_m", [0.22, 0.23, 0.76])
    pier_core_z = number_param(params, "pier_core_location_z_m", 0.54)
    base_foot_size = vector_param(params, "pier_base_foot_size_m", [0.42, 0.34, 0.08])
    base_foot_z = number_param(params, "pier_base_foot_location_z_m", 0.04)
    base_step_size = vector_param(params, "pier_base_step_size_m", [0.34, 0.30, 0.06])
    base_step_z = number_param(params, "pier_base_step_location_z_m", 0.11)
    cap_slab_size = vector_param(params, "pier_cap_slab_size_m", [0.44, 0.34, 0.09])
    cap_slab_z = number_param(params, "pier_cap_slab_location_z_m", 0.98)
    finial_vertices = int_param(params, "finial_vertices", 8, minimum=4)
    finial_radius = number_param(params, "finial_radius_m", 0.07)
    finial_depth = number_param(params, "finial_depth_m", 0.12)
    finial_z = number_param(params, "finial_location_z_m", 1.095)
    panel_size = vector_param(params, "center_guard_panel_size_m", [1.18, 0.14, 0.43])
    panel_z = number_param(params, "center_guard_panel_location_z_m", 0.56)
    coping_size = vector_param(params, "top_coping_rail_size_m", [1.40, 0.26, 0.11])
    coping_z = number_param(params, "top_coping_rail_location_z_m", 0.84)
    molding_primary_size = vector_param(params, "lower_molding_primary_size_m", [1.28, 0.20, 0.06])
    molding_primary_z = number_param(params, "lower_molding_primary_location_z_m", 0.28)
    molding_secondary_size = vector_param(params, "lower_molding_secondary_size_m", [1.10, 0.18, 0.04])
    molding_secondary_z = number_param(params, "lower_molding_secondary_location_z_m", 0.34)
    collar_size = vector_param(params, "panel_socket_collar_size_m", [0.10, 0.18, 0.38])
    collar_x = number_param(params, "panel_socket_collar_center_x_m", 0.63)
    collar_z = number_param(params, "panel_socket_collar_location_z_m", 0.55)
    inner_panel_size = vector_param(params, "front_inner_panel_size_m", [0.76, 0.034, 0.24])
    inner_panel_y = number_param(params, "front_inner_panel_surface_y_m", -0.087)
    inner_panel_z = number_param(params, "front_inner_panel_location_z_m", 0.56)
    horizontal_trim_size = vector_param(params, "inner_panel_trim_horizontal_size_m", [0.82, 0.034, 0.04])
    horizontal_trim_top_z = number_param(params, "inner_panel_trim_top_location_z_m", 0.69)
    horizontal_trim_bottom_z = number_param(params, "inner_panel_trim_bottom_location_z_m", 0.43)
    side_strip_size = vector_param(params, "side_ornament_strip_size_m", [0.05, 0.034, 0.34])
    side_strip_x = number_param(params, "side_ornament_strip_center_x_m", 0.55)
    side_strip_y = number_param(params, "side_ornament_strip_surface_y_m", -0.089)
    side_strip_z = number_param(params, "side_ornament_strip_location_z_m", 0.56)
    recess_depth_y = number_param(params, "pier_recess_depth_y_m", 0.028)
    recess_y = number_param(params, "pier_recess_surface_y_m", -0.129)
    recess_width = number_param(params, "pier_recess_width_m", 0.13)
    recess_base_z = number_param(params, "pier_recess_base_z_m", 0.38)
    recess_shoulder_z = number_param(params, "pier_recess_shoulder_z_m", 0.72)
    recess_apex_z = number_param(params, "pier_recess_apex_z_m", 0.84)
    recess_trim_width = number_param(params, "pier_recess_trim_width_m", 0.026)

    steps: list[dict[str, Any]] = []
    for side, sign in (("left", -1.0), ("right", 1.0)):
        x = round(sign * pier_x, 6)
        steps.extend(
            [
                {
                    "step_id": f"create_{side}_base_foot",
                    "tool_id": "primitive_cube_add",
                    "purpose": f"Create the {side} pier bottom square foot block.",
                    "params": {"size_m": base_foot_size, "location_m": [x, 0.0, base_foot_z], "material_role": "base"},
                },
                {
                    "step_id": f"create_{side}_base_step",
                    "tool_id": "primitive_cube_add",
                    "purpose": f"Create the {side} pier stepped plinth block.",
                    "params": {"size_m": base_step_size, "location_m": [x, 0.0, base_step_z], "material_role": "base"},
                },
                {
                    "step_id": f"create_{side}_pier_core",
                    "tool_id": "primitive_cube_add",
                    "purpose": f"Create the {side} square pier mass.",
                    "params": {"size_m": pier_core_size, "location_m": [x, 0.0, pier_core_z], "material_role": "pier"},
                },
                {
                    "step_id": f"create_{side}_cap_slab",
                    "tool_id": "primitive_cube_add",
                    "purpose": f"Create the {side} heavy cap slab.",
                    "params": {"size_m": cap_slab_size, "location_m": [x, 0.0, cap_slab_z], "material_role": "cap"},
                },
                {
                    "step_id": f"create_{side}_finial",
                    "tool_id": "primitive_cylinder_add",
                    "purpose": f"Create the {side} low-poly top finial.",
                    "params": {
                        "vertices": finial_vertices,
                        "radius_m": finial_radius,
                        "depth_m": finial_depth,
                        "location_m": [x, 0.0, finial_z],
                        "material_role": "finial",
                    },
                },
            ]
        )

    steps.extend(
        [
            {
                "step_id": "create_left_panel_socket_collar",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the left thick collar where the solid panel enters the pier.",
                "params": {"size_m": collar_size, "location_m": [-collar_x, 0.0, collar_z], "material_role": "collar"},
            },
            {
                "step_id": "create_right_panel_socket_collar",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the right thick collar where the solid panel enters the pier.",
                "params": {"size_m": collar_size, "location_m": [collar_x, 0.0, collar_z], "material_role": "collar"},
            },
            {
                "step_id": "create_center_guard_panel",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the solid rectangular guard panel between the piers.",
                "params": {"size_m": panel_size, "location_m": [0.0, 0.0, panel_z], "material_role": "panel"},
            },
            {
                "step_id": "create_top_coping_rail",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the thick top coping rail crossing the panel span.",
                "params": {"size_m": coping_size, "location_m": [0.0, 0.0, coping_z], "material_role": "coping"},
            },
            {
                "step_id": "create_lower_molding_primary",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the lower primary molding band below the guard panel.",
                "params": {"size_m": molding_primary_size, "location_m": [0.0, 0.0, molding_primary_z], "material_role": "trim"},
            },
            {
                "step_id": "create_lower_molding_secondary",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the second lower molding band below the guard panel.",
                "params": {"size_m": molding_secondary_size, "location_m": [0.0, 0.0, molding_secondary_z], "material_role": "trim"},
            },
            {
                "step_id": "create_front_inner_panel",
                "tool_id": "primitive_cube_add",
                "purpose": "Create a raised center face panel on the reference-facing side.",
                "params": {"size_m": inner_panel_size, "location_m": [0.0, inner_panel_y, inner_panel_z], "material_role": "panel"},
            },
            {
                "step_id": "create_front_inner_panel_top_trim",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the top trim bar around the raised center panel.",
                "params": {"size_m": horizontal_trim_size, "location_m": [0.0, inner_panel_y, horizontal_trim_top_z], "material_role": "trim"},
            },
            {
                "step_id": "create_front_inner_panel_bottom_trim",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the bottom trim bar around the raised center panel.",
                "params": {"size_m": horizontal_trim_size, "location_m": [0.0, inner_panel_y, horizontal_trim_bottom_z], "material_role": "trim"},
            },
            {
                "step_id": "create_left_panel_side_strip",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the left repeated side ornament strip beside the panel.",
                "params": {"size_m": side_strip_size, "location_m": [-side_strip_x, side_strip_y, side_strip_z], "material_role": "trim"},
            },
            {
                "step_id": "create_right_panel_side_strip",
                "tool_id": "primitive_cube_add",
                "purpose": "Create the right repeated side ornament strip beside the panel.",
                "params": {"size_m": side_strip_size, "location_m": [side_strip_x, side_strip_y, side_strip_z], "material_role": "trim"},
            },
        ]
    )

    trim_half = recess_trim_width * 0.5
    for side, sign in (("left", -1.0), ("right", 1.0)):
        center_x = round(sign * pier_x, 6)
        half_recess = recess_width * 0.5
        recess_points = [
            [center_x - half_recess, recess_base_z],
            [center_x + half_recess, recess_base_z],
            [center_x + half_recess, recess_shoulder_z],
            [center_x, recess_apex_z],
            [center_x - half_recess, recess_shoulder_z],
        ]
        trim_points = [
            [center_x - half_recess - trim_half, recess_base_z - trim_half],
            [center_x + half_recess + trim_half, recess_base_z - trim_half],
            [center_x + half_recess + trim_half, recess_shoulder_z + trim_half],
            [center_x, recess_apex_z + trim_half],
            [center_x - half_recess - trim_half, recess_shoulder_z + trim_half],
        ]
        steps.extend(
            [
                gothic_panel_guard_mesh_step(
                    f"create_{side}_pier_arch_recess_shadow",
                    f"Create the {side} shallow pointed-arch recess as a low-vertex shadow prism.",
                    recess_points,
                    y_center=recess_y,
                    depth_y=recess_depth_y,
                    material_role="recess",
                ),
                gothic_panel_guard_mesh_step(
                    f"create_{side}_pier_arch_raised_trim",
                    f"Create the {side} raised pointed-arch trim as a low-vertex outline plate.",
                    trim_points,
                    y_center=round(recess_y - recess_depth_y, 6),
                    depth_y=recess_depth_y,
                    material_role="trim",
                ),
            ]
        )

    join_objects = [
        "left_base_foot",
        "left_base_step",
        "left_pier_core",
        "left_cap_slab",
        "left_finial",
        "right_base_foot",
        "right_base_step",
        "right_pier_core",
        "right_cap_slab",
        "right_finial",
        "left_panel_socket_collar",
        "right_panel_socket_collar",
        "center_guard_panel",
        "top_coping_rail",
        "lower_molding_primary",
        "lower_molding_secondary",
        "front_inner_panel",
        "front_inner_panel_top_trim",
        "front_inner_panel_bottom_trim",
        "left_panel_side_strip",
        "right_panel_side_strip",
        "left_pier_arch_recess_shadow",
        "left_pier_arch_raised_trim",
        "right_pier_arch_recess_shadow",
        "right_pier_arch_raised_trim",
    ]
    if "railing_detail_profile_stack" in asset.get("features", []):
        join_objects.extend(["railing_detail_recesses", "railing_detail_trim", "railing_detail_beads"])
    steps.append(
        {
            "step_id": "join_gothic_panel_guard_blocks",
            "tool_id": "join_objects",
            "purpose": "Join piers, collars, panel, coping, molding, trim, recess plates, and source-owned 2D detail profiles into one reference-led guard asset.",
            "params": {
                "objects": join_objects,
                "reference_packet": require_string(params.get("reference_packet"), f"{asset['asset_id']}.style_parameters.reference_packet"),
                "source_component_count": 9,
                "socket_collar_composition": True,
                "railing_detail_profile_stack": "railing_detail_profile_stack" in asset.get("features", []),
            },
        }
    )
    return steps


def rectangular_frame_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    params = style_params(asset)
    dims = dimensions(asset)
    asset_family = require_string(asset.get("asset_family"), f"{asset['asset_id']}.asset_family")
    frame_label = "door" if asset_family == "door_frame" else "window"
    width = positive_number(params.get("frame_width_m", dims["width"]), f"{asset['asset_id']}.style_parameters.frame_width_m")
    depth = positive_number(params.get("frame_depth_m", dims["depth"]), f"{asset['asset_id']}.style_parameters.frame_depth_m")
    height = positive_number(params.get("frame_height_m", dims["height"]), f"{asset['asset_id']}.style_parameters.frame_height_m")
    side_width = positive_number(params.get("side_member_width_m", 0.14), f"{asset['asset_id']}.style_parameters.side_member_width_m")
    top_height = positive_number(params.get("top_member_height_m", side_width), f"{asset['asset_id']}.style_parameters.top_member_height_m")
    bottom_height = positive_number(params.get("bottom_member_height_m", top_height), f"{asset['asset_id']}.style_parameters.bottom_member_height_m")
    if side_width * 2.0 >= width:
        fail(f"{asset['asset_id']}.style_parameters side members must leave a center opening")
    if top_height + bottom_height >= height:
        fail(f"{asset['asset_id']}.style_parameters top and bottom members must leave a center opening")
    jamb_height = round(height - top_height - bottom_height, 6)
    left_x = round(-width * 0.5 + side_width * 0.5, 6)
    right_x = round(width * 0.5 - side_width * 0.5, 6)
    bottom_z = round(bottom_height * 0.5, 6)
    jamb_z = round(bottom_height + jamb_height * 0.5, 6)
    top_z = round(height - top_height * 0.5, 6)
    return [
        {"step_id": f"create_{frame_label}_left_jamb", "tool_id": "primitive_cube_add", "purpose": f"Create the left vertical {frame_label} jamb.", "params": {"size_m": [side_width, depth, jamb_height], "location_m": [left_x, 0.0, jamb_z]}},
        {"step_id": f"create_{frame_label}_right_jamb", "tool_id": "primitive_cube_add", "purpose": f"Create the right vertical {frame_label} jamb.", "params": {"size_m": [side_width, depth, jamb_height], "location_m": [right_x, 0.0, jamb_z]}},
        {"step_id": f"create_{frame_label}_sill", "tool_id": "primitive_cube_add", "purpose": f"Create the lower {frame_label} sill block.", "params": {"size_m": [width, depth, bottom_height], "location_m": [0.0, 0.0, bottom_z]}},
        {"step_id": f"create_{frame_label}_header", "tool_id": "primitive_cube_add", "purpose": f"Create the upper {frame_label} header block.", "params": {"size_m": [width, depth, top_height], "location_m": [0.0, 0.0, top_z]}},
        {
            "step_id": f"join_{frame_label}_frame_blocks",
            "tool_id": "join_objects",
            "purpose": f"Join the four {frame_label} frame blocks into one deterministic frame mesh.",
            "params": {
                "objects": [f"{frame_label}_left_jamb", f"{frame_label}_right_jamb", f"{frame_label}_sill", f"{frame_label}_header"],
                "opening_m": [round(width - side_width * 2.0, 6), round(height - bottom_height - top_height, 6)],
            },
        },
    ]


def profile_operation_stack_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    stack = require_object(asset.get("profile_operation_stack"), f"{asset_id}.profile_operation_stack")
    steps: list[dict[str, Any]] = []
    for part_index, item in enumerate(require_list(stack.get("parts"), f"{asset_id}.profile_operation_stack.parts")):
        part = require_object(item, f"{asset_id}.profile_operation_stack.parts[{part_index}]")
        part_id = require_string(part.get("part_id"), f"{asset_id}.profile_operation_stack.parts[{part_index}].part_id")
        profile = require_string(part.get("profile"), f"{asset_id}.profile_operation_stack.parts[{part_index}].profile")
        operation = require_string(part.get("operation"), f"{asset_id}.profile_operation_stack.parts[{part_index}].operation")
        if operation == "extrude" and profile in {"square", "rectangle"}:
            steps.append(
                {
                    "step_id": f"create_{part_id}",
                    "tool_id": "primitive_cube_add",
                    "purpose": f"Create `{part_id}` from a {profile} profile extrusion.",
                    "params": {
                        "size_m": positive_vector(part.get("size_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].size_m", 3),
                        "location_m": finite_vector(part.get("location_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].location_m", 3),
                        "source_profile": profile,
                        "source_operation": operation,
                        "material_role": part.get("material_role", "default"),
                    },
                }
            )
        elif operation == "extrude" and profile == "circle":
            vertices = part.get("vertices")
            if not isinstance(vertices, int) or isinstance(vertices, bool):
                fail(f"{asset_id}.profile_operation_stack.parts[{part_index}].vertices must be an integer")
            steps.append(
                {
                    "step_id": f"create_{part_id}",
                    "tool_id": "primitive_cylinder_add",
                    "purpose": f"Create `{part_id}` from a low-vertex circle profile extrusion.",
                    "params": {
                        "vertices": vertices,
                        "radius_m": positive_number(part.get("radius_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].radius_m"),
                        "depth_m": positive_number(part.get("depth_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].depth_m"),
                        "location_m": finite_vector(part.get("location_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].location_m", 3),
                        "source_profile": profile,
                        "source_operation": operation,
                        "material_role": part.get("material_role", "default"),
                    },
                }
            )
        elif operation == "array_radial":
            source_part_id = require_string(part.get("source_part_id"), f"{asset_id}.profile_operation_stack.parts[{part_index}].source_part_id")
            count = part.get("count")
            if not isinstance(count, int) or isinstance(count, bool):
                fail(f"{asset_id}.profile_operation_stack.parts[{part_index}].count must be an integer")
            steps.extend(
                [
                    {
                        "step_id": f"create_{source_part_id}",
                        "tool_id": "primitive_cube_add",
                        "purpose": f"Create `{source_part_id}` before radial profile-operation expansion.",
                        "params": {
                            "size_m": positive_vector(part.get("source_size_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].source_size_m", 3),
                            "location_m": finite_vector(part.get("source_location_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].source_location_m", 3),
                            "source_profile": profile,
                            "source_operation": operation,
                            "material_role": part.get("material_role", "default"),
                        },
                    },
                    {
                        "step_id": f"duplicate_{part_id}_radially",
                        "tool_id": "object_duplicate_radial",
                        "purpose": f"Expand `{source_part_id}` with deterministic radial operation `{part_id}`.",
                        "params": {
                            "source_object": source_part_id,
                            "count": count,
                            "axis": require_string(stack.get("axis"), f"{asset_id}.profile_operation_stack.axis"),
                            "radius_m": positive_number(part.get("radius_m"), f"{asset_id}.profile_operation_stack.parts[{part_index}].radius_m"),
                            "source_profile": profile,
                            "source_operation": operation,
                        },
                    },
                ]
            )
        else:
            fail(f"{asset_id}.profile_operation_stack.parts[{part_index}] uses unsupported profile/operation pair `{profile}/{operation}`")
    join = require_object(stack.get("join"), f"{asset_id}.profile_operation_stack.join")
    steps.append(
        {
            "step_id": require_string(join.get("step_id"), f"{asset_id}.profile_operation_stack.join.step_id"),
            "tool_id": "join_objects",
            "purpose": "Join profile-operation stack parts into one deterministic asset.",
            "params": {
                "objects": require_string_list(join.get("objects"), f"{asset_id}.profile_operation_stack.join.objects"),
                "profile_transition_sequence": require_string_list(
                    join.get("profile_transition_sequence"),
                    f"{asset_id}.profile_operation_stack.join.profile_transition_sequence",
                ),
                "source_operation": "profile_operation_stack",
                "grammar_id": require_string(stack.get("grammar_id"), f"{asset_id}.profile_operation_stack.grammar_id"),
            },
        }
    )
    return steps


def resolved_finish_tool_stack(asset: dict[str, Any]) -> dict[str, Any]:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    return require_object(asset.get("_resolved_finish_tool_stack"), f"{asset_id}._resolved_finish_tool_stack")


def finish_tool_stack_steps(asset: dict[str, Any]) -> list[dict[str, Any]]:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    stack = resolved_finish_tool_stack(asset)
    steps: list[dict[str, Any]] = []
    for entry_index, item in enumerate(require_list(stack.get("sequence"), f"{asset_id}.finish_tool_stack.sequence")):
        entry = require_object(item, f"{asset_id}.finish_tool_stack.sequence[{entry_index}]")
        feature = require_string(entry.get("feature"), f"{asset_id}.finish_tool_stack.sequence[{entry_index}].feature")
        if feature not in FINISH_FEATURES:
            fail(f"{asset_id}.finish_tool_stack.sequence[{entry_index}] uses unknown finish feature `{feature}`")
        steps.extend(feature_steps(asset, feature))
    return steps


def feature_steps(asset: dict[str, Any], feature: str) -> list[dict[str, Any]]:
    params = style_params(asset)
    if feature == "profile_operation_stack":
        return profile_operation_stack_steps(asset)
    if feature == "railing_detail_profile_stack":
        return railing_detail_profile_steps(asset)
    if feature == "profiled_plinth_base_detail":
        return profiled_plinth_base_detail_steps(asset)
    if feature == "finish_tool_stack":
        return finish_tool_stack_steps(asset)
    if feature == "stepped_square_base":
        base_foot_size = vector_param(params, "base_foot_size_m", [0.52, 0.52, 0.10])
        base_mid_size = vector_param(params, "base_mid_size_m", [0.44, 0.44, 0.06])
        base_top_size = vector_param(params, "base_top_size_m", [0.34, 0.34, 0.06])
        cap_neck_size = vector_param(params, "cap_neck_size_m", [0.34, 0.34, 0.07])
        cap_top_size = vector_param(params, "cap_top_size_m", [0.50, 0.50, 0.13])
        post_core_height = number_param(params, "post_core_height_m", 0.96)
        base_foot_z = round(base_foot_size[2] * 0.5, 6)
        base_mid_z = round(base_foot_size[2] + base_mid_size[2] * 0.5, 6)
        base_top_z = round(base_foot_size[2] + base_mid_size[2] + base_top_size[2] * 0.5, 6)
        cap_neck_z = round(base_foot_size[2] + base_mid_size[2] + base_top_size[2] + post_core_height + cap_neck_size[2] * 0.5, 6)
        cap_top_z = round(base_foot_size[2] + base_mid_size[2] + base_top_size[2] + post_core_height + cap_neck_size[2] + cap_top_size[2] * 0.5, 6)
        base_steps = [
            {"step_id": "create_base_foot", "tool_id": "primitive_cube_add", "purpose": "Create the bottom square foot block.", "params": {"size_m": base_foot_size, "location_m": [0.0, 0.0, base_foot_z]}},
            {"step_id": "create_base_mid_step", "tool_id": "primitive_cube_add", "purpose": "Create the middle stepped plinth block.", "params": {"size_m": base_mid_size, "location_m": [0.0, 0.0, base_mid_z]}},
            {"step_id": "create_base_top_step", "tool_id": "primitive_cube_add", "purpose": "Create the top base transition block.", "params": {"size_m": base_top_size, "location_m": [0.0, 0.0, base_top_z], "base_step_count": params.get("base_step_count", 3)}},
        ]
        if not bool_param(params, "include_cap_blocks", True):
            return base_steps
        return [
            *base_steps,
            {"step_id": "create_cap_neck", "tool_id": "primitive_cube_add", "purpose": "Create the upper necking block under the cap.", "params": {"size_m": cap_neck_size, "location_m": [0.0, 0.0, cap_neck_z]}},
            {"step_id": "create_cap_top", "tool_id": "primitive_cube_add", "purpose": "Create the square top cap block.", "params": {"size_m": cap_top_size, "location_m": [0.0, 0.0, cap_top_z]}},
        ]
    if feature == "round_transition_ring":
        bottom_radius = number_param(params, "bottom_transition_radius_m", 0.24)
        top_radius = number_param(params, "top_transition_radius_m", bottom_radius)
        bottom_depth = number_param(params, "bottom_transition_depth_m", 0.08)
        top_depth = number_param(params, "top_transition_depth_m", bottom_depth)
        bottom_z = number_param(params, "bottom_transition_location_z_m", 0.26)
        top_z = number_param(params, "top_transition_location_z_m", 1.16)
        bottom_vertices = int_param(params, "bottom_transition_vertices", 8, minimum=4)
        top_vertices = int_param(params, "top_transition_vertices", bottom_vertices, minimum=4)
        return [
            {"step_id": "create_bottom_transition_ring", "tool_id": "primitive_cylinder_add", "purpose": "Create the low-vertex circular transition from square base to shaft.", "params": {"vertices": bottom_vertices, "radius_m": bottom_radius, "depth_m": bottom_depth, "location_m": [0.0, 0.0, bottom_z]}},
            {"step_id": "create_top_transition_ring", "tool_id": "primitive_cylinder_add", "purpose": "Create the low-vertex circular transition from shaft to square cap.", "params": {"vertices": top_vertices, "radius_m": top_radius, "depth_m": top_depth, "location_m": [0.0, 0.0, top_z]}},
        ]
    if feature == "star_or_fluted_shaft":
        shaft_vertices = int_param(params, "shaft_vertices", 8, minimum=4)
        shaft_radius = number_param(params, "shaft_radius_m", 0.18)
        shaft_height = number_param(params, "shaft_height_m", 0.82)
        shaft_z = number_param(params, "shaft_location_z_m", 0.71)
        rib_size = vector_param(params, "column_rib_source_size_m", [0.025, 0.04, 0.80])
        rib_radius = number_param(params, "column_rib_radius_m", 0.21)
        rib_z = number_param(params, "column_rib_location_z_m", shaft_z)
        rib_count = int_param(params, "column_rib_count", 8, minimum=4)
        return [
            {"step_id": "create_column_shaft_core", "tool_id": "primitive_cylinder_add", "purpose": "Create the low-vertex central column shaft.", "params": {"vertices": shaft_vertices, "radius_m": shaft_radius, "depth_m": shaft_height, "location_m": [0.0, 0.0, shaft_z]}},
            {"step_id": "create_column_single_rib_source", "tool_id": "primitive_cube_add", "purpose": "Create one blocky shaft rib before radial duplication.", "params": {"size_m": rib_size, "location_m": [rib_radius, 0.0, rib_z]}},
            {"step_id": "duplicate_column_ribs_radially", "tool_id": "object_duplicate_radial", "purpose": "Duplicate blocky shaft ribs around the column core.", "params": {"source_object": "column_single_rib_source", "count": rib_count, "axis": "z", "radius_m": rib_radius}},
        ]
    if feature == "square_top_cap":
        base_foot_size = vector_param(params, "base_foot_size_m", [0.52, 0.52, 0.10])
        base_mid_size = vector_param(params, "base_mid_size_m", [0.44, 0.44, 0.06])
        base_top_size = vector_param(params, "base_top_size_m", [0.34, 0.34, 0.06])
        cap_neck_size = vector_param(params, "cap_neck_size_m", [0.34, 0.34, 0.07])
        cap_top_size = vector_param(params, "cap_top_size_m", [0.50, 0.50, 0.13])
        post_core_height = number_param(params, "post_core_height_m", 0.96)
        default_cap_neck_z = round(base_foot_size[2] + base_mid_size[2] + base_top_size[2] + post_core_height + cap_neck_size[2] * 0.5, 6)
        default_cap_top_z = round(base_foot_size[2] + base_mid_size[2] + base_top_size[2] + post_core_height + cap_neck_size[2] + cap_top_size[2] * 0.5, 6)
        cap_neck_z = number_param(params, "cap_neck_location_z_m", default_cap_neck_z)
        cap_top_z = number_param(params, "cap_top_location_z_m", default_cap_top_z)
        return [
            {"step_id": "create_cap_neck", "tool_id": "primitive_cube_add", "purpose": "Create the square necking block above the upper transition ring.", "params": {"size_m": cap_neck_size, "location_m": [0.0, 0.0, cap_neck_z]}},
            {"step_id": "create_cap_top", "tool_id": "primitive_cube_add", "purpose": "Create the square top cap block.", "params": {"size_m": cap_top_size, "location_m": [0.0, 0.0, cap_top_z]}},
            {
                "step_id": "join_column_parts",
                "tool_id": "join_objects",
                "purpose": "Join square base, circular transitions, fluted shaft, and square cap into one deterministic column.",
                "params": {
                    "objects": ["base", "bottom_transition_ring", "column_shaft_core", "ribs", "top_transition_ring", "cap"],
                    "profile_transition_sequence": ["square_base", "circle_ring", "fluted_shaft", "circle_ring", "square_cap"],
                },
            },
        ]
    if feature == "ribbed_post_core":
        core_size = vector_param(params, "post_core_size_m", [0.24, 0.24, 0.96])
        core_location_z = number_param(params, "post_core_location_z_m", 0.67)
        rib_size = vector_param(params, "rib_source_size_m", [params.get("rib_depth_m", 0.025), 0.035, 0.90])
        rib_radius = number_param(params, "rib_radius_m", 0.145)
        rib_location_z = number_param(params, "rib_location_z_m", 0.68)
        return [
            {"step_id": "create_post_core", "tool_id": "primitive_cube_add", "purpose": "Create the central square post core.", "params": {"size_m": core_size, "location_m": [0.0, 0.0, core_location_z]}},
            {"step_id": "create_single_rib_source", "tool_id": "primitive_cube_add", "purpose": "Create one narrow rib source block before radial duplication.", "params": {"size_m": rib_size, "location_m": [rib_radius, 0.0, rib_location_z]}},
            {"step_id": "duplicate_ribs_radially", "tool_id": "object_duplicate_radial", "purpose": "Duplicate the rib source around the post core.", "params": {"count": params.get("rib_count", 12), "axis": "z", "radius_m": rib_radius}},
        ]
    if feature == "rectangular_frame_blocks":
        return rectangular_frame_steps(asset)
    if feature == "rail_segment_blocks":
        return rail_segment_steps(asset)
    if feature == "gothic_panel_guard_blocks":
        return gothic_panel_guard_steps(asset)
    if feature in {"east_west_rail_sockets", "rail_sockets"}:
        socket_size = vector_param(params, "rail_socket_size_m", [0.16, 0.22, params.get("rail_socket_height_m", 0.26)])
        socket_x = number_param(params, "rail_socket_x_m", 0.18)
        socket_z = number_param(params, "rail_socket_z_m", 0.70)
        socket_surface_x = number_param(params, "rail_socket_surface_x_m", 0.12)
        return [
            {"step_id": "create_east_socket_cutter", "tool_id": "primitive_cube_add", "purpose": "Create the east rail socket cutter volume.", "params": {"size_m": socket_size, "location_m": [socket_x, 0.0, socket_z]}},
            {"step_id": "create_west_socket_cutter", "tool_id": "primitive_cube_add", "purpose": "Create the west rail socket cutter volume.", "params": {"size_m": socket_size, "location_m": [-socket_x, 0.0, socket_z]}},
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
                        "surface_x_m": socket_surface_x,
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
        material_map = {
            "base": "gothic_stone_dark",
            "cap": "gothic_stone_cap",
            "shaft": "gothic_stone",
            "rib": "gothic_stone_highlight",
            "socket": "gothic_stone_shadow",
            "socket_shadow": "gothic_stone_shadow",
        }
        if asset.get("asset_family") == "column":
            material_map = {
                "base": "gothic_stone_dark",
                "cap": "gothic_stone_cap",
                "transition": "gothic_stone_transition",
                "shaft": "gothic_stone",
                "rib": "gothic_stone_highlight",
                "default": "gothic_stone",
            }
        if asset.get("asset_family") in {"window_frame", "door_frame"}:
            material_map = {
                "frame": "gothic_stone_frame",
                "default": "gothic_stone_frame",
            }
        if asset.get("asset_family") == "rail_segment":
            material_map = {
                "body": "gothic_stone",
                "base": "gothic_stone_dark",
                "cap": "gothic_stone_cap",
                "connector": "gothic_stone_shadow",
                "rib": "gothic_stone_highlight",
                "default": "gothic_stone",
            }
        if asset.get("asset_family") == "guard_panel":
            material_map = {
                "pier": "gothic_stone_pier",
                "base": "gothic_stone_dark",
                "cap": "gothic_stone_cap",
                "panel": "gothic_stone_panel",
                "coping": "gothic_stone_coping",
                "trim": "gothic_stone_trim",
                "recess": "gothic_stone_recess",
                "finial": "gothic_stone_finial",
                "collar": "gothic_stone_collar",
                "default": "gothic_stone",
            }
        if asset.get("asset_family") == "profile_detail":
            material_map = {
                "base": "gothic_stone_dark",
                "trim": "gothic_stone_trim",
                "default": "gothic_stone",
            }
        return [
            {"step_id": "add_stone_displacement", "tool_id": "modifier_displace", "purpose": "Add restrained procedural stone surface variation.", "params": {"strength_m": 0.006, "texture": "stone_noise"}},
            {"step_id": "create_stone_material", "tool_id": "material_principled_shader", "purpose": "Create the base gothic stone material.", "params": {"base_color": [0.48, 0.46, 0.39], "roughness": 0.82, "metallic": 0.0}},
            {"step_id": "add_stone_noise_texture", "tool_id": "procedural_noise_texture", "purpose": "Add deterministic stone color and roughness variation.", "params": {"scale": params.get("stone_noise_scale", 38.0), "detail": 9, "roughness": 0.58, "seed": 19}},
            {"step_id": "add_stone_bump_map", "tool_id": "procedural_bump_map", "purpose": "Connect subtle bump detail for close views.", "params": {"height_source": "stone_noise", "strength": 0.07}},
            {"step_id": "assign_material_regions", "tool_id": "material_assign_by_part", "purpose": "Assign material indexes by generated part role.", "params": {"material_map": material_map}},
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
        preview = {}
        if "_resolved_finish_tool_stack" in asset:
            finish_stack = resolved_finish_tool_stack(asset)
            preview = require_object(finish_stack.get("preview", {}), f"{asset['asset_id']}.finish_tool_stack.preview")
        visibility = params.get("preview_visibility", preview.get("visibility", "scene_with_validation_helpers"))
        if not isinstance(visibility, str) or visibility not in {"final_asset_only", "scene_with_validation_helpers"}:
            fail(f"{asset['asset_id']}.preview_visibility uses unsupported mode `{visibility}`")
        hide_helpers = params.get("hide_validation_helpers", preview.get("hide_validation_helpers", visibility == "final_asset_only"))
        if not isinstance(hide_helpers, bool):
            fail(f"{asset['asset_id']}.hide_validation_helpers must be a boolean")
        return [
            {
                "step_id": "render_workbench_asset_preview",
                "tool_id": "render_workbench_preview",
                "purpose": "Render a neutral final-asset preview after execution.",
                "params": {
                    "resolution": [1600, 1100],
                    "hide_connectors": False,
                    "preview_visibility": visibility,
                    "hide_validation_helpers": hide_helpers,
                },
            },
            {"step_id": "export_game_ready_glb", "tool_id": "export_gltf", "purpose": "Export the executed asset as GLB when export is requested.", "params": {"format": "GLB", "apply_modifiers": True}},
        ]
    fail(f"{asset['asset_id']} uses unknown feature `{feature}`")


def source_terms_for_asset(asset: dict[str, Any]) -> dict[str, Any]:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    features = require_list(asset.get("features"), f"{asset_id}.features")
    result: dict[str, Any] = {"geometry": [], "profiles": [], "operators": []}

    def append_unique(field: str, values: list[str]) -> None:
        current = result[field]
        for value in values:
            if value not in current:
                current.append(value)

    if "profile_operation_stack" in features:
        stack = require_object(asset.get("profile_operation_stack"), f"{asset_id}.profile_operation_stack")
        append_unique("geometry", require_string_list(stack.get("geometry_terms_used"), f"{asset_id}.profile_operation_stack.geometry_terms_used"))
        append_unique("profiles", require_string_list(stack.get("profile_terms"), f"{asset_id}.profile_operation_stack.profile_terms"))
        append_unique("operators", require_string_list(stack.get("operations"), f"{asset_id}.profile_operation_stack.operations"))
        result["profile_operation_stack"] = {
            "grammar_id": require_string(stack.get("grammar_id"), f"{asset_id}.profile_operation_stack.grammar_id"),
            "axis": require_string(stack.get("axis"), f"{asset_id}.profile_operation_stack.axis"),
            "sequence": require_string_list(stack.get("sequence"), f"{asset_id}.profile_operation_stack.sequence"),
        }
    if "gothic_panel_guard_blocks" in features:
        params = style_params(asset)
        result["reference_packet"] = require_string(params.get("reference_packet"), f"{asset_id}.style_parameters.reference_packet")
        append_unique("geometry", ["rectangle", "pointed_arch_profile", "extrude", "compound_asset", "bevel_edges"])
        append_unique("profiles", ["rectangle", "pointed_arch_profile"])
        append_unique("operators", ["extrude", "compound_asset", "bevel_edges"])
    if "railing_detail_profile_stack" in features:
        params = style_params(asset)
        bundle_path = repo_relative_path(
            params.get("railing_detail_profile_bundle", repo_display_path(DEFAULT_RAILING_DETAIL_PROFILES)),
            f"{asset_id}.style_parameters.railing_detail_profile_bundle",
        )
        bundle = load_json(bundle_path)
        selected_profile_ids = require_string_list(params.get("railing_detail_profile_ids"), f"{asset_id}.style_parameters.railing_detail_profile_ids")
        profile_map = {}
        for index, profile_value in enumerate(require_list(bundle.get("profiles"), f"{asset_id}.railing_detail_profile_bundle.profiles")):
            profile = require_object(profile_value, f"{asset_id}.railing_detail_profile_bundle.profiles[{index}]")
            profile_map[require_string(profile.get("profile_id"), f"{asset_id}.railing_detail_profile_bundle.profiles[{index}].profile_id")] = profile
        detail_profiles = []
        tool_ids = []
        placement_regions = []
        for profile_id in selected_profile_ids:
            profile = require_object(profile_map.get(profile_id), f"{asset_id}.railing_detail_profile_stack.{profile_id}")
            append_unique("geometry", require_string_list(profile.get("geometry_terms_used"), f"{profile_id}.geometry_terms_used"))
            append_unique("profiles", require_string_list(profile.get("profile_terms"), f"{profile_id}.profile_terms"))
            append_unique("operators", require_string_list(profile.get("operations"), f"{profile_id}.operations"))
            detail_profiles.append(profile_id)
            for placement_value in require_list(profile.get("where_used"), f"{profile_id}.where_used"):
                placement = require_object(placement_value, f"{profile_id}.where_used[]")
                if placement.get("target_asset_family") == asset.get("asset_family"):
                    placement_regions.append(
                        {
                            "profile_id": profile_id,
                            "placement_region": require_string(placement.get("placement_region"), f"{profile_id}.placement_region"),
                            "detail_role": require_string(placement.get("detail_role"), f"{profile_id}.detail_role"),
                            "application_method": require_string(placement.get("application_method"), f"{profile_id}.application_method"),
                        }
                    )
            for step_value in require_list(profile.get("blender_tool_sequence"), f"{profile_id}.blender_tool_sequence"):
                step = require_object(step_value, f"{profile_id}.blender_tool_sequence[]")
                tool_id = require_string(step.get("tool_id"), f"{profile_id}.blender_tool_sequence.tool_id")
                if tool_id not in tool_ids:
                    tool_ids.append(tool_id)
        result["railing_detail_profile_stack"] = {
            "bundle_path": repo_display_path(bundle_path),
            "profile_ids": detail_profiles,
            "placement_regions": placement_regions,
            "tool_ids": tool_ids,
            "compile_mode": "guard_panel_cut_shadow_and_trim_v0",
        }
    if "profiled_plinth_base_detail" in features:
        params = style_params(asset)
        bundle_path = repo_relative_path(
            params.get("profiled_plinth_profile_bundle", repo_display_path(DEFAULT_RAILING_DETAIL_PROFILES)),
            f"{asset_id}.style_parameters.profiled_plinth_profile_bundle",
        )
        bundle = load_json(bundle_path)
        profile_id = require_string(
            params.get("profiled_plinth_profile_id", PROFILED_PLINTH_BASE_DETAIL_PROFILE_ID),
            f"{asset_id}.style_parameters.profiled_plinth_profile_id",
        )
        profile_map = profile_map_from_bundle(bundle, f"{asset_id}.profiled_plinth_profile_bundle")
        profile = require_object(profile_map.get(profile_id), f"{asset_id}.profiled_plinth_base_detail.{profile_id}")
        append_unique("geometry", require_string_list(profile.get("geometry_terms_used"), f"{profile_id}.geometry_terms_used"))
        append_unique("profiles", require_string_list(profile.get("profile_terms"), f"{profile_id}.profile_terms"))
        append_unique("operators", require_string_list(profile.get("operations"), f"{profile_id}.operations"))
        tool_ids = []
        for step_value in require_list(profile.get("blender_tool_sequence"), f"{profile_id}.blender_tool_sequence"):
            step = require_object(step_value, f"{profile_id}.blender_tool_sequence[]")
            tool_id = require_string(step.get("tool_id"), f"{profile_id}.blender_tool_sequence.tool_id")
            if tool_id not in tool_ids:
                tool_ids.append(tool_id)
        result["profiled_plinth_base_detail"] = {
            "bundle_path": repo_display_path(bundle_path),
            "profile_id": profile_id,
            "compile_mode": "single_custom_polygon_extrusion_v0",
            "source_control_point_count": 14,
            "tool_ids": tool_ids,
        }
    if "finish_tool_stack" in features:
        finish_stack = resolved_finish_tool_stack(asset)
        append_unique("geometry", require_string_list(finish_stack.get("geometry_terms_used"), f"{asset_id}.finish_tool_stack.geometry_terms_used"))
        append_unique("operators", require_string_list(finish_stack.get("operations"), f"{asset_id}.finish_tool_stack.operations"))
        sequence_features = []
        tool_ids = []
        for entry_index, item in enumerate(require_list(finish_stack.get("sequence"), f"{asset_id}.finish_tool_stack.sequence")):
            entry = require_object(item, f"{asset_id}.finish_tool_stack.sequence[{entry_index}]")
            sequence_features.append(require_string(entry.get("feature"), f"{asset_id}.finish_tool_stack.sequence[{entry_index}].feature"))
            for tool_id in require_string_list(entry.get("tool_ids"), f"{asset_id}.finish_tool_stack.sequence[{entry_index}].tool_ids"):
                if tool_id not in tool_ids:
                    tool_ids.append(tool_id)
        result["finish_tool_stack"] = {
            "stack_id": require_string(finish_stack.get("stack_id"), f"{asset_id}.finish_tool_stack.stack_id"),
            "grammar_id": require_string(finish_stack.get("grammar_id"), f"{asset_id}.finish_tool_stack.grammar_id"),
            "sequence": sequence_features,
            "tool_ids": tool_ids,
        }
    return result


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


def enforce_sequence_policy(asset: dict[str, Any], steps: list[dict[str, Any]], policy_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    asset_id = require_string(asset.get("asset_id"), "asset_id")
    asset_family = require_string(asset.get("asset_family"), f"{asset_id}.asset_family")
    if asset_family not in policy_map:
        fail(f"{asset_id}.asset_family `{asset_family}` has no sequence policy")
    policy = policy_map[asset_family]
    for feature_index, feature in enumerate(require_list(asset.get("features"), f"{asset_id}.features")):
        feature_id = require_string(feature, f"{asset_id}.features[{feature_index}]")
        if feature_id not in policy["allowed_features"]:
            fail(f"{asset_id}.features[{feature_index}] `{feature_id}` is not allowed by the {asset_family} sequence policy")

    observed_stages: list[str] = []
    tool_positions: dict[str, list[int]] = {}
    for step in steps:
        stage = step["stage"]
        tool_id = step["tool_id"]
        if stage not in observed_stages:
            observed_stages.append(stage)
        if tool_id in policy["forbidden_tools"]:
            fail(f"{asset_id}.{step['step_id']} uses forbidden {asset_family} tool `{tool_id}`")
        allowed_tools = policy["allowed_tools_by_stage"].get(stage, set())
        if tool_id not in allowed_tools:
            fail(f"{asset_id}.{step['step_id']} uses `{tool_id}` outside the {asset_family} sequence policy")
        tool_positions.setdefault(tool_id, []).append(step["order"])

    for stage in policy["required_stage_coverage"]:
        if stage not in observed_stages:
            fail(f"{asset_id} missing sequence-policy stage `{stage}`")
    missing_tools = sorted(tool for tool in policy["required_tools"] if tool not in tool_positions)
    if missing_tools:
        fail(f"{asset_id} missing sequence-policy required tools: {missing_tools}")
    for constraint in policy["tool_order_constraints"]:
        before = constraint["before"]
        after = constraint["after"]
        if before in tool_positions and after in tool_positions and min(tool_positions[before]) >= min(tool_positions[after]):
            fail(f"{asset_id} sequence policy requires `{before}` before `{after}`")
    return policy


def compile_asset_plan(
    asset: dict[str, Any],
    tool_map: dict[str, dict[str, Any]],
    dictionary: dict[str, Any],
    sequence_policy: dict[str, Any],
    policy_map: dict[str, dict[str, Any]],
    recipe_path: Path,
) -> dict[str, Any]:
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
    family_policy = enforce_sequence_policy(asset, steps, policy_map)
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
        "tool_sequence_policy": sequence_policy["policy_id"],
        "asset_family_policy": family_policy["asset_family"],
        "asset_id": asset["asset_id"],
        "asset_family": asset["asset_family"],
        "style": asset["style"],
        "detail_level": asset["detail_level"],
        "target_readiness": asset.get("target_readiness", "procedural_asset"),
        "dimensions_m": require_object(asset.get("dimensions_m"), f"{asset['asset_id']}.dimensions_m"),
        "features": require_list(asset.get("features"), f"{asset['asset_id']}.features"),
        "style_parameters": style_params(asset),
        "source_terms": source_terms_for_asset(asset),
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
            "asset_family_sequence_policy_validated": True,
            "geometry_dictionary_source_terms_validated": True,
        },
        "no_claims": validate_false_claims(asset.get("no_claims"), f"{asset['asset_id']}.no_claims"),
    }


def write_outputs(plans: list[dict[str, Any]], out_root: Path, recipe_path: Path, sequence_policy: dict[str, Any]) -> None:
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
        "tool_sequence_policy": sequence_policy["policy_id"],
        "plan_count": len(plans),
        "plans": manifest_plans,
        "rules": {
            "no_blender_execution": True,
            "no_media": True,
            "no_mesh_export_files": True,
            "tool_dictionary_enforced": True,
            "stage_order_enforced": True,
            "asset_family_sequence_policy_enforced": True,
        },
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile source intent into deterministic Blender tool-plan JSON.")
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--sequence-policy", type=Path, default=DEFAULT_SEQUENCE_POLICY)
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
    sequence_policy_path = args.sequence_policy if args.sequence_policy.is_absolute() else ROOT / args.sequence_policy
    sequence_policy = load_json(sequence_policy_path)
    recipe = load_json(recipe_path)
    geometry_terms = load_geometry_terms()
    tool_map = validate_tool_dictionary(dictionary)
    policy_map = validate_sequence_policy(sequence_policy, dictionary, tool_map)
    assets = validate_recipe_bundle(recipe, [str(stage) for stage in require_list(dictionary.get("stages"), "dictionary.stages")], geometry_terms, tool_map)
    plans = [compile_asset_plan(asset, tool_map, dictionary, sequence_policy, policy_map, recipe_path) for asset in assets]
    if not args.validate_only:
        write_outputs(plans, out_root, recipe_path, sequence_policy)
    total_steps = sum(plan["summary"]["step_count"] for plan in plans)
    print(f"compiled tool plans={len(plans)} steps={total_steps} tools={len(tool_map)} out={out_root if not args.validate_only else '<validate-only>'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
