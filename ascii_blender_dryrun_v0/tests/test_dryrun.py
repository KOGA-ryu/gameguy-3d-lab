import json
from pathlib import Path

from ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun.ops import load_ops, save_ops
from ascii_blender_dryrun.recipes import doric_column_plan
from ascii_blender_dryrun.validators import validation_report


def test_doric_plan_validates():
    ops = doric_column_plan()
    report = validation_report(ops)
    assert report["ok"], report


def test_ascii_backend_emits_front_side_top():
    ops = doric_column_plan()
    backend = AsciiBackend(width=64, height=48)
    for projection in ["front", "side", "top"]:
        txt = backend.render_projection(ops, projection)
        assert projection.upper() in txt
        assert "█" in txt


def test_blender_backend_emits_named_parts():
    ops = doric_column_plan()
    script = BlenderBackend().emit(ops)
    assert "plinth.lower_step" in script
    assert "shaft.tapered_fluted_core" in script
    assert "capital.abacus_square_slab" in script
    assert "TODO: cut 20 radial flutes" in script


def test_recipe_roundtrip(tmp_path):
    ops = doric_column_plan()
    path = tmp_path / "recipe.json"
    save_ops(str(path), ops)
    loaded = load_ops(str(path))
    assert len(loaded) == len(ops)
