"""Tests for humanoid head control variant generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate_humanoid_head_control_variants_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class HumanoidHeadControlVariantTests(unittest.TestCase):
    def test_generator_emits_distinct_qc_passing_variants(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "variants"
            report_path = Path(tmp) / "variant_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
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

            self.assertIn("PASS humanoid head control variants", result.stdout)
            self.assertEqual(report["schema"], "humanoid_head_control_variants_report_v0")
            self.assertEqual(report["variant_count"], 5)
            self.assertEqual(report["unique_geometry_signature_count"], 5)
            self.assertTrue(report["validation"]["all_qc_passed"])
            self.assertTrue(report["validation"]["all_geometry_signatures_unique"])
            self.assertFalse(report["render_requested"])

            signatures = {variant["geometry_signature"] for variant in report["variants"]}
            self.assertEqual(len(signatures), 5)
            for variant in report["variants"]:
                self.assertTrue(Path(variant["recipe_path"]).exists())
                self.assertTrue(Path(variant["qc_report_path"]).exists())
                self.assertIsNone(variant["render_path"])
                self.assertEqual(variant["max_connection_gap_m"], 0.0)
                self.assertEqual(variant["max_symmetry_error_m"], 0.0)
                self.assertTrue(variant["qc_passed"])

    def test_variant_overrides_reach_compiled_recipe(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "variants"
            subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--out-root",
                    str(out_root),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            neutral = load_json(out_root / "neutral_mannequin_head_v0" / "neutral_mannequin_head_v0.json")
            strong = load_json(out_root / "strong_brow_deep_socket_head_v0" / "strong_brow_deep_socket_head_v0.json")
            narrow = load_json(out_root / "narrow_long_face_head_v0" / "narrow_long_face_head_v0.json")

        neutral_controls = {row["control_id"]: row["value"] for row in neutral["shape_refinement_controls"]}
        strong_controls = {row["control_id"]: row["value"] for row in strong["shape_refinement_controls"]}
        self.assertGreater(strong_controls["brow_arc_ratio"], neutral_controls["brow_arc_ratio"])
        self.assertGreater(strong_controls["feature_embed_overlap_m"], neutral_controls["feature_embed_overlap_m"])
        self.assertLess(
            narrow["measurement_profile"]["dimensions_m"]["head_breadth"],
            neutral["measurement_profile"]["dimensions_m"]["head_breadth"],
        )
        self.assertGreater(
            narrow["measurement_profile"]["dimensions_m"]["menton_sellion_length"],
            neutral["measurement_profile"]["dimensions_m"]["menton_sellion_length"],
        )


if __name__ == "__main__":
    unittest.main()
