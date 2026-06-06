#!/usr/bin/env python3
"""Measure the external skull GLTF as deterministic 3D contour stacks."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/characters/head_construction/humanoid_skull_measurement_stack_v0.json"
DEFAULT_OUT_ROOT = Path("/tmp/gameguy_humanoid_skull_measurement_stack_v0")
DEFAULT_OUT = DEFAULT_OUT_ROOT / "humanoid_skull_measurement_stack_v0.json"
DEFAULT_REPORT = DEFAULT_OUT_ROOT / "humanoid_skull_measurement_stack_v0_report.json"
SOURCE_SCHEMA = "humanoid_skull_measurement_stack_source_v0"
OUTPUT_SCHEMA = "humanoid_skull_measurement_stack_v0"
REPORT_SCHEMA = "humanoid_skull_measurement_stack_report_v0"

AXIS_INDEX = {"x": 0, "y": 1, "z": 2}
COMPONENTS_BY_TYPE = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
COMPONENT_FORMATS = {
    5120: ("b", 1),
    5121: ("B", 1),
    5122: ("h", 2),
    5123: ("H", 2),
    5125: ("I", 4),
    5126: ("f", 4),
}


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


def write_json_object(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


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


def rounded_point(point: Iterable[float]) -> list[float]:
    return [rounded(value) for value in point]


def validate_source(source: dict[str, Any]) -> None:
    if source.get("schema") != SOURCE_SCHEMA:
        fail(f"source schema must be {SOURCE_SCHEMA}")
    rules = require_object(source.get("rules"), "rules")
    for key in (
        "reference_only",
        "external_asset_not_copied",
        "source_provenance_required",
        "compiler_reads_gltf_positions",
        "compiler_emits_3d_slice_stack",
        "blender_not_required",
        "no_join_pass",
        "no_skull_as_final_skin",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")

    skull_source = require_object(source.get("external_skull_source"), "external_skull_source")
    for key in ("gltf_path", "bin_path", "build_report_path", "registry_path", "approval_path"):
        path = Path(require_string(skull_source.get(key), f"external_skull_source.{key}"))
        if not path.exists():
            fail(f"external_skull_source.{key} does not exist: {path}")

    coordinate_map = require_object(source.get("coordinate_map"), "coordinate_map")
    require_number(coordinate_map.get("bbox_match_tolerance_m"), "coordinate_map.bbox_match_tolerance_m", minimum=0.0)

    mesh_read = require_object(source.get("mesh_read"), "mesh_read")
    if mesh_read.get("supported_primitive_mode") != "TRIANGLES":
        fail("mesh_read.supported_primitive_mode must be TRIANGLES")
    slice_plan = require_object(source.get("slice_plan"), "slice_plan")
    require_number(slice_plan.get("band_width_m"), "slice_plan.band_width_m", minimum=0.000001)
    require_number(slice_plan.get("max_band_width_m"), "slice_plan.max_band_width_m", minimum=0.000001)
    require_number(slice_plan.get("angular_bin_count"), "slice_plan.angular_bin_count", minimum=8)
    require_number(
        slice_plan.get("minimum_source_vertices_per_slice"),
        "slice_plan.minimum_source_vertices_per_slice",
        minimum=1,
    )
    require_list(slice_plan.get("families"), "slice_plan.families")


def accessor_values(gltf: dict[str, Any], bin_data: bytes, accessor_index: int) -> list[Any]:
    accessors = require_list(gltf.get("accessors"), "gltf.accessors")
    buffer_views = require_list(gltf.get("bufferViews"), "gltf.bufferViews")
    accessor = require_object(accessors[accessor_index], f"gltf.accessors[{accessor_index}]")
    buffer_view = require_object(
        buffer_views[int(accessor["bufferView"])],
        f"gltf.bufferViews[{accessor['bufferView']}]",
    )
    component_type = int(accessor["componentType"])
    if component_type not in COMPONENT_FORMATS:
        fail(f"unsupported accessor componentType {component_type}")
    accessor_type = require_string(accessor.get("type"), f"gltf.accessors[{accessor_index}].type")
    if accessor_type not in COMPONENTS_BY_TYPE:
        fail(f"unsupported accessor type {accessor_type}")

    component_format, component_size = COMPONENT_FORMATS[component_type]
    component_count = COMPONENTS_BY_TYPE[accessor_type]
    count = int(accessor["count"])
    byte_offset = int(buffer_view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    default_stride = component_size * component_count
    byte_stride = int(buffer_view.get("byteStride", default_stride))
    unpacker = struct.Struct("<" + component_format * component_count)

    values: list[Any] = []
    for index in range(count):
        offset = byte_offset + index * byte_stride
        row = unpacker.unpack_from(bin_data, offset)
        values.append(row[0] if component_count == 1 else row)
    return values


def node_translation_for_mesh(gltf: dict[str, Any], mesh_index: int) -> tuple[float, float, float]:
    nodes = require_list(gltf.get("nodes"), "gltf.nodes")
    for index, node_value in enumerate(nodes):
        node = require_object(node_value, f"gltf.nodes[{index}]")
        if node.get("mesh") != mesh_index:
            continue
        translation = node.get("translation", [0.0, 0.0, 0.0])
        if not isinstance(translation, list) or len(translation) != 3:
            fail(f"gltf.nodes[{index}].translation must be a three-value list")
        return (
            require_number(translation[0], f"gltf.nodes[{index}].translation[0]"),
            require_number(translation[1], f"gltf.nodes[{index}].translation[1]"),
            require_number(translation[2], f"gltf.nodes[{index}].translation[2]"),
        )
    return (0.0, 0.0, 0.0)


def project_vertices(
    raw_vertices: list[Any],
    translation: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    tx, ty, tz = translation
    projected: list[tuple[float, float, float]] = []
    for index, row in enumerate(raw_vertices):
        if not isinstance(row, tuple) or len(row) != 3:
            fail(f"POSITION row {index} must be VEC3")
        gltf_x, gltf_y, gltf_z = (float(row[0]), float(row[1]), float(row[2]))
        projected.append((gltf_x + tx, -(gltf_z + tz), gltf_y + ty))
    return projected


def bbox_for_points(points: list[tuple[float, float, float]]) -> dict[str, Any]:
    mins = [min(point[index] for point in points) for index in range(3)]
    maxs = [max(point[index] for point in points) for index in range(3)]
    dimensions = [maxs[index] - mins[index] for index in range(3)]
    center = [(mins[index] + maxs[index]) / 2.0 for index in range(3)]
    return {
        "min": rounded_point(mins),
        "max": rounded_point(maxs),
        "center": rounded_point(center),
        "dimensions": rounded_point(dimensions),
    }


def expected_bbox_from_report(build_report: dict[str, Any]) -> dict[str, Any]:
    truth_objects = require_list(build_report.get("truth_object_metadata"), "build_report.truth_object_metadata")
    if len(truth_objects) != 1:
        fail("build_report.truth_object_metadata must contain one truth object")
    truth = require_object(truth_objects[0], "build_report.truth_object_metadata[0]")
    bbox = require_object(truth.get("bbox"), "truth_object_metadata[0].bbox")
    bbox_min = [require_number(value, f"bbox.min[{index}]") for index, value in enumerate(require_list(bbox.get("min"), "bbox.min"))]
    bbox_max = [require_number(value, f"bbox.max[{index}]") for index, value in enumerate(require_list(bbox.get("max"), "bbox.max"))]
    return {
        "min": rounded_point(bbox_min),
        "max": rounded_point(bbox_max),
        "center": rounded_point((bbox_min[index] + bbox_max[index]) / 2.0 for index in range(3)),
        "dimensions": rounded_point((bbox_max[index] - bbox_min[index]) for index in range(3)),
    }


def bbox_delta(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    max_error = 0.0
    for key in ("min", "max", "center", "dimensions"):
        deltas = [rounded(actual[key][index] - expected[key][index]) for index in range(3)]
        rows[key] = deltas
        max_error = max(max_error, *(abs(value) for value in deltas))
    return {"max_abs_error_m": rounded(max_error), "by_field_m": rows}


def bounds_for_selected(points: list[tuple[float, float, float]]) -> dict[str, list[float]]:
    return {
        axis: [
            rounded(min(point[axis_index] for point in points)),
            rounded(max(point[axis_index] for point in points)),
        ]
        for axis, axis_index in AXIS_INDEX.items()
    }


def slice_contour(
    points: list[tuple[float, float, float]],
    *,
    slice_id: str,
    family_id: str,
    fixed_axis: str,
    project_axes: list[str],
    plane_m: float,
    base_band_width_m: float,
    max_band_width_m: float,
    min_source_vertices: int,
    angular_bin_count: int,
    anatomy_role: str,
) -> dict[str, Any]:
    fixed_index = AXIS_INDEX[fixed_axis]
    project_indices = [AXIS_INDEX[axis] for axis in project_axes]
    band_width = base_band_width_m
    selected: list[tuple[float, float, float]] = []
    while band_width <= max_band_width_m + 0.0000001:
        selected = [point for point in points if abs(point[fixed_index] - plane_m) <= band_width]
        if len(selected) >= min_source_vertices:
            break
        band_width *= 1.5
    if len(selected) < min_source_vertices:
        nearest = sorted(points, key=lambda point: abs(point[fixed_index] - plane_m))
        selected = nearest[:min_source_vertices]
        band_width = max(abs(point[fixed_index] - plane_m) for point in selected)

    center_2d = [
        sum(point[project_index] for point in selected) / len(selected)
        for project_index in project_indices
    ]
    bins: list[tuple[float, tuple[float, float, float]] | None] = [None] * angular_bin_count
    for point in selected:
        dx = point[project_indices[0]] - center_2d[0]
        dy = point[project_indices[1]] - center_2d[1]
        radius = math.hypot(dx, dy)
        if radius <= 0.0:
            continue
        angle = math.atan2(dy, dx)
        bin_index = int(((angle + math.pi) / (2.0 * math.pi)) * angular_bin_count) % angular_bin_count
        existing = bins[bin_index]
        if existing is None or radius > existing[0]:
            snapped = list(point)
            snapped[fixed_index] = plane_m
            bins[bin_index] = (radius, (snapped[0], snapped[1], snapped[2]))

    contour_points = [value[1] for value in bins if value is not None]
    if len(contour_points) < max(8, angular_bin_count // 6):
        fail(f"{slice_id} produced too few contour points")

    return {
        "slice_id": slice_id,
        "family_id": family_id,
        "fixed_axis": fixed_axis,
        "project_axes": project_axes,
        "plane_m": rounded(plane_m),
        "band_width_used_m": rounded(band_width),
        "anatomy_role": anatomy_role,
        "source_vertex_count": len(selected),
        "contour_point_count": len(contour_points),
        "missing_angular_bins": angular_bin_count - len(contour_points),
        "source_bounds_m": bounds_for_selected(selected),
        "contour_points_m": [rounded_point(point) for point in contour_points],
    }


def planned_plane(level: dict[str, Any], fixed_axis: str, bbox: dict[str, Any]) -> float:
    if "plane_m" in level:
        return require_number(level["plane_m"], f"{level.get('slice_id', 'level')}.plane_m")
    axis_index = AXIS_INDEX[fixed_axis]
    axis_min = float(bbox["min"][axis_index])
    axis_max = float(bbox["max"][axis_index])
    if fixed_axis == "z" and "height_fraction" in level:
        fraction = require_number(level["height_fraction"], f"{level['slice_id']}.height_fraction", minimum=0.0)
        return axis_min + fraction * (axis_max - axis_min)
    if fixed_axis == "y" and "depth_fraction" in level:
        fraction = require_number(level["depth_fraction"], f"{level['slice_id']}.depth_fraction", minimum=0.0)
        return axis_min + fraction * (axis_max - axis_min)
    fail(f"{level.get('slice_id', 'level')} must define plane_m or matching axis fraction")


def build_slices(
    source: dict[str, Any],
    points: list[tuple[float, float, float]],
    bbox: dict[str, Any],
) -> list[dict[str, Any]]:
    slice_plan = require_object(source.get("slice_plan"), "slice_plan")
    base_band_width_m = require_number(slice_plan.get("band_width_m"), "slice_plan.band_width_m")
    max_band_width_m = require_number(slice_plan.get("max_band_width_m"), "slice_plan.max_band_width_m")
    min_source_vertices = int(require_number(slice_plan.get("minimum_source_vertices_per_slice"), "slice_plan.minimum_source_vertices_per_slice"))
    angular_bin_count = int(require_number(slice_plan.get("angular_bin_count"), "slice_plan.angular_bin_count"))

    slices: list[dict[str, Any]] = []
    for family_index, family_value in enumerate(require_list(slice_plan.get("families"), "slice_plan.families")):
        family = require_object(family_value, f"slice_plan.families[{family_index}]")
        family_id = require_string(family.get("family_id"), f"slice_plan.families[{family_index}].family_id")
        fixed_axis = require_string(family.get("fixed_axis"), f"{family_id}.fixed_axis")
        if fixed_axis not in AXIS_INDEX:
            fail(f"{family_id}.fixed_axis must be x, y, or z")
        project_axes = [require_string(axis, f"{family_id}.project_axes[{index}]") for index, axis in enumerate(require_list(family.get("project_axes"), f"{family_id}.project_axes"))]
        if len(project_axes) != 2 or any(axis not in AXIS_INDEX for axis in project_axes):
            fail(f"{family_id}.project_axes must contain two known axes")
        for level_index, level_value in enumerate(require_list(family.get("levels"), f"{family_id}.levels")):
            level = require_object(level_value, f"{family_id}.levels[{level_index}]")
            slice_id = require_string(level.get("slice_id"), f"{family_id}.levels[{level_index}].slice_id")
            anatomy_role = require_string(level.get("anatomy_role"), f"{slice_id}.anatomy_role")
            slices.append(
                slice_contour(
                    points,
                    slice_id=slice_id,
                    family_id=family_id,
                    fixed_axis=fixed_axis,
                    project_axes=project_axes,
                    plane_m=planned_plane(level, fixed_axis, bbox),
                    base_band_width_m=base_band_width_m,
                    max_band_width_m=max_band_width_m,
                    min_source_vertices=min_source_vertices,
                    angular_bin_count=angular_bin_count,
                    anatomy_role=anatomy_role,
                )
            )
    return slices


def extreme_point(points: list[tuple[float, float, float]], axis: str, reverse: bool = False) -> list[float]:
    axis_index = AXIS_INDEX[axis]
    return rounded_point(max(points, key=lambda point: point[axis_index]) if reverse else min(points, key=lambda point: point[axis_index]))


def contour_extreme(slices_by_id: dict[str, dict[str, Any]], slice_id: str, axis: str, reverse: bool = False) -> list[float]:
    points = slices_by_id[slice_id]["contour_points_m"]
    axis_index = AXIS_INDEX[axis]
    return list(max(points, key=lambda point: point[axis_index]) if reverse else min(points, key=lambda point: point[axis_index]))


def build_landmarks(
    points: list[tuple[float, float, float]],
    bbox: dict[str, Any],
    slices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    slices_by_id = {row["slice_id"]: row for row in slices}
    return [
        {
            "landmark_id": "bbox_center",
            "method": "bbox_center",
            "point_m": bbox["center"],
            "use": "global alignment point for overlay and conform scaling",
        },
        {
            "landmark_id": "cranial_vault_top",
            "method": "mesh_extreme_max_z",
            "point_m": extreme_point(points, "z", reverse=True),
            "use": "top skull height and upper cranium limit",
        },
        {
            "landmark_id": "mandible_lowest_point",
            "method": "mesh_extreme_min_z",
            "point_m": extreme_point(points, "z"),
            "use": "jaw/chin lower limit",
        },
        {
            "landmark_id": "frontmost_face_depth",
            "method": "mesh_extreme_min_y",
            "point_m": extreme_point(points, "y"),
            "use": "face-side depth limit; negative y is front",
        },
        {
            "landmark_id": "rearmost_occiput_depth",
            "method": "mesh_extreme_max_y",
            "point_m": extreme_point(points, "y", reverse=True),
            "use": "back-skull depth limit",
        },
        {
            "landmark_id": "leftmost_temporal_width",
            "method": "mesh_extreme_min_x",
            "point_m": extreme_point(points, "x"),
            "use": "left skull width limit",
        },
        {
            "landmark_id": "rightmost_temporal_width",
            "method": "mesh_extreme_max_x",
            "point_m": extreme_point(points, "x", reverse=True),
            "use": "right skull width limit",
        },
        {
            "landmark_id": "brow_band_front_edge",
            "method": "xy_brow_band_min_y_contour",
            "point_m": contour_extreme(slices_by_id, "xy_brow_band", "y"),
            "use": "front brow/upper-orbit projection anchor",
        },
        {
            "landmark_id": "zygoma_left_width",
            "method": "xy_zygoma_orbit_min_x_contour",
            "point_m": contour_extreme(slices_by_id, "xy_zygoma_orbit", "x"),
            "use": "left cheekbone width anchor",
        },
        {
            "landmark_id": "zygoma_right_width",
            "method": "xy_zygoma_orbit_max_x_contour",
            "point_m": contour_extreme(slices_by_id, "xy_zygoma_orbit", "x", reverse=True),
            "use": "right cheekbone width anchor",
        },
        {
            "landmark_id": "mandible_left_width",
            "method": "xy_jaw_arc_min_x_contour",
            "point_m": contour_extreme(slices_by_id, "xy_jaw_arc", "x"),
            "use": "left jaw width anchor",
        },
        {
            "landmark_id": "mandible_right_width",
            "method": "xy_jaw_arc_max_x_contour",
            "point_m": contour_extreme(slices_by_id, "xy_jaw_arc", "x", reverse=True),
            "use": "right jaw width anchor",
        },
    ]


def read_source_mesh(source: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[float, float, float]], list[int]]:
    skull_source = require_object(source.get("external_skull_source"), "external_skull_source")
    gltf_path = Path(require_string(skull_source.get("gltf_path"), "external_skull_source.gltf_path"))
    bin_path = Path(require_string(skull_source.get("bin_path"), "external_skull_source.bin_path"))
    gltf = load_json_object(gltf_path)
    bin_data = bin_path.read_bytes()

    mesh_read = require_object(source.get("mesh_read"), "mesh_read")
    mesh_index = int(mesh_read.get("mesh_index", 0))
    primitive_index = int(mesh_read.get("primitive_index", 0))
    meshes = require_list(gltf.get("meshes"), "gltf.meshes")
    mesh = require_object(meshes[mesh_index], f"gltf.meshes[{mesh_index}]")
    primitive = require_object(
        require_list(mesh.get("primitives"), f"gltf.meshes[{mesh_index}].primitives")[primitive_index],
        f"gltf.meshes[{mesh_index}].primitives[{primitive_index}]",
    )
    if int(primitive.get("mode", 4)) != 4:
        fail("skull primitive mode must be TRIANGLES")
    attributes = require_object(primitive.get("attributes"), "gltf.primitive.attributes")
    position_semantic = require_string(mesh_read.get("position_semantic"), "mesh_read.position_semantic")
    if position_semantic not in attributes:
        fail(f"gltf primitive does not contain {position_semantic} attribute")
    if "indices" not in primitive:
        fail("gltf primitive must contain an indices accessor")
    position_accessor = int(attributes[position_semantic])
    index_accessor = int(primitive["indices"])
    accessors = require_list(gltf.get("accessors"), "gltf.accessors")
    position_meta = require_object(accessors[position_accessor], f"gltf.accessors[{position_accessor}]")
    index_meta = require_object(accessors[index_accessor], f"gltf.accessors[{index_accessor}]")
    expected_position_component_type = int(mesh_read.get("required_position_component_type", 5126))
    if int(position_meta.get("componentType")) != expected_position_component_type:
        fail(f"POSITION accessor componentType must be {expected_position_component_type}")
    allowed_index_component_types = {
        int(value)
        for value in require_list(mesh_read.get("required_index_component_types"), "mesh_read.required_index_component_types")
    }
    if int(index_meta.get("componentType")) not in allowed_index_component_types:
        fail("index accessor componentType is not allowed by the source config")
    raw_positions = accessor_values(gltf, bin_data, position_accessor)
    indices = [int(value) for value in accessor_values(gltf, bin_data, index_accessor)]
    translation = node_translation_for_mesh(gltf, mesh_index)
    points = project_vertices(raw_positions, translation)

    return {
        "gltf_path": str(gltf_path),
        "bin_path": str(bin_path),
        "position_accessor": position_accessor,
        "index_accessor": index_accessor,
        "node_translation": rounded_point(translation),
    }, points, indices


def build_measurement_stack(source: dict[str, Any]) -> dict[str, Any]:
    validate_source(source)
    mesh_read_summary, points, indices = read_source_mesh(source)
    skull_source = require_object(source.get("external_skull_source"), "external_skull_source")
    build_report = load_json_object(Path(require_string(skull_source.get("build_report_path"), "external_skull_source.build_report_path")))
    expected_bbox = expected_bbox_from_report(build_report)
    bbox = bbox_for_points(points)
    delta = bbox_delta(bbox, expected_bbox)
    tolerance = require_number(
        require_object(source.get("coordinate_map"), "coordinate_map").get("bbox_match_tolerance_m"),
        "coordinate_map.bbox_match_tolerance_m",
    )
    if delta["max_abs_error_m"] > tolerance:
        fail(f"coordinate map bbox delta {delta['max_abs_error_m']} exceeds tolerance {tolerance}")
    if len(indices) % 3 != 0:
        fail("index count must be divisible by 3")
    if max(indices) >= len(points):
        fail("index references a missing vertex")

    slices = build_slices(source, points, bbox)
    landmarks = build_landmarks(points, bbox, slices)
    truth_objects = require_list(build_report.get("truth_object_metadata"), "build_report.truth_object_metadata")
    truth = require_object(truth_objects[0], "build_report.truth_object_metadata[0]")
    slice_plan = require_object(source.get("slice_plan"), "slice_plan")

    validation = {
        "external_files_exist": True,
        "gltf_positions_read": len(points) > 0,
        "gltf_indices_read": len(indices) > 0,
        "indices_divisible_by_three": len(indices) % 3 == 0,
        "all_indices_in_vertex_range": max(indices) < len(points),
        "coordinate_map_matches_build_report_bbox": delta["max_abs_error_m"] <= tolerance,
        "each_slice_has_source_vertices": all(row["source_vertex_count"] > 0 for row in slices),
        "each_slice_has_contour_points": all(row["contour_point_count"] >= 8 for row in slices),
        "contour_points_are_3d": all(
            len(point) == 3
            for row in slices
            for point in row["contour_points_m"]
        ),
    }
    return {
        "schema": OUTPUT_SCHEMA,
        "bundle_id": source["bundle_id"],
        "purpose": source["purpose"],
        "source_provenance": {
            "source_id": skull_source["source_id"],
            "plain_name": skull_source["plain_name"],
            "phase_role": build_report.get("phase_role"),
            "active_seam_id": build_report.get("active_seam_id"),
            "source_paths": {
                "gltf_path": skull_source["gltf_path"],
                "bin_path": skull_source["bin_path"],
                "build_report_path": skull_source["build_report_path"],
                "registry_path": skull_source["registry_path"],
                "approval_path": skull_source["approval_path"],
                "upstream_vendor_obj": skull_source["upstream_vendor_obj"],
            },
            "upstream_license_note": skull_source["upstream_license_note"],
        },
        "coordinate_map": source["coordinate_map"],
        "mesh_read": mesh_read_summary,
        "mesh_summary": {
            "truth_object_name": truth.get("object_name"),
            "source_chunk_ids": truth.get("source_chunk_ids", []),
            "gltf_position_vertex_count": len(points),
            "build_report_study_vertex_count": build_report.get("study_vertex_count"),
            "gltf_index_count": len(indices),
            "gltf_triangle_count": len(indices) // 3,
            "build_report_study_triangle_count": build_report.get("study_triangle_count"),
            "bbox_m": bbox,
            "expected_build_report_bbox_m": expected_bbox,
            "bbox_delta_m": delta,
            "vertex_count_note": "The GLTF position accessor keeps all source positions; the build report study count records the approved study mesh count.",
        },
        "slice_stack": {
            "method": slice_plan["method"],
            "band_width_m": slice_plan["band_width_m"],
            "max_band_width_m": slice_plan["max_band_width_m"],
            "minimum_source_vertices_per_slice": slice_plan["minimum_source_vertices_per_slice"],
            "angular_bin_count": slice_plan["angular_bin_count"],
            "slice_count": len(slices),
            "slices": slices,
        },
        "landmarks": landmarks,
        "validation": validation,
    }


def build_report(measurement: dict[str, Any], out_path: Path) -> dict[str, Any]:
    validation = measurement["validation"]
    return {
        "schema": REPORT_SCHEMA,
        "measurement_path": str(out_path),
        "source_id": measurement["source_provenance"]["source_id"],
        "gltf_position_vertex_count": measurement["mesh_summary"]["gltf_position_vertex_count"],
        "gltf_triangle_count": measurement["mesh_summary"]["gltf_triangle_count"],
        "slice_count": measurement["slice_stack"]["slice_count"],
        "landmark_count": len(measurement["landmarks"]),
        "bbox_max_abs_error_m": measurement["mesh_summary"]["bbox_delta_m"]["max_abs_error_m"],
        "validation": validation,
        "pass": all(validation.values()),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = load_json_object(args.source)
    measurement = build_measurement_stack(source)
    report = build_report(measurement, args.out)
    write_json_object(args.out, measurement)
    write_json_object(args.json_report, report)
    print(
        "PASS humanoid skull measurement stack "
        f"vertices={report['gltf_position_vertex_count']} "
        f"triangles={report['gltf_triangle_count']} "
        f"slices={report['slice_count']} "
        f"landmarks={report['landmark_count']} "
        f"out={args.out}"
    )


if __name__ == "__main__":
    main()
