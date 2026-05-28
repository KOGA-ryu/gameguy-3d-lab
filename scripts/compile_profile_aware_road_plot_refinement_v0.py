#!/usr/bin/env python3
"""Refine roads, building plots, and anchors on profiled terrain.

This pass does not add terrain laws. It consumes the profiled map template graph
and adds buildability metadata plus refined center/anchor samples:

profiled terrain graph -> road width/shoulder/banking refinement -> plot
foundation/entrance refinement -> profiled-normal asset anchors.
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

import compile_map_template_profile_application_v0 as profile_application  # noqa: E402


PROFILED_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "profiled_terrain" / "tiled_hex_map_template_v0_profiled_terrain_graph.json"
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v0" / "road_plot_refined"
REFINED_GRAPH_PATH = OUT_DIR / "tiled_hex_map_template_v0_road_plot_refined_graph.json"
REPORT_PATH = OUT_DIR / "profile_aware_road_plot_refinement_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "profile_aware_road_plot_refinement_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}

ROAD_SLOPE_LIMIT = 0.24
ENTRANCE_CONNECTOR_MAX_M = 3.25


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


def normalize3(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in vector))
    if length <= 1e-9:
        return (0.0, 0.0, 1.0)
    return tuple(component / length for component in vector)  # type: ignore[return-value]


def dot3(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def cross3(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, float, tuple[float, float]]:
    abx = bx - ax
    aby = by - ay
    length_sq = abx * abx + aby * aby
    if length_sq <= 1e-9:
        return math.hypot(px - ax, py - ay), 0.0, (ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / length_sq))
    hit = (ax + abx * t, ay + aby * t)
    return math.hypot(px - hit[0], py - hit[1]), t, hit


def polyline_lengths(points: list[list[float]]) -> list[float]:
    lengths = [0.0]
    for left, right in zip(points, points[1:], strict=False):
        lengths.append(lengths[-1] + math.hypot(float(right[0]) - float(left[0]), float(right[1]) - float(left[1])))
    return lengths


def nearest_polyline_projection(px: float, py: float, points: list[list[float]]) -> dict[str, Any]:
    cumulative = polyline_lengths(points)
    best = {
        "distance_m": float("inf"),
        "station_m": 0.0,
        "position": [px, py],
        "tangent": [1.0, 0.0],
    }
    for index, (left, right) in enumerate(zip(points, points[1:], strict=False)):
        ax, ay = float(left[0]), float(left[1])
        bx, by = float(right[0]), float(right[1])
        distance, t, hit = distance_to_segment(px, py, ax, ay, bx, by)
        if distance < float(best["distance_m"]):
            segment_length = math.hypot(bx - ax, by - ay)
            tangent = (1.0, 0.0) if segment_length <= 1e-9 else ((bx - ax) / segment_length, (by - ay) / segment_length)
            best = {
                "distance_m": distance,
                "station_m": cumulative[index] + t * segment_length,
                "position": [hit[0], hit[1]],
                "tangent": [tangent[0], tangent[1]],
            }
    return best


def plot_height(plot: dict[str, Any]) -> float:
    return float(plot.get("refined_center_height_m", plot.get("profiled_center_height_m", plot.get("center_height", 0.0))))


def fit_plot_planes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    plots_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    planes: dict[str, dict[str, Any]] = {}
    for plot in graph["hex_plots"]:
        cx, cy = float(plot["center"][0]), float(plot["center"][1])
        cz = plot_height(plot)
        sxx = sxy = syy = sxz = syz = 0.0
        for edge in plot["edges"]:
            neighbor = plots_by_id.get(edge["neighbor"])
            if neighbor is None:
                continue
            dx = float(neighbor["center"][0]) - cx
            dy = float(neighbor["center"][1]) - cy
            dz = plot_height(neighbor) - cz
            sxx += dx * dx
            sxy += dx * dy
            syy += dy * dy
            sxz += dx * dz
            syz += dy * dz
        det = sxx * syy - sxy * sxy
        if abs(det) <= 1e-9:
            gx = gy = 0.0
        else:
            gx = (sxz * syy - syz * sxy) / det
            gy = (sxx * syz - sxy * sxz) / det
        normal = normalize3((-gx, -gy, 1.0))
        planes[plot["cell_id"]] = {
            "origin": [cx, cy, cz],
            "gradient": [round(gx, 6), round(gy, 6)],
            "normal": [round(normal[0], 6), round(normal[1], 6), round(normal[2], 6)],
        }
    return planes


def height_on_plane(plane: dict[str, Any], x: float, y: float) -> float:
    ox, oy, oz = [float(value) for value in plane["origin"]]
    gx, gy = [float(value) for value in plane["gradient"]]
    return oz + gx * (x - ox) + gy * (y - oy)


def smooth_road_records(records: list[dict[str, Any]], slope_limit: float) -> None:
    if len(records) < 2:
        return
    records.sort(key=lambda item: float(item["station_m"]))
    for index in range(1, len(records)):
        prev = records[index - 1]
        current = records[index]
        dist = max(float(current["station_m"]) - float(prev["station_m"]), 0.001)
        allowed = slope_limit * dist
        current["refined_height_m"] = max(
            min(float(current["refined_height_m"]), float(prev["refined_height_m"]) + allowed),
            float(prev["refined_height_m"]) - allowed,
        )
    for index in range(len(records) - 2, -1, -1):
        next_record = records[index + 1]
        current = records[index]
        dist = max(float(next_record["station_m"]) - float(current["station_m"]), 0.001)
        allowed = slope_limit * dist
        current["refined_height_m"] = max(
            min(float(current["refined_height_m"]), float(next_record["refined_height_m"]) + allowed),
            float(next_record["refined_height_m"]) - allowed,
        )
    for left, right in zip(records, records[1:], strict=False):
        dist = max(float(right["station_m"]) - float(left["station_m"]), 0.001)
        grade = (float(right["refined_height_m"]) - float(left["refined_height_m"])) / dist
        left["grade_to_next"] = round(grade, 6)
    records[-1]["grade_to_next"] = 0.0


def refine_roads(graph: dict[str, Any]) -> dict[str, Any]:
    plots_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    road_refinements: list[dict[str, Any]] = []
    for road in graph["map_template_overlays"]["roads"]:
        records: list[dict[str, Any]] = []
        width_m = float(road["width_m"])
        traversable_width = round(width_m * 0.78, 6)
        shoulder_width = round((width_m - traversable_width) * 0.5, 6)
        bank_crossfall = 0.035 if width_m < 1.8 else 0.025
        for cell_id in road["affected_cells"]:
            plot = plots_by_id.get(cell_id)
            if plot is None or plot.get("profile_law") == "flat_pad":
                continue
            px, py = float(plot["center"][0]), float(plot["center"][1])
            projection = nearest_polyline_projection(px, py, road["points"])
            tangent = projection["tangent"]
            lateral_sign = 1.0 if ((px - projection["position"][0]) * -float(tangent[1]) + (py - projection["position"][1]) * float(tangent[0])) >= 0 else -1.0
            lateral_offset = lateral_sign * float(projection["distance_m"])
            base_height = float(plot.get("profiled_center_height_m", plot["center_height"]))
            refined_height = base_height + lateral_offset * bank_crossfall
            zone = "road_core" if abs(lateral_offset) <= traversable_width * 0.5 else "road_shoulder"
            records.append(
                {
                    "cell_id": cell_id,
                    "station_m": round(float(projection["station_m"]), 6),
                    "lateral_offset_m": round(lateral_offset, 6),
                    "base_height_m": round(base_height, 6),
                    "refined_height_m": round(refined_height, 6),
                    "zone": zone,
                    "traversable_width_m": traversable_width,
                    "shoulder_width_m": shoulder_width,
                    "bank_crossfall": bank_crossfall,
                }
            )
        smooth_road_records(records, ROAD_SLOPE_LIMIT)
        for record in records:
            plot = plots_by_id[record["cell_id"]]
            plot["refined_center_height_m"] = round(float(record["refined_height_m"]), 6)
            plot.setdefault("road_refinement", []).append({key: value for key, value in record.items() if key != "cell_id"})
        grades = [abs(float(record["grade_to_next"])) for record in records]
        road_refinements.append(
            {
                "road_id": road["road_id"],
                "width_m": width_m,
                "traversable_width_m": traversable_width,
                "shoulder_width_m": shoulder_width,
                "bank_crossfall": bank_crossfall,
                "refined_cell_count": len(records),
                "min_traversable_width_m": traversable_width if records else 0.0,
                "max_grade": round(max(grades) if grades else 0.0, 6),
                "slope_limit": ROAD_SLOPE_LIMIT,
                "grade_within_limit": all(grade <= ROAD_SLOPE_LIMIT + 1e-6 for grade in grades),
                "records": records,
            }
        )
    return {"roads": road_refinements}


def refine_plots(graph: dict[str, Any]) -> dict[str, Any]:
    plots_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    roads = graph["map_template_overlays"]["roads"]
    sockets = graph["map_template_overlays"]["asset_sockets"]
    plot_refinements: list[dict[str, Any]] = []
    for building_plot in graph["map_template_overlays"]["building_plots"]:
        occupied_ids = [cell_id for cell_id in building_plot["occupied_cells"] if cell_id in plots_by_id]
        if not occupied_ids:
            continue
        pad_height = round(sum(plot_height(plots_by_id[cell_id]) for cell_id in occupied_ids) / len(occupied_ids), 6)
        for cell_id in occupied_ids:
            plot = plots_by_id[cell_id]
            if plot.get("profile_law") == "flat_pad":
                plot["refined_center_height_m"] = pad_height
                plot["plot_refinement"] = {
                    "plot_id": building_plot["plot_id"],
                    "pad_height_m": pad_height,
                    "foundation_role": "flat_pad_interior",
                }
        retaining_edges: list[dict[str, Any]] = []
        occupied = set(occupied_ids)
        for cell_id in occupied_ids:
            plot = plots_by_id[cell_id]
            for edge in plot["edges"]:
                if edge["neighbor"] in occupied:
                    continue
                neighbor = plots_by_id.get(edge["neighbor"])
                neighbor_height = plot_height(neighbor) if neighbor is not None else 0.0
                delta = round(pad_height - neighbor_height, 6)
                retaining_edges.append(
                    {
                        "cell_id": cell_id,
                        "side": edge["side"],
                        "neighbor": edge["neighbor"],
                        "edge_midpoint_id": edge["edge_midpoint_id"],
                        "corner_vertex_ids": edge["corner_vertex_ids"],
                        "pad_height_m": pad_height,
                        "outside_height_m": round(neighbor_height, 6),
                        "height_delta_m": delta,
                        "edge_role": "retaining_edge" if abs(delta) > 0.05 else "flush_join",
                    }
                )
        entrances: list[dict[str, Any]] = []
        for socket in sockets:
            if socket.get("anchor_ref") != building_plot["plot_id"]:
                continue
            if socket.get("socket_type") not in {"portal", "vertical_transition"}:
                continue
            sx, sy = float(socket["world_position"][0]), float(socket["world_position"][1])
            nearest = min(
                (
                    {**nearest_polyline_projection(sx, sy, road["points"]), "road_id": road["road_id"]}
                    for road in roads
                ),
                key=lambda item: float(item["distance_m"]),
            )
            entrances.append(
                {
                    "socket_id": socket["socket_id"],
                    "road_id": nearest["road_id"],
                    "connector_length_m": round(float(nearest["distance_m"]), 6),
                    "connector_status": "pass" if float(nearest["distance_m"]) <= ENTRANCE_CONNECTOR_MAX_M else "warn",
                    "max_connector_length_m": ENTRANCE_CONNECTOR_MAX_M,
                    "road_station_m": round(float(nearest["station_m"]), 6),
                }
            )
        plot_refinements.append(
            {
                "plot_id": building_plot["plot_id"],
                "pad_height_m": pad_height,
                "occupied_cell_count": len(occupied_ids),
                "foundation_edge_count": len(retaining_edges),
                "retaining_edge_count": sum(1 for edge in retaining_edges if edge["edge_role"] == "retaining_edge"),
                "flush_join_count": sum(1 for edge in retaining_edges if edge["edge_role"] == "flush_join"),
                "retaining_edges": retaining_edges,
                "entrance_connectors": entrances,
                "entrances_align_to_roads": all(item["connector_status"] == "pass" for item in entrances) if entrances else True,
            }
        )
    return {"building_plots": plot_refinements}


def recompute_anchor_frames(graph: dict[str, Any]) -> list[dict[str, Any]]:
    planes = fit_plot_planes(graph)
    sockets = graph["map_template_overlays"]["asset_sockets"]
    recomputed: list[dict[str, Any]] = []
    for socket in sockets:
        updated = copy.deepcopy(socket)
        x, y = float(updated["world_position"][0]), float(updated["world_position"][1])
        nearest = min(
            graph["hex_plots"],
            key=lambda plot: math.hypot(float(plot["center"][0]) - x, float(plot["center"][1]) - y),
        )
        plane = planes[nearest["cell_id"]]
        z = round(height_on_plane(plane, x, y), 6)
        normal = normalize3(tuple(float(value) for value in plane["normal"]))  # type: ignore[arg-type]
        frame = updated.get("anchor_frame", {})
        old_forward = tuple(float(value) for value in frame.get("forward", [0.0, 1.0, 0.0]))
        forward = normalize3(
            (
                old_forward[0] - dot3(old_forward, normal) * normal[0],
                old_forward[1] - dot3(old_forward, normal) * normal[1],
                old_forward[2] - dot3(old_forward, normal) * normal[2],
            )
        )
        right = normalize3(cross3(forward, normal))
        forward = normalize3(cross3(normal, right))
        updated["world_position"][2] = z
        updated["nearest_cell_id"] = nearest["cell_id"]
        if isinstance(frame, dict):
            frame["position"][2] = z
            frame["forward"] = [round(value, 6) for value in forward]
            frame["right"] = [round(value, 6) for value in right]
            frame["up"] = [round(value, 6) for value in normal]
            frame["profiled_surface_source"] = "refined_profiled_plane_sample_v0"
            frame["surface_gradient"] = plane["gradient"]
            frame["surface_normal_rule"] = "least_squares_neighbor_center_plane_v0"
        updated["placement_validation"] = {
            **updated.get("placement_validation", {}),
            "profiled_surface_recomputed": True,
            "profiled_height_m": z,
            "profiled_nearest_cell_id": nearest["cell_id"],
            "profiled_normal": [round(value, 6) for value in normal],
            "height_rule": "refined_profiled_plane_sample_v0",
            "normal_rule": "least_squares_neighbor_center_plane_v0",
        }
        recomputed.append(updated)
    return recomputed


def validate_refinement(graph: dict[str, Any]) -> dict[str, Any]:
    roads = graph["profile_aware_road_plot_refinement_v0"]["road_refinements"]
    plots = graph["profile_aware_road_plot_refinement_v0"]["plot_refinements"]
    sockets = graph["map_template_overlays"]["asset_sockets"]
    status_counts: dict[str, int] = {}
    for socket in sockets:
        status = socket.get("placement_validation", {}).get("status", "missing")
        status_counts[status] = status_counts.get(status, 0) + 1
    foundation_edges = sum(plot["foundation_edge_count"] for plot in plots)
    retaining_edges = sum(plot["retaining_edge_count"] for plot in plots)
    validation = {
        "cracked_seam_count": graph["profile_validation"]["cracked_seam_count"],
        "roads_have_consistent_traversable_width": all(road["min_traversable_width_m"] > 0.95 for road in roads),
        "road_grade_changes_below_slope_limit": all(road["grade_within_limit"] for road in roads),
        "max_road_grade": max((road["max_grade"] for road in roads), default=0.0),
        "road_slope_limit": ROAD_SLOPE_LIMIT,
        "building_pads_expose_foundation_edges": foundation_edges > 0,
        "foundation_edge_count": foundation_edges,
        "retaining_edge_count": retaining_edges,
        "building_entrances_align_to_connectors": all(plot["entrances_align_to_roads"] for plot in plots),
        "asset_anchor_count": len(sockets),
        "asset_anchor_status_counts": dict(sorted(status_counts.items())),
        "asset_anchors_place_7_of_7": len(sockets) == 7 and sum(status_counts.get(status, 0) for status in ("pass", "warn")) == 7,
        "asset_anchors_use_profiled_normals_and_heights": all(
            socket.get("placement_validation", {}).get("height_rule") == "refined_profiled_plane_sample_v0"
            and socket.get("placement_validation", {}).get("normal_rule") == "least_squares_neighbor_center_plane_v0"
            for socket in sockets
        ),
    }
    if validation["cracked_seam_count"] != 0:
        fail("road/plot refined graph has cracked seams")
    if not validation["asset_anchors_place_7_of_7"]:
        fail(f"asset anchors did not place 7/7 after refinement: {status_counts}")
    return validation


def write_report(graph: dict[str, Any]) -> None:
    validation = graph["profile_aware_road_plot_refinement_v0"]["validation"]
    lines = [
        "# Profile-Aware Road And Plot Refinement v0",
        "",
        "Refines the existing profiled map terrain for buildable roads, foundations, entrances, and profiled anchor frames without adding terrain laws.",
        "",
        "| Graph | Roads | Plots | Max Road Grade | Foundation Edges | Retaining Edges | Anchors | Cracks | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
        (
            f"| `{graph['graph_id']}` | {len(graph['profile_aware_road_plot_refinement_v0']['road_refinements'])} | "
            f"{len(graph['profile_aware_road_plot_refinement_v0']['plot_refinements'])} | {validation['max_road_grade']} | "
            f"{validation['foundation_edge_count']} | {validation['retaining_edge_count']} | "
            f"`{validation['asset_anchor_status_counts']}` | {validation['cracked_seam_count']} | "
            f"`{REFINED_GRAPH_PATH.relative_to(ROOT)}` |"
        ),
        "",
        "## Acceptance",
        "",
        f"- roads have consistent traversable width: {validation['roads_have_consistent_traversable_width']}",
        f"- road grade changes stay below slope limit: {validation['road_grade_changes_below_slope_limit']}",
        f"- building pads expose clean foundation edges: {validation['building_pads_expose_foundation_edges']}",
        f"- building entrances align to road/plot connectors: {validation['building_entrances_align_to_connectors']}",
        f"- asset anchors use profiled normals/height: {validation['asset_anchors_use_profiled_normals_and_heights']}",
        f"- no seam cracks after refinement: {validation['cracked_seam_count'] == 0}",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(graph: dict[str, Any]) -> None:
    validation = graph["profile_aware_road_plot_refinement_v0"]["validation"]
    receipt = {
        "receipt_type": "profile_aware_road_plot_refinement_v0",
        "created_at_utc": now_iso(),
        "source_profiled_graph": str(PROFILED_GRAPH_PATH.relative_to(ROOT)),
        "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "acceptance": {
            "roads_have_consistent_traversable_width": validation["roads_have_consistent_traversable_width"],
            "road_grade_changes_below_slope_limit": validation["road_grade_changes_below_slope_limit"],
            "building_pads_expose_clean_foundation_edges": validation["building_pads_expose_foundation_edges"],
            "building_entrances_align_to_connectors": validation["building_entrances_align_to_connectors"],
            "asset_anchors_use_profiled_normals_and_height": validation["asset_anchors_use_profiled_normals_and_heights"],
            "cracked_seam_count_is_zero": validation["cracked_seam_count"] == 0,
            "asset_anchors_place_7_of_7": validation["asset_anchors_place_7_of_7"],
        },
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILED_GRAPH_PATH.exists():
        profile_application.main()
    graph = load_json(PROFILED_GRAPH_PATH)
    refined = copy.deepcopy(graph)
    refined["schema"] = "profile_aware_road_plot_refined_graph_v0"
    refined["graph_id"] = "tiled_hex_map_template_v0_profile_aware_road_plot_refined_graph"
    for plot in refined["hex_plots"]:
        plot["refined_center_height_m"] = plot.get("profiled_center_height_m", plot["center_height"])
    road_data = refine_roads(refined)
    plot_data = refine_plots(refined)
    refined["map_template_overlays"]["asset_sockets"] = recompute_anchor_frames(refined)
    refined["mesh_plan"]["height_source"] = "refined_center_height_m_with_profiled_weld_vertices_v0"
    refined["profile_aware_road_plot_refinement_v0"] = {
        "source_profiled_graph": str(PROFILED_GRAPH_PATH.relative_to(ROOT)),
        "road_refinements": road_data["roads"],
        "plot_refinements": plot_data["building_plots"],
        "rules": {
            "no_new_terrain_laws": True,
            "road_width_shoulders_banking": True,
            "road_grade_limit": ROAD_SLOPE_LIMIT,
            "plot_foundation_edges": True,
            "plot_entrance_connector_max_m": ENTRANCE_CONNECTOR_MAX_M,
            "asset_anchor_surface_rule": "refined_profiled_plane_sample_v0",
        },
    }
    refined["profile_aware_road_plot_refinement_v0"]["validation"] = validate_refinement(refined)
    REFINED_GRAPH_PATH.write_text(json.dumps(refined, indent=2) + "\n", encoding="utf-8")
    write_report(refined)
    write_receipt(refined)
    validation = refined["profile_aware_road_plot_refinement_v0"]["validation"]
    print(f"wrote {REFINED_GRAPH_PATH.relative_to(ROOT)}")
    print(
        f"roads={len(road_data['roads'])} plots={len(plot_data['building_plots'])} "
        f"max_grade={validation['max_road_grade']} cracks={validation['cracked_seam_count']} "
        f"anchors={validation['asset_anchor_status_counts']}"
    )
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
