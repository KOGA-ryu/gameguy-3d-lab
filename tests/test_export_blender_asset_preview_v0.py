#!/usr/bin/env python3
"""Tests for the Blender asset preview adapter's normal-Python validation mode."""

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
ADAPTER = ROOT / "scripts" / "export_blender_asset_preview_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class BlenderAssetPreviewAdapterTests(unittest.TestCase):
    def test_validate_only_consumes_asset_pump_manifest(self) -> None:
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

        self.assertIn("PASS Blender asset adapter validation", result.stdout)
        self.assertEqual(report["schema"], "blender_asset_preview_adapter_report_v0")
        self.assertEqual(report["source_manifest_schema"], "gameguy_asset_pump_manifest_v0")
        self.assertEqual(report["asset_schema"], "gameguy_asset_v0")
        self.assertEqual(report["asset_count"], 14)
        self.assertEqual(report["total_vertices"], 280)
        self.assertEqual(report["total_faces"], 186)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["consumes_deterministic_asset_json"])
        self.assertFalse(report["rules"]["reads_source_recipes"])
        self.assertFalse(report["rules"]["runs_asset_pump"])
        self.assertFalse(report["rules"]["source_design_logic"])

    def test_validate_only_rejects_non_asset_schema(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            subprocess.run(
                [sys.executable, str(PUMP), "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            first_asset = out_root / "assets" / "rectangular_slab_v0.json"
            asset = load_json(first_asset)
            asset["schema"] = "source_recipe_not_generated_asset"
            first_asset.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "--manifest",
                    str(out_root / "manifest.json"),
                    "--validate-only",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("schema must be gameguy_asset_v0", result.stderr)


if __name__ == "__main__":
    unittest.main()
