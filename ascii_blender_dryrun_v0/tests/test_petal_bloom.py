from ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun.ops import AddPetalBloom, load_ops
from ascii_blender_dryrun.sweep_geometry import petal_layer_instances, petal_thickness_at, petal_width_at
from ascii_blender_dryrun.validators import validation_report


LAYERED_ROSE = "ascii_blender_dryrun_v0/examples/layered_rose_bloom_recipe_v0.json"


def test_layered_petal_bloom_recipe_validates_and_emits_blender():
    ops = load_ops(LAYERED_ROSE)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert any(isinstance(op, AddPetalBloom) for op in ops)
    assert "add_petal_bloom('proof.layered_rose_bloom_v0'" in script


def test_ascii_backend_handles_petal_bloom():
    backend = AsciiBackend(width=72, height=54)
    ops = load_ops(LAYERED_ROSE)

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
