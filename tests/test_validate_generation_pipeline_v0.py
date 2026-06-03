#!/usr/bin/env python3
"""Tests for the deterministic 3D generation pipeline validator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "scripts" / "validate_generation_pipeline_v0.py"


def load_pipeline_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_generation_pipeline_v0", PIPELINE)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load pipeline module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerationPipelineValidatorTests(unittest.TestCase):
    def test_non_blender_pipeline_gate_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "pipeline_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINE),
                    "--skip-unit-tests",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertIn("PASS generation pipeline validation", result.stdout)
        self.assertEqual(report["schema"], "gameguy_3d_generation_pipeline_validation_v0")
        self.assertFalse(report["include_blender"])
        self.assertFalse(report["unit_tests_run"])
        self.assertGreater(report["json_file_count"], 0)
        self.assertGreater(report["command_count"], 10)
        self.assertEqual(report["pattern_lab_path_count"], 0)
        self.assertEqual(report["repo_media_mesh_output_count"], 0)
        self.assertFalse(report["rules"]["generated_outputs_in_repo"])
        labels = {command["label"] for command in report["commands"]}
        self.assertIn("generation_registry_validate", labels)
        self.assertIn("reference_dissection_validate", labels)
        self.assertIn("measured_molding_profile_validate", labels)
        self.assertIn("railing_detail_profile_validate", labels)
        self.assertIn("tool_plan_validate", labels)
        self.assertIn("fence_post_blender_adapter_validate_only", labels)
        self.assertIn("rail_segment_blender_adapter_validate_only", labels)
        self.assertIn("column_blender_adapter_validate_only", labels)
        self.assertIn("window_frame_blender_adapter_validate_only", labels)
        self.assertIn("door_frame_blender_adapter_validate_only", labels)
        self.assertIn("guard_panel_blender_adapter_validate_only", labels)
        self.assertIn("simple_asset_validate", labels)
        self.assertIn("measured_asset_adapter_validate", labels)
        self.assertIn("script_orbit_audit", labels)

        module = load_pipeline_module()
        blender_labels = {
            step.label for step in module.build_command_steps(include_blender=True, skip_unit_tests=True, blender_path=module.DEFAULT_BLENDER)
        }
        self.assertIn("fence_post_blender_execution_report_validate", blender_labels)
        self.assertIn("rail_segment_blender_execution_report_validate", blender_labels)
        self.assertIn("column_blender_execution_report_validate", blender_labels)
        self.assertIn("window_frame_blender_execution_report_validate", blender_labels)
        self.assertIn("door_frame_blender_execution_report_validate", blender_labels)
        self.assertIn("guard_panel_blender_execution_report_validate", blender_labels)

    def test_forbidden_output_guard_detects_media_and_mesh_files(self) -> None:
        module = load_pipeline_module()
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            self.assertEqual(module.find_forbidden_output_files(tmp_root), [])
            (tmp_root / "bad_preview.glb").write_text("not allowed\n", encoding="utf-8")
            (tmp_root / "bad_render.png").write_text("not allowed\n", encoding="utf-8")

            forbidden = module.find_forbidden_output_files(tmp_root)

        self.assertEqual(forbidden, ["bad_preview.glb", "bad_render.png"])


if __name__ == "__main__":
    unittest.main()
