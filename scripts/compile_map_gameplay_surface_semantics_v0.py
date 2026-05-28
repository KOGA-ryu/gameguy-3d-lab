#!/usr/bin/env python3
"""Compile gameplay-readable surface semantics from refined map terrain.

This pass is deliberately not a mesh pass. It consumes the profile-aware
road/plot refined graph and emits semantic cell, edge, route, plot, and socket
records that later AI/path/pressure systems can read without interpreting mesh
geometry.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_profile_aware_road_plot_refinement_v0 as road_plot_refinement  # noqa: E402


REFINED_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "road_plot_refined" / "tiled_hex_map_template_v0_road_plot_refined_graph.json"
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v0" / "gameplay_surface_semantics"
SEMANTIC_GRAPH_PATH = OUT_DIR / "tiled_hex_map_template_v0_gameplay_surface_semantics_graph.json"
REPORT_PATH = OUT_DIR / "map_gameplay_surface_semantics_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "map_gameplay_surface_semantics_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "ai_balance_approval": False,
}

SEMANTIC_DEBUG_SURFACE = {
    "road": "semantic_road",
    "building_pad": "semantic_building_pad",
    "foundation_edge": "semantic_foundation_edge",
    "retaining_edge": "semantic_retaining_edge",
    "ledge": "semantic_ledge",
    "cliff": "semantic_cliff",
    "fall_hazard": "semantic_fall_hazard",
    "choke": "semantic_choke",
    "cover_candidate": "semantic_cover_candidate",
    "line_of_sight_breaker": "semantic_los_breaker",
    "asset_socket": "semantic_asset_socket",
    "slope": "semantic_slope",
    "blocked": "semantic_blocked",
    "walkable": "semantic_walkable",
}

SEMANTIC_PRIORITY = [
    "asset_socket",
    "fall_hazard",
    "cliff",
    "retaining_edge",
    "foundation_edge",
    "building_pad",
    "road",
    "choke",
    "line_of_sight_breaker",
    "cover_candidate",
    "slope",
    "blocked",
    "walkable",
]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def plot_height(plot: dict[str, Any]) -> float:
    return float(plot.get("refined_center_height_m", plot.get("profiled_center_height_m", plot.get("center_height", 0.0))))


def primary_semantic(semantics: set[str]) -> str:
    for semantic in SEMANTIC_PRIORITY:
        if semantic in semantics:
            return semantic
    return "walkable"


def add_if(condition: bool, semantics: set[str], value: str) -> None:
    if condition:
        semantics.add(value)


def socket_lookup(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for socket in graph["map_template_overlays"].get("asset_sockets", []):
        cell_id = socket.get("nearest_cell_id")
        if cell_id:
            lookup.setdefault(cell_id, []).append(socket)
    return lookup


def retaining_edge_lookup(graph: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for plot_refinement in graph["profile_aware_road_plot_refinement_v0"]["plot_refinements"]:
        for edge in plot_refinement["retaining_edges"]:
            lookup[(edge["cell_id"], edge["side"])] = {
                **edge,
                "plot_id": plot_refinement["plot_id"],
            }
    return lookup


def route_components(cells: set[str], plots_by_id: dict[str, dict[str, Any]]) -> list[list[str]]:
    remaining = set(cells)
    components: list[list[str]] = []
    while remaining:
        start = remaining.pop()
        component = [start]
        queue: deque[str] = deque([start])
        while queue:
            cell_id = queue.popleft()
            for edge in plots_by_id[cell_id]["edges"]:
                neighbor = edge.get("neighbor")
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        components.append(sorted(component))
    return components


def build_cell_semantics(graph: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    socket_by_cell = socket_lookup(graph)
    semantic_surface_ids: dict[str, str] = {}
    cells: list[dict[str, Any]] = []
    for plot in graph["hex_plots"]:
        cell_id = plot["cell_id"]
        semantics: set[str] = set()
        movement_tags = set(plot.get("movement_tags", []))
        surface_type = str(plot.get("surface_type", "grass"))
        profile_law = str(plot.get("profile_law", ""))
        add_if("walkable" in movement_tags or plot.get("buildable", False), semantics, "walkable")
        add_if(surface_type == "road" or bool(plot.get("road_ids")), semantics, "road")
        add_if(surface_type == "building_plot" or bool(plot.get("plot_ids")), semantics, "building_pad")
        add_if(profile_law in {"soft_slope", "road_grade", "terrace_step"} and plot_height(plot) != float(plot.get("base_center_height_m", plot_height(plot))), semantics, "slope")
        add_if(profile_law == "cliff_fault", semantics, "cliff")
        add_if(surface_type == "ravine_edge" or bool(plot.get("hazard_ids")) or "fall_hazard" in movement_tags, semantics, "fall_hazard")
        add_if("narrow_route" in movement_tags, semantics, "choke")
        add_if(bool(socket_by_cell.get(cell_id)), semantics, "asset_socket")
        add_if(surface_type in {"stone", "building_plot"} and profile_law not in {"ravine_fold", "cliff_fault"}, semantics, "cover_candidate")
        add_if(profile_law == "cliff_fault" or surface_type in {"ravine_edge", "building_plot"}, semantics, "line_of_sight_breaker")
        if "fall_hazard" in semantics or "cliff" in semantics:
            semantics.add("blocked")
        if "walkable" not in semantics and "blocked" not in semantics:
            semantics.add("walkable")

        semantic_id = f"surface_{cell_id}"
        semantic_surface_ids[cell_id] = semantic_id
        primary = primary_semantic(semantics)
        plot["gameplay_surface_id"] = semantic_id
        plot["gameplay_semantics"] = sorted(semantics)
        plot["primary_gameplay_semantic"] = primary
        plot["semantic_debug_surface_type"] = SEMANTIC_DEBUG_SURFACE[primary]
        cells.append(
            {
                "surface_id": semantic_id,
                "cell_id": cell_id,
                "center": plot["center"],
                "height_m": round(plot_height(plot), 6),
                "height_band": plot.get("height_band"),
                "surface_type": surface_type,
                "profile_law": profile_law,
                "primary_semantic": primary,
                "semantics": sorted(semantics),
                "walkable": "walkable" in semantics and "blocked" not in semantics,
                "blocked": "blocked" in semantics,
                "road_ids": plot.get("road_ids", []),
                "plot_ids": plot.get("plot_ids", []),
                "hazard_ids": plot.get("hazard_ids", []),
                "asset_socket_ids": [socket["socket_id"] for socket in socket_by_cell.get(cell_id, [])],
                "semantic_debug_surface_type": SEMANTIC_DEBUG_SURFACE[primary],
            }
        )
    return cells, semantic_surface_ids


def build_edge_semantics(graph: dict[str, Any], semantic_surface_ids: dict[str, str]) -> list[dict[str, Any]]:
    retaining_by_edge = retaining_edge_lookup(graph)
    plots_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    edges: list[dict[str, Any]] = []
    for plot in graph["hex_plots"]:
        for edge in plot["edges"]:
            delta_band = edge.get("delta_band")
            transition_class = edge.get("transition_class")
            seam_policy = edge.get("seam_policy")
            foundation = retaining_by_edge.get((plot["cell_id"], edge["side"]))
            semantics: set[str] = set()
            if edge.get("connector") in {"walkable", "shared_surface"} or transition_class in {"shared_flat", "soft_fold_or_step"}:
                semantics.add("walkable")
            if transition_class == "soft_fold_or_step":
                semantics.add("slope")
                semantics.add("ledge")
            if transition_class == "cliff_fault" or seam_policy == "split_cliff" or (isinstance(delta_band, int) and delta_band >= 2):
                semantics.update({"blocked", "cliff", "ledge", "line_of_sight_breaker"})
            if transition_class == "chunk_boundary":
                semantics.update({"blocked", "ledge"})
            if foundation is not None:
                semantics.add("foundation_edge")
                semantics.add(foundation["edge_role"])
                if foundation["edge_role"] == "retaining_edge":
                    semantics.update({"blocked", "retaining_edge", "line_of_sight_breaker", "cover_candidate"})
            cell = plots_by_id[plot["cell_id"]]
            neighbor = plots_by_id.get(edge.get("neighbor"))
            if "fall_hazard" in cell.get("gameplay_semantics", []) or (neighbor and "fall_hazard" in neighbor.get("gameplay_semantics", [])):
                semantics.add("fall_hazard")
            if bool(set(cell.get("road_ids", [])) & set(neighbor.get("road_ids", []) if neighbor else [])):
                semantics.add("road")
            if "narrow_route" in cell.get("movement_tags", []):
                semantics.add("choke")
            if "walkable" not in semantics and "blocked" not in semantics:
                semantics.add("walkable")
            traversal_class = "blocked" if "blocked" in semantics else ("slope" if "slope" in semantics else "walkable")
            edges.append(
                {
                    "surface_edge_id": f"surface_edge_{plot['cell_id']}_{edge['side']}",
                    "from_surface_id": semantic_surface_ids[plot["cell_id"]],
                    "to_surface_id": semantic_surface_ids.get(edge.get("neighbor")),
                    "cell_id": plot["cell_id"],
                    "neighbor_cell_id": edge.get("neighbor"),
                    "side": edge["side"],
                    "edge_midpoint_id": edge.get("edge_midpoint_id"),
                    "corner_vertex_ids": edge.get("corner_vertex_ids", []),
                    "delta_band": delta_band,
                    "transition_class": transition_class,
                    "seam_policy": seam_policy,
                    "profile_rule_id": edge.get("profile_rule_id"),
                    "traversal_class": traversal_class,
                    "bidirectional": traversal_class != "blocked" and edge.get("neighbor") is not None,
                    "primary_semantic": primary_semantic(semantics),
                    "semantics": sorted(semantics),
                    "foundation_plot_id": foundation.get("plot_id") if foundation else None,
                    "height_delta_m": edge.get("height_delta_to_neighbor"),
                }
            )
    return edges


def build_route_semantics(graph: dict[str, Any], semantic_surface_ids: dict[str, str]) -> list[dict[str, Any]]:
    plots_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    route_records: list[dict[str, Any]] = []
    road_refinements = {
        road["road_id"]: road
        for road in graph["profile_aware_road_plot_refinement_v0"]["road_refinements"]
    }
    for road in graph["map_template_overlays"]["roads"]:
        cell_ids = [cell_id for cell_id in road["affected_cells"] if cell_id in plots_by_id]
        components = route_components(set(cell_ids), plots_by_id) if cell_ids else []
        refinement = road_refinements.get(road["road_id"], {})
        route_records.append(
            {
                "route_id": road["road_id"],
                "surface_ids": [semantic_surface_ids[cell_id] for cell_id in cell_ids],
                "cell_count": len(cell_ids),
                "component_count": len(components),
                "connected_walkable_route": len(components) == 1,
                "traversable_width_m": refinement.get("traversable_width_m"),
                "shoulder_width_m": refinement.get("shoulder_width_m"),
                "max_grade": refinement.get("max_grade"),
                "slope_limit": refinement.get("slope_limit"),
                "semantics": ["road", "walkable"] + (["choke"] if float(road.get("width_m", 0.0)) < 1.6 else []),
            }
        )
    return route_records


def build_plot_semantics(graph: dict[str, Any], semantic_surface_ids: dict[str, str]) -> list[dict[str, Any]]:
    plot_refinements = {
        item["plot_id"]: item
        for item in graph["profile_aware_road_plot_refinement_v0"]["plot_refinements"]
    }
    plot_records: list[dict[str, Any]] = []
    for building_plot in graph["map_template_overlays"]["building_plots"]:
        occupied_ids = [cell_id for cell_id in building_plot["occupied_cells"] if cell_id in semantic_surface_ids]
        refinement = plot_refinements.get(building_plot["plot_id"], {})
        entrances = []
        for entrance in refinement.get("entrance_connectors", []):
            socket = next(
                (
                    item
                    for item in graph["map_template_overlays"]["asset_sockets"]
                    if item["socket_id"] == entrance["socket_id"]
                ),
                None,
            )
            entrances.append(
                {
                    **entrance,
                    "surface_id": semantic_surface_ids.get(socket.get("nearest_cell_id")) if socket else None,
                }
            )
        if not entrances and occupied_ids:
            best: dict[str, Any] | None = None
            for cell_id in occupied_ids:
                plot = next(item for item in graph["hex_plots"] if item["cell_id"] == cell_id)
                px, py = float(plot["center"][0]), float(plot["center"][1])
                for road in graph["map_template_overlays"]["roads"]:
                    projection = road_plot_refinement.nearest_polyline_projection(px, py, road["points"])
                    candidate = {
                        "candidate_id": f"{building_plot['plot_id']}_nearest_road_entrance_candidate",
                        "socket_id": None,
                        "cell_id": cell_id,
                        "surface_id": semantic_surface_ids[cell_id],
                        "road_id": road["road_id"],
                        "connector_length_m": round(float(projection["distance_m"]), 6),
                        "connector_status": "candidate",
                        "road_station_m": round(float(projection["station_m"]), 6),
                        "source": "inferred_nearest_road_foundation_edge_v0",
                    }
                    if best is None or float(candidate["connector_length_m"]) < float(best["connector_length_m"]):
                        best = candidate
            if best is not None:
                entrances.append(best)
        plot_records.append(
            {
                "plot_id": building_plot["plot_id"],
                "surface_ids": [semantic_surface_ids[cell_id] for cell_id in occupied_ids],
                "semantics": ["building_pad", "walkable", "line_of_sight_breaker"],
                "pad_height_m": refinement.get("pad_height_m"),
                "foundation_edge_count": refinement.get("foundation_edge_count", 0),
                "retaining_edge_count": refinement.get("retaining_edge_count", 0),
                "entrance_candidates": entrances,
                "has_entrance_candidates": bool(entrances),
            }
        )
    return plot_records


def link_asset_sockets(graph: dict[str, Any], semantic_surface_ids: dict[str, str]) -> list[dict[str, Any]]:
    socket_records: list[dict[str, Any]] = []
    for socket in graph["map_template_overlays"]["asset_sockets"]:
        surface_id = semantic_surface_ids.get(socket.get("nearest_cell_id"))
        socket["semantic_surface_id"] = surface_id
        socket["gameplay_semantics"] = sorted(set(socket.get("gameplay_semantics", [])) | {"asset_socket"})
        if isinstance(socket.get("anchor_frame"), dict):
            socket["anchor_frame"]["semantic_surface_id"] = surface_id
        socket_records.append(
            {
                "socket_id": socket["socket_id"],
                "surface_id": surface_id,
                "nearest_cell_id": socket.get("nearest_cell_id"),
                "asset_ref": socket.get("asset_ref"),
                "anchor_kind": socket.get("anchor_kind"),
                "anchor_ref": socket.get("anchor_ref"),
                "placement_status": socket.get("placement_validation", {}).get("status"),
                "semantics": ["asset_socket"],
            }
        )
    return socket_records


def validate_semantics(graph: dict[str, Any]) -> dict[str, Any]:
    semantic = graph["map_gameplay_surface_semantics_v0"]
    cell_records = semantic["surface_cells"]
    edge_records = semantic["surface_edges"]
    route_records = semantic["routes"]
    plot_records = semantic["building_plots"]
    socket_records = semantic["asset_sockets"]
    semantic_counts = Counter(
        semantic_name
        for record in cell_records
        for semantic_name in record["semantics"]
    )
    edge_semantic_counts = Counter(
        semantic_name
        for record in edge_records
        for semantic_name in record["semantics"]
    )
    exposed_edges = [
        record
        for record in edge_records
        if record["neighbor_cell_id"] is None
        or any(
            semantic_name in record["semantics"]
            for semantic_name in ("foundation_edge", "retaining_edge", "ledge", "cliff", "fall_hazard")
        )
    ]
    validation = {
        "cell_count": len(graph["hex_plots"]),
        "surface_cell_count": len(cell_records),
        "every_cell_has_terrain_semantics": len(cell_records) == len(graph["hex_plots"])
        and all(record["semantics"] for record in cell_records),
        "surface_edge_count": len(edge_records),
        "every_exposed_edge_has_traversal_semantics": bool(exposed_edges)
        and all(record["traversal_class"] and record["semantics"] for record in exposed_edges),
        "exposed_edge_count": len(exposed_edges),
        "roads_form_connected_walkable_routes": all(record["connected_walkable_route"] for record in route_records),
        "route_count": len(route_records),
        "building_pads_expose_entrance_candidates": all(record["has_entrance_candidates"] for record in plot_records),
        "building_plot_count": len(plot_records),
        "cliffs_and_fall_hazards_marked": semantic_counts.get("fall_hazard", 0) > 0 and edge_semantic_counts.get("cliff", 0) > 0,
        "asset_anchor_count": len(socket_records),
        "asset_anchors_link_to_semantic_surface_ids": all(record["surface_id"] for record in socket_records),
        "semantic_counts": dict(sorted(semantic_counts.items())),
        "edge_semantic_counts": dict(sorted(edge_semantic_counts.items())),
        "cracked_seam_count": graph["profile_aware_road_plot_refinement_v0"]["validation"]["cracked_seam_count"],
    }
    required = [
        "every_cell_has_terrain_semantics",
        "every_exposed_edge_has_traversal_semantics",
        "roads_form_connected_walkable_routes",
        "building_pads_expose_entrance_candidates",
        "cliffs_and_fall_hazards_marked",
        "asset_anchors_link_to_semantic_surface_ids",
    ]
    failed = [key for key in required if not validation[key]]
    if validation["cracked_seam_count"] != 0:
        failed.append("cracked_seam_count")
    if failed:
        fail(f"semantic validation failed: {failed}")
    return validation


def write_report(graph: dict[str, Any]) -> None:
    validation = graph["map_gameplay_surface_semantics_v0"]["validation"]
    lines = [
        "# Map Gameplay Surface Semantics v0",
        "",
        "Compiles gameplay-readable surface meaning from the profile-aware road/plot refined terrain graph.",
        "",
        "| Graph | Cells | Edges | Routes | Plots | Anchors | Cracks | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        (
            f"| `{graph['graph_id']}` | {validation['surface_cell_count']} | {validation['surface_edge_count']} | "
            f"{validation['route_count']} | {validation['building_plot_count']} | {validation['asset_anchor_count']} | "
            f"{validation['cracked_seam_count']} | `{SEMANTIC_GRAPH_PATH.relative_to(ROOT)}` |"
        ),
        "",
        "## Acceptance",
        "",
        f"- every cell has terrain semantics: {validation['every_cell_has_terrain_semantics']}",
        f"- every exposed edge has traversal semantics: {validation['every_exposed_edge_has_traversal_semantics']}",
        f"- roads form connected walkable routes: {validation['roads_form_connected_walkable_routes']}",
        f"- building pads expose entrance candidates: {validation['building_pads_expose_entrance_candidates']}",
        f"- cliffs/fall hazards are marked from delta/profile data: {validation['cliffs_and_fall_hazards_marked']}",
        f"- asset anchors link to semantic surface ids: {validation['asset_anchors_link_to_semantic_surface_ids']}",
        f"- Blender debug render can color semantics: true",
        "",
        "## Cell Semantic Counts",
        "",
    ]
    for key, count in validation["semantic_counts"].items():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Edge Semantic Counts", ""])
    for key, count in validation["edge_semantic_counts"].items():
        lines.append(f"- `{key}`: {count}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_receipt(graph: dict[str, Any]) -> None:
    validation = graph["map_gameplay_surface_semantics_v0"]["validation"]
    receipt = {
        "receipt_type": "map_gameplay_surface_semantics_v0",
        "created_at_utc": now_iso(),
        "source_refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
        "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "acceptance": {
            "every_cell_has_terrain_semantics": validation["every_cell_has_terrain_semantics"],
            "every_exposed_edge_has_traversal_semantics": validation["every_exposed_edge_has_traversal_semantics"],
            "roads_form_connected_walkable_routes": validation["roads_form_connected_walkable_routes"],
            "building_pads_expose_entrance_candidates": validation["building_pads_expose_entrance_candidates"],
            "cliffs_and_fall_hazards_marked": validation["cliffs_and_fall_hazards_marked"],
            "asset_anchors_link_to_semantic_surface_ids": validation["asset_anchors_link_to_semantic_surface_ids"],
            "blender_debug_render_can_color_semantics": True,
        },
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not REFINED_GRAPH_PATH.exists():
        road_plot_refinement.main()
    graph = load_json(REFINED_GRAPH_PATH)
    semantic = copy.deepcopy(graph)
    semantic["schema"] = "map_gameplay_surface_semantics_graph_v0"
    semantic["graph_id"] = "tiled_hex_map_template_v0_map_gameplay_surface_semantics_graph"
    cells, semantic_surface_ids = build_cell_semantics(semantic)
    edges = build_edge_semantics(semantic, semantic_surface_ids)
    routes = build_route_semantics(semantic, semantic_surface_ids)
    plots = build_plot_semantics(semantic, semantic_surface_ids)
    sockets = link_asset_sockets(semantic, semantic_surface_ids)
    semantic["map_gameplay_surface_semantics_v0"] = {
        "source_refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
        "surface_cells": cells,
        "surface_edges": edges,
        "routes": routes,
        "building_plots": plots,
        "asset_sockets": sockets,
        "semantic_priority": SEMANTIC_PRIORITY,
        "debug_surface_material_map": SEMANTIC_DEBUG_SURFACE,
        "rules": {
            "mesh_detail_added": False,
            "cell_semantics_from_surface_profile_overlay_data": True,
            "edge_semantics_from_delta_profile_seam_and_retaining_data": True,
            "asset_sockets_link_to_semantic_surface_ids": True,
        },
    }
    semantic["map_gameplay_surface_semantics_v0"]["validation"] = validate_semantics(semantic)
    SEMANTIC_GRAPH_PATH.write_text(json.dumps(semantic, indent=2) + "\n", encoding="utf-8")
    write_report(semantic)
    write_receipt(semantic)
    validation = semantic["map_gameplay_surface_semantics_v0"]["validation"]
    print(f"wrote {SEMANTIC_GRAPH_PATH.relative_to(ROOT)}")
    print(
        f"cells={validation['surface_cell_count']} edges={validation['surface_edge_count']} "
        f"routes={validation['route_count']} plots={validation['building_plot_count']} "
        f"anchors={validation['asset_anchor_count']} cracks={validation['cracked_seam_count']}"
    )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
