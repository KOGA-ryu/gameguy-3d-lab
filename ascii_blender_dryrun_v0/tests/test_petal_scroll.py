from ascii_blender_dryrun.ascii_backend import AsciiBackend
from ascii_blender_dryrun.blender_backend import BlenderBackend
from ascii_blender_dryrun.ops import AddPetalScroll, load_ops
from ascii_blender_dryrun.sweep_geometry import petal_scroll_bounds, petal_scroll_path_points, petal_thickness_at
from ascii_blender_dryrun.validators import validation_report


PETAL_SCROLL = "ascii_blender_dryrun_v0/examples/petal_scroll_column_ornament_recipe_v0.json"


def test_petal_scroll_recipe_validates_and_emits_blender():
    ops = load_ops(PETAL_SCROLL)
    report = validation_report(ops)
    script = BlenderBackend().emit(ops)

    assert report["ok"], report
    assert len(ops) == 1
    assert isinstance(ops[0], AddPetalScroll)
    assert ops[0].name == "proof.petal_scroll_column_ornament_v0"
    assert ops[0].scroll["solid_fill"]["enabled"] is True
    assert "add_petal_scroll('proof.petal_scroll_column_ornament_v0'" in script
    assert "add_petal_scroll_solid_fill(name + '.solid_fill'" in script
    assert "def petal_scroll_surface_point" in script


def test_ascii_backend_handles_petal_scroll():
    backend = AsciiBackend(width=72, height=54)
    ops = load_ops(PETAL_SCROLL)

    text = backend.render_projection(ops, "front")

    assert "FRONT PROJECTION" in text
    assert "╎" in text or "▓" in text
    assert "◆" in text


def test_petal_scroll_path_curls_inward():
    op = load_ops(PETAL_SCROLL)[0]
    assert isinstance(op, AddPetalScroll)

    path = petal_scroll_path_points(op.scroll, op.x, op.y, op.z)
    bounds = petal_scroll_bounds(op.petal, op.scroll, op.x, op.y, op.z)

    assert len(path) == 54
    assert path[0]["radius"] > path[-1]["radius"]
    assert bounds[0] < bounds[1]
    assert bounds[4] < bounds[5]


def test_petal_scroll_thickness_slopes_into_inner_roll():
    op = load_ops(PETAL_SCROLL)[0]
    assert isinstance(op, AddPetalScroll)

    outer_edge = petal_thickness_at(op.petal, 0.0)
    mid_roll = petal_thickness_at(op.petal, 0.55)
    inner_roll = petal_thickness_at(op.petal, 0.92)
    tip = petal_thickness_at(op.petal, 1.0)

    assert outer_edge < mid_roll < inner_roll
    assert tip > outer_edge * 6


def test_petal_scroll_solid_fill_closes_daylight():
    op = load_ops(PETAL_SCROLL)[0]
    assert isinstance(op, AddPetalScroll)

    fill = op.scroll["solid_fill"]

    assert fill["mode"] == "center_fan"
    assert fill["front_depth"] > fill["back_depth"]


def test_petal_scroll_rejects_bad_direction():
    report = validation_report([
        AddPetalScroll(
            name="bad.scroll",
            petal={
                "length": 1.0,
                "max_width": 0.4,
                "max_thickness": 0.05,
            },
            scroll={
                "type": "volute",
                "turns": 1.0,
                "radius_start": 1.0,
                "radius_end": 0.2,
                "direction": "sideways",
            },
        )
    ])

    assert not report["ok"]
    assert any(finding["code"] == "bad_petal_scroll_direction" for finding in report["findings"])
