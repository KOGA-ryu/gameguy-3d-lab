#!/usr/bin/env python3
"""Validate a hand-edited gameguy_tool_plan_v0 against UI templates."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_ui_templates_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL missing JSON file: {path}", file=sys.stderr)
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        print(f"FAIL malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(data, dict):
        print(f"FAIL {path} must contain a JSON object", file=sys.stderr)
        raise SystemExit(1)
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def as_template_map(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    if data.get("schema") != "blender_tool_ui_templates_v0":
        errors.append("templates.schema must be blender_tool_ui_templates_v0")
    stage_order = data.get("stage_order")
    if not isinstance(stage_order, list) or not all(isinstance(stage, str) and stage for stage in stage_order):
        errors.append("templates.stage_order must be a non-empty string list")
        stage_order = []
    templates: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(data.get("templates", [])):
        if not isinstance(item, dict):
            errors.append(f"templates[{index}] must be an object")
            continue
        tool_id = item.get("tool_id")
        if not isinstance(tool_id, str) or not tool_id:
            errors.append(f"templates[{index}].tool_id must be a non-empty string")
            continue
        templates[tool_id] = item
    if errors:
        print("FAIL invalid UI templates: " + "; ".join(errors), file=sys.stderr)
        raise SystemExit(1)
    return templates, stage_order


def control_map(template: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    controls = template.get("controls")
    if isinstance(controls, list):
        for control in controls:
            if isinstance(control, dict) and isinstance(control.get("param"), str):
                result[control["param"]] = control
    return result


def validate_scalar_range(value: float, control: dict[str, Any], field: str, errors: list[str]) -> None:
    if "min" in control and finite_number(control["min"]) and value < float(control["min"]):
        errors.append(f"{field} must be >= {control['min']}")
    if "max" in control and finite_number(control["max"]) and value > float(control["max"]):
        errors.append(f"{field} must be <= {control['max']}")


def validate_value(value: Any, control: dict[str, Any], field: str, errors: list[str]) -> None:
    kind = control.get("kind")
    if kind == "number":
        if not finite_number(value):
            errors.append(f"{field} must be a number")
        else:
            validate_scalar_range(float(value), control, field, errors)
    elif kind == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field} must be an integer")
        else:
            validate_scalar_range(float(value), control, field, errors)
    elif kind == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field} must be a boolean")
    elif kind == "enum":
        options = control.get("options")
        if not isinstance(options, list) or value not in options:
            errors.append(f"{field} must be one of {options}")
    elif kind == "vector3":
        if not isinstance(value, list) or len(value) != 3:
            errors.append(f"{field} must be a three-number list")
            return
        for index, item in enumerate(value):
            if not finite_number(item):
                errors.append(f"{field}[{index}] must be a number")
            else:
                validate_scalar_range(float(item), control, f"{field}[{index}]", errors)
    elif kind in {"json_array", "object_alias_list"}:
        if not isinstance(value, list):
            errors.append(f"{field} must be a list")
    elif kind in {"json_object", "material_map"}:
        if not isinstance(value, dict):
            errors.append(f"{field} must be an object")
    elif kind in {"string", "object_alias"}:
        if not isinstance(value, str):
            errors.append(f"{field} must be a string")
    else:
        errors.append(f"{field} uses unsupported control kind `{kind}`")


def validate_plan(plan: dict[str, Any], templates: dict[str, dict[str, Any]], stage_order: list[str]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if plan.get("schema") != "gameguy_tool_plan_v0":
        errors.append("plan.schema must be gameguy_tool_plan_v0")
    if plan.get("source_schema") != "asset_mill_tool_plan_recipe_bundle_v0":
        errors.append("plan.source_schema must be asset_mill_tool_plan_recipe_bundle_v0")
    if plan.get("stage_order") != stage_order:
        errors.append("plan.stage_order must match template stage_order")
    rules = plan.get("rules")
    if not isinstance(rules, dict) or rules.get("blender_adapter_must_consume_plan") is not True:
        errors.append("plan.rules.blender_adapter_must_consume_plan must be true")

    steps = plan.get("steps")
    if not isinstance(steps, list):
        errors.append("plan.steps must be a list")
        steps = []

    summary = plan.get("summary")
    if not isinstance(summary, dict):
        errors.append("plan.summary must be an object")
        summary = {}
    elif summary.get("step_count") != len(steps):
        errors.append("plan.summary.step_count must match steps length")

    stage_indexes = {stage: index for index, stage in enumerate(stage_order)}
    previous_order = -1
    previous_stage = -1
    seen_step_ids: set[str] = set()
    final_object_created = False
    bounds_calculated = False
    visible_geometry_created = False
    unique_tools: set[str] = set()

    for index, value in enumerate(steps):
        field = f"steps[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{field} must be an object")
            continue
        step_id = value.get("step_id")
        if not isinstance(step_id, str) or not step_id:
            errors.append(f"{field}.step_id must be a non-empty string")
            step_id = field
        elif step_id in seen_step_ids:
            errors.append(f"{step_id}.step_id is duplicated")
        seen_step_ids.add(step_id)

        order = value.get("order")
        if not isinstance(order, int) or isinstance(order, bool) or order <= previous_order:
            errors.append(f"{step_id}.order must strictly increase")
        elif order % 10 != 0:
            warnings.append(f"{step_id}.order is valid but not on the UI editor's 10-step spacing")
        if isinstance(order, int) and not isinstance(order, bool):
            previous_order = order

        tool_id = value.get("tool_id")
        if not isinstance(tool_id, str) or not tool_id:
            errors.append(f"{step_id}.tool_id must be a non-empty string")
            continue
        template = templates.get(tool_id)
        if template is None:
            errors.append(f"{step_id}.tool_id `{tool_id}` has no executable UI template")
            continue
        unique_tools.add(tool_id)

        stage = value.get("stage")
        template_stage = template.get("stage")
        if stage != template_stage:
            errors.append(f"{step_id}.stage must be `{template_stage}` for {tool_id}")
        stage_index = stage_indexes.get(stage)
        if stage_index is None:
            errors.append(f"{step_id}.stage uses unknown stage `{stage}`")
        elif stage_index < previous_stage:
            errors.append(f"{step_id} is out of stage order")
        else:
            previous_stage = stage_index

        if value.get("status") != template.get("status"):
            errors.append(f"{step_id}.status must be `{template.get('status')}`")
        if value.get("deterministic") is not True:
            errors.append(f"{step_id}.deterministic must be true")

        if template.get("requires_final_object") is True and not final_object_created:
            errors.append(f"{step_id} requires an earlier final object step such as join_objects")
        if template.get("requires_bounds") is True and not bounds_calculated:
            errors.append(f"{step_id} requires an earlier calculate_bounds step")

        params = value.get("params")
        if not isinstance(params, dict):
            errors.append(f"{step_id}.params must be an object")
            params = {}
        controls = control_map(template)
        allowed_params = set(controls) | set(template.get("step_template", {}).get("params", {}))
        for required in template.get("required_params", []):
            if required not in params:
                errors.append(f"{step_id}.params.{required} is required")
        for param, param_value in params.items():
            if param not in allowed_params:
                errors.append(f"{step_id}.params.{param} is not part of the v0 UI template contract")
                continue
            control = controls.get(param)
            if control is not None:
                validate_value(param_value, control, f"{step_id}.params.{param}", errors)

        if template.get("creates_visible_geometry") is True:
            visible_geometry_created = True
        if template.get("creates_final_object") is True:
            final_object_created = True
            if not visible_geometry_created:
                warnings.append(f"{step_id} creates a final object before any visible geometry step")
        if tool_id == "calculate_bounds":
            bounds_calculated = True

    return {
        "schema": "tool_plan_ui_template_validation_report_v0",
        "plan_schema": plan.get("schema"),
        "plan_id": plan.get("plan_id"),
        "asset_id": plan.get("asset_id"),
        "step_count": len(steps),
        "unique_tool_count": len(unique_tools),
        "unique_tools": sorted(unique_tools),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rules": {
            "validates_against_blender_tool_ui_templates_v0": True,
            "imports_blender": False,
            "executes_blender": False,
            "creates_media_or_mesh": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a hand-edited tool plan against UI templates.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    templates, stage_order = as_template_map(load_json(args.templates))
    plan = load_json(args.plan)
    report = validate_plan(plan, templates, stage_order)
    if args.json_report is not None:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["valid"]:
        print(f"PASS tool plan UI template validation: steps={report['step_count']} tools={report['unique_tool_count']}")
        return 0
    print(f"FAIL tool plan UI template validation: errors={report['error_count']}", file=sys.stderr)
    for error in report["errors"]:
        print(f"- {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
