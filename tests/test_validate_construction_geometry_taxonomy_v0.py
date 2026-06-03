#!/usr/bin/env python3
"""Tests for construction geometry taxonomy validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_construction_geometry_taxonomy_v0.py"
BUNDLE = ROOT / "data" / "architecture" / "taxonomy" / "construction_geometry" / "construction_geometry_taxonomy_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class ConstructionGeometryTaxonomyValidatorTests(unittest.TestCase):
    def test_default_taxonomy_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "taxonomy_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS construction geometry taxonomy validation", result.stdout)
        self.assertEqual(report["schema"], "construction_geometry_taxonomy_validation_v0")
        self.assertEqual(report["source_count"], 9)
        self.assertEqual(report["taxonomy_term_count"], 23)
        self.assertEqual(report["claim_count"], 5)
        self.assertEqual(report["repo_mapping_count"], 9)
        self.assertFalse(report["rules"]["runs_blender"])
        self.assertTrue(report["rules"]["validates_required_terms"])
        self.assertTrue(report["rules"]["validates_source_support"])

    def test_missing_required_term_fails(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["taxonomy_terms"] = [
            term for term in bundle["taxonomy_terms"] if term["term_id"] != "construction_field"
        ]
        bundle["taxonomy_term_count"] = len(bundle["taxonomy_terms"])

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_taxonomy.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required construction geometry terms", result.stderr)

    def test_unknown_source_support_fails(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["taxonomy_terms"][0]["source_support"].append("missing_source")

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_taxonomy.json"
            bad_bundle.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--bundle", str(bad_bundle)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown source ids", result.stderr)


if __name__ == "__main__":
    unittest.main()
