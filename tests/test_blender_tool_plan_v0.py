#!/usr/bin/env python3
"""Tests for Blender tool dictionary and tool-plan compilation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_blender_tool_plan_v0.py"
DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "tool_plan_recipes" / "architectural_tool_plan_recipes_v0.json"
CONTRACT = ROOT / "contracts" / "gameguy_tool_plan_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_compiler(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(COMPILER), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def plan_by_asset(out_root: Path, asset_id: str) -> dict[str, Any]:
    manifest = load_json(out_root / "manifest.json")
    for row in manifest["plans"]:
        plan = load_json(out_root / row["path"])
        if plan["asset_id"] == asset_id:
            return plan
    raise AssertionError(f"missing plan for {asset_id}")


class BlenderToolPlanTests(unittest.TestCase):
    def test_tool_dictionary_is_large_and_stage_classified(self) -> None:
        dictionary = load_json(DICTIONARY)
        tool_ids = [tool["tool_id"] for tool in dictionary["tools"]]
        stages = dictionary["stages"]
        lanes = dictionary["execution_lanes"]

        self.assertEqual(dictionary["schema"], "blender_tool_dictionary_v0")
        self.assertEqual(dictionary["tool_count"], len(dictionary["tools"]))
        self.assertGreaterEqual(dictionary["tool_count"], 90)
        self.assertEqual(len(tool_ids), len(set(tool_ids)))
        self.assertIn("base_form", stages)
        self.assertIn("validation_export", stages)
        self.assertIn("blender_adapter_action", lanes)
        self.assertIn("future_geometry_nodes_target", lanes)

        by_id = {tool["tool_id"]: tool for tool in dictionary["tools"]}
        for expected in (
            "primitive_cube_add",
            "modifier_boolean",
            "modifier_bevel",
            "object_duplicate_radial",
            "uv_smart_project",
            "material_principled_shader",
            "render_workbench_preview",
            "export_gltf",
        ):
            self.assertIn(expected, by_id)
            self.assertIn(by_id[expected]["stage"], stages)
            self.assertIn(by_id[expected]["execution_lane"], lanes)

    def test_contract_matches_compiled_plan_shape(self) -> None:
        contract = load_json(CONTRACT)
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "plans"
            run_compiler(out_root)
            manifest = load_json(out_root / "manifest.json")
            plan_path = out_root / manifest["plans"][0]["path"]
            plan = load_json(plan_path)

        self.assertEqual(contract["generated_schema"], "gameguy_tool_plan_v0")
        self.assertEqual(plan["schema"], contract["generated_schema"])
        for field in contract["required_fields"]:
            self.assertIn(field, plan)
        for step in plan["steps"]:
            for field in contract["step_required_fields"]:
                self.assertIn(field, step)

    def test_banister_post_recipe_compiles_to_staged_tool_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "plans"
            run_compiler(out_root)
            manifest = load_json(out_root / "manifest.json")
            plan = plan_by_asset(out_root, "gothic_stone_banister_post_tool_plan_v0")

        self.assertEqual(manifest["schema"], "gameguy_tool_plan_manifest_v0")
        self.assertEqual(manifest["plan_count"], 2)
        self.assertEqual(manifest["plans"][0]["step_count"], 32)
        self.assertEqual(manifest["plans"][0]["unique_tool_count"], 24)
        self.assertEqual(plan["asset_family"], "banister_post")
        self.assertEqual(plan["style"], "gothic_stone")
        self.assertEqual(plan["summary"]["covered_stages"], plan["stage_order"])
        self.assertEqual(plan["summary"]["non_deterministic_step_count"], 0)
        self.assertEqual(plan["rules"]["compiler_executes_blender"], False)
        self.assertEqual(plan["rules"]["writes_generated_media_or_mesh"], False)

        stage_indexes = {stage: index for index, stage in enumerate(plan["stage_order"])}
        observed = [stage_indexes[step["stage"]] for step in plan["steps"]]
        self.assertEqual(observed, sorted(observed))
        self.assertEqual(plan["steps"][0]["step_id"], "create_base_foot")
        self.assertEqual(plan["steps"][0]["stage"], "base_form")
        self.assertEqual(plan["steps"][9]["step_id"], "duplicate_ribs_radially")
        self.assertEqual(plan["steps"][9]["tool_id"], "object_duplicate_radial")
        self.assertEqual(plan["steps"][-1]["tool_id"], "export_gltf")
        self.assertIn("uv_smart_project", plan["summary"]["unique_tools"])
        self.assertIn("material_principled_shader", plan["summary"]["unique_tools"])
        self.assertIn("create_collision_proxy", plan["summary"]["unique_tools"])

        by_step = {step["step_id"]: step for step in plan["steps"]}
        socket_boolean = by_step["boolean_cut_rail_sockets"]["params"]
        self.assertEqual(socket_boolean["targets"], ["post_core"])
        self.assertEqual(socket_boolean["solver"], "EXACT")
        self.assertTrue(socket_boolean["cleanup_cutters"])
        self.assertTrue(socket_boolean["socket_shadow_panels"]["enabled"])
        self.assertEqual(socket_boolean["socket_shadow_panels"]["material_role"], "socket_shadow")
        self.assertIn("socket_shadows", by_step["join_visible_post_parts"]["params"]["objects"])
        material_map = by_step["assign_material_regions"]["params"]["material_map"]
        self.assertEqual(material_map["socket_shadow"], "gothic_stone_shadow")
        self.assertEqual(by_step["weld_close_vertices"]["params"]["merge_distance_m"], 0.0)
        topology_validation = by_step["validate_topology_non_manifold"]["params"]
        self.assertEqual(topology_validation["cleanup_merge_distance_m"], 0.0)
        self.assertEqual(topology_validation["cleanup_fill_hole_sides"], 0)

    def test_window_frame_recipe_compiles_to_different_tool_sequence(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "plans"
            run_compiler(out_root)
            plan = plan_by_asset(out_root, "gothic_stone_window_frame_tool_plan_v0")

        self.assertEqual(plan["asset_family"], "window_frame")
        self.assertEqual(plan["style"], "gothic_stone")
        self.assertEqual(plan["summary"]["step_count"], 25)
        self.assertEqual(plan["summary"]["unique_tool_count"], 22)
        self.assertEqual(plan["summary"]["covered_stages"], plan["stage_order"])
        self.assertEqual(plan["summary"]["non_deterministic_step_count"], 0)
        self.assertNotIn("modifier_boolean", plan["summary"]["unique_tools"])
        self.assertNotIn("object_duplicate_radial", plan["summary"]["unique_tools"])
        self.assertIn("join_objects", plan["summary"]["unique_tools"])

        by_step = {step["step_id"]: step for step in plan["steps"]}
        self.assertEqual(plan["steps"][0]["step_id"], "create_window_left_jamb")
        self.assertEqual(by_step["create_window_left_jamb"]["params"]["size_m"], [0.14, 0.16, 0.84])
        self.assertEqual(by_step["create_window_sill"]["params"]["size_m"], [0.92, 0.16, 0.18])
        self.assertEqual(by_step["create_window_header"]["params"]["size_m"], [0.92, 0.16, 0.16])
        self.assertEqual(
            by_step["join_window_frame_blocks"]["params"]["objects"],
            ["window_left_jamb", "window_right_jamb", "window_sill", "window_header"],
        )
        self.assertEqual(by_step["join_window_frame_blocks"]["params"]["opening_m"], [0.64, 0.84])

    def test_validate_only_writes_no_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "plans"
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--validate-only", "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("compiled tool plans=2 steps=57 tools=97 out=<validate-only>", result.stdout)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_unknown_feature_fails_before_output(self) -> None:
        source = load_json(DEFAULT_RECIPE)
        source["assets"][0]["features"].append("floating_magic")

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            recipe_path = Path(tmp) / "bad_recipe.json"
            out_root = Path(tmp) / "plans"
            recipe_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--recipe", str(recipe_path), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown feature `floating_magic`", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_window_frame_invalid_member_dimensions_fail_before_output(self) -> None:
        source = load_json(DEFAULT_RECIPE)
        source["assets"][1]["style_parameters"]["side_member_width_m"] = 0.5

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            recipe_path = Path(tmp) / "bad_recipe.json"
            out_root = Path(tmp) / "plans"
            recipe_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--recipe", str(recipe_path), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("side members must leave a center opening", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_tool_count_mismatch_fails_before_output(self) -> None:
        dictionary = load_json(DICTIONARY)
        dictionary["tool_count"] += 1

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            dictionary_path = Path(tmp) / "bad_dictionary.json"
            out_root = Path(tmp) / "plans"
            dictionary_path.write_text(json.dumps(dictionary, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--dictionary", str(dictionary_path), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tool_count must match tools length", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
