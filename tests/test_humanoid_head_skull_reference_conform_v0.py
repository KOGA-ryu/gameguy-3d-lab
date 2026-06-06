"""Tests for humanoid head skull-reference conform reporting."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILE_SCRIPT = REPO_ROOT / "scripts" / "compile_humanoid_head_skull_reference_conform_v0.py"
RENDER_SCRIPT = REPO_ROOT / "scripts" / "render_humanoid_head_skull_reference_conform_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidHeadSkullReferenceConformTests(unittest.TestCase):
    def test_conform_compiler_uses_external_skull_reference(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "conform"
            report_path = Path(tmp) / "conform_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(COMPILE_SCRIPT),
                    "--out-root",
                    str(out_root),
                    "--json-report",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS humanoid head skull reference conform compile", result.stdout)
        self.assertEqual(report["schema"], "humanoid_head_skull_reference_conform_report_v0")
        self.assertEqual(report["variant_count"], 5)
        self.assertEqual(report["skull_reference"]["source_id"], "human_skull_source_v1_full_skull_truth")
        self.assertEqual(report["skull_reference"]["phase_role"], "source_of_truth")
        self.assertIn("CC BY-SA", report["skull_reference"]["upstream_license_note"])
        self.assertTrue(report["validation"]["skull_reference_loaded"])
        self.assertTrue(report["validation"]["all_variant_numeric_qc_passed"])
        self.assertTrue(report["validation"]["all_conform_targets_present"])
        self.assertTrue(report["validation"]["all_join_blocked_until_conform_review"])

        for variant in report["variants"]:
            self.assertFalse(variant["missing_conform_targets"])
            self.assertEqual(variant["join_readiness_status"], "blocked_until_skull_conform_visual_review")
            self.assertGreaterEqual(len(variant["conform_recommendations"]), 10)
            self.assertIn(
                variant["profile_depth_status"],
                {"shallower_than_reference_skull", "near_reference_depth", "deeper_than_reference_skull"},
            )
            self.assertIn("y", variant["dimension_delta_variant_minus_fitted_skull_m"])

    def test_conform_render_runner_builds_overlay_matrix_without_render(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "conform_render"
            report_path = Path(tmp) / "render_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_SCRIPT),
                    "--out-root",
                    str(out_root),
                    "--json-report",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS humanoid head skull reference conform render", result.stdout)
        self.assertEqual(report["schema"], "humanoid_head_skull_reference_conform_render_report_v0")
        self.assertEqual(report["variant_count"], 5)
        self.assertEqual(report["overlay_view_count"], 4)
        self.assertEqual(report["total_overlay_records"], 20)
        self.assertFalse(report["render_requested"])
        self.assertTrue(report["validation"]["conform_compile_passed"])
        self.assertTrue(report["validation"]["all_variants_have_all_overlay_views"])
        for variant in report["variants"]:
            self.assertEqual(variant["overlay_view_count"], 4)
            self.assertFalse(variant["all_overlay_views_rendered"])
            for view in variant["views"]:
                self.assertEqual(view["status"], "planned_not_rendered")
                self.assertIsNone(view["render_path"])


if __name__ == "__main__":
    unittest.main()
