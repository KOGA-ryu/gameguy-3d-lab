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
    AddPetalBloomDetail,
    AddPetalScroll,
    AddRing,
    AddSectionStack,
    AddSphere,
    CutFlutes,
    BuildOp,
)
from .sweep_geometry import (
    path_sweep_bounds,
    path_sweep_instances,
    petal_bloom_bounds,
    petal_layer_instances,
    petal_scroll_bounds,
    petal_scroll_path_points,
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


def box_z_center(op: AddBox) -> float:
    return op.z + op.height / 2 if op.z_mode == "base" else op.z


def cylinder_z_center(op: AddCylinder) -> float:
    return op.z + op.height / 2 if op.z_mode == "base" and op.axis == "z" else op.z


def cylinder_extents(op: AddCylinder) -> tuple[float, float, float, float, float, float]:
    z = cylinder_z_center(op)
    radius = op.radius
    if op.axis == "x":
        return (
            op.x - op.height / 2,
            op.x + op.height / 2,
            op.y - radius,
            op.y + radius,
            z - radius,
            z + radius,
        )
    if op.axis == "y":
        return (
            op.x - radius,
            op.x + radius,
            op.y - op.height / 2,
            op.y + op.height / 2,
            z - radius,
            z + radius,
        )
    return (
        op.x - radius,
        op.x + radius,
        op.y - radius,
        op.y + radius,
        z - op.height / 2,
        z + op.height / 2,
    )


def estimate_bounds(ops: Iterable[BuildOp]) -> Bounds:
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    bloom_bounds: dict[str, tuple[float, float, float, float, float, float]] = {}

    for op in ops:
        if isinstance(op, AddBox):
            z = box_z_center(op)
            min_x = min(min_x, op.x - op.width / 2)
            max_x = max(max_x, op.x + op.width / 2)
            min_y = min(min_y, op.y - op.depth / 2)
            max_y = max(max_y, op.y + op.depth / 2)
            min_z = min(min_z, z - op.height / 2)
            max_z = max(max_z, z + op.height / 2)
        elif isinstance(op, AddCylinder):
            x0, x1, y0, y1, z0, z1 = cylinder_extents(op)
            min_x = min(min_x, x0)
            max_x = max(max_x, x1)
            min_y = min(min_y, y0)
            max_y = max(max_y, y1)
            min_z = min(min_z, z0)
            max_z = max(max_z, z1)
        elif isinstance(op, AddSphere):
            min_x = min(min_x, op.x - op.radius)
            max_x = max(max_x, op.x + op.radius)
            min_y = min(min_y, op.y - op.radius)
            max_y = max(max_y, op.y + op.radius)
            min_z = min(min_z, op.z - op.radius)
            max_z = max(max_z, op.z + op.radius)
        elif isinstance(op, AddRing):
            radius = op.radius + op.overhang
            min_x = min(min_x, op.x - radius)
            max_x = max(max_x, op.x + radius)
            min_y = min(min_y, op.y - radius)
            max_y = max(max_y, op.y + radius)
            min_z = min(min_z, op.z - op.tube_height / 2)
            max_z = max(max_z, op.z + op.tube_height / 2)
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
            bloom_bounds[op.name] = (sx0, sx1, sy0, sy1, sz0, sz1)
            min_x = min(min_x, sx0)
            max_x = max(max_x, sx1)
            min_y = min(min_y, sy0)
            max_y = max(max_y, sy1)
            min_z = min(min_z, sz0)
            max_z = max(max_z, sz1)
        elif isinstance(op, AddPetalBloomDetail) and op.target in bloom_bounds:
            sx0, sx1, sy0, sy1, sz0, sz1 = bloom_bounds[op.target]
            cx = (sx0 + sx1) * 0.5
            cy = (sy0 + sy1) * 0.5
            radius = 0.0
            if op.mount:
                radius = max(radius, float(op.mount.get("radius", 0.0)))
                sz0 -= float(op.mount.get("height", 0.0))
            if op.center_boss:
                radius = max(radius, float(op.center_boss.get("radius", 0.0)))
                sz1 += float(op.center_boss.get("height", op.center_boss.get("radius", 0.0)))
            sx0 = min(sx0, cx - radius)
            sx1 = max(sx1, cx + radius)
            sy0 = min(sy0, cy - radius)
            sy1 = max(sy1, cy + radius)
            min_x = min(min_x, sx0)
            max_x = max(max_x, sx1)
            min_y = min(min_y, sy0)
            max_y = max(max_y, sy1)
            min_z = min(min_z, sz0)
            max_z = max(max_z, sz1)
        elif isinstance(op, AddPetalScroll):
            sx0, sx1, sy0, sy1, sz0, sz1 = petal_scroll_bounds(
                op.petal, op.scroll, op.x, op.y, op.z
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
        self._bloom_lookup = {op.name: op for op in ops if isinstance(op, AddPetalBloom)}

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

    def _draw_petal_detail(
        self,
        c: AsciiCanvas,
        mapper,
        op: AddPetalBloomDetail,
        projection: Projection,
    ) -> None:
        target = getattr(self, "_bloom_lookup", {}).get(op.target)
        if target is None:
            return
        if projection == "top":
            cx, cy = mapper(target.x, target.y)
            if op.mount:
                mx, _ = mapper(target.x + float(op.mount.get("radius", 0.0)), target.y)
                c.circle(cx, cy, abs(mx - cx), fill=" ", border="▒")
            if op.veins and op.veins.get("enabled", True):
                for layer in target.layers:
                    count = max(1, int(layer["count"]))
                    radius = float(layer.get("radius", 0.0))
                    length = float(target.petal["length"]) * float(layer.get("length_scale", 1.0))
                    for index in range(count):
                        angle = math.radians(float(layer.get("spiral_offset_deg", 0.0)))
                        angle += math.tau * index / count
                        x1 = target.x + math.cos(angle) * radius
                        y1 = target.y + math.sin(angle) * radius
                        x2 = target.x + math.cos(angle) * (radius + length * 0.82)
                        y2 = target.y + math.sin(angle) * (radius + length * 0.82)
                        p1 = mapper(x1, y1)
                        p2 = mapper(x2, y2)
                        self._line(c, p1[0], p1[1], p2[0], p2[1], "╎")
            if op.center_boss:
                bx, _ = mapper(target.x + float(op.center_boss.get("radius", 0.0)), target.y)
                c.circle(cx, cy, abs(bx - cx), fill="●", border="█")
        else:
            bounds = petal_bloom_bounds(target.petal, target.layers, target.x, target.y, target.z)
            center_axis = target.x if projection == "front" else target.y
            z_top = bounds[5]
            if op.mount:
                radius = float(op.mount.get("radius", 0.0))
                height = float(op.mount.get("height", 0.0))
                x1, y1 = mapper(center_axis - radius, bounds[4] - height)
                x2, y2 = mapper(center_axis + radius, bounds[4])
                c.rect(x1, y1, x2, y2, fill="▒", border="█")
            if op.center_boss:
                radius = float(op.center_boss.get("radius", 0.0))
                height = float(op.center_boss.get("height", radius))
                x1, y1 = mapper(center_axis - radius, z_top)
                x2, y2 = mapper(center_axis + radius, z_top + height)
                c.rect(x1, y1, x2, y2, fill="●", border="█")

    def _draw_petal_scroll(self, c: AsciiCanvas, mapper, op: AddPetalScroll, projection: Projection) -> None:
        path = petal_scroll_path_points(op.scroll, op.x, op.y, op.z)
        centerline: list[tuple[int, int]] = []
        left_edge: list[tuple[int, int]] = []
        right_edge: list[tuple[int, int]] = []
        relief_depth = float(op.scroll.get("relief_depth", 0.06))
        curl_depth = float(op.scroll.get("curl_depth", 0.12))

        for index, point in enumerate(path):
            previous = path[max(0, index - 1)]
            next_point = path[min(len(path) - 1, index + 1)]
            tx = next_point["x"] - previous["x"]
            tz = next_point["z"] - previous["z"]
            length = max(1e-9, math.hypot(tx, tz))
            nx = -tz / length
            nz = tx / length
            t = point["t"]
            width = petal_width_at(op.petal, t)
            if projection == "front":
                centerline.append(mapper(point["x"], point["z"]))
                left_edge.append(mapper(point["x"] - nx * width * 0.5, point["z"] - nz * width * 0.5))
                right_edge.append(mapper(point["x"] + nx * width * 0.5, point["z"] + nz * width * 0.5))
            elif projection == "side":
                depth = op.y + relief_depth + curl_depth * (t ** 1.2)
                centerline.append(mapper(depth, point["z"]))
                left_edge.append(mapper(depth + curl_depth * 0.35, point["z"] - width * 0.35))
                right_edge.append(mapper(depth + curl_depth * 0.35, point["z"] + width * 0.35))
            else:
                depth = op.y + relief_depth + curl_depth * (t ** 1.2)
                centerline.append(mapper(point["x"], depth))
                left_edge.append(mapper(point["x"] - nx * width * 0.5, depth + curl_depth * 0.25))
                right_edge.append(mapper(point["x"] + nx * width * 0.5, depth + curl_depth * 0.25))

        solid_fill = op.scroll.get("solid_fill")
        if projection == "front" and solid_fill and solid_fill.get("enabled", True) and centerline:
            vertical_lift = float(op.scroll.get("vertical_lift", 0.45))
            fill_center = mapper(op.x, op.z + vertical_lift * 0.55)
            for point in left_edge[::2] + right_edge[::2] + centerline[::3]:
                self._line(c, fill_center[0], fill_center[1], point[0], point[1], "▒")

        for points, ch in ((left_edge, "░"), (right_edge, "░"), (centerline, "▓")):
            for start, end in zip(points, points[1:]):
                self._line(c, start[0], start[1], end[0], end[1], ch)
        if op.vein and op.vein.get("enabled", True):
            for start, end in zip(centerline, centerline[1:]):
                self._line(c, start[0], start[1], end[0], end[1], "╎")
        if centerline:
            c.set(centerline[0][0], centerline[0][1], "•")
            c.set(centerline[-1][0], centerline[-1][1], "◆")

    def _draw_front(self, c: AsciiCanvas, mapper, op: BuildOp) -> None:
        if isinstance(op, AddBox):
            z = box_z_center(op)
            x1, y1 = mapper(op.x - op.width / 2, z - op.height / 2)
            x2, y2 = mapper(op.x + op.width / 2, z + op.height / 2)
            c.rect(x1, y1, x2, y2, fill="░", border="█")
        elif isinstance(op, AddCylinder):
            z = cylinder_z_center(op)
            if op.axis == "x":
                x1, y1 = mapper(op.x - op.height / 2, z - op.radius)
                x2, y2 = mapper(op.x + op.height / 2, z + op.radius)
                c.rect(x1, y1, x2, y2, fill="▒", border="█")
            elif op.axis == "y":
                cx, cy = mapper(op.x, z)
                rx, _ = mapper(op.x + op.radius, z)
                c.circle(cx, cy, abs(rx - cx), fill="▒", border="█")
            else:
                self._draw_cylinder_elevation(c, mapper, op.x, z, op.radius, op.taper_top_radius or op.radius, op.height, op.entasis)
        elif isinstance(op, AddSphere):
            cx, cy = mapper(op.x, op.z)
            rx, _ = mapper(op.x + op.radius, op.z)
            c.circle(cx, cy, abs(rx - cx), fill="▒", border="█")
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
        elif isinstance(op, AddPetalBloomDetail):
            self._draw_petal_detail(c, mapper, op, "front")
        elif isinstance(op, AddPetalScroll):
            self._draw_petal_scroll(c, mapper, op, "front")
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
            z = box_z_center(op)
            x1, y1 = mapper(op.y - op.depth / 2, z - op.height / 2)
            x2, y2 = mapper(op.y + op.depth / 2, z + op.height / 2)
            c.rect(x1, y1, x2, y2, fill="░", border="█")
        elif isinstance(op, AddCylinder):
            z = cylinder_z_center(op)
            if op.axis == "x":
                cx, cy = mapper(op.y, z)
                rx, _ = mapper(op.y + op.radius, z)
                c.circle(cx, cy, abs(rx - cx), fill="▒", border="█")
            elif op.axis == "y":
                x1, y1 = mapper(op.y - op.height / 2, z - op.radius)
                x2, y2 = mapper(op.y + op.height / 2, z + op.radius)
                c.rect(x1, y1, x2, y2, fill="▒", border="█")
            else:
                self._draw_cylinder_elevation(c, mapper, op.y, z, op.radius, op.taper_top_radius or op.radius, op.height, op.entasis)
        elif isinstance(op, AddSphere):
            cx, cy = mapper(op.y, op.z)
            rx, _ = mapper(op.y + op.radius, op.z)
            c.circle(cx, cy, abs(rx - cx), fill="▒", border="█")
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
        elif isinstance(op, AddPetalBloomDetail):
            self._draw_petal_detail(c, mapper, op, "side")
        elif isinstance(op, AddPetalScroll):
            self._draw_petal_scroll(c, mapper, op, "side")

    def _draw_top(self, c: AsciiCanvas, mapper, op: BuildOp) -> None:
        if isinstance(op, AddBox):
            x1, y1 = mapper(op.x - op.width / 2, op.y - op.depth / 2)
            x2, y2 = mapper(op.x + op.width / 2, op.y + op.depth / 2)
            c.rect(x1, y1, x2, y2, fill="░", border="█")
        elif isinstance(op, AddCylinder):
            if op.axis == "x":
                x1, y1 = mapper(op.x - op.height / 2, op.y - op.radius)
                x2, y2 = mapper(op.x + op.height / 2, op.y + op.radius)
                c.rect(x1, y1, x2, y2, fill="▒", border="█")
            elif op.axis == "y":
                x1, y1 = mapper(op.x - op.radius, op.y - op.height / 2)
                x2, y2 = mapper(op.x + op.radius, op.y + op.height / 2)
                c.rect(x1, y1, x2, y2, fill="▒", border="█")
            else:
                cx, cy = mapper(op.x, op.y)
                rx, _ = mapper(op.x + op.radius, op.y)
                r = abs(rx - cx)
                c.circle(cx, cy, r, fill="▒", border="█")
        elif isinstance(op, AddSphere):
            cx, cy = mapper(op.x, op.y)
            rx, _ = mapper(op.x + op.radius, op.y)
            c.circle(cx, cy, abs(rx - cx), fill="▒", border="█")
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
        elif isinstance(op, AddPetalBloomDetail):
            self._draw_petal_detail(c, mapper, op, "top")
        elif isinstance(op, AddPetalScroll):
            self._draw_petal_scroll(c, mapper, op, "top")
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
