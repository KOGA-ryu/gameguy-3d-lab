#!/usr/bin/env python3
"""Tests for the measured component Blender adapter validation mode."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUMP = ROOT / "scripts" / "asset_pump_v0.py"
ADAPTER = ROOT / "scripts" / "export_blender_measured_components_preview_v0.py"
MEASURED_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class BlenderMeasuredComponentsPreviewAdapterTests(unittest.TestCase):
    def test_validate_only_consumes_measured_asset_pump_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "adapter_report.json"
            subprocess.run(
                [sys.executable, str(PUMP), "--bundle", str(MEASURED_BUNDLE), "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
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

        self.assertIn("PASS measured component Blender adapter validation", result.stdout)
        self.assertEqual(report["schema"], "blender_measured_components_preview_adapter_report_v0")
        self.assertEqual(report["source_manifest_schema"], "gameguy_asset_pump_manifest_v0")
        self.assertEqual(report["source_bundle_schema"], "asset_mill_measured_component_bundle_v0")
        self.assertEqual(report["asset_schema"], "gameguy_asset_v0")
        self.assertEqual(report["asset_count"], 22)
        self.assertEqual(report["v1_asset_count"], 12)
        self.assertEqual(report["v2_asset_count"], 10)
        self.assertEqual(report["proof_primitive_count"], 52)
        self.assertEqual(report["proof_primitive_counts"], {"cube": 47, "cylinder": 2, "curve": 3})
        self.assertEqual(report["socket_count"], 74)
        self.assertEqual(report["total_vertices"], 1256)
        self.assertEqual(report["total_faces"], 926)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["consumes_deterministic_asset_json"])
        self.assertFalse(report["rules"]["reads_source_recipes"])
        self.assertFalse(report["rules"]["runs_asset_pump"])
        self.assertFalse(report["rules"]["imports_old_compiler_scripts"])
        self.assertFalse(report["rules"]["runs_old_compiler_scripts"])
        self.assertFalse(report["rules"]["source_design_logic"])

    def test_validate_only_rejects_non_measured_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            subprocess.run(
                [sys.executable, str(PUMP), "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [sys.executable, str(ADAPTER), "--manifest", str(out_root / "manifest.json"), "--validate-only"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest source_bundle_schema must be asset_mill_measured_component_bundle_v0", result.stderr)


if __name__ == "__main__":
    unittest.main()
