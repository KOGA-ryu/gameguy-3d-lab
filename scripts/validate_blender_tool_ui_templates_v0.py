#!/usr/bin/env python3
"""Validate blank Blender tool-plan UI templates.

This checks the machine-readable UI layer against the tool dictionary and the
current generic Blender executor. It does not import Blender, run tools, render,
or create asset outputs.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_ui_templates_v0.json"
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_EXECUTOR = ROOT / "scripts" / "execute_blender_tool_plan_v0.py"
TEMPLATE_SCHEMA = "blender_tool_ui_templates_v0"
DICTIONARY_SCHEMA = "blender_tool_dictionary_v0"
PLAN_SCHEMA = "gameguy_tool_plan_v0"
ALLOWED_CONTROL_KINDS = {
    "boolean",
    "enum",
    "integer",
    "json_array",
    "json_object",
    "material_map",
    "number",
    "object_alias",
    "object_alias_list",
    "string",
    "vector3",
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
        fail(f"{path} must contain a JSON object")
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


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_vector3(value: Any, field: str) -> None:
    if not isinstance(value, list) or len(value) != 3:
        fail(f"{field} must be a three-number list")
    for index, item in enumerate(value):
        if not is_number(item):
            fail(f"{field}[{index}] must be a finite number")


def supported_tools_from_executor(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "SUPPORTED_TOOLS":
                value = ast.literal_eval(node.value)
                if not isinstance(value, set) or not all(isinstance(item, str) for item in value):
                    fail("SUPPORTED_TOOLS must be a set of strings")
                return value
    fail(f"{path} does not define SUPPORTED_TOOLS")


def validate_dictionary(dictionary: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if dictionary.get("schema") != DICTIONARY_SCHEMA:
        fail(f"tool dictionary schema must be {DICTIONARY_SCHEMA}")
    stages = require_string_list(dictionary.get("stages"), "dictionary.stages")
    tools = require_list(dictionary.get("tools"), "dictionary.tools")
    if dictionary.get("tool_count") != len(tools):
        fail("dictionary.tool_count must match tools length")
    tool_map: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(tools):
        tool = require_object(item, f"dictionary.tools[{index}]")
        tool_id = require_string(tool.get("tool_id"), f"dictionary.tools[{index}].tool_id")
        if tool_id in tool_map:
            fail(f"duplicate tool_id `{tool_id}` in dictionary")
        stage = require_string(tool.get("stage"), f"{tool_id}.stage")
        if stage not in stages:
            fail(f"{tool_id}.stage is not in dictionary stages")
        require_bool(tool.get("deterministic"), f"{tool_id}.deterministic")
        require_string(tool.get("execution_lane"), f"{tool_id}.execution_lane")
        tool_map[tool_id] = tool
    return tool_map, stages


def validate_control(control: dict[str, Any], template: dict[str, Any], field: str) -> str:
    param = require_string(control.get("param"), f"{field}.param")
    require_string(control.get("label"), f"{field}.label")
    kind = require_string(control.get("kind"), f"{field}.kind")
    if kind not in ALLOWED_CONTROL_KINDS:
        fail(f"{field}.kind `{kind}` is not allowed")
    if "default" not in control:
        fail(f"{field}.default is required")
    default = control["default"]
    if kind == "number":
        if not is_number(default):
            fail(f"{field}.default must be a number")
    elif kind == "integer":
        if not isinstance(default, int) or isinstance(default, bool):
            fail(f"{field}.default must be an integer")
    elif kind == "boolean":
        if not isinstance(default, bool):
            fail(f"{field}.default must be a boolean")
    elif kind == "enum":
        options = require_string_list(control.get("options"), f"{field}.options")
        if default not in options:
            fail(f"{field}.default must be one of options")
    elif kind == "vector3":
        validate_vector3(default, f"{field}.default")
    elif kind in {"json_array", "object_alias_list"}:
        if not isinstance(default, list):
            fail(f"{field}.default must be a list")
    elif kind in {"json_object", "material_map"}:
        if not isinstance(default, dict):
            fail(f"{field}.default must be an object")
    elif kind in {"string", "object_alias"}:
        if not isinstance(default, str):
            fail(f"{field}.default must be a string")
    if "min" in control and not is_number(control["min"]):
        fail(f"{field}.min must be a finite number")
    if "max" in control and not is_number(control["max"]):
        fail(f"{field}.max must be a finite number")
    if "step" in control and not is_number(control["step"]):
        fail(f"{field}.step must be a finite number")
    return param


def validate_templates(templates: dict[str, Any], dictionary: dict[str, dict[str, Any]], stages: list[str], supported_tools: set[str]) -> dict[str, Any]:
    if templates.get("schema") != TEMPLATE_SCHEMA:
        fail(f"template schema must be {TEMPLATE_SCHEMA}")
    if templates.get("plan_schema") != PLAN_SCHEMA:
        fail(f"plan_schema must be {PLAN_SCHEMA}")
    if require_string_list(templates.get("stage_order"), "stage_order") != stages:
        fail("stage_order must match dictionary.stages")
    rules = require_object(templates.get("rules"), "rules")
    for key in (
        "templates_cover_executor_supported_tools",
        "templates_only_cover_executable_tools",
        "ui_writes_step_params_only",
        "step_order_and_stage_are_ui_owned",
        "blender_execution_requires_final_object",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")
    control_kinds = set(require_string_list(templates.get("control_kinds"), "control_kinds"))
    if control_kinds != ALLOWED_CONTROL_KINDS:
        fail("control_kinds must exactly match validator allowed control kinds")

    template_items = require_list(templates.get("templates"), "templates")
    template_map: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(template_items):
        template = require_object(item, f"templates[{index}]")
        tool_id = require_string(template.get("tool_id"), f"templates[{index}].tool_id")
        if tool_id in template_map:
            fail(f"duplicate template for `{tool_id}`")
        if tool_id not in supported_tools:
            fail(f"template `{tool_id}` is not supported by executor")
        if tool_id not in dictionary:
            fail(f"template `{tool_id}` is not in tool dictionary")
        dictionary_tool = dictionary[tool_id]
        stage = require_string(template.get("stage"), f"{tool_id}.stage")
        if stage != dictionary_tool["stage"]:
            fail(f"{tool_id}.stage must match tool dictionary")
        if template.get("status") != "exec":
            fail(f"{tool_id}.status must be exec")
        require_string(template.get("step_id_prefix"), f"{tool_id}.step_id_prefix")
        required_params = set(require_string_list(template.get("required_params"), f"{tool_id}.required_params", allow_empty=True))
        step_template = require_object(template.get("step_template"), f"{tool_id}.step_template")
        if step_template.get("tool_id") != tool_id:
            fail(f"{tool_id}.step_template.tool_id must match template tool_id")
        if step_template.get("stage") != stage:
            fail(f"{tool_id}.step_template.stage must match template stage")
        if step_template.get("deterministic") is not True:
            fail(f"{tool_id}.step_template.deterministic must be true")
        params = require_object(step_template.get("params"), f"{tool_id}.step_template.params")
        for param in sorted(required_params):
            if param not in params:
                fail(f"{tool_id}.step_template.params must include required param `{param}`")
        controls = require_list(template.get("controls"), f"{tool_id}.controls")
        seen_controls: set[str] = set()
        for control_index, control_value in enumerate(controls):
            control = require_object(control_value, f"{tool_id}.controls[{control_index}]")
            param = validate_control(control, template, f"{tool_id}.controls[{control_index}]")
            if param in seen_controls:
                fail(f"{tool_id}.controls contains duplicate param `{param}`")
            seen_controls.add(param)
        for param in sorted(required_params):
            if param not in seen_controls:
                fail(f"{tool_id}.controls must include required param `{param}`")
        template_map[tool_id] = template

    missing = sorted(supported_tools - set(template_map))
    extra = sorted(set(template_map) - supported_tools)
    if missing:
        fail(f"missing templates for supported tools: {', '.join(missing)}")
    if extra:
        fail(f"templates include unsupported tools: {', '.join(extra)}")
    return {
        "schema": "blender_tool_ui_template_validation_report_v0",
        "template_schema": templates["schema"],
        "dictionary_tool_count": len(dictionary),
        "executor_supported_tool_count": len(supported_tools),
        "template_count": len(template_map),
        "stage_count": len(stages),
        "control_kind_count": len(control_kinds),
        "validated_tool_ids": sorted(template_map),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Blender tool UI templates.")
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--executor", type=Path, default=DEFAULT_EXECUTOR)
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    templates_path = args.templates if args.templates.is_absolute() else ROOT / args.templates
    dictionary_path = args.dictionary if args.dictionary.is_absolute() else ROOT / args.dictionary
    executor_path = args.executor if args.executor.is_absolute() else ROOT / args.executor
    dictionary, stages = validate_dictionary(load_json(dictionary_path))
    supported_tools = supported_tools_from_executor(executor_path)
    report = validate_templates(load_json(templates_path), dictionary, stages, supported_tools)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS Blender tool UI templates: "
        f"templates={report['template_count']} supported={report['executor_supported_tool_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
