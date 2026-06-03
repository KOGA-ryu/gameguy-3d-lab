#!/usr/bin/env python3
"""Tests for the Asset Mill retirement-readiness packet."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "workflow" / "reports" / "3D-LAB-0013-asset-mill-retirement-readiness" / "replacement_decision.json"
AUDIT = ROOT / "scripts" / "audit_script_orbit_v0.py"
PUMP = ROOT / "scripts" / "asset_pump_v0.py"
ASSET_VALIDATOR = ROOT / "scripts" / "validate_gameguy_asset_v0.py"
SIMPLE_ADAPTER = ROOT / "scripts" / "export_blender_asset_preview_v0.py"
MEASURED_ADAPTER = ROOT / "scripts" / "export_blender_measured_components_preview_v0.py"
MEASURED_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class AssetMillRetirementReadinessTests(unittest.TestCase):
    def test_packet_records_removed_replaced_scripts(self) -> None:
        decision = load_json(DECISION)
        candidates = decision["retirement_candidates"]

        self.assertEqual(decision["schema"], "asset_mill_retirement_readiness_decision_v0")
        self.assertEqual(decision["decision"], "DELETE_REPLACED_ASSET_MILL_SCRIPTS")
        self.assertTrue(decision["safe_to_delete_now"])
        self.assertEqual(len(candidates), 6)
        for candidate in candidates:
            self.assertEqual(candidate["bucket"], "REMOVED")
            self.assertFalse((ROOT / candidate["script"]).exists(), candidate["script"])
            for replacement in candidate["replaced_by"]:
                self.assertTrue((ROOT / replacement).exists(), replacement)

    def test_script_orbit_matches_retirement_packet(self) -> None:
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

        decision = load_json(DECISION)
        expected_counts = decision["script_orbit_expected_after"]
        rows = {row["script"]: row for row in report["scripts"]}

        self.assertEqual(report["bucket_counts"], expected_counts)
        for candidate in decision["retirement_candidates"]:
            self.assertNotIn(candidate["script"], rows)

    def test_replacement_outputs_match_packet_evidence(self) -> None:
        decision = load_json(DECISION)

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            simple_out = tmp_root / "simple_pump"
            simple_report = tmp_root / "simple_asset_report.json"
            simple_adapter_report = tmp_root / "simple_adapter_report.json"
            measured_out = tmp_root / "measured_pump"
            measured_report = tmp_root / "measured_asset_report.json"
            measured_adapter_report = tmp_root / "measured_adapter_report.json"

            subprocess.run([sys.executable, str(PUMP), "--out", str(simple_out)], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run(
                [sys.executable, str(ASSET_VALIDATOR), "--manifest", str(simple_out / "manifest.json"), "--json-report", str(simple_report)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SIMPLE_ADAPTER),
                    "--manifest",
                    str(simple_out / "manifest.json"),
                    "--validate-only",
                    "--json-report",
                    str(simple_adapter_report),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [sys.executable, str(PUMP), "--bundle", str(MEASURED_BUNDLE), "--out", str(measured_out)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [sys.executable, str(ASSET_VALIDATOR), "--manifest", str(measured_out / "manifest.json"), "--json-report", str(measured_report)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(MEASURED_ADAPTER),
                    "--manifest",
                    str(measured_out / "manifest.json"),
                    "--validate-only",
                    "--json-report",
                    str(measured_adapter_report),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            simple = load_json(simple_report)
            simple_adapter = load_json(simple_adapter_report)
            measured = load_json(measured_report)
            measured_adapter = load_json(measured_adapter_report)

        candidates = {candidate["script"]: candidate for candidate in decision["retirement_candidates"]}
        simple_evidence = candidates["scripts/compile_asset_mill_solids_v0.py"]["replacement_evidence"]
        smoke_evidence = candidates["scripts/blender_asset_mill_smoke_test_v0.py"]["replacement_evidence"]
        measured_compiler_evidence = candidates["scripts/compile_asset_mill_measured_components_v1.py"]["replacement_evidence"]
        measured_adapter_evidence = candidates["scripts/blender_asset_mill_measured_components_v1.py"]["replacement_evidence"]

        self.assertEqual(simple["asset_count"], simple_evidence["asset_count"])
        self.assertEqual(simple["total_vertices"], simple_evidence["vertex_count"])
        self.assertEqual(simple["total_faces"], simple_evidence["face_count"])
        self.assertEqual(simple_adapter["asset_count"], smoke_evidence["asset_count"])
        self.assertEqual(simple_adapter["total_vertices"], smoke_evidence["vertex_count"])
        self.assertEqual(simple_adapter["total_faces"], smoke_evidence["face_count"])
        self.assertEqual(measured["asset_count"], measured_compiler_evidence["pumped_asset_count"])
        self.assertEqual(measured["total_vertices"], measured_compiler_evidence["vertex_count"])
        self.assertEqual(measured["total_faces"], measured_compiler_evidence["face_count"])
        self.assertEqual(measured_adapter["asset_count"], measured_adapter_evidence["asset_count"])
        self.assertEqual(measured_adapter["proof_primitive_count"], measured_adapter_evidence["part_count"])
        self.assertEqual(measured_adapter["socket_count"], measured_adapter_evidence["socket_count"])


if __name__ == "__main__":
    unittest.main()
