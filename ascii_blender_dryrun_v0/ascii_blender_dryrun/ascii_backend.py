"""
ASCII dry-run backend.

This backend interprets the same build ops that the Blender backend uses.
It produces cheap front/side/top projections so the plan can be inspected
before Blender is opened.

It intentionally renders approximate symbols rather than high art.
The purpose is to catch bad scale, missing parts, broken symmetry, wrong
order, and incorrect footprint.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal

from .ops import (
    AddBox,
    AddCylinder,
    AddMoulding,
    AddPathSweep,
    AddPetalBloom,
    AddRing,
    AddSectionStack,
    CutFlutes,
    BuildOp,
)
from .sweep_geometry import (
    path_sweep_bounds,
    path_sweep_instances,
    petal_bloom_bounds,
    petal_layer_instances,
    petal_width_at,
    section_stack_bounds,
    transformed_profile_points,
)


Projection = Literal["front", "side", "top"]


@dataclass
class Bounds:
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float


def estimate_bounds(ops: Iterable[BuildOp]) -> Bounds:
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for op in ops:
        if isinstance(op, AddBox):
            min_x = min(min_x, op.x - op.width / 2)
            max_x = max(max_x, op.x + op.width / 2)
            min_y = min(min_y, op.y - op.depth / 2)
            max_y = max(max_y, op.y + op.depth / 2)
            min_z = min(min_z, op.z - op.height / 2)
            max_z = max(max_z, op.z + op.height / 2)
        elif isinstance(op, (AddCylinder, AddRing)):
            radius = op.radius + (op.overhang if isinstance(op, AddRing) else 0.0)
            height = op.height if isinstance(op, AddCylinder) else op.tube_height
            min_x = min(min_x, op.x - radius)
            max_x = max(max_x, op.x + radius)
            min_y = min(min_y, op.y - radius)
            max_y = max(max_y, op.y + radius)
            min_z = min(min_z, op.z - height / 2)
            max_z = max(max_z, op.z + height / 2)
        elif isinstance(op, AddMoulding):
            radii = [float(point["radius"]) for point in op.profile if "radius" in point]
            local_zs = [float(point["z"]) for point in op.profile if "z" in point]
            if not radii or not local_zs:
                continue
            radius = max(radii)
            min_x = min(min_x, op.x - radius)
            max_x = max(max_x, op.x + radius)
            min_y = min(min_y, op.y - radius)
            max_y = max(max_y, op.y + radius)
            min_z = min(min_z, op.base_z + min(local_zs))
            max_z = max(max_z, op.base_z + max(local_zs))
        elif isinstance(op, AddSectionStack):
            sx0, sx1, sy0, sy1, sz0, sz1 = section_stack_bounds(op.sections, op.x, op.y)
            min_x = min(min_x, sx0)
            max_x = max(max_x, sx1)
            min_y = min(min_y, sy0)
            max_y = max(max_y, sy1)
            min_z = min(min_z, sz0)
            max_z = max(max_z, sz1)
        elif isinstance(op, AddPathSweep):
            sx0, sx1, sy0, sy1, sz0, sz1 = path_sweep_bounds(
                op.path, op.profile, op.taper, op.repeat
            )
            min_x = min(min_x, sx0)
            max_x = max(max_x, sx1)
            min_y = min(min_y, sy0)
            max_y = max(max_y, sy1)
            min_z = min(min_z, sz0)
            max_z = max(max_z, sz1)
        elif isinstance(op, AddPetalBloom):
            sx0, sx1, sy0, sy1, sz0, sz1 = petal_bloom_bounds(
                op.petal, op.layers, op.x, op.y, op.z
            )
            min_x = min(min_x, sx0)
            max_x = max(max_x, sx1)
            min_y = min(min_y, sy0)
            max_y = max(max_y, sy1)
            min_z = min(min_z, sz0)
            max_z = max(max_z, sz1)

    if min_x == float("inf"):
        return Bounds(-1, 1, -1, 1, 0, 1)
    pad = 2.0
    return Bounds(min_x - pad, max_x + pad, min_y - pad, max_y + pad, min_z - pad, max_z + pad)


class AsciiCanvas:
    def __init__(self, width: int = 96, height: int = 72):
        self.width = width
        self.height = height
        self.pixels = [[" " for _ in range(width)] for _ in range(height)]

    def set(self, x: int, y: int, ch: str) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = ch

    def line_h(self, y: int, x1: int, x2: int, ch: str = "─") -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.set(x, y, ch)

    def line_v(self, x: int, y1: int, y2: int, ch: str = "│") -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.set(x, y, ch)

    def rect(self, x1: int, y1: int, x2: int, y2: int, fill: str = "░", border: str = "█") -> None:
        xa, xb = sorted((x1, x2))
        ya, yb = sorted((y1, y2))
        for y in range(ya, yb + 1):
            for x in range(xa, xb + 1):
                if x in (xa, xb) or y in (ya, yb):
                    self.set(x, y, border)
                else:
                    self.set(x, y, fill)

    def circle(self, cx: int, cy: int, r: int, fill: str = "▓", border: str = "█") -> None:
        if r <= 0:
            return
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if d <= r:
                    self.set(x, y, border if abs(d - r) < 1.0 else fill)

    def text(self, x: int, y: int, s: str) -> None:
        for i, ch in enumerate(s):
            self.set(x + i, y, ch)

    def render(self) -> str:
        return "\n".join("".join(row).rstrip() for row in self.pixels)


class AsciiBackend:
    def __init__(self, width: int = 96, height: int = 72):
        self.width = width
        self.height = height

    def render_projection(self, ops: list[BuildOp], projection: Projection) -> str:
        bounds = estimate_bounds(ops)
        c = AsciiCanvas(self.width, self.height)

        def map_front(x: float, z: float) -> tuple[int, int]:
            sx = (x - bounds.min_x) / max(1e-9, bounds.max_x - bounds.min_x)
            sz = (z - bounds.min_z) / max(1e-9, bounds.max_z - bounds.min_z)
            return round(sx * (self.width - 1)), round((1.0 - sz) * (self.height - 1))

        def map_side(y: float, z: float) -> tuple[int, int]:
            sy = (y - bounds.min_y) / max(1e-9, bounds.max_y - bounds.min_y)
            sz = (z - bounds.min_z) / max(1e-9, bounds.max_z - bounds.min_z)
            return round(sy * (self.width - 1)), round((1.0 - sz) * (self.height - 1))

        def map_top(x: float, y: float) -> tuple[int, int]:
            sx = (x - bounds.min_x) / max(1e-9, bounds.max_x - bounds.min_x)
            sy = (y - bounds.min_y) / max(1e-9, bounds.max_y - bounds.min_y)
            return round(sx * (self.width - 1)), round(sy * (self.height - 1))

        for op in ops:
            if projection == "front":
                self._draw_front(c, map_front, op)
            elif projection == "side":
                self._draw_side(c, map_side, op)
            elif projection == "top":
                self._draw_top(c, map_top, op)

        title = f"{projection.upper()} PROJECTION"
        c.text(1, 1, title)
        return c.render()

    def _draw_cylinder_elevation(
        self,
        c: AsciiCanvas,
        mapper,
        center_axis: float,
        center_z: float,
        radius: float,
        top_radius: float,
        height: float,
        entasis: bool,
    ) -> None:
        segments = 20 if entasis or abs(top_radius - radius) > 1e-9 else 1
        left_points: list[tuple[int, int]] = []
        right_points: list[tuple[int, int]] = []
        for segment in range(segments + 1):
            t = segment / segments
            z = center_z - height / 2 + height * t
            linear_radius = radius + (top_radius - radius) * t
            bulge = math.sin(math.pi * t) * radius * 0.045 if entasis else 0.0
            rr = max(0.001, linear_radius + bulge)
            left = mapper(center_axis - rr, z)
            right = mapper(center_axis + rr, z)
            left_points.append(left)
            right_points.append(right)
            c.line_h(left[1], left[0], right[0], "▒")
        c.line_h(left_points[0][1], left_points[0][0], right_points[0][0], "▄")
        c.line_h(left_points[-1][1], left_points[-1][0], right_points[-1][0], "▀")
        for index in range(segments):
            self._line(c, left_points[index][0], left_points[index][1], left_points[index + 1][0], left_points[index + 1][1], "█")
            self._line(c, right_points[index][0], right_points[index][1], right_points[index + 1][0], right_points[index + 1][1], "█")

    def _draw_moulding_elevation(
        self,
        c: AsciiCanvas,
        mapper,
        center_axis: float,
        base_z: float,
        profile: list[dict],
    ) -> None:
        left_points: list[tuple[int, int]] = []
        right_points: list[tuple[int, int]] = []
        for point in profile:
            radius = float(point["radius"])
            z = base_z + float(point["z"])
            left = mapper(center_axis - radius, z)
            right = mapper(center_axis + radius, z)
            left_points.append(left)
            right_points.append(right)
            c.line_h(left[1], left[0], right[0], "▓")
        for index in range(len(left_points) - 1):
            self._line(c, left_points[index][0], left_points[index][1], left_points[index + 1][0], left_points[index + 1][1], "█")
            self._line(c, right_points[index][0], right_points[index][1], right_points[index + 1][0], right_points[index + 1][1], "█")

    def _draw_section_stack_elevation(self, c: AsciiCanvas, mapper, op: AddSectionStack, axis: str) -> None:
        left_points: list[tuple[int, int]] = []
        right_points: list[tuple[int, int]] = []
        for section in op.sections:
            points = transformed_profile_points(section, {"type": "circle", "radius": 1.0}, op.vertices)
            center = op.x if axis == "x" else op.y
            center += float(section.get(axis, section.get(f"{axis}_offset", 0.0)))
            local_values = [point[0] if axis == "x" else point[1] for point in points]
            z = float(section["z"])
            left = mapper(center + min(local_values), z)
            right = mapper(center + max(local_values), z)
            left_points.append(left)
            right_points.append(right)
            c.line_h(left[1], left[0], right[0], "▒")
        for index in range(len(left_points) - 1):
            self._line(c, left_points[index][0], left_points[index][1], left_points[index + 1][0], left_points[index + 1][1], "█")
            self._line(c, right_points[index][0], right_points[index][1], right_points[index + 1][0], right_points[index + 1][1], "█")

    def _draw_path_sweep(self, c: AsciiCanvas, mapper, op: AddPathSweep, projection: Projection) -> None:
        for instance in path_sweep_instances(op.path, op.repeat):
            mapped: list[tuple[int, int]] = []
            for point in instance:
                if projection == "front":
                    mapped.append(mapper(point["x"], point["z"]))
                elif projection == "side":
                    mapped.append(mapper(point["y"], point["z"]))
                else:
                    mapped.append(mapper(point["x"], point["y"]))
            for start, end in zip(mapped, mapped[1:]):
                self._line(c, start[0], start[1], end[0], end[1], "▓")

    def _draw_petal_bloom(self, c: AsciiCanvas, mapper, op: AddPetalBloom, projection: Projection) -> None:
        for instance in petal_layer_instances(op.layers):
            centerline = [
                self._petal_ascii_point(op, instance, t_index / 8, 0.0, projection, mapper)
                for t_index in range(9)
            ]
            left_edge = [
                self._petal_ascii_point(op, instance, t_index / 8, -1.0, projection, mapper)
                for t_index in range(9)
            ]
            right_edge = [
                self._petal_ascii_point(op, instance, t_index / 8, 1.0, projection, mapper)
                for t_index in range(9)
            ]
            for points, ch in ((left_edge, "░"), (right_edge, "░"), (centerline, "▓")):
                for start, end in zip(points, points[1:]):
                    self._line(c, start[0], start[1], end[0], end[1], ch)
            if projection == "top":
                root = centerline[0]
                tip = centerline[-1]
                c.set(root[0], root[1], "•")
                c.set(tip[0], tip[1], "◆")

    def _petal_ascii_point(
        self,
        op: AddPetalBloom,
        instance: dict[str, float],
        t: float,
        side: float,
        projection: Projection,
        mapper,
    ) -> tuple[int, int]:
        length = float(op.petal["length"]) * instance["length_scale"]
        width = petal_width_at(op.petal, t) * instance["width_scale"]
        angle = instance["angle"] + (instance["tip_angle"] - instance["angle"]) * t
        radial_x = math.cos(angle)
        radial_y = math.sin(angle)
        tangent_x = -radial_y
        tangent_y = radial_x
        distance = instance["radius"] + length * t
        side_offset = side * width * 0.5
        bend_start = float(op.petal.get("bend_start_t", 0.45))
        bend_t = max(0.0, (t - bend_start) / max(1e-9, 1.0 - bend_start))
        bend_height = math.sin(math.radians(instance["bend_angle_deg"])) * length * 0.42
        curl_height = math.sin(math.radians(abs(instance["curl_angle_deg"]))) * width * 0.24
        z = op.z + instance["z_offset"] + bend_height * (bend_t ** 1.35)
        z += abs(side) * curl_height * (t ** 1.25)
        x = op.x + radial_x * distance + tangent_x * side_offset
        y = op.y + radial_y * distance + tangent_y * side_offset
        if projection == "front":
            return mapper(x, z)
        if projection == "side":
            return mapper(y, z)
        return mapper(x, y)

    def _draw_front(self, c: AsciiCanvas, mapper, op: BuildOp) -> None:
        if isinstance(op, AddBox):
            x1, y1 = mapper(op.x - op.width / 2, op.z - op.height / 2)
            x2, y2 = mapper(op.x + op.width / 2, op.z + op.height / 2)
            c.rect(x1, y1, x2, y2, fill="░", border="█")
        elif isinstance(op, AddCylinder):
            self._draw_cylinder_elevation(c, mapper, op.x, op.z, op.radius, op.taper_top_radius or op.radius, op.height, op.entasis)
        elif isinstance(op, AddRing):
            r = op.radius + op.overhang
            h = op.tube_height
            x1, y1 = mapper(op.x - r, op.z - h / 2)
            x2, y2 = mapper(op.x + r, op.z + h / 2)
            c.rect(x1, y1, x2, y2, fill="▓", border="█")
        elif isinstance(op, AddMoulding):
            self._draw_moulding_elevation(c, mapper, op.x, op.base_z, op.profile)
        elif isinstance(op, AddSectionStack):
            self._draw_section_stack_elevation(c, mapper, op, "x")
        elif isinstance(op, AddPathSweep):
            self._draw_path_sweep(c, mapper, op, "front")
        elif isinstance(op, AddPetalBloom):
            self._draw_petal_bloom(c, mapper, op, "front")
        elif isinstance(op, CutFlutes):
            # Front preview: rhythm markers only, because actual radial boolean
            # cuts belong to the Blender backend.
            count = min(op.count, 32)
            for i in range(count):
                # distribute visible grooves across middle half of canvas
                x = round(c.width * (0.30 + 0.40 * (i / max(1, count - 1))))
                c.line_v(x, round(c.height * 0.20), round(c.height * 0.78), "░")

    def _draw_side(self, c: AsciiCanvas, mapper, op: BuildOp) -> None:
        if isinstance(op, AddBox):
            x1, y1 = mapper(op.y - op.depth / 2, op.z - op.height / 2)
            x2, y2 = mapper(op.y + op.depth / 2, op.z + op.height / 2)
            c.rect(x1, y1, x2, y2, fill="░", border="█")
        elif isinstance(op, AddCylinder):
            self._draw_cylinder_elevation(c, mapper, op.y, op.z, op.radius, op.taper_top_radius or op.radius, op.height, op.entasis)
        elif isinstance(op, AddRing):
            r = op.radius + op.overhang
            h = op.tube_height
            x1, y1 = mapper(op.y - r, op.z - h / 2)
            x2, y2 = mapper(op.y + r, op.z + h / 2)
            c.rect(x1, y1, x2, y2, fill="▓", border="█")
        elif isinstance(op, AddMoulding):
            self._draw_moulding_elevation(c, mapper, op.y, op.base_z, op.profile)
        elif isinstance(op, AddSectionStack):
            self._draw_section_stack_elevation(c, mapper, op, "y")
        elif isinstance(op, AddPathSweep):
            self._draw_path_sweep(c, mapper, op, "side")
        elif isinstance(op, AddPetalBloom):
            self._draw_petal_bloom(c, mapper, op, "side")

    def _draw_top(self, c: AsciiCanvas, mapper, op: BuildOp) -> None:
        if isinstance(op, AddBox):
            x1, y1 = mapper(op.x - op.width / 2, op.y - op.depth / 2)
            x2, y2 = mapper(op.x + op.width / 2, op.y + op.depth / 2)
            c.rect(x1, y1, x2, y2, fill="░", border="█")
        elif isinstance(op, AddCylinder):
            cx, cy = mapper(op.x, op.y)
            rx, _ = mapper(op.x + op.radius, op.y)
            r = abs(rx - cx)
            c.circle(cx, cy, r, fill="▒", border="█")
        elif isinstance(op, AddRing):
            cx, cy = mapper(op.x, op.y)
            rx, _ = mapper(op.x + op.radius + op.overhang, op.y)
            r = abs(rx - cx)
            c.circle(cx, cy, r, fill="▓", border="█")
        elif isinstance(op, AddMoulding):
            cx, cy = mapper(op.x, op.y)
            radius = max(float(point["radius"]) for point in op.profile)
            rx, _ = mapper(op.x + radius, op.y)
            r = abs(rx - cx)
            c.circle(cx, cy, r, fill="▓", border="█")
        elif isinstance(op, AddSectionStack):
            for section in op.sections:
                points = transformed_profile_points(
                    section, {"type": "circle", "radius": 1.0}, op.vertices
                )
                center_x = op.x + float(section.get("x", section.get("x_offset", 0.0)))
                center_y = op.y + float(section.get("y", section.get("y_offset", 0.0)))
                mapped = [mapper(center_x + px, center_y + py) for px, py in points]
                for start, end in zip(mapped, mapped[1:] + mapped[:1]):
                    self._line(c, start[0], start[1], end[0], end[1], "▒")
        elif isinstance(op, AddPathSweep):
            self._draw_path_sweep(c, mapper, op, "top")
        elif isinstance(op, AddPetalBloom):
            self._draw_petal_bloom(c, mapper, op, "top")
        elif isinstance(op, CutFlutes):
            cx, cy = c.width // 2, c.height // 2
            r1 = round(min(c.width, c.height) * 0.12)
            r2 = round(min(c.width, c.height) * 0.28)
            for i in range(op.count):
                a = 2 * math.pi * i / op.count
                x1 = round(cx + math.cos(a) * r1)
                y1 = round(cy + math.sin(a) * r1)
                x2 = round(cx + math.cos(a) * r2)
                y2 = round(cy + math.sin(a) * r2)
                self._line(c, x1, y1, x2, y2, "░")

    @staticmethod
    def _line(c: AsciiCanvas, x1: int, y1: int, x2: int, y2: int, ch: str) -> None:
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        x, y = x1, y1
        while True:
            c.set(x, y, ch)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
