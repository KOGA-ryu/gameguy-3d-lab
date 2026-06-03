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
DEFAULT_OUT = Path("/tmp/gameguy_blender_tool_plan_v0")
SEQUENCE_POLICY_SCHEMA = "asset_family_tool_sequence_policy_v0"
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


def feature_steps(asset: dict[str, Any], feature: str) -> list[dict[str, Any]]:
    params = style_params(asset)
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
    tool_map = validate_tool_dictionary(dictionary)
    policy_map = validate_sequence_policy(sequence_policy, dictionary, tool_map)
    assets = validate_recipe_bundle(recipe, [str(stage) for stage in require_list(dictionary.get("stages"), "dictionary.stages")])
    plans = [compile_asset_plan(asset, tool_map, dictionary, sequence_policy, policy_map, recipe_path) for asset in assets]
    if not args.validate_only:
        write_outputs(plans, out_root, recipe_path, sequence_policy)
    total_steps = sum(plan["summary"]["step_count"] for plan in plans)
    print(f"compiled tool plans={len(plans)} steps={total_steps} tools={len(tool_map)} out={out_root if not args.validate_only else '<validate-only>'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
