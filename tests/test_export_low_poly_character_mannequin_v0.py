#!/usr/bin/env python3
"""Tests for the low-poly character mannequin OBJ exporter."""

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
EXPORTER = ROOT / "scripts" / "export_low_poly_character_mannequin_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class LowPolyCharacterMannequinExportTests(unittest.TestCase):
    def test_validate_only_consumes_recipe_without_blender(self) -> None:
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

        self.assertIn("PASS low-poly mannequin recipe validation", result.stdout)
        self.assertEqual(report["schema"], "low_poly_character_mannequin_obj_report_v0")
        self.assertEqual(report["recipe_schema"], "low_poly_character_mannequin_recipe_v0")
        self.assertEqual(report["asset_id"], "low_poly_character_mannequin_v0")
        self.assertEqual(report["part_count"], 29)
        self.assertGreater(report["vertex_count"], 300)
        self.assertGreater(report["face_count"], 250)
        self.assertFalse(report["generated_outputs_created"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertTrue(report["rules"]["consumes_source_recipe"])

    def test_export_writes_blender_importable_obj_and_mtl(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "export"
            result = subprocess.run(
                [sys.executable, str(EXPORTER), "--recipe", str(RECIPE), "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            obj_path = out_root / "low_poly_character_mannequin_v0.obj"
            mtl_path = out_root / "low_poly_character_mannequin_v0.mtl"
            report = load_json(out_root / "low_poly_character_mannequin_v0_report.json")
            obj_exists = obj_path.exists()
            mtl_exists = mtl_path.exists()
            obj_text = obj_path.read_text(encoding="utf-8")
            mtl_text = mtl_path.read_text(encoding="utf-8")

        self.assertIn("PASS low-poly mannequin OBJ export", result.stdout)
        self.assertTrue(obj_exists)
        self.assertTrue(mtl_exists)
        self.assertIn("mtllib low_poly_character_mannequin_v0.mtl", obj_text)
        self.assertIn("o head", obj_text)
        self.assertIn("o eye_L", obj_text)
        self.assertIn("usemtl ivory_body", obj_text)
        self.assertIn("usemtl eye_black", obj_text)
        self.assertIn("newmtl joint_shadow", mtl_text)
        self.assertTrue(report["generated_outputs_created"])
        self.assertEqual(report["object_count"], 29)
        self.assertTrue(report["rules"]["writes_obj_mtl"])

    def test_recipe_records_reference_and_separate_part_rules(self) -> None:
        recipe = load_json(RECIPE)
        self.assertEqual(
            recipe["source_reference"]["front_reference_role"],
            "user supplied front-view segmented mannequin image",
        )
        self.assertTrue(recipe["rules"]["body_parts_are_separate_mesh_objects"])
        self.assertTrue(recipe["rules"]["front_reference_controls_silhouette"])
        self.assertEqual(recipe["coordinate_system"]["origin"], "feet_center")


if __name__ == "__main__":
    unittest.main()
