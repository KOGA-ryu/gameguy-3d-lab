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
    AddProfileMoulding,
    AddRing,
    AddSectionStack,
    CutFlutes,
    BuildOp,
)
from .profile_mouldings import SUPPORTED_TERMS
from .sweep_geometry import path_sweep_bounds, profile_points, transformed_profile_points


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
