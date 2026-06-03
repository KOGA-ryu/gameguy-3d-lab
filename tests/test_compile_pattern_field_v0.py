#!/usr/bin/env python3
"""Tests for multi-center pattern field compilation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_pattern_field_v0.py"
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "pattern_field_recipes_v0.json"


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


class PatternFieldCompilerTests(unittest.TestCase):
    def test_default_pattern_field_compiles_multi_center_rosettes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pattern_field"
            result = run_compiler(out_root)
            manifest = load_json(out_root / "manifest.json")
            field = load_json(out_root / "fields" / "hex_rosette_pattern_field_v0.json")
            svg = (out_root / "svg" / "hex_rosette_pattern_field_v0.svg").read_text(encoding="utf-8")

        self.assertIn("compiled pattern fields=1 edges=432 selected=96", result.stdout)
        self.assertEqual(manifest["schema"], "gameguy_pattern_field_manifest_v0")
        self.assertEqual(manifest["field_count"], 1)
        self.assertEqual(manifest["fields"][0]["edge_count"], 432)
        self.assertEqual(manifest["fields"][0]["unique_selected_edge_count"], 96)
        self.assertEqual(field["schema"], "gameguy_pattern_field_v0")
        self.assertEqual(field["field_id"], "hex_rosette_pattern_field_v0")
        self.assertEqual(field["summary"]["instance_count"], 7)
        self.assertEqual(field["summary"]["circle_count"], 21)
        self.assertEqual(field["summary"]["point_count"], 259)
        self.assertEqual(field["summary"]["edge_count"], 432)
        self.assertEqual(field["summary"]["selection_count"], 3)
        self.assertEqual(field["summary"]["selected_edge_reference_count"], 96)
        self.assertEqual(field["summary"]["unique_selected_edge_count"], 96)

        selections = {selection["selection_id"]: selection for selection in field["selections"]}
        self.assertEqual(selections["center_rosette_inner_star_traces"]["selected_count"], 12)
        self.assertEqual(selections["surrounding_rosette_inner_star_traces"]["selected_count"], 72)
        self.assertEqual(selections["selected_connector_traces"]["selected_count"], 12)
        edge_by_id = {edge["edge_id"]: edge for edge in field["edges"]}
        center_selected_edges = [edge_by_id[edge_id] for edge_id in selections["center_rosette_inner_star_traces"]["edge_ids"]]
        surrounding_selected_edges = [edge_by_id[edge_id] for edge_id in selections["surrounding_rosette_inner_star_traces"]["edge_ids"]]
        self.assertTrue(all("ring:star" in edge["tags"] for edge in center_selected_edges + surrounding_selected_edges))
        self.assertTrue(all("ring:outer" not in edge["tags"] for edge in center_selected_edges + surrounding_selected_edges))
        self.assertIn("hex_rosette_pattern_field_v0", svg)
        self.assertIn('class="selected"', svg)

    def test_validate_only_writes_no_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "pattern_field"
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--validate-only", "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("compiled pattern fields=1 edges=432 out=<validate-only>", result.stdout)
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
                    msg=f"non-deterministic pattern field output for {rel_path}",
                )

    def test_unknown_module_reference_fails_before_output(self) -> None:
        source = load_json(DEFAULT_BUNDLE)
        source["fields"][0]["instances"][0]["module_id"] = "missing_module"
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_pattern_field_bundle.json"
            out_root = Path(tmp) / "pattern_field"
            bad_bundle.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--bundle", str(bad_bundle), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown module", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
