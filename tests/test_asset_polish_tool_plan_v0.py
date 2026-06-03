#!/usr/bin/env python3
"""Tests for asset polish tool-plan compilation and validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_asset_polish_tool_plan_v0.py"
VALIDATOR = ROOT / "scripts" / "validate_asset_polish_tool_plan_v0.py"
RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "polish_recipes" / "asset_polish_tool_plan_recipes_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def compile_to(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(COMPILER), "--clean", "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class AssetPolishToolPlanTests(unittest.TestCase):
    def test_validate_only_accepts_default_recipe(self) -> None:
        result = subprocess.run(
            [sys.executable, str(COMPILER), "--validate-only"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("PASS asset polish tool-plan compile", result.stdout)
        self.assertIn("plans=1", result.stdout)
        self.assertIn("steps=10", result.stdout)
        self.assertIn("targets=8", result.stdout)

    def test_default_recipe_compiles_to_named_polish_targets(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "polish"
            compile_to(out_root)
            validation = subprocess.run(
                [sys.executable, str(VALIDATOR), "--manifest", str(out_root / "manifest.json")],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = load_json(out_root / "manifest.json")
            plan = load_json(out_root / manifest["plans"][0]["path"])

        self.assertIn("PASS asset polish tool-plan validation", validation.stdout)
        self.assertEqual(manifest["schema"], "asset_polish_tool_plan_manifest_v0")
        self.assertEqual(manifest["plan_count"], 1)
        self.assertEqual(plan["schema"], "asset_polish_tool_plan_v0")
        self.assertEqual(plan["source_asset"]["asset_id"], "blocky_fence_post_v0")
        self.assertEqual(plan["asset_family"], "newel_post")
        self.assertEqual(plan["summary"]["target_count"], 8)
        self.assertEqual(plan["summary"]["step_count"], 10)
        self.assertEqual(plan["summary"]["non_deterministic_step_count"], 0)
        self.assertIn("asset_polish_tool_plan", plan["geometry_terms_used"])
        self.assertIn("fielded_panel", plan["terminology_terms"])
        self.assertIn("ogee", plan["terminology_terms"])
        self.assertIn("weighted_normals", plan["terminology_terms"])

        targets = {target["target_id"]: target for target in plan["targets"]}
        self.assertIn("newel.plinth.fielded_panel_faces", targets)
        self.assertEqual(targets["newel.plinth.fielded_panel_faces"]["selector"]["faces"], ["front", "back", "left", "right"])
        self.assertIn("newel.cap.lower_outer_ogee_lip", targets)
        self.assertEqual(targets["newel.shaft.panel_lips"]["selector"]["from_target"], "newel.shaft.side_panels")

        steps = {step["step_id"]: step for step in plan["steps"]}
        self.assertEqual(
            [step["step_id"] for step in plan["steps"]],
            [
                "inset_plinth_fielded_panels",
                "inset_shaft_side_panels",
                "raise_shaft_panel_beads",
                "define_east_west_socket_reveals",
                "sweep_cap_lower_outer_ogee_lip",
                "chamfer_plinth_outer_arrises",
                "bevel_all_visible_hard_edges",
                "assign_gothic_stone_material_slots",
                "apply_weighted_normals",
                "smart_uv_unwrap_visible_parts",
            ],
        )
        self.assertEqual(steps["inset_plinth_fielded_panels"]["operation"], "inset_faces")
        self.assertEqual(steps["sweep_cap_lower_outer_ogee_lip"]["tool_id"], "curve_bevel_profile")
        self.assertEqual(steps["apply_weighted_normals"]["tool_id"], "modifier_weighted_normal")
        self.assertEqual(steps["smart_uv_unwrap_visible_parts"]["tool_id"], "uv_smart_project")
        self.assertFalse(plan["rules"]["compiler_executes_blender"])
        self.assertFalse(plan["rules"]["writes_generated_media_or_mesh"])

    def test_validator_rejects_unknown_step_target(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "polish"
            compile_to(out_root)
            manifest = load_json(out_root / "manifest.json")
            plan_path = out_root / manifest["plans"][0]["path"]
            plan = load_json(plan_path)
            plan["steps"][0]["target"] = "missing.target"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--manifest", str(out_root / "manifest.json")],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown target", result.stderr)

    def test_validator_rejects_unknown_selector_from_target(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "polish"
            compile_to(out_root)
            manifest = load_json(out_root / "manifest.json")
            plan_path = out_root / manifest["plans"][0]["path"]
            plan = load_json(plan_path)
            plan["targets"][3]["selector"]["from_target"] = "missing.side_panels"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--manifest", str(out_root / "manifest.json")],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("selector.from_target references unknown target", result.stderr)

    def test_recipe_references_terminology_doc(self) -> None:
        recipe = load_json(RECIPE)

        self.assertEqual(recipe["terminology_reference"], "docs/asset_pump/asset_polish_terminology_reference_v0.md")
        self.assertTrue((ROOT / recipe["terminology_reference"]).exists())
        self.assertEqual(recipe["plans"][0]["validation_expectations"]["target_count"], 8)
        self.assertEqual(recipe["plans"][0]["validation_expectations"]["step_count"], 10)


if __name__ == "__main__":
    unittest.main()
