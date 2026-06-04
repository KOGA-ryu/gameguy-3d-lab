"""
Validation pass for build plans.

This is deliberately boring and blunt. It should catch the dumb failures
before Blender gets involved.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable

from .ops import AddBox, AddCylinder, AddRing, CutFlutes, BuildOp


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
