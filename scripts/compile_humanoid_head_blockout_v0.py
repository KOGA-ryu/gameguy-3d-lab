#!/usr/bin/env python3
"""Compile a humanoid head blockout geometry recipe from the head layer taxonomy."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY = ROOT / "data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json"
DEFAULT_OUT = ROOT / "data/characters/head_construction/humanoid_head_blockout_v0.json"
DEFAULT_REPORT = Path("/tmp/gameguy_humanoid_head_blockout_v0/compiler_report.json")
SOURCE_SCHEMA = "humanoid_head_layer_taxonomy_v0"
GEOMETRY_SCHEMA = "humanoid_head_geometry_v0"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        fail(f"{field} must be >= {minimum}")
    return number


def rounded(value: float) -> float:
    return round(float(value), 6)


def point(x: float, y: float, z: float) -> list[float]:
    return [rounded(x), rounded(y), rounded(z)]


def ellipsoid_mesh(
    *,
    center: tuple[float, float, float],
    radii: tuple[float, float, float],
    segments: int,
    rings: int,
    front_flatten_ratio: float,
) -> tuple[list[list[float]], list[list[int]]]:
    cx, cy, cz = center
    rx, ry, rz = radii
    vertices: list[list[float]] = []
    faces: list[list[int]] = []

    vertices.append(point(cx, cy, cz + rz))
    ring_indexes: list[list[int]] = []
    for ring in range(1, rings):
        phi = math.pi * ring / rings
        row: list[int] = []
        for segment in range(segments):
            theta = math.tau * segment / segments
            x = rx * math.sin(phi) * math.cos(theta)
            y = ry * math.sin(phi) * math.sin(theta)
            if y < 0:
                y *= front_flatten_ratio
            z = rz * math.cos(phi)
            row.append(len(vertices))
            vertices.append(point(cx + x, cy + y, cz + z))
        ring_indexes.append(row)
    bottom_index = len(vertices)
    vertices.append(point(cx, cy, cz - rz))

    first = ring_indexes[0]
    for segment in range(segments):
        faces.append([0, first[(segment + 1) % segments], first[segment]])
    for row_index in range(len(ring_indexes) - 1):
        upper = ring_indexes[row_index]
        lower = ring_indexes[row_index + 1]
        for segment in range(segments):
            faces.append([upper[segment], upper[(segment + 1) % segments], lower[(segment + 1) % segments], lower[segment]])
    last = ring_indexes[-1]
    for segment in range(segments):
        faces.append([last[segment], last[(segment + 1) % segments], bottom_index])
    return vertices, faces


def prism_from_xz_contour(contour: list[tuple[float, float]], *, y_center: float, depth: float) -> tuple[list[list[float]], list[list[int]]]:
    half_depth = depth / 2.0
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for x, z in contour:
        vertices.append(point(x, y_center - half_depth, z))
    for x, z in contour:
        vertices.append(point(x, y_center + half_depth, z))
    count = len(contour)
    faces.append(list(range(count)))
    faces.append(list(range((count * 2) - 1, count - 1, -1)))
    for index in range(count):
        next_index = (index + 1) % count
        faces.append([index, next_index, next_index + count, index + count])
    return vertices, faces


def curved_prism_from_xz_contour(
    contour: list[tuple[float, float]],
    *,
    y_front_for_point: Any,
    thickness: float,
) -> tuple[list[list[float]], list[list[int]]]:
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    front_y_values = [float(y_front_for_point(x, z)) for x, z in contour]
    for (x, z), y_front in zip(contour, front_y_values):
        vertices.append(point(x, y_front, z))
    for (x, z), y_front in zip(contour, front_y_values):
        vertices.append(point(x, y_front + thickness, z))
    count = len(contour)
    faces.append(list(range(count)))
    faces.append(list(range((count * 2) - 1, count - 1, -1)))
    for index in range(count):
        next_index = (index + 1) % count
        faces.append([index, next_index, next_index + count, index + count])
    return vertices, faces


def bent_prism_from_xz_contour(
    contour: list[tuple[float, float]],
    *,
    y_front_for_point: Any,
    thickness: float,
    center_y_front: float | None = None,
) -> tuple[list[list[float]], list[list[int]]]:
    center_x = sum(x for x, _ in contour) / len(contour)
    center_z = sum(z for _, z in contour) / len(contour)
    front_y_values = [float(y_front_for_point(x, z)) for x, z in contour]
    if center_y_front is None:
        center_y_front = float(y_front_for_point(center_x, center_z))

    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for (x, z), y_front in zip(contour, front_y_values):
        vertices.append(point(x, y_front, z))
    front_center_index = len(vertices)
    vertices.append(point(center_x, center_y_front, center_z))

    back_offset = len(vertices)
    for (x, z), y_front in zip(contour, front_y_values):
        vertices.append(point(x, y_front + thickness, z))
    back_center_index = len(vertices)
    vertices.append(point(center_x, center_y_front + thickness, center_z))

    count = len(contour)
    for index in range(count):
        next_index = (index + 1) % count
        faces.append([front_center_index, index, next_index])
        faces.append([back_center_index, next_index + back_offset, index + back_offset])
        faces.append([index, index + back_offset, next_index + back_offset, next_index])
    return vertices, faces


def transition_ring_surface(
    contour: list[tuple[float, float]],
    *,
    inner_y_for_point: Any,
    outer_y_for_point: Any,
    outer_scale: float,
    outer_z_offset: float = 0.0,
) -> tuple[list[list[float]], list[list[int]]]:
    center_x = sum(x for x, _ in contour) / len(contour)
    center_z = sum(z for _, z in contour) / len(contour)
    vertices: list[list[float]] = []
    faces: list[list[int]] = []

    outer_points: list[tuple[float, float]] = []
    for x, z in contour:
        vertices.append(point(x, float(inner_y_for_point(x, z)), z))
        outer_x = center_x + (x - center_x) * outer_scale
        outer_z = center_z + (z - center_z) * outer_scale + outer_z_offset
        outer_points.append((outer_x, outer_z))
    for x, z in outer_points:
        vertices.append(point(x, float(outer_y_for_point(x, z)), z))

    count = len(contour)
    for index in range(count):
        next_index = (index + 1) % count
        faces.append([index, next_index, next_index + count, index + count])
    return vertices, faces


def surface_grid_from_xz_contour(
    contour: list[tuple[float, float]],
    *,
    y_for_point: Any,
    rows: int,
    columns: int,
) -> tuple[list[list[float]], list[list[int]]]:
    z_values = [z for _, z in contour]
    z_min = min(z_values)
    z_max = max(z_values)

    def x_span_at_z(z: float) -> tuple[float, float]:
        intersections: list[float] = []
        for index, (x0, z0) in enumerate(contour):
            x1, z1 = contour[(index + 1) % len(contour)]
            if z0 == z1:
                continue
            lower = min(z0, z1)
            upper = max(z0, z1)
            if lower <= z <= upper:
                t = (z - z0) / (z1 - z0)
                intersections.append(x0 + (x1 - x0) * t)
        if len(intersections) < 2:
            x_values = [x for x, _ in contour]
            return min(x_values), max(x_values)
        intersections.sort()
        return intersections[0], intersections[-1]

    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for row in range(rows):
        z_t = row / max(rows - 1, 1)
        z = z_min + (z_max - z_min) * (0.02 + 0.96 * z_t)
        x_min, x_max = x_span_at_z(z)
        for column in range(columns):
            x_t = column / max(columns - 1, 1)
            x = x_min + (x_max - x_min) * x_t
            vertices.append(point(x, float(y_for_point(x, z)), z))
    for row in range(rows - 1):
        for column in range(columns - 1):
            current = row * columns + column
            faces.append([current, current + 1, current + columns + 1, current + columns])
    return vertices, faces


def box_mesh(*, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> tuple[list[list[float]], list[list[int]]]:
    vertices = [
        point(x0, y0, z0),
        point(x1, y0, z0),
        point(x1, y0, z1),
        point(x0, y0, z1),
        point(x0, y1, z0),
        point(x1, y1, z0),
        point(x1, y1, z1),
        point(x0, y1, z1),
    ]
    faces = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
    return vertices, faces


def almond_contour(cx: float, cz: float, width: float, height: float, slant_ratio: float = 0.0) -> list[tuple[float, float]]:
    base = [
        (cx - width * 0.50, cz),
        (cx - width * 0.23, cz + height * 0.45),
        (cx + width * 0.23, cz + height * 0.45),
        (cx + width * 0.50, cz),
        (cx + width * 0.23, cz - height * 0.45),
        (cx - width * 0.23, cz - height * 0.45),
    ]
    return [(x, z + ((x - cx) / max(width, 1e-6)) * height * slant_ratio) for x, z in base]


def capsule_contour(cx: float, cz: float, width: float, height: float) -> list[tuple[float, float]]:
    radius = height / 2.0
    straight = max(0.0, width - height)
    left = cx - straight / 2.0
    right = cx + straight / 2.0
    return [
        (left, cz + radius),
        (right, cz + radius),
        (right + radius * 0.72, cz + radius * 0.55),
        (right + radius, cz),
        (right + radius * 0.72, cz - radius * 0.55),
        (right, cz - radius),
        (left, cz - radius),
        (left - radius * 0.72, cz - radius * 0.55),
        (left - radius, cz),
        (left - radius * 0.72, cz + radius * 0.55),
    ]


def oval_contour(cx: float, cz: float, width: float, height: float, count: int = 10) -> list[tuple[float, float]]:
    return [
        (cx + math.cos(math.tau * index / count) * width / 2.0, cz + math.sin(math.tau * index / count) * height / 2.0)
        for index in range(count)
    ]


def nose_wedge_mesh(
    *,
    face_y: float,
    nose_tip_y: float,
    sellion_z: float,
    subnasale_z: float,
    nose_width: float,
    bridge_blend_ratio: float,
    base_blend_ratio: float,
) -> tuple[list[list[float]], list[list[int]]]:
    bridge_width = nose_width * (0.34 + 0.28 * bridge_blend_ratio)
    base_width = nose_width * (0.92 + 0.32 * base_blend_ratio)
    middle_width = (bridge_width + base_width) * 0.5
    mid_z = (sellion_z + subnasale_z) / 2.0
    vertices = [
        point(-bridge_width / 2.0, face_y, sellion_z),
        point(bridge_width / 2.0, face_y, sellion_z),
        point(-middle_width / 2.0, face_y + (nose_tip_y - face_y) * 0.35, mid_z),
        point(middle_width / 2.0, face_y + (nose_tip_y - face_y) * 0.35, mid_z),
        point(-base_width / 2.0, face_y - 0.002, subnasale_z),
        point(base_width / 2.0, face_y - 0.002, subnasale_z),
        point(0.0, nose_tip_y, mid_z + 0.008),
        point(0.0, nose_tip_y * 0.94 + face_y * 0.06, subnasale_z - 0.006),
    ]
    faces = [
        [0, 1, 6],
        [0, 6, 2],
        [1, 3, 6],
        [2, 6, 7, 4],
        [3, 5, 7, 6],
        [4, 7, 5],
        [0, 2, 4],
        [1, 5, 3],
        [0, 4, 5, 1],
    ]
    return vertices, faces


def make_part(
    *,
    part_id: str,
    layer_id: str,
    facial_part: str,
    shape_terms: list[str],
    operation_terms: list[str],
    blender_tool_ids: list[str],
    vertices: list[list[float]],
    faces: list[list[int]],
    material_id: str,
    bevel_m: float,
    shade: str,
    purpose: str,
    bend_field: dict[str, Any] | None = None,
    transition_field: dict[str, Any] | None = None,
    merge_field: dict[str, Any] | None = None,
    render_group: str | None = None,
) -> dict[str, Any]:
    part = {
        "part_id": part_id,
        "layer_id": layer_id,
        "facial_part": facial_part,
        "shape_terms": shape_terms,
        "operation_terms": operation_terms,
        "blender_tool_ids": blender_tool_ids,
        "material_id": material_id,
        "bevel_m": rounded(bevel_m),
        "shade": shade,
        "purpose": purpose,
        "mesh": {
            "type": "mesh_from_pydata",
            "vertices_m": vertices,
            "faces": faces,
        },
    }
    if bend_field is not None:
        part["bend_field"] = bend_field
    if transition_field is not None:
        part["transition_field"] = transition_field
    if merge_field is not None:
        part["merge_field"] = merge_field
    if render_group is not None:
        part["render_group"] = render_group
    return part


def layer_by_id(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers = taxonomy.get("construction_layers")
    if not isinstance(layers, list):
        fail("taxonomy.construction_layers must be a list")
    result: dict[str, dict[str, Any]] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            fail("construction_layers entries must be objects")
        layer_id = require_string(layer.get("layer_id"), "construction_layers.layer_id")
        result[layer_id] = layer
    return result


def tools_for(layer: dict[str, Any]) -> list[str]:
    values = layer.get("blender_tool_ids")
    if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
        fail(f"{layer.get('layer_id', '<layer>')}.blender_tool_ids must be non-empty strings")
    return values


def ops_for(layer: dict[str, Any]) -> list[str]:
    values = layer.get("operation_terms")
    if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
        fail(f"{layer.get('layer_id', '<layer>')}.operation_terms must be non-empty strings")
    return values


def controls_by_id(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    controls = taxonomy.get("shape_refinement_controls")
    if not isinstance(controls, list):
        fail("taxonomy.shape_refinement_controls must be a list")
    result: dict[str, dict[str, Any]] = {}
    for control in controls:
        if not isinstance(control, dict):
            fail("shape_refinement_controls entries must be objects")
        control_id = require_string(control.get("control_id"), "shape_refinement_controls.control_id")
        if control_id in result:
            fail(f"duplicate shape_refinement_controls.control_id {control_id}")
        default = require_number(control.get("default"), f"{control_id}.default")
        allowed_range = control.get("allowed_range")
        if not isinstance(allowed_range, list) or len(allowed_range) != 2:
            fail(f"{control_id}.allowed_range must be [min, max]")
        lower = require_number(allowed_range[0], f"{control_id}.allowed_range[0]")
        upper = require_number(allowed_range[1], f"{control_id}.allowed_range[1]")
        if lower >= upper or not lower <= default <= upper:
            fail(f"{control_id}.default must sit inside an ascending allowed_range")
        result[control_id] = control
    return result


def control_value(controls: dict[str, dict[str, Any]], control_id: str) -> float:
    if control_id not in controls:
        fail(f"missing shape_refinement_controls.{control_id}")
    return float(controls[control_id]["default"])


def control_rows(controls: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for control_id in sorted(controls):
        control = controls[control_id]
        rows.append(
            {
                "control_id": control_id,
                "plain_name": control.get("plain_name", control_id),
                "value": control["default"],
                "allowed_range": control["allowed_range"],
                "target_layers": control.get("target_layers", []),
                "source_field_mapping": control.get("source_field_mapping", []),
            }
        )
    return rows


def wrap_y(base_y: float, x: float, max_width: float, wrap_ratio: float, amount: float) -> float:
    side = min(1.0, abs(x) / max(max_width / 2.0, 1e-6))
    return base_y + amount * wrap_ratio * (side**1.45)


def compile_geometry(taxonomy: dict[str, Any], source_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if taxonomy.get("schema") != SOURCE_SCHEMA:
        fail(f"taxonomy schema must be {SOURCE_SCHEMA}")
    profile = taxonomy.get("measurement_profile")
    if not isinstance(profile, dict):
        fail("taxonomy.measurement_profile must be an object")
    dimensions = profile.get("dimensions_m")
    if not isinstance(dimensions, dict):
        fail("taxonomy.measurement_profile.dimensions_m must be an object")

    head_length = require_number(dimensions.get("head_length"), "dimensions_m.head_length", minimum=0.01)
    head_breadth = require_number(dimensions.get("head_breadth"), "dimensions_m.head_breadth", minimum=0.01)
    cheek_width = require_number(dimensions.get("bizygomatic_breadth"), "dimensions_m.bizygomatic_breadth", minimum=0.01)
    jaw_width = require_number(dimensions.get("bigonial_breadth"), "dimensions_m.bigonial_breadth", minimum=0.01)
    forehead_width = require_number(dimensions.get("minimum_frontal_breadth"), "dimensions_m.minimum_frontal_breadth", minimum=0.01)
    brow_width = require_number(dimensions.get("maximum_frontal_breadth"), "dimensions_m.maximum_frontal_breadth", minimum=0.01)
    eye_spacing = require_number(dimensions.get("interpupillary_distance"), "dimensions_m.interpupillary_distance", minimum=0.01)
    face_height = require_number(dimensions.get("menton_sellion_length"), "dimensions_m.menton_sellion_length", minimum=0.01)
    nose_height = require_number(dimensions.get("subnasale_sellion_length"), "dimensions_m.subnasale_sellion_length", minimum=0.01)
    nose_width = require_number(dimensions.get("nose_breadth"), "dimensions_m.nose_breadth", minimum=0.001)
    nose_protrusion = require_number(dimensions.get("nose_protrusion"), "dimensions_m.nose_protrusion", minimum=0.001)
    mouth_width = require_number(dimensions.get("lip_length"), "dimensions_m.lip_length", minimum=0.001)
    controls = controls_by_id(taxonomy)
    forehead_wrap_ratio = control_value(controls, "forehead_wrap_ratio")
    brow_arc_ratio = control_value(controls, "brow_arc_ratio")
    eye_socket_slant_ratio = control_value(controls, "eye_socket_slant_ratio")
    brow_forward_offset_m = control_value(controls, "brow_forward_offset_m")
    socket_under_brow_setback_m = control_value(controls, "socket_under_brow_setback_m")
    glabella_peak_ratio = control_value(controls, "glabella_peak_ratio")
    brow_side_wrap_ratio = control_value(controls, "brow_side_wrap_ratio")
    nose_bridge_blend_ratio = control_value(controls, "nose_bridge_blend_ratio")
    nose_base_blend_ratio = control_value(controls, "nose_base_blend_ratio")
    cheek_wrap_ratio = control_value(controls, "cheek_wrap_ratio")
    jaw_taper_ratio = control_value(controls, "jaw_taper_ratio")
    ear_lowering_ratio = control_value(controls, "ear_lowering_ratio")
    feature_embed_overlap_m = control_value(controls, "feature_embed_overlap_m")

    head_height = rounded(head_length * 1.16)
    chin_z = rounded(head_height * 0.105)
    sellion_z = rounded(chin_z + face_height)
    subnasale_z = rounded(sellion_z - nose_height)
    brow_z = rounded(sellion_z + head_height * 0.065)
    eye_z = rounded(brow_z - head_height * 0.065)
    mouth_z = rounded(chin_z + (subnasale_z - chin_z) * 0.42)
    skull_center_z = rounded(head_height * 0.515)
    skull_center = (0.0, 0.0, skull_center_z)
    skull_radii = (head_breadth / 2.0, head_length / 2.0, head_height / 2.0)
    face_y = rounded(-head_length * 0.37)
    brow_base_y = rounded(face_y - 0.004 - brow_forward_offset_m - feature_embed_overlap_m * 0.35)
    socket_rim_y = rounded(brow_base_y + socket_under_brow_setback_m * 0.32)
    socket_shadow_y = rounded(brow_base_y + socket_under_brow_setback_m * 0.62)
    nose_tip_y = rounded(face_y - nose_protrusion)

    layers = layer_by_id(taxonomy)
    parts: list[dict[str, Any]] = []

    def bend_field(field_id: str, meaning: str, controls_used: list[str]) -> dict[str, Any]:
        return {
            "field_id": field_id,
            "space": "xz_contour_to_y_depth",
            "meaning": meaning,
            "controls_used": controls_used,
        }

    def transition_field(
        field_id: str,
        *,
        child_part_id: str,
        parent_part_id: str,
        meaning: str,
        controls_used: list[str],
    ) -> dict[str, Any]:
        return {
            "field_id": field_id,
            "space": "child_contour_to_parent_face_surface",
            "child_part_id": child_part_id,
            "parent_part_id": parent_part_id,
            "meaning": meaning,
            "controls_used": controls_used,
        }

    def add_face_transition_part(
        *,
        part_id: str,
        child_part_id: str,
        facial_part: str,
        contour: list[tuple[float, float]],
        inner_y_for_point: Any,
        outer_scale: float,
        outer_z_offset: float,
        material_id: str = "skin_transition",
    ) -> None:
        vertices, faces = transition_ring_surface(
            contour,
            inner_y_for_point=inner_y_for_point,
            outer_y_for_point=face_mask_y_front,
            outer_scale=outer_scale,
            outer_z_offset=outer_z_offset,
        )
        parts.append(
            make_part(
                part_id=part_id,
                layer_id="face_mask_planes",
                facial_part=facial_part,
                shape_terms=["relief", "plane_break", "bevel"],
                operation_terms=ops_for(face_layer),
                blender_tool_ids=tools_for(face_layer),
                vertices=vertices,
                faces=faces,
                material_id=material_id,
                bevel_m=0.0008,
                shade="flat",
                purpose=f"pre-join transition surface from {child_part_id} into face_mask_plane",
                transition_field=transition_field(
                    f"{part_id}_transition_v0",
                    child_part_id=child_part_id,
                    parent_part_id="face_mask_plane",
                    meaning="Bridge the child contour back into the bent face mask so the blockout reads as one constructed facial surface.",
                    controls_used=["feature_embed_overlap_m", "forehead_wrap_ratio"],
                ),
            )
        )

    skull_layer = layers["skull_envelope"]
    vertices, faces = ellipsoid_mesh(center=skull_center, radii=skull_radii, segments=14, rings=7, front_flatten_ratio=0.72)
    parts.append(
        make_part(
            part_id="skull_envelope",
            layer_id="skull_envelope",
            facial_part="cranium",
            shape_terms=["envelope", "bevel"],
            operation_terms=ops_for(skull_layer),
            blender_tool_ids=tools_for(skull_layer),
            vertices=vertices,
            faces=faces,
            material_id="skin_base",
            bevel_m=0.0025,
            shade="smooth",
            purpose="largest cranium and occiput mass",
        )
    )

    face_layer = layers["face_mask_planes"]
    face_contour = [
        (-forehead_width * 0.48, head_height * 0.805),
        (-forehead_width * 0.16, head_height * 0.84),
        (forehead_width * 0.16, head_height * 0.84),
        (forehead_width * 0.48, head_height * 0.805),
        (cheek_width * 0.50, eye_z - head_height * 0.02),
        (cheek_width * 0.44, mouth_z + head_height * 0.12),
        (jaw_width * 0.43, chin_z + head_height * 0.09),
        (jaw_width * (0.25 - jaw_taper_ratio * 0.05), chin_z - head_height * 0.022),
        (0.0, chin_z - head_height * 0.035),
        (-jaw_width * (0.25 - jaw_taper_ratio * 0.05), chin_z - head_height * 0.022),
        (-jaw_width * 0.43, chin_z + head_height * 0.09),
        (-cheek_width * 0.44, mouth_z + head_height * 0.12),
        (-cheek_width * 0.50, eye_z - head_height * 0.02),
    ]
    def face_mask_y_front(x: float, z: float) -> float:
        side_wrap = wrap_y(face_y - 0.002, x, cheek_width, forehead_wrap_ratio, head_length * 0.082)
        midface_ratio = max(0.0, 1.0 - abs(z - (eye_z - head_height * 0.09)) / max(head_height * 0.20, 1e-6))
        center_ratio = max(0.0, 1.0 - abs(x) / max(cheek_width * 0.42, 1e-6))
        lower_retreat = max(0.0, 1.0 - abs(z - (chin_z + head_height * 0.05)) / max(head_height * 0.12, 1e-6))
        return side_wrap - head_length * 0.010 * center_ratio * midface_ratio + head_length * 0.012 * lower_retreat

    vertices, faces = bent_prism_from_xz_contour(
        face_contour,
        y_front_for_point=face_mask_y_front,
        thickness=0.006 + feature_embed_overlap_m,
    )
    parts.append(
        make_part(
            part_id="face_mask_plane",
            layer_id="face_mask_planes",
            facial_part="forehead",
            shape_terms=["plane", "plane_break", "chamfer"],
            operation_terms=ops_for(face_layer),
            blender_tool_ids=tools_for(face_layer),
            vertices=vertices,
            faces=faces,
            material_id="skin_plane",
            bevel_m=0.0018,
            shade="flat",
            purpose="front face mask plane sitting on the skull envelope",
            bend_field=bend_field(
                "face_mask_side_wrap_and_lower_retreat_v0",
                "Wrap the face mask around the skull sides while letting the lower face retreat from the midface.",
                ["forehead_wrap_ratio", "feature_embed_overlap_m"],
            ),
        )
    )

    brow_layer = layers["brow_eye_band"]
    glabella_width = max(nose_width * (0.62 + 0.24 * nose_bridge_blend_ratio), brow_width * 0.18)
    glabella_contour = [
        (-glabella_width * 0.40, brow_z + head_height * (0.012 + 0.006 * brow_arc_ratio)),
        (0.0, brow_z + head_height * (0.025 + 0.016 * glabella_peak_ratio)),
        (glabella_width * 0.40, brow_z + head_height * (0.012 + 0.006 * brow_arc_ratio)),
        (glabella_width * 0.34, brow_z - head_height * (0.006 + 0.006 * glabella_peak_ratio)),
        (0.0, brow_z - head_height * (0.022 + 0.016 * glabella_peak_ratio)),
        (-glabella_width * 0.34, brow_z - head_height * (0.006 + 0.006 * glabella_peak_ratio)),
    ]

    def glabella_y_front(x: float, z: float) -> float:
        center_ratio = max(0.0, 1.0 - abs(x) / max(glabella_width * 0.50, 1e-6))
        center_push = brow_forward_offset_m * (0.36 + 0.22 * glabella_peak_ratio) * (center_ratio**1.7)
        return brow_base_y - center_push

    vertices, faces = bent_prism_from_xz_contour(
        glabella_contour,
        y_front_for_point=glabella_y_front,
        thickness=0.011 + feature_embed_overlap_m,
    )
    parts.append(
        make_part(
            part_id="brow_glabella",
            layer_id="brow_eye_band",
            facial_part="brow_ridge",
            shape_terms=["ridge", "plane_break", "chamfer", "bevel"],
            operation_terms=ops_for(brow_layer),
            blender_tool_ids=tools_for(brow_layer),
            vertices=vertices,
            faces=faces,
            material_id="skin_ridge",
            bevel_m=0.003,
            shade="flat",
            purpose="projecting center glabella knot that receives the nose bridge",
            bend_field=bend_field(
                "glabella_center_peak_v0",
                "Push the center brow knot forward while its side edges sink back toward the brow wings.",
                ["brow_forward_offset_m", "glabella_peak_ratio", "feature_embed_overlap_m"],
            ),
        )
    )
    add_face_transition_part(
        part_id="brow_glabella_to_face_blend",
        child_part_id="brow_glabella",
        facial_part="brow_ridge",
        contour=glabella_contour,
        inner_y_for_point=glabella_y_front,
        outer_scale=1.18,
        outer_z_offset=0.0,
    )

    def brow_wing_contour(sign: float) -> list[tuple[float, float]]:
        return [
            (sign * nose_width * 0.16, brow_z + head_height * (0.005 + 0.006 * brow_arc_ratio)),
            (sign * eye_spacing * 0.28, brow_z + head_height * (0.025 + 0.012 * brow_arc_ratio)),
            (sign * brow_width * 0.52, brow_z + head_height * 0.017),
            (sign * brow_width * 0.49, brow_z - head_height * 0.006),
            (sign * eye_spacing * 0.24, brow_z - head_height * (0.017 + 0.006 * brow_arc_ratio)),
            (sign * nose_width * 0.14, brow_z - head_height * (0.006 + 0.004 * glabella_peak_ratio)),
        ]

    def brow_wing_y_front(x: float, z: float) -> float:
        wing_base_y = brow_base_y + socket_under_brow_setback_m * 0.08
        return wrap_y(wing_base_y, x, brow_width, brow_side_wrap_ratio, head_length * 0.070)

    for side, sign in (("L", -1.0), ("R", 1.0)):
        vertices, faces = bent_prism_from_xz_contour(
            brow_wing_contour(sign),
            y_front_for_point=brow_wing_y_front,
            thickness=0.010 + feature_embed_overlap_m,
        )
        parts.append(
            make_part(
                part_id=f"brow_wing_{side}",
                layer_id="brow_eye_band",
                facial_part="brow_ridge",
                shape_terms=["ridge", "plane_break", "chamfer", "bevel"],
                operation_terms=ops_for(brow_layer),
                blender_tool_ids=tools_for(brow_layer),
                vertices=vertices,
                faces=faces,
                material_id="skin_ridge",
                bevel_m=0.0028,
                shade="flat",
                purpose=f"{side} wrapped brow wing over the socket recess",
                bend_field=bend_field(
                    f"brow_wing_{side}_side_wrap_v0",
                    "Bend the brow wing backward toward the temple while keeping its inner edge near the glabella.",
                    ["brow_side_wrap_ratio", "socket_under_brow_setback_m", "feature_embed_overlap_m"],
                ),
            )
        )
        add_face_transition_part(
            part_id=f"brow_wing_{side}_to_face_blend",
            child_part_id=f"brow_wing_{side}",
            facial_part="brow_ridge",
            contour=brow_wing_contour(sign),
            inner_y_for_point=brow_wing_y_front,
            outer_scale=1.12,
            outer_z_offset=0.0,
        )

    socket_width = eye_spacing * 0.42
    socket_height = head_height * 0.082

    def socket_y_front(base_y: float) -> Any:
        return lambda x, z: wrap_y(base_y, x, brow_width, brow_side_wrap_ratio, head_length * 0.036)

    for side, sign in (("L", -1.0), ("R", 1.0)):
        eye_x = sign * eye_spacing / 2.0
        rim_depth = 0.0035 + feature_embed_overlap_m * 0.35
        rim_front_y = socket_rim_y - rim_depth / 2.0
        rim_vertices, rim_faces = bent_prism_from_xz_contour(
            almond_contour(eye_x, eye_z, socket_width * 1.32, socket_height * 1.36, slant_ratio=eye_socket_slant_ratio * sign),
            y_front_for_point=socket_y_front(rim_front_y),
            center_y_front=rim_front_y + socket_under_brow_setback_m * 0.18,
            thickness=rim_depth,
        )
        parts.append(
            make_part(
                part_id=f"eye_socket_rim_{side}",
                layer_id="brow_eye_band",
                facial_part="eye_sockets",
                shape_terms=["socket", "bevel"],
                operation_terms=ops_for(brow_layer),
                blender_tool_ids=tools_for(brow_layer),
                vertices=rim_vertices,
                faces=rim_faces,
                material_id="socket_rim",
                bevel_m=0.0015,
                shade="flat",
                purpose=f"{side} socket bevel rim proxy",
                bend_field=bend_field(
                    f"eye_socket_rim_{side}_shallow_dish_v0",
                    "Bend the socket rim into a shallow dish so the eye area starts recessing under the brow wing.",
                    ["eye_socket_slant_ratio", "socket_under_brow_setback_m", "brow_side_wrap_ratio"],
                ),
            )
        )
        shadow_depth = 0.0024 + feature_embed_overlap_m * 0.2
        shadow_front_y = socket_shadow_y - shadow_depth / 2.0
        dark_vertices, dark_faces = bent_prism_from_xz_contour(
            almond_contour(eye_x, eye_z, socket_width * 1.02, socket_height * 1.04, slant_ratio=eye_socket_slant_ratio * sign),
            y_front_for_point=socket_y_front(shadow_front_y),
            center_y_front=shadow_front_y + socket_under_brow_setback_m * 0.22,
            thickness=shadow_depth,
        )
        parts.append(
            make_part(
                part_id=f"eye_socket_dark_{side}",
                layer_id="brow_eye_band",
                facial_part="eye_sockets",
                shape_terms=["socket", "valley"],
                operation_terms=ops_for(brow_layer),
                blender_tool_ids=tools_for(brow_layer),
                vertices=dark_vertices,
                faces=dark_faces,
                material_id="socket_shadow",
                bevel_m=0.0008,
                shade="flat",
                purpose=f"{side} recessed socket read",
                bend_field=bend_field(
                    f"eye_socket_dark_{side}_deep_dish_v0",
                    "Bend the socket shadow farther back than the rim center so it reads as cavity depth, not paint.",
                    ["eye_socket_slant_ratio", "socket_under_brow_setback_m", "brow_side_wrap_ratio"],
                ),
            )
        )

    nose_layer = layers["nose_wedge"]
    vertices, faces = nose_wedge_mesh(
        face_y=face_y - 0.002 + feature_embed_overlap_m * 0.18,
        nose_tip_y=nose_tip_y,
        sellion_z=sellion_z,
        subnasale_z=subnasale_z,
        nose_width=nose_width,
        bridge_blend_ratio=nose_bridge_blend_ratio,
        base_blend_ratio=nose_base_blend_ratio,
    )
    parts.append(
        make_part(
            part_id="nose_wedge",
            layer_id="nose_wedge",
            facial_part="nose",
            shape_terms=["wedge", "plane", "chamfer", "bevel"],
            operation_terms=ops_for(nose_layer),
            blender_tool_ids=tools_for(nose_layer),
            vertices=vertices,
            faces=faces,
            material_id="skin_nose",
            bevel_m=0.0024,
            shade="flat",
            purpose="central nose bridge, tip, base, and side planes",
            bend_field=bend_field(
                "nose_wedge_native_bridge_tip_base_planes_v0",
                "Use wedge planes as the nose bend field: bridge, tip, base, and side planes already carry different depths.",
                ["nose_bridge_blend_ratio", "nose_base_blend_ratio"],
            ),
        )
    )

    cheek_layer = layers["cheek_midface_planes"]

    def cheek_y_front_for(sign: float) -> Any:
        def y_front(x: float, z: float) -> float:
            base = wrap_y(face_y - 0.010, x, cheek_width, cheek_wrap_ratio, head_length * 0.072)
            cheekbone_x = sign * cheek_width * 0.34
            cheekbone_z = eye_z - head_height * 0.004
            cheekbone = max(
                0.0,
                1.0
                - (abs(x - cheekbone_x) / max(cheek_width * 0.28, 1e-6)) ** 2
                - (abs(z - cheekbone_z) / max(head_height * 0.10, 1e-6)) ** 2,
            )
            mouth_retreat = max(0.0, 1.0 - abs(z - (mouth_z + head_height * 0.035)) / max(head_height * 0.08, 1e-6))
            return base - head_length * 0.020 * cheekbone + head_length * 0.010 * mouth_retreat

        return y_front

    for side, sign in (("L", -1.0), ("R", 1.0)):
        x0 = sign * nose_width * (0.54 + 0.10 * nose_base_blend_ratio)
        x1 = sign * cheek_width * 0.52
        contour = [
            (x0, eye_z - head_height * 0.040),
            (sign * cheek_width * 0.28, eye_z - head_height * 0.010),
            (x1, eye_z - head_height * 0.032),
            (sign * cheek_width * 0.49, mouth_z + head_height * 0.120),
            (sign * cheek_width * 0.34, mouth_z + head_height * 0.045),
            (sign * nose_width * 0.86, mouth_z + head_height * 0.030),
        ]
        vertices, faces = bent_prism_from_xz_contour(
            contour,
            y_front_for_point=cheek_y_front_for(sign),
            thickness=0.006 + feature_embed_overlap_m,
        )
        parts.append(
            make_part(
                part_id=f"cheek_plane_{side}",
                layer_id="cheek_midface_planes",
                facial_part="cheeks",
                shape_terms=["plane", "ridge", "plane_break", "bevel"],
                operation_terms=ops_for(cheek_layer),
                blender_tool_ids=tools_for(cheek_layer),
                vertices=vertices,
                faces=faces,
                material_id="skin_cheek",
                bevel_m=0.0018,
                shade="flat",
                purpose=f"{side} cheekbone and midface plane",
                bend_field=bend_field(
                    f"cheek_plane_{side}_cheekbone_to_mouth_retreat_v0",
                    "Push the cheekbone high point forward while the lower cheek retreats toward the mouth plane.",
                    ["cheek_wrap_ratio", "nose_base_blend_ratio", "feature_embed_overlap_m"],
                ),
            )
        )
        add_face_transition_part(
            part_id=f"cheek_plane_{side}_to_face_blend",
            child_part_id=f"cheek_plane_{side}",
            facial_part="cheeks",
            contour=contour,
            inner_y_for_point=cheek_y_front_for(sign),
            outer_scale=1.08,
            outer_z_offset=-head_height * 0.003,
        )

    mouth_layer = layers["mouth_lip_zone"]
    mouth_depth = 0.0032
    mouth_front_y = face_y - 0.003 + feature_embed_overlap_m * 0.2 - mouth_depth / 2.0
    mouth_contour = capsule_contour(0.0, mouth_z, mouth_width * 0.92, head_height * 0.014)

    def mouth_y_front(x: float, z: float) -> float:
        return mouth_front_y + head_length * 0.006 * min(1.0, abs(x) / max(mouth_width * 0.46, 1e-6))

    mouth_vertices, mouth_faces = bent_prism_from_xz_contour(
        mouth_contour,
        y_front_for_point=mouth_y_front,
        center_y_front=mouth_front_y + head_length * 0.012,
        thickness=mouth_depth,
    )
    parts.append(
        make_part(
            part_id="mouth_crease",
            layer_id="mouth_lip_zone",
            facial_part="mouth",
            shape_terms=["valley"],
            operation_terms=ops_for(mouth_layer),
            blender_tool_ids=tools_for(mouth_layer),
            vertices=mouth_vertices,
            faces=mouth_faces,
            material_id="mouth_shadow",
            bevel_m=0.0008,
            shade="flat",
            purpose="neutral horizontal mouth valley",
            bend_field=bend_field(
                "mouth_crease_center_valley_v0",
                "Sink the center of the mouth crease behind its corners so it reads as a valley in the face.",
                ["feature_embed_overlap_m"],
            ),
        )
    )
    add_face_transition_part(
        part_id="mouth_crease_to_face_blend",
        child_part_id="mouth_crease",
        facial_part="mouth",
        contour=mouth_contour,
        inner_y_for_point=mouth_y_front,
        outer_scale=1.42,
        outer_z_offset=0.0,
        material_id="skin_lip",
    )
    for lip_id, z_offset, scale in (("upper_lip_relief", 0.0024, 0.76), ("lower_lip_relief", -0.0024, 0.70)):
        lip_depth = 0.0036
        lip_front_y = face_y - 0.0032 + feature_embed_overlap_m * 0.12 - lip_depth / 2.0
        lip_contour = capsule_contour(0.0, mouth_z + z_offset, mouth_width * scale, head_height * 0.010)
        vertices, faces = bent_prism_from_xz_contour(
            lip_contour,
            y_front_for_point=lambda x, z, lip_front_y=lip_front_y, scale=scale: lip_front_y
            + head_length * 0.004 * min(1.0, abs(x) / max(mouth_width * scale * 0.50, 1e-6)),
            center_y_front=lip_front_y - head_length * 0.005,
            thickness=lip_depth,
        )
        parts.append(
            make_part(
                part_id=lip_id,
                layer_id="mouth_lip_zone",
                facial_part="mouth",
                shape_terms=["relief", "ridge", "bevel"],
                operation_terms=ops_for(mouth_layer),
                blender_tool_ids=tools_for(mouth_layer),
                vertices=vertices,
                faces=faces,
                material_id="skin_lip",
                bevel_m=0.0012,
                shade="flat",
                purpose=f"{lip_id.replace('_', ' ')}",
                bend_field=bend_field(
                    f"{lip_id}_bowed_relief_v0",
                    "Bow the lip relief forward at the center while the corners tuck back into the mouth crease.",
                    ["feature_embed_overlap_m"],
                ),
            )
        )

    jaw_layer = layers["chin_jaw_mass"]
    chin_contour = [
        (-jaw_width * (0.28 - jaw_taper_ratio * 0.05), chin_z + head_height * 0.108),
        (-jaw_width * 0.09, chin_z + head_height * 0.126),
        (jaw_width * 0.09, chin_z + head_height * 0.126),
        (jaw_width * (0.28 - jaw_taper_ratio * 0.05), chin_z + head_height * 0.108),
        (jaw_width * (0.20 - jaw_taper_ratio * 0.03), chin_z - head_height * 0.026),
        (0.0, chin_z - head_height * 0.045),
        (-jaw_width * (0.20 - jaw_taper_ratio * 0.03), chin_z - head_height * 0.026),
    ]
    def chin_y_front(x: float, z: float) -> float:
        base = wrap_y(face_y - 0.008, x, jaw_width, jaw_taper_ratio, head_length * 0.030)
        chin_center = max(
            0.0,
            1.0
            - (abs(x) / max(jaw_width * 0.22, 1e-6)) ** 2
            - (abs(z - (chin_z + head_height * 0.055)) / max(head_height * 0.10, 1e-6)) ** 2,
        )
        jaw_edge_retreat = min(1.0, abs(x) / max(jaw_width * 0.34, 1e-6))
        return base - head_length * 0.014 * chin_center + head_length * 0.006 * jaw_edge_retreat

    vertices, faces = bent_prism_from_xz_contour(
        chin_contour,
        y_front_for_point=chin_y_front,
        thickness=0.007 + feature_embed_overlap_m,
    )
    parts.append(
        make_part(
            part_id="chin_mass",
            layer_id="chin_jaw_mass",
            facial_part="chin",
            shape_terms=["ridge", "plane", "bevel"],
            operation_terms=ops_for(jaw_layer),
            blender_tool_ids=tools_for(jaw_layer),
            vertices=vertices,
            faces=faces,
            material_id="skin_chin",
            bevel_m=0.002,
            shade="flat",
            purpose="lower chin protrusion and lower-face anchor",
            bend_field=bend_field(
                "chin_mass_center_push_side_retreat_v0",
                "Push the center chin forward while the edges retreat into the jaw side planes.",
                ["jaw_taper_ratio", "feature_embed_overlap_m"],
            ),
        )
    )
    add_face_transition_part(
        part_id="chin_mass_to_face_blend",
        child_part_id="chin_mass",
        facial_part="chin",
        contour=chin_contour,
        inner_y_for_point=chin_y_front,
        outer_scale=1.10,
        outer_z_offset=head_height * 0.002,
    )

    def jaw_y_front_for(sign: float) -> Any:
        def y_front(x: float, z: float) -> float:
            base = wrap_y(face_y - 0.006, x, jaw_width, jaw_taper_ratio, head_length * 0.060)
            mandibular_angle = max(
                0.0,
                1.0
                - (abs(x - sign * jaw_width * 0.48) / max(jaw_width * 0.18, 1e-6)) ** 2
                - (abs(z - (chin_z + head_height * 0.075)) / max(head_height * 0.10, 1e-6)) ** 2,
            )
            chin_overlap = max(0.0, 1.0 - abs(x - sign * jaw_width * 0.24) / max(jaw_width * 0.20, 1e-6))
            return base + head_length * 0.010 * mandibular_angle - head_length * 0.006 * chin_overlap

        return y_front

    for side, sign in (("L", -1.0), ("R", 1.0)):
        contour = [
            (sign * jaw_width * 0.30, chin_z + head_height * 0.116),
            (sign * jaw_width * 0.52, chin_z + head_height * 0.145),
            (sign * jaw_width * 0.50, chin_z + head_height * 0.050),
            (sign * jaw_width * 0.34, chin_z - head_height * 0.010),
            (sign * jaw_width * 0.22, chin_z + head_height * 0.020),
        ]
        vertices, faces = bent_prism_from_xz_contour(
            contour,
            y_front_for_point=jaw_y_front_for(sign),
            thickness=0.006 + feature_embed_overlap_m,
        )
        parts.append(
            make_part(
                part_id=f"jaw_side_plane_{side}",
                layer_id="chin_jaw_mass",
                facial_part="jaw",
                shape_terms=["plane", "plane_break", "chamfer"],
                operation_terms=ops_for(jaw_layer),
                blender_tool_ids=tools_for(jaw_layer),
                vertices=vertices,
                faces=faces,
                material_id="skin_jaw",
                bevel_m=0.0015,
                shade="flat",
                purpose=f"{side} jaw chamfer into side face",
                bend_field=bend_field(
                    f"jaw_side_plane_{side}_mandibular_angle_wrap_v0",
                    "Bend the side jaw from the chin overlap into a rearward mandibular angle.",
                    ["jaw_taper_ratio", "feature_embed_overlap_m"],
                ),
            )
        )
        add_face_transition_part(
            part_id=f"jaw_side_plane_{side}_to_face_blend",
            child_part_id=f"jaw_side_plane_{side}",
            facial_part="jaw",
            contour=contour,
            inner_y_for_point=jaw_y_front_for(sign),
            outer_scale=1.08,
            outer_z_offset=0.0,
        )

    ear_layer = layers["ear_side_anchor"]
    ear_z = eye_z - head_height * (0.018 + 0.072 * ear_lowering_ratio)
    for side, sign in (("L", -1.0), ("R", 1.0)):
        vertices, faces = prism_from_xz_contour(
            oval_contour(sign * head_breadth * 0.515, ear_z, 0.020, 0.040, 10),
            y_center=0.002 + feature_embed_overlap_m * 0.4,
            depth=0.012,
        )
        parts.append(
            make_part(
                part_id=f"ear_anchor_{side}",
                layer_id="ear_side_anchor",
                facial_part="ears",
                shape_terms=["socket", "relief", "bevel"],
                operation_terms=ops_for(ear_layer),
                blender_tool_ids=tools_for(ear_layer),
                vertices=vertices,
                faces=faces,
                material_id="skin_ear",
                bevel_m=0.0018,
                shade="flat",
                purpose=f"{side} future ear/hair/helmet side anchor",
            )
        )

    material_palette = [
        {"material_id": "skin_base", "color_hex": "#c9ad83", "role": "skull envelope"},
        {"material_id": "skin_plane", "color_hex": "#d1b58c", "role": "face mask planes"},
        {"material_id": "skin_transition", "color_hex": "#cab08b", "role": "pre-join facial transition surfaces"},
        {"material_id": "skin_ridge", "color_hex": "#b99269", "role": "brow and raised ridges"},
        {"material_id": "socket_rim", "color_hex": "#9f846b", "role": "eye socket rim"},
        {"material_id": "socket_shadow", "color_hex": "#263039", "role": "recessed eye socket"},
        {"material_id": "skin_nose", "color_hex": "#c49a70", "role": "nose wedge"},
        {"material_id": "skin_cheek", "color_hex": "#d0a985", "role": "cheek planes"},
        {"material_id": "mouth_shadow", "color_hex": "#402b2a", "role": "mouth valley"},
        {"material_id": "skin_lip", "color_hex": "#ad745f", "role": "lip relief"},
        {"material_id": "skin_chin", "color_hex": "#bc936f", "role": "chin mass"},
        {"material_id": "skin_jaw", "color_hex": "#b38967", "role": "jaw side planes"},
        {"material_id": "skin_ear", "color_hex": "#bd956f", "role": "ear anchors"},
        {"material_id": "guide_blue", "color_hex": "#4a6f9e", "role": "measurement guide"},
    ]
    connection_targets = {
        "face_mask_plane": "skull_envelope",
        "brow_glabella": "face_mask_plane",
        "brow_glabella_to_face_blend": "face_mask_plane",
        "brow_wing_L": "face_mask_plane",
        "brow_wing_L_to_face_blend": "face_mask_plane",
        "brow_wing_R": "face_mask_plane",
        "brow_wing_R_to_face_blend": "face_mask_plane",
        "eye_socket_rim_L": "brow_wing_L",
        "eye_socket_dark_L": "eye_socket_rim_L",
        "eye_socket_rim_R": "brow_wing_R",
        "eye_socket_dark_R": "eye_socket_rim_R",
        "nose_wedge": "face_mask_plane",
        "cheek_plane_L": "face_mask_plane",
        "cheek_plane_L_to_face_blend": "face_mask_plane",
        "cheek_plane_R": "face_mask_plane",
        "cheek_plane_R_to_face_blend": "face_mask_plane",
        "mouth_crease": "face_mask_plane",
        "mouth_crease_to_face_blend": "face_mask_plane",
        "upper_lip_relief": "mouth_crease",
        "lower_lip_relief": "mouth_crease",
        "chin_mass": "face_mask_plane",
        "chin_mass_to_face_blend": "face_mask_plane",
        "jaw_side_plane_L": "chin_mass",
        "jaw_side_plane_L_to_face_blend": "face_mask_plane",
        "jaw_side_plane_R": "chin_mass",
        "jaw_side_plane_R_to_face_blend": "face_mask_plane",
        "ear_anchor_L": "skull_envelope",
        "ear_anchor_R": "skull_envelope",
    }
    connection_policy = {
        "mode": "refined_overlap_before_join_v0",
        "purpose": "Keep construction layers separate for tuning while sinking each non-base feature into its parent enough to avoid a floating-plate read.",
        "rules": [
            {
                "part_id": part["part_id"],
                "connects_to": connection_targets[part["part_id"]],
                "method": "embed_overlap",
                "overlap_m": rounded(feature_embed_overlap_m),
            }
            for part in parts
            if part["part_id"] != "skull_envelope"
        ],
    }

    geometry = {
        "schema": GEOMETRY_SCHEMA,
        "asset_id": "humanoid_head_blockout_v0",
        "asset_family": "character_head_construction",
        "style": "low_compute_faceted_mannequin_head",
        "purpose": "First source-compiled head blockout using measured anchors and layer taxonomy: skull, face planes, brow/eye band, nose wedge, cheeks, mouth, chin/jaw, ears, and edge language.",
        "source_reference": {
            "taxonomy": str(source_path),
            "measurement_profile_id": profile.get("profile_id"),
            "source_support": taxonomy.get("source_support", []),
            "not_claimed": ["final face sculpt", "expression rig", "medical anatomy", "production character skin"],
        },
        "coordinate_system": {
            "space": "local_xyz_m",
            "unit": "meter",
            "origin": "neck_socket_bottom_center",
            "x": "left/right",
            "y": "depth; negative y faces camera",
            "z": "height/up",
        },
        "rules": {
            "source_taxonomy_owns_design": True,
            "compiler_emits_vertices_faces": True,
            "blender_adapter_consumes_geometry": True,
            "blender_adapter_must_not_invent_facial_features": True,
            "largest_forms_first": True,
        },
        "measurement_profile": {
            "profile_id": profile.get("profile_id"),
            "units": "m",
            "dimensions_m": dimensions,
            "derived_dimensions_m": {
                "head_height": head_height,
                "chin_z": chin_z,
                "sellion_z": sellion_z,
                "subnasale_z": subnasale_z,
                "brow_z": brow_z,
                "eye_z": eye_z,
                "mouth_z": mouth_z,
                "face_y": face_y,
                "brow_base_y": brow_base_y,
                "socket_rim_y": socket_rim_y,
                "socket_shadow_y": socket_shadow_y,
                "nose_tip_y": nose_tip_y,
            },
        },
        "shape_refinement_controls": control_rows(controls),
        "connection_policy": connection_policy,
        "build_chain": [
            "validate_humanoid_head_layer_taxonomy_v0",
            "compile_humanoid_head_blockout_v0",
            "export_blender_humanoid_head_blockout_v0",
        ],
        "construction_layers": [
            {
                "sequence": layer["sequence"],
                "layer_id": layer["layer_id"],
                "priority": layer["priority"],
                "largest_to_smallest_rank": layer["largest_to_smallest_rank"],
            }
            for layer in taxonomy["construction_layers"]
        ],
        "material_palette": material_palette,
        "parts": parts,
        "validation_checks": [
            "skull envelope exists and is the largest mesh",
            "brow/eye band, nose wedge, and chin/jaw are present as critical read layers",
            "every non-base part has a positive source-owned connection overlap",
            "all mesh parts have vertices, faces, material IDs, and source layer IDs",
            "measurement anchors are preserved in the recipe for future tuning",
            "Blender adapter can validate without importing Blender",
        ],
    }
    report = {
        "schema": "humanoid_head_blockout_compiler_report_v0",
        "source_schema": taxonomy["schema"],
        "geometry_schema": geometry["schema"],
        "asset_id": geometry["asset_id"],
        "part_count": len(parts),
        "layer_count": len(geometry["construction_layers"]),
        "material_count": len(material_palette),
        "measurement_profile_id": profile.get("profile_id"),
        "rules": {
            "uses_head_layer_taxonomy": True,
            "uses_measured_anchors": True,
            "uses_shape_refinement_controls": True,
            "uses_brow_eye_region_controls": True,
            "records_connection_policy": True,
            "emits_deterministic_vertices_faces": True,
            "imports_blender": False,
            "manual_blender_design_logic": False,
        },
    }
    return geometry, report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY, help="Input humanoid head layer taxonomy JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output humanoid head geometry recipe JSON")
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT, help="Output compiler report JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    taxonomy = load_json_object(args.taxonomy)
    geometry, report = compile_geometry(taxonomy, args.taxonomy)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(geometry, indent=2) + "\n", encoding="utf-8")
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS humanoid head blockout compile: "
        f"parts={report['part_count']} layers={report['layer_count']} materials={report['material_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
