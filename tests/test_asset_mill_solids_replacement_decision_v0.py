#!/usr/bin/env python3
"""Tests for the Asset Mill solids replacement decision."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "workflow" / "reports" / "3D-LAB-0008-asset-mill-solids-replacement-decision" / "replacement_decision.json"
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"
RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json"
SCRIPTS = ROOT / "scripts"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class AssetMillSolidsReplacementDecisionTests(unittest.TestCase):
    def test_decision_evidence_matches_no_write_compiler_comparison(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import asset_pump_v0 as pump  # noqa: PLC0415
        import compile_asset_mill_solids_v0 as old_compiler  # noqa: PLC0415

        bundle = load_json(RECIPE)
        old_compiled = old_compiler.compile_bundle(bundle)
        pump.validate_recipe_terms(bundle, pump.load_geometry_terms())
        new_compiled: dict[str, dict[str, Any]] = {}
        for asset in bundle["assets"]:
            new_compiled[asset["asset_id"]] = pump.compile_asset(asset, new_compiled)

        dimension_mismatches = []
        for asset_id, new_asset in new_compiled.items():
            old_bounds = old_compiled[asset_id]["geometry_outputs"]["bounds"]
            old_dimensions = {
                "width": round(old_bounds["max"][0] - old_bounds["min"][0], 6),
                "depth": round(old_bounds["max"][1] - old_bounds["min"][1], 6),
                "height": round(old_bounds["max"][2] - old_bounds["min"][2], 6),
            }
            if old_dimensions != new_asset["dimensions_m"]:
                dimension_mismatches.append(asset_id)

        decision = load_json(DECISION)
        evidence = decision["comparison_evidence"]
        self.assertEqual(evidence["old_asset_count"], len(old_compiled))
        self.assertEqual(evidence["new_asset_count"], len(new_compiled))
        self.assertEqual(evidence["asset_ids_match"], sorted(old_compiled) == sorted(new_compiled))
        self.assertEqual(evidence["dimension_mismatch_count"], len(dimension_mismatches))
        self.assertTrue(all("child_slots" in asset for asset in new_compiled.values()))

    def test_replacement_decision_demotes_old_compiler_to_reference(self) -> None:
        decision = load_json(DECISION)

        self.assertEqual(decision["schema"], "asset_mill_solids_replacement_decision_v0")
        self.assertEqual(decision["target_script"], "scripts/compile_asset_mill_solids_v0.py")
        self.assertEqual(decision["replacement_script"], "scripts/asset_pump_v0.py")
        self.assertEqual(decision["decision"], "DEMOTE_TO_REFERENCE_ONLY")
        self.assertFalse(decision["safe_to_delete_now"])
        self.assertEqual(decision["comparison_evidence"]["old_asset_count"], 14)
        self.assertEqual(decision["comparison_evidence"]["new_asset_count"], 14)
        self.assertTrue(decision["comparison_evidence"]["asset_ids_match"])
        self.assertEqual(decision["comparison_evidence"]["dimension_mismatch_count"], 0)
        self.assertTrue(decision["comparison_evidence"]["new_preserves_child_slots"])

    def test_script_orbit_audit_matches_replacement_decision(self) -> None:
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
        self.assertEqual(rows["scripts/compile_asset_mill_solids_v0.py"]["bucket"], "DELETE_LATER")


if __name__ == "__main__":
    unittest.main()
