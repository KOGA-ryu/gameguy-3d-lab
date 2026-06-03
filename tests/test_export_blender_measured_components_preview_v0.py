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
ADAPTER = ROOT / "scripts" / "export_blender_measured_components_preview_v0.py"
BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class BlenderMeasuredComponentsPreviewAdapterTests(unittest.TestCase):
    def test_validate_only_consumes_promoted_source_bundle(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "adapter_report.json"
            result = subprocess.run(
                [sys.executable, str(ADAPTER), "--validate-only", "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS measured component Blender adapter validation", result.stdout)
        self.assertEqual(report["schema"], "blender_measured_components_preview_adapter_report_v0")
        self.assertEqual(report["source_bundle_schema"], "asset_mill_measured_component_bundle_v0")
        self.assertEqual(report["asset_count"], 22)
        self.assertEqual(report["v1_asset_count"], 12)
        self.assertEqual(report["v2_asset_count"], 10)
        self.assertEqual(report["proof_primitive_count"], 52)
        self.assertEqual(report["socket_count"], 74)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["consumes_promoted_source_catalog"])
        self.assertFalse(report["rules"]["imports_old_compiler_scripts"])
        self.assertFalse(report["rules"]["runs_old_compiler_scripts"])
        self.assertFalse(report["rules"]["source_design_logic"])

    def test_validate_only_rejects_bad_proof_primitive(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["assets"][0]["proof_primitives"][0]["dimensions_m"] = [2.2, 0.34, 0.0]

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_measured_components.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ADAPTER), "--bundle", str(bad_bundle), "--validate-only"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dimensions_m values must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()
