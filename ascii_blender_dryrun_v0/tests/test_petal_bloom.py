from ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun.ops import AddPetalBloom, AddPetalBloomDetail, AddPetalBloomPreset, load_ops
from ascii_blender_dryrun.petal_bloom_presets import (
    compile_petal_bloom_presets,
    load_petal_bloom_presets,
)
from ascii_blender_dryrun.sweep_geometry import petal_layer_instances, petal_thickness_at, petal_width_at
from ascii_blender_dryrun.validators import validation_report


LAYERED_ROSE = "ascii_blender_dryrun_v0/examples/layered_rose_bloom_recipe_v0.json"
SPIRAL_ROSE_BUD = "ascii_blender_dryrun_v0/examples/spiral_rose_bud_recipe_v0.json"
PRESET_SPIRAL_ROSE_BUD = "ascii_blender_dryrun_v0/examples/preset_spiral_rose_bud_recipe_v0.json"
PETAL_BLOOM_PRESET_ZOO = "ascii_blender_dryrun_v0/examples/petal_bloom_preset_zoo_recipe_v0.json"
POLISHED_ROSE_BOSS = "ascii_blender_dryrun_v0/examples/polished_rose_boss_recipe_v0.json"
PETAL_BLOOM_RECIPES = [LAYERED_ROSE, SPIRAL_ROSE_BUD]


def test_layered_petal_bloom_recipe_validates_and_emits_blender():
    for path in PETAL_BLOOM_RECIPES:
        ops = load_ops(path)
        report = validation_report(ops)
        script = BlenderBackend().emit(ops)

        assert report["ok"], report
        assert any(isinstance(op, AddPetalBloom) for op in ops)
        assert "add_petal_bloom(" in script

    layered_script = BlenderBackend().emit(load_ops(LAYERED_ROSE))
    rose_script = BlenderBackend().emit(load_ops(SPIRAL_ROSE_BUD))
    assert "add_petal_bloom('proof.layered_rose_bloom_v0'" in layered_script
    assert "add_petal_bloom('proof.spiral_rose_bud_v0'" in rose_script


def test_ascii_backend_handles_petal_bloom():
    backend = AsciiBackend(width=72, height=54)
    for path in PETAL_BLOOM_RECIPES:
        ops = load_ops(path)

        for projection in ["front", "side", "top"]:
            text = backend.render_projection(ops, projection)
            assert projection.upper() in text
            assert "▓" in text or "░" in text


def test_petal_curve_is_skinny_wide_skinny():
    op = load_ops(LAYERED_ROSE)[0]
    assert isinstance(op, AddPetalBloom)

    width_start = petal_width_at(op.petal, 0.0)
    width_peak = petal_width_at(op.petal, op.petal["width_peak_t"])
    width_tip = petal_width_at(op.petal, 1.0)
    thickness_start = petal_thickness_at(op.petal, 0.0)
    thickness_peak = petal_thickness_at(op.petal, op.petal["thickness_peak_t"])
    thickness_tip = petal_thickness_at(op.petal, 1.0)

    assert width_start < width_peak
    assert width_tip < width_peak
    assert thickness_start < thickness_peak
    assert thickness_tip < thickness_peak


def test_petal_layers_create_spiral_instances():
    op = load_ops(LAYERED_ROSE)[0]
    assert isinstance(op, AddPetalBloom)

    instances = petal_layer_instances(op.layers)

    assert len(instances) == 22
    assert instances[0]["angle"] != instances[8]["angle"]
    assert instances[-1]["length_scale"] < instances[0]["length_scale"]


def test_spiral_rose_bud_is_denser_and_blunter_than_bloom_proof():
    op = load_ops(SPIRAL_ROSE_BUD)[0]
    assert isinstance(op, AddPetalBloom)

    instances = petal_layer_instances(op.layers)
    width_tip = petal_width_at(op.petal, 1.0)
    width_peak = petal_width_at(op.petal, op.petal["width_peak_t"])

    assert len(instances) == 31
    assert width_tip > width_peak * 0.5
    assert op.layers[-1]["bend_angle_deg"] > op.layers[0]["bend_angle_deg"]
    assert op.layers[-1]["petal_twist_deg"] > op.layers[0]["petal_twist_deg"]


