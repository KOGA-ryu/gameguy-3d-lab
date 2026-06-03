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


if __name__ == "__main__":
    unittest.main()
