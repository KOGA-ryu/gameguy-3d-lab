#!/usr/bin/env python3
"""Tests for the Blender Asset Mill smoke-test demotion decision."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "workflow" / "reports" / "3D-LAB-0010-blender-asset-mill-smoke-test-demotion" / "replacement_decision.json"
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"
PUMP = ROOT / "scripts" / "asset_pump_v0.py"
ADAPTER = ROOT / "scripts" / "export_blender_asset_preview_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class BlenderAssetMillSmokeTestDemotionTests(unittest.TestCase):
    def test_decision_points_to_json_adapter_replacement(self) -> None:
        decision = load_json(DECISION)

        self.assertEqual(decision["schema"], "blender_asset_mill_smoke_test_replacement_decision_v0")
        self.assertEqual(decision["target_script"], "scripts/blender_asset_mill_smoke_test_v0.py")
        self.assertEqual(decision["replacement_adapter"], "scripts/export_blender_asset_preview_v0.py")
        self.assertEqual(decision["replacement_input_schema"], "gameguy_asset_v0")
        self.assertEqual(decision["decision"], "DEMOTE_TO_REFERENCE_ONLY")
        self.assertFalse(decision["safe_to_delete_now"])
        self.assertEqual(decision["comparison_evidence"]["new_adapter_asset_count"], 14)
        self.assertEqual(decision["comparison_evidence"]["new_adapter_total_vertices"], 280)
        self.assertEqual(decision["comparison_evidence"]["new_adapter_total_faces"], 186)

    def test_adapter_report_matches_decision_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "adapter_report.json"
            subprocess.run(
                [sys.executable, str(PUMP), "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "--manifest",
                    str(out_root / "manifest.json"),
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

        decision = load_json(DECISION)
        evidence = decision["comparison_evidence"]
        self.assertEqual(report["asset_count"], evidence["new_adapter_asset_count"])
        self.assertEqual(report["total_vertices"], evidence["new_adapter_total_vertices"])
        self.assertEqual(report["total_faces"], evidence["new_adapter_total_faces"])
        self.assertFalse(report["rules"]["reads_source_recipes"])
        self.assertFalse(report["rules"]["source_design_logic"])

    def test_script_orbit_demotes_old_smoke_test(self) -> None:
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

        rows = {row["script"]: row for row in report["scripts"]}
        self.assertEqual(rows["scripts/blender_asset_mill_smoke_test_v0.py"]["bucket"], "REFERENCE_ONLY")
        self.assertEqual(report["bucket_counts"]["CONVERT_TO_ADAPTER"], 0)


if __name__ == "__main__":
    unittest.main()
