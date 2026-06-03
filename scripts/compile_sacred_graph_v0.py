#!/usr/bin/env python3
"""Compile sacred-geometry source recipes into deterministic 2D graph JSON.

This is the construction layer before assets:

source graph recipe -> named points/edges/selections -> graph JSON + SVG preview

It intentionally does not execute Blender, write mesh exports, or make repo-local
generated media. SVG previews are written under /tmp by default.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "sacred_graph_recipes_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_sacred_graph_v0")
DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SCHEMA = "sacred_graph_recipe_bundle_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {repo_display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {repo_display_path(path)}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"{repo_display_path(path)} must contain a JSON object")
    return data


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def finite_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    return round(float(value), 6)


def positive_float(value: Any, field: str) -> float:
    number = finite_float(value, field)
    if number <= 0.0:
        fail(f"{field} must be positive")
    return number


def integer_at_least(value: Any, minimum: int, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def ratio_less_than_one(value: Any, field: str) -> float:
    number = finite_float(value, field)
    if number < 0.0 or number >= 1.0:
        fail(f"{field} must be >= 0 and < 1")
    return number


def finite_vector(value: Any, field: str, length: int = 2) -> list[float]:
    items = require_list(value, field)
    if len(items) != length:
        fail(f"{field} must contain {length} numbers")
    return [finite_float(item, f"{field}[{index}]") for index, item in enumerate(items)]


def require_false_claims(value: Any, field: str) -> None:
    claims = require_object(value, field)
    if claims != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")


def load_operation_terms() -> set[str]:
    terms: set[str] = set()
    for path in sorted((DICTIONARY_ROOT / "operations").glob("*.json")):
        term = load_json(path)
        term_id = require_string(term.get("term_id"), f"{repo_display_path(path)}.term_id")
        category = require_string(term.get("category"), f"{repo_display_path(path)}.category")
        if category in {"mesh_operation", "composition_operation", "transform"}:
            terms.add(term_id)
    if not terms:
        fail("geometry dictionary operation terms are empty")
    return terms


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def angle_for_index(index: int, divisions: int, orientation_degrees: float) -> float:
    return math.radians(orientation_degrees) + math.tau * index / divisions


def radial_point(radius: float, index: int, divisions: int, orientation_degrees: float, origin: list[float]) -> list[float]:
    angle = angle_for_index(index, divisions, orientation_degrees)
    return [
        round(origin[0] + math.cos(angle) * radius, 6),
        round(origin[1] + math.sin(angle) * radius, 6),
    ]


def ellipse_point(angle: float, radius_x: float, radius_y: float) -> list[float]:
    return [round(math.cos(angle) * radius_x, 6), round(math.sin(angle) * radius_y, 6)]


def star_polygon_points(params: dict[str, Any]) -> list[list[float]]:
    point_count = integer_at_least(params.get("points"), 3, "star_polygon.points")
    outer_radius_x = positive_float(params.get("outer_radius_x"), "star_polygon.outer_radius_x")
    outer_radius_y = positive_float(params.get("outer_radius_y"), "star_polygon.outer_radius_y")
    inner_radius_x = positive_float(params.get("inner_radius_x"), "star_polygon.inner_radius_x")
    inner_radius_y = positive_float(params.get("inner_radius_y"), "star_polygon.inner_radius_y")
    flat_edge_ratio = ratio_less_than_one(params.get("flat_edge_ratio", 0.0), "star_polygon.flat_edge_ratio")
    if inner_radius_x >= outer_radius_x:
        fail("star_polygon.inner_radius_x must be less than outer_radius_x")
    if inner_radius_y >= outer_radius_y:
        fail("star_polygon.inner_radius_y must be less than outer_radius_y")

    step = math.tau / point_count
    half_step = step * 0.5
    points: list[list[float]] = []
    if flat_edge_ratio == 0.0:
        for index in range(point_count):
            angle = step * index
            points.append(ellipse_point(angle, outer_radius_x, outer_radius_y))
            points.append(ellipse_point(angle + half_step, inner_radius_x, inner_radius_y))
        return points

    flat_half_angle = half_step * flat_edge_ratio
    for index in range(point_count):
        angle = step * index
        points.append(ellipse_point(angle - flat_half_angle, outer_radius_x, outer_radius_y))
        points.append(ellipse_point(angle + flat_half_angle, outer_radius_x, outer_radius_y))
        points.append(ellipse_point(angle + half_step, inner_radius_x, inner_radius_y))
    return points


def validate_rings(graph_id: str, rings_value: Any) -> list[dict[str, Any]]:
    rings: list[dict[str, Any]] = []
    seen: set[str] = set()
    previous_radius: float | None = None
    for index, item in enumerate(require_list(rings_value, f"{graph_id}.rings")):
        ring = require_object(item, f"{graph_id}.rings[{index}]")
        ring_id = require_string(ring.get("ring_id"), f"{graph_id}.rings[{index}].ring_id")
        if ring_id in seen:
            fail(f"{graph_id}.rings duplicate ring_id: {ring_id}")
        seen.add(ring_id)
        radius = positive_float(ring.get("radius_m"), f"{graph_id}.rings[{index}].radius_m")
        if previous_radius is not None and radius <= previous_radius:
            fail(f"{graph_id}.rings[{index}].radius_m must increase")
        previous_radius = radius
        rings.append(
            {
                "ring_id": ring_id,
                "radius_m": radius,
                "role_hint": require_string(ring.get("role_hint"), f"{graph_id}.rings[{index}].role_hint"),
            }
        )
    if len(rings) < 1:
        fail(f"{graph_id}.rings must not be empty")
    return rings


def validate_star_connections(graph_id: str, divisions: int, rings: list[dict[str, Any]], value: Any) -> list[dict[str, Any]]:
    ring_ids = {ring["ring_id"] for ring in rings}
    seen: set[str] = set()
    result = []
    for index, item in enumerate(require_list(value, f"{graph_id}.star_connections")):
        connection = require_object(item, f"{graph_id}.star_connections[{index}]")
        connection_id = require_string(connection.get("connection_id"), f"{graph_id}.star_connections[{index}].connection_id")
        if connection_id in seen:
            fail(f"{graph_id}.star_connections duplicate connection_id: {connection_id}")
        seen.add(connection_id)
        ring_id = require_string(connection.get("ring_id"), f"{graph_id}.star_connections[{index}].ring_id")
        if ring_id not in ring_ids:
            fail(f"{graph_id}.star_connections[{index}].ring_id references unknown ring: {ring_id}")
        step = integer_at_least(connection.get("step"), 1, f"{graph_id}.star_connections[{index}].step")
        if step >= divisions:
            fail(f"{graph_id}.star_connections[{index}].step must be less than divisions")
        if gcd(step, divisions) != 1:
            fail(f"{graph_id}.star_connections[{index}].step must be coprime with divisions")
        result.append(
            {
                "connection_id": connection_id,
                "ring_id": ring_id,
                "step": step,
                "role_hint": require_string(connection.get("role_hint"), f"{graph_id}.star_connections[{index}].role_hint"),
            }
        )
    return result


def validate_derived_profiles(graph_id: str, value: Any) -> list[dict[str, Any]]:
    profiles = []
    seen: set[str] = set()
    for index, item in enumerate(require_list(value, f"{graph_id}.derived_profiles")):
        profile = require_object(item, f"{graph_id}.derived_profiles[{index}]")
        profile_id = require_string(profile.get("profile_id"), f"{graph_id}.derived_profiles[{index}].profile_id")
        if profile_id in seen:
            fail(f"{graph_id}.derived_profiles duplicate profile_id: {profile_id}")
        seen.add(profile_id)
        profile_type = require_string(profile.get("profile_type"), f"{graph_id}.derived_profiles[{index}].profile_type")
        if profile_type != "star_polygon":
            fail(f"{graph_id}.derived_profiles[{index}].profile_type only supports star_polygon in v0")
        params = require_object(profile.get("params"), f"{graph_id}.derived_profiles[{index}].params")
        vertices = star_polygon_points(params)
        roles = [
            require_string(role, f"{graph_id}.derived_profiles[{index}].architectural_roles[{role_index}]")
            for role_index, role in enumerate(require_list(profile.get("architectural_roles"), f"{graph_id}.derived_profiles[{index}].architectural_roles"))
        ]
        profiles.append(
            {
                "profile_id": profile_id,
                "profile_type": profile_type,
                "role_hint": require_string(profile.get("role_hint"), f"{graph_id}.derived_profiles[{index}].role_hint"),
                "params": {
                    "points": integer_at_least(params.get("points"), 3, f"{profile_id}.points"),
                    "outer_radius_x": positive_float(params.get("outer_radius_x"), f"{profile_id}.outer_radius_x"),
                    "outer_radius_y": positive_float(params.get("outer_radius_y"), f"{profile_id}.outer_radius_y"),
                    "inner_radius_x": positive_float(params.get("inner_radius_x"), f"{profile_id}.inner_radius_x"),
                    "inner_radius_y": positive_float(params.get("inner_radius_y"), f"{profile_id}.inner_radius_y"),
                    "flat_edge_ratio": ratio_less_than_one(params.get("flat_edge_ratio", 0.0), f"{profile_id}.flat_edge_ratio"),
                },
                "architectural_roles": roles,
                "vertices": vertices,
                "vertex_count": len(vertices),
            }
        )
    return profiles


def validate_selections(graph_id: str, selections: Any, profile_ids: set[str]) -> list[dict[str, Any]]:
    result = []
    seen: set[str] = set()
    for index, item in enumerate(require_list(selections, f"{graph_id}.selections")):
        selection = require_object(item, f"{graph_id}.selections[{index}]")
        selection_id = require_string(selection.get("selection_id"), f"{graph_id}.selections[{index}].selection_id")
        if selection_id in seen:
            fail(f"{graph_id}.selections duplicate selection_id: {selection_id}")
        seen.add(selection_id)
        selector = require_object(selection.get("selector"), f"{graph_id}.selections[{index}].selector")
        kind = require_string(selector.get("kind"), f"{graph_id}.selections[{index}].selector.kind")
        if kind == "derived_profile":
            profile_id = require_string(selector.get("profile_id"), f"{graph_id}.selections[{index}].selector.profile_id")
            if profile_id not in profile_ids:
                fail(f"{graph_id}.selections[{index}].selector.profile_id references unknown profile: {profile_id}")
        elif kind == "point_id":
            require_string(selector.get("point_id"), f"{graph_id}.selections[{index}].selector.point_id")
        elif kind == "edge_tag_query":
            require_string(selector.get("tag"), f"{graph_id}.selections[{index}].selector.tag")
        else:
            fail(f"{graph_id}.selections[{index}].selector.kind unsupported: {kind}")
        result.append(
            {
                "selection_id": selection_id,
                "selection_type": require_string(selection.get("selection_type"), f"{graph_id}.selections[{index}].selection_type"),
                "selector": selector,
                "architectural_roles": [
                    require_string(role, f"{graph_id}.selections[{index}].architectural_roles[{role_index}]")
                    for role_index, role in enumerate(require_list(selection.get("architectural_roles"), f"{graph_id}.selections[{index}].architectural_roles"))
                ],
            }
        )
    return result


def validate_graph(graph: Any, operations: set[str], index: int) -> dict[str, Any]:
    item = require_object(graph, f"graphs[{index}]")
    graph_id = require_string(item.get("graph_id"), f"graphs[{index}].graph_id")
    if require_string(item.get("graph_type"), f"{graph_id}.graph_type") != "radial_sacred_graph":
        fail(f"{graph_id}.graph_type only supports radial_sacred_graph in v0")
    operation = require_string(item.get("geometry_operation"), f"{graph_id}.geometry_operation")
    if operation not in operations:
        fail(f"{graph_id}.geometry_operation references unknown geometry operation: {operation}")
    divisions = integer_at_least(item.get("divisions"), 3, f"{graph_id}.divisions")
    origin = finite_vector(item.get("origin_m", [0.0, 0.0]), f"{graph_id}.origin_m", 2)
    orientation = finite_float(item.get("orientation_degrees", 0.0), f"{graph_id}.orientation_degrees")
    rings = validate_rings(graph_id, item.get("rings"))
    star_connections = validate_star_connections(graph_id, divisions, rings, item.get("star_connections", []))
    profiles = validate_derived_profiles(graph_id, item.get("derived_profiles", []))
    selections = validate_selections(graph_id, item.get("selections", []), {profile["profile_id"] for profile in profiles})
    require_false_claims(item.get("no_claims"), f"{graph_id}.no_claims")
    return {
        "graph_id": graph_id,
        "graph_type": "radial_sacred_graph",
        "geometry_operation": operation,
        "description": require_string(item.get("description"), f"{graph_id}.description"),
        "origin_m": origin,
        "divisions": divisions,
        "orientation_degrees": orientation,
        "rings": rings,
        "star_connections": star_connections,
        "derived_profiles": profiles,
        "selections": selections,
        "downstream_proofs": require_list(item.get("downstream_proofs", []), f"{graph_id}.downstream_proofs"),
        "validation_expectations": require_object(item.get("validation_expectations", {}), f"{graph_id}.validation_expectations"),
        "no_claims": item["no_claims"],
    }


def validate_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    if bundle.get("schema") != SCHEMA:
        fail(f"bundle schema must be {SCHEMA}")
    if require_object(bundle.get("rules"), "rules") != {
        "source_lane": True,
        "deterministic_output": True,
        "no_blender_logic": True,
        "no_generated_outputs": True,
        "no_wall_clock_fields": True,
        "graph_is_source_field": True,
    }:
        fail("bundle rules must match sacred graph source boundaries")
    operations = load_operation_terms()
    graphs_source = require_list(bundle.get("graphs"), "graphs")
    if bundle.get("graph_count") != len(graphs_source):
        fail("bundle graph_count must match graphs length")
    graphs = [validate_graph(graph, operations, index) for index, graph in enumerate(graphs_source)]
    seen: set[str] = set()
    for graph in graphs:
        if graph["graph_id"] in seen:
            fail(f"duplicate graph_id: {graph['graph_id']}")
        seen.add(graph["graph_id"])
    return graphs


def graph_points(graph: dict[str, Any]) -> list[dict[str, Any]]:
    points = [{"point_id": "center", "xy_m": graph["origin_m"], "tags": ["center", "boss"]}]
    divisions = graph["divisions"]
    orientation = graph["orientation_degrees"]
    origin = graph["origin_m"]
    for ring in graph["rings"]:
        ring_id = ring["ring_id"]
        for index in range(divisions):
            points.append(
                {
                    "point_id": f"{ring_id}_p_{index:02d}",
                    "xy_m": radial_point(ring["radius_m"], index, divisions, orientation, origin),
                    "ring_id": ring_id,
                    "division_index": index,
                    "tags": ["ring_point", f"ring:{ring_id}", f"division:{index:02d}"],
                }
            )
    return points


def edge_record(edge_id: str, a: str, b: str, edge_type: str, tags: list[str]) -> dict[str, Any]:
    return {"edge_id": edge_id, "from": a, "to": b, "edge_type": edge_type, "tags": tags}


def graph_edges(graph: dict[str, Any]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    divisions = graph["divisions"]
    rings = graph["rings"]
    for ring in rings:
        ring_id = ring["ring_id"]
        for index in range(divisions):
            nxt = (index + 1) % divisions
            edges.append(
                edge_record(
                    f"ring_{ring_id}_{index:02d}_{nxt:02d}",
                    f"{ring_id}_p_{index:02d}",
                    f"{ring_id}_p_{nxt:02d}",
                    "ring",
                    ["ring", f"ring:{ring_id}", f"division:{index:02d}"],
                )
            )
    for index in range(divisions):
        first_ring = rings[0]["ring_id"]
        edges.append(
            edge_record(
                f"radial_{index:02d}_center_to_{first_ring}",
                "center",
                f"{first_ring}_p_{index:02d}",
                "radial",
                ["radial", f"division:{index:02d}"],
            )
        )
        for ring_index in range(len(rings) - 1):
            a = rings[ring_index]["ring_id"]
            b = rings[ring_index + 1]["ring_id"]
            edges.append(
                edge_record(
                    f"radial_{index:02d}_{a}_to_{b}",
                    f"{a}_p_{index:02d}",
                    f"{b}_p_{index:02d}",
                    "radial",
                    ["radial", f"division:{index:02d}"],
                )
            )
    for connection in graph["star_connections"]:
        ring_id = connection["ring_id"]
        step = connection["step"]
        for index in range(divisions):
            target = (index + step) % divisions
            edges.append(
                edge_record(
                    f"star_{connection['connection_id']}_{index:02d}_{target:02d}",
                    f"{ring_id}_p_{index:02d}",
                    f"{ring_id}_p_{target:02d}",
                    "star_step",
                    ["star", f"ring:{ring_id}", f"star_step:{step}", f"division:{index:02d}"],
                )
            )
    return edges


def selected_parts(selections: list[dict[str, Any]], points: list[dict[str, Any]], edges: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    point_ids = {point["point_id"] for point in points}
    profile_by_id = {profile["profile_id"]: profile for profile in profiles}
    result = []
    for selection in selections:
        selector = selection["selector"]
        kind = selector["kind"]
        selected_point_ids: list[str] = []
        selected_edge_ids: list[str] = []
        selected_profile: dict[str, Any] | None = None
        if kind == "point_id":
            point_id = selector["point_id"]
            if point_id not in point_ids:
                fail(f"{selection['selection_id']} references unknown point: {point_id}")
            selected_point_ids = [point_id]
        elif kind == "edge_tag_query":
            tag = selector["tag"]
            selected_edge_ids = [edge["edge_id"] for edge in edges if tag in edge["tags"]]
            if not selected_edge_ids:
                fail(f"{selection['selection_id']} selected no edges for tag `{tag}`")
        elif kind == "derived_profile":
            profile = profile_by_id[selector["profile_id"]]
            selected_profile = {
                "profile_id": profile["profile_id"],
                "profile_type": profile["profile_type"],
                "vertices": profile["vertices"],
                "vertex_count": profile["vertex_count"],
            }
        result.append(
            {
                "selection_id": selection["selection_id"],
                "selection_type": selection["selection_type"],
                "architectural_roles": selection["architectural_roles"],
                "point_ids": selected_point_ids,
                "edge_ids": selected_edge_ids,
                "profile": selected_profile,
            }
        )
    return result


def bounds_2d(points: list[list[float]]) -> dict[str, list[float]]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "min": [round(min(xs), 6), round(min(ys), 6)],
        "max": [round(max(xs), 6), round(max(ys), 6)],
    }


def compile_graph(bundle: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    points = graph_points(graph)
    edges = graph_edges(graph)
    selections = selected_parts(graph["selections"], points, edges, graph["derived_profiles"])
    xy_points = [point["xy_m"] for point in points]
    profile_bounds = {
        profile["profile_id"]: bounds_2d(profile["vertices"])
        for profile in graph["derived_profiles"]
    }
    compiled = {
        "schema": "gameguy_sacred_graph_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "graph_id": graph["graph_id"],
        "graph_type": graph["graph_type"],
        "geometry_operation": graph["geometry_operation"],
        "description": graph["description"],
        "units": bundle.get("units", "abstract_meter"),
        "origin_m": graph["origin_m"],
        "divisions": graph["divisions"],
        "orientation_degrees": graph["orientation_degrees"],
        "bounds_m": bounds_2d(xy_points),
        "rings": graph["rings"],
        "star_connections": graph["star_connections"],
        "points": points,
        "edges": edges,
        "derived_profiles": graph["derived_profiles"],
        "selections": selections,
        "downstream_proofs": graph["downstream_proofs"],
        "summary": {
            "point_count": len(points),
            "edge_count": len(edges),
            "ring_count": len(graph["rings"]),
            "star_connection_count": len(graph["star_connections"]),
            "derived_profile_count": len(graph["derived_profiles"]),
            "selection_count": len(selections),
            "profile_bounds_m": profile_bounds,
        },
        "rules": {
            "source_graph_only": True,
            "selected_subgraphs_named": True,
            "blender_is_adapter_layer": True,
            "no_mesh_output": True,
            "no_media_output_in_repo": True,
        },
        "validation_expectations": graph["validation_expectations"],
        "no_claims": graph["no_claims"],
    }
    expected = graph["validation_expectations"]
    checks = {
        "point_count": len(points),
        "edge_count": len(edges),
        "ring_count": len(graph["rings"]),
        "star_connection_count": len(graph["star_connections"]),
        "derived_profile_count": len(graph["derived_profiles"]),
    }
    for key, value in checks.items():
        if expected.get(key) != value:
            fail(f"{graph['graph_id']}.validation_expectations.{key} must be {value}")
    return compiled


def svg_point(point: list[float], scale: float, origin: float) -> tuple[float, float]:
    return origin + point[0] * scale, origin - point[1] * scale


def svg_line(a: list[float], b: list[float], scale: float, origin: float, klass: str) -> str:
    ax, ay = svg_point(a, scale, origin)
    bx, by = svg_point(b, scale, origin)
    return f'<line class="{klass}" x1="{ax:.3f}" y1="{ay:.3f}" x2="{bx:.3f}" y2="{by:.3f}" />'


def render_svg(graph: dict[str, Any]) -> str:
    point_by_id = {point["point_id"]: point["xy_m"] for point in graph["points"]}
    radius = max(abs(value) for point in point_by_id.values() for value in point) + 0.08
    size = 960
    center = size * 0.5
    scale = (size * 0.42) / radius
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="960" viewBox="0 0 960 960">',
        "<style>",
        ".bg{fill:#fbfaf6}.ring{fill:none;stroke:#b9b3a7;stroke-width:1.2}.radial{stroke:#7aa6b8;stroke-width:1.1;opacity:.8}.star_step{stroke:#d66b3d;stroke-width:1;opacity:.55}.point{fill:#202020}.label{font:18px monospace;fill:#202020}",
        "</style>",
        '<rect class="bg" x="0" y="0" width="960" height="960" />',
    ]
    for ring in graph["rings"]:
        lines.append(f'<circle class="ring" cx="{center:.3f}" cy="{center:.3f}" r="{ring["radius_m"] * scale:.3f}" />')
    for edge in graph["edges"]:
        if edge["edge_type"] in {"radial", "star_step"}:
            lines.append(svg_line(point_by_id[edge["from"]], point_by_id[edge["to"]], scale, center, edge["edge_type"]))
    for point_id, xy in point_by_id.items():
        if point_id == "center" or point_id.startswith("outer_tip_p_"):
            x, y = svg_point(xy, scale, center)
            lines.append(f'<circle class="point" cx="{x:.3f}" cy="{y:.3f}" r="3" />')
    lines.append(f'<text class="label" x="28" y="42">{graph["graph_id"]}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def write_outputs(bundle: dict[str, Any], graphs: list[dict[str, Any]], out_root: Path, clean: bool) -> dict[str, Any]:
    if clean and out_root.exists():
        shutil.rmtree(out_root)
    (out_root / "graphs").mkdir(parents=True, exist_ok=True)
    (out_root / "svg").mkdir(parents=True, exist_ok=True)
    manifest_graphs = []
    for graph in graphs:
        compiled = compile_graph(bundle, graph)
        graph_path = out_root / "graphs" / f"{graph['graph_id']}.json"
        svg_path = out_root / "svg" / f"{graph['graph_id']}.svg"
        graph_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        svg_path.write_text(render_svg(compiled), encoding="utf-8")
        manifest_graphs.append(
            {
                "graph_id": graph["graph_id"],
                "path": f"graphs/{graph['graph_id']}.json",
                "svg_path": f"svg/{graph['graph_id']}.svg",
                "point_count": compiled["summary"]["point_count"],
                "edge_count": compiled["summary"]["edge_count"],
                "selection_count": compiled["summary"]["selection_count"],
            }
        )
    manifest = {
        "schema": "gameguy_sacred_graph_manifest_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "graph_count": len(manifest_graphs),
        "graphs": manifest_graphs,
        "rules": {
            "no_blender": True,
            "no_mesh_export_files": True,
            "json_and_svg_preview_only": True,
            "generated_outputs_in_repo": False,
        },
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile sacred construction graph source recipes.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    bundle = load_json(bundle_path)
    graphs = validate_bundle(bundle)
    if args.validate_only:
        print(f"compiled sacred graphs={len(graphs)} out=<validate-only>")
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = write_outputs(bundle, graphs, out_root, args.clean)
    point_count = sum(graph["point_count"] for graph in manifest["graphs"])
    edge_count = sum(graph["edge_count"] for graph in manifest["graphs"])
    print(f"compiled sacred graphs={manifest['graph_count']} points={point_count} edges={edge_count} out={out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
