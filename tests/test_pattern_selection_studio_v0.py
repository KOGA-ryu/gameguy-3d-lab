#!/usr/bin/env python3
"""Tests for the local pattern selection studio."""

from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "scripts" / "serve_pattern_selection_studio_v0.py"


def load_studio() -> Any:
    spec = importlib.util.spec_from_file_location("serve_pattern_selection_studio_v0", STUDIO)
    if spec is None or spec.loader is None:
        raise AssertionError("could not import serve_pattern_selection_studio_v0")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixture_graph() -> dict[str, Any]:
    return {
        "schema": "gameguy_pattern_segment_graph_v0",
        "segment_set_id": "tiny_segments_v0",
        "source_field_id": "tiny_field_v0",
        "bounds_m": {"width": 1.0, "height": 1.0},
        "intersections": [],
        "segments": [
            {
                "segment_id": "segment_a",
                "source_edge_id": "edge_a",
                "source_edge_type": "linework_chord",
                "start_xy_m": [0.1, 0.1],
                "end_xy_m": [0.9, 0.1],
                "length_m": 0.8,
                "tags": ["pattern_segment", "source:ring:star"],
            },
            {
                "segment_id": "segment_b",
                "source_edge_id": "edge_b",
                "source_edge_type": "linework_bridge",
                "start_xy_m": [0.2, 0.2],
                "end_xy_m": [0.8, 0.8],
                "length_m": 0.848528,
                "tags": ["pattern_segment", "source:from_ring:star", "source:to_ring:star"],
            },
        ],
        "summary": {
            "source_edge_count": 2,
            "intersection_point_count": 0,
            "segment_count": 2,
            "selection_count": 0,
            "selected_segment_reference_count": 0,
            "unique_selected_segment_count": 0,
        },
    }


class PatternSelectionStudioTests(unittest.TestCase):
    def test_validate_only_accepts_segment_graph(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            graph_path = Path(tmp) / "segments.json"
            graph_path.write_text(json.dumps(fixture_graph(), indent=2) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(STUDIO),
                    "--segment-set",
                    str(graph_path),
                    "--selection-out",
                    str(Path(tmp) / "selection.json"),
                    "--no-compile-missing",
                    "--validate-only",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("PASS pattern selection studio validation", result.stdout)
        self.assertIn("segments=2", result.stdout)

    def test_selection_recipe_normalizes_known_segments(self) -> None:
        studio = load_studio()
        graph = fixture_graph()
        recipe = {
            "schema": "pattern_selection_recipe_v0",
            "selection_id": "tiny_selection_v0",
            "source_segment_set_id": "tiny_segments_v0",
            "selected_segment_ids": ["segment_b", "segment_a", "segment_a"],
            "segment_styles": {
                "segment_a": {"role": "rib", "stroke": "#315a99", "stroke_width": 2.5},
                "segment_b": {"role": "ornament", "stroke": "#c6972e", "stroke_width": 1.8},
            },
        }

        normalized = studio.normalize_selection_recipe(recipe, graph, Path("/tmp/tiny_segments.json"))

        self.assertEqual(normalized["selection_id"], "tiny_selection_v0")
        self.assertEqual(normalized["selected_segment_ids"], ["segment_a", "segment_b"])
        self.assertEqual(normalized["segment_styles"]["segment_a"]["role"], "rib")
        self.assertEqual(normalized["segment_styles"]["segment_b"]["stroke"], "#c6972e")

    def test_selection_recipe_rejects_unknown_segment(self) -> None:
        studio = load_studio()
        graph = fixture_graph()
        recipe = {
            "schema": "pattern_selection_recipe_v0",
            "source_segment_set_id": "tiny_segments_v0",
            "selected_segment_ids": ["missing_segment"],
            "segment_styles": {},
        }

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                studio.normalize_selection_recipe(recipe, graph, Path("/tmp/tiny_segments.json"))


if __name__ == "__main__":
    unittest.main()
