#!/usr/bin/env python3
"""Tests for the low-poly character mannequin Blender scene exporter."""

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
EXPORTER = ROOT / "scripts" / "export_blender_low_poly_character_mannequin_v0.py"
BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class LowPolyCharacterMannequinBlenderExportTests(unittest.TestCase):
    def test_validate_only_consumes_recipe_without_importing_blender(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXPORTER),
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

        self.assertIn("PASS low-poly mannequin Blender scene validation", result.stdout)
        self.assertEqual(report["schema"], "low_poly_character_mannequin_blender_scene_report_v0")
        self.assertEqual(report["asset_id"], "low_poly_character_mannequin_v0")
        self.assertEqual(report["part_count"], 29)
        self.assertEqual(report["armature_bone_count"], 11)
        self.assertEqual(report["beveled_part_count"], 7)
        self.assertEqual(report["weighted_normal_part_count"], 7)
        self.assertFalse(report["generated_outputs_created"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertFalse(report["rules"]["creates_starter_armature"])

    @unittest.skipUnless(BLENDER.exists(), "Blender app is not installed at the expected path")
    def test_blender_export_writes_scene_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "scene"
            result = subprocess.run(
                [
                    str(BLENDER),
                    "--background",
                    "--python",
                    str(EXPORTER),
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
            report = load_json(out_root / "low_poly_character_mannequin_v0_blender_report.json")
            blend_exists = (out_root / "low_poly_character_mannequin_v0.blend").exists()
            obj_exists = (out_root / "low_poly_character_mannequin_v0.obj").exists()
            mtl_exists = (out_root / "low_poly_character_mannequin_v0.mtl").exists()

        self.assertIn("PASS low-poly mannequin Blender scene export", result.stdout)
        self.assertTrue(blend_exists)
        self.assertTrue(obj_exists)
        self.assertTrue(mtl_exists)
        self.assertTrue(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["creates_reference_sheet_plane"])
        self.assertTrue(report["rules"]["creates_starter_armature"])
        self.assertTrue(report["rules"]["applies_bevel_modifiers"])
        self.assertTrue(report["rules"]["applies_weighted_normals"])
        self.assertEqual(report["armature_bone_count"], 11)
        self.assertEqual(report["beveled_part_count"], 7)


if __name__ == "__main__":
    unittest.main()
