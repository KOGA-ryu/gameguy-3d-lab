#!/usr/bin/env python3
"""Tests for the blank tool-plan UI editor backend."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CREATE_BLANK = ROOT / "scripts" / "create_blank_tool_plan_v0.py"
ADD_STEP = ROOT / "scripts" / "add_tool_plan_step_v0.py"
UI_VALIDATOR = ROOT / "scripts" / "validate_tool_plan_against_ui_templates_v0.py"
BLENDER_VALIDATOR = ROOT / "scripts" / "execute_blender_tool_plan_v0.py"
ASCII_DRYRUN = ROOT / "scripts" / "render_tool_plan_ascii_dryrun_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)


class ToolPlanUiEditorTests(unittest.TestCase):
    def test_add_step_canonicalizes_stage_order_and_feeds_dryrun(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            plan_path = root / "plan.json"
            run_command([sys.executable, str(CREATE_BLANK), "--out", str(plan_path)])
            run_command([sys.executable, str(ADD_STEP), "--plan", str(plan_path), "--tool-id", "primitive_cube_add"])
            run_command(
                [
                    sys.executable,
                    str(ADD_STEP),
                    "--plan",
                    str(plan_path),
                    "--tool-id",
                    "modifier_bevel",
                    "--set",
                    "width_m=0.04",
                    "--set",
                    "segments=2",
                ]
            )
            run_command([sys.executable, str(ADD_STEP), "--plan", str(plan_path), "--tool-id", "join_objects"])
            ui_report = root / "ui_validation.json"
            blender_report = root / "blender_validation.json"
            ascii_out = root / "ascii"
            run_command([sys.executable, str(UI_VALIDATOR), "--plan", str(plan_path), "--json-report", str(ui_report)])
            run_command(
                [
                    sys.executable,
                    str(BLENDER_VALIDATOR),
                    "--plan",
                    str(plan_path),
                    "--validate-only",
                    "--json-report",
                    str(blender_report),
                ]
            )
            run_command(
                [
                    sys.executable,
                    str(ASCII_DRYRUN),
                    "--plan",
                    str(plan_path),
                    "--out",
                    str(ascii_out),
                    "--width",
                    "80",
                    "--height",
                    "50",
                ]
            )
            plan = load_json(plan_path)
            report = load_json(ui_report)
            ascii_report = load_json(ascii_out / "ascii_dryrun_report.json")

        self.assertEqual([step["tool_id"] for step in plan["steps"]], ["primitive_cube_add", "join_objects", "modifier_bevel"])
        self.assertEqual([step["order"] for step in plan["steps"]], [10, 20, 30])
        self.assertTrue(report["valid"])
        self.assertEqual(report["step_count"], 3)
        self.assertEqual(ascii_report["supported_step_count"], 1)
        self.assertEqual(ascii_report["skipped_step_count"], 2)

    def test_ui_validator_rejects_bad_control_value(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            plan_path = root / "plan.json"
            report_path = root / "ui_validation.json"
            run_command([sys.executable, str(CREATE_BLANK), "--out", str(plan_path)])
            run_command([sys.executable, str(ADD_STEP), "--plan", str(plan_path), "--tool-id", "primitive_cube_add"])
            run_command([sys.executable, str(ADD_STEP), "--plan", str(plan_path), "--tool-id", "join_objects"])
            run_command(
                [
                    sys.executable,
                    str(ADD_STEP),
                    "--plan",
                    str(plan_path),
                    "--tool-id",
                    "modifier_bevel",
                    "--set",
                    "segments=0",
                ]
            )
            result = subprocess.run(
                [sys.executable, str(UI_VALIDATOR), "--plan", str(plan_path), "--json-report", str(report_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(report["valid"])
        self.assertIn("bevel_001.params.segments must be >= 1", report["errors"])


if __name__ == "__main__":
    unittest.main()
