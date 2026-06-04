import pytest

from ascii_blender_dryrun.ops import AddMoulding, AddProfileMoulding, load_ops
from ascii_blender_dryrun.profile_mouldings import compile_profile_moulding, compile_profile_mouldings
from ascii_blender_dryrun.recipes import doric_column_plan, doric_column_source_plan


EXAMPLE_RECIPE = "ascii_blender_dryrun_v0/examples/doric_column_recipe_v0.json"


def test_profile_moulding_compiles_terms_to_points():
    source = AddProfileMoulding(
        "test.profile",
        base_z=10.0,
        sequence=[
            {
                "term": "fillet",
                "height": 0.25,
                "start_radius": 2.0,
                "end_radius": 2.0,
            },
            {"term": "torus", "height": 0.75, "end_radius": 3.0},
            {"term": "scotia", "height": 0.5, "end_radius": 2.4},
        ],
    )

    compiled = compile_profile_moulding(source)

    assert isinstance(compiled, AddMoulding)
    assert compiled.name == source.name
    assert compiled.base_z == source.base_z
    assert compiled.profile[0] == {"term": "fillet_start", "z": 0.0, "radius": 2.0}
    assert compiled.profile[-1]["z"] == 1.5
    assert compiled.profile[-1]["radius"] == 2.4
    assert len(compiled.profile) > len(source.sequence)


def test_doric_source_plan_uses_profile_terms_and_compiled_plan_does_not():
    source_ops = doric_column_source_plan()
    compiled_ops = doric_column_plan()

    assert any(isinstance(op, AddProfileMoulding) for op in source_ops)
    assert not any(isinstance(op, AddProfileMoulding) for op in compiled_ops)
    assert any(isinstance(op, AddMoulding) for op in compiled_ops)


def test_doric_json_source_recipe_compiles_profile_terms():
    source_ops = load_ops(EXAMPLE_RECIPE)
    compiled_ops = compile_profile_mouldings(source_ops)

    assert any(isinstance(op, AddProfileMoulding) for op in source_ops)
    assert not any(isinstance(op, AddProfileMoulding) for op in compiled_ops)
    assert any(isinstance(op, AddMoulding) for op in compiled_ops)


def test_profile_moulding_requires_first_start_radius():
    source = AddProfileMoulding(
        "bad.profile",
        base_z=0.0,
        sequence=[{"term": "torus", "height": 1.0, "end_radius": 3.0}],
    )

    with pytest.raises(ValueError, match="first segment needs start_radius"):
        compile_profile_moulding(source)
