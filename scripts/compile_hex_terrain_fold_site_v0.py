#!/usr/bin/env python3
"""Compile hex_terrain_fold_recipe_v0 into folded hex terrain assembly JSON.

This compiler proves the terrain grammar path:

standard map cube -> axial/cube hex cells -> base heightfield ->
fold offsets -> final heights -> edge grammar -> visible terrain face stats

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
MAP_CUBE_DIR = ROOT / "data" / "architecture" / "map_cubes"
SITE_DIR = ROOT / "data" / "architecture" / "hex_terrain_fold_sites"
OUT_DIR = ROOT / "goal" / "architecture" / "hex_terrain_fold_sites_v0"
COMPILED_DIR = OUT_DIR / "sites"
REPORT_PATH = OUT_DIR / "hex_terrain_fold_site_catalog_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "hex_terrain_fold_sites_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}

AXIAL_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
EDGE_NAMES = ["east", "north_east", "north_west", "west", "south_west", "south_east"]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cell_id(q: int, r: int) -> str:
    def part(value: int) -> str:
        return f"m{abs(value)}" if value < 0 else f"p{value}"

    return f"hex_{part(q)}_{part(r)}"


def axial_to_world(q: int, r: int, radius: float) -> tuple[float, float]:
    # Pointy-top axial coordinates.
    x = radius * math.sqrt(3.0) * (q + r * 0.5)
    y = radius * 1.5 * r
    return x, y


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def quantize(value: float, step: float) -> float:
    if step <= 0:
        return value
    return round(value / step) * step


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    length_sq = abx * abx + aby * aby
    if length_sq == 0.0:
        return math.hypot(px - ax, py - ay)
    t = clamp((apx * abx + apy * aby) / length_sq, 0.0, 1.0)
    cx = ax + t * abx
    cy = ay + t * aby
    return math.hypot(px - cx, py - cy)


def evaluate_round_hill(site: dict[str, Any], x: float, y: float) -> float:
    heightfield = site["heightfield"]
    cx, cy = [float(v) for v in heightfield["center"]]
    radius = float(heightfield["radius"])
    base_height = float(heightfield["base_height"])
    peak_height = float(heightfield["peak_height"])
    distance = math.hypot(x - cx, y - cy)
    t = clamp(distance / radius, 0.0, 1.0)
    if heightfield.get("falloff") == "smoothstep":
        falloff = 1.0 - smoothstep(0.0, 1.0, t)
    else:
        falloff = 1.0 - t
    height = base_height + peak_height * falloff
    if heightfield.get("quantize_to_vertical_step", False):
        height = quantize(height, float(site["hex_grid"]["vertical_step"]))
    return height


def evaluate_fold_offset(site: dict[str, Any], x: float, y: float) -> tuple[float, list[dict[str, Any]]]:
    total = 0.0
    contributions: list[dict[str, Any]] = []
    for fold in site.get("folds", []):
        start = fold["line"]["start"]
        end = fold["line"]["end"]
        distance = distance_to_segment(x, y, float(start[0]), float(start[1]), float(end[0]), float(end[1]))
        falloff_radius = float(fold["falloff_radius"])
        if distance > falloff_radius:
            continue
        influence = 1.0 - smoothstep(0.0, falloff_radius, distance)
        magnitude = float(fold["magnitude"])
        if fold["type"] == "valley":
            signed = -magnitude * influence
        elif fold["type"] == "mountain":
            signed = magnitude * influence
        elif fold["type"] == "hinge":
            signed = magnitude * influence * 0.5
        else:
            signed = 0.0
        total += signed
        contributions.append(
            {
                "fold_id": fold["fold_id"],
                "type": fold["type"],
                "offset": round(signed, 6),
                "influence": round(influence, 6),
            }
        )
    return total, contributions


def topology_role_for_height(heightfield: dict[str, Any], x: float, y: float, final_height: float) -> tuple[str, list[str], bool, list[str]]:
    cx, cy = [float(v) for v in heightfield["center"]]
    radius = float(heightfield["radius"])
    d = math.hypot(x - cx, y - cy)
    t = clamp(d / radius, 0.0, 1.0)
    if t <= 0.22:
        return "hilltop", ["walkable", "height_advantage", "buildable_site"], True, ["building_pad_candidate"]
    if t <= 0.52:
        return "upper_slope", ["walkable", "height_advantage"], False, []
    if t <= 0.82:
        return "lower_slope", ["walkable", "slope"], False, []
    return "outer_flat", ["walkable"], True, ["edge_stitch_candidate"] if final_height <= 0.5 else []


def classify_directed_edge(delta: float, rules: dict[str, Any]) -> str:
    abs_delta = abs(delta)
    if abs_delta <= float(rules["flat_delta_max"]):
        return "flat"
    if abs_delta <= float(rules["step_delta_max"]):
        return "step_up" if delta > 0 else "step_down"
    if abs_delta <= float(rules["ledge_delta_max"]):
        return "ledge"
    return "cliff"


def traversal_for_edge(edge_type: str, delta: float, rules: dict[str, Any]) -> str:
    if edge_type == "flat":
        return "walkable"
    if abs(delta) <= float(rules["walkable_delta_max"]):
        return "walkable_step"
    if edge_type == "ledge":
        return "difficult"
    if edge_type == "cliff":
        return "blocked_without_connector"
    return "unknown"


def generate_cells(site: dict[str, Any], map_cube: dict[str, Any]) -> list[dict[str, Any]]:
    radius = float(site["hex_grid"]["radius"])
    if radius <= 0:
        fail("hex radius must be positive")
    x_min, x_max = [float(v) for v in map_cube["coordinate_range"]["x"]]
    y_min, y_max = [float(v) for v in map_cube["coordinate_range"]["y"]]
    z_min, z_max = [float(v) for v in map_cube["coordinate_range"]["z"]]
    span = max(abs(x_min), abs(x_max), abs(y_min), abs(y_max))
    coord_limit = int(math.ceil(span / radius * 1.5)) + 4

    cells: list[dict[str, Any]] = []
    for q in range(-coord_limit, coord_limit + 1):
        for r in range(-coord_limit, coord_limit + 1):
            x, y = axial_to_world(q, r, radius)
            if not (x_min <= x <= x_max and y_min <= y <= y_max):
                continue
            base_height = evaluate_round_hill(site, x, y)
            fold_offset, fold_contributions = evaluate_fold_offset(site, x, y)
            final_height = clamp(base_height + fold_offset, z_min, z_max)
            if site["heightfield"].get("quantize_to_vertical_step", False):
                final_height = quantize(final_height, float(site["hex_grid"]["vertical_step"]))
            if base_height < z_min or base_height > z_max or final_height < z_min or final_height > z_max:
                fail(f"cell {q},{r} height outside map cube z range")
            topology_role, movement_tags, buildable, socket_tags = topology_role_for_height(site["heightfield"], x, y, final_height)
            cells.append(
                {
                    "cell_id": cell_id(q, r),
                    "q": q,
                    "r": r,
                    "s": -q - r,
                    "world_x": round(x, 6),
                    "world_y": round(y, 6),
                    "base_height": round(base_height, 6),
                    "fold_offset": round(final_height - base_height, 6),
                    "final_height": round(final_height, 6),
                    "surface_type": site["heightfield"]["surface_type"],
                    "topology_role": topology_role,
                    "buildable": buildable,
                    "edge_profiles": [],
                    "movement_tags": movement_tags,
                    "structure_socket_tags": socket_tags,
                    "fold_contributions": fold_contributions,
                }
            )
    return sorted(cells, key=lambda cell: (cell["r"], cell["q"]))


def classify_edges(cells: list[dict[str, Any]], rules: dict[str, Any], height_key: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    by_coord = {(cell["q"], cell["r"]): cell for cell in cells}
    edge_rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    for cell in cells:
        directed_profiles: list[str] = []
        for direction_index, (dq, dr) in enumerate(AXIAL_DIRECTIONS):
            neighbor = by_coord.get((cell["q"] + dq, cell["r"] + dr))
            if neighbor is None:
                directed_profiles.append("boundary")
                counts["boundary"] = counts.get("boundary", 0) + 1
                continue
            delta = float(neighbor[height_key]) - float(cell[height_key])
            directed_type = classify_directed_edge(delta, rules)
            directed_profiles.append(directed_type)

            key = tuple(sorted((cell["cell_id"], neighbor["cell_id"])))
            if key in seen:
                continue
            seen.add(key)
            abs_delta = abs(float(cell[height_key]) - float(neighbor[height_key]))
            undirected_type = classify_directed_edge(abs_delta, rules)
            counts[undirected_type] = counts.get(undirected_type, 0) + 1
            high = cell if float(cell[height_key]) >= float(neighbor[height_key]) else neighbor
            low = neighbor if high is cell else cell
            edge_rows.append(
                {
                    "edge_id": f"edge_{cell['cell_id']}_{neighbor['cell_id']}",
                    "from": cell["cell_id"],
                    "to": neighbor["cell_id"],
                    "direction": EDGE_NAMES[direction_index],
                    "height_key": height_key,
                    "edge_type": undirected_type,
                    "traversal": traversal_for_edge(undirected_type, abs_delta, rules),
                    "elevation_delta": round(abs_delta, 6),
                    "high_cell": high["cell_id"],
                    "low_cell": low["cell_id"],
                }
            )
        if height_key == "final_height":
            cell["edge_profiles"] = directed_profiles
    return edge_rows, dict(sorted(counts.items()))


def visible_face_stats(cells: list[dict[str, Any]]) -> dict[str, int]:
    by_coord = {(cell["q"], cell["r"]): cell for cell in cells}
    stats = {
        "top_faces": len(cells),
        "candidate_side_faces": len(cells) * 6,
        "visible_side_faces": 0,
        "hidden_internal_side_faces": 0,
        "outer_boundary_side_faces": 0,
        "partial_height_side_faces": 0,
        "bottom_faces": 0,
    }
    for cell in cells:
        top_z = float(cell["final_height"])
        for dq, dr in AXIAL_DIRECTIONS:
            neighbor = by_coord.get((cell["q"] + dq, cell["r"] + dr))
            if neighbor is None:
                stats["outer_boundary_side_faces"] += 1
                stats["visible_side_faces"] += 1
                continue
            neighbor_z = float(neighbor["final_height"])
            if neighbor_z >= top_z:
                stats["hidden_internal_side_faces"] += 1
            else:
                stats["partial_height_side_faces"] += 1
                stats["visible_side_faces"] += 1
    return stats


def summarize_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_role: dict[str, int] = {}
    by_final_height: dict[str, int] = {}
    folded_count = 0
    for cell in cells:
        by_role[cell["topology_role"]] = by_role.get(cell["topology_role"], 0) + 1
        height = f"{float(cell['final_height']):.2f}"
        by_final_height[height] = by_final_height.get(height, 0) + 1
        if abs(float(cell["fold_offset"])) > 0.001:
            folded_count += 1
    return {
        "cell_count": len(cells),
        "folded_cell_count": folded_count,
        "buildable_cell_count": sum(1 for cell in cells if cell["buildable"]),
        "by_role": dict(sorted(by_role.items())),
        "by_final_height": dict(sorted(by_final_height.items(), key=lambda item: float(item[0]))),
        "min_base_height": min(float(cell["base_height"]) for cell in cells),
        "max_base_height": max(float(cell["base_height"]) for cell in cells),
        "min_final_height": min(float(cell["final_height"]) for cell in cells),
        "max_final_height": max(float(cell["final_height"]) for cell in cells),
    }


def compile_site(path: Path) -> dict[str, Any]:
    site = load_json(path)
    if site.get("schema") != "hex_terrain_fold_recipe_v0":
        fail(f"{path.relative_to(ROOT)} schema must be hex_terrain_fold_recipe_v0")
    if site.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    map_cube_path = MAP_CUBE_DIR / f"{site['map_cube_ref']}.json"
    if not map_cube_path.exists():
        fail(f"missing map cube `{site['map_cube_ref']}`")
    map_cube = load_json(map_cube_path)
    if map_cube.get("no_claims") != NO_CLAIMS:
        fail(f"{map_cube_path.relative_to(ROOT)} no_claims must exactly match required false claims")

    cells = generate_cells(site, map_cube)
    base_edges, base_edge_counts = classify_edges(cells, site["classification_rules"], "base_height")
    final_edges, final_edge_counts = classify_edges(cells, site["classification_rules"], "final_height")
    face_stats = visible_face_stats(cells)
    cell_summary = summarize_cells(cells)

    edge_profile_errors = [cell["cell_id"] for cell in cells if len(cell["edge_profiles"]) != 6]
    if edge_profile_errors:
        fail(f"cells missing six edge profiles: {edge_profile_errors[:5]}")

    return {
        "schema": "hex_terrain_fold_site_assembly_v0",
        "site_id": site["site_id"],
        "source_recipe": str(path.relative_to(ROOT)),
        "summary": site.get("summary", ""),
        "units": site["units"],
        "map_cube": map_cube,
        "hex_grid": site["hex_grid"],
        "heightfield": site["heightfield"],
        "folds": site["folds"],
        "edge_fold_policy": site.get("edge_fold_policy", {}),
        "classification_rules": site["classification_rules"],
        "cell_summary": cell_summary,
        "base_edge_summary": base_edge_counts,
        "final_edge_summary": final_edge_counts,
        "visible_face_stats": face_stats,
        "hex_cells": cells,
        "base_edges": base_edges,
        "final_edges": final_edges,
        "affordance_facts": [
            {
                "fact_id": "round_hill_height_advantage",
                "affordance": "height_advantage",
                "max_final_height": cell_summary["max_final_height"],
                "min_final_height": cell_summary["min_final_height"],
                "elevation_delta": round(cell_summary["max_final_height"] - cell_summary["min_final_height"], 6),
            },
            {
                "fact_id": "round_hill_buildable_cells",
                "affordance": "buildable_site",
                "buildable_cell_count": cell_summary["buildable_cell_count"],
            },
            {
                "fact_id": "folded_cells",
                "affordance": "fold_seam_logic",
                "folded_cell_count": cell_summary["folded_cell_count"],
                "fold_count": len(site["folds"]),
            },
        ],
        "no_claims": NO_CLAIMS,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Hex Terrain Fold Sites v0",
        "",
        "Compiled hex terrain sites with base heightfields, fold offsets, final heights, edge grammar, and visible-face stats.",
        "",
        "```text",
        "map cube -> hex cells q/r/s -> base height -> fold offset -> final height -> edge grammar -> optimized mesh",
        "```",
        "",
        "| Site | Cells | Folded Cells | Max Height | Base Edges | Final Edges | Visible Side Faces | Output |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['site_id']}` | {row['cell_count']} | {row['folded_cell_count']} | {row['max_final_height']:.2f} | `{row['base_edge_summary']}` | `{row['final_edge_summary']}` | {row['visible_side_faces']} | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "`base_height` remains the tactical truth. `final_height` is the visible/topology-refined height after fold offsets.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "hex_terrain_fold_sites_v0",
        "created_at_utc": now_iso(),
        "site_count": len(rows),
        "sites": rows,
        "rules": {
            "cube_coordinate_hexes": True,
            "q_plus_r_plus_s_equals_zero": True,
            "base_height_preserved": True,
            "final_height_includes_fold_offset": True,
            "edge_profiles_have_six_entries": True,
            "visible_faces_only": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True
        },
        "recommended_next_goal": "Render round_hill_fold_site_v0 with the optimized terrain mesh renderer.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for path in sorted(SITE_DIR.glob("*.json")):
        compiled = compile_site(path)
        out = COMPILED_DIR / f"{compiled['site_id']}_assembly.json"
        out.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "site_id": compiled["site_id"],
                "map_cube_ref": compiled["map_cube"]["map_cube_id"],
                "cell_count": compiled["cell_summary"]["cell_count"],
                "folded_cell_count": compiled["cell_summary"]["folded_cell_count"],
                "buildable_cell_count": compiled["cell_summary"]["buildable_cell_count"],
                "max_final_height": compiled["cell_summary"]["max_final_height"],
                "base_edge_summary": compiled["base_edge_summary"],
                "final_edge_summary": compiled["final_edge_summary"],
                "visible_side_faces": compiled["visible_face_stats"]["visible_side_faces"],
                "output_path": str(out.relative_to(ROOT)),
            }
        )

    if not rows:
        fail(f"no hex terrain fold recipes found in {SITE_DIR.relative_to(ROOT)}")
    write_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} hex terrain fold site assemblies")
    for row in rows:
        print(
            f"{row['site_id']}: {row['cell_count']} cells, "
            f"{row['folded_cell_count']} folded, max height {row['max_final_height']:.2f}"
        )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
