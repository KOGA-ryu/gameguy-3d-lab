#!/usr/bin/env python3
"""Tests for measured molding profile source validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_measured_molding_profiles_v0.py"
BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "profile_sources" / "measured_molding_profiles_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class MeasuredMoldingProfileValidatorTests(unittest.TestCase):
    def test_default_bundle_passes_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "measured_molding_profile_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS measured molding profile validation", result.stdout)
        self.assertEqual(report["schema"], "measured_molding_profile_validation_result_v0")
        self.assertEqual(report["profile_count"], 5)
        self.assertEqual(report["reference_count"], 2)
        self.assertEqual(report["profile_family_counts"]["side_molding_profile"], 3)
        self.assertEqual(report["profile_family_counts"]["shaft_channel_cross_section"], 1)
        self.assertEqual(report["profile_family_counts"]["compound_pier_cross_section"], 1)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["source_profile_only"])

    def test_unknown_geometry_term_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profiles"][0]["operations"].append("unknown_profile_operation")

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_measured_molding_profiles.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown geometry terms", result.stderr)

    def test_family_coordinate_space_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profiles"][0]["coordinate_space"] = "local_xy"

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_measured_molding_profiles.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("coordinate_space must be local_xz", result.stderr)

    def test_unknown_blender_tool_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profiles"][0]["candidate_blender_tools"][0]["tool_id"] = "unknown_blender_tool"

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_measured_molding_profiles.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown Blender tool", result.stderr)

    def test_profile_count_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["profile_count"] = 99

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_measured_molding_profiles.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("profile_count must match profiles length", result.stderr)


if __name__ == "__main__":
    unittest.main()
