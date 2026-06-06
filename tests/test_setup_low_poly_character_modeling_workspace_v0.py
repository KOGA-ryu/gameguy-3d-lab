#!/usr/bin/env python3
"""Tests for the low-poly character manual modeling workspace setup."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "data" / "characters" / "low_poly_mannequin" / (
    "low_poly_character_mannequin_v0.json"
)
WORKSPACE = ROOT / "scripts" / "setup_low_poly_character_modeling_workspace_v0.py"
BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class LowPolyCharacterModelingWorkspaceTests(unittest.TestCase):
    def test_validate_only_reports_manual_modeling_workspace_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "workspace_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(WORKSPACE),
                    "--recipe",
                    str(RECIPE),
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

        self.assertIn("PASS low-poly mannequin modeling workspace validation", result.stdout)
        self.assertEqual(report["schema"], "low_poly_character_modeling_workspace_report_v0")
        self.assertEqual(report["editable_object_count"], 29)
        self.assertEqual(report["ghost_object_count"], 29)
        self.assertEqual(report["reference_plane_count"], 2)
        self.assertFalse(report["generated_outputs_created"])
        self.assertFalse(report["starter_armature_included"])

    @unittest.skipUnless(BLENDER.exists(), "Blender app is not installed at the expected path")
    def test_blender_export_writes_manual_modeling_workspace(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "workspace"
            result = subprocess.run(
                [
                    str(BLENDER),
                    "--background",
                    "--python",
                    str(WORKSPACE),
                    "--",
                    "--recipe",
                    str(RECIPE),
                    "--out",
                    str(out_root),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(
                out_root / "low_poly_character_mannequin_v0_modeling_workspace_report.json"
            )
            blend_exists = (
                out_root / "low_poly_character_mannequin_v0_modeling_workspace.blend"
            ).exists()

        self.assertIn("PASS low-poly mannequin modeling workspace export", result.stdout)
        self.assertTrue(blend_exists)
        self.assertTrue(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["creates_editable_parts"])
        self.assertTrue(report["rules"]["creates_locked_ghost_parts"])
        self.assertTrue(report["rules"]["keeps_parts_unparented_for_manual_modeling"])
        self.assertEqual(report["editable_object_count"], 29)


if __name__ == "__main__":
    unittest.main()
