#!/usr/bin/env python3
"""Tests for construction cell selection compilation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GRAPH_COMPILER = ROOT / "scripts" / "compile_sacred_graph_v0.py"
CELL_COMPILER = ROOT / "scripts" / "compile_construction_cell_selection_v0.py"
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "construction_cell_selection_recipes_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_graph_compiler(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(GRAPH_COMPILER), "--clean", "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_cell_compiler(graph_out: Path, cell_out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CELL_COMPILER),
            "--graph-manifest",
            str(graph_out / "manifest.json"),
            "--clean",
            "--out",
            str(cell_out),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class ConstructionCellSelectionCompilerTests(unittest.TestCase):
    def test_default_cell_selection_compiles_ring_band_cells(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            graph_out = Path(tmp) / "graph"
            cell_out = Path(tmp) / "cells"
            run_graph_compiler(graph_out)
            result = run_cell_compiler(graph_out, cell_out)
            manifest = load_json(cell_out / "manifest.json")
            cell_set = load_json(cell_out / "cell_sets" / "sacred_22_star_radial_cell_selection_v0.json")
            svg = (cell_out / "svg" / "sacred_22_star_radial_cell_selection_v0.svg").read_text(encoding="utf-8")

        self.assertIn("compiled construction cell selections=1 cells=66 selected=26", result.stdout)
        self.assertEqual(manifest["schema"], "gameguy_construction_cell_selection_manifest_v0")
        self.assertEqual(manifest["selection_set_count"], 1)
        self.assertEqual(manifest["selection_sets"][0]["cell_count"], 66)
        self.assertEqual(manifest["selection_sets"][0]["unique_selected_cell_count"], 26)
        self.assertEqual(cell_set["schema"], "gameguy_construction_cell_selection_v0")
        self.assertEqual(cell_set["source_graph_id"], "sacred_22_star_construction_graph_v0")
        self.assertEqual(cell_set["summary"]["band_count"], 3)
        self.assertEqual(cell_set["summary"]["cell_count"], 66)
        self.assertEqual(cell_set["summary"]["selection_count"], 3)
        self.assertEqual(cell_set["summary"]["selected_cell_reference_count"], 26)
        self.assertEqual(cell_set["summary"]["unique_selected_cell_count"], 26)

        bands = {band["band_id"]: band for band in cell_set["bands"]}
        self.assertEqual(sorted(bands), ["boss_to_inner_cell", "inner_cell_to_shaft_valley", "shaft_valley_to_outer_tip"])
        self.assertEqual(bands["boss_to_inner_cell"]["cell_count"], 22)
        first_cell = cell_set["cells"][0]
        self.assertEqual(first_cell["cell_id"], "cell_boss_to_inner_cell_00")
        self.assertEqual(
            first_cell["point_ids"],
            ["boss_p_00", "boss_p_01", "inner_cell_p_01", "inner_cell_p_00"],
        )
        self.assertGreater(first_cell["area_m2"], 0.0)

        selections = {selection["selection_id"]: selection for selection in cell_set["selections"]}
        self.assertEqual(selections["vault_web_cells_primary"]["selected_count"], 11)
        self.assertEqual(selections["vault_web_cells_primary"]["cell_ids"][0], "cell_inner_cell_to_shaft_valley_00")
        self.assertEqual(selections["outer_tracery_opening_cells"]["selected_count"], 11)
        self.assertEqual(selections["outer_tracery_opening_cells"]["cell_ids"][0], "cell_shaft_valley_to_outer_tip_01")
        self.assertEqual(selections["railing_recess_panel_cells"]["selected_count"], 4)
        self.assertEqual(
            selections["railing_recess_panel_cells"]["cell_ids"],
            [
                "cell_boss_to_inner_cell_02",
                "cell_boss_to_inner_cell_07",
                "cell_boss_to_inner_cell_13",
                "cell_boss_to_inner_cell_18",
            ],
        )
        self.assertIn("sacred_22_star_radial_cell_selection_v0", svg)

    def test_validate_only_uses_source_graph_without_writing_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "cells"
            result = subprocess.run(
                [sys.executable, str(CELL_COMPILER), "--validate-only", "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("compiled construction cell selections=1 cells=66 out=<validate-only>", result.stdout)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_output_is_deterministic_across_runs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            graph_out = Path(tmp) / "graph"
            out_a = Path(tmp) / "a"
            out_b = Path(tmp) / "b"
            run_graph_compiler(graph_out)
            run_cell_compiler(graph_out, out_a)
            run_cell_compiler(graph_out, out_b)
            files_a = sorted(path.relative_to(out_a) for path in out_a.rglob("*") if path.is_file())
            files_b = sorted(path.relative_to(out_b) for path in out_b.rglob("*") if path.is_file())

            self.assertEqual(files_a, files_b)
            for rel_path in files_a:
                self.assertEqual(
                    (out_a / rel_path).read_text(encoding="utf-8"),
                    (out_b / rel_path).read_text(encoding="utf-8"),
                    msg=f"non-deterministic construction cell output for {rel_path}",
                )

    def test_unknown_band_selection_fails_before_output(self) -> None:
        source = load_json(DEFAULT_BUNDLE)
        source["selection_sets"][0]["selections"][0]["selector"]["band_id"] = "missing_band"
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_cell_selection_bundle.json"
            out_root = Path(tmp) / "cells"
            bad_bundle.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CELL_COMPILER), "--bundle", str(bad_bundle), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("selector references unknown band_id", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
