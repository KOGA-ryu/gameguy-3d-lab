import json
from pathlib import Path

from ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun.ops import AddMoulding, load_ops, save_ops
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
    assert "add_tapered_cylinder" in script
    assert "add_moulding('base.torus_scotia_moulding'" in script
    assert "add_moulding('capital.echinus_cushion'" in script
    assert "cut_flutes('shaft.tapered_fluted_core', 20" in script


def test_recipe_roundtrip(tmp_path):
    ops = doric_column_plan()
    path = tmp_path / "recipe.json"
    save_ops(str(path), ops)
    loaded = load_ops(str(path))
    assert len(loaded) == len(ops)
    assert any(isinstance(op, AddMoulding) for op in loaded)


def test_moulding_profile_validation_catches_bad_order():
    ops = [
        AddMoulding(
            "bad.profile",
            base_z=0.0,
            profile=[
                {"term": "start", "z": 1.0, "radius": 2.0},
                {"term": "drops", "z": 0.5, "radius": 2.4},
            ],
        )
    ]
    report = validation_report(ops)
    codes = {finding["code"] for finding in report["findings"]}
    assert "moulding_profile_not_monotonic" in codes
