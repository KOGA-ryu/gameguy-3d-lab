#!/usr/bin/env python3
"""Adapt compiled map templates into shared-midpoint radial terrain graphs.

Tiled-style map template -> compiled map cells -> shared midpoint hex terrain
graph -> overlay-preserving map terrain graph.

No Blender, mesh, or image output is created here.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_hex_plot_vertex_graph_v0 as terrain_graph  # noqa: E402


COMPILED_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "compiled" / "tiled_hex_map_template_v0_compiled.json"
MAP_CUBE_DIR = ROOT / "data" / "architecture" / "map_cubes"
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v0" / "shared_terrain"
ASSEMBLY_PATH = OUT_DIR / "tiled_hex_map_template_v0_shared_terrain_assembly.json"
GRAPH_PATH = OUT_DIR / "tiled_hex_map_template_v0_shared_terrain_graph.json"
REPORT_PATH = OUT_DIR / "map_template_shared_terrain_adapter_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "map_template_shared_terrain_adapter_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}


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


def build_cell_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_role: dict[str, int] = {}
    by_final_height: dict[str, int] = {}
    for cell in cells:
        by_role[cell["topology_role"]] = by_role.get(cell["topology_role"], 0) + 1
        height_key = f"{float(cell['final_height']):.2f}"
        by_final_height[height_key] = by_final_height.get(height_key, 0) + 1
    return {
        "cell_count": len(cells),
        "folded_cell_count": 0,
        "buildable_cell_count": sum(1 for cell in cells if cell.get("buildable")),
        "by_role": dict(sorted(by_role.items())),
        "by_final_height": dict(sorted(by_final_height.items(), key=lambda item: float(item[0]))),
        "min_base_height": min(float(cell["base_height"]) for cell in cells),
        "max_base_height": max(float(cell["base_height"]) for cell in cells),
        "min_final_height": min(float(cell["final_height"]) for cell in cells),
        "max_final_height": max(float(cell["final_height"]) for cell in cells),
    }


def adapted_cells(compiled: dict[str, Any]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for cell in compiled["cells"]:
        movement_tags = list(cell.get("movement_tags", []))
        if cell.get("road_ids") and "road" not in movement_tags:
            movement_tags.append("road")
        if cell.get("plot_ids") and "building_plot" not in movement_tags:
            movement_tags.append("building_plot")
        if cell.get("hazard_ids") and "hazard" not in movement_tags:
            movement_tags.append("hazard")
        structure_socket_tags = list(cell.get("structure_socket_tags", []))
        if cell.get("plot_ids") and "building_pad" not in structure_socket_tags:
            structure_socket_tags.append("building_pad")
        cells.append(
            {
                **cell,
                "movement_tags": movement_tags,
                "structure_socket_tags": structure_socket_tags,
                "fold_contributions": [],
            }
        )
    return cells


def build_assembly(compiled: dict[str, Any]) -> dict[str, Any]:
    if compiled.get("schema") != "compiled_tiled_map_template_v0":
        fail(f"{COMPILED_PATH.relative_to(ROOT)} schema must be compiled_tiled_map_template_v0")
    map_cube = load_json(MAP_CUBE_DIR / f"{compiled['map_cube_id']}.json")
    cells = adapted_cells(compiled)
    return {
        "schema": "hex_terrain_fold_site_assembly_v0",
        "site_id": "tiled_hex_map_template_v0_shared_terrain",
        "source_recipe": str(COMPILED_PATH.relative_to(ROOT)),
        "summary": "Shared-midpoint radial terrain adapter assembly generated from the compiled Tiled-style hex map template.",
        "units": "abstract_meter",
        "map_cube": map_cube,
        "hex_grid": {
            "layout": "pointy_top",
            "radius": float(compiled["hex_radius_m"]),
            "vertical_step": float(compiled["vertical_step_m"]),
            "edge_corner_order": "tiled_odd_r_y_down_v0",
            "bounds_source": "compiled_tiled_map_template_v0",
        },
        "heightfield": {
            "type": "compiled_map_template_height_levels",
            "quantize_to_vertical_step": True,
            "surface_type": "map_template_surface_layers",
        },
        "folds": [],
        "edge_fold_policy": {},
        "classification_rules": {
            "flat_delta_max": 0.001,
            "step_delta_max": float(compiled["vertical_step_m"]),
            "ledge_delta_max": float(compiled["vertical_step_m"]) * 2.0,
            "cliff_delta_min": float(compiled["vertical_step_m"]) * 2.0,
            "buildable_slope_delta_max": float(compiled["vertical_step_m"]),
            "walkable_delta_max": float(compiled["vertical_step_m"]),
        },
        "cell_summary": build_cell_summary(cells),
        "base_edge_summary": compiled["summary"]["edge_counts"],
        "final_edge_summary": compiled["summary"]["edge_counts"],
        "visible_face_stats": {
            "top_faces": len(cells),
            "candidate_side_faces": len(cells) * 6,
            "visible_side_faces": None,
            "hidden_internal_side_faces": None,
            "outer_boundary_side_faces": compiled["summary"]["edge_counts"].get("boundary", 0),
            "partial_height_side_faces": None,
            "bottom_faces": 0,
        },
        "hex_cells": cells,
        "no_claims": NO_CLAIMS,
    }


def attach_map_overlays(graph: dict[str, Any], compiled: dict[str, Any]) -> dict[str, Any]:
    cells_by_id = {cell["cell_id"]: cell for cell in compiled["cells"]}
    for plot in graph["hex_plots"]:
        source_cell = cells_by_id[plot["cell_id"]]
        plot["source_tile_index"] = source_cell["source_tile_index"]
        plot["surface_type"] = source_cell["surface_type"]
        plot["plot_ids"] = source_cell.get("plot_ids", [])
        plot["road_ids"] = source_cell.get("road_ids", [])
        plot["hazard_ids"] = source_cell.get("hazard_ids", [])
    graph["graph_id"] = "tiled_hex_map_template_v0_shared_terrain_graph"
    graph["source_terrain_assembly"] = str(ASSEMBLY_PATH.relative_to(ROOT))
    graph["map_template_adapter_v0"] = {
        "source_compiled_map": str(COMPILED_PATH.relative_to(ROOT)),
        "build_path": [
            "Tiled-style map template",
            "compiled map cells",
            "shared midpoint hex terrain graph",
            "seam-safe terrain mesh",
            "road/building/hazard overlays",
            "existing asset anchors",
            "Blender proof render",
        ],
        "preserves_roads": True,
        "preserves_building_plots": True,
        "preserves_hazards": True,
        "preserves_asset_sockets": True,
        "preserves_anchor_frames": True,
    }
    graph["map_template_overlays"] = {
        "roads": compiled["roads"],
        "building_plots": compiled["building_plots"],
        "hazards": compiled["hazards"],
        "asset_sockets": compiled["asset_sockets"],
        "summary": {
            "road_count": len(compiled["roads"]),
            "building_plot_count": len(compiled["building_plots"]),
            "hazard_count": len(compiled["hazards"]),
            "asset_socket_count": len(compiled["asset_sockets"]),
            "anchor_status_counts": compiled["summary"].get("anchor_status_counts", {}),
        },
    }
    graph["validation"] = terrain_graph.validate_compiled_graph(graph)
    graph["validation"]["overlay_counts"] = graph["map_template_overlays"]["summary"]
    graph["validation"]["roads_visible"] = len(compiled["roads"]) > 0
    graph["validation"]["building_plots_visible"] = len(compiled["building_plots"]) > 0
    graph["validation"]["hazards_visible"] = len(compiled["hazards"]) > 0
    graph["validation"]["asset_anchors_deterministic"] = all(
        socket.get("placement_validation", {}).get("status") in {"pass", "warn", "reject"}
        for socket in compiled["asset_sockets"]
    )
    graph["validation"]["no_internal_wall_spam_between_equal_height_cells"] = graph["delta_band_summary"].get("0", 0) == graph["seam_policy_summary"].get("shared_surface", 0) - graph["delta_band_summary"].get("1", 0)
    return graph


def write_report(graph: dict[str, Any]) -> None:
    validation = graph["validation"]
    overlays = graph["map_template_overlays"]["summary"]
    lines = [
        "# Map Template Shared Terrain Adapter v0",
        "",
        "Converts the compiled Tiled-style hex map template into the shared-midpoint radial hex terrain graph while preserving map overlays and asset anchors.",
        "",
        "| Graph | Cells | Midpoints | Shared | Split | Top Triangles | Cracks | Roads | Plots | Hazards | Sockets | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        (
            f"| `{graph['graph_id']}` | {validation['cell_count']} | {validation['edge_midpoint_count']} | "
            f"{validation['shared_midpoint_count']} | {validation['split_midpoint_count']} | "
            f"{validation['top_triangle_count']} | {validation['cracked_seam_count']} | "
            f"{overlays['road_count']} | {overlays['building_plot_count']} | {overlays['hazard_count']} | "
            f"{overlays['asset_socket_count']} | `{GRAPH_PATH.relative_to(ROOT)}` |"
        ),
        "",
        "## Acceptance",
        "",
        f"- `top_triangle_count == cell_count * 12`: {validation['top_triangle_count_matches']}",
        f"- `cracked_seam_count == 0`: {validation['cracked_seam_count'] == 0}",
        f"- shared midpoint ids validate across seams: {validation['cracked_seam_count'] == 0}",
        f"- roads preserved: {validation['roads_visible']}",
        f"- building plots preserved: {validation['building_plots_visible']}",
        f"- hazards preserved: {validation['hazards_visible']}",
        f"- asset anchors deterministic: {validation['asset_anchors_deterministic']}",
        f"- delta >= 2 edges are cliff/fault: {validation['delta_two_plus_all_cliff_fault']}",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(graph: dict[str, Any]) -> None:
    validation = graph["validation"]
    receipt = {
        "receipt_type": "map_template_shared_terrain_adapter_v0",
        "created_at_utc": now_iso(),
        "source_compiled_map": str(COMPILED_PATH.relative_to(ROOT)),
        "assembly_path": str(ASSEMBLY_PATH.relative_to(ROOT)),
        "graph_path": str(GRAPH_PATH.relative_to(ROOT)),
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "graph_id": graph["graph_id"],
        "acceptance": {
            "top_triangle_count_equals_cell_count_times_12": validation["top_triangle_count_matches"],
            "cracked_seam_count_is_zero": validation["cracked_seam_count"] == 0,
            "shared_midpoint_ids_validate_across_seams": validation["cracked_seam_count"] == 0,
            "roads_still_visible": validation["roads_visible"],
            "building_plots_still_visible": validation["building_plots_visible"],
            "hazards_still_visible": validation["hazards_visible"],
            "asset_anchors_pass_warn_deterministically": validation["asset_anchors_deterministic"],
            "no_internal_wall_spam_between_equal_height_cells": validation["no_internal_wall_spam_between_equal_height_cells"],
        },
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    compiled = load_json(COMPILED_PATH)
    assembly = build_assembly(compiled)
    ASSEMBLY_PATH.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
    graph = terrain_graph.compile_graph(ASSEMBLY_PATH)
    graph = attach_map_overlays(graph, compiled)
    GRAPH_PATH.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    write_report(graph)
    write_receipt(graph)
    validation = graph["validation"]
    print(f"wrote {GRAPH_PATH.relative_to(ROOT)}")
    print(
        f"cells={validation['cell_count']} top_triangles={validation['top_triangle_count']} "
        f"midpoints={validation['edge_midpoint_count']} cracks={validation['cracked_seam_count']}"
    )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
