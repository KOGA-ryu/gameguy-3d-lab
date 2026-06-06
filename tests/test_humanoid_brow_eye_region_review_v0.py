"""Tests for the compact brow/eye-region review compiler."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILE_SCRIPT = REPO_ROOT / "scripts" / "compile_humanoid_brow_eye_region_review_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidBrowEyeRegionReviewTests(unittest.TestCase):
    def test_compiler_emits_compact_brow_region_report_without_raw_contours(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "brow_eye_region_report.json"
            markdown_path = Path(tmp) / "brow_eye_region_report.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(COMPILE_SCRIPT),
                    "--json-report",
                    str(report_path),
                    "--markdown",
                    str(markdown_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)
            raw_report_text = report_path.read_text(encoding="utf-8")
            self.assertTrue(markdown_path.exists())
            markdown_text = markdown_path.read_text(encoding="utf-8")

        self.assertIn("PASS humanoid brow eye region review", result.stdout)
        self.assertEqual(report["schema"], "humanoid_brow_eye_region_review_v0")
        self.assertEqual(report["region_id"], "brow_eye_band")
        self.assertTrue(report["validation"]["compiled_head_blockout_not_read"])
        self.assertTrue(report["validation"]["raw_contour_points_omitted"])
        self.assertTrue(report["validation"]["all_evidence_slices_found"])
        self.assertNotIn("contour_points_m", raw_report_text)
        self.assertNotIn("humanoid_head_blockout_v0.json", raw_report_text)
        self.assertLess(len(raw_report_text), 32000)
        self.assertIn("brow ridge and eye socket band", markdown_text)

        slice_ids = {row["slice_id"] for row in report["selected_skull_slice_summaries"]}
        self.assertEqual(slice_ids, {"xy_brow_band", "yz_center_profile", "xz_front_face_surface", "xy_zygoma_orbit"})

        metrics = report["region_metrics_m"]
        self.assertGreater(metrics["brow_band_width_m"], 0.05)
        self.assertGreater(metrics["brow_band_depth_m"], 0.05)
        self.assertGreater(metrics["brow_to_lower_orbit_z_gap_m"], 0.0)

        existing_controls = {row["control_id"] for row in report["controls"]["existing_shape_controls"]}
        self.assertIn("brow_arc_ratio", existing_controls)
        self.assertIn("eye_socket_slant_ratio", existing_controls)
        proposed_controls = {row["control_id"] for row in report["controls"]["proposed_region_controls"]}
        self.assertIn("brow_forward_offset_m", proposed_controls)
        self.assertIn("socket_under_brow_setback_m", proposed_controls)
        self.assertTrue(all(row["promoted_to_taxonomy"] for row in report["controls"]["proposed_region_controls"]))


if __name__ == "__main__":
    unittest.main()
