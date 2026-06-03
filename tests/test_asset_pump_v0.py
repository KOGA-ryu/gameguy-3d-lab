#!/usr/bin/env python3
"""Tests for the canonical Asset Pump v0 generator."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUMP = ROOT / "scripts" / "asset_pump_v0.py"
ASSET_CONTRACT = ROOT / "contracts" / "gameguy_asset_v0.json"
MEASURED_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"
SECTION_STACK_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "section_stack_assets_v0.json"
BLOCKY_COLUMN_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "blocky_column_assets_v0.json"
BLOCKY_SHAPE_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "blocky_shape_grammar_assets_v0.json"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}


def run_pump(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(PUMP), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_measured_pump(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(PUMP), "--bundle", str(MEASURED_BUNDLE), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_section_stack_pump(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(PUMP), "--bundle", str(SECTION_STACK_BUNDLE), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_blocky_column_pump(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(PUMP), "--bundle", str(BLOCKY_COLUMN_BUNDLE), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_blocky_shape_pump(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(PUMP), "--bundle", str(BLOCKY_SHAPE_BUNDLE), "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_pump_with_bundle(bundle: Path, out_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PUMP), "--bundle", str(bundle), "--out", str(out_root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def assert_finite_vector(testcase: unittest.TestCase, vector: Any, length: int) -> None:
    testcase.assertIsInstance(vector, list)
    testcase.assertEqual(len(vector), length)
    for value in vector:
        testcase.assertIsInstance(value, (int, float))
        testcase.assertFalse(isinstance(value, bool))
        testcase.assertTrue(math.isfinite(float(value)))


class AssetPumpTests(unittest.TestCase):
    def test_asset_contract_matches_generated_shape(self) -> None:
        contract = load_json(ASSET_CONTRACT)
        required_fields = contract["required_fields"]

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_pump(out_root)
            manifest = load_json(out_root / "manifest.json")

            self.assertEqual(manifest["schema"], "gameguy_asset_pump_manifest_v0")
            self.assertEqual(manifest["asset_count"], 14)
            self.assertEqual(
                manifest["rules"],
                {
                    "no_reports": True,
                    "no_receipts": True,
                    "no_blender": True,
                    "no_media": True,
                    "no_mesh_export_files": True,
                    "geometry_dictionary_terms_enforced": True,
                },
            )

            for entry in manifest["assets"]:
                asset = load_json(out_root / entry["path"])
                self.assertEqual(asset["schema"], contract["generated_schema"])
                for field in required_fields:
                    self.assertIn(field, asset)
                self.assertEqual(asset["no_claims"], FALSE_CLAIMS)
                self.assertEqual(asset["mesh"]["coordinate_space"], contract["coordinate_model"]["coordinate_space"])
                self.assertEqual(asset["dimensions_m"], entry["dimensions_m"])
                self.assert_mesh_is_well_formed(asset)

    def test_rectangular_slab_has_expected_geometry_and_connectors(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_pump(out_root)
            slab = load_json(out_root / "assets" / "rectangular_slab_v0.json")

        self.assertEqual(slab["source_operation"], "extrude")
        self.assertEqual(slab["dimensions_m"], {"width": 2.0, "depth": 1.0, "height": 0.18})
        self.assertEqual(slab["child_slots"], ["surface_panel", "edge_trim", "support_anchor"])
        self.assertEqual(len(slab["mesh"]["vertices"]), 8)
        self.assertEqual(len(slab["mesh"]["faces"]), 6)
        self.assertEqual(
            [connector["connector_id"] for connector in slab["connectors"]],
            ["north", "south", "east", "west", "floor", "ceiling"],
        )

    def test_compound_asset_keeps_component_refs_and_merged_mesh(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_pump(out_root)
            railing = load_json(out_root / "assets" / "railing_unit_v0.json")

        self.assertEqual(railing["source_operation"], "compound_asset")
        self.assertEqual(
            railing["components"],
            [
                {"instance_id": "left_post", "asset_ref": "square_post_v0", "translation_m": [-0.75, 0.0, 0.0]},
                {"instance_id": "right_post", "asset_ref": "square_post_v0", "translation_m": [0.75, 0.0, 0.0]},
                {"instance_id": "top_rail", "asset_ref": "rail_bar_v0", "translation_m": [0.0, 0.0, 0.92]},
            ],
        )
        self.assertGreater(len(railing["mesh"]["vertices"]), 8)
        self.assertGreater(len(railing["mesh"]["faces"]), 6)

    def test_measured_bundle_maps_source_fields_to_asset_schema(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_measured_pump(out_root)
            manifest = load_json(out_root / "manifest.json")
            wall = load_json(out_root / "assets" / "measured_rectangular_wall_block_v1.json")

        self.assertEqual(manifest["source_bundle_schema"], "asset_mill_measured_component_bundle_v0")
        self.assertEqual(manifest["asset_schema"], "gameguy_asset_v0")
        self.assertEqual(manifest["asset_count"], 22)
        self.assertEqual(wall["schema"], "gameguy_asset_v0")
        self.assertEqual(wall["source_schema"], "asset_mill_measured_component_bundle_v0")
        self.assertEqual(wall["source_operation"], "proof_primitives")
        self.assertEqual(wall["asset_kind"], "measured_component")
        self.assertEqual(wall["dimensions_m"], {"width": 2.2, "depth": 0.34, "height": 1.6})
        self.assertEqual(wall["bounds_m"], {"min": [-1.1, -0.17, 0.0], "max": [1.1, 0.17, 1.6]})
        self.assertEqual(wall["semantic_tags"], ["blocked", "cover", "line_of_sight_blocker", "collision_proxy"])
        self.assertEqual(
            wall["connectors"][0],
            {
                "connector_id": "floor_anchor",
                "connector_term": "floor",
                "position_m": [0.0, 0.0, 0.0],
                "direction": [0.0, 0.0, -1.0],
                "role": "placement",
            },
        )
        self.assertEqual(
            wall["mesh"]["parts"],
            [
                {
                    "part_id": "wall_block",
                    "source_primitive": "cube",
                    "vertex_range": [0, 7],
                    "face_range": [0, 5],
                    "material_role": "stone",
                }
            ],
        )
        self.assertEqual(len(wall["mesh"]["vertices"]), 8)
        self.assertEqual(len(wall["mesh"]["faces"]), 6)
        self.assertEqual(wall["source_refs"][0]["ref"], "habs_tn181_splayed_support_opening_ratio_v0")
        self.assertEqual(wall["source_terms"]["profiles"], ["rectangle"])
        self.assertEqual(wall["source_terms"]["operators"], ["extrude", "bevel_edges"])
        self.assertEqual(wall["validation_expectations"]["socket_count_min"], 2)
        self.assertFalse(wall["no_claims"]["historical_accuracy"])
        self.assertNotIn("source_script", wall)
        self.assertEqual(
            wall["source_provenance"],
            {
                "source_version": "v1",
                "legacy_source_script": "scripts/compile_asset_mill_measured_components_v1.py",
                "legacy_source_script_removed": True,
            },
        )
        self.assert_mesh_is_well_formed(wall)

    def test_measured_cylinder_and_curve_primitives_generate_parts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_measured_pump(out_root)
            column = load_json(out_root / "assets" / "measured_round_column_v1.json")
            arch = load_json(out_root / "assets" / "measured_pointed_arch_doorway_v1.json")

        self.assertEqual(column["mesh"]["parts"][0]["source_primitive"], "cylinder")
        self.assertEqual(len(column["mesh"]["vertices"]), 64)
        self.assertEqual(len(column["mesh"]["faces"]), 34)
        self.assertEqual([part["source_primitive"] for part in arch["mesh"]["parts"]], ["cube", "cube", "cube", "curve"])
        self.assertGreater(len(arch["mesh"]["vertices"]), 24)
        self.assertGreater(len(arch["mesh"]["faces"]), 18)
        self.assertIn("validation_warnings", arch)
        self.assertEqual(arch["validation_warnings"][0]["mesh_bounds_m"], arch["mesh"]["bounds_m"])

    def test_section_stack_bundle_generates_star_column(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_section_stack_pump(out_root)
            manifest = load_json(out_root / "manifest.json")
            column = load_json(out_root / "assets" / "star_column_22_v0.json")

        self.assertEqual(manifest["source_bundle_schema"], "asset_mill_section_stack_bundle_v0")
        self.assertEqual(manifest["asset_count"], 1)
        self.assertEqual(column["schema"], "gameguy_asset_v0")
        self.assertEqual(column["source_schema"], "asset_mill_section_stack_bundle_v0")
        self.assertEqual(column["source_operation"], "section_stack")
        self.assertEqual(column["asset_kind"], "section_stack")
        self.assertEqual(column["dimensions_m"], {"width": 0.858926, "depth": 0.677072, "height": 2.46})
        self.assertEqual(len(column["mesh"]["vertices"]), 464)
        self.assertEqual(len(column["mesh"]["faces"]), 528)
        self.assertEqual(
            column["mesh"]["parts"],
            [
                {
                    "part_id": "section_stack_body",
                    "source_primitive": "section_stack",
                    "vertex_range": [0, 463],
                    "face_range": [0, 527],
                }
            ],
        )
        self.assertEqual(column["mesh"]["section_stack"]["axis"], "z")
        self.assertEqual(column["mesh"]["section_stack"]["ring_count"], 7)
        self.assertEqual(column["mesh"]["section_stack"]["rings"][0]["ring_id"], "base_foot")
        self.assertEqual(column["mesh"]["section_stack"]["rings"][-1]["vertex_range"], [396, 461])
        self.assertEqual(column["mesh"]["section_stack"]["cap_triangulation"], "center_fan")
        self.assertEqual(column["mesh"]["section_stack"]["bottom_center_vertex"], 462)
        self.assertEqual(column["mesh"]["section_stack"]["top_center_vertex"], 463)
        self.assertEqual(sum(1 for face in column["mesh"]["faces"] if len(face) == 3), 132)
        self.assertEqual(sum(1 for face in column["mesh"]["faces"] if len(face) == 4), 396)
        self.assertEqual(column["source_terms"]["profiles"], ["star_polygon"])
        self.assertEqual(column["source_terms"]["operators"], ["section_stack", "loft_sections"])
        self.assert_mesh_is_well_formed(column)

    def test_blocky_column_bundle_generates_simple_part_ribbed_column(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_blocky_column_pump(out_root)
            manifest = load_json(out_root / "manifest.json")
            column = load_json(out_root / "assets" / "blocky_ribbed_column_v0.json")

        self.assertEqual(manifest["source_bundle_schema"], "asset_mill_blocky_column_bundle_v0")
        self.assertEqual(manifest["asset_count"], 1)
        self.assertEqual(column["schema"], "gameguy_asset_v0")
        self.assertEqual(column["source_schema"], "asset_mill_blocky_column_bundle_v0")
        self.assertEqual(column["source_operation"], "blocky_column")
        self.assertEqual(column["asset_kind"], "blocky_compound_column")
        self.assertEqual(column["dimensions_m"], {"width": 0.92, "depth": 0.92, "height": 2.46})
        self.assertEqual(len(column["mesh"]["vertices"]), 264)
        self.assertEqual(len(column["mesh"]["faces"]), 186)
        self.assertEqual(len(column["mesh"]["parts"]), 27)
        self.assertEqual(column["mesh"]["parts"][0]["part_id"], "square_plinth")
        self.assertEqual(column["mesh"]["parts"][0]["source_primitive"], "box")
        self.assertEqual(column["mesh"]["parts"][3]["part_id"], "vertical_rib_00")
        self.assertEqual(column["mesh"]["parts"][3]["source_primitive"], "oriented_box")
        self.assertEqual(column["mesh"]["parts"][-1]["part_id"], "square_abacus")
        self.assertEqual(column["mesh"]["blocky_column"]["axis"], "z")
        self.assertEqual(column["mesh"]["blocky_column"]["assembly"], "simple_parts")
        self.assertEqual(column["mesh"]["blocky_column"]["part_count"], 27)
        self.assertEqual(column["mesh"]["blocky_column"]["rib_count"], 22)
        self.assertEqual(column["mesh"]["blocky_column"]["rib_depth_m"], 0.04)
        self.assertEqual(column["mesh"]["blocky_column"]["rib_center_radius_m"], 0.32)
        self.assertIn(
            {"seam_id": "lower_collar_to_ribs", "overlap_z": [0.36, 0.4]},
            column["mesh"]["blocky_column"]["covered_seams"],
        )
        self.assertEqual(column["source_terms"]["profiles"], ["square", "circle", "rectangle"])
        self.assertEqual(column["source_terms"]["operators"], ["blocky_column", "compound_asset", "extrude", "array_radial"])
        self.assertEqual(column["validation_expectations"]["rib_count"], 22)
        self.assertEqual(column["validation_expectations"]["rib_depth_m"], 0.04)
        self.assert_mesh_is_well_formed(column)

    def test_blocky_shape_grammar_bundle_generates_column_and_fence_post(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pump"
            run_blocky_shape_pump(out_root)
            manifest = load_json(out_root / "manifest.json")
            column = load_json(out_root / "assets" / "grammar_ribbed_column_v0.json")
            post = load_json(out_root / "assets" / "blocky_fence_post_v0.json")

        self.assertEqual(manifest["source_bundle_schema"], "asset_mill_blocky_shape_grammar_bundle_v0")
        self.assertEqual(manifest["asset_count"], 2)

        self.assertEqual(column["schema"], "gameguy_asset_v0")
        self.assertEqual(column["source_schema"], "asset_mill_blocky_shape_grammar_bundle_v0")
        self.assertEqual(column["source_operation"], "blocky_shape")
        self.assertEqual(column["asset_kind"], "blocky_shape_column")
        self.assertEqual(column["dimensions_m"], {"width": 0.92, "depth": 0.92, "height": 2.46})
        self.assertEqual(len(column["mesh"]["vertices"]), 264)
        self.assertEqual(len(column["mesh"]["faces"]), 186)
        self.assertEqual(len(column["mesh"]["parts"]), 27)
        self.assertEqual(column["mesh"]["parts"][3]["part_id"], "vertical_rib_00")
        self.assertEqual(column["mesh"]["blocky_shape"]["grammar"], "blocky_shape_v0")
        self.assertEqual(column["mesh"]["blocky_shape"]["source_part_count"], 6)
        self.assertEqual(column["mesh"]["blocky_shape"]["expanded_part_count"], 27)
        self.assertEqual(column["mesh"]["blocky_shape"]["part_types"], ["box", "cylinder", "cylinder", "radial_box_array", "cylinder", "box"])
        self.assertEqual(column["mesh"]["blocky_shape"]["radial_arrays"][0]["count"], 22)
        self.assertEqual(column["mesh"]["blocky_shape"]["radial_arrays"][0]["rib_depth_m"], 0.04)
        self.assertEqual(column["source_terms"]["operators"], ["blocky_shape", "compound_asset", "extrude", "array_radial"])
        self.assert_mesh_is_well_formed(column)

        self.assertEqual(post["schema"], "gameguy_asset_v0")
        self.assertEqual(post["source_schema"], "asset_mill_blocky_shape_grammar_bundle_v0")
        self.assertEqual(post["source_operation"], "blocky_shape")
        self.assertEqual(post["asset_kind"], "blocky_shape_post")
        self.assertEqual(post["dimensions_m"], {"width": 0.5, "depth": 0.5, "height": 1.24})
        self.assertEqual(len(post["mesh"]["vertices"]), 56)
        self.assertEqual(len(post["mesh"]["faces"]), 42)
        self.assertEqual(len(post["mesh"]["parts"]), 7)
        self.assertEqual([part["part_id"] for part in post["mesh"]["parts"][3:5]], ["rail_socket_east", "rail_socket_west"])
        self.assertEqual(post["mesh"]["blocky_shape"]["source_part_count"], 7)
        self.assertEqual(post["mesh"]["blocky_shape"]["expanded_part_count"], 7)
        self.assertEqual(post["mesh"]["blocky_shape"]["source_parts"][3]["center_xy"], [0.18, 0.0])
        self.assertEqual(post["mesh"]["blocky_shape"]["source_parts"][4]["center_xy"], [-0.18, 0.0])
        self.assertEqual(post["source_terms"]["profiles"], ["square", "rectangle"])
        self.assertEqual(post["source_terms"]["operators"], ["blocky_shape", "compound_asset", "extrude"])
        self.assertEqual(post["validation_expectations"]["side_socket_count"], 2)
        self.assert_mesh_is_well_formed(post)

    def test_output_is_deterministic_across_runs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_a = Path(tmp) / "pump_a"
            out_b = Path(tmp) / "pump_b"
            run_pump(out_a)
            run_pump(out_b)

            files_a = sorted(path.relative_to(out_a) for path in out_a.rglob("*.json"))
            files_b = sorted(path.relative_to(out_b) for path in out_b.rglob("*.json"))
            self.assertEqual(files_a, files_b)
            for rel_path in files_a:
                self.assertEqual(
                    (out_a / rel_path).read_text(encoding="utf-8"),
                    (out_b / rel_path).read_text(encoding="utf-8"),
                    msg=f"non-deterministic output for {rel_path}",
                )

    def test_unknown_dictionary_terms_fail_before_output(self) -> None:
        source_bundle = load_json(ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json")
        source_bundle["assets"][0]["semantic_tags"] = ["walkable", "made_up_semantic"]

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown geometry dictionary semantic tag `made_up_semantic`", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_dictionary_valid_but_unsupported_pump_connector_fails(self) -> None:
        source_bundle = load_json(ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json")
        source_bundle["assets"][0]["connectors"] = ["socket"]

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported pump connector: socket", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_measured_unknown_semantic_role_fails_before_output(self) -> None:
        source_bundle = load_json(MEASURED_BUNDLE)
        source_bundle["assets"][0]["semantic_roles"] = ["blocked", "made_up_semantic"]

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_measured_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown geometry dictionary term `made_up_semantic`", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_section_stack_mismatched_ring_vertex_count_fails_before_output(self) -> None:
        source_bundle = load_json(SECTION_STACK_BUNDLE)
        source_bundle["assets"][0]["section_stack"]["rings"][1]["profile"]["params"]["points"] = 21

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_section_stack_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rings must have matching vertex counts", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_star_polygon_rejects_inner_radius_outside_outer_radius(self) -> None:
        source_bundle = load_json(SECTION_STACK_BUNDLE)
        source_bundle["assets"][0]["section_stack"]["rings"][0]["profile"]["params"]["inner_radius_x"] = 0.5

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_star_profile_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inner_radius_x must be less than outer_radius_x", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_blocky_column_rejects_non_positive_rib_depth_before_output(self) -> None:
        source_bundle = load_json(BLOCKY_COLUMN_BUNDLE)
        source_bundle["assets"][0]["blocky_column"]["ribs"]["rib_depth_m"] = 0.0

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_blocky_column_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blocky_column.ribs.rib_depth_m must be positive", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_blocky_shape_rejects_unknown_part_type_before_output(self) -> None:
        source_bundle = load_json(BLOCKY_SHAPE_BUNDLE)
        source_bundle["assets"][1]["blocky_shape"]["parts"][0]["part_type"] = "spline_magic"

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_blocky_shape_bundle.json"
            out_root = Path(tmp) / "pump"
            bundle_path.write_text(json.dumps(source_bundle, indent=2) + "\n", encoding="utf-8")
            result = run_pump_with_bundle(bundle_path, out_root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported blocky_shape part_type `spline_magic`", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())

    def assert_mesh_is_well_formed(self, asset: dict[str, Any]) -> None:
        vertices = asset["mesh"]["vertices"]
        faces = asset["mesh"]["faces"]
        self.assertIsInstance(vertices, list)
        self.assertIsInstance(faces, list)
        self.assertGreaterEqual(len(vertices), 3)
        self.assertGreaterEqual(len(faces), 1)

        for vertex in vertices:
            assert_finite_vector(self, vertex, 3)

        for face in faces:
            self.assertIsInstance(face, list)
            self.assertGreaterEqual(len(face), 3)
            for index in face:
                self.assertIsInstance(index, int)
                self.assertGreaterEqual(index, 0)
                self.assertLess(index, len(vertices))

        for axis in ("width", "depth", "height"):
            self.assertIn(axis, asset["dimensions_m"])
            self.assertGreaterEqual(asset["dimensions_m"][axis], 0.0)

        for connector in asset["connectors"]:
            self.assertIn("connector_id", connector)
            assert_finite_vector(self, connector["position_m"], 3)
            assert_finite_vector(self, connector["direction"], 3)

        self.assertIn("source_schema", asset)
        self.assertIn("source_refs", asset)
        self.assertIn("source_terms", asset)
        self.assertIn("validation_expectations", asset)


if __name__ == "__main__":
    unittest.main()
