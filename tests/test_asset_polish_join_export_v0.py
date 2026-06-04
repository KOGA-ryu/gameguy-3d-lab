#!/usr/bin/env python3
"""Tests for asset polish join/export validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from test_asset_polish_blender_execution_report_v0 import valid_report as valid_polish_execution_report


EXPORTER = ROOT / "scripts" / "export_asset_polish_joined_v0.py"
VALIDATOR = ROOT / "scripts" / "validate_asset_polish_join_export_report_v0.py"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def valid_join_report(tmp_root: Path) -> dict[str, Any]:
    source_slots = ["gothic_stone_base", "gothic_stone_body", "gothic_stone_trim_highlight"]
    prejoin_objects = [
        {"object": "square_foot", "face_count": 106, "uv_loop_count": 400, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "lower_step_band", "face_count": 98, "uv_loop_count": 384, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "post_core", "face_count": 244, "uv_loop_count": 976, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "rail_socket_east", "face_count": 6, "uv_loop_count": 24, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "rail_socket_west", "face_count": 6, "uv_loop_count": 24, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "upper_step_band", "face_count": 26, "uv_loop_count": 96, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "square_cap", "face_count": 26, "uv_loop_count": 96, "active_uv_layer": "polish_uv0", "asset_polish_generated": False},
        {"object": "sweep_cap_lower_outer_ogee_lip", "face_count": 40, "uv_loop_count": 160, "active_uv_layer": "polish_uv0", "asset_polish_generated": True},
    ]
    return {
        "schema": "asset_polish_join_export_report_v0",
        "adapter": "scripts/export_asset_polish_joined_v0.py",
        "source_execution_report": str(tmp_root / "asset_polish_execution_report_v0.json"),
        "source_execution_schema": "asset_polish_blender_execution_report_v0",
        "source_blend": str(tmp_root / "asset_polish_execution_v0.blend"),
        "plan_id": "blocky_fence_post_asset_polish_plan_v0_compiled",
        "source_recipe_id": "blocky_fence_post_polish_recipe_v0",
        "source_asset_id": "blocky_fence_post_v0",
        "asset_id": "blocky_fence_post_v0",
        "generated_outputs_created": True,
        "out_root": str(tmp_root),
        "source_supported_step_count": 10,
        "source_future_step_count": 0,
        "source_executed_step_count": 10,
        "source_skipped_future_step_count": 0,
        "source_mesh_object_count": 8,
        "source_uv_loop_count": 2160,
        "source_material_slot_count": len(source_slots),
        "source_material_slots": source_slots,
        "unique_tools": ["export_gltf", "join_objects", "save_blend_file"],
        "prejoin_mesh_object_count": 8,
        "prejoin_asset_polish_generated_object_count": 1,
        "prejoin_uv_loop_count": 2160,
        "prejoin_objects": prejoin_objects,
        "joined_mesh_object_count": 1,
        "joined_object_name": "blocky_fence_post_polished_joined_v0",
        "joined_blend_path": str(tmp_root / "asset_polish_joined_v0.blend"),
        "glb_path": str(tmp_root / "blocky_fence_post_polished_joined_v0.glb"),
        "glb_file_size_bytes": 4096,
        "joined_object": {
            "object": "blocky_fence_post_polished_joined_v0",
            "vertex_count": 720,
            "face_count": 552,
            "material_slot_count": 3,
            "material_slots": source_slots,
            "material_face_counts": {
                "gothic_stone_base": 120,
                "gothic_stone_body": 300,
                "gothic_stone_trim_highlight": 132,
            },
            "uv_layer_count": 1,
            "active_uv_layer": "polish_uv0",
            "uv_loop_count": 2160,
            "weighted_normal_modifier_count": 1,
        },
        "quality_pass": {
            "source_polish_execution_complete": True,
            "joined_single_mesh_object": True,
            "material_slots_preserved": True,
            "uv_layer_preserved": True,
            "export_written": True,
            "outputs_under_tmp": True,
            "source_recipe_not_read": True,
            "source_asset_json_not_mutated": True,
        },
        "rules": {
            "consumes_asset_polish_blender_execution_report_v0": True,
            "consumes_completed_polish_blend": True,
            "reads_source_recipe": False,
            "runs_asset_pump": False,
            "executes_design_logic": False,
            "joins_existing_polish_meshes_only": True,
            "generated_outputs_stay_under_tmp": True,
        },
    }


class AssetPolishJoinExportTests(unittest.TestCase):
    def test_join_export_report_validator_accepts_complete_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report_path = Path(tmp) / "join_export_report.json"
            report_path.write_text(json.dumps(valid_join_report(Path(tmp)), indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report_path)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("PASS asset polish join/export report validation", result.stdout)

    def test_join_export_report_validator_rejects_repo_output_path(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            report = valid_join_report(Path(tmp))
            report["glb_path"] = str(ROOT / "bad.glb")
            report_path = Path(tmp) / "join_export_report.json"
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("glb_path must not point inside the repo", result.stderr)

    def test_exporter_validate_only_consumes_complete_polish_report(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            source_report = valid_polish_execution_report()
            blend_path = tmp_root / "asset_polish_execution_v0.blend"
            blend_path.write_bytes(b"placeholder blend")
            source_report["blend_path"] = str(blend_path)
            source_report_path = tmp_root / "asset_polish_execution_report_v0.json"
            source_report_path.write_text(json.dumps(source_report, indent=2) + "\n", encoding="utf-8")
            report_path = tmp_root / "join_validate_only.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(EXPORTER),
                    "--execution-report",
                    str(source_report_path),
                    "--blend",
                    str(blend_path),
                    "--validate-only",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_json(report_path)

        self.assertIn("PASS asset polish join/export validation", result.stdout)
        self.assertEqual(report["schema"], "asset_polish_join_export_report_v0")
        self.assertFalse(report["generated_outputs_created"])
        self.assertEqual(report["source_future_step_count"], 0)
        self.assertEqual(report["source_uv_loop_count"], 2160)


if __name__ == "__main__":
    unittest.main()
