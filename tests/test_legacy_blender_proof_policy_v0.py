#!/usr/bin/env python3
"""Tests for legacy Blender proof script policy."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "workflow" / "reports" / "3D-LAB-0012-legacy-blender-proof-policy" / "replacement_decision.json"
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class LegacyBlenderProofPolicyTests(unittest.TestCase):
    def test_script_orbit_has_no_pending_conversion_buckets(self) -> None:
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

        self.assertEqual(report["bucket_counts"]["CONVERT_TO_ADAPTER"], 0)
        self.assertEqual(report["bucket_counts"]["REPLACE_BY_PUMP"], 0)
        rows = {row["script"]: row for row in report["scripts"]}
        self.assertEqual(rows["scripts/blender_integrated_map_scene_v0.py"]["bucket"], "REFERENCE_ONLY")
        self.assertEqual(rows["scripts/blender_tiled_map_template_v0.py"]["bucket"], "REFERENCE_ONLY")
        self.assertEqual(rows["scripts/export_blender_asset_preview_v0.py"]["bucket"], "KEEP_CANONICAL")
        self.assertEqual(rows["scripts/export_blender_measured_components_preview_v0.py"]["bucket"], "KEEP_CANONICAL")

    def test_decision_lists_demoted_legacy_proofs(self) -> None:
        decision = load_json(DECISION)

        self.assertEqual(decision["schema"], "legacy_blender_proof_policy_decision_v0")
        self.assertEqual(decision["decision"], "DEMOTE_LEGACY_BLENDER_PROOFS_TO_REFERENCE_ONLY")
        self.assertFalse(decision["safe_to_delete_now"])
        self.assertEqual(decision["script_orbit_after"]["CONVERT_TO_ADAPTER"], 0)
        self.assertEqual(decision["script_orbit_after"]["REPLACE_BY_PUMP"], 0)
        self.assertIn("scripts/blender_integrated_map_scene_v0.py", decision["legacy_blender_proofs_demoted"])
        self.assertIn("scripts/export_blender_asset_preview_v0.py", decision["canonical_adapters"])


if __name__ == "__main__":
    unittest.main()
