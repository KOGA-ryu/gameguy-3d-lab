#!/usr/bin/env python3
"""Tests for sacred construction graph compilation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_sacred_graph_v0.py"
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "sacred_graph_recipes_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_compiler(out_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COMPILER), "--clean", "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class SacredGraphCompilerTests(unittest.TestCase):
    def test_default_22_division_graph_compiles_named_selections(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "sacred_graph"
            result = run_compiler(out_root)
            manifest = load_json(out_root / "manifest.json")
            graph = load_json(out_root / "graphs" / "sacred_22_star_construction_graph_v0.json")
            svg = (out_root / "svg" / "sacred_22_star_construction_graph_v0.svg").read_text(encoding="utf-8")

        self.assertIn("compiled sacred graphs=1 points=89 edges=220", result.stdout)
        self.assertEqual(manifest["schema"], "gameguy_sacred_graph_manifest_v0")
        self.assertEqual(manifest["graph_count"], 1)
        self.assertEqual(manifest["graphs"][0]["point_count"], 89)
        self.assertEqual(manifest["graphs"][0]["edge_count"], 220)
        self.assertEqual(manifest["graphs"][0]["selection_count"], 4)
        self.assertEqual(graph["schema"], "gameguy_sacred_graph_v0")
        self.assertEqual(graph["graph_id"], "sacred_22_star_construction_graph_v0")
        self.assertEqual(graph["geometry_operation"], "sacred_graph")
        self.assertEqual(graph["divisions"], 22)
        self.assertEqual(graph["summary"]["point_count"], 89)
        self.assertEqual(graph["summary"]["edge_count"], 220)
        self.assertEqual(graph["summary"]["profile_bounds_m"]["column_star_outline"]["min"], [-0.429463, -0.338536])
        self.assertEqual(graph["summary"]["profile_bounds_m"]["column_star_outline"]["max"], [0.429463, 0.338536])

        selections = {selection["selection_id"]: selection for selection in graph["selections"]}
        self.assertEqual(selections["center_boss_node"]["point_ids"], ["center"])
        self.assertEqual(len(selections["primary_radial_ribs"]["edge_ids"]), 88)
        self.assertEqual(len(selections["outer_star_step_5_trace"]["edge_ids"]), 22)
        column_profile = selections["column_star_outline"]["profile"]
        self.assertIsInstance(column_profile, dict)
        self.assertEqual(column_profile["vertex_count"], 66)
        self.assertEqual(
            column_profile["vertices"][:3],
            [
                [0.429463, -0.016986],
                [0.429463, 0.016986],
                [0.364254, 0.039421],
            ],
        )
        self.assertIn('<polygon class="outline"', svg)
        self.assertIn("sacred_22_star_construction_graph_v0", svg)

    def test_validate_only_writes_no_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "sacred_graph"
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--validate-only", "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("compiled sacred graphs=1 out=<validate-only>", result.stdout)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_output_is_deterministic_across_runs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_a = Path(tmp) / "a"
            out_b = Path(tmp) / "b"
            run_compiler(out_a)
            run_compiler(out_b)
            files_a = sorted(path.relative_to(out_a) for path in out_a.rglob("*") if path.is_file())
            files_b = sorted(path.relative_to(out_b) for path in out_b.rglob("*") if path.is_file())

            self.assertEqual(files_a, files_b)
            for rel_path in files_a:
                self.assertEqual(
                    (out_a / rel_path).read_text(encoding="utf-8"),
                    (out_b / rel_path).read_text(encoding="utf-8"),
                    msg=f"non-deterministic sacred graph output for {rel_path}",
                )

    def test_non_coprime_star_step_fails_before_output(self) -> None:
        source = load_json(DEFAULT_BUNDLE)
        source["graphs"][0]["star_connections"][0]["step"] = 2
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bundle_path = Path(tmp) / "bad_sacred_graph_bundle.json"
            out_root = Path(tmp) / "sacred_graph"
            bundle_path.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--bundle", str(bundle_path), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("step must be coprime with divisions", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
