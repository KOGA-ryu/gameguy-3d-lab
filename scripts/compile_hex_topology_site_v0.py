#!/usr/bin/env python3
"""Compile hex_topology_site_recipe_v0 into hex terrain/site assembly JSON.

This is the first cube-grid terrain bridge:

standard_32m_cube_v0 -> pointy-top axial hex surface -> elevation deltas ->
route/fall-edge facts -> foundation adapter -> placed building assembly

No mesh, Blender, or render output is created here.
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
SITE_DIR = ROOT / "data" / "architecture" / "hex_topology_sites"
ASSEMBLY_DIR = ROOT / "goal" / "architecture" / "building_assemblies_v0" / "assemblies"
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
OUT_DIR = ROOT / "goal" / "architecture" / "hex_topology_sites_v0"
COMPILED_DIR = OUT_DIR / "sites"
REPORT_PATH = OUT_DIR / "hex_topology_site_catalog_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "hex_topology_sites_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}

AXIAL_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]


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
        if value < 0:
            return f"m{abs(value)}"
        return f"p{value}"

    return f"hex_{part(q)}_{part(r)}"


def axial_to_world(q: int, r: int, radius: float) -> tuple[float, float]:
    # Pointy-top axial coordinates.
    x = radius * math.sqrt(3.0) * (q + r * 0.5)
    y = radius * 1.5 * r
    return x, y


def safe_condition_matches(condition: str, x: float, y: float) -> bool:
    allowed = {"__builtins__": {}}
    names = {"x": x, "y": y, "abs": abs}
    try:
        return bool(eval(condition, allowed, names))  # noqa: S307 - local authored recipe expressions only.
    except Exception as exc:  # pragma: no cover - error path is reported through fail().
        fail(f"invalid elevation condition `{condition}`: {exc}")


def classify_elevation(recipe: dict[str, Any], x: float, y: float) -> dict[str, Any]:
    model = recipe["elevation_model"]
    selected: dict[str, Any] | None = None
    for rule in model["base_rules"]:
        if safe_condition_matches(rule["condition"], x, y):
            selected = dict(rule)
            break
    if selected is None:
        fail(f"no base elevation rule matched x={x} y={y}")

    for override in model.get("overrides", []):
        if safe_condition_matches(override["condition"], x, y):
            selected = dict(override)

    return {
        "elevation": float(selected["elevation"]),
        "terrain_role": selected["terrain_role"],
        "semantic_tags": selected["semantic_tags"],
        "rule_id": selected.get("rule_id", selected.get("override_id", "unknown_rule")),
    }


def generate_hex_cells(site: dict[str, Any], map_cube: dict[str, Any]) -> list[dict[str, Any]]:
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
            classified = classify_elevation(site, x, y)
            elevation = classified["elevation"]
            if elevation < z_min or elevation > z_max:
                fail(f"hex {q},{r} elevation {elevation} outside map cube z range")
            cells.append(
                {
                    "cell_id": cell_id(q, r),
                    "q": q,
                    "r": r,
                    "center": [round(x, 6), round(y, 6)],
                    "elevation": round(elevation, 6),
                    "terrain_role": classified["terrain_role"],
                    "semantic_tags": classified["semantic_tags"],
                    "elevation_rule": classified["rule_id"],
                }
            )
    return sorted(cells, key=lambda cell: (cell["r"], cell["q"]))


def classify_neighbor_edges(cells: list[dict[str, Any]], rules: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_coord = {(cell["q"], cell["r"]): cell for cell in cells}
    edge_rows: list[dict[str, Any]] = []
    fall_edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    walkable_delta = float(rules["walkable_delta_max"])
    slope_delta = float(rules["slope_delta_max"])
    fall_delta = float(rules["fall_edge_delta_min"])

    for cell in cells:
        for dq, dr in AXIAL_DIRECTIONS:
            other = by_coord.get((cell["q"] + dq, cell["r"] + dr))
            if other is None:
                continue
            a = cell["cell_id"]
            b = other["cell_id"]
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)

            delta = abs(float(cell["elevation"]) - float(other["elevation"]))
            if delta >= fall_delta:
                edge_type = "fall_edge"
                traversal = "blocked_without_connector"
            elif delta <= walkable_delta:
                edge_type = "walkable"
                traversal = "walkable"
            elif delta <= slope_delta:
                edge_type = "slope"
                traversal = "difficult"
            else:
                edge_type = "blocked"
                traversal = "blocked"

            edge = {
                "edge_id": f"edge_{a}_{b}",
                "from": a,
                "to": b,
                "elevation_delta": round(delta, 6),
                "edge_type": edge_type,
                "traversal": traversal,
            }
            edge_rows.append(edge)
            if edge_type == "fall_edge":
                high = cell if float(cell["elevation"]) >= float(other["elevation"]) else other
                low = other if high is cell else cell
                fall_edges.append(
                    {
                        "fact_id": f"fall_{high['cell_id']}_to_{low['cell_id']}",
                        "affordance": "fall_edge",
                        "high_cell": high["cell_id"],
                        "low_cell": low["cell_id"],
                        "drop_height": round(delta, 6),
                        "risk": min(1.0, round(delta / max(fall_delta, 0.001), 3)),
                    }
                )
    return edge_rows, fall_edges


def summarize_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_role: dict[str, int] = {}
    by_elevation: dict[str, int] = {}
    for cell in cells:
        by_role[cell["terrain_role"]] = by_role.get(cell["terrain_role"], 0) + 1
        elevation = f"{float(cell['elevation']):.2f}"
        by_elevation[elevation] = by_elevation.get(elevation, 0) + 1
    return {
        "cell_count": len(cells),
        "by_role": dict(sorted(by_role.items())),
        "by_elevation": dict(sorted(by_elevation.items(), key=lambda item: float(item[0]))),
    }


def solid_dimensions(solids: dict[str, dict[str, Any]], asset_ref: str) -> dict[str, float]:
    if asset_ref not in solids:
        fail(f"unknown compiled solid asset_ref `{asset_ref}`")
    return solids[asset_ref]["semantic_outputs"]["bounds_role_summary"]["dimensions"]


def scale_for_target(solids: dict[str, dict[str, Any]], asset_ref: str, target: tuple[float, float, float]) -> list[float]:
    dims = solid_dimensions(solids, asset_ref)
    base = (float(dims["width_x"]), float(dims["depth_y"]), float(dims["height_z"]))
    return [round(target[i] / base[i], 6) for i in range(3)]


def rotate_xy(x: float, y: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    return (x * c - y * s, x * s + y * c)


def transform_instance(inst: dict[str, Any], origin: list[float], rotation_z: float, elevation: float) -> dict[str, Any]:
    lx, ly, lz = [float(v) for v in inst["translation"]]
    rx, ry = rotate_xy(lx, ly, rotation_z)
    rotation = list(inst.get("rotation_degrees", [0.0, 0.0, 0.0]))
    rotation[2] = round(float(rotation[2]) + rotation_z, 6)
    transformed = dict(inst)
    transformed["instance_id"] = f"building_{inst['instance_id']}"
    transformed["translation"] = [
        round(float(origin[0]) + rx, 6),
        round(float(origin[1]) + ry, 6),
        round(elevation + lz, 6),
    ]
    transformed["rotation_degrees"] = rotation
    transformed["topology_source"] = "hex_building_placement"
    return transformed


def compile_foundation(site: dict[str, Any], solids: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []
    for inst in site["foundation_adapter"]["asset_instances"]:
        target = tuple(float(v) for v in inst["target_dimensions"])
        compiled.append(
            {
                "instance_id": inst["instance_id"],
                "asset_ref": inst["asset_ref"],
                "role": inst["role"],
                "translation": [round(float(v), 6) for v in inst["translation"]],
                "rotation_degrees": inst.get("rotation_degrees", [0.0, 0.0, 0.0]),
                "scale": scale_for_target(solids, inst["asset_ref"], target),
                "semantic_tags": inst.get("semantic_tags", []),
                "target_dimensions": {
                    "width_x": round(target[0], 6),
                    "depth_y": round(target[1], 6),
                    "height_z": round(target[2], 6),
                },
                "topology_source": "hex_foundation_adapter",
            }
        )
    return compiled


def compile_site(path: Path, solids: dict[str, dict[str, Any]]) -> dict[str, Any]:
    site = load_json(path)
    if site.get("schema") != "hex_topology_site_recipe_v0":
        fail(f"{path.relative_to(ROOT)} schema must be hex_topology_site_recipe_v0")
    if site.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    map_cube_path = MAP_CUBE_DIR / f"{site['map_cube_ref']}.json"
    if not map_cube_path.exists():
        fail(f"missing map cube `{site['map_cube_ref']}`")
    map_cube = load_json(map_cube_path)
    if map_cube.get("no_claims") != NO_CLAIMS:
        fail(f"{map_cube_path.relative_to(ROOT)} no_claims must exactly match required false claims")

    cells = generate_hex_cells(site, map_cube)
    neighbor_edges, fall_edges = classify_neighbor_edges(cells, site["classification_rules"])
    summary = summarize_cells(cells)

    placement = site["building_placement"]
    assembly_path = ASSEMBLY_DIR / f"{placement['source_assembly_id']}.json"
    if not assembly_path.exists():
        fail(f"missing source assembly `{placement['source_assembly_id']}`")
    building = load_json(assembly_path)
    origin = [float(v) for v in placement["origin"]]
    rotation_z = float(placement.get("rotation_degrees", [0.0, 0.0, 0.0])[2])
    elevation = float(placement["elevation"])

    building_instances = [transform_instance(inst, origin, rotation_z, elevation) for inst in building["instances"]]
    foundation_instances = compile_foundation(site, solids)

    edge_counts: dict[str, int] = {}
    for edge in neighbor_edges:
        edge_counts[edge["edge_type"]] = edge_counts.get(edge["edge_type"], 0) + 1

    buildable_cells = [cell["cell_id"] for cell in cells if cell["terrain_role"] == "buildable_pad"]
    affordance_facts = [
        {
            "fact_id": "hex_cell_count",
            "affordance": "terrain_grid",
            "cell_count": len(cells),
            "map_cube_ref": site["map_cube_ref"],
        },
        {
            "fact_id": "hex_buildable_patch",
            "affordance": "buildable_site",
            "buildable_cell_count": len(buildable_cells),
            "required_flat_hexes": placement["required_flat_hexes"],
            "passes_requirement": len(buildable_cells) >= int(placement["required_flat_hexes"]),
        },
        {
            "fact_id": "hex_height_advantage",
            "affordance": "height_advantage",
            "max_elevation": max(float(cell["elevation"]) for cell in cells),
            "min_elevation": min(float(cell["elevation"]) for cell in cells),
            "elevation_delta": round(max(float(cell["elevation"]) for cell in cells) - min(float(cell["elevation"]) for cell in cells), 6),
        },
        {
            "fact_id": "hex_fall_edge_summary",
            "affordance": "fall_edge",
            "fall_edge_count": len(fall_edges),
            "sample_fall_edges": fall_edges[:20],
        },
    ]

    return {
        "schema": "hex_topology_site_assembly_v0",
        "site_id": site["site_id"],
        "source_recipe": str(path.relative_to(ROOT)),
        "summary": site.get("summary", ""),
        "units": site["units"],
        "map_cube": map_cube,
        "hex_grid": site["hex_grid"],
        "cell_summary": summary,
        "neighbor_edge_summary": dict(sorted(edge_counts.items())),
        "hex_cells": cells,
        "neighbor_edges": neighbor_edges,
        "fall_edges": fall_edges,
        "source_building_assembly": placement["source_assembly_id"],
        "building_placement": placement,
        "foundation_instances": foundation_instances,
        "building_instances": building_instances,
        "affordance_facts": affordance_facts,
        "no_claims": NO_CLAIMS,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Hex Topology Sites v0",
        "",
        "Compiled pointy-top hex terrain inside the standard `32x32x8` map cube.",
        "",
        "```text",
        "standard map cube -> axial hex cells -> elevations -> neighbor edge facts -> building site -> Blender proof",
        "```",
        "",
        "| Site | Cells | Walkable Edges | Slope Edges | Fall Edges | Building Instances | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        edge_counts = row["neighbor_edge_summary"]
        lines.append(
            f"| `{row['site_id']}` | {row['cell_count']} | {edge_counts.get('walkable', 0)} | {edge_counts.get('slope', 0)} | {edge_counts.get('fall_edge', 0)} | {row['building_instance_count']} | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "- A bounded `32x32x8` cube can contain a full hex terrain surface.",
            "- Elevation values derive route, slope, and fall-edge classifications.",
            "- The building system can plant an existing building assembly on a flat high hex patch.",
            "- The hex terrain layer emits facts useful to the future AI graph without requiring full AI integration yet.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "hex_topology_sites_v0",
        "created_at_utc": now_iso(),
        "site_count": len(rows),
        "sites": rows,
        "rules": {
            "standard_cube_grid_used": True,
            "hex_surface_mode_not_stacked_voxels": True,
            "elevation_derives_neighbor_edges": True,
            "fall_edges_derived_from_height_delta": True,
            "building_assembly_reused": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True
        },
        "recommended_next_goal": "Render hex_topology_site_assembly_v0 in Blender and compare it against the box terrain proof.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    solids = {path.stem: load_json(path) for path in sorted(SOLID_DIR.glob("*.json"))}
    if not solids:
        fail("no Asset Mill solids found; run asset_pump_v0.py with simple_solids_v0.json first")

    rows: list[dict[str, Any]] = []
    for path in sorted(SITE_DIR.glob("*.json")):
        compiled = compile_site(path, solids)
        out = COMPILED_DIR / f"{compiled['site_id']}_assembly.json"
        out.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "site_id": compiled["site_id"],
                "map_cube_ref": compiled["map_cube"]["map_cube_id"],
                "cell_count": compiled["cell_summary"]["cell_count"],
                "cell_summary": compiled["cell_summary"],
                "neighbor_edge_summary": compiled["neighbor_edge_summary"],
                "fall_edge_count": len(compiled["fall_edges"]),
                "foundation_instance_count": len(compiled["foundation_instances"]),
                "building_instance_count": len(compiled["building_instances"]),
                "output_path": str(out.relative_to(ROOT)),
            }
        )

    write_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} hex topology site assemblies")
    for row in rows:
        print(f"{row['site_id']}: {row['cell_count']} hex cells, {row['fall_edge_count']} fall edges")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
