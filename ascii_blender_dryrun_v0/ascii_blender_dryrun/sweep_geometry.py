"""
Deterministic geometry helpers for section stacks and path sweeps.

These helpers are intentionally small. They let the dry-run package reason
about twisted bars and filigree/rose scrolls without involving Blender.
"""

from __future__ import annotations

import math
from typing import Any


def profile_points(profile: dict[str, Any], vertices: int = 32) -> list[tuple[float, float]]:
    profile_type = str(profile.get("type", "circle"))
    vertices = max(3, int(profile.get("vertices", vertices)))

    if profile_type == "square":
        half = float(profile.get("radius", profile.get("size", 1.0))) * 0.5
        return [(-half, -half), (half, -half), (half, half), (-half, half)]
    if profile_type == "octagon":
        return _regular_polygon(8, float(profile.get("radius", 1.0)), 0.0)
    if profile_type == "circle":
        return _regular_polygon(vertices, float(profile.get("radius", 1.0)), 0.0)
    if profile_type == "oval":
        radius_x = float(profile.get("radius_x", profile.get("radius", 1.0)))
        radius_y = float(profile.get("radius_y", profile.get("radius", 0.5)))
        return [
            (math.cos(math.tau * index / vertices) * radius_x,
             math.sin(math.tau * index / vertices) * radius_y)
            for index in range(vertices)
        ]
    if profile_type == "ribbon":
        half_w = float(profile.get("width", 1.0)) * 0.5
        half_h = float(profile.get("height", 0.12)) * 0.5
        return [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
    raise ValueError(f"Unsupported profile type: {profile_type!r}")


def section_stack_bounds(sections: list[dict[str, Any]], origin_x: float, origin_y: float) -> tuple[float, float, float, float, float, float]:
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    for section in sections:
        profile = section.get("profile", {"type": "circle", "radius": section.get("radius", 1.0)})
        points = transformed_profile_points(section, profile)
        x = origin_x + float(section.get("x", section.get("x_offset", 0.0)))
        y = origin_y + float(section.get("y", section.get("y_offset", 0.0)))
        z = float(section["z"])
        for px, py in points:
            min_x = min(min_x, x + px)
            max_x = max(max_x, x + px)
            min_y = min(min_y, y + py)
            max_y = max(max_y, y + py)
        min_z = min(min_z, z)
        max_z = max(max_z, z)
    return min_x, max_x, min_y, max_y, min_z, max_z


def transformed_profile_points(section: dict[str, Any], default_profile: dict[str, Any], vertices: int = 32) -> list[tuple[float, float]]:
    profile = dict(default_profile)
    profile.update(section.get("profile", {}))
    if "radius" in section:
        profile["radius"] = section["radius"]
    points = profile_points(profile, int(section.get("vertices", vertices)))
    scale = float(section.get("scale", 1.0))
    rotation = math.radians(float(section.get("rotation_deg", 0.0)))
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    return [
        ((px * scale) * cos_r - (py * scale) * sin_r,
         (px * scale) * sin_r + (py * scale) * cos_r)
        for px, py in points
    ]


def path_sweep_samples(op_path: dict[str, Any]) -> list[dict[str, float]]:
    path_type = str(op_path.get("type", "spiral"))
    samples = max(2, int(op_path.get("samples", 32)))
    if path_type != "spiral":
        raise ValueError(f"Unsupported path type: {path_type!r}")

    turns = float(op_path.get("turns", 1.0))
    radius_start = float(op_path.get("radius_start", 0.1))
    radius_end = float(op_path.get("radius_end", 1.0))
    height = float(op_path.get("height", 0.0))
    center_x = float(op_path.get("x", 0.0))
    center_y = float(op_path.get("y", 0.0))
    base_z = float(op_path.get("z", 0.0))
    start_angle = math.radians(float(op_path.get("start_angle_deg", 0.0)))
    direction = -1.0 if str(op_path.get("direction", "ccw")) == "cw" else 1.0

    points: list[dict[str, float]] = []
    for index in range(samples):
        t = index / max(1, samples - 1)
        radius = radius_start + (radius_end - radius_start) * t
        angle = start_angle + direction * math.tau * turns * t
        points.append({
            "t": t,
            "x": center_x + math.cos(angle) * radius,
            "y": center_y + math.sin(angle) * radius,
            "z": base_z + height * t,
            "angle": angle,
        })
    return points


def path_sweep_instances(path: dict[str, Any], repeat: dict[str, Any] | None) -> list[list[dict[str, float]]]:
    base = path_sweep_samples(path)
    if not repeat:
        return [base]
    if str(repeat.get("type", "none")) != "radial":
        raise ValueError(f"Unsupported repeat type: {repeat.get('type')!r}")

    count = max(1, int(repeat.get("count", 1)))
    center_x = float(repeat.get("x", path.get("x", 0.0)))
    center_y = float(repeat.get("y", path.get("y", 0.0)))
    result: list[list[dict[str, float]]] = []
    for repeat_index in range(count):
        angle = math.tau * repeat_index / count
        cos_r = math.cos(angle)
        sin_r = math.sin(angle)
        instance: list[dict[str, float]] = []
        for point in base:
            dx = point["x"] - center_x
            dy = point["y"] - center_y
            instance.append({
                **point,
                "x": center_x + dx * cos_r - dy * sin_r,
                "y": center_y + dx * sin_r + dy * cos_r,
                "angle": point["angle"] + angle,
            })
        result.append(instance)
    return result


def taper_scale(taper: list[dict[str, Any]] | None, t: float) -> float:
    if not taper:
        return 1.0
    points = sorted((float(point["t"]), float(point["scale"])) for point in taper)
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]
    for (t0, s0), (t1, s1) in zip(points, points[1:]):
        if t0 <= t <= t1:
            span = max(1e-9, t1 - t0)
            local = (t - t0) / span
            return s0 + (s1 - s0) * local
    return points[-1][1]


def path_sweep_bounds(path: dict[str, Any], profile: dict[str, Any], taper: list[dict[str, Any]] | None, repeat: dict[str, Any] | None) -> tuple[float, float, float, float, float, float]:
    instances = path_sweep_instances(path, repeat)
    base_points = profile_points(profile)
    base_radius = max(math.hypot(x, y) for x, y in base_points)
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    for instance in instances:
        for point in instance:
            radius = base_radius * taper_scale(taper, point["t"])
            min_x = min(min_x, point["x"] - radius)
            max_x = max(max_x, point["x"] + radius)
            min_y = min(min_y, point["y"] - radius)
            max_y = max(max_y, point["y"] + radius)
            min_z = min(min_z, point["z"] - radius)
            max_z = max(max_z, point["z"] + radius)
    return min_x, max_x, min_y, max_y, min_z, max_z


def _regular_polygon(vertices: int, radius: float, rotation: float) -> list[tuple[float, float]]:
    return [
        (math.cos(math.tau * index / vertices + rotation) * radius,
         math.sin(math.tau * index / vertices + rotation) * radius)
        for index in range(vertices)
    ]
