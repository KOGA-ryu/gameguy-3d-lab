#!/usr/bin/env python3
"""Validate compiled asset_polish_tool_plan_v0 JSON.

This validator checks source-to-polish-plan output before any Blender adapter
is allowed to execute it. It does not import Blender or create assets.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("/tmp/gameguy_asset_polish_tool_plan_v0/manifest.json")
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
PLAN_SCHEMA = "asset_polish_tool_plan_v0"
MANIFEST_SCHEMA = "asset_polish_tool_plan_manifest_v0"
TOOL_DICTIONARY_SCHEMA = "blender_tool_dictionary_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
}
FORBIDDEN_OUTPUT_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".blend", ".obj", ".gltf", ".glb", ".fbx"}


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
    number = float(value)
    if not math.isfinite(number):
        fail(f"{field} must be finite")
    if positive and number <= 0.0:
        fail(f"{field} must be positive")
    return number


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


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    result = []
    for index, item in enumerate(require_list(value, field, allow_empty=allow_empty)):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def validate_tool_dictionary(dictionary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if dictionary.get("schema") != TOOL_DICTIONARY_SCHEMA:
        fail(f"tool dictionary schema must be {TOOL_DICTIONARY_SCHEMA}")
    tools = require_list(dictionary.get("tools"), "tool_dictionary.tools")
    if dictionary.get("tool_count") != len(tools):
        fail("tool_dictionary.tool_count must match tools length")
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(tools):
        tool = require_object(item, f"tool_dictionary.tools[{index}]")
        tool_id = require_string(tool.get("tool_id"), f"tool_dictionary.tools[{index}].tool_id")
        result[tool_id] = tool
    return result


def assert_no_forbidden_paths(value: Any, field: str) -> None:
    if isinstance(value, str):
        if Path(value).suffix.lower() in FORBIDDEN_OUTPUT_SUFFIXES:
            fail(f"{field} must not reference generated media/mesh output `{value}`")
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_forbidden_paths(item, f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_forbidden_paths(item, f"{field}[{index}]")


def validate_dimensions(value: Any, field: str) -> None:
    dimensions = require_object(value, field)
    for key in ("width", "depth", "height"):
        require_number(dimensions.get(key), f"{field}.{key}", positive=True)


def validate_plan(plan: dict[str, Any], tool_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if plan.get("schema") != PLAN_SCHEMA:
        fail(f"plan schema must be {PLAN_SCHEMA}")
    plan_id = require_string(plan.get("plan_id"), "plan_id")
    source_asset = require_object(plan.get("source_asset"), f"{plan_id}.source_asset")
    if require_string(source_asset.get("asset_schema"), f"{plan_id}.source_asset.asset_schema") != "gameguy_asset_v0":
        fail(f"{plan_id}.source_asset.asset_schema must be gameguy_asset_v0")
    require_string(source_asset.get("asset_id"), f"{plan_id}.source_asset.asset_id")
    require_string(source_asset.get("source_bundle"), f"{plan_id}.source_asset.source_bundle")
    validate_dimensions(plan.get("dimensions_m"), f"{plan_id}.dimensions_m")
    if "asset_polish_tool_plan" not in require_string_list(plan.get("geometry_terms_used"), f"{plan_id}.geometry_terms_used"):
        fail(f"{plan_id}.geometry_terms_used must include asset_polish_tool_plan")
    if "asset_polish_tool_plan" not in require_string_list(plan.get("operations"), f"{plan_id}.operations"):
        fail(f"{plan_id}.operations must include asset_polish_tool_plan")
    target_ids: set[str] = set()
    targets = require_list(plan.get("targets"), f"{plan_id}.targets")
    for index, item in enumerate(targets):
        target = require_object(item, f"{plan_id}.targets[{index}]")
        target_id = require_string(target.get("target_id"), f"{plan_id}.targets[{index}].target_id")
        if target_id in target_ids:
            fail(f"{plan_id} duplicate target_id `{target_id}`")
        target_ids.add(target_id)
        require_string_list(target.get("architectural_terms"), f"{target_id}.architectural_terms")
        require_string_list(target.get("source_part_ids"), f"{target_id}.source_part_ids")
        require_object(target.get("selector"), f"{target_id}.selector")
        require_string(target.get("material_role"), f"{target_id}.material_role")
    steps = require_list(plan.get("steps"), f"{plan_id}.steps")
    step_ids: set[str] = set()
    unique_tools: set[str] = set()
    operations: set[str] = set()
    non_deterministic = 0
    for index, item in enumerate(steps):
        step = require_object(item, f"{plan_id}.steps[{index}]")
        if require_int(step.get("step_index"), f"{plan_id}.steps[{index}].step_index", minimum=0) != index:
            fail(f"{plan_id}.steps[{index}].step_index must match index")
        step_id = require_string(step.get("step_id"), f"{plan_id}.steps[{index}].step_id")
        if step_id in step_ids:
            fail(f"{plan_id} duplicate step_id `{step_id}`")
        step_ids.add(step_id)
        operations.add(require_string(step.get("operation"), f"{step_id}.operation"))
        tool_id = require_string(step.get("tool_id"), f"{step_id}.tool_id")
        if tool_id not in tool_map:
            fail(f"{step_id}.tool_id uses unknown tool `{tool_id}`")
        unique_tools.add(tool_id)
        target = require_string(step.get("target"), f"{step_id}.target")
        if target not in target_ids:
            fail(f"{step_id}.target references unknown target `{target}`")
        require_object(step.get("params"), f"{step_id}.params")
        deterministic = require_bool(step.get("deterministic"), f"{step_id}.deterministic")
        if not deterministic:
            non_deterministic += 1
    material_slots = require_list(plan.get("material_slots"), f"{plan_id}.material_slots")
    summary = require_object(plan.get("summary"), f"{plan_id}.summary")
    if summary.get("target_count") != len(targets):
        fail(f"{plan_id}.summary.target_count must match targets")
    if summary.get("step_count") != len(steps):
        fail(f"{plan_id}.summary.step_count must match steps")
    if summary.get("unique_tool_count") != len(unique_tools):
        fail(f"{plan_id}.summary.unique_tool_count must match unique tools")
    if summary.get("non_deterministic_step_count") != non_deterministic:
        fail(f"{plan_id}.summary.non_deterministic_step_count must match steps")
    if require_object(plan.get("rules"), f"{plan_id}.rules").get("compiler_executes_blender") is not False:
        fail(f"{plan_id}.rules.compiler_executes_blender must be false")
    if plan.get("no_claims") != FALSE_CLAIMS:
        fail(f"{plan_id}.no_claims must match required false claim flags")
    assert_no_forbidden_paths(plan, plan_id)
    return {
        "plan_id": plan_id,
        "target_count": len(targets),
        "step_count": len(steps),
        "material_slot_count": len(material_slots),
        "unique_tool_count": len(unique_tools),
        "operation_count": len(operations),
    }


def validate_manifest(path: Path, tool_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest = load_json(path)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        fail(f"manifest schema must be {MANIFEST_SCHEMA}")
    plans = require_list(manifest.get("plans"), "manifest.plans")
    if manifest.get("plan_count") != len(plans):
        fail("manifest.plan_count must match plans length")
    results = []
    for index, row_value in enumerate(plans):
        row = require_object(row_value, f"manifest.plans[{index}]")
        relative = Path(require_string(row.get("path"), f"manifest.plans[{index}].path"))
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"manifest.plans[{index}].path must be relative")
        plan = load_json(path.parent / relative)
        result = validate_plan(plan, tool_map)
        if row.get("plan_id") != result["plan_id"]:
            fail(f"manifest.plans[{index}].plan_id must match plan")
        if row.get("step_count") != result["step_count"]:
            fail(f"manifest.plans[{index}].step_count must match plan")
        if row.get("target_count") != result["target_count"]:
            fail(f"manifest.plans[{index}].target_count must match plan")
        results.append(result)
    return {
        "schema": "asset_polish_tool_plan_validation_result_v0",
        "status": "pass",
        "manifest": str(path),
        "plan_count": len(results),
        "step_count": sum(result["step_count"] for result in results),
        "target_count": sum(result["target_count"] for result in results),
        "unique_tool_count": sum(result["unique_tool_count"] for result in results),
        "material_slot_count": sum(result["material_slot_count"] for result in results),
        "rules": {
            "runs_blender": False,
            "imports_blender": False,
            "creates_media_or_mesh": False,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate compiled asset_polish_tool_plan_v0 JSON.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--plan", type=Path, help="Validate one compiled plan instead of a manifest.")
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--json-report", type=Path, help="Optional path for a validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dictionary_path = args.dictionary if args.dictionary.is_absolute() else ROOT / args.dictionary
    tool_map = validate_tool_dictionary(load_json(dictionary_path))
    if args.plan:
        plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
        result = validate_plan(load_json(plan_path), tool_map)
        report = {
            "schema": "asset_polish_tool_plan_validation_result_v0",
            "status": "pass",
            "plan_count": 1,
            **result,
        }
    else:
        manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
        report = validate_manifest(manifest_path, tool_map)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS asset polish tool-plan validation: "
        f"plans={report['plan_count']} "
        f"steps={report['step_count']} "
        f"targets={report['target_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
