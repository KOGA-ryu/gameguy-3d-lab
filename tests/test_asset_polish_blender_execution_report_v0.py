#!/usr/bin/env python3
"""Tests for asset polish Blender execution report validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_asset_polish_blender_execution_report_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def valid_report() -> dict[str, Any]:
    return {
        "schema": "asset_polish_blender_execution_report_v0",
        "adapter": "scripts/execute_asset_polish_blender_adapter_v0.py",
        "source_plan": "/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json",
        "source_asset": "/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json",
        "plan_schema": "asset_polish_tool_plan_v0",
        "asset_schema": "gameguy_asset_v0",
        "plan_id": "blocky_fence_post_asset_polish_plan_v0_compiled",
        "source_recipe_id": "blocky_fence_post_polish_recipe_v0",
        "source_asset_id": "blocky_fence_post_v0",
        "asset_id": "blocky_fence_post_v0",
        "step_count": 10,
        "supported_step_count": 7,
        "future_step_count": 3,
        "executed_step_count": 7,
        "skipped_future_step_count": 3,
        "unique_tool_count": 5,
        "unique_tools": ["extrude_faces", "inset_faces", "material_assign_by_part", "modifier_bevel", "modifier_weighted_normal"],
        "mesh_part_count": 7,
        "generated_outputs_created": True,
        "blend_path": "/tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend",
        "object_count": 10,
        "mesh_object_count": 7,
        "part_object_count": 7,
        "validation_warnings": [],
        "executed_steps": [
            {"step_id": "inset_plinth_fielded_panels", "operation": "inset_faces", "tool_id": "inset_faces", "target": "newel.plinth.fielded_panel_faces"},
            {"step_id": "inset_shaft_side_panels", "operation": "inset_faces", "tool_id": "inset_faces", "target": "newel.shaft.side_panels"},
            {"step_id": "raise_shaft_panel_beads", "operation": "extrude_along_normals", "tool_id": "extrude_faces", "target": "newel.shaft.panel_lips"},
            {"step_id": "chamfer_plinth_outer_arrises", "operation": "chamfer_edges", "tool_id": "modifier_bevel", "target": "newel.plinth.outer_arrises"},
            {"step_id": "bevel_all_visible_hard_edges", "operation": "bevel_edges", "tool_id": "modifier_bevel", "target": "newel.all.hard_edges"},
            {"step_id": "assign_gothic_stone_material_slots", "operation": "material_assign", "tool_id": "material_assign_by_part", "target": "newel.all.visible_parts"},
            {"step_id": "apply_weighted_normals", "operation": "weighted_normals", "tool_id": "modifier_weighted_normal", "target": "newel.all.visible_parts"},
        ],
        "skipped_steps": [
            {"step_id": f"future_{index}", "operation": "future", "tool_id": "future_tool", "reason": "recognized_future_operation_not_in_first_execution_slice"}
            for index in range(3)
        ],
        "inset_applications": [
            {
                "step_id": "inset_plinth_fielded_panels",
                "tool_id": "inset_faces",
                "operation": "inset_faces",
                "target_objects": ["square_foot"],
                "requested_faces": ["back", "front", "left", "right"],
                "inset_m": 0.035,
                "depth_m": -0.012,
                "panel_face_count": 4,
                "skipped_face_count": 0,
                "added_vertex_count": 16,
                "added_face_count": 16
            },
            {
                "step_id": "inset_shaft_side_panels",
                "tool_id": "inset_faces",
                "operation": "inset_faces",
                "target_objects": ["post_core"],
                "requested_faces": ["back", "front", "left", "right"],
                "inset_m": 0.026,
                "depth_m": -0.01,
                "panel_face_count": 4,
                "skipped_face_count": 0,
                "added_vertex_count": 16,
                "added_face_count": 16
            }
        ],
        "inset_panel_face_count": 8,
        "extrusion_applications": [
            {
                "step_id": "raise_shaft_panel_beads",
                "tool_id": "extrude_faces",
                "operation": "extrude_along_normals",
                "from_target": "newel.shaft.side_panels",
                "target_objects": ["post_core"],
                "depth_m": 0.014,
                "lip_width_m": 0.008,
                "lip_profile": "small_bead",
                "panel_face_count": 4,
                "lip_surface_count": 16,
                "skipped_face_count": 0,
                "added_vertex_count": 128,
                "added_face_count": 80
            }
        ],
        "extruded_lip_surface_count": 16,
        "trim_lip_face_count": 80,
        "modifier_applications": [
            {"step_id": "chamfer_plinth_outer_arrises", "modifier_type": "BEVEL", "target_objects": ["square_foot"], "applied": True},
            {"step_id": "bevel_all_visible_hard_edges", "modifier_type": "BEVEL", "target_objects": ["square_foot"], "applied": True},
            {"step_id": "apply_weighted_normals", "modifier_type": "WEIGHTED_NORMAL", "target_objects": ["square_foot"], "applied": False},
        ],
        "material_assignment": {
            "step_id": "assign_gothic_stone_material_slots",
            "tool_id": "material_assign_by_part",
            "assigned_parts_by_role": {"base": ["square_foot"], "stone": ["post_core"], "trim": ["post_core"]},
            "assigned_faces_by_slot": {"gothic_stone_base": 6, "gothic_stone_body": 6, "gothic_stone_trim_highlight": 80},
            "material_slot_count": 6,
        },
        "weighted_normals": {
            "step_id": "apply_weighted_normals",
            "tool_id": "modifier_weighted_normal",
            "modifier_type": "WEIGHTED_NORMAL",
            "target_objects": ["square_foot"],
            "applied": False,
        },
        "quality_pass": {
            "supported_polish_steps_executed": True,
            "future_steps_skipped": True,
            "source_asset_preserved": True,
            "source_recipe_not_read": True,
            "insets_applied": True,
            "extrusions_applied": True,
            "material_assignment_applied": True,
            "bevels_applied": True,
            "weighted_normals_added": True,
        },
        "rules": {
            "consumes_asset_polish_tool_plan_v0": True,
            "consumes_gameguy_asset_v0": True,
            "reads_source_recipe": False,
            "runs_asset_pump": False,
            "executes_only_supported_deterministic_steps": True,
            "skips_future_operations": True,
            "source_design_logic": False,
            "mutates_source_asset_json": False,
        },
    }


class AssetPolishBlenderExecutionReportTests(unittest.TestCase):
    def test_valid_report_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "execution_report.json"
            report_path.write_text(json.dumps(valid_report(), indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("PASS asset polish Blender execution report validation", result.stdout)

    def test_rejects_unexecuted_supported_steps(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report = valid_report()
            report["executed_step_count"] = 6
            report_path = Path(tmp) / "execution_report.json"
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("executed_step_count must match supported_step_count", result.stderr)

    def test_rejects_repo_output_path(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report = valid_report()
            report["blend_path"] = str(ROOT / "bad.blend")
            report_path = Path(tmp) / "execution_report.json"
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blend_path must not point inside the repo", result.stderr)


if __name__ == "__main__":
    unittest.main()
