#!/usr/bin/env python3
"""Tests for canonical asset generation registry validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_asset_generation_registry_v0.py"
REGISTRY = ROOT / "data" / "architecture" / "asset_mill" / "asset_generation_registry_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


class AssetGenerationRegistryValidatorTests(unittest.TestCase):
    def test_default_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "registry_validation.json"
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--json-report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS asset generation registry validation", result.stdout)
        self.assertEqual(report["schema"], "asset_generation_registry_validation_result_v0")
        self.assertEqual(report["canonical_geometry_bundle_count"], 5)
        self.assertEqual(report["canonical_geometry_asset_count"], 40)
        self.assertEqual(report["canonical_tool_plan_bundle"]["asset_family_policy_count"], 9)
        self.assertEqual(report["canonical_tool_plan_bundle"]["default_plan_count"], 10)
        self.assertEqual(report["canonical_tool_plan_bundle"]["geometry_dictionary"], "geometry_dictionary")
        self.assertEqual(report["source_asset_polish_plan_bundle_count"], 1)
        self.assertEqual(report["source_asset_polish_plan_count"], 1)
        self.assertEqual(report["source_profile_bundle_count"], 2)
        self.assertEqual(report["source_profile_count"], 19)
        self.assertEqual(report["source_graph_bundle_count"], 1)
        self.assertEqual(report["source_graph_count"], 1)
        self.assertEqual(report["source_cell_selection_bundle_count"], 1)
        self.assertEqual(report["source_cell_selection_set_count"], 1)
        self.assertEqual(report["source_pattern_field_bundle_count"], 1)
        self.assertEqual(report["source_pattern_field_count"], 1)
        self.assertEqual(report["source_pattern_segment_bundle_count"], 1)
        self.assertEqual(report["source_pattern_segment_set_count"], 1)
        self.assertEqual(report["source_taxonomy_bundle_count"], 1)
        self.assertEqual(report["source_taxonomy_term_count"], 23)
        self.assertEqual(report["reference_only_recipe_count"], 3)
        self.assertFalse(report["generated_outputs_created"])
        self.assertTrue(report["rules"]["validates_pipeline_label_coverage"])
        self.assertTrue(report["rules"]["validates_source_asset_polish_plan_boundaries"])
        self.assertTrue(report["rules"]["validates_source_profile_boundaries"])
        self.assertTrue(report["rules"]["validates_source_graph_boundaries"])
        self.assertTrue(report["rules"]["validates_source_cell_selection_boundaries"])
        self.assertTrue(report["rules"]["validates_source_pattern_field_boundaries"])
        self.assertTrue(report["rules"]["validates_source_pattern_segment_boundaries"])
        self.assertTrue(report["rules"]["validates_source_taxonomy_boundaries"])

    def test_unknown_pipeline_label_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["canonical_geometry_bundles"][0]["pipeline_labels"].append("missing_pipeline_label")

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown pipeline labels", result.stderr)

    def test_reference_recipe_cannot_also_be_canonical(self) -> None:
        registry = load_json(REGISTRY)
        registry["reference_only_recipe_bundles"][0]["path"] = registry["canonical_geometry_bundles"][0]["path"]
        registry["reference_only_recipe_bundles"][0]["schema"] = registry["canonical_geometry_bundles"][0]["schema"]

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not also be canonical", result.stderr)

    def test_sequence_policy_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["canonical_tool_plan_bundle"]["expected_asset_family_policy_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_asset_family_policy_count must match sequence policy", result.stderr)

    def test_source_profile_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_profile_bundles"][0]["expected_profile_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_profile_count must match profiles length", result.stderr)

    def test_source_asset_polish_plan_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_asset_polish_plan_bundles"][0]["expected_plan_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_plan_count must match plans length", result.stderr)

    def test_source_graph_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_graph_bundles"][0]["expected_graph_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_graph_count must match graphs length", result.stderr)

    def test_source_cell_selection_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_cell_selection_bundles"][0]["expected_selection_set_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_selection_set_count must match selection_sets length", result.stderr)

    def test_source_taxonomy_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_taxonomy_bundles"][0]["expected_term_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_term_count must match taxonomy_terms length", result.stderr)

    def test_source_pattern_field_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_pattern_field_bundles"][0]["expected_field_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_field_count must match fields length", result.stderr)

    def test_source_pattern_segment_count_mismatch_fails(self) -> None:
        registry = load_json(REGISTRY)
        registry["source_pattern_segment_bundles"][0]["expected_segment_set_count"] = 999

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            registry_path = Path(tmp) / "bad_registry.json"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_segment_set_count must match segment_sets length", result.stderr)


if __name__ == "__main__":
    unittest.main()
