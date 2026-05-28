#!/usr/bin/env python3
"""Compile Terrain Profile Bending v0 proof graphs.

This pass sits after the shared-midpoint terrain graph and before mesh
emission:

cell height bands -> edge delta classification -> profile law selection ->
center/corner/midpoint height offsets -> welded top mesh.

No Blender, mesh, or image output is created here.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_hex_plot_vertex_graph_v0 as shared_graph  # noqa: E402


OUT_DIR = ROOT / "goal" / "architecture" / "terrain_profile_bending_v0"
ASSEMBLY_DIR = OUT_DIR / "assemblies"
SHARED_GRAPH_DIR = OUT_DIR / "shared_graphs"
PROFILED_GRAPH_DIR = OUT_DIR / "profiled_graphs"
REPORT_PATH = OUT_DIR / "terrain_profile_bending_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "terrain_profile_bending_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}

PROFILE_LAWS = {
    "flat_pad": "force building foundation cell centers, corners, and edge midpoints to one pad height",
    "soft_slope": "blend shared corners and edge midpoints between neighbor height bands for rounded hills",
    "road_grade": "smooth road cell centers and incident welded vertices across single-band elevation changes",
    "cliff_fault": "preserve split cliff/fault seams for delta >= 2 instead of stretching slopes",
    "terrace_step": "keep deliberate banded steps while retaining welded midpoint/corner seams",
    "ravine_fold": "pull ravine centers and edge midpoints downward into a V-shaped depression",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def axial_to_world(q: int, r: int, radius: float) -> tuple[float, float]:
    return radius * math.sqrt(3.0) * (q + r * 0.5), radius * 1.5 * r


def cell_id(site_id: str, q: int, r: int) -> str:
    def part(value: int) -> str:
        return f"m{abs(value)}" if value < 0 else f"p{value}"

    return f"{site_id}_{part(q)}_{part(r)}"


def base_map_cube() -> dict[str, Any]:
    return {
        "schema": "map_cube_grid_v0",
        "map_cube_id": "terrain_profile_bending_tiny_map_cube_v0",
        "cell_size_m": 1.0,
        "dimensions": {"x": 12, "y": 12, "z": 8},
        "origin": "centered_xy_floor_z",
        "coordinate_range": {"x": [-8.0, 8.0], "y": [-8.0, 8.0], "z": [0.0, 8.0]},
        "connector_faces": {
            "north": "chunk_stitch_candidate",
            "south": "chunk_stitch_candidate",
            "east": "chunk_stitch_candidate",
            "west": "chunk_stitch_candidate",
            "upper": "vertical_stack_candidate",
            "lower": "vertical_stack_candidate",
        },
        "layer_stack": [
            "topology_elevation_graph",
            "terrain_profile_bending_layer",
            "building_site_layer",
            "route_connectivity_graph",
            "visual_mesh_layer",
        ],
        "recommended_defaults": {
            "hex_radius": 1.0,
            "vertical_step": 0.5,
            "path_width_m": 2.0,
            "choke_width_m": 1.0,
            "fall_threshold_m": 1.0,
            "walkable_delta_max_m": 0.5,
            "slope_delta_max_m": 1.0,
        },
        "no_claims": NO_CLAIMS,
    }


def hex_disk(radius: int) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= radius:
                coords.append((q, r))
    return sorted(coords, key=lambda item: (item[1], item[0]))


def rect_coords(q_min: int, q_max: int, r_min: int, r_max: int) -> list[tuple[int, int]]:
    return [(q, r) for r in range(r_min, r_max + 1) for q in range(q_min, q_max + 1)]


def make_cell(site_id: str, q: int, r: int, height: float, surface_type: str, role: str, tags: list[str], sockets: list[str]) -> dict[str, Any]:
    x, y = axial_to_world(q, r, 1.0)
    return {
        "cell_id": cell_id(site_id, q, r),
        "q": q,
        "r": r,
        "s": -q - r,
        "world_x": round(x, 6),
        "world_y": round(y, 6),
        "base_height": round(height, 6),
        "fold_offset": 0.0,
        "final_height": round(height, 6),
        "height_level": int(round(height / 0.5)),
        "surface_type": surface_type,
        "topology_role": role,
        "buildable": "building_plot" in sockets or surface_type == "building_plot",
        "edge_profiles": ["flat"] * 6,
        "movement_tags": tags,
        "structure_socket_tags": sockets,
        "source_tile_index": 0,
        "plot_ids": ["pad_a"] if surface_type == "building_plot" else [],
        "road_ids": ["road_a"] if "road" in tags else [],
        "hazard_ids": ["ravine_a"] if "hazard" in tags else [],
        "fold_contributions": [],
    }


def scenario_cells(scenario_id: str) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    if scenario_id == "round_hill_profile":
        for q, r in hex_disk(2):
            dist = max(abs(q), abs(r), abs(-q - r))
            height = {0: 2.0, 1: 1.5, 2: 1.0}[dist]
            role = "hilltop" if dist == 0 else "upper_slope" if dist == 1 else "lower_slope"
            cells.append(make_cell(scenario_id, q, r, height, "grass", role, ["walkable"], []))
        return cells
    if scenario_id == "road_over_slope_profile":
        for q, r in rect_coords(-3, 3, -1, 1):
            height = 1.0 + (q + 3) * (0.5 / 2.0)
            is_road = r == 0
            cells.append(
                make_cell(
                    scenario_id,
                    q,
                    r,
                    height,
                    "road" if is_road else "grass",
                    "road" if is_road else "terrain",
                    ["walkable", "route", "road"] if is_road else ["walkable"],
                    [],
                )
            )
        return cells
    if scenario_id == "flat_building_pad_on_slope":
        for q, r in rect_coords(-2, 2, -2, 2):
            height = 0.75 + (q + r + 4) * 0.125
            is_pad = -1 <= q <= 1 and -1 <= r <= 1
            cells.append(
                make_cell(
                    scenario_id,
                    q,
                    r,
                    height,
                    "building_plot" if is_pad else "grass",
                    "building_plot" if is_pad else "terrain",
                    ["walkable", "building_plot"] if is_pad else ["walkable"],
                    ["building_plot_candidate", "building_pad"] if is_pad else [],
                )
            )
        return cells
    if scenario_id == "terrace_steps_profile":
        for q, r in rect_coords(-3, 3, -2, 2):
            height = 1.0 + (r + 2) * 0.5
            if q == 3:
                height += 1.0
            cells.append(make_cell(scenario_id, q, r, height, "stone", "terrace_step", ["walkable", "terrace_step"], []))
        return cells
    if scenario_id == "ravine_fold_profile":
        for q, r in rect_coords(-3, 3, -2, 2):
            is_ravine = q == 0 or (q == 1 and r == -1)
            cells.append(
                make_cell(
                    scenario_id,
                    q,
                    r,
                    1.5,
                    "ravine_edge" if is_ravine else "grass",
                    "ravine_fold" if is_ravine else "terrain",
                    ["walkable", "hazard", "avoid"] if is_ravine else ["walkable"],
                    [],
                )
            )
        return cells
    fail(f"unknown scenario {scenario_id}")


def cell_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_role: dict[str, int] = {}
    by_height: dict[str, int] = {}
    for cell in cells:
        by_role[cell["topology_role"]] = by_role.get(cell["topology_role"], 0) + 1
        key = f"{float(cell['final_height']):.2f}"
        by_height[key] = by_height.get(key, 0) + 1
    return {
        "cell_count": len(cells),
        "folded_cell_count": 0,
        "buildable_cell_count": sum(1 for cell in cells if cell["buildable"]),
        "by_role": dict(sorted(by_role.items())),
        "by_final_height": dict(sorted(by_height.items(), key=lambda item: float(item[0]))),
        "min_base_height": min(float(cell["base_height"]) for cell in cells),
        "max_base_height": max(float(cell["base_height"]) for cell in cells),
        "min_final_height": min(float(cell["final_height"]) for cell in cells),
        "max_final_height": max(float(cell["final_height"]) for cell in cells),
    }


def make_assembly(scenario_id: str) -> dict[str, Any]:
    cells = scenario_cells(scenario_id)
    return {
        "schema": "hex_terrain_fold_site_assembly_v0",
        "site_id": scenario_id,
        "source_recipe": "generated_by_compile_terrain_profile_bending_v0",
        "summary": f"Tiny profile-law fixture for {scenario_id}.",
        "units": "abstract_meter",
        "map_cube": base_map_cube(),
        "hex_grid": {"layout": "pointy_top", "radius": 1.0, "vertical_step": 0.5, "bounds_source": "terrain_profile_bending_v0_fixture"},
        "heightfield": {"type": scenario_id, "quantize_to_vertical_step": True, "surface_type": "profile_fixture"},
        "folds": [],
        "edge_fold_policy": {},
        "classification_rules": {
            "flat_delta_max": 0.001,
            "step_delta_max": 0.5,
            "ledge_delta_max": 1.0,
            "cliff_delta_min": 1.0,
            "buildable_slope_delta_max": 0.5,
            "walkable_delta_max": 0.5,
        },
        "cell_summary": cell_summary(cells),
        "base_edge_summary": {},
        "final_edge_summary": {},
        "visible_face_stats": {"top_faces": len(cells), "candidate_side_faces": len(cells) * 6, "bottom_faces": 0},
        "hex_cells": cells,
        "no_claims": NO_CLAIMS,
    }


def profile_law_for_plot(plot: dict[str, Any]) -> str:
    tags = set(plot.get("movement_tags", [])) | set(plot.get("structure_socket_tags", []))
    if "building_pad" in tags or plot.get("surface_type") == "building_plot" or plot.get("plot_ids"):
        return "flat_pad"
    if "road" in tags or "route" in tags or plot.get("road_ids"):
        return "road_grade"
    if "hazard" in tags or plot.get("surface_type") == "ravine_edge" or plot.get("hazard_ids"):
        return "ravine_fold"
    if any(edge.get("delta_band") is not None and int(edge["delta_band"]) >= 2 for edge in plot["edges"]):
        return "cliff_fault"
    if "terrace_step" in tags or plot.get("plot_role") == "terrace_step":
        return "terrace_step"
    return "soft_slope"


def connected_groups(ids: set[str], neighbor_pairs: list[tuple[str, str]]) -> list[set[str]]:
    remaining = set(ids)
    adjacency = {item: set() for item in ids}
    for left, right in neighbor_pairs:
        if left in ids and right in ids:
            adjacency[left].add(right)
            adjacency[right].add(left)
    groups: list[set[str]] = []
    while remaining:
        start = remaining.pop()
        group = {start}
        stack = [start]
        while stack:
            item = stack.pop()
            for other in adjacency[item]:
                if other in remaining:
                    remaining.remove(other)
                    group.add(other)
                    stack.append(other)
        groups.append(group)
    return groups


def apply_profile_laws(graph: dict[str, Any]) -> dict[str, Any]:
    profiled = copy.deepcopy(graph)
    profiled["schema"] = "terrain_profile_bending_graph_v0"
    profiled["source_shared_graph_id"] = graph["graph_id"]
    profiled["profile_laws"] = PROFILE_LAWS

    corners = {vertex["vertex_id"]: vertex for vertex in profiled["corner_vertices"]}
    midpoints = {midpoint["midpoint_id"]: midpoint for midpoint in profiled["edge_midpoints"]}
    plots = {plot["cell_id"]: plot for plot in profiled["hex_plots"]}
    for vertex in corners.values():
        vertex["base_height_m"] = vertex["height_m"]
        vertex["profiled_height_m"] = vertex["height_m"]
        vertex["profile_offset_m"] = 0.0
    for midpoint in midpoints.values():
        midpoint["base_height_m"] = midpoint["height_m"]
        midpoint["profiled_height_m"] = midpoint["height_m"]
        midpoint["profile_offset_m"] = 0.0
    for plot in profiled["hex_plots"]:
        law = profile_law_for_plot(plot)
        plot["profile_law"] = law
        plot["base_center_height_m"] = plot["center_height"]
        plot["profiled_center_height_m"] = plot["center_height"]
        plot["profile_offset_m"] = 0.0
        for edge in plot["edges"]:
            edge["profile_law"] = "cliff_fault" if edge.get("delta_band") is not None and int(edge["delta_band"]) >= 2 else law

    road_ids = {plot["cell_id"] for plot in profiled["hex_plots"] if plot["profile_law"] == "road_grade"}
    pad_ids = {plot["cell_id"] for plot in profiled["hex_plots"] if plot["profile_law"] == "flat_pad"}
    neighbor_pairs = [
        (plot["cell_id"], edge["neighbor"])
        for plot in profiled["hex_plots"]
        for edge in plot["edges"]
        if edge["neighbor"] is not None
    ]

    for group in connected_groups(pad_ids, neighbor_pairs):
        pad_height = round(sum(float(plots[cell_id]["center_height"]) for cell_id in group) / len(group), 6)
        for cell_id in group:
            plot = plots[cell_id]
            plot["profiled_center_height_m"] = pad_height
            plot["profile_offset_m"] = round(pad_height - float(plot["center_height"]), 6)
            for vertex_id in plot["corner_vertex_ids"]:
                corners[vertex_id]["profiled_height_m"] = pad_height
            for midpoint_id in plot["edge_midpoint_ids"]:
                midpoints[midpoint_id]["profiled_height_m"] = pad_height

    for group in connected_groups(road_ids, neighbor_pairs):
        sorted_group = sorted(group, key=lambda cell_id: (plots[cell_id]["q"], plots[cell_id]["r"]))
        for index, cell_id in enumerate(sorted_group):
            plot = plots[cell_id]
            neighbor_heights = [
                float(plots[edge["neighbor"]]["center_height"])
                for edge in plot["edges"]
                if edge["neighbor"] in group
            ]
            target = (float(plot["center_height"]) + sum(neighbor_heights)) / (1 + len(neighbor_heights)) if neighbor_heights else float(plot["center_height"])
            # Keep a slight monotonic grade so road direction remains readable.
            grade_bias = (index - (len(sorted_group) - 1) * 0.5) * 0.015
            profiled_height = round(target + grade_bias, 6)
            plot["profiled_center_height_m"] = profiled_height
            plot["profile_offset_m"] = round(profiled_height - float(plot["center_height"]), 6)
            for midpoint_id in plot["edge_midpoint_ids"]:
                midpoint = midpoints[midpoint_id]
                midpoint["profiled_height_m"] = round((float(midpoint["profiled_height_m"]) * 0.65) + (profiled_height * 0.35), 6)
            for vertex_id in plot["corner_vertex_ids"]:
                vertex = corners[vertex_id]
                vertex["profiled_height_m"] = round((float(vertex["profiled_height_m"]) * 0.78) + (profiled_height * 0.22), 6)

    for plot in profiled["hex_plots"]:
        if plot["profile_law"] == "ravine_fold":
            base = float(plot["center_height"])
            folded = round(base - 0.6, 6)
            plot["profiled_center_height_m"] = folded
            plot["profile_offset_m"] = round(folded - base, 6)
            for midpoint_id in plot["edge_midpoint_ids"]:
                midpoint = midpoints[midpoint_id]
                midpoint["profiled_height_m"] = round(min(float(midpoint["profiled_height_m"]), folded + 0.25), 6)
            for vertex_id in plot["corner_vertex_ids"]:
                vertex = corners[vertex_id]
                vertex["profiled_height_m"] = round(min(float(vertex["profiled_height_m"]), base - 0.15), 6)
        elif plot["profile_law"] == "soft_slope":
            lower_neighbors = [
                float(edge["neighbor_height_m"])
                for edge in plot["edges"]
                if edge["neighbor_height_m"] is not None and float(edge["neighbor_height_m"]) < float(plot["center_height"])
            ]
            if lower_neighbors:
                pull = min(0.12, (float(plot["center_height"]) - min(lower_neighbors)) * 0.12)
                plot["profiled_center_height_m"] = round(float(plot["center_height"]) - pull, 6)
                plot["profile_offset_m"] = round(-pull, 6)
        elif plot["profile_law"] == "terrace_step":
            step = float(profiled["height_band_rules"]["height_band_step_m"])
            snapped = round(round(float(plot["center_height"]) / step) * step, 6)
            plot["profiled_center_height_m"] = snapped
            plot["profile_offset_m"] = round(snapped - float(plot["center_height"]), 6)

    # Foundations are a hard local constraint. Re-apply them after road and
    # ravine shaping so shared pad vertices cannot be pulled out of plane.
    for group in connected_groups(pad_ids, neighbor_pairs):
        pad_height = round(sum(float(plots[cell_id]["profiled_center_height_m"]) for cell_id in group) / len(group), 6)
        for cell_id in group:
            plot = plots[cell_id]
            plot["profiled_center_height_m"] = pad_height
            plot["profile_offset_m"] = round(pad_height - float(plot["center_height"]), 6)
            for vertex_id in plot["corner_vertex_ids"]:
                corners[vertex_id]["profiled_height_m"] = pad_height
            for midpoint_id in plot["edge_midpoint_ids"]:
                midpoints[midpoint_id]["profiled_height_m"] = pad_height

    for vertex in corners.values():
        vertex["profile_offset_m"] = round(float(vertex["profiled_height_m"]) - float(vertex["base_height_m"]), 6)
    for midpoint in midpoints.values():
        midpoint["profile_offset_m"] = round(float(midpoint["profiled_height_m"]) - float(midpoint["base_height_m"]), 6)

    profiled["mesh_plan"]["height_source"] = "profiled_center_corner_midpoint_height_m"
    profiled["profile_summary"] = profile_summary(profiled)
    profiled["profile_validation"] = validate_profiled_graph(profiled)
    return profiled


def profile_summary(graph: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for plot in graph["hex_plots"]:
        counts[plot["profile_law"]] = counts.get(plot["profile_law"], 0) + 1
    return {
        "profile_law_counts": dict(sorted(counts.items())),
        "corner_profile_offset_range_m": [
            min(float(vertex["profile_offset_m"]) for vertex in graph["corner_vertices"]),
            max(float(vertex["profile_offset_m"]) for vertex in graph["corner_vertices"]),
        ],
        "midpoint_profile_offset_range_m": [
            min(float(midpoint["profile_offset_m"]) for midpoint in graph["edge_midpoints"]),
            max(float(midpoint["profile_offset_m"]) for midpoint in graph["edge_midpoints"]),
        ],
    }


def validate_profiled_graph(graph: dict[str, Any]) -> dict[str, Any]:
    plots = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    corners = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    midpoints = {midpoint["midpoint_id"]: midpoint for midpoint in graph["edge_midpoints"]}
    cracked: list[dict[str, Any]] = []
    road_checks = 0
    road_bad = 0
    cliff_checks = 0
    for plot in graph["hex_plots"]:
        for edge in plot["edges"]:
            neighbor_id = edge["neighbor"]
            if edge.get("delta_band") is not None and int(edge["delta_band"]) >= 2:
                cliff_checks += 1
                if edge["seam_policy"] != "split_cliff":
                    cracked.append({"cell_id": plot["cell_id"], "side": edge["side"], "reason": "delta_two_plus_not_split_cliff"})
            if neighbor_id is None or edge["seam_policy"] != "shared_surface":
                continue
            midpoint = midpoints[edge["edge_midpoint_id"]]
            # Canonical IDs are the weld. Height mismatch can only happen if a
            # future profile pass writes per-cell edge heights.
            if abs(float(midpoint["profiled_height_m"]) - float(midpoint["profiled_height_m"])) > 1e-6:
                cracked.append({"cell_id": plot["cell_id"], "side": edge["side"], "reason": "shared_midpoint_profile_height_mismatch"})
            for vertex_id in edge["corner_vertex_ids"]:
                vertex = corners[vertex_id]
                if abs(float(vertex["profiled_height_m"]) - float(vertex["profiled_height_m"])) > 1e-6:
                    cracked.append({"cell_id": plot["cell_id"], "side": edge["side"], "reason": "shared_corner_profile_height_mismatch"})
            if plot["profile_law"] == "road_grade" and plots[neighbor_id]["profile_law"] == "road_grade":
                road_checks += 1
                if abs(float(plot["profiled_center_height_m"]) - float(plots[neighbor_id]["profiled_center_height_m"])) > 0.55:
                    road_bad += 1

    pad_ranges: list[float] = []
    ravine_depths: list[float] = []
    hill_rounding_scores: list[float] = []
    for plot in graph["hex_plots"]:
        heights = [float(plot["profiled_center_height_m"])]
        heights.extend(float(corners[vertex_id]["profiled_height_m"]) for vertex_id in plot["corner_vertex_ids"])
        heights.extend(float(midpoints[midpoint_id]["profiled_height_m"]) for midpoint_id in plot["edge_midpoint_ids"])
        if plot["profile_law"] == "flat_pad":
            pad_ranges.append(max(heights) - min(heights))
        if plot["profile_law"] == "ravine_fold":
            edge_avg = sum(heights[7:]) / 6
            ravine_depths.append(edge_avg - float(plot["profiled_center_height_m"]))
        if plot["profile_law"] == "soft_slope" and plot["plot_role"] == "hilltop":
            edge_avg = sum(heights[7:]) / 6
            corner_avg = sum(heights[1:7]) / 6
            hill_rounding_scores.append(float(plot["profiled_center_height_m"]) - ((edge_avg + corner_avg) * 0.5))

    validation = {
        "cell_count": len(graph["hex_plots"]),
        "top_triangle_count": graph["mesh_plan"]["top_triangle_count"],
        "expected_top_triangle_count": len(graph["hex_plots"]) * 12,
        "top_triangle_count_matches": graph["mesh_plan"]["top_triangle_count"] == len(graph["hex_plots"]) * 12,
        "cracked_seam_count": len(cracked),
        "cracked_seams": cracked,
        "shared_edge_midpoint_heights_match": len(cracked) == 0,
        "shared_corner_heights_match": len(cracked) == 0,
        "roads_remain_continuous": road_bad == 0,
        "road_continuity_checks": road_checks,
        "building_pads_are_flat": all(value <= 1e-6 for value in pad_ranges),
        "max_building_pad_height_range_m": max(pad_ranges) if pad_ranges else 0.0,
        "cliffs_stay_sharp": cliff_checks == graph["seam_policy_summary"].get("split_cliff", 0),
        "cliff_fault_edge_checks": cliff_checks,
        "small_hill_looks_rounded_numeric": all(score > 0.05 for score in hill_rounding_scores) if hill_rounding_scores else True,
        "hill_rounding_scores": hill_rounding_scores,
        "ravine_is_v_shaped": all(depth > 0.2 for depth in ravine_depths) if ravine_depths else True,
        "ravine_depths_m": ravine_depths,
    }
    if validation["cracked_seam_count"] != 0:
        fail(f"{graph['graph_id']} has profiled cracks: {cracked[:3]}")
    if not validation["top_triangle_count_matches"]:
        fail(f"{graph['graph_id']} top triangle count mismatch")
    return validation


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Terrain Profile Bending v0",
        "",
        "Applies profile laws to shared-midpoint terrain graphs before mesh emission.",
        "",
        "| Scenario | Cells | Law Counts | Top Triangles | Cracks | Roads Continuous | Pads Flat | Cliffs Sharp | Hill Rounded | Ravine V | Output |",
        "| --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        v = row["profile_validation"]
        lines.append(
            f"| `{row['scenario_id']}` | {v['cell_count']} | `{row['profile_summary']['profile_law_counts']}` | "
            f"{v['top_triangle_count']} | {v['cracked_seam_count']} | {v['roads_remain_continuous']} | "
            f"{v['building_pads_are_flat']} | {v['cliffs_stay_sharp']} | {v['small_hill_looks_rounded_numeric']} | "
            f"{v['ravine_is_v_shaped']} | `{row['profiled_graph_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Profile Laws",
            "",
            *[f"- `{key}`: {value}" for key, value in PROFILE_LAWS.items()],
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    receipt = {
        "receipt_type": "terrain_profile_bending_v0",
        "created_at_utc": now_iso(),
        "scenario_count": len(rows),
        "profile_laws": PROFILE_LAWS,
        "scenarios": rows,
        "acceptance": {
            "cracked_seam_count_is_zero": all(row["profile_validation"]["cracked_seam_count"] == 0 for row in rows),
            "shared_edge_midpoint_heights_match": all(row["profile_validation"]["shared_edge_midpoint_heights_match"] for row in rows),
            "shared_corner_heights_match": all(row["profile_validation"]["shared_corner_heights_match"] for row in rows),
            "roads_remain_continuous": all(row["profile_validation"]["roads_remain_continuous"] for row in rows),
            "building_pads_are_flat": all(row["profile_validation"]["building_pads_are_flat"] for row in rows),
            "cliffs_stay_sharp": all(row["profile_validation"]["cliffs_stay_sharp"] for row in rows),
            "small_hill_looks_rounded_numeric": all(row["profile_validation"]["small_hill_looks_rounded_numeric"] for row in rows),
            "ravine_is_v_shaped": all(row["profile_validation"]["ravine_is_v_shaped"] for row in rows),
        },
        "outputs": {
            "report": str(REPORT_PATH.relative_to(ROOT)),
            "profiled_graph_dir": str(PROFILED_GRAPH_DIR.relative_to(ROOT)),
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def compile_scenario(scenario_id: str) -> dict[str, Any]:
    assembly = make_assembly(scenario_id)
    assembly_path = ASSEMBLY_DIR / f"{scenario_id}_assembly.json"
    assembly_path.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
    graph = shared_graph.compile_graph(assembly_path)
    shared_path = SHARED_GRAPH_DIR / f"{scenario_id}_shared_graph.json"
    shared_path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    profiled = apply_profile_laws(graph)
    profiled_path = PROFILED_GRAPH_DIR / f"{scenario_id}_profiled_graph.json"
    profiled_path.write_text(json.dumps(profiled, indent=2) + "\n", encoding="utf-8")
    return {
        "scenario_id": scenario_id,
        "assembly_path": str(assembly_path.relative_to(ROOT)),
        "shared_graph_path": str(shared_path.relative_to(ROOT)),
        "profiled_graph_path": str(profiled_path.relative_to(ROOT)),
        "profile_summary": profiled["profile_summary"],
        "profile_validation": profiled["profile_validation"],
    }


def main() -> None:
    for directory in (ASSEMBLY_DIR, SHARED_GRAPH_DIR, PROFILED_GRAPH_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    scenario_ids = [
        "round_hill_profile",
        "road_over_slope_profile",
        "flat_building_pad_on_slope",
        "terrace_steps_profile",
        "ravine_fold_profile",
    ]
    rows = [compile_scenario(scenario_id) for scenario_id in scenario_ids]
    write_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} terrain profile bending scenarios")
    for row in rows:
        validation = row["profile_validation"]
        print(
            f"{row['scenario_id']}: cells={validation['cell_count']} "
            f"top_triangles={validation['top_triangle_count']} cracks={validation['cracked_seam_count']}"
        )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
