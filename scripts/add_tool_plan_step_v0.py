#!/usr/bin/env python3
"""Append a UI-template-backed step to a blank gameguy_tool_plan_v0 draft."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_ui_templates_v0.json"


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


def load_templates(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    data = load_json(path)
    if data.get("schema") != "blender_tool_ui_templates_v0":
        fail("template schema must be blender_tool_ui_templates_v0")
    stage_order = data.get("stage_order")
    if not isinstance(stage_order, list) or not all(isinstance(stage, str) and stage for stage in stage_order):
        fail("template stage_order must be a non-empty string list")
    templates: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(data.get("templates", [])):
        if not isinstance(item, dict):
            fail(f"templates[{index}] must be an object")
        tool_id = item.get("tool_id")
        if not isinstance(tool_id, str) or not tool_id:
            fail(f"templates[{index}].tool_id must be a non-empty string")
        templates[tool_id] = item
    return templates, stage_order


def parse_param_overrides(values: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            fail(f"--set value `{value}` must be param=json")
        key, raw = value.split("=", 1)
        if not key:
            fail("--set param name must not be empty")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        result[key] = parsed
    return result


def next_step_id(prefix: str, steps: list[dict[str, Any]]) -> str:
    used = {step.get("step_id") for step in steps if isinstance(step, dict)}
    index = 1
    while True:
        candidate = f"{prefix}_{index:03d}"
        if candidate not in used:
            return candidate
        index += 1


def stage_indexes(stage_order: list[str]) -> dict[str, int]:
    return {stage: index for index, stage in enumerate(stage_order)}


def canonicalize_steps(plan: dict[str, Any], stage_order: list[str]) -> None:
    steps = plan.get("steps")
    if not isinstance(steps, list):
        fail("plan.steps must be a list")
    indexes = stage_indexes(stage_order)
    indexed_steps: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(steps):
        if not isinstance(item, dict):
            fail(f"steps[{index}] must be an object")
        stage = item.get("stage")
        if stage not in indexes:
            fail(f"steps[{index}].stage uses unknown stage `{stage}`")
        indexed_steps.append((indexes[stage], index, item))
    indexed_steps.sort(key=lambda item: (item[0], item[1]))
    plan["steps"] = [item[2] for item in indexed_steps]
    for index, step in enumerate(plan["steps"], start=1):
        step["order"] = index * 10
    summary = plan.setdefault("summary", {})
    if not isinstance(summary, dict):
        fail("plan.summary must be an object")
    summary["step_count"] = len(plan["steps"])
    summary["unique_tools"] = sorted({step["tool_id"] for step in plan["steps"] if isinstance(step.get("tool_id"), str)})
    summary["ui_canonicalized_stage_order"] = True


def make_step(template: dict[str, Any], step_id: str, overrides: dict[str, Any]) -> dict[str, Any]:
    step_template = template.get("step_template")
    if not isinstance(step_template, dict):
        fail(f"{template.get('tool_id', '<unknown>')}.step_template must be an object")
    params = copy.deepcopy(step_template.get("params", {}))
    if not isinstance(params, dict):
        fail(f"{template.get('tool_id', '<unknown>')}.step_template.params must be an object")
    params.update(overrides)
    return {
        "step_id": step_id,
        "order": 0,
        "stage": step_template["stage"],
        "tool_id": step_template["tool_id"],
        "status": template["status"],
        "deterministic": step_template["deterministic"],
        "params": params,
    }


def add_step(args: argparse.Namespace) -> dict[str, Any]:
    templates, template_stage_order = load_templates(args.templates)
    plan = load_json(args.plan)
    if plan.get("schema") != "gameguy_tool_plan_v0":
        fail("plan schema must be gameguy_tool_plan_v0")
    if plan.get("stage_order") != template_stage_order:
        fail("plan.stage_order must match template stage_order")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        fail("plan.steps must be a list")
    template = templates.get(args.tool_id)
    if template is None:
        fail(f"tool_id `{args.tool_id}` has no executable UI template")
    prefix = args.step_id_prefix or template.get("step_id_prefix")
    if not isinstance(prefix, str) or not prefix:
        fail(f"{args.tool_id}.step_id_prefix must be a non-empty string")
    step_id = args.step_id or next_step_id(prefix, steps)
    if any(isinstance(step, dict) and step.get("step_id") == step_id for step in steps):
        fail(f"step_id `{step_id}` already exists")
    plan["steps"].append(make_step(template, step_id, parse_param_overrides(args.set)))
    canonicalize_steps(plan, template_stage_order)
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a Blender tool step from the UI template catalog.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--tool-id", required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--step-id")
    parser.add_argument("--step-id-prefix")
    parser.add_argument("--set", action="append", default=[], metavar="PARAM=JSON")
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = add_step(args)
    text = json.dumps(plan, indent=2) + "\n"
    if args.stdout:
        print(text, end="")
    else:
        out = args.out or args.plan
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"PASS added {args.tool_id}: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
