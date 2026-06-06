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


def almond_contour(cx: float, cz: float, width: float, height: float) -> list[tuple[float, float]]:
    return [
        (cx - width * 0.50, cz),
        (cx - width * 0.23, cz + height * 0.45),
        (cx + width * 0.23, cz + height * 0.45),
        (cx + width * 0.50, cz),
        (cx + width * 0.23, cz - height * 0.45),
        (cx - width * 0.23, cz - height * 0.45),
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
) -> tuple[list[list[float]], list[list[int]]]:
    bridge_width = nose_width * 0.34
    mid_z = (sellion_z + subnasale_z) / 2.0
    vertices = [
        point(-bridge_width / 2.0, face_y, sellion_z),
        point(bridge_width / 2.0, face_y, sellion_z),
        point(-nose_width / 2.0, face_y, subnasale_z),
        point(nose_width / 2.0, face_y, subnasale_z),
        point(0.0, nose_tip_y, mid_z + 0.008),
        point(0.0, nose_tip_y * 0.94 + face_y * 0.06, subnasale_z - 0.006),
    ]
    faces = [
        [0, 1, 4],
        [2, 5, 3],
        [0, 4, 5, 2],
        [1, 3, 5, 4],
        [0, 2, 3, 1],
        [4, 1, 3, 5],
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
) -> dict[str, Any]:
    return {
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
    raised_y = rounded(face_y - 0.012)
    socket_y = rounded(face_y - 0.004)
    nose_tip_y = rounded(face_y - nose_protrusion)

    layers = layer_by_id(taxonomy)
    parts: list[dict[str, Any]] = []

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
        (-forehead_width / 2.0, head_height * 0.82),
        (forehead_width / 2.0, head_height * 0.82),
        (cheek_width / 2.0, head_height * 0.57),
        (jaw_width / 2.0, chin_z + head_height * 0.12),
        (jaw_width * 0.24, chin_z - head_height * 0.03),
        (-jaw_width * 0.24, chin_z - head_height * 0.03),
        (-jaw_width / 2.0, chin_z + head_height * 0.12),
        (-cheek_width / 2.0, head_height * 0.57),
    ]
    vertices, faces = prism_from_xz_contour(face_contour, y_center=face_y, depth=0.004)
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
        )
    )

    brow_layer = layers["brow_eye_band"]
    brow_contour = [
        (-brow_width / 2.0, brow_z + 0.012),
        (brow_width / 2.0, brow_z + 0.012),
        (brow_width * 0.47, brow_z - 0.008),
        (nose_width * 0.25, brow_z - 0.014),
        (0.0, brow_z - 0.006),
        (-nose_width * 0.25, brow_z - 0.014),
        (-brow_width * 0.47, brow_z - 0.008),
    ]
    vertices, faces = prism_from_xz_contour(brow_contour, y_center=raised_y, depth=0.011)
    parts.append(
        make_part(
            part_id="brow_ridge",
            layer_id="brow_eye_band",
            facial_part="brow_ridge",
            shape_terms=["ridge", "chamfer", "bevel"],
            operation_terms=ops_for(brow_layer),
            blender_tool_ids=tools_for(brow_layer),
            vertices=vertices,
            faces=faces,
            material_id="skin_ridge",
            bevel_m=0.003,
            shade="flat",
            purpose="raised brow ridge and glabella band",
        )
    )

    socket_width = eye_spacing * 0.42
    socket_height = head_height * 0.082
    for side, sign in (("L", -1.0), ("R", 1.0)):
        eye_x = sign * eye_spacing / 2.0
        rim_vertices, rim_faces = prism_from_xz_contour(
            almond_contour(eye_x, eye_z, socket_width * 1.24, socket_height * 1.26),
            y_center=socket_y - 0.001,
            depth=0.003,
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
            )
        )
        dark_vertices, dark_faces = prism_from_xz_contour(
            almond_contour(eye_x, eye_z, socket_width, socket_height),
            y_center=socket_y - 0.0035,
            depth=0.002,
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
            )
        )

    nose_layer = layers["nose_wedge"]
    vertices, faces = nose_wedge_mesh(face_y=face_y - 0.002, nose_tip_y=nose_tip_y, sellion_z=sellion_z, subnasale_z=subnasale_z, nose_width=nose_width)
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
        )
    )

    cheek_layer = layers["cheek_midface_planes"]
    for side, sign in (("L", -1.0), ("R", 1.0)):
        x0 = sign * nose_width * 0.56
        x1 = sign * cheek_width * 0.48
        contour = [
            (x0, eye_z - 0.018),
            (x1, eye_z - 0.006),
            (sign * cheek_width * 0.43, mouth_z + 0.031),
            (sign * nose_width * 0.72, mouth_z + 0.017),
        ]
        vertices, faces = prism_from_xz_contour(contour, y_center=face_y - 0.009, depth=0.005)
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
            )
        )

    mouth_layer = layers["mouth_lip_zone"]
    mouth_vertices, mouth_faces = box_mesh(
        x0=-mouth_width / 2.0,
        x1=mouth_width / 2.0,
        y0=face_y - 0.014,
        y1=face_y - 0.010,
        z0=mouth_z - 0.002,
        z1=mouth_z + 0.002,
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
        )
    )
    for lip_id, z_offset in (("upper_lip_relief", 0.006), ("lower_lip_relief", -0.006)):
        vertices, faces = box_mesh(
            x0=-mouth_width * 0.43,
            x1=mouth_width * 0.43,
            y0=face_y - 0.013,
            y1=face_y - 0.008,
            z0=mouth_z + z_offset - 0.0015,
            z1=mouth_z + z_offset + 0.0015,
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
            )
        )

    jaw_layer = layers["chin_jaw_mass"]
    chin_contour = [
        (-jaw_width * 0.25, chin_z + 0.022),
        (jaw_width * 0.25, chin_z + 0.022),
        (jaw_width * 0.19, chin_z - 0.014),
        (0.0, chin_z - 0.025),
        (-jaw_width * 0.19, chin_z - 0.014),
    ]
    vertices, faces = prism_from_xz_contour(chin_contour, y_center=face_y - 0.008, depth=0.008)
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
        )
    )
    for side, sign in (("L", -1.0), ("R", 1.0)):
        contour = [
            (sign * jaw_width * 0.28, chin_z + 0.028),
            (sign * jaw_width * 0.50, chin_z + 0.053),
            (sign * jaw_width * 0.50, chin_z + 0.015),
            (sign * jaw_width * 0.30, chin_z - 0.009),
        ]
        vertices, faces = prism_from_xz_contour(contour, y_center=face_y - 0.004, depth=0.005)
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
            )
        )

    ear_layer = layers["ear_side_anchor"]
    for side, sign in (("L", -1.0), ("R", 1.0)):
        vertices, faces = prism_from_xz_contour(
            oval_contour(sign * head_breadth * 0.53, eye_z - 0.002, 0.022, 0.046, 10),
            y_center=-0.004,
            depth=0.01,
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
                "nose_tip_y": nose_tip_y,
            },
        },
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
