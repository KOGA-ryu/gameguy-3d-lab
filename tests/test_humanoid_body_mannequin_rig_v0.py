#!/usr/bin/env python3
"""Tests for the humanoid body mannequin rig recipe and Blender adapter."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BUNDLE = ROOT / "data" / "characters" / "mannequin_rigs" / "sources" / "humanoid_body_mannequin_sources_v0.json"
RECIPE = ROOT / "data" / "characters" / "mannequin_rigs" / "humanoid_body_mannequin_rig_v0.json"
COMPILER = ROOT / "scripts" / "compile_humanoid_mannequin_rig_v0.py"
ADAPTER = ROOT / "scripts" / "export_blender_humanoid_mannequin_rig_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidBodyMannequinRigTests(unittest.TestCase):
    def test_compiler_builds_recipe_from_human_profile_and_region_lanes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_recipe = Path(tmp) / "compiled_recipe.json"
            report_path = Path(tmp) / "compiler_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(COMPILER),
                    "--source-bundle",
                    str(SOURCE_BUNDLE),
                    "--out",
                    str(out_recipe),
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            compiled = load_json(out_recipe)
            report = load_json(report_path)

        self.assertIn("PASS humanoid mannequin rig compile", result.stdout)
        self.assertEqual(report["schema"], "humanoid_body_mannequin_compiler_report_v0")
        self.assertEqual(report["profile_id"], "neutral_adult_p50")
        self.assertTrue(report["rules"]["uses_human_profile_source"])
        self.assertTrue(report["rules"]["uses_extracted_region_lane_bboxes"])
        self.assertFalse(report["rules"]["manual_contour_coordinates"])
        self.assertEqual(compiled["measurement_profile"]["profile_id"], "neutral_adult_p50")
        self.assertEqual(compiled["source_projection"]["occupied_bbox_px"], [9, 18, 267, 570])
        self.assertAlmostEqual(compiled["source_projection"]["scale_m_per_px"], 0.003218807)

    def test_validate_only_consumes_source_recipe_without_blender(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "humanoid_report.json"
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
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS humanoid mannequin rig recipe validation", result.stdout)
        self.assertEqual(report["schema"], "humanoid_body_mannequin_rig_blender_report_v0")
        self.assertEqual(report["recipe_schema"], "humanoid_body_mannequin_rig_recipe_v0")
        self.assertEqual(report["asset_id"], "humanoid_body_mannequin_rig_v0")
        self.assertEqual(report["region_count"], 16)
        self.assertEqual(report["joint_count"], 18)
        self.assertEqual(report["socket_count"], 9)
        self.assertEqual(report["control_count"], 17)
        self.assertFalse(report["generated_outputs_created"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertTrue(report["rules"]["consumes_source_recipe"])
        self.assertFalse(report["rules"]["source_design_logic_in_blender_adapter"])

    def test_recipe_region_ids_pivots_and_sockets_are_stable(self) -> None:
        recipe = load_json(RECIPE)
        palette_ids = [row["region_id"] for row in recipe["region_palette"]]
        region_ids = [region["region_id"] for region in recipe["regions"]]
        joint_ids = {joint["joint_id"] for joint in recipe["joints"]}
        draw_layers = set(recipe["draw_order"])

        self.assertEqual(palette_ids, list(range(1, 17)))
        self.assertEqual(region_ids, list(range(1, 17)))
        self.assertIn("root", joint_ids)
        for region in recipe["regions"]:
            self.assertIn(region["pivot_joint"], joint_ids)
            self.assertIn(region["draw_layer"], draw_layers)
            self.assertEqual(region["shape"]["type"], "extruded_contour")
            self.assertGreaterEqual(len(region["shape"]["contour_xz_m"]), 3)
            self.assertGreater(region["shape"]["depth_m"], 0)
            self.assertIn("source_shape_family", region["shape"])
            self.assertIn("source_lane", region["shape"])
            self.assertIn("source_bbox_px", region["shape"])
            self.assertIn("source_mask", region["shape"])
        for socket in recipe["sockets"]:
            self.assertIn(socket["joint_id"], joint_ids)
            self.assertEqual(len(socket["position_m"]), 3)

    def test_recipe_records_silhouette_symmetry_strategy(self) -> None:
        recipe = load_json(RECIPE)
        strategy = recipe["silhouette_strategy"]

        self.assertEqual(strategy["method"], "source_bbox_contour_extrusion")
        self.assertEqual(len(strategy["mirrored_pairs"]), 6)
        self.assertIn(["upper_arm_L", "upper_arm_R"], strategy["mirrored_pairs"])
        self.assertIn(["foot_L", "foot_R"], strategy["mirrored_pairs"])

    def test_recipe_records_human_measurement_profile(self) -> None:
        recipe = load_json(RECIPE)
        profile = recipe["measurement_profile"]
        landmarks = profile["scaled_landmarks_m"]

        self.assertEqual(profile["profile_id"], "neutral_adult_p50")
        self.assertEqual(profile["body_height_m"], 1.78)
        self.assertEqual(profile["population_basis"], "ANSUR II + NASA Anthropometry")
        self.assertAlmostEqual(landmarks["head_center_z_m"], 1.609999)
        self.assertAlmostEqual(landmarks["shoulder_z_m"], 1.45)
        self.assertAlmostEqual(landmarks["knee_z_m"], 0.53)

    def test_pose_sets_match_reference_sheet_counts(self) -> None:
        recipe = load_json(RECIPE)
        pose_counts = {pose["pose_set_id"]: pose["frame_count"] for pose in recipe["required_pose_sets"]}

        self.assertEqual(pose_counts["idle_loop_v0"], 6)
        self.assertEqual(pose_counts["walk_loop_v0"], 8)
        self.assertEqual(pose_counts["hurt_reaction_v0"], 3)


if __name__ == "__main__":
    unittest.main()
