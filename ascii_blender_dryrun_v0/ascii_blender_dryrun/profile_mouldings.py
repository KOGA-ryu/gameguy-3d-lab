"""
Profile moulding helper compiler.

Source recipes can describe architectural mouldings as named term sequences.
This module expands those terms into deterministic radius/z profile points for
the lower-level AddMoulding operation consumed by ASCII and Blender backends.
"""

from __future__ import annotations

import math
from typing import Any

from .ops import AddMoulding, AddProfileMoulding, BuildOp


CURVED_TERMS = {
    "bead",
    "cavetto",
    "cyma",
    "cyma_recta",
    "cyma_reversa",
    "echinus",
    "scotia",
    "torus",
}
LINEAR_TERMS = {"fillet", "annulet"}
SUPPORTED_TERMS = CURVED_TERMS | LINEAR_TERMS


def compile_profile_mouldings(ops: list[BuildOp]) -> list[BuildOp]:
    """Expand high-level AddProfileMoulding ops into low-level AddMoulding ops."""
    compiled: list[BuildOp] = []
    for op in ops:
        if isinstance(op, AddProfileMoulding):
            compiled.append(compile_profile_moulding(op))
        else:
            compiled.append(op)
    return compiled


def compile_profile_moulding(op: AddProfileMoulding) -> AddMoulding:
    """Compile one named moulding sequence into radius/z profile points."""
    if not op.sequence:
        raise ValueError(f"{op.name} needs at least one profile segment.")

    points: list[dict[str, Any]] = []
    current_z = 0.0
    current_radius: float | None = None

    for index, segment in enumerate(op.sequence):
        term = str(segment.get("term", "")).strip()
        if term not in SUPPORTED_TERMS:
            raise ValueError(f"{op.name} segment {index} has unsupported term: {term!r}")

        height = float(segment.get("height", 0.0))
        if height <= 0:
            raise ValueError(f"{op.name} segment {index} height must be positive.")

        start_radius = segment.get("start_radius", current_radius)
        if start_radius is None:
            raise ValueError(f"{op.name} first segment needs start_radius.")
        start_radius = float(start_radius)

        if "end_radius" in segment:
            end_radius = float(segment["end_radius"])
        elif "radius_delta" in segment:
            end_radius = start_radius + float(segment["radius_delta"])
        else:
            end_radius = start_radius

        if start_radius <= 0 or end_radius <= 0:
            raise ValueError(f"{op.name} segment {index} radii must be positive.")

        steps = int(segment.get("steps", default_steps(term)))
        if steps < 1:
            raise ValueError(f"{op.name} segment {index} steps must be at least 1.")

        if not points:
            points.append(_point(term, current_z, start_radius, "start"))

        for step in range(1, steps + 1):
            t = step / steps
            points.append(
                _point(
                    term,
                    current_z + height * t,
                    _interpolate_radius(term, start_radius, end_radius, t),
                    f"{step:02d}",
                )
            )

        current_z += height
        current_radius = end_radius

    return AddMoulding(
        name=op.name,
        base_z=op.base_z,
        profile=[_rounded_point(point) for point in points],
        x=op.x,
        y=op.y,
        vertices=op.vertices,
        material=op.material,
    )


def default_steps(term: str) -> int:
    if term in LINEAR_TERMS:
        return 1
    if term == "echinus":
        return 6
    if term in {"cyma", "cyma_recta", "cyma_reversa"}:
        return 5
    return 4


def _interpolate_radius(term: str, start_radius: float, end_radius: float, t: float) -> float:
    if term in LINEAR_TERMS:
        eased = t
    elif term in {"torus", "bead"}:
        eased = _smoothstep(t)
    elif term in {"cavetto", "scotia"}:
        eased = 1.0 - math.cos(t * math.pi * 0.5)
    elif term == "echinus":
        eased = _smoothstep(t) ** 0.72
    elif term == "cyma_reversa":
        eased = 1.0 - _smoothstep(1.0 - t)
    else:
        eased = _smoothstep(t)
    return start_radius + (end_radius - start_radius) * eased


def _smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def _point(term: str, z: float, radius: float, suffix: str) -> dict[str, Any]:
    return {
        "term": f"{term}_{suffix}",
        "z": z,
        "radius": radius,
    }


def _rounded_point(point: dict[str, Any]) -> dict[str, Any]:
    return {
        "term": point["term"],
        "z": round(float(point["z"]), 4),
        "radius": round(float(point["radius"]), 4),
    }
