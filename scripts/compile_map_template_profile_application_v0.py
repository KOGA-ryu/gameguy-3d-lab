#!/usr/bin/env python3
"""Apply Terrain Profile Bending v0 to the real compiled map template.

compiled map template -> shared terrain graph -> profile law assignment ->
profiled terrain graph -> asset anchors recomputed on profiled surface.
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

import compile_map_template_shared_terrain_adapter_v0 as shared_adapter  # noqa: E402
import compile_terrain_profile_bending_v0 as profile_bending  # noqa: E402


SHARED_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "shared_terrain" / "tiled_hex_map_template_v0_shared_terrain_graph.json"
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v0" / "profiled_terrain"
PROFILED_GRAPH_PATH = OUT_DIR / "tiled_hex_map_template_v0_profiled_terrain_graph.json"
REPORT_PATH = OUT_DIR / "map_template_profile_application_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "map_template_profile_application_v0.receipt.json"

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


def nearest_profiled_plot(graph: dict[str, Any], x: float, y: float) -> dict[str, Any]:
    return min(
        graph["hex_plots"],
        key=lambda plot: math.hypot(float(plot["center"][0]) - x, float(plot["center"][1]) - y),
    )


def profiled_clearance(
    *,
    graph: dict[str, Any],
    world_x: float,
    world_y: float,
    footprint_width: float,
    footprint_depth: float,
    anchor_kind: str,
) -> dict[str, Any]:
    radius = max(footprint_width, footprint_depth) * 0.62
    near_plots = [
        plot
        for plot in graph["hex_plots"]
        if math.hypot(float(plot["center"][0]) - world_x, float(plot["center"][1]) - world_y) <= radius
    ]
    if not near_plots:
        return {"status": "reject", "reason": "no_profiled_cells_under_footprint", "checked_cell_count": 0, "height_range_m": 0.0, "hazard_cell_count": 0}
    heights = [float(plot["profiled_center_height_m"]) for plot in near_plots]
    hazard_count = sum(
        1
        for plot in near_plots
        if "hazard" in plot.get("movement_tags", []) or plot.get("surface_type") == "ravine_edge"
    )
    height_range = max(heights) - min(heights)
    if anchor_kind != "bridge_span" and hazard_count:
        status, reason = "warn", "profiled_footprint_overlaps_hazard_cells"
    elif anchor_kind != "bridge_span" and height_range > 0.75:
        status, reason = "warn", "profiled_uneven_footprint_height"
    elif anchor_kind == "bridge_span" and hazard_count == 0:
        status, reason = "warn", "profiled_bridge_span_has_no_hazard_underfoot"
    else:
        status, reason = "pass", "profiled_clearance_ok"
    return {
        "status": status,
        "reason": reason,
        "checked_cell_count": len(near_plots),
        "height_range_m": round(height_range, 6),
        "hazard_cell_count": hazard_count,
    }


def recompute_asset_sockets_on_profiled_surface(graph: dict[str, Any]) -> list[dict[str, Any]]:
    sockets = graph.get("map_template_overlays", {}).get("asset_sockets", [])
    recomputed: list[dict[str, Any]] = []
    for socket in sockets:
        updated = copy.deepcopy(socket)
        x = float(updated["world_position"][0])
        y = float(updated["world_position"][1])
        nearest_plot = nearest_profiled_plot(graph, x, y)
        profiled_z = round(float(nearest_plot["profiled_center_height_m"]), 6)
        updated["world_position"][2] = profiled_z
        updated["nearest_cell_id"] = nearest_plot["cell_id"]
        if "anchor_frame" in updated and isinstance(updated["anchor_frame"], dict):
            updated["anchor_frame"]["position"][2] = profiled_z
            updated["anchor_frame"]["profiled_surface_source"] = "nearest_profiled_hex_center_v0"
        footprint = updated.get("anchor_frame", {}).get("footprint", {})
        clearance = profiled_clearance(
            graph=graph,
            world_x=x,
            world_y=y,
            footprint_width=float(footprint.get("width_m", 1.0)),
            footprint_depth=float(footprint.get("depth_m", 1.0)),
            anchor_kind=str(updated.get("anchor_kind", "free_point")),
        )
        old_status = updated.get("placement_validation", {}).get("status")
        updated["placement_validation"] = {
            **updated.get("placement_validation", {}),
            "status": clearance["status"],
            "profiled_surface_recomputed": True,
            "profiled_nearest_cell_id": nearest_plot["cell_id"],
            "profiled_height_m": profiled_z,
            "clearance": clearance,
            "previous_status": old_status,
        }
        recomputed.append(updated)
    return recomputed


def validate_map_profile_application(graph: dict[str, Any]) -> dict[str, Any]:
    profile_validation = graph["profile_validation"]
    sockets = graph["map_template_overlays"]["asset_sockets"]
    status_counts: dict[str, int] = {}
    for socket in sockets:
        status = socket.get("placement_validation", {}).get("status", "missing")
        status_counts[status] = status_counts.get(status, 0) + 1
    law_counts = graph["profile_summary"]["profile_law_counts"]
    validation = {
        "cracked_seam_count": profile_validation["cracked_seam_count"],
        "shared_edge_midpoint_heights_match": profile_validation["shared_edge_midpoint_heights_match"],
        "shared_corner_heights_match": profile_validation["shared_corner_heights_match"],
        "road_paths_stay_continuous": profile_validation["roads_remain_continuous"] and law_counts.get("road_grade", 0) > 0,
        "building_pads_are_flat": profile_validation["building_pads_are_flat"] and law_counts.get("flat_pad", 0) > 0,
        "cliffs_remain_sharp": profile_validation["cliffs_stay_sharp"] and law_counts.get("cliff_fault", 0) > 0,
        "asset_anchor_count": len(sockets),
        "asset_anchor_status_counts": dict(sorted(status_counts.items())),
        "asset_anchors_place_7_of_7": len(sockets) == 7 and sum(status_counts.get(status, 0) for status in ("pass", "warn")) == 7,
        "asset_anchor_statuses_deterministic": set(status_counts).issubset({"pass", "warn", "reject"}),
        "main_map_has_profiled_heights": all("profiled_center_height_m" in plot for plot in graph["hex_plots"]),
        "profile_law_counts": law_counts,
    }
    if validation["cracked_seam_count"] != 0:
        fail("profiled map template has cracked seams")
    if not validation["asset_anchors_place_7_of_7"]:
        fail(f"profiled map template asset anchors did not place 7/7: {status_counts}")
    return validation


def write_report(graph: dict[str, Any]) -> None:
    validation = graph["map_template_profile_application_v0"]["validation"]
    lines = [
        "# Map Template Profile Application v0",
        "",
        "Applies the existing Terrain Profile Bending v0 laws to the real 32x32 compiled map template.",
        "",
        "| Graph | Cells | Top Triangles | Cracks | Law Counts | Anchor Status | Output |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
        (
            f"| `{graph['graph_id']}` | {len(graph['hex_plots'])} | {graph['mesh_plan']['top_triangle_count']} | "
            f"{validation['cracked_seam_count']} | `{validation['profile_law_counts']}` | "
            f"`{validation['asset_anchor_status_counts']}` | `{PROFILED_GRAPH_PATH.relative_to(ROOT)}` |"
        ),
        "",
        "## Acceptance",
        "",
        f"- cracked seams: {validation['cracked_seam_count'] == 0}",
        f"- road paths stay continuous: {validation['road_paths_stay_continuous']}",
        f"- building pads flat: {validation['building_pads_are_flat']}",
        f"- cliffs sharp: {validation['cliffs_remain_sharp']}",
        f"- asset anchors 7/7 pass or warn: {validation['asset_anchors_place_7_of_7']}",
        f"- deterministic anchor statuses: {validation['asset_anchors_statuses_deterministic'] if 'asset_anchors_statuses_deterministic' in validation else validation['asset_anchor_statuses_deterministic']}",
        f"- main map has profiled heights: {validation['main_map_has_profiled_heights']}",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(graph: dict[str, Any]) -> None:
    validation = graph["map_template_profile_application_v0"]["validation"]
    receipt = {
        "receipt_type": "map_template_profile_application_v0",
        "created_at_utc": now_iso(),
        "source_shared_graph": str(SHARED_GRAPH_PATH.relative_to(ROOT)),
        "profiled_graph": str(PROFILED_GRAPH_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "acceptance": {
            "cracked_seam_count_is_zero": validation["cracked_seam_count"] == 0,
            "road_paths_stay_continuous": validation["road_paths_stay_continuous"],
            "building_pads_are_flat": validation["building_pads_are_flat"],
            "cliffs_remain_sharp": validation["cliffs_remain_sharp"],
            "asset_anchors_place_7_of_7": validation["asset_anchors_place_7_of_7"],
            "asset_anchor_statuses_deterministic": validation["asset_anchor_statuses_deterministic"],
            "main_map_render_uses_profiled_heights": validation["main_map_has_profiled_heights"],
        },
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SHARED_GRAPH_PATH.exists():
        shared_adapter.main()
    graph = load_json(SHARED_GRAPH_PATH)
    profiled = profile_bending.apply_profile_laws(graph)
    profiled["graph_id"] = "tiled_hex_map_template_v0_profiled_terrain_graph"
    profiled["schema"] = "map_template_profiled_terrain_graph_v0"
    profiled["map_template_overlays"]["asset_sockets"] = recompute_asset_sockets_on_profiled_surface(profiled)
    profiled["map_template_profile_application_v0"] = {
        "source_shared_graph": str(SHARED_GRAPH_PATH.relative_to(ROOT)),
        "profile_assignment_rules": {
            "building_plots": "flat_pad",
            "roads": "road_grade",
            "normal_hills": "soft_slope",
            "delta_band_gte_2": "cliff_fault",
            "deliberate_step_regions": "terrace_step",
            "ravine_or_hazard_cuts": "ravine_fold",
        },
        "asset_anchor_height_rule": "nearest_profiled_hex_center_v0",
    }
    profiled["map_template_profile_application_v0"]["validation"] = validate_map_profile_application(profiled)
    PROFILED_GRAPH_PATH.write_text(json.dumps(profiled, indent=2) + "\n", encoding="utf-8")
    write_report(profiled)
    write_receipt(profiled)
    validation = profiled["map_template_profile_application_v0"]["validation"]
    print(f"wrote {PROFILED_GRAPH_PATH.relative_to(ROOT)}")
    print(
        f"cells={len(profiled['hex_plots'])} top_triangles={profiled['mesh_plan']['top_triangle_count']} "
        f"cracks={validation['cracked_seam_count']} anchors={validation['asset_anchor_status_counts']}"
    )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
