#!/usr/bin/env python3
"""Tests for Blender tool-plan execution quality report validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_blender_tool_plan_execution_report_v0.py"


def valid_report() -> dict[str, Any]:
    return {
        "schema": "blender_tool_plan_execution_report_v0",
        "adapter": "scripts/execute_blender_tool_plan_v0.py",
        "source_plan": "/tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json",
        "plan_schema": "gameguy_tool_plan_v0",
        "plan_id": "gothic_stone_banister_post_tool_plan_v0_compiled",
        "asset_id": "gothic_stone_banister_post_tool_plan_v0",
        "asset_family": "banister_post",
        "style": "gothic_stone",
        "step_count": 32,
        "supported_step_count": 32,
        "unique_tool_count": 4,
        "unique_tools": ["export_gltf", "material_assign_by_part", "modifier_boolean", "validate_non_manifold"],
        "generated_outputs_created": True,
        "render_requested": True,
        "export_requested": True,
        "rules": {
            "consumes_gameguy_tool_plan_v0": True,
            "reads_source_intent_recipe": False,
            "runs_tool_plan_compiler": False,
            "imports_asset_pump": False,
            "executes_only_supported_deterministic_steps": True,
            "source_design_logic": False,
        },
        "blend_path": "/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0.blend",
        "object_count": 5,
        "mesh_object_count": 3,
        "executed_step_count": 32,
        "skipped_step_count": 0,
        "executed_steps": [],
        "skipped_steps": [],
        "bounds_m": {"min": [-0.25, -0.25, 0.0], "max": [0.25, 0.25, 1.35]},
        "validation": {
            "non_manifold_edge_count_before_cleanup": 0,
            "non_manifold_edge_count": 0,
        },
        "material_regions": {
            "material_slot_count": 6,
            "face_counts_by_role": {
                "base": 158,
                "cap": 106,
                "rib": 626,
                "shaft": 115,
                "socket_shadow": 153,
            },
            "material_slots": [],
        },
        "socket_pass": {
            "step_id": "boolean_cut_rail_sockets",
            "operation": "DIFFERENCE",
            "solver_requested": "EXACT",
            "target_names": ["post_core"],
            "cutter_names": ["east_socket_cutter", "west_socket_cutter"],
            "applied_modifier_count": 2,
            "failed_modifier_count": 0,
            "socket_shadow_panel_count": 2,
            "cutter_objects_removed": True,
            "removed_cutter_names": ["east_socket_cutter", "west_socket_cutter"],
        },
        "topology_cleanup": {
            "attempted": True,
            "operations": ["remove_doubles", "fill_holes", "normals_make_consistent"],
            "merge_distance_m": 0.0,
            "fill_hole_sides": 0,
            "vertex_count_before": 1225,
            "edge_count_before": 2343,
            "face_count_before": 1158,
            "vertex_count_after": 1225,
            "edge_count_after": 2343,
            "face_count_after": 1158,
            "non_manifold_edge_count_before": 0,
            "non_manifold_edge_count_after": 0,
        },
        "quality_pass": {
            "asset_family_quality_profile": "banister_post",
            "material_regions_preserved": True,
            "explicit_socket_boolean_targets": True,
            "socket_cutters_removed": True,
            "socket_boolean_not_required": False,
            "topology_cleanup_attempted": True,
        },
        "render_path": "/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_workbench.png",
        "export_path": "/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0.glb",
        "final_object": {
            "name": "gothic_stone_banister_post_tool_plan_v0",
            "vertex_count": 1225,
            "edge_count": 2343,
            "face_count": 1158,
            "material_slot_count": 6,
        },
    }


def valid_window_frame_report() -> dict[str, Any]:
    report = valid_report()
    report.update(
        {
            "source_plan": "/tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_window_frame_tool_plan_v0_compiled.json",
            "plan_id": "gothic_stone_window_frame_tool_plan_v0_compiled",
            "asset_id": "gothic_stone_window_frame_tool_plan_v0",
            "asset_family": "window_frame",
            "step_count": 25,
            "supported_step_count": 25,
            "unique_tool_count": 3,
            "unique_tools": ["join_objects", "material_assign_by_part", "validate_non_manifold"],
            "executed_step_count": 25,
            "bounds_m": {"min": [-0.46, -0.08, 0.0], "max": [0.46, 0.08, 1.18]},
            "material_regions": {
                "material_slot_count": 1,
                "face_counts_by_role": {
                    "frame": 24
                },
                "material_slots": [],
            },
            "socket_pass": {},
            "quality_pass": {
                "asset_family_quality_profile": "window_frame",
                "material_regions_preserved": True,
                "explicit_socket_boolean_targets": False,
                "socket_cutters_removed": False,
                "socket_boolean_not_required": True,
                "topology_cleanup_attempted": True,
            },
            "final_object": {
                "name": "gothic_stone_window_frame_tool_plan_v0",
                "vertex_count": 32,
                "edge_count": 48,
                "face_count": 24,
                "material_slot_count": 1,
            },
        }
    )
    return report


def valid_fence_post_report() -> dict[str, Any]:
    report = valid_report()
    report.update(
        {
            "source_plan": "/tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_fence_post_tool_plan_v0_compiled.json",
            "plan_id": "gothic_stone_fence_post_tool_plan_v0_compiled",
            "asset_id": "gothic_stone_fence_post_tool_plan_v0",
            "asset_family": "fence_post",
            "bounds_m": {"min": [-0.22, -0.22, 0.0], "max": [0.22, 0.22, 1.1]},
            "quality_pass": {
                "asset_family_quality_profile": "fence_post",
                "material_regions_preserved": True,
                "explicit_socket_boolean_targets": True,
                "socket_cutters_removed": True,
                "socket_boolean_not_required": False,
                "topology_cleanup_attempted": True,
            },
            "final_object": {
                "name": "gothic_stone_fence_post_tool_plan_v0",
                "vertex_count": 900,
                "edge_count": 1700,
                "face_count": 850,
                "material_slot_count": 6,
            },
        }
    )
    return report


def valid_door_frame_report() -> dict[str, Any]:
    report = valid_window_frame_report()
    report.update(
        {
            "source_plan": "/tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_door_frame_tool_plan_v0_compiled.json",
            "plan_id": "gothic_stone_door_frame_tool_plan_v0_compiled",
            "asset_id": "gothic_stone_door_frame_tool_plan_v0",
            "asset_family": "door_frame",
            "bounds_m": {"min": [-0.55, -0.1, 0.0], "max": [0.55, 0.1, 1.75]},
            "quality_pass": {
                "asset_family_quality_profile": "door_frame",
                "material_regions_preserved": True,
                "explicit_socket_boolean_targets": False,
                "socket_cutters_removed": False,
                "socket_boolean_not_required": True,
                "topology_cleanup_attempted": True,
            },
            "final_object": {
                "name": "gothic_stone_door_frame_tool_plan_v0",
                "vertex_count": 32,
                "edge_count": 48,
                "face_count": 24,
                "material_slot_count": 1,
            },
        }
    )
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def run_validator(path: Path, json_report: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(VALIDATOR), "--report", str(path)]
    if json_report is not None:
        command.extend(["--json-report", str(json_report)])
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)


class BlenderToolPlanExecutionReportValidatorTests(unittest.TestCase):
    def test_accepts_quality_execution_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            json_report = Path(tmp) / "quality_validation.json"
            write_report(report_path, valid_report())
            result = run_validator(report_path, json_report)
            validation = json.loads(json_report.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS Blender tool-plan execution quality validation", result.stdout)
        self.assertEqual(validation["schema"], "blender_tool_plan_execution_quality_validation_v0")
        self.assertEqual(validation["non_manifold_edge_count"], 0)
        self.assertEqual(validation["material_role_count"], 5)
        self.assertEqual(validation["socket_shadow_panel_count"], 2)
        self.assertFalse(validation["generated_outputs_in_repo"])

    def test_accepts_window_frame_quality_execution_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            json_report = Path(tmp) / "quality_validation.json"
            write_report(report_path, valid_window_frame_report())
            result = run_validator(report_path, json_report)
            validation = json.loads(json_report.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS Blender tool-plan execution quality validation", result.stdout)
        self.assertEqual(validation["asset_id"], "gothic_stone_window_frame_tool_plan_v0")
        self.assertEqual(validation["material_role_count"], 1)
        self.assertEqual(validation["socket_shadow_panel_count"], 0)

    def test_accepts_fence_post_quality_execution_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            json_report = Path(tmp) / "quality_validation.json"
            write_report(report_path, valid_fence_post_report())
            result = run_validator(report_path, json_report)
            validation = json.loads(json_report.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS Blender tool-plan execution quality validation", result.stdout)
        self.assertEqual(validation["asset_id"], "gothic_stone_fence_post_tool_plan_v0")
        self.assertEqual(validation["material_role_count"], 5)
        self.assertEqual(validation["socket_shadow_panel_count"], 2)

    def test_accepts_door_frame_quality_execution_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            json_report = Path(tmp) / "quality_validation.json"
            write_report(report_path, valid_door_frame_report())
            result = run_validator(report_path, json_report)
            validation = json.loads(json_report.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS Blender tool-plan execution quality validation", result.stdout)
        self.assertEqual(validation["asset_id"], "gothic_stone_door_frame_tool_plan_v0")
        self.assertEqual(validation["material_role_count"], 1)
        self.assertEqual(validation["socket_shadow_panel_count"], 0)

    def test_rejects_nonzero_non_manifold_count(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            report = valid_report()
            report["validation"]["non_manifold_edge_count"] = 1
            report["topology_cleanup"]["non_manifold_edge_count_after"] = 1
            write_report(report_path, report)
            result = run_validator(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("validation.non_manifold_edge_count must be <= 0", result.stderr)

    def test_rejects_missing_socket_shadow_material_region(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            report = valid_report()
            del report["material_regions"]["face_counts_by_role"]["socket_shadow"]
            write_report(report_path, report)
            result = run_validator(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must include `socket_shadow`", result.stderr)

    def test_rejects_adapter_boundary_violation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            report = valid_report()
            report["rules"]["reads_source_intent_recipe"] = True
            write_report(report_path, report)
            result = run_validator(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rules.reads_source_intent_recipe must be false", result.stderr)

    def test_rejects_generated_output_inside_repo(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "tool_plan_execution_report.json"
            report = valid_report()
            report["render_path"] = str(ROOT / "bad_preview.png")
            write_report(report_path, report)
            result = run_validator(report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("render_path must not point inside the repo", result.stderr)


if __name__ == "__main__":
    unittest.main()
