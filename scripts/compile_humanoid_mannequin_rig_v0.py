#!/usr/bin/env python3
"""Compile the humanoid mannequin rig recipe from source dimensions and lanes."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_BUNDLE = ROOT / "data" / "characters" / "mannequin_rigs" / "sources" / "humanoid_body_mannequin_sources_v0.json"
DEFAULT_OUT = ROOT / "data" / "characters" / "mannequin_rigs" / "humanoid_body_mannequin_rig_v0.json"
DEFAULT_REPORT = Path("/tmp/gameguy_humanoid_body_mannequin_rig_v0/compiler_report.json")
RECIPE_SCHEMA = "humanoid_body_mannequin_rig_recipe_v0"
SOURCE_SCHEMA = "humanoid_body_mannequin_source_bundle_v0"


REGION_SPECS = [
    (1, "head", "head", "neck", "head", "head_neck", "head_projected_front_three_quarter"),
    (2, "neck", "neck", "chest", "neck", "head_neck", "neck_and_collar_projected"),
    (3, "chest", "torso", "pelvis", "chest", "torso_back", "torso_chest_plate_projected"),
    (4, "pelvis", "pelvis", "root", "pelvis", "pelvis_torso_mid", "pelvis_shorts_projected"),
    (5, "upper_arm_L", "upper_arm_left", "chest", "shoulder_L", "front_arm_L", "upper_arm_pair"),
    (6, "lower_arm_L", "lower_arm_left", "upper_arm_L", "elbow_L", "front_arm_L", "lower_arm_pair"),
    (7, "hand_L", "hand_left", "lower_arm_L", "wrist_L", "hands", "hand_pair"),
    (8, "upper_arm_R", "upper_arm_right", "chest", "shoulder_R", "rear_arm_R", "upper_arm_pair"),
    (9, "lower_arm_R", "lower_arm_right", "upper_arm_R", "elbow_R", "rear_arm_R", "lower_arm_pair"),
    (10, "hand_R", "hand_right", "lower_arm_R", "wrist_R", "hands", "hand_pair"),
    (11, "upper_leg_L", "upper_leg_left", "pelvis", "hip_L", "front_leg_L", "upper_leg_pair"),
    (12, "lower_leg_L", "lower_leg_left", "upper_leg_L", "knee_L", "front_leg_L", "lower_leg_pair"),
    (13, "foot_L", "foot_left", "lower_leg_L", "ankle_L", "feet", "foot_pair"),
    (14, "upper_leg_R", "upper_leg_right", "pelvis", "hip_R", "rear_leg_R", "upper_leg_pair"),
    (15, "lower_leg_R", "lower_leg_right", "upper_leg_R", "knee_R", "rear_leg_R", "lower_leg_pair"),
    (16, "foot_R", "foot_right", "lower_leg_R", "ankle_R", "feet", "foot_pair"),
]

SYMMETRY_ROLES = {
    "upper_arm_L": "mirrored_from_upper_arm_R_visible_reference",
    "lower_arm_L": "mirrored_from_lower_arm_R_visible_reference",
    "hand_L": "mirrored_from_hand_R_visible_reference",
    "upper_arm_R": "visible_reference_side",
    "lower_arm_R": "visible_reference_side",
    "hand_R": "visible_reference_side",
    "upper_leg_L": "visible_reference_side",
    "lower_leg_L": "visible_reference_side",
    "foot_L": "visible_reference_side",
    "upper_leg_R": "mirrored_from_upper_leg_L_visible_reference",
    "lower_leg_R": "mirrored_from_lower_leg_L_visible_reference",
    "foot_R": "mirrored_from_foot_L_visible_reference",
}

DRAW_ORDER = [
    "back_cape_future",
    "rear_arm_R",
    "torso_back",
    "rear_leg_R",
    "rear_leg_L",
    "pelvis_torso_mid",
    "front_arm_L",
    "front_arm_R",
    "front_leg_L",
    "front_leg_R",
    "head_neck",
    "hands",
    "feet",
    "accessories_future",
]


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


def require_bbox(value: Any, field: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 4:
        fail(f"{field} must be [x0, y0, x1, y1]")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, int) or isinstance(item, bool):
            fail(f"{field}[{index}] must be an integer")
        result.append(item)
    x0, y0, x1, y1 = result
    if x1 <= x0 or y1 <= y0:
        fail(f"{field} must have positive width and height")
    return result


def load_profile(profile_source: dict[str, Any]) -> dict[str, Any]:
    source_path = Path(require_string(profile_source.get("source_path"), "human_profile_source.source_path"))
    profile_id = require_string(profile_source.get("profile_id"), "human_profile_source.profile_id")
    try:
        data = tomllib.loads(source_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing human profile TOML: {source_path}")
    for row in data.get("profiles", []):
        if row.get("profile_id") == profile_id:
            return {
                "source_path": str(source_path),
                "profile_id": profile_id,
                "display_name": row["display_name"],
                "sex_class": row["sex_class"],
                "population_basis": row["population_basis"],
                "stature_percentile": row["stature_percentile"],
                "body_height_m": round(float(row["body_height_m"]), 6),
                "ratios": {str(key): round(float(value), 9) for key, value in row.get("ratios", {}).items()},
                "notes": [str(note) for note in row.get("notes", [])],
            }
    fail(f"profile_id not found in {source_path}: {profile_id}")


def scaled_profile_landmarks(profile: dict[str, Any]) -> dict[str, float]:
    body_height = float(profile["body_height_m"])
    ratios = profile["ratios"]
    return {f"{key}_m": round(body_height * float(value), 6) for key, value in ratios.items()}


def layer_by_lane(region_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers = region_manifest.get("layers")
    if not isinstance(layers, list):
        fail("region manifest layers must be a list")
    result: dict[str, dict[str, Any]] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            fail("region manifest layer rows must be objects")
        lane = require_string(layer.get("lane"), "layer.lane")
        result[lane] = layer
    return result


def px_to_m(point: tuple[float, float], *, center_x: float, bottom_y: float, scale_m_per_px: float) -> list[float]:
    x, y = point
    return [round((x - center_x) * scale_m_per_px, 6), round((bottom_y - y) * scale_m_per_px, 6)]


def bbox_point(bbox: list[int], nx: float, ny: float) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return (x0 + (x1 - x0) * nx, y0 + (y1 - y0) * ny)


def contour_norms(lane: str) -> list[tuple[float, float]]:
    if lane == "head":
        return [(0.22, 0.00), (0.78, 0.00), (0.96, 0.16), (1.00, 0.56), (0.86, 0.88), (0.62, 1.00), (0.30, 0.94), (0.05, 0.68), (0.03, 0.25)]
    if lane == "neck":
        return [(0.18, 0.00), (0.82, 0.00), (1.00, 0.62), (0.70, 1.00), (0.30, 1.00), (0.00, 0.62)]
    if lane == "torso":
        return [(0.12, 0.00), (0.82, 0.00), (1.00, 0.22), (0.92, 0.88), (0.58, 1.00), (0.18, 0.88), (0.00, 0.28)]
    if lane == "pelvis":
        return [(0.08, 0.00), (0.94, 0.00), (0.88, 0.58), (0.62, 1.00), (0.48, 0.78), (0.32, 1.00), (0.02, 0.62)]
    if "hand" in lane:
        return [(0.18, 0.02), (0.72, 0.00), (0.98, 0.28), (0.90, 0.74), (0.62, 1.00), (0.20, 0.92), (0.00, 0.55)]
    if "foot_left" == lane:
        return [(0.26, 0.02), (0.80, 0.02), (1.00, 0.36), (0.88, 0.74), (0.42, 0.98), (0.02, 0.82), (0.00, 0.45)]
    if "foot_right" == lane:
        return [(0.20, 0.02), (0.74, 0.02), (1.00, 0.44), (0.94, 0.82), (0.48, 0.98), (0.06, 0.76), (0.00, 0.34)]
    if "upper_arm_left" == lane:
        return [(0.22, 0.04), (0.92, 0.12), (1.00, 0.42), (0.72, 1.00), (0.06, 0.86), (0.00, 0.30)]
    if "lower_arm_left" == lane:
        return [(0.18, 0.02), (0.90, 0.06), (1.00, 0.32), (0.80, 0.96), (0.18, 1.00), (0.00, 0.72), (0.02, 0.22)]
    if "upper_arm_right" == lane:
        return [(0.08, 0.08), (0.72, 0.00), (1.00, 0.30), (0.92, 0.78), (0.28, 1.00), (0.00, 0.42)]
    if "lower_arm_right" == lane:
        return [(0.12, 0.04), (0.80, 0.02), (1.00, 0.28), (0.98, 0.74), (0.70, 1.00), (0.08, 0.92), (0.00, 0.24)]
    if "upper_leg_left" == lane:
        return [(0.18, 0.00), (0.92, 0.06), (0.98, 0.36), (0.72, 1.00), (0.16, 0.90), (0.00, 0.22)]
    if "lower_leg_left" == lane:
        return [(0.18, 0.00), (0.86, 0.04), (0.98, 0.30), (0.80, 0.98), (0.20, 1.00), (0.02, 0.72), (0.08, 0.22)]
    if "upper_leg_right" == lane:
        return [(0.08, 0.04), (0.78, 0.00), (1.00, 0.26), (0.84, 0.88), (0.28, 1.00), (0.00, 0.36)]
    if "lower_leg_right" == lane:
        return [(0.14, 0.02), (0.82, 0.00), (0.94, 0.22), (0.98, 0.78), (0.76, 1.00), (0.16, 0.96), (0.00, 0.28)]
    return [(0.12, 0.02), (0.88, 0.02), (0.98, 0.20), (0.98, 0.82), (0.82, 0.98), (0.18, 0.98), (0.02, 0.82), (0.02, 0.20)]


def contour_from_bbox(
    lane: str,
    bbox: list[int],
    *,
    center_x: float,
    bottom_y: float,
    scale_m_per_px: float,
) -> list[list[float]]:
    return [
        px_to_m(bbox_point(bbox, nx, ny), center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
        for nx, ny in contour_norms(lane)
    ]


def lane_center(
    layers: dict[str, dict[str, Any]],
    lane: str,
    *,
    center_x: float,
    bottom_y: float,
    scale_m_per_px: float,
) -> list[float]:
    bbox = require_bbox(layers[lane].get("bbox"), f"{lane}.bbox")
    return px_to_m(((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0), center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)


def joint_between(
    layers: dict[str, dict[str, Any]],
    lane_a: str,
    lane_b: str,
    *,
    center_x: float,
    bottom_y: float,
    scale_m_per_px: float,
) -> list[float]:
    a = require_bbox(layers[lane_a].get("bbox"), f"{lane_a}.bbox")
    b = require_bbox(layers[lane_b].get("bbox"), f"{lane_b}.bbox")
    return px_to_m(((max(a[0], b[0]) + min(a[2], b[2])) / 2.0, (a[3] + b[1]) / 2.0), center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)


def add_depth(point_xz: list[float], y_depth: float) -> list[float]:
    return [point_xz[0], round(y_depth, 6), point_xz[1]]


def y_depth_for_name(name: str) -> float:
    if name.endswith("_L"):
        return -0.055
    if name.endswith("_R"):
        return 0.03
    if name == "head":
        return -0.05
    if name == "neck":
        return -0.035
    if name == "chest":
        return -0.025
    if name == "pelvis":
        return -0.015
    return 0.0


def shape_depth_for_lane(lane: str, profile_landmarks: dict[str, float]) -> float:
    if lane == "torso":
        return max(0.045, round(profile_landmarks["chest_depth_m"] * 0.28, 6))
    if lane == "pelvis":
        return max(0.045, round(profile_landmarks["pelvis_depth_m"] * 0.34, 6))
    if lane == "head":
        return 0.048
    if "foot" in lane:
        return 0.056
    return 0.044


def make_region_palette(layers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    palette = []
    for region_id, name, lane, *_rest in REGION_SPECS:
        color = layers[lane].get("average_hex")
        if not isinstance(color, str) or not color.startswith("#"):
            fail(f"{lane}.average_hex must be a hex color")
        palette.append({"region_id": region_id, "name": name, "color_hex": color})
    return palette


def make_regions(
    layers: dict[str, dict[str, Any]],
    *,
    center_x: float,
    bottom_y: float,
    scale_m_per_px: float,
    profile_landmarks: dict[str, float],
) -> list[dict[str, Any]]:
    regions = []
    for region_id, name, lane, parent, pivot_joint, draw_layer, family in REGION_SPECS:
        layer = layers[lane]
        bbox = require_bbox(layer.get("bbox"), f"{lane}.bbox")
        contour = contour_from_bbox(lane, bbox, center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
        pivot = add_depth(lane_center(layers, lane, center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), y_depth_for_name(name))
        shape: dict[str, Any] = {
            "type": "extruded_contour",
            "source_shape_family": family,
            "pivot_m": pivot,
            "depth_m": shape_depth_for_lane(lane, profile_landmarks),
            "bevel_m": 0.006 if lane not in {"torso", "pelvis", "foot_left", "foot_right"} else 0.008,
            "outline_m": 0.0035 if lane not in {"torso", "pelvis", "head", "foot_left", "foot_right"} else 0.004,
            "source_lane": lane,
            "source_bbox_px": bbox,
            "source_pixels": int(layer.get("pixels", 0)),
            "source_mask": layer.get("mask"),
            "source_cutout": layer.get("cutout"),
            "contour_xz_m": contour,
        }
        if name in SYMMETRY_ROLES:
            shape["symmetry_role"] = SYMMETRY_ROLES[name]
        regions.append(
            {
                "region_id": region_id,
                "name": name,
                "parent_region": parent,
                "pivot_joint": pivot_joint,
                "draw_layer": draw_layer,
                "shape": shape,
            }
        )
    return regions


def make_joints(
    layers: dict[str, dict[str, Any]],
    *,
    center_x: float,
    bottom_y: float,
    scale_m_per_px: float,
) -> list[dict[str, Any]]:
    torso_center = lane_center(layers, "torso", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
    pelvis_center = lane_center(layers, "pelvis", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
    neck_center = lane_center(layers, "neck", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
    head_center = lane_center(layers, "head", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
    return [
        {"joint_id": "root", "parent_joint": None, "pivot_m": [0.0, 0.0, 0.0], "joint_type": "root", "control": "root_xy"},
        {"joint_id": "shadow_anchor", "parent_joint": "root", "pivot_m": [0.0, 0.0, 0.0], "joint_type": "anchor", "control": "shadow_anchor"},
        {"joint_id": "pelvis", "parent_joint": "root", "pivot_m": add_depth(pelvis_center, -0.015), "joint_type": "hinge", "control": "pelvis_rotate", "range_deg": [-45, 45]},
        {"joint_id": "chest", "parent_joint": "pelvis", "pivot_m": add_depth(torso_center, -0.025), "joint_type": "hinge", "control": "torso_rotate", "range_deg": [-60, 60]},
        {"joint_id": "neck", "parent_joint": "chest", "pivot_m": add_depth(neck_center, -0.035), "joint_type": "ball_socket", "control": "neck_rotate", "range_deg": [-35, 35]},
        {"joint_id": "head", "parent_joint": "neck", "pivot_m": add_depth(head_center, -0.05), "joint_type": "ball_socket", "control": "head_rotate", "range_deg": [-45, 45]},
        {"joint_id": "shoulder_L", "parent_joint": "chest", "pivot_m": add_depth(joint_between(layers, "torso", "upper_arm_left", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), -0.055), "joint_type": "ball_socket", "control": "arm_L_raise", "range_deg": [-90, 90]},
        {"joint_id": "elbow_L", "parent_joint": "shoulder_L", "pivot_m": add_depth(joint_between(layers, "upper_arm_left", "lower_arm_left", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), -0.055), "joint_type": "hinge", "control": "arm_L_bend", "range_deg": [0, 150]},
        {"joint_id": "wrist_L", "parent_joint": "elbow_L", "pivot_m": add_depth(joint_between(layers, "lower_arm_left", "hand_left", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), -0.06), "joint_type": "hinge", "control": "hand_L_rotate", "range_deg": [-45, 45]},
        {"joint_id": "shoulder_R", "parent_joint": "chest", "pivot_m": add_depth(joint_between(layers, "torso", "upper_arm_right", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), 0.03), "joint_type": "ball_socket", "control": "arm_R_raise", "range_deg": [-90, 90]},
        {"joint_id": "elbow_R", "parent_joint": "shoulder_R", "pivot_m": add_depth(joint_between(layers, "upper_arm_right", "lower_arm_right", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), 0.03), "joint_type": "hinge", "control": "arm_R_bend", "range_deg": [0, 150]},
        {"joint_id": "wrist_R", "parent_joint": "elbow_R", "pivot_m": add_depth(joint_between(layers, "lower_arm_right", "hand_right", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), 0.03), "joint_type": "hinge", "control": "hand_R_rotate", "range_deg": [-45, 45]},
        {"joint_id": "hip_L", "parent_joint": "pelvis", "pivot_m": add_depth(joint_between(layers, "pelvis", "upper_leg_left", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), -0.035), "joint_type": "ball_socket", "control": "leg_L_raise", "range_deg": [-90, 90]},
        {"joint_id": "knee_L", "parent_joint": "hip_L", "pivot_m": add_depth(joint_between(layers, "upper_leg_left", "lower_leg_left", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), -0.035), "joint_type": "hinge", "control": "leg_L_bend", "range_deg": [0, 150]},
        {"joint_id": "ankle_L", "parent_joint": "knee_L", "pivot_m": add_depth(joint_between(layers, "lower_leg_left", "foot_left", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), -0.04), "joint_type": "hinge", "control": "foot_L_rotate", "range_deg": [-45, 45]},
        {"joint_id": "hip_R", "parent_joint": "pelvis", "pivot_m": add_depth(joint_between(layers, "pelvis", "upper_leg_right", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), 0.025), "joint_type": "ball_socket", "control": "leg_R_raise", "range_deg": [-90, 90]},
        {"joint_id": "knee_R", "parent_joint": "hip_R", "pivot_m": add_depth(joint_between(layers, "upper_leg_right", "lower_leg_right", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), 0.025), "joint_type": "hinge", "control": "leg_R_bend", "range_deg": [0, 150]},
        {"joint_id": "ankle_R", "parent_joint": "knee_R", "pivot_m": add_depth(joint_between(layers, "lower_leg_right", "foot_right", center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px), 0.02), "joint_type": "hinge", "control": "foot_R_rotate", "range_deg": [-45, 45]},
    ]


def joint_map(joints: list[dict[str, Any]]) -> dict[str, list[float]]:
    return {joint["joint_id"]: joint["pivot_m"] for joint in joints}


def socket_at(joints: dict[str, list[float]], joint_id: str, dx: float, dy: float, dz: float) -> list[float]:
    pivot = joints[joint_id]
    return [round(pivot[0] + dx, 6), round(pivot[1] + dy, 6), round(pivot[2] + dz, 6)]


def make_sockets(joints: list[dict[str, Any]], profile_landmarks: dict[str, float]) -> list[dict[str, Any]]:
    jm = joint_map(joints)
    foot_forward = profile_landmarks["foot_forward_m"]
    return [
        {"socket_id": "head_socket", "joint_id": "head", "position_m": socket_at(jm, "head", 0.0, -0.025, 0.19), "role": "hat_hair_face_overlay"},
        {"socket_id": "face_socket", "joint_id": "head", "position_m": socket_at(jm, "head", -0.025, -0.04, -0.02), "role": "face_direction"},
        {"socket_id": "chest_socket", "joint_id": "chest", "position_m": socket_at(jm, "chest", 0.0, -0.05, 0.02), "role": "shirt_armor_front"},
        {"socket_id": "back_socket", "joint_id": "chest", "position_m": socket_at(jm, "chest", 0.0, 0.05, 0.02), "role": "cape_backpack"},
        {"socket_id": "hand_L_socket", "joint_id": "wrist_L", "position_m": socket_at(jm, "wrist_L", -0.025, -0.025, -0.05), "role": "held_item_left"},
        {"socket_id": "hand_R_socket", "joint_id": "wrist_R", "position_m": socket_at(jm, "wrist_R", 0.025, -0.025, -0.05), "role": "held_item_right"},
        {"socket_id": "hip_socket", "joint_id": "pelvis", "position_m": socket_at(jm, "pelvis", 0.0, -0.04, -0.02), "role": "belt_pouch_scabbard"},
        {"socket_id": "foot_L_socket", "joint_id": "ankle_L", "position_m": socket_at(jm, "ankle_L", -foot_forward * 0.35, -0.035, -0.13), "role": "ground_contact_left"},
        {"socket_id": "foot_R_socket", "joint_id": "ankle_R", "position_m": socket_at(jm, "ankle_R", foot_forward * 0.35, -0.02, -0.13), "role": "ground_contact_right"},
    ]


def make_controls() -> list[dict[str, Any]]:
    return [
        {"control": "root_x", "type": "translate_x", "range": [-0.64, 0.64], "default": 0.0},
        {"control": "root_y", "type": "translate_y", "range": [-0.32, 0.32], "default": 0.0},
        {"control": "pelvis_rotate", "type": "rotate", "range": [-45, 45], "default": 0.0},
        {"control": "torso_rotate", "type": "rotate", "range": [-60, 60], "default": 0.0},
        {"control": "head_rotate", "type": "rotate", "range": [-45, 45], "default": 0.0},
        {"control": "arm_L_raise", "type": "rotate", "range": [-90, 90], "default": 0.0},
        {"control": "arm_L_bend", "type": "rotate", "range": [0, 150], "default": 0.0},
        {"control": "arm_R_raise", "type": "rotate", "range": [-90, 90], "default": 0.0},
        {"control": "arm_R_bend", "type": "rotate", "range": [0, 150], "default": 0.0},
        {"control": "leg_L_raise", "type": "rotate", "range": [-90, 90], "default": 0.0},
        {"control": "leg_L_bend", "type": "rotate", "range": [0, 150], "default": 0.0},
        {"control": "leg_R_raise", "type": "rotate", "range": [-90, 90], "default": 0.0},
        {"control": "leg_R_bend", "type": "rotate", "range": [0, 150], "default": 0.0},
        {"control": "foot_L_rotate", "type": "rotate", "range": [-45, 45], "default": 0.0},
        {"control": "foot_R_rotate", "type": "rotate", "range": [-45, 45], "default": 0.0},
        {"control": "body_squash", "type": "scale_y", "range": [0.8, 1.2], "default": 1.0},
        {"control": "body_stretch", "type": "scale_z", "range": [0.8, 1.2], "default": 1.0},
    ]


def compile_recipe(source_bundle: dict[str, Any], source_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if source_bundle.get("schema") != SOURCE_SCHEMA:
        fail(f"source bundle schema must be {SOURCE_SCHEMA}")
    target_asset_id = require_string(source_bundle.get("target_asset_id"), "target_asset_id")
    profile = load_profile(source_bundle["human_profile_source"])
    profile_landmarks = scaled_profile_landmarks(profile)
    lane_source = source_bundle["region_lane_source"]
    manifest_path = Path(require_string(lane_source.get("manifest_path"), "region_lane_source.manifest_path"))
    region_manifest = load_json_object(manifest_path)
    occupied_bbox = require_bbox(region_manifest.get("occupied_bbox_pixels"), "region_manifest.occupied_bbox_pixels")
    x0, y0, x1, y1 = occupied_bbox
    occupied_height_px = y1 - y0 + 1
    center_x = (x0 + x1) / 2.0
    bottom_y = float(y1)
    scale_m_per_px = round(float(profile["body_height_m"]) / occupied_height_px, 9)
    layers = layer_by_lane(region_manifest)
    missing = sorted({spec[2] for spec in REGION_SPECS} - set(layers))
    if missing:
        fail(f"region manifest missing lanes: {', '.join(missing)}")

    joints = make_joints(layers, center_x=center_x, bottom_y=bottom_y, scale_m_per_px=scale_m_per_px)
    recipe = {
        "schema": RECIPE_SCHEMA,
        "asset_id": target_asset_id,
        "asset_family": "character_animation_foundation",
        "style": "stylized_pixel_body_mannequin",
        "purpose": "Reusable rigid body mannequin rig for low-compute animation planning, body region fills, pivots, sockets, draw order, and later clothing or equipment overlays.",
        "source_reference": {
            "source_bundle": str(source_path),
            "human_profile_source": profile["source_path"],
            "human_profile_id": profile["profile_id"],
            "region_manifest": str(manifest_path),
            "region_image_paths": lane_source.get("image_paths", {}),
            "reference_role": "compiled from local human profile dimensions and extracted region-map lanes",
            "not_claimed": ["true anatomical measurement", "final character skin", "facial expression rig", "game engine controller"],
        },
        "working_size_px": [128, 128],
        "export_size_px_options": [[64, 64], [96, 96]],
        "origin": "bottom_center",
        "view": "three_quarter_front",
        "coordinate_system": {
            "space": "local_xyz_m",
            "unit": "meter",
            "x": "left/right",
            "y": "depth; negative y faces camera",
            "z": "height/up",
        },
        "rules": {
            "body_parts_are_rigid_segments": True,
            "segment_origins_are_pivots": True,
            "region_ids_drive_color_masks": True,
            "overlays_define_appearance": True,
            "blender_adapter_consumes_this_recipe": True,
            "blender_adapter_must_not_invent_regions": True,
        },
        "measurement_profile": {
            "profile_id": profile["profile_id"],
            "display_name": profile["display_name"],
            "sex_class": profile["sex_class"],
            "population_basis": profile["population_basis"],
            "stature_percentile": profile["stature_percentile"],
            "body_height_m": profile["body_height_m"],
            "scaled_landmarks_m": profile_landmarks,
            "source_note": "Used for body-height scale and provenance; extracted image lanes drive stylized silhouette.",
        },
        "source_projection": {
            "method": source_bundle["projection"]["method"],
            "region_manifest_size_px": [region_manifest["width"], region_manifest["height"]],
            "occupied_bbox_px": occupied_bbox,
            "center_x_px": round(center_x, 6),
            "bottom_y_px": round(bottom_y, 6),
            "scale_m_per_px": scale_m_per_px,
            "body_height_m": profile["body_height_m"],
        },
        "silhouette_strategy": {
            "method": "source_bbox_contour_extrusion",
            "measurement_note": "The reference is a 3/4 projected pixel rig. This recipe stores compiled projected silhouettes, not true body-depth measurements.",
            "symmetry_rule": "Limbs are paired as mirrored silhouette families, then separated by draw order and y-depth offsets for the 3/4 view.",
            "shared_shape_families": ["upper_arm_pair", "lower_arm_pair", "hand_pair", "upper_leg_pair", "lower_leg_pair", "foot_pair"],
            "mirrored_pairs": [
                ["upper_arm_L", "upper_arm_R"],
                ["lower_arm_L", "lower_arm_R"],
                ["hand_L", "hand_R"],
                ["upper_leg_L", "upper_leg_R"],
                ["lower_leg_L", "lower_leg_R"],
                ["foot_L", "foot_R"],
            ],
        },
        "region_palette": make_region_palette(layers),
        "regions": make_regions(
            layers,
            center_x=center_x,
            bottom_y=bottom_y,
            scale_m_per_px=scale_m_per_px,
            profile_landmarks=profile_landmarks,
        ),
        "joints": joints,
        "sockets": make_sockets(joints, profile_landmarks),
        "draw_order": DRAW_ORDER,
        "controls": make_controls(),
        "required_pose_sets": [
            {"pose_set_id": "idle_loop_v0", "frame_count": 6, "purpose": "standing breathing loop"},
            {"pose_set_id": "walk_loop_v0", "frame_count": 8, "purpose": "reusable walk contact and passing frames"},
            {"pose_set_id": "hurt_reaction_v0", "frame_count": 3, "purpose": "impact reaction check"},
        ],
        "validation_checks": [
            "feet stay on baseline in neutral pose",
            "body remains inside frame bounds",
            "left and right parts do not swap",
            "pivot positions are stable across poses",
            "limbs do not collapse or break",
            "region IDs remain stable across frames",
            "sockets exist and export correct positions",
        ],
    }
    report = {
        "schema": "humanoid_body_mannequin_compiler_report_v0",
        "source_bundle_schema": source_bundle["schema"],
        "source_bundle_id": source_bundle["bundle_id"],
        "source_bundle_path": str(source_path),
        "target_asset_id": target_asset_id,
        "profile_id": profile["profile_id"],
        "body_height_m": profile["body_height_m"],
        "region_manifest": str(manifest_path),
        "region_count": len(recipe["regions"]),
        "joint_count": len(recipe["joints"]),
        "socket_count": len(recipe["sockets"]),
        "occupied_bbox_px": occupied_bbox,
        "scale_m_per_px": scale_m_per_px,
        "rules": {
            "uses_human_profile_source": True,
            "uses_extracted_region_lane_bboxes": True,
            "stores_mask_paths_as_provenance": True,
            "imports_blender": False,
            "manual_contour_coordinates": False,
        },
    }
    return recipe, report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile a humanoid mannequin rig recipe from local human profile and extracted region lane sources.")
    parser.add_argument("--source-bundle", type=Path, default=DEFAULT_SOURCE_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true", help="Compile and report without writing the recipe.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    source_path = args.source_bundle if args.source_bundle.is_absolute() else ROOT / args.source_bundle
    source_bundle = load_json_object(source_path)
    recipe, report = compile_recipe(source_bundle, source_path)
    if not args.check:
        out = args.out if args.out.is_absolute() else ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS humanoid mannequin rig compile: "
        f"regions={report['region_count']} profile={report['profile_id']} scale={report['scale_m_per_px']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
