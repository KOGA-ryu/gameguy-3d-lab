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


def part_index(recipe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {part["part_id"]: part for part in recipe["parts"]}


def part_bounds(part: dict[str, Any]) -> dict[str, list[float]]:
    vertices = part["mesh"]["vertices_m"]
    return {
        axis: [min(vertex[index] for vertex in vertices), max(vertex[index] for vertex in vertices)]
        for index, axis in enumerate(("x", "y", "z"))
    }


def axis_overlap(a: list[float], b: list[float]) -> float:
    return min(a[1], b[1]) - max(a[0], b[0])


def unique_y_count(part: dict[str, Any]) -> int:
    return len({vertex[1] for vertex in part["mesh"]["vertices_m"]})


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
        self.assertTrue(report["rules"]["uses_shape_refinement_controls"])
        self.assertTrue(report["rules"]["uses_brow_eye_region_controls"])
        self.assertTrue(report["rules"]["records_connection_policy"])
        self.assertTrue(report["rules"]["emits_deterministic_vertices_faces"])
        self.assertFalse(report["rules"]["imports_blender"])
        self.assertEqual(len(recipe["parts"]), 29)
        self.assertEqual(len(recipe["shape_refinement_controls"]), 13)
        self.assertEqual(len(recipe["connection_policy"]["rules"]), 28)
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
        self.assertEqual(report["part_count"], 29)
        self.assertEqual(report["control_count"], 13)
        self.assertEqual(report["connection_rule_count"], 28)
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
        control_ids = {control["control_id"] for control in recipe["shape_refinement_controls"]}
        self.assertIn("brow_arc_ratio", control_ids)
        self.assertIn("brow_forward_offset_m", control_ids)
        self.assertIn("socket_under_brow_setback_m", control_ids)
        self.assertIn("glabella_peak_ratio", control_ids)
        self.assertIn("brow_side_wrap_ratio", control_ids)
        self.assertIn("feature_embed_overlap_m", control_ids)
        connected_part_ids = {rule["part_id"] for rule in recipe["connection_policy"]["rules"]}
        self.assertNotIn("skull_envelope", connected_part_ids)
        for part in recipe["parts"]:
            self.assertEqual(part["mesh"]["type"], "mesh_from_pydata")
            self.assertGreaterEqual(len(part["mesh"]["vertices_m"]), 3)
            self.assertGreaterEqual(len(part["mesh"]["faces"]), 1)
            if part["part_id"] != "skull_envelope":
                self.assertIn(part["part_id"], connected_part_ids)

    def test_brow_eye_region_controls_shape_recessed_wrapped_socket_band(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_recipe = Path(tmp) / "head_blockout.json"
            subprocess.run(
                [
                    sys.executable,
                    str(COMPILER),
                    "--taxonomy",
                    str(TAXONOMY),
                    "--out",
                    str(out_recipe),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            recipe = load_json(out_recipe)

        controls = {row["control_id"]: row["value"] for row in recipe["shape_refinement_controls"]}
        self.assertGreater(controls["brow_forward_offset_m"], 0.0)
        self.assertGreater(controls["socket_under_brow_setback_m"], 0.0)

        parts = part_index(recipe)
        self.assertNotIn("brow_ridge", parts)
        glabella_bounds = part_bounds(parts["brow_glabella"])
        wing_l_bounds = part_bounds(parts["brow_wing_L"])
        wing_r_bounds = part_bounds(parts["brow_wing_R"])
        rim_l_bounds = part_bounds(parts["eye_socket_rim_L"])
        rim_r_bounds = part_bounds(parts["eye_socket_rim_R"])
        dark_l_bounds = part_bounds(parts["eye_socket_dark_L"])
        dark_r_bounds = part_bounds(parts["eye_socket_dark_R"])

        self.assertLess(glabella_bounds["y"][0], wing_l_bounds["y"][0])
        self.assertLess(glabella_bounds["y"][0], wing_r_bounds["y"][0])
        self.assertLess(wing_l_bounds["y"][0], dark_l_bounds["y"][0])
        self.assertLess(wing_r_bounds["y"][0], dark_r_bounds["y"][0])
        self.assertGreater(axis_overlap(wing_l_bounds["y"], rim_l_bounds["y"]), 0.0)
        self.assertGreater(axis_overlap(wing_r_bounds["y"], rim_r_bounds["y"]), 0.0)
        self.assertGreater(axis_overlap(rim_l_bounds["y"], dark_l_bounds["y"]), 0.0)
        self.assertGreater(axis_overlap(rim_r_bounds["y"], dark_r_bounds["y"]), 0.0)

        self.assertAlmostEqual(-wing_l_bounds["x"][1], wing_r_bounds["x"][0], places=6)
        self.assertAlmostEqual(-wing_l_bounds["x"][0], wing_r_bounds["x"][1], places=6)
        self.assertAlmostEqual(-rim_l_bounds["x"][1], rim_r_bounds["x"][0], places=6)
        self.assertAlmostEqual(-rim_l_bounds["x"][0], rim_r_bounds["x"][1], places=6)
        self.assertAlmostEqual(-dark_l_bounds["x"][1], dark_r_bounds["x"][0], places=6)
        self.assertAlmostEqual(-dark_l_bounds["x"][0], dark_r_bounds["x"][1], places=6)

        self.assertGreaterEqual(dark_l_bounds["x"][0], rim_l_bounds["x"][0])
        self.assertLessEqual(dark_l_bounds["x"][1], rim_l_bounds["x"][1])
        self.assertGreaterEqual(dark_l_bounds["z"][0], rim_l_bounds["z"][0])
        self.assertLessEqual(dark_l_bounds["z"][1], rim_l_bounds["z"][1])
        self.assertGreaterEqual(dark_r_bounds["x"][0], rim_r_bounds["x"][0])
        self.assertLessEqual(dark_r_bounds["x"][1], rim_r_bounds["x"][1])
        self.assertGreaterEqual(dark_r_bounds["z"][0], rim_r_bounds["z"][0])
        self.assertLessEqual(dark_r_bounds["z"][1], rim_r_bounds["z"][1])

    def test_face_parts_use_region_bend_fields_instead_of_flat_prisms(self) -> None:
        recipe = load_json(RECIPE)
        parts = part_index(recipe)
        bend_part_ids = {
            "face_mask_plane",
            "brow_glabella",
            "brow_wing_L",
            "brow_wing_R",
            "eye_socket_rim_L",
            "eye_socket_rim_R",
            "eye_socket_dark_L",
            "eye_socket_dark_R",
            "nose_wedge",
            "cheek_plane_L",
            "cheek_plane_R",
            "mouth_crease",
            "upper_lip_relief",
            "lower_lip_relief",
            "chin_mass",
            "jaw_side_plane_L",
            "jaw_side_plane_R",
        }

        for part_id in bend_part_ids:
            with self.subTest(part_id=part_id):
                part = parts[part_id]
                bend_field = part.get("bend_field")
                self.assertIsInstance(bend_field, dict)
                self.assertEqual(bend_field["space"], "xz_contour_to_y_depth")
                self.assertGreater(unique_y_count(part), 2)

    def test_face_transition_surfaces_bridge_child_parts_to_face_mask(self) -> None:
        recipe = load_json(RECIPE)
        parts = part_index(recipe)
        transition_part_ids = {
            "brow_glabella_to_face_blend",
            "brow_wing_L_to_face_blend",
            "brow_wing_R_to_face_blend",
            "cheek_plane_L_to_face_blend",
            "cheek_plane_R_to_face_blend",
            "mouth_crease_to_face_blend",
            "chin_mass_to_face_blend",
            "jaw_side_plane_L_to_face_blend",
            "jaw_side_plane_R_to_face_blend",
        }
        connected = {rule["part_id"]: rule["connects_to"] for rule in recipe["connection_policy"]["rules"]}

        self.assertEqual(len(transition_part_ids), 9)
        for part_id in transition_part_ids:
            with self.subTest(part_id=part_id):
                part = parts[part_id]
                field = part.get("transition_field")
                self.assertIsInstance(field, dict)
                self.assertEqual(field["space"], "child_contour_to_parent_face_surface")
                self.assertEqual(field["parent_part_id"], "face_mask_plane")
                self.assertEqual(connected[part_id], "face_mask_plane")
                self.assertGreaterEqual(len(part["mesh"]["faces"]), 4)


if __name__ == "__main__":
    unittest.main()
