#!/usr/bin/env python3
"""Compile folded hex terrain into a plot-aware shared vertex graph.

This upgrades cells from flat samples into connected plots:

hex cells -> shared corner vertices + shared edge midpoints -> six edge
profiles -> sockets -> seamless 12-triangle radial top mesh plan

No Blender, image, or mesh file is created here.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "goal" / "architecture" / "hex_terrain_fold_sites_v0" / "sites"
OUT_DIR = ROOT / "goal" / "architecture" / "hex_plot_vertex_graph_v0"
GRAPH_DIR = OUT_DIR / "graphs"
REPORT_PATH = OUT_DIR / "hex_plot_vertex_graph_v0_report.md"
POINT_REPORT_PATH = OUT_DIR / "hex_point_connection_graph_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "hex_plot_vertex_graph_v0.receipt.json"
SHARED_MIDPOINT_RECEIPT_PATH = ROOT / "goal" / "receipts" / "shared_midpoint_radial_hex_terrain_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}

DIRECTIONS = [
    {"side": "east", "delta": (1, 0), "corners": (5, 0)},
    {"side": "north_east", "delta": (1, -1), "corners": (4, 5)},
    {"side": "north_west", "delta": (0, -1), "corners": (3, 4)},
    {"side": "west", "delta": (-1, 0), "corners": (2, 3)},
    {"side": "south_west", "delta": (-1, 1), "corners": (1, 2)},
    {"side": "south_east", "delta": (0, 1), "corners": (0, 1)},
]

TILED_Y_DOWN_EVEN_R_DIRECTIONS = [
    {"side": "east", "delta": (1, 0), "corners": (5, 0)},
    {"side": "north_east", "delta": (0, -1), "corners": (0, 1)},
    {"side": "north_west", "delta": (-1, -1), "corners": (1, 2)},
    {"side": "west", "delta": (-1, 0), "corners": (2, 3)},
    {"side": "south_west", "delta": (-1, 1), "corners": (3, 4)},
    {"side": "south_east", "delta": (0, 1), "corners": (4, 5)},
]

TILED_Y_DOWN_ODD_R_DIRECTIONS = [
    {"side": "east", "delta": (1, 0), "corners": (5, 0)},
    {"side": "north_east", "delta": (1, -1), "corners": (0, 1)},
    {"side": "north_west", "delta": (0, -1), "corners": (1, 2)},
    {"side": "west", "delta": (-1, 0), "corners": (2, 3)},
    {"side": "south_west", "delta": (0, 1), "corners": (3, 4)},
    {"side": "south_east", "delta": (1, 1), "corners": (4, 5)},
]

RADIAL_EDGE_BY_CORNER_START = {
    0: "south_east",
    1: "south_west",
    2: "west",
    3: "north_west",
    4: "north_east",
    5: "east",
}

EDGE_PROFILE_RULE_TABLE = [
    {
        "rule_id": "building_pad_boundary",
        "priority": 90,
        "requires": {"tags": ["building_pad_edge"]},
        "profile": "foundation_snap",
        "mesh": "pad_locked_top_plus_boundary_adapter",
        "walkability": "walkable_or_socket",
    },
    {
        "rule_id": "road_single_band_override",
        "priority": 80,
        "requires": {"delta_band": 1, "tags": ["road"]},
        "profile": "road_ramp",
        "mesh": "shared_midpoint_12_tri_top",
        "walkability": "walkable",
    },
    {
        "rule_id": "cliff_delta_two_plus",
        "priority": 30,
        "requires": {"delta_band_min": 2},
        "profile": "cliff_fault",
        "mesh": "upper_top_plus_vertical_wall",
        "walkability": "blocked_without_connector",
    },
    {
        "rule_id": "soft_single_band",
        "priority": 20,
        "requires": {"delta_band": 1},
        "profile": "soft_fold",
        "mesh": "shared_midpoint_12_tri_top",
        "walkability": "walkable_with_cost",
    },
    {
        "rule_id": "flat_same_band",
        "priority": 10,
        "requires": {"delta_band": 0},
        "profile": "shared_flat",
        "mesh": "shared_midpoint_12_tri_top",
        "walkability": "walkable",
    },
]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def directions_for_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    return DIRECTIONS


def directions_for_cell(source: dict[str, Any], cell: dict[str, Any]) -> list[dict[str, Any]]:
    if source.get("hex_grid", {}).get("edge_corner_order") == "tiled_odd_r_y_down_v0":
        return TILED_Y_DOWN_ODD_R_DIRECTIONS if int(cell["r"]) % 2 else TILED_Y_DOWN_EVEN_R_DIRECTIONS
    return directions_for_source(source)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hex_points(radius: float) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos(math.radians(30.0 + i * 60.0)),
            radius * math.sin(math.radians(30.0 + i * 60.0)),
        )
        for i in range(6)
    ]


def quantize_coord(value: float) -> float:
    # Source terrain assemblies store world coordinates at 6 decimals. Hex
    # corner math can otherwise land on opposite sides of the 5th decimal for
    # the same physical endpoint. Four decimals is still sub-millimeter scale
    # in the current abstract-meter map while keeping neighbor keys stable.
    rounded = round(value, 4)
    return 0.0 if rounded == 0.0 else rounded


def vertex_key(x: float, y: float) -> str:
    return f"{quantize_coord(x):.4f}:{quantize_coord(y):.4f}"


def corner_key_for_cell(cell: dict[str, Any], corner_points: list[tuple[float, float]], corner_index: int) -> str:
    px, py = corner_points[corner_index]
    return vertex_key(float(cell["world_x"]) + px, float(cell["world_y"]) + py)


def midpoint_key_for_cell(cell: dict[str, Any], corner_points: list[tuple[float, float]], corner_a: int, corner_b: int) -> str:
    ax, ay = corner_points[corner_a]
    bx, by = corner_points[corner_b]
    return vertex_key(float(cell["world_x"]) + (ax + bx) * 0.5, float(cell["world_y"]) + (ay + by) * 0.5)


def canonical_raw_edge_key(cell: dict[str, Any], corner_points: list[tuple[float, float]], corner_a: int, corner_b: int) -> str:
    left = corner_key_for_cell(cell, corner_points, corner_a)
    right = corner_key_for_cell(cell, corner_points, corner_b)
    return "|".join(sorted((left, right)))


def height_band_step(source: dict[str, Any]) -> float:
    step = float(source.get("hex_grid", {}).get("vertical_step") or 0.0)
    if step <= 0.0:
        step = float(source.get("map_cube", {}).get("recommended_defaults", {}).get("vertical_step") or 0.0)
    if step <= 0.0:
        step = 0.25
    return step


def height_band_for_height(height_m: float, step: float) -> int:
    return int(math.floor((float(height_m) / step) + 0.5))


def tags_for_cell(cell: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    for field in ("movement_tags", "structure_socket_tags"):
        for tag in cell.get(field, []) or []:
            tags.add(str(tag))
    if cell.get("surface_type") in {"road", "stone_road"} or "route" in tags or "narrow_route" in tags:
        tags.add("road")
    if cell.get("buildable"):
        tags.add("buildable")
    return tags


def edge_tags(cell: dict[str, Any], neighbor: dict[str, Any] | None) -> set[str]:
    tags = tags_for_cell(cell)
    if neighbor is not None:
        tags |= tags_for_cell(neighbor)
        if bool(cell.get("buildable")) != bool(neighbor.get("buildable")):
            tags.add("buildable_boundary")
    return tags


def edge_profile_rule_for(delta_band: int, tags: set[str]) -> dict[str, Any]:
    for rule in sorted(EDGE_PROFILE_RULE_TABLE, key=lambda row: int(row["priority"]), reverse=True):
        requires = rule["requires"]
        required_tags = set(requires.get("tags", []))
        if required_tags and not required_tags.issubset(tags):
            continue
        if "delta_band" in requires and int(requires["delta_band"]) != delta_band:
            continue
        if "delta_band_min" in requires and delta_band < int(requires["delta_band_min"]):
            continue
        return rule
    fail(f"no edge profile rule matched delta_band={delta_band} tags={sorted(tags)}")


def transition_class_for_delta_band(delta_band: int) -> str:
    if delta_band == 0:
        return "shared_flat"
    if delta_band == 1:
        return "soft_fold_or_step"
    return "cliff_fault"


def legacy_profile_for_rule(rule_id: str) -> tuple[str, str]:
    if rule_id == "flat_same_band":
        return "flat_join", "walkable"
    if rule_id == "soft_single_band":
        return "smooth_slope", "walkable_with_cost"
    if rule_id == "road_single_band_override":
        return "smooth_slope", "walkable"
    if rule_id == "building_pad_boundary":
        return "hard_step", "structure_socket"
    if rule_id == "cliff_delta_two_plus":
        return "cliff_drop", "blocked_without_connector"
    fail(f"unknown edge profile rule {rule_id}")


def classify_edge_transition(
    *,
    cell: dict[str, Any],
    neighbor: dict[str, Any] | None,
    step: float,
) -> dict[str, Any]:
    cell_band = height_band_for_height(float(cell["final_height"]), step)
    if neighbor is None:
        return {
            "height_band": cell_band,
            "neighbor_height_band": None,
            "height_m": round(float(cell["final_height"]), 6),
            "neighbor_height_m": None,
            "signed_delta_band": None,
            "delta_band": None,
            "transition_class": "chunk_boundary",
            "profile_rule_id": "chunk_boundary",
            "terrain_profile": "chunk_boundary",
            "edge_profile": "chunk_boundary",
            "connector": "chunk_boundary",
            "profile_mesh": "chunk_skirt",
            "walkability": "chunk_boundary",
        }
    neighbor_band = height_band_for_height(float(neighbor["final_height"]), step)
    signed_delta_band = neighbor_band - cell_band
    delta_band = abs(signed_delta_band)
    rule = edge_profile_rule_for(delta_band, edge_tags(cell, neighbor))
    edge_profile_name, connector = legacy_profile_for_rule(str(rule["rule_id"]))
    return {
        "height_band": cell_band,
        "neighbor_height_band": neighbor_band,
        "height_m": round(float(cell["final_height"]), 6),
        "neighbor_height_m": round(float(neighbor["final_height"]), 6),
        "signed_delta_band": signed_delta_band,
        "delta_band": delta_band,
        "transition_class": transition_class_for_delta_band(delta_band),
        "profile_rule_id": rule["rule_id"],
        "terrain_profile": rule["profile"],
        "edge_profile": edge_profile_name,
        "connector": connector,
        "profile_mesh": rule["mesh"],
        "walkability": rule["walkability"],
    }


def edge_profile(delta: float, rules: dict[str, Any]) -> tuple[str, str]:
    abs_delta = abs(delta)
    if abs_delta <= float(rules["flat_delta_max"]):
        return "flat_join", "walkable"
    if abs_delta <= float(rules["step_delta_max"]):
        return "smooth_slope", "walkable_with_cost"
    if abs_delta <= float(rules["ledge_delta_max"]):
        return "hard_step", "step_connector"
    return "cliff_drop", "blocked_without_connector"


def seam_policy_for(profile: str, connector: str) -> dict[str, Any]:
    if profile in {"flat_join", "smooth_slope"}:
        return {
            "seam_policy": "shared_surface",
            "mesh_behavior": "share_corner_vertices_and_do_not_emit_vertical_seam_mesh",
            "affordance_outputs": ["walkable_surface", "continuous_route"],
        }
    if profile == "hard_step":
        return {
            "seam_policy": "split_riser",
            "mesh_behavior": "emit_vertical_riser_between_height_levels",
            "affordance_outputs": ["step_connector", "minor_obstruction", "cover_candidate"],
        }
    if profile == "cliff_drop":
        return {
            "seam_policy": "split_cliff",
            "mesh_behavior": "emit_vertical_cliff_wall_between_height_levels",
            "affordance_outputs": ["fall_edge", "line_of_sight_break", connector],
        }
    if profile == "chunk_boundary":
        return {
            "seam_policy": "chunk_skirt",
            "mesh_behavior": "emit_outer_boundary_skirt_to_base_plane",
            "affordance_outputs": ["map_boundary", "chunk_edge"],
        }
    return {
        "seam_policy": "blocked_wall",
        "mesh_behavior": "emit_or_reserve_blocking_wall_geometry",
        "affordance_outputs": ["blocked", connector],
    }


def edge_fold_policy_for(
    profile: str,
    connector: str,
    delta: float | None,
    source: dict[str, Any],
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = source.get("edge_fold_policy", {})
    if (
        profile in {"hard_step", "smooth_slope"}
        and delta is not None
        and policy.get("hard_step") == "fold_meet_halfway"
        and (classification is None or classification.get("delta_band") == 1)
    ):
        max_delta = float(policy.get("max_delta", 1.0))
        if abs(float(delta)) <= max_delta:
            return {
                "seam_policy": "fold_meet_halfway",
                "mesh_behavior": "emit_two_sloped_fold_faces_meeting_at_mid_edge",
                "affordance_outputs": ["folded_slope", "walkable_transition_candidate", connector],
                "fold_bias": float(policy.get("fold_bias", 0.5)),
            }
    return seam_policy_for(profile, connector)


def collect_corner_vertices(source: dict[str, Any], radius: float) -> dict[str, dict[str, Any]]:
    points = hex_points(radius)
    vertices: dict[str, dict[str, Any]] = {}
    for cell in source["hex_cells"]:
        cx = float(cell["world_x"])
        cy = float(cell["world_y"])
        for corner_index, (px, py) in enumerate(points):
            x = quantize_coord(cx + px)
            y = quantize_coord(cy + py)
            key = vertex_key(x, y)
            entry = vertices.setdefault(
                key,
                {
                    "world_x": x,
                    "world_y": y,
                    "adjacent_cells": [],
                    "height_samples": [],
                    "fold_samples": [],
                    "corner_indices": [],
                    "occurrences": [],
                },
            )
            entry["adjacent_cells"].append(cell["cell_id"])
            entry["height_samples"].append(float(cell["final_height"]))
            entry["fold_samples"].append(float(cell["fold_offset"]))
            entry["corner_indices"].append(corner_index)
            entry["occurrences"].append(
                {
                    "cell_id": cell["cell_id"],
                    "q": cell["q"],
                    "r": cell["r"],
                    "corner_index": corner_index,
                    "height": float(cell["final_height"]),
                    "fold_offset": float(cell["fold_offset"]),
                }
            )
    return vertices


def find_parent(parent: dict[int, int], item: int) -> int:
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def union_parent(parent: dict[int, int], left: int, right: int) -> None:
    left_root = find_parent(parent, left)
    right_root = find_parent(parent, right)
    if left_root != right_root:
        parent[right_root] = left_root


def final_vertex_sort_key(row: dict[str, Any]) -> tuple[float, float, str]:
    return (float(row["world_y"]), float(row["world_x"]), row["_pending_id"])


def finalize_vertices(
    vertices: dict[str, dict[str, Any]],
    cells_by_coord: dict[tuple[int, int], dict[str, Any]],
    cells_by_id: dict[str, dict[str, Any]],
    edge_rules: dict[str, Any],
    source: dict[str, Any],
    step: float,
    directions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], str], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    corner_ref_to_id: dict[tuple[str, int], str] = {}
    split_raw_corner_count = 0
    split_extra_vertex_count = 0
    corner_cap_drafts: list[dict[str, Any]] = []
    pending_rows: list[dict[str, Any]] = []

    for key in sorted(vertices, key=lambda item: (float(item.split(":")[1]), float(item.split(":")[0]))):
        entry = vertices[key]
        occurrences = entry["occurrences"]
        parent = {index: index for index in range(len(occurrences))}
        occurrence_index_by_cell = {occurrence["cell_id"]: index for index, occurrence in enumerate(occurrences)}

        for index, occurrence in enumerate(occurrences):
            cell = cells_by_id[occurrence["cell_id"]]
            corner_index = occurrence["corner_index"]
            for direction in directions_for_cell(source, cell):
                if corner_index not in direction["corners"]:
                    continue
                dq, dr = direction["delta"]
                neighbor = cells_by_coord.get((cell["q"] + dq, cell["r"] + dr))
                if neighbor is None:
                    continue
                neighbor_index = occurrence_index_by_cell.get(neighbor["cell_id"])
                if neighbor_index is None:
                    continue
                classification = classify_edge_transition(cell=cell, neighbor=neighbor, step=step)
                policy = edge_fold_policy_for(
                    classification["edge_profile"],
                    classification["connector"],
                    round(float(neighbor["final_height"]) - float(cell["final_height"]), 6),
                    source,
                    classification,
                )
                if policy["seam_policy"] == "shared_surface":
                    union_parent(parent, index, neighbor_index)

        # Hex corners can touch at a point without a full shared edge. Keep
        # smooth-height corner fans connected, but do not bridge hard risers or
        # cliffs through a third point contact.
        smooth_corner_delta_max = float(edge_rules["step_delta_max"])
        for left_index, left in enumerate(occurrences):
            for right_index in range(left_index + 1, len(occurrences)):
                right = occurrences[right_index]
                delta_qr = (int(right["q"]) - int(left["q"]), int(right["r"]) - int(left["r"]))
                reverse_delta_qr = (-delta_qr[0], -delta_qr[1])
                left_direction_deltas = {direction["delta"] for direction in directions_for_cell(source, cells_by_id[left["cell_id"]])}
                right_direction_deltas = {direction["delta"] for direction in directions_for_cell(source, cells_by_id[right["cell_id"]])}
                if delta_qr in left_direction_deltas or reverse_delta_qr in right_direction_deltas:
                    height_delta = float(right["height"]) - float(left["height"])
                    profile, connector = edge_profile(height_delta, edge_rules)
                    if seam_policy_for(profile, connector)["seam_policy"] != "shared_surface":
                        continue
                if abs(float(left["height"]) - float(right["height"])) <= smooth_corner_delta_max:
                    union_parent(parent, left_index, right_index)

        components: dict[int, list[dict[str, Any]]] = {}
        for index, occurrence in enumerate(occurrences):
            root = find_parent(parent, index)
            components.setdefault(root, []).append(occurrence)

        refined_components: list[list[dict[str, Any]]] = []
        # v0 shared-surface edges are authoritative after band classification:
        # do not split a connected shared component by height range afterward,
        # or a single edge can retain a shared midpoint while losing one corner.
        max_shared_height_range = float("inf")
        for group in components.values():
            sorted_group = sorted(group, key=lambda item: (float(item["height"]), item["cell_id"]))
            current: list[dict[str, Any]] = []
            current_min = 0.0
            for item in sorted_group:
                item_height = float(item["height"])
                if not current:
                    current = [item]
                    current_min = item_height
                    continue
                if item_height - current_min <= max_shared_height_range:
                    current.append(item)
                else:
                    refined_components.append(current)
                    current = [item]
                    current_min = item_height
            if current:
                refined_components.append(current)

        if len(refined_components) > 1:
            split_raw_corner_count += 1
            split_extra_vertex_count += len(refined_components) - 1

        raw_corner_pending_groups: list[dict[str, Any]] = []
        for group_index, group in enumerate(refined_components):
            final_height = sum(item["height"] for item in group) / len(group)
            fold_offset = sum(item["fold_offset"] for item in group) / len(group)
            adjacent_cells = sorted({item["cell_id"] for item in group})
            pending_id = f"pending_{len(pending_rows)}"
            pending_rows.append(
                {
                    "vertex_id": "",
                    "_pending_id": pending_id,
                    "raw_corner_key": key,
                    "split_group_index": group_index,
                    "world_x": entry["world_x"],
                    "world_y": entry["world_y"],
                    "final_height": round(final_height, 6),
                    "height_m": round(final_height, 6),
                    "height_band": height_band_for_height(final_height, step),
                    "fold_offset": round(fold_offset, 6),
                    "adjacent_cells": adjacent_cells,
                    "adjacent_cell_count": len(adjacent_cells),
                    "source_corner_count": len(group),
                    "height_rule": "seam_aware_average_shared_surface_only_v0",
                }
            )
            raw_corner_pending_groups.append(
                {
                    "pending_id": pending_id,
                    "height": round(final_height, 6),
                    "adjacent_cells": adjacent_cells,
                    "source_corner_count": len(group),
                }
            )
            for item in group:
                corner_ref_to_id[(item["cell_id"], item["corner_index"])] = f"pending_{len(pending_rows) - 1}"

        if len(raw_corner_pending_groups) > 1:
            heights = [float(group["height"]) for group in raw_corner_pending_groups]
            corner_cap_drafts.append(
                {
                    "cap_id": f"cap_{len(corner_cap_drafts):04d}",
                    "raw_corner_key": key,
                    "world_x": entry["world_x"],
                    "world_y": entry["world_y"],
                    "pending_vertex_ids": [group["pending_id"] for group in raw_corner_pending_groups],
                    "height_min": round(min(heights), 6),
                    "height_max": round(max(heights), 6),
                    "height_span": round(max(heights) - min(heights), 6),
                    "height_groups": raw_corner_pending_groups,
                    "mesh_behavior": "emit_small_vertical_corner_cap_between_split_corner_groups",
                    "seam_policy": "corner_seam_cap",
                    "affordance_outputs": ["seam_junction", "hole_closure"],
                }
            )

    pending_to_final: dict[str, str] = {}
    for index, row in enumerate(sorted(pending_rows, key=final_vertex_sort_key)):
        old_id = row.pop("_pending_id")
        vertex_id = f"v_{index:04d}"
        pending_to_final[old_id] = vertex_id
        row["vertex_id"] = vertex_id
        rows.append(row)

    corner_ref_to_id = {
        corner_ref: pending_to_final[pending_id]
        for corner_ref, pending_id in corner_ref_to_id.items()
    }
    corner_caps = []
    for draft in corner_cap_drafts:
        cap = dict(draft)
        cap["corner_vertex_ids"] = [pending_to_final[pending_id] for pending_id in cap.pop("pending_vertex_ids")]
        cap["height_groups"] = [
            {
                **group,
                "vertex_id": pending_to_final[group["pending_id"]],
            }
            for group in cap["height_groups"]
        ]
        for group in cap["height_groups"]:
            group.pop("pending_id")
        corner_caps.append(cap)
    summary = {
        "raw_corner_key_count": len(vertices),
        "emitted_corner_vertex_count": len(rows),
        "split_raw_corner_count": split_raw_corner_count,
        "split_extra_vertex_count": split_extra_vertex_count,
        "corner_seam_cap_count": len(corner_caps),
        "height_rule": "seam_aware_average_shared_surface_only_v0",
    }
    return rows, corner_ref_to_id, summary, corner_caps


def make_socket(cell: dict[str, Any]) -> dict[str, Any] | None:
    if not cell.get("buildable") and not cell.get("structure_socket_tags"):
        return None
    socket_type = "building_pad_candidate" if cell.get("buildable") else "terrain_anchor"
    return {
        "socket_id": f"{cell['cell_id']}_{socket_type}",
        "socket_type": socket_type,
        "position": [cell["world_x"], cell["world_y"], cell["final_height"]],
        "compatible_tags": cell.get("structure_socket_tags", []) or ["terrain_anchor"],
        "source_cell": cell["cell_id"],
    }


def make_neighbor_point_connection(
    *,
    connection_index: int,
    cell: dict[str, Any],
    neighbor: dict[str, Any],
    direction: dict[str, Any],
    corner_points: list[tuple[float, float]],
    corner_ref_to_id: dict[tuple[str, int], str],
) -> dict[str, Any]:
    neighbor_corner_by_raw_key = {
        corner_key_for_cell(neighbor, corner_points, corner_index): corner_index
        for corner_index in range(6)
    }
    point_pairs: list[dict[str, Any]] = []
    for source_corner_index in direction["corners"]:
        raw_key = corner_key_for_cell(cell, corner_points, source_corner_index)
        if raw_key not in neighbor_corner_by_raw_key:
            fail(
                "neighbor point connection mismatch: "
                f"{cell['cell_id']} {direction['side']} corner {source_corner_index} does not align with {neighbor['cell_id']}"
            )
        neighbor_corner_index = neighbor_corner_by_raw_key[raw_key]
        source_vertex_id = corner_ref_to_id[(cell["cell_id"], source_corner_index)]
        neighbor_vertex_id = corner_ref_to_id[(neighbor["cell_id"], neighbor_corner_index)]
        point_pairs.append(
            {
                "source_corner_index": source_corner_index,
                "neighbor_corner_index": neighbor_corner_index,
                "raw_corner_key": raw_key,
                "source_vertex_id": source_vertex_id,
                "neighbor_vertex_id": neighbor_vertex_id,
                "connection_state": "same_vertex" if source_vertex_id == neighbor_vertex_id else "split_vertex_same_xy",
            }
        )
    return {
        "connection_id": f"pc_{connection_index:05d}",
        "source_cell": cell["cell_id"],
        "neighbor_cell": neighbor["cell_id"],
        "side": direction["side"],
        "source_edge_corner_indices": list(direction["corners"]),
        "point_pairs": point_pairs,
        "rule": "edge_endpoints_connect_by_exact_matching_raw_corner_xy_before_mesh_policy",
    }


def make_midpoint_pending_key(
    *,
    cell: dict[str, Any],
    direction: dict[str, Any],
    neighbor: dict[str, Any] | None,
    raw_edge_key: str,
    policy: dict[str, Any],
) -> tuple[str, str]:
    if neighbor is not None and policy["seam_policy"] == "shared_surface":
        return raw_edge_key, "shared_edge"
    if neighbor is None:
        return f"{raw_edge_key}|boundary|{cell['cell_id']}|{direction['side']}", "cell_owned_boundary"
    return f"{raw_edge_key}|split|{cell['cell_id']}|{direction['side']}", "cell_owned_split_seam"


def register_edge_midpoint(
    *,
    registry: dict[str, dict[str, Any]],
    cell: dict[str, Any],
    direction: dict[str, Any],
    corner_points: list[tuple[float, float]],
    neighbor: dict[str, Any] | None,
    policy: dict[str, Any],
    classification: dict[str, Any],
    edge_vertices: list[str],
    step: float,
) -> str:
    corner_a, corner_b = direction["corners"]
    raw_edge_key = canonical_raw_edge_key(cell, corner_points, corner_a, corner_b)
    midpoint_key = midpoint_key_for_cell(cell, corner_points, corner_a, corner_b)
    pending_key, ownership_model = make_midpoint_pending_key(
        cell=cell,
        direction=direction,
        neighbor=neighbor,
        raw_edge_key=raw_edge_key,
        policy=policy,
    )
    x_str, y_str = midpoint_key.split(":")
    height_samples = [float(cell["final_height"])]
    if neighbor is not None and policy["seam_policy"] == "shared_surface":
        height_samples.append(float(neighbor["final_height"]))
    height_m = sum(height_samples) / len(height_samples)
    entry = registry.setdefault(
        pending_key,
        {
            "midpoint_id": "",
            "_pending_key": pending_key,
            "raw_edge_key": raw_edge_key,
            "raw_midpoint_key": midpoint_key,
            "world_x": float(x_str),
            "world_y": float(y_str),
            "height_m": round(height_m, 6),
            "height_band": height_band_for_height(height_m, step),
            "ownership_model": ownership_model,
            "incident_cells": [],
            "occurrences": [],
            "corner_vertex_ids": edge_vertices,
            "seam_policy": policy["seam_policy"],
            "edge_profile": classification["edge_profile"],
            "profile_rule_id": classification["profile_rule_id"],
            "terrain_profile": classification["terrain_profile"],
            "transition_class": classification["transition_class"],
            "delta_band": classification["delta_band"],
            "signed_delta_band_samples": [],
            "height_rule": "shared_surface_average_or_explicit_cell_owned_split_v0",
        },
    )
    entry["incident_cells"] = sorted(set(entry["incident_cells"]) | {cell["cell_id"]})
    if neighbor is not None and policy["seam_policy"] == "shared_surface":
        entry["incident_cells"] = sorted(set(entry["incident_cells"]) | {neighbor["cell_id"]})
    entry["occurrences"].append(
        {
            "cell_id": cell["cell_id"],
            "side": direction["side"],
            "neighbor": neighbor["cell_id"] if neighbor is not None else None,
            "corner_indices": [corner_a, corner_b],
            "seam_policy": policy["seam_policy"],
            "profile_rule_id": classification["profile_rule_id"],
        }
    )
    if classification["signed_delta_band"] is not None:
        entry["signed_delta_band_samples"].append(classification["signed_delta_band"])
    return pending_key


def finalize_edge_midpoints(
    registry: dict[str, dict[str, Any]],
    pending_refs: dict[tuple[str, str], str],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pending_to_final: dict[str, str] = {}
    sorted_entries = sorted(
        registry.values(),
        key=lambda row: (float(row["world_y"]), float(row["world_x"]), row["_pending_key"]),
    )
    for index, entry in enumerate(sorted_entries):
        pending_key = entry.pop("_pending_key")
        midpoint_id = f"m_{index:04d}"
        pending_to_final[pending_key] = midpoint_id
        entry["midpoint_id"] = midpoint_id
        entry["incident_cell_count"] = len(entry["incident_cells"])
        rows.append(entry)
    midpoint_ref_to_id = {
        ref: pending_to_final[pending_key]
        for ref, pending_key in pending_refs.items()
    }
    shared_midpoint_count = sum(1 for row in rows if row["ownership_model"] == "shared_edge")
    split_midpoint_count = sum(1 for row in rows if row["ownership_model"] == "cell_owned_split_seam")
    boundary_midpoint_count = sum(1 for row in rows if row["ownership_model"] == "cell_owned_boundary")
    summary = {
        "edge_midpoint_count": len(rows),
        "shared_midpoint_count": shared_midpoint_count,
        "split_midpoint_count": split_midpoint_count,
        "boundary_midpoint_count": boundary_midpoint_count,
        "height_rule": "shared_surface_average_or_explicit_cell_owned_split_v0",
    }
    return rows, midpoint_ref_to_id, summary


def reverse_side(side: str) -> str:
    opposites = {
        "east": "west",
        "north_east": "south_west",
        "north_west": "south_east",
        "west": "east",
        "south_west": "north_east",
        "south_east": "north_west",
    }
    return opposites[side]


def validate_compiled_graph(graph: dict[str, Any]) -> dict[str, Any]:
    plot_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    cracked_seams: list[dict[str, Any]] = []
    shared_checks = 0
    for plot in graph["hex_plots"]:
        for edge in plot["edges"]:
            neighbor_id = edge["neighbor"]
            if neighbor_id is None or edge["seam_policy"] != "shared_surface":
                continue
            neighbor_plot = plot_by_id[neighbor_id]
            neighbor_edge = next(
                candidate for candidate in neighbor_plot["edges"]
                if candidate["side"] == reverse_side(edge["side"])
            )
            shared_checks += 1
            if edge["edge_midpoint_id"] != neighbor_edge["edge_midpoint_id"]:
                cracked_seams.append(
                    {
                        "source_cell": plot["cell_id"],
                        "neighbor_cell": neighbor_id,
                        "side": edge["side"],
                        "reason": "shared_surface_midpoint_id_mismatch",
                        "source_midpoint_id": edge["edge_midpoint_id"],
                        "neighbor_midpoint_id": neighbor_edge["edge_midpoint_id"],
                    }
                )
            if set(edge["corner_vertex_ids"]) != set(neighbor_edge["corner_vertex_ids"]):
                cracked_seams.append(
                    {
                        "source_cell": plot["cell_id"],
                        "neighbor_cell": neighbor_id,
                        "side": edge["side"],
                        "reason": "shared_surface_corner_vertex_id_mismatch",
                        "source_corner_vertex_ids": edge["corner_vertex_ids"],
                        "neighbor_corner_vertex_ids": neighbor_edge["corner_vertex_ids"],
                    }
                )
    top_triangle_count = graph["mesh_plan"]["top_triangle_count"]
    expected_top_triangle_count = len(graph["hex_plots"]) * 12
    bad_delta_edges = [
        {
            "cell_id": plot["cell_id"],
            "side": edge["side"],
            "delta_band": edge["delta_band"],
            "transition_class": edge["transition_class"],
            "profile_rule_id": edge["profile_rule_id"],
        }
        for plot in graph["hex_plots"]
        for edge in plot["edges"]
        if edge["delta_band"] is not None
        and int(edge["delta_band"]) >= 2
        and edge["transition_class"] != "cliff_fault"
    ]
    validation = {
        "cell_count": len(graph["hex_plots"]),
        "corner_vertex_count": len(graph["corner_vertices"]),
        "edge_midpoint_count": len(graph["edge_midpoints"]),
        "top_triangle_count": top_triangle_count,
        "expected_top_triangle_count": expected_top_triangle_count,
        "top_triangle_count_matches": top_triangle_count == expected_top_triangle_count,
        "shared_midpoint_count": graph["edge_midpoint_summary"]["shared_midpoint_count"],
        "split_midpoint_count": graph["edge_midpoint_summary"]["split_midpoint_count"],
        "cracked_seam_count": len(cracked_seams),
        "cracked_seams": cracked_seams,
        "shared_surface_edge_checks": shared_checks,
        "delta_band_counts": graph["delta_band_summary"],
        "profile_counts": graph["profile_rule_summary"],
        "delta_two_plus_all_cliff_fault": not bad_delta_edges,
        "bad_delta_two_plus_edges": bad_delta_edges,
    }
    if validation["cracked_seam_count"] != 0:
        fail(f"{graph['graph_id']} has cracked seams: {cracked_seams[:3]}")
    if not validation["top_triangle_count_matches"]:
        fail(f"{graph['graph_id']} top triangle count {top_triangle_count} != {expected_top_triangle_count}")
    if bad_delta_edges:
        fail(f"{graph['graph_id']} has delta>=2 edges that are not cliff_fault: {bad_delta_edges[:3]}")
    return validation


def compile_graph(path: Path) -> dict[str, Any]:
    source = load_json(path)
    if source.get("schema") != "hex_terrain_fold_site_assembly_v0":
        fail(f"{path.relative_to(ROOT)} schema must be hex_terrain_fold_site_assembly_v0")
    if source.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    radius = float(source["hex_grid"]["radius"])
    corner_points = hex_points(radius)
    directions = directions_for_source(source)
    cells_by_coord = {(cell["q"], cell["r"]): cell for cell in source["hex_cells"]}
    cells_by_id = {cell["cell_id"]: cell for cell in source["hex_cells"]}
    edge_rules = source.get(
        "classification_rules",
        {
            "flat_delta_max": 0.15,
            "step_delta_max": 0.5,
            "ledge_delta_max": 1.0,
        },
    )
    step = height_band_step(source)
    raw_vertices = collect_corner_vertices(source, radius)
    corner_vertices, corner_ref_to_id, vertex_split_summary, corner_seam_caps = finalize_vertices(
        raw_vertices,
        cells_by_coord,
        cells_by_id,
        edge_rules,
        source,
        step,
        directions,
    )
    vertex_by_id = {vertex["vertex_id"]: vertex for vertex in corner_vertices}

    edge_counts: dict[str, int] = {}
    connector_counts: dict[str, int] = {}
    seam_policy_counts: dict[str, int] = {}
    delta_band_counts: dict[str, int] = {}
    transition_class_counts: dict[str, int] = {}
    profile_rule_counts: dict[str, int] = {}
    seam_facts: list[dict[str, Any]] = []
    seen_seam_facts: set[tuple[str, ...]] = set()
    point_connections: list[dict[str, Any]] = []
    point_connection_pair_count = 0
    same_vertex_pair_count = 0
    split_vertex_pair_count = 0
    boundary_edge_count = 0
    sockets: list[dict[str, Any]] = []
    plots: list[dict[str, Any]] = []
    top_triangles: list[dict[str, Any]] = []
    midpoint_registry: dict[str, dict[str, Any]] = {}
    midpoint_pending_refs: dict[tuple[str, str], str] = {}

    for cell in source["hex_cells"]:
        cx = float(cell["world_x"])
        cy = float(cell["world_y"])
        corner_vertex_ids: list[str] = []
        for corner_index, (_px, _py) in enumerate(corner_points):
            corner_vertex_ids.append(corner_ref_to_id[(cell["cell_id"], corner_index)])
        corner_heights = [vertex_by_id[vertex_id]["final_height"] for vertex_id in corner_vertex_ids]
        edge_midpoint_pending_ids_by_corner_start: dict[int, str] = {}

        edges: list[dict[str, Any]] = []
        for direction in directions_for_cell(source, cell):
            dq, dr = direction["delta"]
            neighbor = cells_by_coord.get((cell["q"] + dq, cell["r"] + dr))
            corner_a, corner_b = direction["corners"]
            edge_vertices = [corner_vertex_ids[corner_a], corner_vertex_ids[corner_b]]
            classification = classify_edge_transition(cell=cell, neighbor=neighbor, step=step)
            if neighbor is None:
                delta = None
                neighbor_id = None
                point_connection_id = None
                boundary_edge_count += 1
            else:
                delta = round(float(neighbor["final_height"]) - float(cell["final_height"]), 6)
                neighbor_id = neighbor["cell_id"]
                point_connection = make_neighbor_point_connection(
                    connection_index=len(point_connections),
                    cell=cell,
                    neighbor=neighbor,
                    direction=direction,
                    corner_points=corner_points,
                    corner_ref_to_id=corner_ref_to_id,
                )
                point_connection_id = point_connection["connection_id"]
                point_connections.append(point_connection)
                for pair in point_connection["point_pairs"]:
                    point_connection_pair_count += 1
                    if pair["connection_state"] == "same_vertex":
                        same_vertex_pair_count += 1
                    else:
                        split_vertex_pair_count += 1
            profile = classification["edge_profile"]
            connector = classification["connector"]
            policy = edge_fold_policy_for(profile, connector, delta, source, classification)
            midpoint_pending_id = register_edge_midpoint(
                registry=midpoint_registry,
                cell=cell,
                direction=direction,
                corner_points=corner_points,
                neighbor=neighbor,
                policy=policy,
                classification=classification,
                edge_vertices=edge_vertices,
                step=step,
            )
            midpoint_pending_refs[(cell["cell_id"], direction["side"])] = midpoint_pending_id
            radial_index = min(corner_a, corner_b) if abs(corner_a - corner_b) == 1 else 5
            edge_midpoint_pending_ids_by_corner_start[radial_index] = midpoint_pending_id
            edge_counts[profile] = edge_counts.get(profile, 0) + 1
            connector_counts[connector] = connector_counts.get(connector, 0) + 1
            seam_policy_counts[policy["seam_policy"]] = seam_policy_counts.get(policy["seam_policy"], 0) + 1
            delta_key = "boundary" if classification["delta_band"] is None else str(classification["delta_band"])
            delta_band_counts[delta_key] = delta_band_counts.get(delta_key, 0) + 1
            transition_class_counts[classification["transition_class"]] = transition_class_counts.get(classification["transition_class"], 0) + 1
            profile_rule_counts[classification["profile_rule_id"]] = profile_rule_counts.get(classification["profile_rule_id"], 0) + 1

            if policy["seam_policy"] != "shared_surface":
                if neighbor_id is None:
                    seam_key = (cell["cell_id"], direction["side"], policy["seam_policy"])
                    high_cell = cell["cell_id"]
                    low_cell = None
                else:
                    seam_key = (*sorted((cell["cell_id"], neighbor_id)), policy["seam_policy"])
                    if float(cell["final_height"]) >= float(neighbor["final_height"]):
                        high_cell = cell["cell_id"]
                        low_cell = neighbor_id
                    else:
                        high_cell = neighbor_id
                        low_cell = cell["cell_id"]
                if seam_key not in seen_seam_facts:
                    seen_seam_facts.add(seam_key)
                    fold_bias = policy.get("fold_bias")
                    mid_height = None
                    if policy["seam_policy"] == "fold_meet_halfway" and neighbor_id is not None:
                        high_height = float(cells_by_id[high_cell]["final_height"])
                        low_height = float(cells_by_id[low_cell]["final_height"])
                        bias = float(fold_bias if fold_bias is not None else 0.5)
                        mid_height = round(low_height + (high_height - low_height) * bias, 6)
                    seam_facts.append(
                        {
                            "seam_id": f"seam_{len(seam_facts):04d}",
                            "source_cell": cell["cell_id"],
                            "neighbor_cell": neighbor_id,
                            "side": direction["side"],
                            "edge_profile": profile,
                            "profile_rule_id": classification["profile_rule_id"],
                            "terrain_profile": classification["terrain_profile"],
                            "transition_class": classification["transition_class"],
                            "connector": connector,
                            "seam_policy": policy["seam_policy"],
                            "mesh_behavior": policy["mesh_behavior"],
                            "affordance_outputs": policy["affordance_outputs"],
                            "height_delta_to_neighbor": delta,
                            "signed_delta_band": classification["signed_delta_band"],
                            "delta_band": classification["delta_band"],
                            "high_cell": high_cell,
                            "low_cell": low_cell,
                            "fold_bias": fold_bias,
                            "mid_height": mid_height,
                            "corner_vertex_ids": edge_vertices,
                        }
                    )
            edges.append(
                {
                    "side": direction["side"],
                    "neighbor": neighbor_id,
                    "edge_profile": profile,
                    "profile_rule_id": classification["profile_rule_id"],
                    "terrain_profile": classification["terrain_profile"],
                    "transition_class": classification["transition_class"],
                    "connector": connector,
                    "height_delta_to_neighbor": delta,
                    "height_band": classification["height_band"],
                    "neighbor_height_band": classification["neighbor_height_band"],
                    "height_m": classification["height_m"],
                    "neighbor_height_m": classification["neighbor_height_m"],
                    "signed_delta_band": classification["signed_delta_band"],
                    "delta_band": classification["delta_band"],
                    "corner_vertex_ids": edge_vertices,
                    "edge_midpoint_pending_id": midpoint_pending_id,
                    "point_connection_id": point_connection_id,
                    "seam_policy": policy["seam_policy"],
                    "mesh_behavior": policy["mesh_behavior"],
                    "affordance_outputs": policy["affordance_outputs"],
                    "fold_bias": policy.get("fold_bias"),
                }
            )

        socket = make_socket(cell)
        cell_sockets = []
        if socket is not None:
            sockets.append(socket)
            cell_sockets.append(socket)

        center_vertex_id = f"center_{cell['cell_id']}"
        edge_midpoint_pending_ids = [edge_midpoint_pending_ids_by_corner_start[i] for i in range(6)]

        plots.append(
            {
                "cell_id": cell["cell_id"],
                "q": cell["q"],
                "r": cell["r"],
                "s": cell["s"],
                "center": [cell["world_x"], cell["world_y"]],
                "center_height": cell["final_height"],
                "height_m": round(float(cell["final_height"]), 6),
                "height_band": height_band_for_height(float(cell["final_height"]), step),
                "plot_role": cell["topology_role"],
                "buildable": cell["buildable"],
                "corner_vertex_ids": corner_vertex_ids,
                "corner_heights": corner_heights,
                "edge_midpoint_pending_ids": edge_midpoint_pending_ids,
                "edges": edges,
                "sockets": cell_sockets,
                "movement_tags": cell["movement_tags"],
                "structure_socket_tags": cell["structure_socket_tags"],
            }
        )

    edge_midpoints, midpoint_ref_to_id, edge_midpoint_summary = finalize_edge_midpoints(
        midpoint_registry,
        midpoint_pending_refs,
    )
    midpoint_id_by_pending = {
        row["midpoint_id"]: row
        for row in edge_midpoints
    }
    pending_to_midpoint_id = {
        pending: midpoint_ref_to_id[ref]
        for ref, pending in midpoint_pending_refs.items()
    }
    for plot in plots:
        edge_midpoint_ids = [pending_to_midpoint_id[pending_id] for pending_id in plot.pop("edge_midpoint_pending_ids")]
        plot["edge_midpoint_ids"] = edge_midpoint_ids
        plot["edge_midpoint_heights"] = [midpoint_id_by_pending[midpoint_id]["height_m"] for midpoint_id in edge_midpoint_ids]
        plot["edge_midpoint_height_bands"] = [midpoint_id_by_pending[midpoint_id]["height_band"] for midpoint_id in edge_midpoint_ids]
        for edge in plot["edges"]:
            pending_id = edge.pop("edge_midpoint_pending_id")
            edge["edge_midpoint_id"] = pending_to_midpoint_id[pending_id]
        center_vertex_id = f"center_{plot['cell_id']}"
        for i in range(6):
            top_triangles.append(
                {
                    "cell_id": plot["cell_id"],
                    "triangle_index_in_cell": i * 2,
                    "vertex_ids": [center_vertex_id, plot["corner_vertex_ids"][i], edge_midpoint_ids[i]],
                    "plot_role": plot["plot_role"],
                }
            )
            top_triangles.append(
                {
                    "cell_id": plot["cell_id"],
                    "triangle_index_in_cell": i * 2 + 1,
                    "vertex_ids": [center_vertex_id, edge_midpoint_ids[i], plot["corner_vertex_ids"][(i + 1) % 6]],
                    "plot_role": plot["plot_role"],
                }
            )

    bad_s = [plot["cell_id"] for plot in plots if plot["q"] + plot["r"] + plot["s"] != 0]
    if bad_s:
        fail(f"q+r+s mismatch in {bad_s[:5]}")
    bad_corners = [
        plot["cell_id"]
        for plot in plots
        if len(plot["corner_vertex_ids"]) != 6 or len(plot["edge_midpoint_ids"]) != 6 or len(plot["edges"]) != 6
    ]
    if bad_corners:
        fail(f"bad plot corner/midpoint/edge count in {bad_corners[:5]}")

    graph = {
        "schema": "hex_plot_vertex_graph_v0",
        "graph_id": f"{source['site_id']}_plot_vertex_graph",
        "source_terrain_assembly": str(path.relative_to(ROOT)),
        "map_cube": source["map_cube"],
        "hex_grid": source["hex_grid"],
        "height_band_rules": {
            "height_band_step_m": step,
            "height_band_method": "round_half_up_from_height_m_divided_by_configured_vertical_step",
            "delta_0": "shared_flat",
            "delta_1": "soft_fold_or_step",
            "delta_2_plus": "cliff_fault",
        },
        "edge_profile_rule_table": EDGE_PROFILE_RULE_TABLE,
        "edge_fold_policy": source.get("edge_fold_policy", {}),
        "source_cell_summary": source["cell_summary"],
        "point_connection_rules": {
            "corner_index_order": "pointy_top_hex_corners_at_degrees_30_90_150_210_270_330",
            "neighbor_edge_rule": "each_neighbor_edge_connects_two_source_corner_points_to_two_matching_neighbor_corner_points_by_raw_xy",
            "connection_first": True,
            "mesh_policy_uses_connection_after_point_pairs_are_declared": True,
        },
        "neighbor_point_connections": point_connections,
        "point_connection_summary": {
            "directed_neighbor_edge_connections": len(point_connections),
            "boundary_edges_without_neighbor": boundary_edge_count,
            "point_pair_count": point_connection_pair_count,
            "same_vertex_pair_count": same_vertex_pair_count,
            "split_vertex_same_xy_pair_count": split_vertex_pair_count,
            "all_neighbor_edges_have_two_point_pairs": all(len(connection["point_pairs"]) == 2 for connection in point_connections),
        },
        "corner_vertices": corner_vertices,
        "vertex_split_summary": vertex_split_summary,
        "corner_seam_caps": corner_seam_caps,
        "edge_midpoints": edge_midpoints,
        "edge_midpoint_summary": edge_midpoint_summary,
        "hex_plots": plots,
        "edge_summary": dict(sorted(edge_counts.items())),
        "connector_summary": dict(sorted(connector_counts.items())),
        "seam_policy_summary": dict(sorted(seam_policy_counts.items())),
        "delta_band_summary": dict(sorted(delta_band_counts.items())),
        "transition_class_summary": dict(sorted(transition_class_counts.items())),
        "profile_rule_summary": dict(sorted(profile_rule_counts.items())),
        "seam_facts": seam_facts,
        "socket_summary": {
            "socket_count": len(sockets),
            "sockets": sockets,
        },
        "mesh_plan": {
            "surface_join_model": "seam_aware_shared_corner_vertices_and_edge_midpoints_v0",
            "topology": "radial_12_triangle_fan_per_hex_using_shared_corners_and_shared_edge_midpoints",
            "center_vertices": len(plots),
            "corner_vertices": len(corner_vertices),
            "edge_midpoints": len(edge_midpoints),
            "raw_corner_keys": vertex_split_summary["raw_corner_key_count"],
            "split_raw_corners": vertex_split_summary["split_raw_corner_count"],
            "split_extra_vertices": vertex_split_summary["split_extra_vertex_count"],
            "corner_seam_caps": vertex_split_summary["corner_seam_cap_count"],
            "top_triangle_count": len(top_triangles),
            "top_triangles": top_triangles,
            "seam_policy_model": "explicit_edge_policy_and_deduped_seam_facts_v0",
            "hard_seam_splitting": "seam_facts_emitted_for_split_riser_split_cliff_and_fold_meet_halfway",
            "bottom_faces": 0,
        },
        "no_claims": NO_CLAIMS,
    }
    graph["validation"] = validate_compiled_graph(graph)
    return graph


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Hex Plot Vertex Graph v0",
        "",
        "Connected plot graph layer that turns hex cells into shared corner vertices, shared edge midpoints, edge profiles, connectors, sockets, and a seamless 12-triangle radial top mesh plan.",
        "",
        "```text",
        "hex cells -> plots -> shared corner vertices + edge midpoints -> edge connectors -> sockets -> 12-triangle terrain surface",
        "```",
        "",
        "| Graph | Cells | Corners | Midpoints | Shared Midpoints | Split Midpoints | Cracks | Top Triangles | Delta Bands | Profiles | Seam Policy Summary | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['graph_id']}` | {row['cell_count']} | {row['corner_vertex_count']} | {row['edge_midpoint_count']} | {row['shared_midpoint_count']} | {row['split_midpoint_count']} | {row['cracked_seam_count']} | {row['top_triangle_count']} | `{row['delta_band_summary']}` | `{row['profile_rule_summary']}` | `{row['seam_policy_summary']}` | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "Cells are no longer isolated tiles. A hex plot owns six edge contracts, six corner references, six edge midpoint references, optional sockets, and shares midpoint ids on shared-surface seams.",
            "",
            "Every edge now carries integer height-band delta, transition class, v0 profile-rule id, and concrete seam policy. Shared-surface edges remain continuous; risers, cliffs, and chunk boundaries emit deduped seam facts for mesh compilers.",
            "",
            "Corner vertices are seam-aware: flat and smooth edges may share averaged corner vertices, while riser/cliff boundaries split duplicate vertices at the same XY so hard terrain does not sag through averaging.",
            "",
            "Split raw corners emit `corner_seam_cap` facts so mesh compilers can close seam junction holes where multiple height groups meet.",
            "",
            "The top mesh plan is now a radial 12-triangle fan per hex: center to each corner/midpoint wedge pair.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_point_connection_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Hex Point Connection Graph v0",
        "",
        "Defines how each hex edge endpoint connects to the matching endpoint on its neighbor before seam policy or mesh generation.",
        "",
        "```text",
        "hex corner points -> neighbor point pairs -> shared/split vertex decision -> seam policy -> mesh",
        "```",
        "",
        "| Graph | Directed Neighbor Edges | Boundary Edges | Point Pairs | Same Vertex Pairs | Split Vertex Pairs | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = row["point_connection_summary"]
        lines.append(
            f"| `{row['graph_id']}` | {summary['directed_neighbor_edge_connections']} | {summary['boundary_edges_without_neighbor']} | {summary['point_pair_count']} | {summary['same_vertex_pair_count']} | {summary['split_vertex_same_xy_pair_count']} | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "Each neighbor edge has exactly two endpoint connections. The compiler matches endpoint pairs by raw world XY first, then assigns either `same_vertex` or `split_vertex_same_xy` after seam-aware vertex splitting.",
            "",
            "`same_vertex` means continuous surface geometry may share one vertex. `split_vertex_same_xy` means the point occupies the same XY position but has separate height groups for risers, cliffs, or corner caps.",
            "",
        ]
    )
    POINT_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "hex_plot_vertex_graph_v0",
        "created_at_utc": now_iso(),
        "graph_count": len(rows),
        "graphs": rows,
        "rules": {
            "hex_cells_become_plots": True,
            "corner_vertices_are_shared": True,
            "edge_midpoints_are_registered": True,
            "shared_surface_edges_use_shared_midpoint_ids": True,
            "split_seams_use_explicit_cell_owned_midpoints": True,
            "integer_height_bands_are_emitted": True,
            "edge_delta_bands_are_emitted": True,
            "edge_profile_rule_table_v0_is_emitted": True,
            "top_mesh_is_12_triangle_radial_fan_per_hex": True,
            "cracked_seam_count_is_zero": all(row["cracked_seam_count"] == 0 for row in rows),
            "top_triangle_count_is_cell_count_times_12": all(row["top_triangle_count"] == row["cell_count"] * 12 for row in rows),
            "corner_vertices_split_at_hard_seams": True,
            "corner_seam_caps_are_emitted": True,
            "neighbor_point_connections_declared_first": True,
            "each_neighbor_edge_has_two_point_pairs": True,
            "each_plot_has_six_edges": True,
            "edge_profiles_are_explicit": True,
            "seam_policies_are_explicit": True,
            "split_edges_emit_seam_facts": True,
            "sockets_are_explicit": True,
            "hard_seam_splitting_deferred": False,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True
        },
        "recommended_next_goal": "Render hex_plot_vertex_graph_v0 as a shared-vertex connected terrain surface.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    midpoint_receipt = {
        **receipt,
        "receipt_type": "shared_midpoint_radial_hex_terrain_v0",
        "source_receipt_type": "hex_plot_vertex_graph_v0",
        "acceptance": {
            "cracked_seam_count_must_be_zero": all(row["cracked_seam_count"] == 0 for row in rows),
            "top_triangle_count_equals_cell_count_times_12": all(row["top_triangle_count"] == row["cell_count"] * 12 for row in rows),
            "shared_edge_midpoint_ids_match_across_shared_seams": all(row["cracked_seam_count"] == 0 for row in rows),
            "delta_two_plus_edges_classify_as_cliff_fault": all(row["delta_two_plus_all_cliff_fault"] for row in rows),
        },
    }
    SHARED_MIDPOINT_RECEIPT_PATH.write_text(json.dumps(midpoint_receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for path in sorted(SOURCE_DIR.glob("*_assembly.json")):
        graph = compile_graph(path)
        out = GRAPH_DIR / f"{graph['graph_id']}.json"
        out.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "graph_id": graph["graph_id"],
                "cell_count": len(graph["hex_plots"]),
                "corner_vertex_count": len(graph["corner_vertices"]),
                "edge_midpoint_count": len(graph["edge_midpoints"]),
                "shared_midpoint_count": graph["edge_midpoint_summary"]["shared_midpoint_count"],
                "split_midpoint_count": graph["edge_midpoint_summary"]["split_midpoint_count"],
                "cracked_seam_count": graph["validation"]["cracked_seam_count"],
                "delta_two_plus_all_cliff_fault": graph["validation"]["delta_two_plus_all_cliff_fault"],
                "raw_corner_key_count": graph["vertex_split_summary"]["raw_corner_key_count"],
                "split_raw_corner_count": graph["vertex_split_summary"]["split_raw_corner_count"],
                "split_extra_vertex_count": graph["vertex_split_summary"]["split_extra_vertex_count"],
                "corner_seam_cap_count": graph["vertex_split_summary"]["corner_seam_cap_count"],
                "top_triangle_count": graph["mesh_plan"]["top_triangle_count"],
                "socket_count": graph["socket_summary"]["socket_count"],
                "edge_summary": graph["edge_summary"],
                "delta_band_summary": graph["delta_band_summary"],
                "profile_rule_summary": graph["profile_rule_summary"],
                "seam_policy_summary": graph["seam_policy_summary"],
                "seam_fact_count": len(graph["seam_facts"]),
                "point_connection_summary": graph["point_connection_summary"],
                "output_path": str(out.relative_to(ROOT)),
            }
        )
    if not rows:
        fail(f"no folded hex terrain assemblies found in {SOURCE_DIR.relative_to(ROOT)}")
    write_report(rows)
    write_point_connection_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} hex plot vertex graphs")
    for row in rows:
        print(
            f"{row['graph_id']}: {row['cell_count']} cells, "
            f"{row['corner_vertex_count']} corner vertices, "
            f"{row['edge_midpoint_count']} edge midpoints, "
            f"{row['top_triangle_count']} top triangles, "
            f"cracks={row['cracked_seam_count']}"
        )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"point connection report: {POINT_REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")
    print(f"shared midpoint receipt: {SHARED_MIDPOINT_RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
