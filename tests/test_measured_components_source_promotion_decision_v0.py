#!/usr/bin/env python3
"""Tests for the measured component source promotion decision."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "workflow" / "reports" / "3D-LAB-0009-measured-components-source-promotion" / "replacement_decision.json"
BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class MeasuredComponentsSourcePromotionDecisionTests(unittest.TestCase):
    def test_decision_matches_promoted_source_bundle(self) -> None:
        decision = load_json(DECISION)
        bundle = load_json(BUNDLE)

        self.assertEqual(decision["schema"], "measured_components_source_promotion_decision_v0")
        self.assertEqual(decision["replacement_source"], "data/architecture/asset_mill/recipes/measured_components_v0.json")
        self.assertEqual(decision["validator"], "scripts/validate_measured_component_source_v0.py")
        self.assertEqual(decision["decision"], "PROMOTE_SOURCE_AND_DEMOTE_SCRIPTS_TO_REFERENCE_ONLY")
        self.assertFalse(decision["safe_to_delete_now"])
        self.assertEqual(decision["comparison_evidence"]["v1_asset_count"], bundle["v1_asset_count"])
        self.assertEqual(decision["comparison_evidence"]["v2_asset_count"], bundle["v2_asset_count"])
        self.assertEqual(decision["comparison_evidence"]["promoted_asset_count"], bundle["asset_count"])
        self.assertNotIn("goal/", json.dumps(bundle))
        self.assertNotIn("created_at_utc", json.dumps(bundle))

    def test_script_orbit_has_no_replace_by_pump_scripts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "script_orbit.json"
            subprocess.run(
                [sys.executable, str(AUDIT), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        rows = {row["script"]: row for row in report["scripts"]}
        self.assertEqual(report["bucket_counts"]["REPLACE_BY_PUMP"], 0)
        self.assertEqual(rows["scripts/compile_asset_mill_measured_components_v1.py"]["bucket"], "REFERENCE_ONLY")
        self.assertEqual(rows["scripts/compile_asset_mill_measured_components_v2.py"]["bucket"], "REFERENCE_ONLY")


if __name__ == "__main__":
    unittest.main()
