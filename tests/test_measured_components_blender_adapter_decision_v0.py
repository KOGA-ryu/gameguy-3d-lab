#!/usr/bin/env python3
"""Tests for the measured components Blender adapter decision."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "workflow" / "reports" / "3D-LAB-0011-measured-components-blender-adapter" / "replacement_decision.json"
ADAPTER = ROOT / "scripts" / "export_blender_measured_components_preview_v0.py"
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class MeasuredComponentsBlenderAdapterDecisionTests(unittest.TestCase):
    def test_adapter_report_matches_decision_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "adapter_report.json"
            subprocess.run(
                [sys.executable, str(ADAPTER), "--validate-only", "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        decision = load_json(DECISION)
        evidence = decision["comparison_evidence"]
        self.assertEqual(report["asset_count"], evidence["source_asset_count"])
        self.assertEqual(report["v1_asset_count"], evidence["v1_asset_count"])
        self.assertEqual(report["v2_asset_count"], evidence["v2_asset_count"])
        self.assertEqual(report["proof_primitive_count"], evidence["proof_primitive_count"])
        self.assertEqual(report["socket_count"], evidence["socket_count"])
        self.assertFalse(report["rules"]["imports_old_compiler_scripts"])
        self.assertFalse(report["rules"]["runs_old_compiler_scripts"])

    def test_script_orbit_demotes_old_measured_blender_scripts(self) -> None:
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
        self.assertEqual(rows["scripts/export_blender_measured_components_preview_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/blender_asset_mill_measured_components_v1.py"]["bucket"], "REFERENCE_ONLY")
        self.assertEqual(rows["scripts/blender_asset_mill_measured_components_v2.py"]["bucket"], "REFERENCE_ONLY")


if __name__ == "__main__":
    unittest.main()
