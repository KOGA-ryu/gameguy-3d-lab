#!/usr/bin/env python3
"""Tests for the local recipe stack workbench."""

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
WORKBENCH = ROOT / "scripts" / "serve_recipe_stack_workbench_v0.py"
PETAL_SCROLL = ROOT / "ascii_blender_dryrun_v0" / "examples" / "petal_scroll_column_ornament_recipe_v0.json"


def load_workbench() -> Any:
    spec = importlib.util.spec_from_file_location("serve_recipe_stack_workbench_v0", WORKBENCH)
    if spec is None or spec.loader is None:
        raise AssertionError("could not import serve_recipe_stack_workbench_v0")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RecipeStackWorkbenchTests(unittest.TestCase):
    def test_validate_only_accepts_default_recipe(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(WORKBENCH),
                    "--recipe",
                    str(PETAL_SCROLL),
                    "--out",
                    tmp,
                    "--validate-only",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("PASS recipe stack workbench validation", result.stdout)

    def test_module_library_exposes_recipe_ops(self) -> None:
        workbench = load_workbench()

        modules = workbench.module_library()
        labels = [module["label"] for module in modules]

        self.assertTrue(any("petal_scroll_column_ornament" in label for label in labels))
        self.assertTrue(any(module["op"]["op"] == "AddPetalScroll" for module in modules))
        self.assertTrue(any(module["op"]["op"] == "AddPetalBloom" for module in modules))

    def test_compile_recipe_writes_ascii_preview_and_script(self) -> None:
        workbench = load_workbench()
        recipe = workbench.normalize_recipe(workbench.load_json(PETAL_SCROLL))
        recipe = json.loads(json.dumps(recipe))
        recipe["ops"][0]["scroll"]["turns"] = 1.1

        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            result = workbench.compile_recipe(recipe, Path(tmp), width=72, height=48)
            compiled = Path(tmp) / "compiled"

            self.assertEqual(result["returncode"], 0, result["log"])
            self.assertTrue((compiled / "validation_report.json").exists())
            self.assertTrue((compiled / "build_doric_column_v0.py").exists())
            self.assertIn("proof.petal_scroll_column_ornament_v0", result["previews"]["script"])
            self.assertGreater(len(result["previews"]["front"]), 100)
            self.assertTrue(result["validation"]["ok"])

    def test_normalize_recipe_rejects_empty_stack(self) -> None:
        workbench = load_workbench()

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                workbench.normalize_recipe({"ops": []})


if __name__ == "__main__":
    unittest.main()
