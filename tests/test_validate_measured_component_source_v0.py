#!/usr/bin/env python3
"""Tests for promoted measured component source validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_measured_component_source_v0.py"
BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class MeasuredComponentSourceValidatorTests(unittest.TestCase):
    def test_default_bundle_passes_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "measured_component_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS measured component source validation", result.stdout)
        self.assertEqual(report["schema"], "measured_component_source_validation_result_v0")
        self.assertEqual(report["asset_count"], 22)
        self.assertEqual(report["v1_asset_count"], 12)
        self.assertEqual(report["v2_asset_count"], 10)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["no_goal_references"])

    def test_bundle_has_no_goal_refs_or_wall_clock_fields(self) -> None:
        bundle = load_json(BUNDLE)
        text = json.dumps(bundle)

        self.assertNotIn("goal/", text)
        self.assertNotIn("created_at_utc", text)
        self.assertEqual(bundle["asset_count"], len(bundle["assets"]))
        self.assertEqual(bundle["v1_asset_count"], sum(1 for asset in bundle["assets"] if asset["source_version"] == "v1"))
        self.assertEqual(bundle["v2_asset_count"], sum(1 for asset in bundle["assets"] if asset["source_version"] == "v2"))

    def test_goal_reference_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["assets"][0]["source_measurement_refs"].append(
            {"ref_type": "local_policy_doc", "ref": "goal/architecture/generated_report.md"}
        )

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_measured_components.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not reference generated goal output", result.stderr)


if __name__ == "__main__":
    unittest.main()
