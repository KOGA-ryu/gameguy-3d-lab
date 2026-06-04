#!/usr/bin/env python3
"""Tests for asset polish Blender adapter validate-only reports."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_asset_polish_tool_plan_v0.py"
ADAPTER = ROOT / "scripts" / "validate_asset_polish_blender_adapter_v0.py"
EXECUTOR = ROOT / "scripts" / "execute_asset_polish_blender_adapter_v0.py"
PUMP = ROOT / "scripts" / "asset_pump_v0.py"
BLOCKY_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "blocky_shape_grammar_assets_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def compile_to(out_root: Path) -> Path:
    subprocess.run(
        [sys.executable, str(COMPILER), "--clean", "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = load_json(out_root / "manifest.json")
    return out_root / manifest["plans"][0]["path"]


def pump_blocky_asset(out_root: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            str(PUMP),
            "--bundle",
            str(BLOCKY_BUNDLE),
            "--clean",
            "--out",
            str(out_root),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return out_root / "assets" / "blocky_fence_post_v0.json"


class AssetPolishBlenderAdapterValidationTests(unittest.TestCase):
    def test_validate_only_reports_supported_and_future_steps(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_to(tmp_root / "polish")
            report_path = tmp_root / "adapter_report.json"
            result = subprocess.run(
                [sys.executable, str(ADAPTER), "--plan", str(plan_path), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("WARN asset polish Blender adapter validation", result.stdout)
        self.assertEqual(report["schema"], "asset_polish_blender_adapter_validation_report_v0")
        self.assertEqual(report["plan_id"], "blocky_fence_post_asset_polish_plan_v0_compiled")
        self.assertEqual(report["source_recipe_id"], "blocky_fence_post_polish_recipe_v0")
        self.assertEqual(report["validation_status"], "warn")
        self.assertEqual(report["supported_step_count"], 9)
        self.assertEqual(report["future_step_count"], 1)
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["step_reports"]), 10)
        self.assertEqual(len(report["target_reports"]), 8)
        self.assertTrue(any("depth_m is greater than lip_width_m" in warning for warning in report["warnings"]))
        self.assertTrue(any("recognized but unsupported" in warning for warning in report["warnings"]))
        self.assertTrue(any(row["adapter_status"] == "supported" for row in report["operation_reports"]))
        self.assertTrue(any(row["adapter_status"] == "future" for row in report["operation_reports"]))
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertFalse(report["rules"]["creates_meshes"])
        self.assertFalse(report["rules"]["exports_files"])

    def test_validate_only_rejects_unknown_step_target(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_to(tmp_root / "polish")
            plan = load_json(plan_path)
            plan["steps"][0]["target"] = "missing.target"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            report_path = tmp_root / "adapter_report.json"
            result = subprocess.run(
                [sys.executable, str(ADAPTER), "--plan", str(plan_path), "--json-report", str(report_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["validation_status"], "fail")
        self.assertTrue(any("references unknown target" in error for error in report["errors"]))

    def test_validate_only_rejects_impossible_bevel_dimensions(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_to(tmp_root / "polish")
            plan = load_json(plan_path)
            plan["steps"][5]["params"]["width_m"] = -0.1
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            report_path = tmp_root / "adapter_report.json"
            result = subprocess.run(
                [sys.executable, str(ADAPTER), "--plan", str(plan_path), "--json-report", str(report_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["validation_status"], "fail")
        self.assertTrue(any("width_m" in error and "must be positive" in error for error in report["errors"]))

    def test_executor_validate_only_consumes_plan_and_asset(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_to(tmp_root / "polish")
            asset_path = pump_blocky_asset(tmp_root / "assets")
            report_path = tmp_root / "executor_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--asset",
                    str(asset_path),
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

        self.assertIn("PASS asset polish Blender executor validation", result.stdout)
        self.assertEqual(report["schema"], "asset_polish_blender_execution_report_v0")
        self.assertEqual(report["asset_schema"], "gameguy_asset_v0")
        self.assertEqual(report["asset_id"], "blocky_fence_post_v0")
        self.assertEqual(report["supported_step_count"], 9)
        self.assertEqual(report["future_step_count"], 1)
        self.assertEqual(report["executed_step_count"], 0)
        self.assertEqual(report["skipped_future_step_count"], 1)
        self.assertEqual(report["mesh_part_count"], 7)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["consumes_asset_polish_tool_plan_v0"])
        self.assertTrue(report["rules"]["consumes_gameguy_asset_v0"])
        self.assertFalse(report["rules"]["reads_source_recipe"])
        self.assertFalse(report["rules"]["runs_asset_pump"])

    def test_executor_validate_only_rejects_asset_mismatch(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            plan_path = compile_to(tmp_root / "polish")
            asset_path = pump_blocky_asset(tmp_root / "assets")
            asset = load_json(asset_path)
            asset["asset_id"] = "wrong_asset"
            asset_path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXECUTOR),
                    "--plan",
                    str(plan_path),
                    "--asset",
                    str(asset_path),
                    "--validate-only",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must match plan source asset", result.stderr)


if __name__ == "__main__":
    unittest.main()
