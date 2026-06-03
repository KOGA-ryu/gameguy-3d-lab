#!/usr/bin/env python3
"""Tests for compiled gameguy_tool_plan_v0 validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_blender_tool_plan_v0.py"
VALIDATOR = ROOT / "scripts" / "validate_gameguy_tool_plan_v0.py"
DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def compile_plan(out_root: Path) -> Path:
    subprocess.run(
        [sys.executable, str(COMPILER), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return out_root / "manifest.json"


def first_plan_path(manifest_path: Path) -> Path:
    manifest = load_json(manifest_path)
    return manifest_path.parent / manifest["plans"][0]["path"]


def plan_path_by_asset(manifest_path: Path, asset_id: str) -> Path:
    manifest = load_json(manifest_path)
    for row in manifest["plans"]:
        plan_path = manifest_path.parent / row["path"]
        if load_json(plan_path)["asset_id"] == asset_id:
            return plan_path
    raise AssertionError(f"missing plan for {asset_id}")


def apply_tool_dictionary_fields(step: dict[str, Any], tool_id: str) -> None:
    dictionary = load_json(DICTIONARY)
    tools = {tool["tool_id"]: tool for tool in dictionary["tools"]}
    tool = tools[tool_id]
    step["stage"] = tool["stage"]
    step["tool_id"] = tool_id
    for field in ("category", "execution_lane", "deterministic", "blender_api", "inputs", "outputs", "preconditions", "postconditions"):
        step[field] = tool[field]


def run_validator(manifest_path: Path, json_report: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(VALIDATOR), "--manifest", str(manifest_path)]
    if json_report is not None:
        command.extend(["--json-report", str(json_report)])
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)


class GameguyToolPlanValidatorTests(unittest.TestCase):
    def test_validates_compiled_tool_plan_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "plans"
            report_path = Path(tmp) / "tool_plan_validation.json"
            manifest_path = compile_plan(out_root)
            result = run_validator(manifest_path, report_path)
            report = load_json(report_path)

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS gameguy_tool_plan_v0 validation", result.stdout)
        self.assertEqual(report["schema"], "gameguy_tool_plan_v0_validation_result_v0")
        self.assertEqual(report["plan_count"], 4)
        self.assertEqual(report["total_steps"], 114)
        self.assertEqual(report["unique_tool_count"], 24)
        self.assertFalse(report["generated_outputs_created"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertFalse(report["rules"]["runs_tool_plan_compiler"])
        self.assertTrue(report["rules"]["validates_known_tool_ids"])
        self.assertTrue(report["rules"]["validates_stage_order"])
        self.assertTrue(report["rules"]["validates_asset_family_sequence_policy"])

    def test_rejects_unknown_tool_id(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            manifest_path = compile_plan(Path(tmp) / "plans")
            plan_path = first_plan_path(manifest_path)
            plan = load_json(plan_path)
            plan["steps"][0]["tool_id"] = "definitely_missing_tool"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = run_validator(manifest_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uses unknown tool_id `definitely_missing_tool`", result.stderr)

    def test_rejects_unstable_step_order(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            manifest_path = compile_plan(Path(tmp) / "plans")
            plan_path = first_plan_path(manifest_path)
            plan = load_json(plan_path)
            plan["steps"][0]["order"] = 2
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = run_validator(manifest_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("steps[0].order must be 1", result.stderr)

    def test_rejects_compiler_boundary_violation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            manifest_path = compile_plan(Path(tmp) / "plans")
            plan_path = first_plan_path(manifest_path)
            plan = load_json(plan_path)
            plan["rules"]["compiler_executes_blender"] = True
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = run_validator(manifest_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rules.compiler_executes_blender must be false", result.stderr)

    def test_rejects_tool_outside_asset_family_policy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            manifest_path = compile_plan(Path(tmp) / "plans")
            plan_path = plan_path_by_asset(manifest_path, "gothic_stone_window_frame_tool_plan_v0")
            plan = load_json(plan_path)
            apply_tool_dictionary_fields(plan["steps"][0], "primitive_cylinder_add")
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = run_validator(manifest_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the window_frame sequence policy", result.stderr)

    def test_rejects_asset_family_tool_order_violation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            manifest_path = compile_plan(Path(tmp) / "plans")
            plan_path = plan_path_by_asset(manifest_path, "gothic_stone_banister_post_tool_plan_v0")
            plan = load_json(plan_path)
            plan["steps"][9], plan["steps"][10] = plan["steps"][10], plan["steps"][9]
            plan["steps"][9]["order"] = 10
            plan["steps"][10]["order"] = 11
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = run_validator(manifest_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sequence policy requires `object_duplicate_radial` before `modifier_boolean`", result.stderr)

    def test_rejects_media_or_mesh_output_in_tool_plan_root(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "plans"
            manifest_path = compile_plan(out_root)
            (out_root / "leaked_preview.glb").write_text("not allowed\n", encoding="utf-8")
            result = run_validator(manifest_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generated media/mesh output is not allowed", result.stderr)


if __name__ == "__main__":
    unittest.main()
