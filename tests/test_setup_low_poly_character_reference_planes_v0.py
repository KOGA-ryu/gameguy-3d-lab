#!/usr/bin/env python3
"""Tests for the professional reference-plane Blender setup."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "characters" / "references" / (
    "low_poly_mannequin_turnaround_v0.png"
)
SETUP = ROOT / "scripts" / "setup_low_poly_character_reference_planes_v0.py"
BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class LowPolyCharacterReferencePlanesTests(unittest.TestCase):
    def test_validate_only_reports_reference_plane_setup(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "reference_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SETUP),
                    "--reference",
                    str(REFERENCE),
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

        self.assertIn("PASS low-poly mannequin reference planes validation", result.stdout)
        self.assertEqual(report["schema"], "low_poly_character_reference_planes_report_v0")
        self.assertEqual(report["reference_view_count"], 6)
        self.assertEqual(report["primary_orthographic_view_count"], 3)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["reference_only_scene"])
        self.assertFalse(report["rules"]["creates_editable_mesh"])

    @unittest.skipUnless(BLENDER.exists(), "Blender app is not installed at the expected path")
    def test_blender_export_writes_reference_only_scene(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "reference_planes"
            result = subprocess.run(
                [
                    str(BLENDER),
                    "--background",
                    "--python",
                    str(SETUP),
                    "--",
                    "--reference",
                    str(REFERENCE),
                    "--out",
                    str(out_root),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(out_root / "low_poly_mannequin_reference_planes_report.json")
            blend_exists = (out_root / "low_poly_mannequin_reference_planes_v0.blend").exists()

        self.assertIn("PASS low-poly mannequin reference planes export", result.stdout)
        self.assertTrue(blend_exists)
        self.assertTrue(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["creates_locked_image_planes"])
        self.assertTrue(report["rules"]["creates_front_side_back_planes"])
        self.assertTrue(report["rules"]["creates_viewport_image_empties"])
        self.assertTrue(report["rules"]["packs_reference_images"])
        self.assertEqual(len(report["locked_plane_names"]), 6)
        self.assertEqual(len(report["viewport_image_empty_names"]), 6)


if __name__ == "__main__":
    unittest.main()
