"""Tests for the compiled humanoid head blockout chain."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = REPO_ROOT / "data" / "characters" / "head_construction" / "humanoid_head_layer_taxonomy_v0.json"
RECIPE = REPO_ROOT / "data" / "characters" / "head_construction" / "humanoid_head_blockout_v0.json"
COMPILER = REPO_ROOT / "scripts" / "compile_humanoid_head_blockout_v0.py"
ADAPTER = REPO_ROOT / "scripts" / "export_blender_humanoid_head_blockout_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidHeadBlockoutTests(unittest.TestCase):
    def test_compiler_emits_layered_head_geometry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_recipe = Path(tmp) / "head_blockout.json"
            report_path = Path(tmp) / "compiler_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(COMPILER),
                    "--taxonomy",
                    str(TAXONOMY),
                    "--out",
                    str(out_recipe),
                    "--json-report",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            recipe = load_json(out_recipe)
            report = load_json(report_path)

        self.assertIn("PASS humanoid head blockout compile", result.stdout)
        self.assertEqual(recipe["schema"], "humanoid_head_geometry_v0")
        self.assertEqual(report["schema"], "humanoid_head_blockout_compiler_report_v0")
        self.assertTrue(report["rules"]["uses_head_layer_taxonomy"])
        self.assertTrue(report["rules"]["emits_deterministic_vertices_faces"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertEqual(len(recipe["parts"]), 18)
        self.assertIn("nose_wedge", {part["part_id"] for part in recipe["parts"]})

    def test_adapter_validates_without_blender(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "validate_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "--recipe",
                    str(RECIPE),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS humanoid head blockout geometry validation", result.stdout)
        self.assertEqual(report["schema"], "humanoid_head_blockout_blender_report_v0")
        self.assertFalse(report["generated_outputs_created"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertFalse(report["rules"]["source_design_logic_in_blender_adapter"])
        self.assertEqual(report["part_count"], 18)
        self.assertGreater(report["vertex_count"], 200)

    def test_recipe_contains_critical_face_layers(self) -> None:
        recipe = load_json(RECIPE)
        layer_ids = {part["layer_id"] for part in recipe["parts"]}
        material_ids = {row["material_id"] for row in recipe["material_palette"]}

        self.assertIn("skull_envelope", layer_ids)
        self.assertIn("brow_eye_band", layer_ids)
        self.assertIn("nose_wedge", layer_ids)
        self.assertIn("chin_jaw_mass", layer_ids)
        self.assertIn("socket_shadow", material_ids)
        self.assertIn("mouth_shadow", material_ids)
        for part in recipe["parts"]:
            self.assertEqual(part["mesh"]["type"], "mesh_from_pydata")
            self.assertGreaterEqual(len(part["mesh"]["vertices_m"]), 3)
            self.assertGreaterEqual(len(part["mesh"]["faces"]), 1)


if __name__ == "__main__":
    unittest.main()
