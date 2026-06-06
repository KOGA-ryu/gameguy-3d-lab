#!/usr/bin/env python3
"""Create a blank gameguy_tool_plan_v0 draft for the tool-plan workbench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_blank_tool_plan_workbench_v0/blank_tool_plan_v0.json")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"FAIL {path} must contain a JSON object")
    return data


def stage_order(dictionary_path: Path) -> list[str]:
    dictionary = load_json(dictionary_path)
    stages = dictionary.get("stages")
    if not isinstance(stages, list) or not all(isinstance(item, str) and item for item in stages):
        raise SystemExit("FAIL dictionary.stages must be a non-empty string list")
    return stages


def blank_plan(args: argparse.Namespace) -> dict[str, Any]:
    dictionary_path = args.dictionary if args.dictionary.is_absolute() else ROOT / args.dictionary
    return {
        "schema": "gameguy_tool_plan_v0",
        "plan_id": args.plan_id,
        "source_schema": "asset_mill_tool_plan_recipe_bundle_v0",
        "asset_id": args.asset_id,
        "asset_family": args.asset_family,
        "style": args.style,
        "stage_order": stage_order(dictionary_path),
        "rules": {
            "blender_adapter_must_consume_plan": True
        },
        "steps": [],
        "summary": {
            "step_count": 0
        }
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a blank gameguy_tool_plan_v0 JSON draft.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--plan-id", default="manual_blank_tool_plan_v0")
    parser.add_argument("--asset-id", default="manual_asset_v0")
    parser.add_argument("--asset-family", default="manual_asset")
    parser.add_argument("--style", default="manual")
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = blank_plan(args)
    text = json.dumps(plan, indent=2) + "\n"
    if args.stdout:
        print(text, end="")
    else:
        out = args.out if args.out.is_absolute() else ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"PASS blank tool plan: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
