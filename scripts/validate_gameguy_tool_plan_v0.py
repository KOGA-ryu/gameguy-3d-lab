#!/usr/bin/env python3
"""Validate compiled gameguy_tool_plan_v0 JSON.

This validates deterministic tool-plan output before Blender sees it. It does
not import Blender, run the tool-plan compiler, read source intent recipes, or
create media/mesh artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("/tmp/gameguy_blender_tool_plan_v0/manifest.json")
DEFAULT_CONTRACT = ROOT / "contracts" / "gameguy_tool_plan_v0.json"
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_SEQUENCE_POLICY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "asset_family_tool_sequence_policy_v0.json"
GEOMETRY_DICTIONARY_ROOT = ROOT / "geometry_dictionary"
PLAN_SCHEMA = "gameguy_tool_plan_v0"
MANIFEST_SCHEMA = "gameguy_tool_plan_manifest_v0"
CONTRACT_SCHEMA = "gameguy_tool_plan_contract_v0"
DICTIONARY_SCHEMA = "blender_tool_dictionary_v0"
SEQUENCE_POLICY_SCHEMA = "asset_family_tool_sequence_policy_v0"
SOURCE_SCHEMA = "asset_mill_tool_plan_recipe_bundle_v0"
FORBIDDEN_OUTPUT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".blend",
    ".blend1",
    ".obj",
    ".gltf",
    ".glb",
    ".fbx",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


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
            fail(f"{path} term_id must be a non-empty string")
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


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{field} must be a boolean")
    return value


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_number(value: Any, field: str, *, positive: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{field} must be a number")
    result = float(value)
    if positive and result <= 0.0:
        fail(f"{field} must be positive")
    return result


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
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


def require_known_terms(values: Any, known: set[str], field: str, *, allow_empty: bool = True) -> list[str]:
    result = []
    for index, item in enumerate(require_string_list(values, field, allow_empty=allow_empty)):
        if item not in known:
            fail(f"{field}[{index}] uses unknown geometry dictionary term `{item}`")
        result.append(item)
    return result


def require_false_rules(value: Any, field: str, rules: dict[str, bool]) -> None:
    obj = require_object(value, field)
    for key, expected in rules.items():
        if obj.get(key) is not expected:
            fail(f"{field}.{key} must be {str(expected).lower()}")


def validate_no_claims(value: Any, required: dict[str, Any], field: str) -> None:
    claims = require_object(value, field)
    for key, expected in required.items():
        if claims.get(key) is not expected:
            fail(f"{field}.{key} must be false")
    for key, value in claims.items():
        if not isinstance(key, str) or value is not False:
            fail(f"{field} must contain only false boolean claim flags")


def validate_dimensions(value: Any, field: str) -> None:
    dimensions = require_object(value, field)
    for key in ("width", "depth", "height"):
        require_number(dimensions.get(key), f"{field}.{key}", positive=True)


def validate_tool_dictionary(dictionary: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    if dictionary.get("schema") != DICTIONARY_SCHEMA:
        fail(f"tool dictionary schema must be {DICTIONARY_SCHEMA}")
    stages = require_string_list(dictionary.get("stages"), "dictionary.stages")
    if len(stages) != len(set(stages)):
        fail("dictionary.stages must be unique")
    lanes = require_string_list(dictionary.get("execution_lanes"), "dictionary.execution_lanes")
    if len(lanes) != len(set(lanes)):
        fail("dictionary.execution_lanes must be unique")
    tools = require_list(dictionary.get("tools"), "dictionary.tools")
    if dictionary.get("tool_count") != len(tools):
        fail("dictionary.tool_count must match tools length")
    tool_map: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(tools):
        tool = require_object(item, f"dictionary.tools[{index}]")
        tool_id = require_string(tool.get("tool_id"), f"dictionary.tools[{index}].tool_id")
        if tool_id in tool_map:
            fail(f"duplicate tool_id `{tool_id}`")
        stage = require_string(tool.get("stage"), f"{tool_id}.stage")
        if stage not in stages:
            fail(f"{tool_id}.stage uses unknown stage `{stage}`")
        lane = require_string(tool.get("execution_lane"), f"{tool_id}.execution_lane")
        if lane not in lanes:
            fail(f"{tool_id}.execution_lane uses unknown lane `{lane}`")
        require_string(tool.get("category"), f"{tool_id}.category")
        require_bool(tool.get("deterministic"), f"{tool_id}.deterministic")
        for list_field in ("blender_api", "inputs", "outputs", "preconditions", "postconditions", "asset_families"):
            require_string_list(tool.get(list_field), f"{tool_id}.{list_field}")
        tool_map[tool_id] = tool
    return tool_map, stages, lanes


def validate_sequence_policy(
    policy: dict[str, Any],
    dictionary: dict[str, Any],
    tool_map: dict[str, dict[str, Any]],
    stages: list[str],
) -> dict[str, dict[str, Any]]:
    if policy.get("schema") != SEQUENCE_POLICY_SCHEMA:
        fail(f"sequence policy schema must be {SEQUENCE_POLICY_SCHEMA}")
    if policy.get("tool_dictionary") != dictionary.get("dictionary_id"):
        fail("sequence policy tool_dictionary must match dictionary_id")
    stage_order = require_string_list(policy.get("stage_order"), "sequence_policy.stage_order")
    if stage_order != stages:
        fail("sequence policy stage_order must match tool dictionary stages")
    require_false_rules(
        policy.get("rules"),
        "sequence_policy.rules",
        {
            "source_policy_only": True,
            "compiler_enforces_policy": True,
            "validator_enforces_policy": True,
            "blender_adapter_reads_compiled_plan_only": True,
            "policy_does_not_execute_blender": True,
            "family_tools_must_exist_in_dictionary": True,
            "stage_order_must_match_dictionary": True,
        },
    )
    required_no_claims = {
        "production_approval": False,
        "structural_safety": False,
        "fabrication_ready": False,
        "gym_museum_approval": False,
        "historical_accuracy": False,
        "game_engine_integration": False,
    }
    validate_no_claims(policy.get("no_claims"), required_no_claims, "sequence_policy.no_claims")
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
            if stage not in stages:
                fail(f"{asset_family}.required_stage_coverage uses unknown stage `{stage}`")
        allowed_by_stage = require_object(family_policy.get("allowed_tools_by_stage"), f"{asset_family}.allowed_tools_by_stage")
        allowed_tools: set[str] = set()
        normalized_allowed_by_stage: dict[str, set[str]] = {}
        for stage, tools_value in allowed_by_stage.items():
            if stage not in stages:
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


def validate_contract(contract: dict[str, Any], stages: list[str]) -> tuple[list[str], list[str], dict[str, Any]]:
    if contract.get("schema") != CONTRACT_SCHEMA:
        fail(f"contract schema must be {CONTRACT_SCHEMA}")
    if contract.get("generated_schema") != PLAN_SCHEMA:
        fail(f"contract.generated_schema must be {PLAN_SCHEMA}")
    required_fields = require_string_list(contract.get("required_fields"), "contract.required_fields")
    step_required_fields = require_string_list(contract.get("step_required_fields"), "contract.step_required_fields")
    contract_stages = require_string_list(contract.get("stage_order"), "contract.stage_order")
    if contract_stages != stages:
        fail("contract.stage_order must match tool dictionary stages")
    required_claims = require_object(contract.get("required_no_claims"), "contract.required_no_claims")
    require_false_rules(
        contract.get("rules"),
        "contract.rules",
        {
            "steps_must_use_known_tool_ids": True,
            "steps_must_follow_stage_order": True,
            "steps_must_have_stable_order_indexes": True,
            "compiler_does_not_execute_blender": True,
            "blender_execution_adapter_must_consume_tool_plan": True,
            "generated_media_or_mesh_outputs_are_not_written_by_compiler": True,
            "asset_family_sequence_policy_must_be_enforced": True,
            "geometry_dictionary_source_terms_must_be_valid": True,
        },
    )
    return required_fields, step_required_fields, required_claims


def validate_manifest(manifest: dict[str, Any], manifest_path: Path, sequence_policy: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        fail(f"{manifest_path} schema must be {MANIFEST_SCHEMA}")
    if manifest.get("source_schema") != SOURCE_SCHEMA:
        fail("manifest.source_schema must be asset_mill_tool_plan_recipe_bundle_v0")
    if manifest.get("plan_schema") != PLAN_SCHEMA:
        fail(f"manifest.plan_schema must be {PLAN_SCHEMA}")
    if manifest.get("tool_sequence_policy") != sequence_policy.get("policy_id"):
        fail("manifest.tool_sequence_policy must match sequence policy")
    plans = require_list(manifest.get("plans"), "manifest.plans")
    if manifest.get("plan_count") != len(plans):
        fail("manifest.plan_count must match plans length")
    require_false_rules(
        manifest.get("rules"),
        "manifest.rules",
        {
            "no_blender_execution": True,
            "no_media": True,
            "no_mesh_export_files": True,
            "tool_dictionary_enforced": True,
            "stage_order_enforced": True,
            "asset_family_sequence_policy_enforced": True,
        },
    )
    if not plans:
        fail("manifest.plans must not be empty")
    return [require_object(item, f"manifest.plans[{index}]") for index, item in enumerate(plans)]


def validate_no_generated_media_or_mesh(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_OUTPUT_SUFFIXES:
            fail(f"generated media/mesh output is not allowed in tool-plan output: {path}")


def validate_step(
    step: dict[str, Any],
    index: int,
    tool_map: dict[str, dict[str, Any]],
    stage_indexes: dict[str, int],
    step_required_fields: list[str],
) -> tuple[str, str]:
    for field in step_required_fields:
        if field not in step:
            fail(f"steps[{index}].{field} is required")
    expected_order = index + 1
    order = require_int(step.get("order"), f"steps[{index}].order", minimum=1)
    if order != expected_order:
        fail(f"steps[{index}].order must be {expected_order}")
    step_id = require_string(step.get("step_id"), f"steps[{index}].step_id")
    stage = require_string(step.get("stage"), f"{step_id}.stage")
    if stage not in stage_indexes:
        fail(f"{step_id}.stage uses unknown stage `{stage}`")
    tool_id = require_string(step.get("tool_id"), f"{step_id}.tool_id")
    if tool_id not in tool_map:
        fail(f"{step_id} uses unknown tool_id `{tool_id}`")
    tool = tool_map[tool_id]
    if stage != tool["stage"]:
        fail(f"{step_id}.stage must match dictionary stage `{tool['stage']}`")
    for field in ("category", "execution_lane", "deterministic", "blender_api", "inputs", "outputs", "preconditions", "postconditions"):
        if step.get(field) != tool[field]:
            fail(f"{step_id}.{field} must match tool dictionary")
    if step.get("deterministic") is not True:
        fail(f"{step_id}.deterministic must be true")
    require_string(step.get("purpose"), f"{step_id}.purpose")
    require_object(step.get("params"), f"{step_id}.params")
    return step_id, tool_id


def validate_source_terms(plan: dict[str, Any], geometry_terms: dict[str, set[str]]) -> None:
    source_terms = require_object(plan.get("source_terms"), "source_terms")
    geometry = require_known_terms(source_terms.get("geometry"), all_geometry_terms(geometry_terms), "source_terms.geometry")
    profiles = require_known_terms(source_terms.get("profiles"), geometry_terms["profile_primitive"], "source_terms.profiles")
    operators = require_known_terms(source_terms.get("operators"), operation_terms(geometry_terms), "source_terms.operators")
    if "profile_operation_stack" not in require_string_list(plan.get("features"), "features"):
        return
    if "profile_operation_stack" not in geometry or "profile_operation_stack" not in operators:
        fail("source_terms must declare profile_operation_stack for profile_operation_stack features")
    if not profiles:
        fail("source_terms.profiles must not be empty for profile_operation_stack features")
    stack = require_object(source_terms.get("profile_operation_stack"), "source_terms.profile_operation_stack")
    require_string(stack.get("grammar_id"), "source_terms.profile_operation_stack.grammar_id")
    if require_string(stack.get("axis"), "source_terms.profile_operation_stack.axis") != "z":
        fail("source_terms.profile_operation_stack.axis only supports z in v0")
    require_string_list(stack.get("sequence"), "source_terms.profile_operation_stack.sequence")


def enforce_plan_sequence_policy(
    plan: dict[str, Any],
    steps: list[dict[str, Any]],
    sequence_policy: dict[str, Any],
    policy_map: dict[str, dict[str, Any]],
) -> None:
    plan_id = require_string(plan.get("plan_id"), "plan_id")
    asset_family = require_string(plan.get("asset_family"), "asset_family")
    if plan.get("tool_sequence_policy") != sequence_policy.get("policy_id"):
        fail(f"{plan_id}.tool_sequence_policy must match sequence policy")
    if plan.get("asset_family_policy") != asset_family:
        fail(f"{plan_id}.asset_family_policy must match asset_family")
    if asset_family not in policy_map:
        fail(f"{plan_id}.asset_family `{asset_family}` has no sequence policy")
    policy = policy_map[asset_family]
    for feature_index, feature in enumerate(require_string_list(plan.get("features"), "features")):
        if feature not in policy["allowed_features"]:
            fail(f"{plan_id}.features[{feature_index}] `{feature}` is not allowed by the {asset_family} sequence policy")

    observed_stages: list[str] = []
    tool_positions: dict[str, list[int]] = {}
    for step in steps:
        stage = step["stage"]
        tool_id = step["tool_id"]
        if stage not in observed_stages:
            observed_stages.append(stage)
        if tool_id in policy["forbidden_tools"]:
            fail(f"{plan_id}.{step['step_id']} uses forbidden {asset_family} tool `{tool_id}`")
        allowed_tools = policy["allowed_tools_by_stage"].get(stage, set())
        if tool_id not in allowed_tools:
            fail(f"{plan_id}.{step['step_id']} uses `{tool_id}` outside the {asset_family} sequence policy")
        tool_positions.setdefault(tool_id, []).append(step["order"])
    for stage in policy["required_stage_coverage"]:
        if stage not in observed_stages:
            fail(f"{plan_id} missing sequence-policy stage `{stage}`")
    missing_tools = sorted(tool for tool in policy["required_tools"] if tool not in tool_positions)
    if missing_tools:
        fail(f"{plan_id} missing sequence-policy required tools: {missing_tools}")
    for constraint in policy["tool_order_constraints"]:
        before = constraint["before"]
        after = constraint["after"]
        if before in tool_positions and after in tool_positions and min(tool_positions[before]) >= min(tool_positions[after]):
            fail(f"{plan_id} sequence policy requires `{before}` before `{after}`")


def validate_plan(
    plan: dict[str, Any],
    plan_path: Path,
    tool_map: dict[str, dict[str, Any]],
    stages: list[str],
    required_fields: list[str],
    step_required_fields: list[str],
    required_claims: dict[str, Any],
    dictionary: dict[str, Any],
    sequence_policy: dict[str, Any],
    policy_map: dict[str, dict[str, Any]],
    geometry_terms: dict[str, set[str]],
) -> dict[str, Any]:
    for field in required_fields:
        if field not in plan:
            fail(f"{plan_path}.{field} is required")
    if plan.get("schema") != PLAN_SCHEMA:
        fail(f"{plan_path} schema must be {PLAN_SCHEMA}")
    if plan.get("source_schema") != SOURCE_SCHEMA:
        fail(f"{plan_path} source_schema must be {SOURCE_SCHEMA}")
    if plan.get("tool_dictionary") != dictionary.get("dictionary_id"):
        fail(f"{plan_path} tool_dictionary must match dictionary_id")
    require_string(plan.get("plan_id"), "plan_id")
    require_string(plan.get("asset_id"), "asset_id")
    require_string(plan.get("asset_family"), "asset_family")
    require_string(plan.get("style"), "style")
    require_string(plan.get("detail_level"), "detail_level")
    require_string_list(plan.get("features"), "features")
    require_object(plan.get("style_parameters", {}), "style_parameters")
    validate_source_terms(plan, geometry_terms)
    validate_dimensions(plan.get("dimensions_m"), "dimensions_m")
    if require_string_list(plan.get("stage_order"), "stage_order") != stages:
        fail("stage_order must match tool dictionary stages")
    validate_no_claims(plan.get("no_claims"), required_claims, "no_claims")
    require_false_rules(
        plan.get("rules"),
        "rules",
        {
            "compiler_imports_bpy": False,
            "compiler_executes_blender": False,
            "writes_generated_media_or_mesh": False,
            "blender_adapter_must_consume_plan": True,
            "tool_ids_validated": True,
            "stage_order_validated": True,
            "asset_family_sequence_policy_validated": True,
            "geometry_dictionary_source_terms_validated": True,
        },
    )

    steps = [require_object(item, f"steps[{index}]") for index, item in enumerate(require_list(plan.get("steps"), "steps"))]
    if not steps:
        fail("steps must not be empty")
    stage_indexes = {stage: index for index, stage in enumerate(stages)}
    previous_stage_index = -1
    step_ids: set[str] = set()
    observed_stages: list[str] = []
    observed_lanes: list[str] = []
    tool_ids: list[str] = []
    for index, step in enumerate(steps):
        step_id, tool_id = validate_step(step, index, tool_map, stage_indexes, step_required_fields)
        if step_id in step_ids:
            fail(f"duplicate step_id `{step_id}`")
        step_ids.add(step_id)
        stage = step["stage"]
        current_stage_index = stage_indexes[stage]
        if current_stage_index < previous_stage_index:
            fail(f"{step_id} is out of stage order")
        previous_stage_index = current_stage_index
        if stage not in observed_stages:
            observed_stages.append(stage)
        lane = step["execution_lane"]
        if lane not in observed_lanes:
            observed_lanes.append(lane)
        tool_ids.append(tool_id)

    enforce_plan_sequence_policy(plan, steps, sequence_policy, policy_map)

    unique_tools = sorted(set(tool_ids))
    summary = require_object(plan.get("summary"), "summary")
    if summary.get("step_count") != len(steps):
        fail("summary.step_count must match steps length")
    if summary.get("unique_tool_count") != len(unique_tools):
        fail("summary.unique_tool_count must match unique tools")
    if require_string_list(summary.get("unique_tools"), "summary.unique_tools") != unique_tools:
        fail("summary.unique_tools must be sorted unique tool ids")
    if require_string_list(summary.get("covered_stages"), "summary.covered_stages") != observed_stages:
        fail("summary.covered_stages must match observed stages")
    if require_string_list(summary.get("execution_lanes"), "summary.execution_lanes") != observed_lanes:
        fail("summary.execution_lanes must match observed execution lanes")
    if summary.get("non_deterministic_step_count") != 0:
        fail("summary.non_deterministic_step_count must be 0")
    return {
        "plan_id": plan["plan_id"],
        "asset_id": plan["asset_id"],
        "asset_family": plan["asset_family"],
        "style": plan["style"],
        "step_count": len(steps),
        "unique_tool_count": len(unique_tools),
        "unique_tools": unique_tools,
        "covered_stages": observed_stages,
    }


def validate_manifest_plans(
    manifest_path: Path,
    manifest_rows: list[dict[str, Any]],
    tool_map: dict[str, dict[str, Any]],
    stages: list[str],
    required_fields: list[str],
    step_required_fields: list[str],
    required_claims: dict[str, Any],
    dictionary: dict[str, Any],
    sequence_policy: dict[str, Any],
    policy_map: dict[str, dict[str, Any]],
    geometry_terms: dict[str, set[str]],
) -> list[dict[str, Any]]:
    manifest_root = manifest_path.parent
    results = []
    seen_plan_ids: set[str] = set()
    for index, row in enumerate(manifest_rows):
        plan_id = require_string(row.get("plan_id"), f"manifest.plans[{index}].plan_id")
        if plan_id in seen_plan_ids:
            fail(f"duplicate manifest plan_id `{plan_id}`")
        seen_plan_ids.add(plan_id)
        path_text = require_string(row.get("path"), f"manifest.plans[{index}].path")
        plan_rel_path = Path(path_text)
        if plan_rel_path.is_absolute() or ".." in plan_rel_path.parts:
            fail(f"manifest.plans[{index}].path must be a relative path inside the manifest root")
        plan_path = manifest_root / plan_rel_path
        plan = load_json(plan_path)
        result = validate_plan(
            plan,
            plan_path,
            tool_map,
            stages,
            required_fields,
            step_required_fields,
            required_claims,
            dictionary,
            sequence_policy,
            policy_map,
            geometry_terms,
        )
        if result["plan_id"] != plan_id:
            fail(f"manifest.plans[{index}].plan_id must match plan.plan_id")
        if row.get("step_count") != result["step_count"]:
            fail(f"manifest.plans[{index}].step_count must match plan summary")
        if row.get("unique_tool_count") != result["unique_tool_count"]:
            fail(f"manifest.plans[{index}].unique_tool_count must match plan summary")
        if require_string_list(row.get("covered_stages"), f"manifest.plans[{index}].covered_stages") != result["covered_stages"]:
            fail(f"manifest.plans[{index}].covered_stages must match plan summary")
        results.append(result)
    return results


def validate_tool_plan_output(manifest_path: Path, contract_path: Path, dictionary_path: Path, sequence_policy_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    contract = load_json(contract_path)
    dictionary = load_json(dictionary_path)
    sequence_policy = load_json(sequence_policy_path)
    geometry_terms = load_geometry_terms()
    tool_map, stages, _lanes = validate_tool_dictionary(dictionary)
    policy_map = validate_sequence_policy(sequence_policy, dictionary, tool_map, stages)
    required_fields, step_required_fields, required_claims = validate_contract(contract, stages)
    manifest_rows = validate_manifest(manifest, manifest_path, sequence_policy)
    validate_no_generated_media_or_mesh(manifest_path.parent)
    plan_results = validate_manifest_plans(
        manifest_path,
        manifest_rows,
        tool_map,
        stages,
        required_fields,
        step_required_fields,
        required_claims,
        dictionary,
        sequence_policy,
        policy_map,
        geometry_terms,
    )
    total_steps = sum(plan["step_count"] for plan in plan_results)
    unique_tools = sorted({tool_id for result in plan_results for tool_id in result["unique_tools"]})
    covered_stages: list[str] = []
    for result in plan_results:
        for stage in result["covered_stages"]:
            if stage not in covered_stages:
                covered_stages.append(stage)
    return {
        "schema": "gameguy_tool_plan_v0_validation_result_v0",
        "manifest": str(manifest_path),
        "contract": str(contract_path),
        "tool_dictionary": dictionary.get("dictionary_id"),
        "tool_sequence_policy": sequence_policy.get("policy_id"),
        "plan_count": len(plan_results),
        "total_steps": total_steps,
        "unique_tool_count": len(unique_tools),
        "covered_stages": covered_stages,
        "generated_outputs_created": False,
        "rules": {
            "imports_blender": False,
            "runs_tool_plan_compiler": False,
            "reads_source_intent_recipe": False,
            "creates_media_or_mesh": False,
            "validates_known_tool_ids": True,
            "validates_stage_order": True,
            "validates_stable_step_order": True,
            "validates_asset_family_sequence_policy": True,
            "validates_geometry_dictionary_terms": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate deterministic gameguy_tool_plan_v0 compiler output.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--sequence-policy", type=Path, default=DEFAULT_SEQUENCE_POLICY)
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    contract_path = args.contract if args.contract.is_absolute() else ROOT / args.contract
    dictionary_path = args.dictionary if args.dictionary.is_absolute() else ROOT / args.dictionary
    sequence_policy_path = args.sequence_policy if args.sequence_policy.is_absolute() else ROOT / args.sequence_policy
    result = validate_tool_plan_output(manifest_path, contract_path, dictionary_path, sequence_policy_path)
    if args.json_report:
        output_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS gameguy_tool_plan_v0 validation: "
        f"{result['plan_count']} plans, {result['total_steps']} steps, {result['unique_tool_count']} tools"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
