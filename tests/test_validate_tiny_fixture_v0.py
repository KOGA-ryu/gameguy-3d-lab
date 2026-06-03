#!/usr/bin/env python3
"""Tests for the canonical tiny source fixture validator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_tiny_fixture_v0.py"
FIXTURE = ROOT / "data" / "architecture" / "test_fixtures" / "tiny_map_building_connector_fixture_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class TinyFixtureValidatorTests(unittest.TestCase):
    def test_default_fixture_passes_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report = Path(tmp) / "tiny_fixture_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = load_json(report)

        self.assertIn("PASS tiny fixture validation", result.stdout)
        self.assertEqual(payload["schema"], "tiny_fixture_validation_result_v0")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["cell_count"], 7)
        self.assertEqual(payload["plug_count"], 2)
        self.assertFalse(payload["generated_outputs_created"])
        self.assertEqual(payload["errors"], [])

    def test_unknown_connector_asset_fails(self) -> None:
        fixture = load_json(FIXTURE)
        fixture["connector_path_segments"][0]["connector_asset_id"] = "missing_connector_asset_v0"

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            fixture_path = Path(tmp) / "bad_fixture.json"
            fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--fixture", str(fixture_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown connector asset ID", result.stderr)

    def test_height_delta_must_match_cell_heights(self) -> None:
        fixture = load_json(FIXTURE)
        fixture["terrain_height_changes"][0]["delta_m"] = 0.25

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            fixture_path = Path(tmp) / "bad_fixture.json"
            fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--fixture", str(fixture_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cell heights imply 0.5", result.stderr)


if __name__ == "__main__":
    unittest.main()
