#!/usr/bin/env python3
"""Validate asset polish Blender execution reports.

This script validates the report after Blender has run. It does not import
Blender, compile recipes, run the asset pump, or create mesh/media artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = Path("/tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json")
REPORT_SCHEMA = "asset_polish_blender_execution_report_v0"
PLAN_SCHEMA = "asset_polish_tool_plan_v0"
ASSET_SCHEMA = "gameguy_asset_v0"
REQUIRED_RULES = {
    "consumes_asset_polish_tool_plan_v0": True,
    "consumes_gameguy_asset_v0": True,
    "reads_source_recipe": False,
    "runs_asset_pump": False,
    "executes_only_supported_deterministic_steps": True,
    "skips_future_operations": True,
    "source_design_logic": False,
    "mutates_source_asset_json": False,
}
REQUIRED_QUALITY_FLAGS = {
    "supported_polish_steps_executed",
    "future_steps_skipped",
    "source_asset_preserved",
    "source_recipe_not_read",
    "booleans_applied",
    "insets_applied",
    "extrusions_applied",
    "material_assignment_applied",
    "bevels_applied",
    "weighted_normals_added",
}
REQUIRED_UNIQUE_TOOLS = {
    "extrude_faces",
    "inset_faces",
    "material_assign_by_part",
    "modifier_bevel",
    "modifier_boolean",
    "modifier_weighted_normal",
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


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_string_list(value: Any, field: str) -> list[str]:
    result = []
    for index, item in enumerate(require_list(value, field)):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def is_under_root(path_text: str, root: Path) -> bool:
    path = Path(path_text)
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def validate_no_repo_generated_outputs(report: dict[str, Any]) -> None:
    for field in ("blend_path", "render_path"):
        value = report.get(field)
        if value is None:
            continue
        path_text = require_string(value, field)
        if is_under_root(path_text, ROOT):
            fail(f"{field} must not point inside the repo")


def validate_rules(report: dict[str, Any]) -> None:
    rules = require_object(report.get("rules"), "rules")
    for key, expected in REQUIRED_RULES.items():
        if rules.get(key) is not expected:
            fail(f"rules.{key} must be {str(expected).lower()}")


def validate_counts(report: dict[str, Any]) -> None:
    step_count = require_int(report.get("step_count"), "step_count", minimum=1)
    supported = require_int(report.get("supported_step_count"), "supported_step_count", minimum=1)
    future = require_int(report.get("future_step_count"), "future_step_count", minimum=1)
    executed = require_int(report.get("executed_step_count"), "executed_step_count", minimum=1)
    skipped = require_int(report.get("skipped_future_step_count"), "skipped_future_step_count", minimum=1)
    unique_tools = require_string_list(report.get("unique_tools"), "unique_tools")
    unique_tool_count = require_int(report.get("unique_tool_count"), "unique_tool_count", minimum=1)
    if step_count != supported + future:
        fail("step_count must equal supported_step_count + future_step_count")
    if executed != supported:
        fail("executed_step_count must match supported_step_count")
    if skipped != future:
        fail("skipped_future_step_count must match future_step_count")
    if unique_tool_count != len(set(unique_tools)):
        fail("unique_tool_count must match unique_tools")
    if not REQUIRED_UNIQUE_TOOLS.issubset(set(unique_tools)):
        fail("unique_tools must include first execution slice tool families")


def validate_step_lists(report: dict[str, Any]) -> None:
    executed = require_list(report.get("executed_steps"), "executed_steps")
    skipped = require_list(report.get("skipped_steps"), "skipped_steps")
    if len(executed) != report["executed_step_count"]:
        fail("executed_steps length must match executed_step_count")
    if len(skipped) != report["skipped_future_step_count"]:
        fail("skipped_steps length must match skipped_future_step_count")
    for index, item in enumerate(executed):
        step = require_object(item, f"executed_steps[{index}]")
        require_string(step.get("step_id"), f"executed_steps[{index}].step_id")
        require_string(step.get("operation"), f"executed_steps[{index}].operation")
        require_string(step.get("tool_id"), f"executed_steps[{index}].tool_id")
    for index, item in enumerate(skipped):
        step = require_object(item, f"skipped_steps[{index}]")
        require_string(step.get("step_id"), f"skipped_steps[{index}].step_id")
        require_string(step.get("reason"), f"skipped_steps[{index}].reason")


def validate_quality(report: dict[str, Any]) -> None:
    quality = require_object(report.get("quality_pass"), "quality_pass")
    for key in sorted(REQUIRED_QUALITY_FLAGS):
        if quality.get(key) is not True:
            fail(f"quality_pass.{key} must be true")
    material_assignment = require_object(report.get("material_assignment"), "material_assignment")
    require_object(material_assignment.get("assigned_parts_by_role"), "material_assignment.assigned_parts_by_role")
    require_object(material_assignment.get("assigned_faces_by_slot"), "material_assignment.assigned_faces_by_slot")
    booleans = require_list(report.get("boolean_applications"), "boolean_applications")
    if len(booleans) < 1:
        fail("boolean_applications must include the socket reveal boolean step")
    first_boolean = require_object(booleans[0], "boolean_applications[0]")
    if require_int(first_boolean.get("applied_modifier_count"), "boolean_applications[0].applied_modifier_count", minimum=1) < 2:
        fail("boolean_applications[0].applied_modifier_count must include east and west socket cuts")
    if require_int(first_boolean.get("failed_modifier_count"), "boolean_applications[0].failed_modifier_count", minimum=0) != 0:
        fail("boolean_applications[0].failed_modifier_count must be 0")
    if require_bool(first_boolean.get("cutter_objects_removed"), "boolean_applications[0].cutter_objects_removed") is not True:
        fail("boolean_applications[0].cutter_objects_removed must be true")
    if require_int(report.get("boolean_cut_count"), "boolean_cut_count", minimum=1) < 2:
        fail("boolean_cut_count must include east and west socket cuts")
    if require_int(report.get("socket_shadow_panel_count"), "socket_shadow_panel_count", minimum=1) < 2:
        fail("socket_shadow_panel_count must include east and west socket shadow panels")
    insets = require_list(report.get("inset_applications"), "inset_applications")
    if len(insets) < 2:
        fail("inset_applications must include both fielded panel inset steps")
    if require_int(report.get("inset_panel_face_count"), "inset_panel_face_count", minimum=1) < 8:
        fail("inset_panel_face_count must include side panels on plinth and shaft")
    extrusions = require_list(report.get("extrusion_applications"), "extrusion_applications")
    if len(extrusions) < 1:
        fail("extrusion_applications must include the shaft panel bead extrusion step")
    if require_int(report.get("extruded_lip_surface_count"), "extruded_lip_surface_count", minimum=1) < 16:
        fail("extruded_lip_surface_count must include four lip surfaces on four shaft panels")
    if require_int(report.get("trim_lip_face_count"), "trim_lip_face_count", minimum=1) < 16:
        fail("trim_lip_face_count must include assigned trim material faces")
    weighted_normals = require_object(report.get("weighted_normals"), "weighted_normals")
    require_string(weighted_normals.get("modifier_type"), "weighted_normals.modifier_type")
    if weighted_normals["modifier_type"] != "WEIGHTED_NORMAL":
        fail("weighted_normals.modifier_type must be WEIGHTED_NORMAL")
    modifiers = require_list(report.get("modifier_applications"), "modifier_applications")
    bevel_count = sum(1 for item in modifiers if isinstance(item, dict) and item.get("modifier_type") == "BEVEL")
    if bevel_count != 2:
        fail("modifier_applications must include exactly two BEVEL applications")


def validate_report(report: dict[str, Any]) -> None:
    if report.get("schema") != REPORT_SCHEMA:
        fail(f"schema must be {REPORT_SCHEMA}")
    if report.get("plan_schema") != PLAN_SCHEMA:
        fail(f"plan_schema must be {PLAN_SCHEMA}")
    if report.get("asset_schema") != ASSET_SCHEMA:
        fail(f"asset_schema must be {ASSET_SCHEMA}")
    require_string(report.get("plan_id"), "plan_id")
    require_string(report.get("source_recipe_id"), "source_recipe_id")
    source_asset_id = require_string(report.get("source_asset_id"), "source_asset_id")
    asset_id = require_string(report.get("asset_id"), "asset_id")
    if asset_id != source_asset_id:
        fail("asset_id must match source_asset_id")
    if require_bool(report.get("generated_outputs_created"), "generated_outputs_created") is not True:
        fail("generated_outputs_created must be true")
    require_string(report.get("blend_path"), "blend_path")
    require_int(report.get("object_count"), "object_count", minimum=1)
    require_int(report.get("mesh_object_count"), "mesh_object_count", minimum=1)
    require_int(report.get("part_object_count"), "part_object_count", minimum=1)
    validate_no_repo_generated_outputs(report)
    validate_rules(report)
    validate_counts(report)
    validate_step_lists(report)
    validate_quality(report)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an asset polish Blender execution report.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    report = load_json(report_path)
    validate_report(report)
    print(
        "PASS asset polish Blender execution report validation: "
        f"executed={report['executed_step_count']} skipped_future={report['skipped_future_step_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