def test_petal_bloom_preset_registry_has_named_roles():
    presets = load_petal_bloom_presets()

    assert set(presets) == {
        "flame_petals_v0",
        "floral_boss_relief_v0",
        "leaf_cluster_v0",
        "open_bloom_chrysanthemum_v0",
        "spiral_rose_bud_v0",
    }
    assert presets["spiral_rose_bud_v0"]["role"] == "rose_bud"


def test_petal_bloom_preset_recipe_compiles_to_low_level_bloom():
    source_ops = load_ops(PRESET_SPIRAL_ROSE_BUD)
    assert isinstance(source_ops[0], AddPetalBloomPreset)

    ops = compile_petal_bloom_presets(source_ops)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert isinstance(ops[0], AddPetalBloom)
    assert ops[0].name == "proof.preset_spiral_rose_bud_v0"
    assert ops[0].petal["length"] == 1.0816
    assert ops[0].petal["max_width"] == 0.60
    assert ops[0].layers[-1]["petal_twist_deg"] == 74
    assert "add_petal_bloom('proof.preset_spiral_rose_bud_v0'" in script


def test_polished_rose_boss_compiles_and_emits_detail_pass():
    source_ops = load_ops(POLISHED_ROSE_BOSS)
    assert isinstance(source_ops[0], AddPetalBloomPreset)
    assert isinstance(source_ops[1], AddPetalBloomDetail)

    ops = compile_petal_bloom_presets(source_ops)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert isinstance(ops[0], AddPetalBloom)
    assert isinstance(ops[1], AddPetalBloomDetail)
    assert ops[1].target == "proof.polished_rose_boss_v0"
    assert "add_petal_bloom('proof.polished_rose_boss_v0'" in script
    assert "add_petal_bloom_detail('proof.polished_rose_boss_v0'" in script


def test_ascii_backend_handles_polished_rose_boss_detail():
    backend = AsciiBackend(width=72, height=54)
    ops = compile_petal_bloom_presets(load_ops(POLISHED_ROSE_BOSS))

    text = backend.render_projection(ops, "top")

    assert "TOP PROJECTION" in text
    assert "●" in text or "╎" in text


def test_petal_detail_requires_existing_target():
    report = validation_report([
        AddPetalBloomDetail(
            target="missing.bloom",
            center_boss={"type": "bead", "radius": 0.1, "height": 0.1},
        )
    ])

    assert not report["ok"]
    assert report["findings"][0]["code"] == "petal_detail_missing_target"


def test_uncompiled_petal_preset_recipe_fails_validation():
    report = validation_report(load_ops(PRESET_SPIRAL_ROSE_BUD))

    assert not report["ok"]
    assert report["findings"][0]["code"] == "uncompiled_petal_bloom_preset"


def test_ascii_backend_handles_compiled_petal_preset_recipe():
    backend = AsciiBackend(width=72, height=54)
    ops = compile_petal_bloom_presets(load_ops(PRESET_SPIRAL_ROSE_BUD))

    text = backend.render_projection(ops, "top")

    assert "TOP PROJECTION" in text
    assert "▓" in text or "░" in text


def test_petal_bloom_preset_zoo_compiles_all_roles():
    source_ops = load_ops(PETAL_BLOOM_PRESET_ZOO)
    assert all(isinstance(op, AddPetalBloomPreset) for op in source_ops)

    ops = compile_petal_bloom_presets(source_ops)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert len(ops) == 5
    assert all(isinstance(op, AddPetalBloom) for op in ops)
    assert [op.name for op in ops] == [
        "proof.zoo.open_bloom_chrysanthemum_v0",
        "proof.zoo.spiral_rose_bud_v0",
        "proof.zoo.floral_boss_relief_v0",
        "proof.zoo.leaf_cluster_v0",
        "proof.zoo.flame_petals_v0",
    ]
    assert script.count("add_petal_bloom('proof.zoo.") == 5


def test_ascii_backend_handles_compiled_petal_zoo_recipe():
    backend = AsciiBackend(width=120, height=48)
    ops = compile_petal_bloom_presets(load_ops(PETAL_BLOOM_PRESET_ZOO))

    text = backend.render_projection(ops, "top")

    assert "TOP PROJECTION" in text
    assert text.count("◆") >= 5
