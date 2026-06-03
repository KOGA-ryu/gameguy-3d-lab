#!/usr/bin/env python3
"""Tests for pattern segment splitting."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIELD_COMPILER = ROOT / "scripts" / "compile_pattern_field_v0.py"
SEGMENT_COMPILER = ROOT / "scripts" / "compile_pattern_segments_v0.py"
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "pattern_segment_recipes_v0.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return data


def run_field_compiler(out_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(FIELD_COMPILER), "--clean", "--out", str(out_root)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_segment_compiler(field_out: Path, segment_out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SEGMENT_COMPILER),
            "--pattern-field-manifest",
            str(field_out / "manifest.json"),
            "--clean",
            "--out",
            str(segment_out),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class PatternSegmentCompilerTests(unittest.TestCase):
    def test_default_pattern_segments_split_intersections(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            field_out = Path(tmp) / "field"
            segment_out = Path(tmp) / "segments"
            run_field_compiler(field_out)
            result = run_segment_compiler(field_out, segment_out)
            manifest = load_json(segment_out / "manifest.json")
            segment_set = load_json(segment_out / "segment_sets" / "hex_rosette_pattern_segments_v0.json")
            svg = (segment_out / "svg" / "hex_rosette_pattern_segments_v0.svg").read_text(encoding="utf-8")

        self.assertIn("compiled pattern segment sets=1", result.stdout)
        self.assertEqual(manifest["schema"], "gameguy_pattern_segment_manifest_v0")
        self.assertEqual(manifest["segment_set_count"], 1)
        self.assertEqual(segment_set["schema"], "gameguy_pattern_segment_graph_v0")
        self.assertEqual(segment_set["source_field_id"], "hex_rosette_pattern_field_v0")
        self.assertEqual(segment_set["summary"]["source_edge_count"], 432)
        self.assertEqual(segment_set["summary"]["intersection_point_count"], 504)
        self.assertEqual(segment_set["summary"]["segment_count"], 1656)
        self.assertEqual(segment_set["summary"]["selection_count"], 3)
        self.assertEqual(segment_set["summary"]["selected_segment_reference_count"], 984)
        self.assertEqual(segment_set["summary"]["unique_selected_segment_count"], 984)

        selections = {selection["selection_id"]: selection for selection in segment_set["selections"]}
        self.assertEqual(selections["selected_center_rosette_segments"]["selected_count"], 132)
        self.assertEqual(selections["selected_surrounding_rosette_segments"]["selected_count"], 792)
        self.assertEqual(selections["selected_connector_segments"]["selected_count"], 60)
        segment_by_id = {segment["segment_id"]: segment for segment in segment_set["segments"]}
        selected_rosette_ids = (
            selections["selected_center_rosette_segments"]["segment_ids"]
            + selections["selected_surrounding_rosette_segments"]["segment_ids"]
        )
        selected_rosette_segments = [segment_by_id[segment_id] for segment_id in selected_rosette_ids]
        self.assertTrue(all("source:ring:star" in segment["tags"] for segment in selected_rosette_segments))
        self.assertTrue(all("source:ring:outer" not in segment["tags"] for segment in selected_rosette_segments))
        self.assertIn("hex_rosette_pattern_segments_v0", svg)
        self.assertIn('class="intersection"', svg)

    def test_validate_only_uses_source_field_without_writing_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out_root = Path(tmp) / "segments"
            result = subprocess.run(
                [sys.executable, str(SEGMENT_COMPILER), "--validate-only", "--out", str(out_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("compiled pattern segment sets=1", result.stdout)
        self.assertFalse((out_root / "manifest.json").exists())

    def test_output_is_deterministic_across_runs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            field_out = Path(tmp) / "field"
            out_a = Path(tmp) / "a"
            out_b = Path(tmp) / "b"
            run_field_compiler(field_out)
            run_segment_compiler(field_out, out_a)
            run_segment_compiler(field_out, out_b)
            files_a = sorted(path.relative_to(out_a) for path in out_a.rglob("*") if path.is_file())
            files_b = sorted(path.relative_to(out_b) for path in out_b.rglob("*") if path.is_file())

            self.assertEqual(files_a, files_b)
            for rel_path in files_a:
                self.assertEqual(
                    (out_a / rel_path).read_text(encoding="utf-8"),
                    (out_b / rel_path).read_text(encoding="utf-8"),
                    msg=f"non-deterministic pattern segment output for {rel_path}",
                )

    def test_unknown_field_reference_fails_before_output(self) -> None:
        source = load_json(DEFAULT_BUNDLE)
        source["segment_sets"][0]["source_field_id"] = "missing_field"
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            bad_bundle = Path(tmp) / "bad_pattern_segments_bundle.json"
            out_root = Path(tmp) / "segments"
            bad_bundle.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SEGMENT_COMPILER), "--bundle", str(bad_bundle), "--out", str(out_root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references unknown source_field_id", result.stderr)
        self.assertFalse((out_root / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
