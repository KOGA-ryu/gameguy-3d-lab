#!/usr/bin/env python3
"""Tests for reference-led asset dissection packet validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_reference_dissection_packet_v0.py"
PACKET = ROOT / "data" / "architecture" / "asset_mill" / "reference_packets" / "gothic_panel_guard_reference_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class ReferenceDissectionPacketValidatorTests(unittest.TestCase):
    def test_default_reference_packet_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "reference_packet_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS reference dissection packet validation", result.stdout)
        self.assertEqual(report["schema"], "asset_reference_dissection_packet_validation_result_v0")
        self.assertEqual(report["packet_id"], "gothic_panel_guard_reference_v0")
        self.assertEqual(report["component_count"], 9)
        self.assertGreaterEqual(report["component_tool_count"], 12)
        self.assertGreaterEqual(report["geometry_term_count"], 8)
        self.assertEqual(report["future_reference_only_tool_count"], 2)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["validates_geometry_terms"])
        self.assertTrue(report["rules"]["validates_blender_tool_ids"])
        self.assertTrue(report["rules"]["requires_deterministic_v0_tools"])

    def test_unknown_geometry_term_fails(self) -> None:
        packet = load_json(PACKET)
        packet["components"][0]["geometry_terms_used"].append("fake_arch_term")

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            packet_path = Path(tmp) / "bad_packet.json"
            packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--packet", str(packet_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown geometry term `fake_arch_term`", result.stderr)

    def test_nondeterministic_preferred_tool_fails(self) -> None:
        packet = load_json(PACKET)
        packet["components"][0]["candidate_blender_tools"][0]["tool_id"] = "sculpt_crease"

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            packet_path = Path(tmp) / "bad_packet.json"
            packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--packet", str(packet_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uses nondeterministic v0 tool `sculpt_crease`", result.stderr)

    def test_non_reference_future_tool_fails(self) -> None:
        packet = load_json(PACKET)
        packet["future_reference_only_tools"][0]["tool_id"] = "primitive_cube_add"

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            packet_path = Path(tmp) / "bad_packet.json"
            packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--packet", str(packet_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must use a reference_only dictionary tool", result.stderr)


if __name__ == "__main__":
    unittest.main()
