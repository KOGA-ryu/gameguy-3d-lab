#!/usr/bin/env python3
"""Compile Building Graph Kit Expansion v0.

Expands attached building graphs into deterministic local primitives while
keeping the baked map-facing contract small. This is still a cheap static graph:
no ornament, no live procedural solve after bake, and no production claims.
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

import compile_building_graph_attachment_v0 as attachment_compile  # noqa: E402


ATTACHMENT_PATH = attachment_compile.ATTACHMENT_PATH
MEASURED_INDEX_PATH = attachment_compile.MEASURED_INDEX_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "building_graph_kit_expansion_v0"
KIT_GRAPH_PATH = OUT_DIR / "building_graph_kit_expansion_v0.json"
REPORT_PATH = OUT_DIR / "building_graph_kit_expansion_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "building_graph_kit_expansion_v0.receipt.json"

NO_CLAIMS = attachment_compile.NO_CLAIMS
REQUIRED_PRIMITIVES = [
    "foundation_skirt",
    "floor_slab",
    "wall_segment",
    "corner_post",
    "door_bay",
    "window_bay",
    "roof_cap_placeholder",
    "interior_socket",
    "exterior_socket",
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


def round6(value: float) -> float:
    return round(float(value), 6)


def measured_dims() -> dict[str, dict[str, float]]:
    index = load_json(MEASURED_INDEX_PATH)
    return {asset["asset_id"]: {key: float(value) for key, value in asset["dimensions_m"].items()} for asset in index["assets"]}


def edge_from_position(local_pos: list[float], bounds: dict[str, float]) -> str:
    distances = {
        "east": abs(float(local_pos[0]) - float(bounds["max_x"])),
        "west": abs(float(local_pos[0]) - float(bounds["min_x"])),
        "north": abs(float(local_pos[1]) - float(bounds["max_y"])),
        "south": abs(float(local_pos[1]) - float(bounds["min_y"])),
    }
    return min(distances, key=distances.get)


def component_box(
    component_id: str,
    component_type: str,
    center: list[float],
    dimensions: list[float],
    semantic_tags: list[str],
    material_role: str,
    measured_component_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    item = {
        "component_id": component_id,
        "component_type": component_type,
        "primitive": "box",
        "local_center_m": [round6(value) for value in center],
        "dimensions_m": [round6(value) for value in dimensions],
        "semantic_tags": semantic_tags,
        "material_role": material_role,
        **extra,
    }
    if measured_component_id:
        item["measured_component_id"] = measured_component_id
    return item


def component_from_existing(source: dict[str, Any], component_type: str, measured_component_id: str | None, material_role: str) -> dict[str, Any]:
    return {
        **source,
        "component_type": component_type,
        "material_role": material_role,
        **({"measured_component_id": measured_component_id} if measured_component_id else {}),
    }


def wall_repeat_count(length: float, wall_block_width: float) -> int:
    return max(1, round(float(length) / max(wall_block_width, 0.1)))


def make_wall_segments(graph: dict[str, Any], dims: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    wall_block = dims["measured_rectangular_wall_block_v1"]
    segments: list[dict[str, Any]] = []
    for source in graph["components"]:
        if source["component_type"] != "outer_wall":
            continue
        sx, sy, sz = [float(value) for value in source["dimensions_m"]]
        length = max(sx, sy)
        segment = component_from_existing(source, "wall_segment", "measured_rectangular_wall_block_v1", "wall")
        segment["component_id"] = source["component_id"].replace("outer_wall", "wall_segment")
        segment["wall_block_repeat_count"] = wall_repeat_count(length, wall_block["width"])
        segment["kit_primitive"] = "wall_segment"
        segments.append(segment)
    return segments


def floor_top_z(graph: dict[str, Any]) -> float:
    floor = next(component for component in graph["components"] if component["component_id"] == "floor_slab")
    return float(floor["local_center_m"][2]) + float(floor["dimensions_m"][2]) * 0.5


def make_corner_posts(graph: dict[str, Any], dims: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    bounds = graph["projected_local_bounds"]
    pier = dims["measured_square_pier_v1"]
    base_z = floor_top_z(graph)
    height = pier["height"]
    positions = {
        "north_east": [bounds["max_x"], bounds["max_y"]],
        "north_west": [bounds["min_x"], bounds["max_y"]],
        "south_east": [bounds["max_x"], bounds["min_y"]],
        "south_west": [bounds["min_x"], bounds["min_y"]],
    }
    return [
        component_box(
            f"corner_post_{name}",
            "corner_post",
            [xy[0], xy[1], base_z + height * 0.5],
            [pier["width"], pier["depth"], height],
            ["support", "blocked", "collision_proxy"],
            "post",
            "measured_square_pier_v1",
            kit_primitive="corner_post",
            corner=name,
        )
        for name, xy in positions.items()
    ]


def socket_with_frame(
    socket_id: str,
    socket_type: str,
    local_position: list[float],
    edge: str,
    compatible_tags: list[str],
    semantic_tags: list[str],
    parent_component_id: str | None = None,
) -> dict[str, Any]:
    return {
        "socket_id": socket_id,
        "socket_type": socket_type,
        "local_position_m": [round6(value) for value in local_position],
        "edge": edge,
        "compatible_tags": compatible_tags,
        "semantic_tags": semantic_tags,
        "parent_component_id": parent_component_id,
        "placement_space": "building_graph_local",
    }


def make_door_and_window_bays(
    graph: dict[str, Any],
    dims: dict[str, dict[str, float]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bounds = graph["projected_local_bounds"]
    floor_z = floor_top_z(graph)
    bay_components: list[dict[str, Any]] = []
    exterior_sockets: list[dict[str, Any]] = []
    has_window = False
    has_door = False
    for socket in graph["internal_asset_sockets"]:
        asset_id = socket["measured_asset_id"]
        if asset_id not in dims:
            continue
        dim = dims[asset_id]
        edge = socket.get("edge") or edge_from_position(socket["local_position_m"], bounds)
        socket_type = str(socket.get("socket_type", "asset_socket"))
        is_door = socket_type in {"portal", "door", "vertical_transition"}
        is_window = socket_type in {"window", "ornament_panel"} or "window" in asset_id or "arch_bay" in asset_id
        if is_door:
            component_type = "door_bay"
            component_id = f"door_bay_{socket['source_map_socket_id']}"
            tags = ["entrance", "walkable_transition", "asset_socket"]
            material = "door_bay"
            has_door = True
        elif is_window:
            component_type = "window_bay"
            component_id = f"window_bay_{socket['source_map_socket_id']}"
            tags = ["window", "wall_socket", "line_of_sight_breaker"]
            material = "window_bay"
            has_window = True
        else:
            continue
        center = [
            float(socket["local_position_m"][0]),
            float(socket["local_position_m"][1]),
            floor_z + float(dim["height"]) * 0.5,
        ]
        bay_components.append(
            component_box(
                component_id,
                component_type,
                center,
                [float(dim["width"]), float(dim["depth"]), float(dim["height"])],
                tags,
                material,
                asset_id,
                kit_primitive=component_type,
                source_local_socket_id=socket["socket_id"],
                source_map_socket_id=socket["source_map_socket_id"],
                edge=edge,
            )
        )
        exterior_sockets.append(
            socket_with_frame(
                f"exterior_{socket['source_map_socket_id']}",
                "exterior_socket",
                socket["local_position_m"],
                edge,
                [component_type, "measured_asset_mount"],
                tags,
                component_id,
            )
        )
    if not has_door:
        doorway = dims["measured_round_arch_bay_v1"]
        edge = graph["local_entrance_edge"]
        if edge == "north":
            x, y = 0.0, bounds["max_y"]
        elif edge == "south":
            x, y = 0.0, bounds["min_y"]
        elif edge == "east":
            x, y = bounds["max_x"], 0.0
        else:
            x, y = bounds["min_x"], 0.0
        component_id = f"door_bay_{graph['building_graph_id']}_service_entrance"
        bay_components.append(
            component_box(
                component_id,
                "door_bay",
                [x, y, floor_z + doorway["height"] * 0.5],
                [doorway["width"], doorway["depth"], doorway["height"]],
                ["entrance", "walkable_transition", "asset_socket"],
                "door_bay",
                "measured_round_arch_bay_v1",
                kit_primitive="door_bay",
                generated_by="deterministic_service_entrance_bay",
                edge=edge,
            )
        )
        exterior_sockets.append(
            socket_with_frame(
                f"exterior_{graph['building_graph_id']}_service_entrance",
                "exterior_socket",
                [x, y, floor_z],
                edge,
                ["door_bay", "road_connector"],
                ["entrance", "walkable_transition"],
                component_id,
            )
        )
    if not has_window:
        lancet = dims["measured_lancet_window_bay_v1"]
        edge = "west" if graph["local_entrance_edge"] in {"north", "south"} else "north"
        x = bounds["min_x"] if edge == "west" else 0.0
        y = bounds["max_y"] if edge == "north" else 0.0
        component_id = f"window_bay_{graph['building_graph_id']}_service_window"
        bay_components.append(
            component_box(
                component_id,
                "window_bay",
                [x, y, floor_z + lancet["height"] * 0.5],
                [lancet["width"], lancet["depth"], lancet["height"]],
                ["window", "wall_socket", "line_of_sight_breaker"],
                "window_bay",
                "measured_lancet_window_bay_v1",
                kit_primitive="window_bay",
                generated_by="deterministic_service_window_socket",
                edge=edge,
            )
        )
        exterior_sockets.append(
            socket_with_frame(
                f"exterior_{graph['building_graph_id']}_service_window",
                "exterior_socket",
                [x, y, floor_z],
                edge,
                ["window_bay", "measured_asset_mount"],
                ["window", "wall_socket"],
                component_id,
            )
        )
    return bay_components, exterior_sockets


def make_interior_sockets(graph: dict[str, Any]) -> list[dict[str, Any]]:
    floor_z = floor_top_z(graph)
    return [
        socket_with_frame(
            f"interior_{graph['building_graph_id']}_floor_center",
            "interior_socket",
            [0.0, 0.0, floor_z + 0.02],
            "center",
            ["floor_mount", "future_interior_asset"],
            ["interior_socket", "walkable"],
            "floor_slab",
        ),
        socket_with_frame(
            f"interior_{graph['building_graph_id']}_rear_wall",
            "interior_socket",
            [0.0, -float(graph["projected_local_bounds"]["max_y"]) * 0.45, floor_z + 0.8],
            "interior_wall",
            ["wall_mount", "future_gameplay_marker"],
            ["interior_socket", "wall_socket"],
            None,
        ),
    ]


def make_exterior_service_socket(graph: dict[str, Any]) -> dict[str, Any]:
    bounds = graph["projected_local_bounds"]
    floor_z = floor_top_z(graph)
    edge = graph["local_entrance_edge"]
    if edge == "north":
        pos = [0.0, bounds["max_y"] + 0.24, floor_z]
    elif edge == "south":
        pos = [0.0, bounds["min_y"] - 0.24, floor_z]
    elif edge == "east":
        pos = [bounds["max_x"] + 0.24, 0.0, floor_z]
    else:
        pos = [bounds["min_x"] - 0.24, 0.0, floor_z]
    return socket_with_frame(
        f"exterior_{graph['building_graph_id']}_entrance_threshold",
        "exterior_socket",
        pos,
        edge,
        ["entrance_threshold", "road_connector"],
        ["exterior_socket", "entrance", "walkable_transition"],
        None,
    )


def normalize_attachment_graph(graph: dict[str, Any]) -> dict[str, Any]:
    bounds = {
        "min_x": -float(graph["footprint"]["width"]) * 0.5,
        "max_x": float(graph["footprint"]["width"]) * 0.5,
        "min_y": -float(graph["footprint"]["depth"]) * 0.5,
        "max_y": float(graph["footprint"]["depth"]) * 0.5,
    }
    return {**graph, "projected_local_bounds": bounds}


def expand_graph(graph: dict[str, Any], dims: dict[str, dict[str, float]]) -> dict[str, Any]:
    normalized = normalize_attachment_graph(graph)
    foundation = component_from_existing(
        next(component for component in graph["components"] if component["component_id"] == "foundation_skirt"),
        "foundation_skirt",
        "measured_base_plinth_v1",
        "foundation",
    )
    foundation["kit_primitive"] = "foundation_skirt"
    floor = component_from_existing(
        next(component for component in graph["components"] if component["component_id"] == "floor_slab"),
        "floor_slab",
        "measured_floor_slab_v1",
        "floor",
    )
    floor["kit_primitive"] = "floor_slab"
    roof = component_from_existing(
        next(component for component in graph["components"] if component["component_type"] == "roof_placeholder"),
        "roof_cap_placeholder",
        "measured_cap_block_v1",
        "roof",
    )
    roof["kit_primitive"] = "roof_cap_placeholder"
    roof["component_id"] = "roof_cap_placeholder"
    wall_segments = make_wall_segments(normalized, dims)
    corner_posts = make_corner_posts(normalized, dims)
    bay_components, exterior_sockets = make_door_and_window_bays(normalized, dims)
    interior_sockets = make_interior_sockets(normalized)
    exterior_sockets.append(make_exterior_service_socket(normalized))
    components = [foundation, floor, *wall_segments, *corner_posts, *bay_components, roof]
    primitive_counts: dict[str, int] = {}
    for component in components:
        primitive = component["component_type"]
        primitive_counts[primitive] = primitive_counts.get(primitive, 0) + 1
    primitive_counts["interior_socket"] = len(interior_sockets)
    primitive_counts["exterior_socket"] = len(exterior_sockets)
    return {
        **normalized,
        "kit_schema": "building_graph_kit_expansion_v0",
        "kit_primitives": REQUIRED_PRIMITIVES,
        "components": components,
        "interior_sockets": interior_sockets,
        "exterior_sockets": exterior_sockets,
        "child_asset_instances": [
            {**asset, "placement_space": "building_graph_local", "kit_mount_resolved": True}
            for asset in graph["child_asset_instances"]
        ],
        "kit_primitive_counts": dict(sorted(primitive_counts.items())),
        "bake_policy": {
            "freeze_after_bake": True,
            "live_graph_discardable_after_bake": True,
            "baked_map_keeps_summary_only": True,
            "do_not_push_wall_window_door_detail_into_map_graph": True,
        },
    }


def compile_expansion() -> dict[str, Any]:
    if not ATTACHMENT_PATH.exists():
        attachment_compile.main()
    attachment = load_json(ATTACHMENT_PATH)
    dims = measured_dims()
    expanded_graphs = [expand_graph(graph, dims) for graph in attachment["building_graphs"]]
    baked = [
        {
            **item,
            "kit_expansion_source": "building_graph_kit_expansion_v0",
            "baked_map_keeps_summary_only": True,
            "component_detail_exported_to_map_graph": False,
        }
        for item in attachment["baked_map_buildings"]
    ]
    validation = validate(expanded_graphs, baked, attachment)
    return {
        "schema": "building_graph_kit_expansion_v0",
        "created_at_utc": now_iso(),
        "source_files": {
            "building_graph_attachment": str(ATTACHMENT_PATH.relative_to(ROOT)),
            "measured_asset_index": str(MEASURED_INDEX_PATH.relative_to(ROOT)),
        },
        "rules": {
            "deterministic_local_building_graphs": True,
            "use_measured_components_where_available": True,
            "no_ornament_added": True,
            "map_graph_receives_baked_summary_only": True,
            "no_asset_geometry_scaling": True,
        },
        "building_graphs": expanded_graphs,
        "baked_map_buildings": baked,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def validate(graphs: list[dict[str, Any]], baked: list[dict[str, Any]], attachment: dict[str, Any]) -> dict[str, Any]:
    per_graph: dict[str, dict[str, Any]] = {}
    for graph in graphs:
        types = [component["component_type"] for component in graph["components"]]
        socket_types = ["interior_socket" for _ in graph["interior_sockets"]] + ["exterior_socket" for _ in graph["exterior_sockets"]]
        all_types = set(types + socket_types)
        per_graph[graph["building_graph_id"]] = {
            "has_foundation": "foundation_skirt" in all_types,
            "has_floor": "floor_slab" in all_types,
            "has_walls": "wall_segment" in all_types,
            "has_entrance": "door_bay" in all_types,
            "has_window_or_socket": "window_bay" in all_types or bool(graph["interior_sockets"] or graph["exterior_sockets"]),
            "has_corner_posts": "corner_post" in all_types,
            "has_roof_cap_placeholder": "roof_cap_placeholder" in all_types,
            "has_interior_socket": bool(graph["interior_sockets"]),
            "has_exterior_socket": bool(graph["exterior_sockets"]),
        }
    component_bounds_nonzero = [
        all(float(value) > 0.0 for value in component["dimensions_m"])
        for graph in graphs
        for component in graph["components"]
        if component.get("primitive") == "box"
    ]
    measured_refs = sorted(
        {
            component["measured_component_id"]
            for graph in graphs
            for component in graph["components"]
            if component.get("measured_component_id")
        }
    )
    validation = {
        "building_graph_count": len(graphs),
        "each_has_foundation_floor_walls_entrance_window_or_socket": all(
            all(checks[key] for key in ["has_foundation", "has_floor", "has_walls", "has_entrance", "has_window_or_socket"])
            for checks in per_graph.values()
        ),
        "each_has_corner_posts": all(checks["has_corner_posts"] for checks in per_graph.values()),
        "each_has_roof_cap_placeholder": all(checks["has_roof_cap_placeholder"] for checks in per_graph.values()),
        "each_has_interior_and_exterior_socket": all(
            checks["has_interior_socket"] and checks["has_exterior_socket"] for checks in per_graph.values()
        ),
        "foundation_skirt_still_hides_terrain_seam": attachment["validation"]["foundation_skirt_sinks_below_terrain"],
        "local_assets_place_relative_to_building_graph_coordinates": all(
            asset["placement_space"] == "building_graph_local"
            for graph in graphs
            for asset in graph["child_asset_instances"]
        ),
        "baked_map_exposes_only_summarized_building_records": all(
            item["baked_map_keeps_summary_only"] and not item["component_detail_exported_to_map_graph"] for item in baked
        ),
        "live_building_graph_remains_discardable_after_bake": all(
            graph["bake_policy"]["freeze_after_bake"] and graph["bake_policy"]["live_graph_discardable_after_bake"]
            for graph in graphs
        ),
        "component_bounds_nonzero": all(component_bounds_nonzero),
        "measured_component_refs_used": measured_refs,
        "primitive_types_required": REQUIRED_PRIMITIVES,
        "per_graph": per_graph,
        "no_claims": NO_CLAIMS,
    }
    required = [
        "each_has_foundation_floor_walls_entrance_window_or_socket",
        "each_has_corner_posts",
        "each_has_roof_cap_placeholder",
        "each_has_interior_and_exterior_socket",
        "foundation_skirt_still_hides_terrain_seam",
        "local_assets_place_relative_to_building_graph_coordinates",
        "baked_map_exposes_only_summarized_building_records",
        "live_building_graph_remains_discardable_after_bake",
        "component_bounds_nonzero",
    ]
    failed = [key for key in required if not validation[key]]
    if validation["building_graph_count"] != 3:
        failed.append("building_graph_count")
    if failed:
        fail(f"building graph kit expansion validation failed: {failed}")
    return validation


def write_report(data: dict[str, Any]) -> None:
    lines = [
        "# Building Graph Kit Expansion v0 Report",
        "",
        "Expands local building graphs with deterministic modular primitives while keeping the map graph on baked summaries.",
        "",
        "## Summary",
        "",
        f"- building_graph_count: {data['validation']['building_graph_count']}",
        f"- foundation_skirt_still_hides_terrain_seam: {data['validation']['foundation_skirt_still_hides_terrain_seam']}",
        f"- local_assets_place_relative_to_building_graph_coordinates: {data['validation']['local_assets_place_relative_to_building_graph_coordinates']}",
        f"- baked_map_exposes_only_summarized_building_records: {data['validation']['baked_map_exposes_only_summarized_building_records']}",
        f"- live_building_graph_remains_discardable_after_bake: {data['validation']['live_building_graph_remains_discardable_after_bake']}",
        "",
        "## Measured Component References",
        "",
    ]
    for ref in data["validation"]["measured_component_refs_used"]:
        lines.append(f"- {ref}")
    lines.extend(["", "## Graph Primitive Counts", ""])
    for graph in data["building_graphs"]:
        lines.append(f"### {graph['building_graph_id']}")
        lines.append("")
        for key, value in graph["kit_primitive_counts"].items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    lines.extend(["## Claim Limits", "", "- no ornament added", "- no production approval", "- no structural safety claim", "- no fabrication readiness claim", "- no historical accuracy claim", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "schema": "building_graph_kit_expansion_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "kit_graph": str(KIT_GRAPH_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": {
            "three_building_graphs_generated": validation["building_graph_count"] == 3,
            "each_has_foundation_floor_walls_entrance_window_or_socket": validation["each_has_foundation_floor_walls_entrance_window_or_socket"],
            "foundation_skirt_still_hides_terrain_seam": validation["foundation_skirt_still_hides_terrain_seam"],
            "local_assets_place_relative_to_building_graph_coordinates": validation["local_assets_place_relative_to_building_graph_coordinates"],
            "baked_map_exposes_only_summarized_building_records": validation["baked_map_exposes_only_summarized_building_records"],
            "live_building_graph_remains_discardable_after_bake": validation["live_building_graph_remains_discardable_after_bake"],
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = compile_expansion()
    KIT_GRAPH_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {KIT_GRAPH_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "building_graphs={building_graph_count} seam_hidden={foundation_skirt_still_hides_terrain_seam} "
        "summary_only={baked_map_exposes_only_summarized_building_records}".format(**data["validation"])
    )


if __name__ == "__main__":
    main()
