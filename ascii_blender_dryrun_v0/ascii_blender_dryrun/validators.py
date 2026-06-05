"""
Validation pass for build plans.

This is deliberately boring and blunt. It should catch the dumb failures
before Blender gets involved.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from .ops import (
    AddBox,
    AddCylinder,
    AddMoulding,
    AddPathSweep,
    AddPetalBloom,
    AddPetalBloomDetail,
    AddPetalBloomPreset,
    AddPetalScroll,
    AddProfileMoulding,
    AddRing,
    AddSectionStack,
    CutFlutes,
    BuildOp,
)
from .profile_mouldings import SUPPORTED_TERMS
from .sweep_geometry import (
    path_sweep_bounds,
    petal_bloom_bounds,
    petal_scroll_bounds,
    petal_thickness_at,
    petal_width_at,
    profile_points,
    transformed_profile_points,
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def validate_ops(ops: list[BuildOp]) -> list[Finding]:
    findings: list[Finding] = []
    names: set[str] = set()
    cylinders: dict[str, AddCylinder] = {}

    for op in ops:
        name = getattr(op, "name", None)
        if name:
            if name in names:
                findings.append(Finding("error", "duplicate_name", f"Duplicate object name: {name}"))
            names.add(name)

        if isinstance(op, AddBox):
            if op.width <= 0 or op.depth <= 0 or op.height <= 0:
                findings.append(Finding("error", "bad_box_dimensions", f"{op.name} has non-positive dimensions."))
        elif isinstance(op, AddCylinder):
            cylinders[op.name] = op
            if op.radius <= 0 or op.height <= 0:
                findings.append(Finding("error", "bad_cylinder_dimensions", f"{op.name} has non-positive dimensions."))
            if op.vertices < 12:
                findings.append(Finding("warning", "low_cylinder_vertices", f"{op.name} has low vertex count: {op.vertices}"))
            if op.taper_top_radius is not None and op.taper_top_radius <= 0:
                findings.append(Finding("error", "bad_taper_radius", f"{op.name} has invalid top radius."))
        elif isinstance(op, AddRing):
            if op.radius <= 0 or op.tube_height <= 0:
                findings.append(Finding("error", "bad_ring_dimensions", f"{op.name} has non-positive dimensions."))
        elif isinstance(op, AddMoulding):
            if op.base_z < 0:
                findings.append(Finding("warning", "negative_moulding_base_z", f"{op.name} starts below z=0."))
            if op.vertices < 12:
                findings.append(Finding("warning", "low_moulding_vertices", f"{op.name} has low vertex count: {op.vertices}"))
            if len(op.profile) < 2:
                findings.append(Finding("error", "short_moulding_profile", f"{op.name} needs at least two profile points."))
            previous_z: float | None = None
            for index, point in enumerate(op.profile):
                if "radius" not in point or "z" not in point:
                    findings.append(Finding("error", "bad_moulding_profile_point", f"{op.name} point {index} needs radius and z."))
                    continue
                radius = float(point["radius"])
                local_z = float(point["z"])
                if radius <= 0:
                    findings.append(Finding("error", "bad_moulding_radius", f"{op.name} point {index} has non-positive radius."))
                if local_z < 0:
                    findings.append(Finding("error", "bad_moulding_z", f"{op.name} point {index} has negative local z."))
                if previous_z is not None and local_z < previous_z:
                    findings.append(Finding("error", "moulding_profile_not_monotonic", f"{op.name} profile z values must rise in order."))
                previous_z = local_z
        elif isinstance(op, AddProfileMoulding):
            if op.base_z < 0:
                findings.append(Finding("warning", "negative_profile_moulding_base_z", f"{op.name} starts below z=0."))
            if op.vertices < 12:
                findings.append(Finding("warning", "low_profile_moulding_vertices", f"{op.name} has low vertex count: {op.vertices}"))
            if not op.sequence:
                findings.append(Finding("error", "empty_profile_moulding_sequence", f"{op.name} needs at least one segment."))
            for index, segment in enumerate(op.sequence):
                term = segment.get("term")
                if term not in SUPPORTED_TERMS:
                    findings.append(Finding("error", "unknown_profile_term", f"{op.name} segment {index} has unknown term: {term!r}"))
                if float(segment.get("height", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_profile_segment_height", f"{op.name} segment {index} height must be positive."))
                if index == 0 and "start_radius" not in segment:
                    findings.append(Finding("error", "missing_profile_start_radius", f"{op.name} first segment needs start_radius."))
                for key in ("start_radius", "end_radius"):
                    if key in segment and float(segment[key]) <= 0:
                        findings.append(Finding("error", "bad_profile_segment_radius", f"{op.name} segment {index} {key} must be positive."))
                if "steps" in segment and int(segment["steps"]) < 1:
                    findings.append(Finding("error", "bad_profile_segment_steps", f"{op.name} segment {index} steps must be at least 1."))
        elif isinstance(op, AddSectionStack):
            if len(op.sections) < 2:
                findings.append(Finding("error", "short_section_stack", f"{op.name} needs at least two sections."))
            if op.vertices < 3:
                findings.append(Finding("error", "bad_section_stack_vertices", f"{op.name} needs at least three vertices."))
            previous_z: float | None = None
            point_count: int | None = None
            for index, section in enumerate(op.sections):
                if "z" not in section:
                    findings.append(Finding("error", "missing_section_z", f"{op.name} section {index} needs z."))
                    continue
                z = float(section["z"])
                if previous_z is not None and z <= previous_z:
                    findings.append(Finding("error", "section_stack_z_order", f"{op.name} sections must rise in z order."))
                previous_z = z
                if float(section.get("scale", 1.0)) <= 0:
                    findings.append(Finding("error", "bad_section_scale", f"{op.name} section {index} scale must be positive."))
                try:
                    points = transformed_profile_points(section, {"type": "circle", "radius": 1.0}, op.vertices)
                except (TypeError, ValueError) as exc:
                    findings.append(Finding("error", "bad_section_profile", f"{op.name} section {index}: {exc}"))
                    continue
                if point_count is None:
                    point_count = len(points)
                elif len(points) != point_count:
                    findings.append(Finding("error", "mixed_section_point_counts", f"{op.name} section profiles must have matching point counts."))
        elif isinstance(op, AddPathSweep):
            try:
                profile_points(op.profile)
            except (TypeError, ValueError) as exc:
                findings.append(Finding("error", "bad_sweep_profile", f"{op.name}: {exc}"))
            try:
                path_sweep_bounds(op.path, op.profile, op.taper, op.repeat)
            except (TypeError, ValueError) as exc:
                findings.append(Finding("error", "bad_sweep_path", f"{op.name}: {exc}"))
            if op.taper:
                for index, point in enumerate(op.taper):
                    if not (0.0 <= float(point.get("t", -1.0)) <= 1.0):
                        findings.append(Finding("error", "bad_sweep_taper_t", f"{op.name} taper point {index} t must be 0..1."))
                    if float(point.get("scale", 0.0)) <= 0:
                        findings.append(Finding("error", "bad_sweep_taper_scale", f"{op.name} taper point {index} scale must be positive."))
        elif isinstance(op, AddPetalBloom):
            petal = op.petal
            for key in ("length", "max_width", "max_thickness"):
                if float(petal.get(key, 0.0)) <= 0:
                    findings.append(Finding("error", "bad_petal_dimension", f"{op.name} petal {key} must be positive."))
            for key in ("base_width", "tip_width", "min_width", "min_thickness", "tip_thickness"):
                if key in petal and float(petal[key]) <= 0:
                    findings.append(Finding("error", "bad_petal_dimension", f"{op.name} petal {key} must be positive."))
            for key in ("width_peak_t", "thickness_peak_t", "bend_start_t"):
                if key in petal and not (0.0 <= float(petal[key]) <= 1.0):
                    findings.append(Finding("error", "bad_petal_t", f"{op.name} petal {key} must be 0..1."))
            for key in ("samples_length", "samples_width"):
                if key in petal and int(petal[key]) < 2:
                    findings.append(Finding("error", "bad_petal_samples", f"{op.name} petal {key} must be at least 2."))
            if not op.layers:
                findings.append(Finding("error", "empty_petal_layers", f"{op.name} needs at least one layer."))
            for index, layer in enumerate(op.layers):
                if int(layer.get("count", 0)) <= 0:
                    findings.append(Finding("error", "bad_petal_layer_count", f"{op.name} layer {index} count must be positive."))
                if float(layer.get("radius", 0.0)) < 0:
                    findings.append(Finding("error", "bad_petal_layer_radius", f"{op.name} layer {index} radius must be non-negative."))
                for key in ("length_scale", "width_scale", "thickness_scale"):
                    if float(layer.get(key, 1.0)) <= 0:
                        findings.append(Finding("error", "bad_petal_layer_scale", f"{op.name} layer {index} {key} must be positive."))
            try:
                petal_width_at(petal, 0.5)
                petal_thickness_at(petal, 0.5)
                petal_bloom_bounds(petal, op.layers, op.x, op.y, op.z)
            except (TypeError, ValueError) as exc:
                findings.append(Finding("error", "bad_petal_bloom", f"{op.name}: {exc}"))
        elif isinstance(op, AddPetalBloomPreset):
            findings.append(Finding(
                "error",
                "uncompiled_petal_bloom_preset",
                f"{op.name} must be expanded with compile_petal_bloom_presets before validation.",
            ))
        elif isinstance(op, AddPetalBloomDetail):
            if op.target not in names:
                findings.append(Finding("error", "petal_detail_missing_target", f"Petal detail target does not exist before detail: {op.target}"))
            if op.center_boss:
                if float(op.center_boss.get("radius", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_center_boss_radius", f"{op.target} center boss radius must be positive."))
                if float(op.center_boss.get("height", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_center_boss_height", f"{op.target} center boss height must be positive."))
            if op.veins and op.veins.get("enabled", True):
                if op.veins.get("mode", "centerline") != "centerline":
                    findings.append(Finding("error", "bad_vein_mode", f"{op.target} vein mode must be centerline."))
                if float(op.veins.get("bevel_depth", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_vein_bevel_depth", f"{op.target} vein bevel_depth must be positive."))
                if int(op.veins.get("samples", 2)) < 2:
                    findings.append(Finding("error", "bad_vein_samples", f"{op.target} vein samples must be at least 2."))
                start_t = float(op.veins.get("start_t", 0.16))
                end_t = float(op.veins.get("end_t", 0.88))
                if not 0.0 <= start_t <= 1.0 or not 0.0 <= end_t <= 1.0 or end_t <= start_t:
                    findings.append(Finding("error", "bad_vein_t_range", f"{op.target} vein start_t/end_t must be ordered within 0..1."))
            if op.edge and "bevel" in op.edge and float(op.edge["bevel"]) <= 0:
                findings.append(Finding("error", "bad_petal_detail_edge_bevel", f"{op.target} edge bevel must be positive."))
            if op.mount:
                if float(op.mount.get("radius", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_mount_radius", f"{op.target} mount radius must be positive."))
                if float(op.mount.get("height", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_mount_height", f"{op.target} mount height must be positive."))
        elif isinstance(op, AddPetalScroll):
            petal = op.petal
            for key in ("length", "max_width", "max_thickness"):
                if float(petal.get(key, 0.0)) <= 0:
                    findings.append(Finding("error", "bad_petal_scroll_dimension", f"{op.name} petal {key} must be positive."))
            for key in ("base_width", "tip_width", "min_width", "min_thickness", "tip_thickness"):
                if key in petal and float(petal[key]) <= 0:
                    findings.append(Finding("error", "bad_petal_scroll_dimension", f"{op.name} petal {key} must be positive."))
            if op.scroll.get("type", "volute") != "volute":
                findings.append(Finding("error", "bad_petal_scroll_type", f"{op.name} scroll type must be volute."))
            if float(op.scroll.get("turns", 0.0)) <= 0:
                findings.append(Finding("error", "bad_petal_scroll_turns", f"{op.name} scroll turns must be positive."))
            for key in ("radius_start", "radius_end"):
                if float(op.scroll.get(key, 0.0)) <= 0:
                    findings.append(Finding("error", "bad_petal_scroll_radius", f"{op.name} scroll {key} must be positive."))
            if int(op.scroll.get("samples", 3)) < 3:
                findings.append(Finding("error", "bad_petal_scroll_samples", f"{op.name} scroll samples must be at least 3."))
            if op.scroll.get("direction", "ccw") not in ("cw", "ccw"):
                findings.append(Finding("error", "bad_petal_scroll_direction", f"{op.name} scroll direction must be cw or ccw."))
            if float(op.scroll.get("relief_depth", 0.06)) < 0:
                findings.append(Finding("error", "bad_petal_scroll_relief", f"{op.name} relief_depth must be non-negative."))
            if float(op.scroll.get("curl_depth", 0.12)) < 0:
                findings.append(Finding("error", "bad_petal_scroll_curl", f"{op.name} curl_depth must be non-negative."))
            solid_fill = op.scroll.get("solid_fill")
            if solid_fill and solid_fill.get("enabled", True):
                if solid_fill.get("mode", "center_fan") != "center_fan":
                    findings.append(Finding("error", "bad_petal_scroll_fill_mode", f"{op.name} solid_fill mode must be center_fan."))
                if float(solid_fill.get("front_depth", 0.0)) < 0:
                    findings.append(Finding("error", "bad_petal_scroll_fill_depth", f"{op.name} solid_fill front_depth must be non-negative."))
                if float(solid_fill.get("back_depth", 0.0)) < 0:
                    findings.append(Finding("error", "bad_petal_scroll_fill_depth", f"{op.name} solid_fill back_depth must be non-negative."))
                if "edge_bevel" in solid_fill and float(solid_fill["edge_bevel"]) <= 0:
                    findings.append(Finding("error", "bad_petal_scroll_fill_bevel", f"{op.name} solid_fill edge_bevel must be positive."))
            if op.vein and op.vein.get("enabled", True):
                if float(op.vein.get("bevel_depth", 0.0)) <= 0:
                    findings.append(Finding("error", "bad_petal_scroll_vein", f"{op.name} vein bevel_depth must be positive."))
                start_t = float(op.vein.get("start_t", 0.1))
                end_t = float(op.vein.get("end_t", 0.92))
                if not 0.0 <= start_t <= 1.0 or not 0.0 <= end_t <= 1.0 or end_t <= start_t:
                    findings.append(Finding("error", "bad_petal_scroll_vein_range", f"{op.name} vein start_t/end_t must be ordered within 0..1."))
            try:
                petal_width_at(petal, 0.5)
                petal_thickness_at(petal, 0.5)
                petal_scroll_bounds(petal, op.scroll, op.x, op.y, op.z)
            except (TypeError, ValueError) as exc:
                findings.append(Finding("error", "bad_petal_scroll", f"{op.name}: {exc}"))
        elif isinstance(op, CutFlutes):
            if op.target not in names:
                findings.append(Finding("error", "flute_missing_target", f"CutFlutes target does not exist before cut: {op.target}"))
            if op.count < 12:
                findings.append(Finding("warning", "low_flute_count", f"Flute count looks low: {op.count}"))
            if op.depth <= 0:
                findings.append(Finding("error", "bad_flute_depth", "Flute depth must be positive."))
            if not (0.05 <= op.width_ratio <= 0.9):
                findings.append(Finding("warning", "odd_flute_width_ratio", f"Flute width ratio looks odd: {op.width_ratio}"))

    # Column-specific sanity checks by convention.
    looks_like_column = any(
        getattr(op, "name", "").startswith(("plinth.", "shaft.", "capital."))
        for op in ops
    )
    if looks_like_column:
        shaft = cylinders.get("shaft.tapered_fluted_core")
        if shaft is None:
            findings.append(Finding("error", "missing_shaft", "Expected shaft.tapered_fluted_core."))
        else:
            base_boxes = [op for op in ops if isinstance(op, AddBox) and op.name.startswith("plinth.")]
            if base_boxes:
                widest_base = max(max(op.width, op.depth) for op in base_boxes)
                if widest_base <= shaft.radius * 2:
                    findings.append(Finding("warning", "base_not_wider_than_shaft", "Base should be wider than shaft."))
            caps = [op for op in ops if getattr(op, "name", "").startswith("capital.")]
            if not caps:
                findings.append(Finding("warning", "missing_capital", "No capital parts found."))

    return findings


def validation_report(ops: list[BuildOp]) -> dict:
    findings = validate_ops(ops)
    return {
        "ok": not any(f.severity == "error" for f in findings),
        "finding_count": len(findings),
        "findings": [asdict(f) for f in findings],
    }


def save_validation(path: str, ops: list[BuildOp]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(validation_report(ops), f, indent=2)
        f.write("\n")
