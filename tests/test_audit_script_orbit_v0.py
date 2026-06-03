#!/usr/bin/env python3
"""Tests for the source-only script orbit audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class ScriptOrbitAuditTests(unittest.TestCase):
    def test_audit_classifies_known_core_scripts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "script_orbit.json"
            result = subprocess.run(
                [sys.executable, str(AUDIT), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        rows = {row["script"]: row for row in report["scripts"]}
        self.assertIn("PASS script orbit audit", result.stdout)
        self.assertEqual(report["schema"], "script_orbit_audit_v0")
        self.assertEqual(rows["scripts/asset_pump_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/compile_blender_tool_plan_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/execute_blender_tool_plan_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/validate_blender_tool_plan_execution_report_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/validate_gameguy_asset_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/export_blender_asset_preview_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/export_blender_measured_components_preview_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/blender_asset_mill_smoke_test_v0.py"]["bucket"], "DELETE_LATER")
        self.assertEqual(rows["scripts/blender_asset_mill_measured_components_v1.py"]["bucket"], "DELETE_LATER")
        self.assertEqual(rows["scripts/blender_asset_mill_measured_components_v2.py"]["bucket"], "DELETE_LATER")
        self.assertEqual(rows["scripts/compile_asset_mill_solids_v0.py"]["bucket"], "DELETE_LATER")
        self.assertEqual(rows["scripts/compile_asset_mill_measured_components_v1.py"]["bucket"], "DELETE_LATER")
        self.assertEqual(rows["scripts/compile_asset_mill_measured_components_v2.py"]["bucket"], "DELETE_LATER")
        self.assertEqual(rows["scripts/validate_measured_component_source_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertFalse(report["rules"]["deletes_files"])
        self.assertFalse(report["rules"]["moves_files"])
        self.assertFalse(report["rules"]["executes_classified_scripts"])

    def test_bucket_counts_match_script_rows(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "script_orbit.json"
            subprocess.run(
                [sys.executable, str(AUDIT), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertEqual(report["script_count"], len(report["scripts"]))
        self.assertEqual(sum(report["bucket_counts"].values()), report["script_count"])
        self.assertEqual(report["bucket_counts"]["CONVERT_TO_ADAPTER"], 0)
        self.assertEqual(report["bucket_counts"]["DELETE_LATER"], 6)
        self.assertGreater(report["bucket_counts"]["REFERENCE_ONLY"], 0)


if __name__ == "__main__":
    unittest.main()
