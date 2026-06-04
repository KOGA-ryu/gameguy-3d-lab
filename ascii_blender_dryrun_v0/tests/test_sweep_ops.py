from ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun.ops import AddPathSweep, AddSectionStack, load_ops
from ascii_blender_dryrun.sweep_geometry import path_sweep_instances, profile_points
from ascii_blender_dryrun.validators import validation_report


TWISTED_BAR = "ascii_blender_dryrun_v0/examples/twisted_square_bar_recipe_v0.json"
ROSE_SCROLL = "ascii_blender_dryrun_v0/examples/rose_scroll_sweep_recipe_v0.json"


def test_section_stack_recipe_validates_and_emits_blender():
    ops = load_ops(TWISTED_BAR)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert any(isinstance(op, AddSectionStack) for op in ops)
    assert "add_section_stack('proof.twisted_square_bar_v0'" in script


def test_path_sweep_recipe_validates_and_emits_blender():
    ops = load_ops(ROSE_SCROLL)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert any(isinstance(op, AddPathSweep) for op in ops)
    assert "add_path_sweep('proof.rose_scroll_sweep_v0'" in script


def test_ascii_backend_handles_sweep_ops():
    backend = AsciiBackend(width=64, height=48)
    for path in [TWISTED_BAR, ROSE_SCROLL]:
        ops = load_ops(path)
        for projection in ["front", "side", "top"]:
            text = backend.render_projection(ops, projection)
            assert projection.upper() in text
            assert "█" in text or "▓" in text or "▒" in text


def test_profile_and_spiral_helpers_are_deterministic():
    square = profile_points({"type": "square", "radius": 2.0}, vertices=4)
    oval = profile_points({"type": "oval", "radius_x": 0.5, "radius_y": 0.25, "vertices": 8})
    instances = path_sweep_instances(
        {"type": "spiral", "turns": 1.0, "radius_start": 0.2, "radius_end": 1.0, "samples": 5},
        {"type": "radial", "count": 4},
    )

    assert square == [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    assert len(oval) == 8
    assert len(instances) == 4
    assert len(instances[0]) == 5
