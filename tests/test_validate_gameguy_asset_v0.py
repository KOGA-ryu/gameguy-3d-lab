#!/usr/bin/env python3
"""Tests for generated gameguy_asset_v0 validation."""

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
VALIDATOR = ROOT / "scripts" / "validate_gameguy_asset_v0.py"
MEASURED_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"
SECTION_STACK_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "section_stack_assets_v0.json"
BLOCKY_COLUMN_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "blocky_column_assets_v0.json"
BLOCKY_SHAPE_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "blocky_shape_grammar_assets_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_pump(out_root: Path, *, measured: bool = False, section_stack: bool = False, blocky_column: bool = False, blocky_shape: bool = False) -> None:
    cmd = [sys.executable, str(PUMP)]
    if measured:
        cmd.extend(["--bundle", str(MEASURED_BUNDLE)])
    if section_stack:
        cmd.extend(["--bundle", str(SECTION_STACK_BUNDLE)])
    if blocky_column:
        cmd.extend(["--bundle", str(BLOCKY_COLUMN_BUNDLE)])
    if blocky_shape:
        cmd.extend(["--bundle", str(BLOCKY_SHAPE_BUNDLE)])
    cmd.extend(["--out", str(out_root)])
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)


def run_validator(manifest: Path, report: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(VALIDATOR), "--manifest", str(manifest)]
    if report:
        cmd.extend(["--json-report", str(report)])
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


class GameguyAssetValidatorTests(unittest.TestCase):
    def test_validates_simple_asset_pump_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "asset_report.json"
            run_pump(out_root)
            result = run_validator(out_root / "manifest.json", report_path)
            report = load_json(report_path)

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS gameguy_asset_v0 validation", result.stdout)
        self.assertEqual(report["schema"], "gameguy_asset_v0_validation_result_v0")
        self.assertEqual(report["asset_count"], 14)
        self.assertEqual(report["measured_asset_count"], 0)
        self.assertEqual(report["total_vertices"], 280)
        self.assertEqual(report["total_faces"], 186)
        self.assertFalse(report["generated_outputs_created"])

    def test_validates_measured_asset_pump_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "asset_report.json"
            run_pump(out_root, measured=True)
            result = run_validator(out_root / "manifest.json", report_path)
            report = load_json(report_path)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["source_bundle_schema"], "asset_mill_measured_component_bundle_v0")
        self.assertEqual(report["asset_count"], 22)
        self.assertEqual(report["measured_asset_count"], 22)
        self.assertEqual(report["total_vertices"], 1256)
        self.assertEqual(report["total_faces"], 926)
        self.assertEqual(report["total_parts"], 52)
        self.assertEqual(report["total_connectors"], 74)

    def test_validates_section_stack_asset_pump_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "asset_report.json"
            run_pump(out_root, section_stack=True)
            result = run_validator(out_root / "manifest.json", report_path)
            report = load_json(report_path)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["source_bundle_schema"], "asset_mill_section_stack_bundle_v0")
        self.assertEqual(report["asset_count"], 1)
        self.assertEqual(report["measured_asset_count"], 0)
        self.assertEqual(report["total_vertices"], 464)
        self.assertEqual(report["total_faces"], 528)
        self.assertEqual(report["total_parts"], 1)

    def test_validates_blocky_column_asset_pump_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "asset_report.json"
            run_pump(out_root, blocky_column=True)
            result = run_validator(out_root / "manifest.json", report_path)
            report = load_json(report_path)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["source_bundle_schema"], "asset_mill_blocky_column_bundle_v0")
        self.assertEqual(report["asset_count"], 1)
        self.assertEqual(report["measured_asset_count"], 0)
        self.assertEqual(report["total_vertices"], 264)
        self.assertEqual(report["total_faces"], 186)
        self.assertEqual(report["total_parts"], 27)

    def test_validates_blocky_shape_grammar_asset_pump_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            report_path = Path(tmp) / "asset_report.json"
            run_pump(out_root, blocky_shape=True)
            result = run_validator(out_root / "manifest.json", report_path)
            report = load_json(report_path)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["source_bundle_schema"], "asset_mill_blocky_shape_grammar_bundle_v0")
        self.assertEqual(report["asset_count"], 2)
        self.assertEqual(report["measured_asset_count"], 0)
        self.assertEqual(report["total_vertices"], 320)
        self.assertEqual(report["total_faces"], 228)
        self.assertEqual(report["total_parts"], 34)

    def test_rejects_invalid_mesh_face_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_pump(out_root)
            asset_path = out_root / "assets" / "rectangular_slab_v0.json"
            asset = load_json(asset_path)
            asset["mesh"]["faces"][0][0] = len(asset["mesh"]["vertices"])
            asset_path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
            result = run_validator(out_root / "manifest.json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contains invalid vertex index", result.stderr)

    def test_rejects_media_or_mesh_output_in_pump_root(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_pump(out_root)
            (out_root / "leaked_preview.obj").write_text("# should not live in pump output\n", encoding="utf-8")
            result = run_validator(out_root / "manifest.json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generated media/mesh output is not allowed", result.stderr)


if __name__ == "__main__":
    unittest.main()
