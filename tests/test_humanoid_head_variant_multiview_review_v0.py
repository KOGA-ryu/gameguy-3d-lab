"""Tests for humanoid head multi-view variant review generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "render_humanoid_head_variant_multiview_review_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidHeadVariantMultiviewReviewTests(unittest.TestCase):
    def test_multiview_review_builds_five_by_five_matrix_without_render(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "multiview"
            report_path = Path(tmp) / "multiview_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
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

            self.assertIn("PASS humanoid head variant multiview review", result.stdout)
            self.assertEqual(report["schema"], "humanoid_head_variant_multiview_review_report_v0")
            self.assertEqual(report["variant_count"], 5)
            self.assertEqual(report["view_count"], 5)
            self.assertEqual(report["total_view_records"], 25)
            self.assertFalse(report["render_requested"])
            self.assertTrue(report["validation"]["all_numeric_qc_passed"])
            self.assertTrue(report["validation"]["all_geometry_signatures_unique"])
            self.assertTrue(report["validation"]["all_variants_have_all_views"])

            view_ids = {view["view_id"] for view in report["views"]}
            self.assertEqual(
                view_ids,
                {"front", "three_quarter_front", "left_profile", "right_profile", "top_construction"},
            )
            for variant in report["variants"]:
                self.assertEqual(variant["view_count"], 5)
                self.assertEqual(variant["max_symmetry_error_m"], 0.0)
                self.assertEqual(variant["max_connection_gap_m"], 0.0)
                self.assertEqual(variant["front_read_status"], "planned_not_rendered")
                self.assertEqual(variant["profile_read_status"], "planned_not_rendered")
                self.assertEqual(
                    variant["join_readiness_status"],
                    "numeric_precheck_passed_visual_review_required",
                )
                for view in variant["views"]:
                    self.assertIsNone(view["render_path"])
                    self.assertEqual(view["status"], "planned_not_rendered")


if __name__ == "__main__":
    unittest.main()
