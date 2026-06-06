"""Tests for external skull GLTF measurement stack extraction."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MEASURE_SCRIPT = REPO_ROOT / "scripts" / "measure_humanoid_skull_reference_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidSkullMeasurementStackTests(unittest.TestCase):
    def test_measurement_stack_reads_external_gltf_and_emits_3d_slices(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_path = Path(tmp) / "skull_measurement.json"
            report_path = Path(tmp) / "skull_measurement_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(MEASURE_SCRIPT),
                    "--out",
                    str(out_path),
                    "--json-report",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            measurement = load_json(out_path)
            report = load_json(report_path)

        self.assertIn("PASS humanoid skull measurement stack", result.stdout)
        self.assertEqual(measurement["schema"], "humanoid_skull_measurement_stack_v0")
        self.assertEqual(report["schema"], "humanoid_skull_measurement_stack_report_v0")
        self.assertTrue(report["pass"])
        self.assertEqual(measurement["source_provenance"]["source_id"], "human_skull_source_v1_full_skull_truth")
        self.assertIn("CC BY-SA", measurement["source_provenance"]["upstream_license_note"])

        mesh = measurement["mesh_summary"]
        self.assertGreater(mesh["gltf_position_vertex_count"], 100000)
        self.assertEqual(mesh["gltf_triangle_count"], 200938)
        self.assertEqual(mesh["build_report_study_triangle_count"], 200938)
        self.assertLessEqual(mesh["bbox_delta_m"]["max_abs_error_m"], 0.000001)
        self.assertAlmostEqual(mesh["bbox_m"]["dimensions"][0], 0.14352, places=5)
        self.assertAlmostEqual(mesh["bbox_m"]["dimensions"][1], 0.196738, places=5)
        self.assertAlmostEqual(mesh["bbox_m"]["dimensions"][2], 0.203077, places=5)

        stack = measurement["slice_stack"]
        self.assertEqual(stack["slice_count"], 15)
        families = {row["family_id"] for row in stack["slices"]}
        self.assertEqual(families, {"xy_at_z", "yz_at_x", "xz_at_y"})
        for row in stack["slices"]:
            self.assertGreaterEqual(row["source_vertex_count"], stack["minimum_source_vertices_per_slice"])
            self.assertGreaterEqual(row["contour_point_count"], 8)
            for point in row["contour_points_m"]:
                self.assertEqual(len(point), 3)
                fixed_axis_index = {"x": 0, "y": 1, "z": 2}[row["fixed_axis"]]
                self.assertAlmostEqual(point[fixed_axis_index], row["plane_m"], places=6)

        landmark_ids = {row["landmark_id"] for row in measurement["landmarks"]}
        self.assertIn("frontmost_face_depth", landmark_ids)
        self.assertIn("rearmost_occiput_depth", landmark_ids)
        self.assertIn("brow_band_front_edge", landmark_ids)
        self.assertIn("mandible_left_width", landmark_ids)
        self.assertTrue(measurement["validation"]["contour_points_are_3d"])
        self.assertTrue(measurement["validation"]["coordinate_map_matches_build_report_bbox"])


if __name__ == "__main__":
    unittest.main()
