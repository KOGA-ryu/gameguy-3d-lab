#!/usr/bin/env python3
"""Tests for the Blender tool-plan execution adapter's validation mode."""

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
EXECUTOR = ROOT / "scripts" / "execute_blender_tool_plan_v0.py"


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
    manifest = load_json(out_root / "manifest.json")
    return out_root / manifest["plans"][0]["path"]


def compile_plan_for_asset(out_root: Path, asset_id: str) -> Path:
    subprocess.run(
        [sys.executable, str(COMPILER), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = load_json(out_root / "manifest.json")
    for row in manifest["plans"]:
        plan_path = out_root / row["path"]
        plan = load_json(plan_path)
        if plan["asset_id"] == asset_id:
            return plan_path
    raise AssertionError(f"missing compiled plan for {asset_id}")


class BlenderToolPlanExecutionAdapterTests(unittest.TestCase):
    def test_validate_only_consumes_compiled_tool_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan(tmp_root / "plans")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["schema"], "blender_tool_plan_execution_report_v0")
        self.assertEqual(report["plan_schema"], "gameguy_tool_plan_v0")
        self.assertEqual(report["plan_id"], "gothic_stone_banister_post_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "banister_post")
        self.assertEqual(report["style"], "gothic_stone")
        self.assertEqual(report["step_count"], 32)
        self.assertEqual(report["supported_step_count"], 32)
        self.assertEqual(report["unique_tool_count"], 24)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])
        self.assertFalse(report["rules"]["reads_source_intent_recipe"])
        self.assertFalse(report["rules"]["runs_tool_plan_compiler"])
        self.assertTrue(report["rules"]["executes_only_supported_deterministic_steps"])

    def test_validate_only_accepts_window_frame_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan_for_asset(tmp_root / "plans", "gothic_stone_window_frame_tool_plan_v0")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["plan_id"], "gothic_stone_window_frame_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "window_frame")
        self.assertEqual(report["step_count"], 25)
        self.assertEqual(report["supported_step_count"], 25)
        self.assertEqual(report["unique_tool_count"], 22)
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])

    def test_validate_only_accepts_fence_post_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan_for_asset(tmp_root / "plans", "gothic_stone_fence_post_tool_plan_v0")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["plan_id"], "gothic_stone_fence_post_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "fence_post")
        self.assertEqual(report["step_count"], 32)
        self.assertEqual(report["supported_step_count"], 32)
        self.assertEqual(report["unique_tool_count"], 24)
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])

    def test_validate_only_accepts_rail_segment_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan_for_asset(tmp_root / "plans", "gothic_stone_rail_segment_tool_plan_v0")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["plan_id"], "gothic_stone_rail_segment_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "rail_segment")
        self.assertEqual(report["step_count"], 28)
        self.assertEqual(report["supported_step_count"], 28)
        self.assertEqual(report["unique_tool_count"], 22)
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])

    def test_validate_only_accepts_column_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan_for_asset(tmp_root / "plans", "gothic_stone_column_tool_plan_v0")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["plan_id"], "gothic_stone_column_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "column")
        self.assertEqual(report["step_count"], 31)
        self.assertEqual(report["supported_step_count"], 31)
        self.assertEqual(report["unique_tool_count"], 24)
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])

    def test_validate_only_accepts_door_frame_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan_for_asset(tmp_root / "plans", "gothic_stone_door_frame_tool_plan_v0")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["plan_id"], "gothic_stone_door_frame_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "door_frame")
        self.assertEqual(report["step_count"], 25)
        self.assertEqual(report["supported_step_count"], 25)
        self.assertEqual(report["unique_tool_count"], 22)
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])

    def test_validate_only_accepts_guard_panel_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan_for_asset(tmp_root / "plans", "gothic_panel_guard_tool_plan_v0")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS Blender tool-plan adapter validation", result.stdout)
        self.assertEqual(report["plan_id"], "gothic_panel_guard_tool_plan_v0_compiled")
        self.assertEqual(report["asset_family"], "guard_panel")
        self.assertEqual(report["step_count"], 46)
        self.assertEqual(report["supported_step_count"], 46)
        self.assertEqual(report["unique_tool_count"], 24)
        self.assertTrue(report["rules"]["consumes_gameguy_tool_plan_v0"])

    def test_validate_only_rejects_unsupported_tool_id_before_output(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan(tmp_root / "plans")
            plan = load_json(plan_path)
            plan["steps"][0]["tool_id"] = "sculpt_draw"
            bad_plan_path = tmp_root / "bad_plan.json"
            report_path = tmp_root / "executor_report.json"
            bad_plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(bad_plan_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported tool_id `sculpt_draw`", result.stderr)
        self.assertFalse(report_path.exists())

    def test_validate_only_rejects_non_deterministic_step(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_plan(tmp_root / "plans")
            plan = load_json(plan_path)
            plan["steps"][0]["deterministic"] = False
            bad_plan_path = tmp_root / "bad_plan.json"
            bad_plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(EXECUTOR), "--plan", str(bad_plan_path), "--validate-only"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be deterministic", result.stderr)


if __name__ == "__main__":
    unittest.main()
