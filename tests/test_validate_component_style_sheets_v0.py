#!/usr/bin/env python3
"""Tests for component style sheet source validation."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_component_style_sheets_v0.py"
BUNDLE = ROOT / "data" / "architecture" / "component_style_sheets" / "railings" / "gothic_railing_post_style_sheets_v0.json"
TAXONOMY = ROOT / "data" / "architecture" / "taxonomy" / "component_domains" / "component_domain_taxonomy_v0.json"
TOOLS = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def load_validator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_component_style_sheets_v0", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load component style sheet validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ComponentStyleSheetValidatorTests(unittest.TestCase):
    def test_default_registry_passes_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "component_style_sheet_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS component style sheet validation", result.stdout)
        self.assertEqual(report["schema"], "component_style_sheet_validation_result_v0")
        self.assertEqual(report["domain_count"], 7)
        self.assertEqual(report["taxonomy_component_count"], 70)
        self.assertEqual(report["style_family_count"], 10)
        self.assertEqual(report["style_sheet_bundle_count"], 1)
        self.assertEqual(report["style_sheet_count"], 5)
        self.assertEqual(report["ledger_entry_count"], 11)
        self.assertEqual(report["source_count"], 7)
        self.assertEqual(report["source_shape_term_count"], 11)
        self.assertEqual(report["operation_term_count"], 12)
        self.assertEqual(report["blender_tool_count"], 23)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["validates_domain_taxonomy"])
        self.assertTrue(report["rules"]["validates_blender_tools"])

    def run_bad_bundle(self, bundle: dict[str, Any], *, expected_count: int = 5) -> str:
        module = load_validator_module()
        _, components_by_domain, style_families, _ = module.validate_domain_taxonomy(TAXONOMY)
        geometry_terms = module.load_geometry_terms()
        tools, stage_order = module.load_tool_dictionary(TOOLS)
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_component_style_sheet.json"
            bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    module.validate_bundle(
                        bundle_path,
                        expected_count,
                        "railings",
                        "gothic",
                        TAXONOMY,
                        components_by_domain,
                        style_families,
                        geometry_terms,
                        tools,
                        stage_order,
                    )
        self.assertNotEqual(raised.exception.code, 0)
        return stderr.getvalue()

    def test_unknown_component_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["style_sheets"][0]["component"] = "unknown_post"

        message = self.run_bad_bundle(bundle)

        self.assertIn("unknown taxonomy component", message)

    def test_unknown_source_shape_term_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["style_sheets"][0]["geometric_shaping_ledger"][0]["source_shapes"][0]["term_id"] = "unknown_shape"

        message = self.run_bad_bundle(bundle)

        self.assertIn("unknown geometry term", message)

    def test_blender_tool_stage_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)
        bundle["style_sheets"][0]["geometric_shaping_ledger"][0]["blender_tool_sequence"][0]["stage"] = "assembly"

        message = self.run_bad_bundle(bundle)

        self.assertIn("stage must match tool dictionary", message)

    def test_style_sheet_count_mismatch_fails_validation(self) -> None:
        bundle = load_json(BUNDLE)

        message = self.run_bad_bundle(bundle, expected_count=99)

        self.assertIn("expected_style_sheet_count must match style_sheets length", message)


if __name__ == "__main__":
    unittest.main()
