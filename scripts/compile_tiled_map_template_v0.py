#!/usr/bin/env python3
"""Compile Tiled-style map templates into map-generation assembly JSON.

This is the first adapter from authored map-template layers into the engine:

Tiled-style JSON -> hex/elevation cells -> roads -> building plots ->
hazards -> asset placement requests -> compiler report

No Blender, mesh, or image output is created here.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "data" / "architecture" / "map_templates"
MAP_CUBE_DIR = ROOT / "data" / "architecture" / "map_cubes"
OUT_DIR = ROOT / "goal" / "architecture" / "map_templates_v0"
COMPILED_DIR = OUT_DIR / "compiled"
REPORT_PATH = OUT_DIR / "map_template_compiler_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "map_template_compiler_v0.receipt.json"


AXIAL_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
EDGE_NAMES = ["east", "north_east", "north_west", "west", "south_west", "south_east"]
SURFACE_TYPES = {
    1: "grass",
    2: "road",
    3: "stone",
    4: "ravine_edge",
    5: "building_plot",
}
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


def props_to_dict(item: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for prop in item.get("properties", []):
        props[prop["name"]] = prop.get("value")
    return props


def layer_by_name(template: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers: dict[str, dict[str, Any]] = {}
    for layer in template.get("layers", []):
        name = layer.get("name")
        if not isinstance(name, str):
            fail("map layer missing string name")
        if name in layers:
            fail(f"duplicate layer name `{name}`")
        layers[name] = layer
    return layers


def cell_id(q: int, r: int) -> str:
    def part(value: int) -> str:
        return f"m{abs(value)}" if value < 0 else f"p{value}"

    return f"cell_{part(q)}_{part(r)}"


def world_from_tiled(x: float, y: float, width: int, height: int, cell_size: float, hex_radius: float) -> tuple[float, float]:
    # Tiled remains the authoring space. The compiler maps it into pointy-top
    # hex world spacing so adjacent hex cells touch instead of becoming columns.
    del cell_size
    return ((x - width * 0.5) * math.sqrt(3.0) * hex_radius, (height * 0.5 - y) * 1.5 * hex_radius)


def object_world_point(obj: dict[str, Any], width: int, height: int, cell_size: float, hex_radius: float) -> tuple[float, float]:
    return world_from_tiled(float(obj.get("x", 0.0)), float(obj.get("y", 0.0)), width, height, cell_size, hex_radius)


def object_polyline_world(obj: dict[str, Any], width: int, height: int, cell_size: float, hex_radius: float) -> list[tuple[float, float]]:
    ox = float(obj.get("x", 0.0))
    oy = float(obj.get("y", 0.0))
    points = []
    for point in obj.get("polyline", []):
        points.append(world_from_tiled(ox + float(point["x"]), oy + float(point["y"]), width, height, cell_size, hex_radius))
    return points


def object_polygon_world(obj: dict[str, Any], width: int, height: int, cell_size: float, hex_radius: float) -> list[tuple[float, float]]:
    ox = float(obj.get("x", 0.0))
    oy = float(obj.get("y", 0.0))
    if "polygon" in obj:
        return [world_from_tiled(ox + float(point["x"]), oy + float(point["y"]), width, height, cell_size, hex_radius) for point in obj["polygon"]]
    w = float(obj.get("width", 0.0))
    h = float(obj.get("height", 0.0))
    return [
        world_from_tiled(ox, oy, width, height, cell_size, hex_radius),
        world_from_tiled(ox + w, oy, width, height, cell_size, hex_radius),
        world_from_tiled(ox + w, oy + h, width, height, cell_size, hex_radius),
        world_from_tiled(ox, oy + h, width, height, cell_size, hex_radius),
    ]


def point_in_polygon(px: float, py: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-6) + xi):
            inside = not inside
        j = i
    return inside


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    length_sq = abx * abx + aby * aby
    if length_sq == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / length_sq))
    return math.hypot(px - (ax + abx * t), py - (ay + aby * t))


def distance_to_polyline(px: float, py: float, points: list[tuple[float, float]]) -> float:
    if len(points) < 2:
        return float("inf")
    return min(
        distance_to_segment(px, py, ax, ay, bx, by)
        for (ax, ay), (bx, by) in zip(points, points[1:], strict=False)
    )


def normalize2(x: float, y: float) -> tuple[float, float]:
    length = math.hypot(x, y)
    if length <= 1e-6:
        return (1.0, 0.0)
    return (x / length, y / length)


def direction_from_degrees(degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return normalize2(math.sin(radians), math.cos(radians))


def right_from_forward(forward: tuple[float, float]) -> tuple[float, float]:
    return normalize2(forward[1], -forward[0])


def project_point_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[tuple[float, float], float, float]:
    abx = bx - ax
    aby = by - ay
    length_sq = abx * abx + aby * aby
    if length_sq <= 1e-9:
        return (ax, ay), 0.0, math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / length_sq))
    hit = (ax + abx * t, ay + aby * t)
    return hit, t, math.hypot(px - hit[0], py - hit[1])


def nearest_polyline_projection(px: float, py: float, points: list[tuple[float, float]]) -> dict[str, Any]:
    best = {
        "position": (px, py),
        "distance": float("inf"),
        "segment_index": None,
        "tangent": (1.0, 0.0),
    }
    for index, ((ax, ay), (bx, by)) in enumerate(zip(points, points[1:], strict=False)):
        hit, _t, distance = project_point_to_segment(px, py, ax, ay, bx, by)
        if distance < float(best["distance"]):
            best = {
                "position": hit,
                "distance": distance,
                "segment_index": index,
                "tangent": normalize2(bx - ax, by - ay),
            }
    return best


def nearest_polygon_edge(px: float, py: float, polygon: list[list[float]]) -> dict[str, Any]:
    points = [(float(x), float(y)) for x, y in polygon]
    if not points:
        return {"position": (px, py), "distance": float("inf"), "edge_index": None, "tangent": (1.0, 0.0)}
    closed = points + [points[0]]
    best = nearest_polyline_projection(px, py, closed)
    best["edge_index"] = best.pop("segment_index")
    return best


def classify_edge(delta: float) -> str:
    abs_delta = abs(delta)
    if abs_delta <= 0.001:
        return "flat"
    if abs_delta <= 0.5:
        return "step_up" if delta > 0 else "step_down"
    if abs_delta <= 1.5:
        return "ledge"
    return "cliff"


def require_tile_layer(layers: dict[str, dict[str, Any]], name: str, width: int, height: int) -> dict[str, Any]:
    layer = layers.get(name)
    if layer is None:
        fail(f"missing required tile layer `{name}`")
    if layer.get("type") != "tilelayer":
        fail(f"layer `{name}` must be tilelayer")
    if int(layer.get("width", -1)) != width or int(layer.get("height", -1)) != height:
        fail(f"layer `{name}` dimensions must match map")
    data = layer.get("data")
    if not isinstance(data, list) or len(data) != width * height:
        fail(f"layer `{name}` data length must be {width * height}")
    return layer


def require_object_layer(layers: dict[str, dict[str, Any]], name: str) -> dict[str, Any]:
    layer = layers.get(name)
    if layer is None:
        fail(f"missing required object layer `{name}`")
    if layer.get("type") != "objectgroup":
        fail(f"layer `{name}` must be objectgroup")
    if not isinstance(layer.get("objects"), list):
        fail(f"object layer `{name}` requires objects list")
    return layer


def anchor_feature_projection(
    *,
    anchor_kind: str,
    anchor_ref: str | None,
    world_x: float,
    world_y: float,
    roads: list[dict[str, Any]],
    plots: list[dict[str, Any]],
    hazards: list[dict[str, Any]],
) -> dict[str, Any]:
    if anchor_kind in {"plot_edge", "height_seam"}:
        candidates = [plot for plot in plots if plot["plot_id"] == anchor_ref] if anchor_ref else plots
        if not candidates:
            return {"status": "reject", "reason": "missing_plot_anchor", "position": (world_x, world_y), "distance": float("inf"), "tangent": (1.0, 0.0)}
        best = min(
            (
                {**nearest_polygon_edge(world_x, world_y, plot["polygon"]), "feature_id": plot["plot_id"], "feature_type": "building_plot"}
                for plot in candidates
            ),
            key=lambda item: float(item["distance"]),
        )
        best["status"] = "ok"
        return best
    if anchor_kind in {"road_edge", "bridge_span"}:
        source = hazards if anchor_kind == "bridge_span" else roads
        id_key = "hazard_id" if anchor_kind == "bridge_span" else "road_id"
        feature_type = "hazard_edge" if anchor_kind == "bridge_span" else "road"
        candidates = [item for item in source if item[id_key] == anchor_ref] if anchor_ref else source
        if not candidates:
            return {"status": "reject", "reason": f"missing_{feature_type}_anchor", "position": (world_x, world_y), "distance": float("inf"), "tangent": (1.0, 0.0)}
        best = min(
            (
                {**nearest_polyline_projection(world_x, world_y, [(float(x), float(y)) for x, y in item["points"]]), "feature_id": item[id_key], "feature_type": feature_type}
                for item in candidates
            ),
            key=lambda item: float(item["distance"]),
        )
        best["status"] = "ok"
        return best
    return {"status": "ok", "feature_id": anchor_ref, "feature_type": "free_point", "position": (world_x, world_y), "distance": 0.0, "tangent": (1.0, 0.0)}


def clearance_status(
    *,
    world_x: float,
    world_y: float,
    footprint_width: float,
    footprint_depth: float,
    anchor_kind: str,
    cells: list[dict[str, Any]],
) -> dict[str, Any]:
    radius = max(footprint_width, footprint_depth) * 0.62
    near_cells = [
        cell
        for cell in cells
        if math.hypot(float(cell["world_x"]) - world_x, float(cell["world_y"]) - world_y) <= radius
    ]
    if not near_cells:
        return {"status": "reject", "reason": "no_cells_under_footprint", "checked_cell_count": 0, "height_range_m": 0.0, "hazard_cell_count": 0}
    heights = [float(cell["final_height"]) for cell in near_cells]
    hazard_count = sum(1 for cell in near_cells if "hazard" in cell["movement_tags"] or cell["surface_type"] == "ravine_edge")
    height_range = max(heights) - min(heights)
    if anchor_kind != "bridge_span" and hazard_count:
        status, reason = "warn", "footprint_overlaps_hazard_cells"
    elif anchor_kind != "bridge_span" and height_range > 0.75:
        status, reason = "warn", "uneven_footprint_height"
    elif anchor_kind == "bridge_span" and hazard_count == 0:
        status, reason = "warn", "bridge_span_has_no_hazard_underfoot"
    else:
        status, reason = "pass", "clearance_ok"
    return {
        "status": status,
        "reason": reason,
        "checked_cell_count": len(near_cells),
        "height_range_m": round(height_range, 6),
        "hazard_cell_count": hazard_count,
    }


def compile_template(path: Path) -> dict[str, Any]:
    template = load_json(path)
    if template.get("type") != "map":
        fail(f"{path.relative_to(ROOT)} is not a Tiled-style map")
    width = int(template.get("width", 0))
    height = int(template.get("height", 0))
    if width <= 0 or height <= 0:
        fail("map width/height must be positive")

    props = props_to_dict(template)
    cell_size = float(props.get("cell_size_m", 1.0))
    hex_radius = float(props.get("hex_radius_m", cell_size * 0.55))
    vertical_step = float(props.get("vertical_step_m", 0.5))
    map_cube_id = str(props.get("map_cube_id", "standard_32m_cube_v0"))
    map_cube_path = MAP_CUBE_DIR / f"{map_cube_id}.json"
    if not map_cube_path.exists():
        fail(f"unknown map_cube_id `{map_cube_id}`")
    map_cube = load_json(map_cube_path)

    layers = layer_by_name(template)
    height_layer = require_tile_layer(layers, "terrain_height", width, height)
    surface_layer = require_tile_layer(layers, "terrain_surface", width, height)
    road_layer = require_object_layer(layers, "roads_paths")
    plot_layer = require_object_layer(layers, "building_plots")
    hazard_layer = require_object_layer(layers, "hazard_edges")
    socket_layer = require_object_layer(layers, "asset_sockets")

    height_data = [int(value) for value in height_layer["data"]]
    surface_data = [int(value) for value in surface_layer["data"]]
    z_min, z_max = [float(v) for v in map_cube["coordinate_range"]["z"]]
    cells: list[dict[str, Any]] = []
    by_coord: dict[tuple[int, int], dict[str, Any]] = {}
    for row in range(height):
        for col in range(width):
            index = row * width + col
            q = col - width // 2
            r = row - height // 2
            world_x, world_y = world_from_tiled(
                col + 0.5 + (0.5 if row % 2 else 0.0),
                row + 0.5,
                width,
                height,
                cell_size,
                hex_radius,
            )
            final_height = height_data[index] * vertical_step
            if final_height < z_min or final_height > z_max:
                fail(f"height outside map cube z range at {col},{row}")
            surface_type = SURFACE_TYPES.get(surface_data[index], f"surface_{surface_data[index]}")
            movement_tags = ["walkable"]
            if surface_type == "road":
                movement_tags.append("route")
            if surface_type == "ravine_edge":
                movement_tags.extend(["fall_hazard", "avoid"])
            cell = {
                "cell_id": cell_id(q, r),
                "col": col,
                "row": row,
                "q": q,
                "r": r,
                "s": -q - r,
                "world_x": round(world_x, 6),
                "world_y": round(world_y, 6),
                "base_height": round(final_height, 6),
                "fold_offset": 0.0,
                "final_height": round(final_height, 6),
                "height_level": height_data[index],
                "surface_type": surface_type,
                "topology_role": "route_surface" if surface_type == "road" else "hazard_edge" if surface_type == "ravine_edge" else "terrain",
                "buildable": surface_type in {"building_plot", "grass", "stone"},
                "edge_profiles": [],
                "movement_tags": movement_tags,
                "structure_socket_tags": ["building_plot_candidate"] if surface_type == "building_plot" else [],
                "source_tile_index": index,
                "plot_ids": [],
                "road_ids": [],
                "hazard_ids": [],
            }
            cells.append(cell)
            by_coord[(q, r)] = cell

    edge_counts: dict[str, int] = {}
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for cell in cells:
        profiles: list[str] = []
        for direction_index, (dq, dr) in enumerate(AXIAL_DIRECTIONS):
            neighbor = by_coord.get((cell["q"] + dq, cell["r"] + dr))
            if neighbor is None:
                profiles.append("boundary")
                edge_counts["boundary"] = edge_counts.get("boundary", 0) + 1
                continue
            delta = float(neighbor["final_height"]) - float(cell["final_height"])
            directed = classify_edge(delta)
            profiles.append(directed)
            edge_key = tuple(sorted((cell["cell_id"], neighbor["cell_id"])))
            if edge_key in seen:
                continue
            seen.add(edge_key)
            undirected = classify_edge(abs(delta))
            edge_counts[undirected] = edge_counts.get(undirected, 0) + 1
            edges.append(
                {
                    "from": cell["cell_id"],
                    "to": neighbor["cell_id"],
                    "direction": EDGE_NAMES[direction_index],
                    "type": undirected,
                    "height_delta": round(abs(delta), 6),
                }
            )
        cell["edge_profiles"] = profiles

    roads = []
    for obj in road_layer["objects"]:
        obj_props = props_to_dict(obj)
        points = object_polyline_world(obj, width, height, cell_size, hex_radius)
        road_id = str(obj.get("name", f"road_{obj.get('id')}"))
        road = {
            "road_id": road_id,
            "source_object_id": obj.get("id"),
            "points": [[round(x, 6), round(y, 6)] for x, y in points],
            "width_m": float(obj_props.get("width_m", 1.0)),
            "movement_tag": obj_props.get("movement_tag", "route"),
            "surface_type": obj_props.get("surface_type", "road"),
            "affected_cells": [],
        }
        for cell in cells:
            if distance_to_polyline(float(cell["world_x"]), float(cell["world_y"]), points) <= road["width_m"] * 0.5:
                cell["road_ids"].append(road_id)
                if road["movement_tag"] not in cell["movement_tags"]:
                    cell["movement_tags"].append(road["movement_tag"])
                if cell["topology_role"] == "terrain":
                    cell["topology_role"] = "route_surface"
                road["affected_cells"].append(cell["cell_id"])
        roads.append(road)

    building_plots = []
    for obj in plot_layer["objects"]:
        obj_props = props_to_dict(obj)
        polygon = object_polygon_world(obj, width, height, cell_size, hex_radius)
        plot_id = str(obj.get("name", f"plot_{obj.get('id')}"))
        plot = {
            "plot_id": plot_id,
            "source_object_id": obj.get("id"),
            "polygon": [[round(x, 6), round(y, 6)] for x, y in polygon],
            "floor_plan_ref": obj_props.get("floor_plan_ref"),
            "plot_role": obj_props.get("plot_role", "building_plot"),
            "recommended_asset_kit": obj_props.get("recommended_asset_kit"),
            "occupied_cells": [],
            "average_height": 0.0,
        }
        heights: list[float] = []
        for cell in cells:
            if point_in_polygon(float(cell["world_x"]), float(cell["world_y"]), polygon):
                cell["plot_ids"].append(plot_id)
                cell["buildable"] = True
                cell["topology_role"] = "building_plot"
                if "building_plot" not in cell["structure_socket_tags"]:
                    cell["structure_socket_tags"].append("building_plot")
                plot["occupied_cells"].append(cell["cell_id"])
                heights.append(float(cell["final_height"]))
        plot["average_height"] = round(sum(heights) / len(heights), 6) if heights else 0.0
        building_plots.append(plot)

    hazards = []
    for obj in hazard_layer["objects"]:
        obj_props = props_to_dict(obj)
        points = object_polyline_world(obj, width, height, cell_size, hex_radius)
        hazard_id = str(obj.get("name", f"hazard_{obj.get('id')}"))
        hazard = {
            "hazard_id": hazard_id,
            "source_object_id": obj.get("id"),
            "points": [[round(x, 6), round(y, 6)] for x, y in points],
            "hazard_type": obj_props.get("hazard_type", "hazard"),
            "severity": obj_props.get("severity", "medium"),
            "affected_cells": [],
        }
        for cell in cells:
            if distance_to_polyline(float(cell["world_x"]), float(cell["world_y"]), points) <= 1.1:
                cell["hazard_ids"].append(hazard_id)
                for tag in ["hazard", str(obj_props.get("movement_tag", "avoid"))]:
                    if tag not in cell["movement_tags"]:
                        cell["movement_tags"].append(tag)
                hazard["affected_cells"].append(cell["cell_id"])
        hazards.append(hazard)

    asset_sockets = []
    for obj in socket_layer["objects"]:
        obj_props = props_to_dict(obj)
        world_x, world_y = object_world_point(obj, width, height, cell_size, hex_radius)
        nearest_cell = min(cells, key=lambda cell: math.hypot(float(cell["world_x"]) - world_x, float(cell["world_y"]) - world_y))
        anchor_kind = str(obj_props.get("anchor_kind", "free_point"))
        anchor_ref = obj_props.get("anchor_ref")
        orientation_degrees = float(obj_props.get("orientation_degrees", 0.0))
        footprint_width = float(obj_props.get("footprint_width_m", 1.0))
        footprint_depth = float(obj_props.get("footprint_depth_m", 0.6))
        footprint_height = float(obj_props.get("footprint_height_m", 1.0))
        projection = anchor_feature_projection(
            anchor_kind=anchor_kind,
            anchor_ref=str(anchor_ref) if anchor_ref is not None else None,
            world_x=world_x,
            world_y=world_y,
            roads=roads,
            plots=building_plots,
            hazards=hazards,
        )
        anchor_x, anchor_y = projection["position"]
        nearest_anchor_cell = min(cells, key=lambda cell: math.hypot(float(cell["world_x"]) - float(anchor_x), float(cell["world_y"]) - float(anchor_y)))
        forward = direction_from_degrees(orientation_degrees)
        right = right_from_forward(forward)
        clearance = clearance_status(
            world_x=float(anchor_x),
            world_y=float(anchor_y),
            footprint_width=footprint_width,
            footprint_depth=footprint_depth,
            anchor_kind=anchor_kind,
            cells=cells,
        )
        anchor_status = "reject" if projection["status"] == "reject" else clearance["status"]
        asset_sockets.append(
            {
                "socket_id": str(obj.get("name", f"socket_{obj.get('id')}")),
                "source_object_id": obj.get("id"),
                "world_position": [round(float(anchor_x), 6), round(float(anchor_y), 6), nearest_anchor_cell["final_height"]],
                "authored_world_position": [round(world_x, 6), round(world_y, 6), nearest_cell["final_height"]],
                "asset_ref": obj_props.get("asset_ref"),
                "socket_type": obj_props.get("socket_type"),
                "anchor_kind": anchor_kind,
                "anchor_ref": anchor_ref,
                "orientation_degrees": orientation_degrees,
                "nearest_cell_id": nearest_anchor_cell["cell_id"],
                "anchor_frame": {
                    "anchor_kind": anchor_kind,
                    "parent_feature_id": projection.get("feature_id"),
                    "parent_feature_type": projection.get("feature_type"),
                    "position": [round(float(anchor_x), 6), round(float(anchor_y), 6), nearest_anchor_cell["final_height"]],
                    "forward": [round(forward[0], 6), round(forward[1], 6), 0.0],
                    "right": [round(right[0], 6), round(right[1], 6), 0.0],
                    "up": [0.0, 0.0, 1.0],
                    "feature_tangent": [round(float(projection["tangent"][0]), 6), round(float(projection["tangent"][1]), 6), 0.0],
                    "feature_distance_m": round(float(projection["distance"]), 6),
                    "orientation_source": "authored_socket_property",
                    "footprint": {
                        "width_m": footprint_width,
                        "depth_m": footprint_depth,
                        "height_m": footprint_height,
                    },
                },
                "placement_validation": {
                    "status": anchor_status,
                    "anchor_projection_status": projection["status"],
                    "anchor_projection_reason": projection.get("reason", "projected_to_feature"),
                    "clearance": clearance,
                },
            }
        )

    template_id = str(props.get("template_id", path.stem))
    anchor_status_counts: dict[str, int] = {}
    for socket in asset_sockets:
        status = socket["placement_validation"]["status"]
        anchor_status_counts[status] = anchor_status_counts.get(status, 0) + 1

    compiled = {
        "schema": "compiled_tiled_map_template_v0",
        "template_id": template_id,
        "source_template": str(path.relative_to(ROOT)),
        "compiled_at_utc": now_iso(),
        "source_model": "tiled_style_json",
        "map_cube_id": map_cube_id,
        "dimensions": {"width": width, "height": height, "z_levels": int(props.get("z_levels", 8))},
        "cell_size_m": cell_size,
        "hex_radius_m": hex_radius,
        "vertical_step_m": vertical_step,
        "cells": cells,
        "edges": edges,
        "roads": roads,
        "building_plots": building_plots,
        "hazards": hazards,
        "asset_sockets": asset_sockets,
        "summary": {
            "cell_count": len(cells),
            "edge_count": len(edges),
            "edge_counts": edge_counts,
            "road_count": len(roads),
            "building_plot_count": len(building_plots),
            "hazard_count": len(hazards),
            "asset_socket_count": len(asset_sockets),
            "anchor_status_counts": anchor_status_counts,
            "height_levels": sorted(set(height_data)),
            "surface_types": sorted(set(SURFACE_TYPES.get(value, f"surface_{value}") for value in surface_data)),
        },
        "source_references": [
            "https://doc.mapeditor.org/en/stable/reference/json-map-format/",
            "https://doc.mapeditor.org/en/stable/manual/objects/",
            "https://doc.mapeditor.org/en/stable/manual/custom-properties/",
            "https://www.redblobgames.com/grids/hexagons/",
            "https://docs.blender.org/api/current/bpy.types.Mesh.html",
        ],
        "no_claims": NO_CLAIMS,
    }
    return compiled


def write_report(compiled_maps: list[dict[str, Any]]) -> None:
    lines = [
        "# Map Template Compiler v0",
        "",
        "This report proves a Tiled-style authored map can compile into engine-readable terrain, roads, building plots, hazards, and asset placement requests.",
        "",
        "| template | cells | roads | plots | hazards | sockets | anchors | height levels | edge counts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for compiled in compiled_maps:
        summary = compiled["summary"]
        edge_summary = ", ".join(f"{key}:{value}" for key, value in sorted(summary["edge_counts"].items()))
        anchor_summary = ", ".join(f"{key}:{value}" for key, value in sorted(summary.get("anchor_status_counts", {}).items()))
        lines.append(
            f"| `{compiled['template_id']}` | {summary['cell_count']} | {summary['road_count']} | "
            f"{summary['building_plot_count']} | {summary['hazard_count']} | {summary['asset_socket_count']} | "
            f"{anchor_summary} | {summary['height_levels']} | {edge_summary} |"
        )
    lines.extend(
        [
            "",
            "## Anchor Frames",
            "",
            "| socket | anchor kind | parent feature | status | feature distance m | clearance reason |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for compiled in compiled_maps:
        for socket in compiled["asset_sockets"]:
            frame = socket["anchor_frame"]
            validation = socket["placement_validation"]
            lines.append(
                f"| `{socket['socket_id']}` | `{frame['anchor_kind']}` | `{frame.get('parent_feature_id')}` | "
                f"`{validation['status']}` | {frame['feature_distance_m']} | `{validation['clearance']['reason']}` |"
            )
    lines.extend(
        [
            "",
            "## Build Path",
            "",
            "```text",
            "Tiled-style JSON -> compiled map template -> Blender debug render -> future terrain/building/game graph compiler",
            "```",
            "",
            "## Scope",
            "",
            "- no mesh output from this compiler",
            "- no production approval",
            "- no structural or fabrication claim",
            "- no Gym/Museum approval",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    template_paths = sorted(TEMPLATE_DIR.glob("*.json"))
    if not template_paths:
        fail(f"no templates found in {TEMPLATE_DIR.relative_to(ROOT)}")
    compiled_maps = []
    files_created = []
    for path in template_paths:
        compiled = compile_template(path)
        out_path = COMPILED_DIR / f"{compiled['template_id']}_compiled.json"
        out_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        compiled_maps.append(compiled)
        files_created.append(str(out_path.relative_to(ROOT)))
        print(f"wrote {out_path.relative_to(ROOT)}")
    write_report(compiled_maps)
    files_created.append(str(REPORT_PATH.relative_to(ROOT)))
    receipt = {
        "receipt_type": "map_template_compiler_v0",
        "created_at_utc": now_iso(),
        "files_created": files_created,
        "template_count": len(compiled_maps),
        "source_model": "tiled_style_json",
        "no_images": True,
        "no_meshes": True,
        "no_production_approval": True,
        "no_gym_museum_approval": True,
        "summary": "Compiled Tiled-style map templates into terrain, road, building plot, hazard, asset socket, and footprint anchor frame records.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
