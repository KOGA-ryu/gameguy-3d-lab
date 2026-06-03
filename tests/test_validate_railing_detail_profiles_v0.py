#!/usr/bin/env python3
"""Tests for railing 2D detail profile source validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_railing_detail_profiles_v0.py"
BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "profile_sources" / "railing_detail_profiles_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_bad_bundle(bundle: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        bad_bundle = Path(tmp) / "bad_railing_detail_profiles.json"
        bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )


class RailingDetailProfileValidatorTests(unittest.TestCase):
    def test_default_bundle_passes_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "railing_detail_profile_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS railing detail profile validation", result.stdout)
        self.assertEqual(report["schema"], "railing_detail_profile_validation_result_v0")
        self.assertEqual(report["profile_count"], 7)
        self.assertEqual(report["reference_count"], 2)
        self.assertEqual(report["placement_count"], 21)
        self.assertEqual(report["sequence_count"], 8)
        self.assertEqual(report["sequence_covered_profile_count"], 7)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["placement_regions_checked"])
        self.assertTrue(report["rules"]["stage_order_checked"])

    def test_unknown_shape_term_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profiles"][0]["source_2d_shape"]["term_id"] = "unknown_shape"

        result = run_bad_bundle(bundle)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_2d_shape.term_id references unknown geometry term", result.stderr)

    def test_missing_placement_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profiles"][0]["where_used"] = []

        result = run_bad_bundle(bundle)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("where_used must not be empty", result.stderr)

    def test_tool_stage_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profiles"][0]["blender_tool_sequence"][0]["stage"] = "assembly"

        result = run_bad_bundle(bundle)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stage must match tool dictionary", result.stderr)

    def test_sequence_stage_order_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["railing_detail_sequence"][0]["stage"] = "validation_export"

        result = run_bad_bundle(bundle)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stage mismatch", result.stderr)

    def test_profile_count_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profile_count"] = 99

        result = run_bad_bundle(bundle)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("profile_count must match profiles length", result.stderr)


if __name__ == "__main__":
    unittest.main()
