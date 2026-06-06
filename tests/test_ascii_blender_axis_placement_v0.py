#!/usr/bin/env python3
"""Regression tests for axis and base-placement recipe fields."""

from __future__ import annotations

import unittest
from pathlib import Path

from ascii_blender_dryrun_v0.ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun_v0.ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun_v0.ascii_blender_dryrun.ops import AddCylinder, AddSphere, load_ops
from ascii_blender_dryrun_v0.ascii_blender_dryrun.validators import validation_report


ROOT = Path(__file__).resolve().parents[1]
CHARACTER_RECIPE = ROOT / "ascii_blender_dryrun_v0" / "examples" / "low_poly_character_blockout_recipe_v0.json"
HUMANOID_RECIPE = ROOT / "ascii_blender_dryrun_v0" / "examples" / "humanoid_proportional_blockout_recipe_v0.json"


class AsciiBlenderAxisPlacementTests(unittest.TestCase):
    def test_character_recipe_uses_horizontal_arm_axis(self) -> None:
        ops = load_ops(str(CHARACTER_RECIPE))
        by_name = {getattr(op, "name", ""): op for op in ops}

        self.assertEqual(by_name["left_arm"].axis, "x")
        self.assertEqual(by_name["right_arm"].axis, "x")
        self.assertEqual(by_name["left_leg"].z_mode, "base")
        self.assertEqual(by_name["head"].z_mode, "base")
        self.assertTrue(validation_report(ops)["ok"])

    def test_blender_backend_emits_axis_for_tapered_cylinders(self) -> None:
        ops = load_ops(str(CHARACTER_RECIPE))
        script = BlenderBackend().emit(ops)

        self.assertIn("axis='x'", script)
        self.assertIn("rotate_axis(obj, axis)", script)
        self.assertIn("add_tapered_cylinder('left_arm'", script)

    def test_ascii_preview_draws_horizontal_cylinder_as_span(self) -> None:
        ops = [AddCylinder("test_arm", radius=0.5, height=5.0, z=1.0, x=0.0, y=0.0, axis="x")]
        text = AsciiBackend(width=48, height=24).render_projection(ops, "front")

        self.assertIn("FRONT PROJECTION", text)
        self.assertIn("████████", text)

    def test_humanoid_recipe_uses_sphere_head_and_section_limbs(self) -> None:
        ops = load_ops(str(HUMANOID_RECIPE))
        by_name = {getattr(op, "name", ""): op for op in ops}

        self.assertIsInstance(by_name["head"], AddSphere)
        self.assertEqual(by_name["left_upper_arm"].sections[0]["x"], -3.25)
        self.assertEqual(by_name["right_forearm"].sections[0]["x"], 4.85)
        self.assertTrue(validation_report(ops)["ok"])


if __name__ == "__main__":
    unittest.main()
