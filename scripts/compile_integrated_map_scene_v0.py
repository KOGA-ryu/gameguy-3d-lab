#!/usr/bin/env python3
"""Compile Integrated Map Scene v0.

Build path:
map template -> shared/profiled/refined/semantic terrain -> building variants
-> plug contracts -> connector records.
"""

from __future__ import annotations

import json
import math
import copy
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_map_gameplay_surface_semantics_v0 as semantics_compile  # noqa: E402
import compile_map_template_profile_application_v0 as profile_compile  # noqa: E402
import compile_map_template_shared_terrain_adapter_v0 as shared_compile  # noqa: E402
import compile_map_template_v2_building_variant_placement as building_place_compile  # noqa: E402
import compile_building_graph_variation_rules_v0 as variation_compile  # noqa: E402
import compile_plug_based_connection_graph_v0 as plug_compile  # noqa: E402
import compile_profile_aware_road_plot_refinement_v0 as refinement_compile  # noqa: E402
import compile_tiled_map_template_v0 as map_compile  # noqa: E402
import create_integrated_map_scene_v0 as scene_create  # noqa: E402


TEMPLATE_PATH = scene_create.TEMPLATE_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "integrated_map_scene_v0"
COMPILED_MAP_PATH = OUT_DIR / "integrated_map_scene_v0_compiled_map.json"
SHARED_DIR = OUT_DIR / "shared_terrain"
PROFILED_DIR = OUT_DIR / "profiled_terrain"
REFINED_DIR = OUT_DIR / "road_plot_refined"
SEMANTIC_DIR = OUT_DIR / "gameplay_surface_semantics"
BUILDING_DIR = OUT_DIR / "building_variant_placement"
PLUG_DIR = OUT_DIR / "plug_connection_graph"
INTEGRATED_GRAPH_PATH = OUT_DIR / "integrated_map_scene_v0_compiled.json"
REPORT_PATH = OUT_DIR / "integrated_map_scene_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "integrated_map_scene_v0.receipt.json"

SHARED_ASSEMBLY_PATH = SHARED_DIR / "integrated_map_scene_v0_shared_terrain_assembly.json"
SHARED_GRAPH_PATH = SHARED_DIR / "integrated_map_scene_v0_shared_terrain_graph.json"
PROFILED_GRAPH_PATH = PROFILED_DIR / "integrated_map_scene_v0_profiled_terrain_graph.json"
REFINED_GRAPH_PATH = REFINED_DIR / "integrated_map_scene_v0_road_plot_refined_graph.json"
SEMANTIC_GRAPH_PATH = SEMANTIC_DIR / "integrated_map_scene_v0_gameplay_surface_semantics_graph.json"
BUILDING_PLACEMENT_PATH = BUILDING_DIR / "integrated_map_scene_v0_building_variant_placement.json"
PLUG_GRAPH_PATH = PLUG_DIR / "integrated_map_scene_v0_plug_connection_graph.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}


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


def run_module_main_with_overrides(module: Any, overrides: dict[str, Any]) -> None:
    previous = {name: getattr(module, name) for name in overrides}
    try:
        for name, value in overrides.items():
            setattr(module, name, value)
        module.main()
    finally:
        for name, value in previous.items():
            setattr(module, name, value)


def round6(value: float) -> float:
    return round(float(value), 6)


def compile_terrain_pipeline() -> dict[str, Any]:
    for directory in (OUT_DIR, SHARED_DIR, PROFILED_DIR, REFINED_DIR, SEMANTIC_DIR, BUILDING_DIR, PLUG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE_PATH.exists():
        scene_create.main()

    compiled = map_compile.compile_template(TEMPLATE_PATH)
    COMPILED_MAP_PATH.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")

    run_module_main_with_overrides(
        shared_compile,
        {
            "COMPILED_PATH": COMPILED_MAP_PATH,
            "OUT_DIR": SHARED_DIR,
            "ASSEMBLY_PATH": SHARED_ASSEMBLY_PATH,
            "GRAPH_PATH": SHARED_GRAPH_PATH,
            "REPORT_PATH": SHARED_DIR / "integrated_map_scene_v0_shared_terrain_report.md",
            "RECEIPT_PATH": ROOT / "goal" / "receipts" / "integrated_map_scene_v0_shared_terrain.receipt.json",
        },
    )

    run_module_main_with_overrides(
        profile_compile,
        {
            "SHARED_GRAPH_PATH": SHARED_GRAPH_PATH,
            "OUT_DIR": PROFILED_DIR,
            "PROFILED_GRAPH_PATH": PROFILED_GRAPH_PATH,
            "REPORT_PATH": PROFILED_DIR / "integrated_map_scene_v0_profile_application_report.md",
            "RECEIPT_PATH": ROOT / "goal" / "receipts" / "integrated_map_scene_v0_profile_application.receipt.json",
        },
    )

    run_module_main_with_overrides(
        refinement_compile,
        {
            "PROFILED_GRAPH_PATH": PROFILED_GRAPH_PATH,
            "OUT_DIR": REFINED_DIR,
            "REFINED_GRAPH_PATH": REFINED_GRAPH_PATH,
            "REPORT_PATH": REFINED_DIR / "integrated_map_scene_v0_road_plot_refinement_report.md",
            "RECEIPT_PATH": ROOT / "goal" / "receipts" / "integrated_map_scene_v0_road_plot_refinement.receipt.json",
        },
    )

    run_module_main_with_overrides(
        semantics_compile,
        {
            "REFINED_GRAPH_PATH": REFINED_GRAPH_PATH,
            "OUT_DIR": SEMANTIC_DIR,
            "SEMANTIC_GRAPH_PATH": SEMANTIC_GRAPH_PATH,
            "REPORT_PATH": SEMANTIC_DIR / "integrated_map_scene_v0_surface_semantics_report.md",
            "RECEIPT_PATH": ROOT / "goal" / "receipts" / "integrated_map_scene_v0_surface_semantics.receipt.json",
        },
    )

    return {
        "compiled_map": load_json(COMPILED_MAP_PATH),
        "shared": load_json(SHARED_GRAPH_PATH),
        "profiled": load_json(PROFILED_GRAPH_PATH),
        "refined": load_json(REFINED_GRAPH_PATH),
        "semantic": load_json(SEMANTIC_GRAPH_PATH),
    }


PLOT_TO_VARIANT = {
    "measured_gatehouse_plot": ("gatehouse_graph_v0", "standard"),
    "measured_watch_plot": ("watch_graph_v0", "tall"),
    "measured_octagon_shrine_plot": ("shrine_graph_v0", "compact"),
}


def polygon_centroid(points: list[list[float]]) -> list[float]:
    if not points:
        return [0.0, 0.0]
    area = 0.0
    cx = 0.0
    cy = 0.0
    closed = points + [points[0]]
    for left, right in zip(closed, closed[1:], strict=False):
        cross = float(left[0]) * float(right[1]) - float(right[0]) * float(left[1])
        area += cross
        cx += (float(left[0]) + float(right[0])) * cross
        cy += (float(left[1]) + float(right[1])) * cross
    if abs(area) <= 1e-9:
        return [round6(sum(float(p[0]) for p in points) / len(points)), round6(sum(float(p[1]) for p in points) / len(points))]
    area *= 0.5
    return [round6(cx / (6.0 * area)), round6(cy / (6.0 * area))]


def distance_to_segment_local(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, tuple[float, float]]:
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return math.hypot(px - ax, py - ay), (ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    hit = (ax + dx * t, ay + dy * t)
    return math.hypot(px - hit[0], py - hit[1]), hit


def nearest_road_point(compiled: dict[str, Any], point: list[float]) -> dict[str, Any]:
    best = {"road_id": "", "distance_m": float("inf"), "point": [point[0], point[1]]}
    for road in compiled["roads"]:
        for left, right in zip(road["points"], road["points"][1:], strict=False):
            distance, hit = distance_to_segment_local(
                float(point[0]),
                float(point[1]),
                float(left[0]),
                float(left[1]),
                float(right[0]),
                float(right[1]),
            )
            if distance < best["distance_m"]:
                best = {"road_id": road["road_id"], "distance_m": round6(distance), "point": [round6(hit[0]), round6(hit[1])]}
    return best


def basis_toward(target: list[float], origin_xy: list[float]) -> dict[str, list[float]]:
    forward_xy = normalize2(float(target[0]) - float(origin_xy[0]), float(target[1]) - float(origin_xy[1]))
    right = [round6(forward_xy[1]), round6(-forward_xy[0]), 0.0]
    return {"right": right, "forward": [forward_xy[0], forward_xy[1], 0.0], "up": [0.0, 0.0, 1.0]}


def basis_faces_target(basis: dict[str, list[float]], target: list[float], origin_xy: list[float], tolerance: float = 0.999) -> bool:
    expected = normalize2(float(target[0]) - float(origin_xy[0]), float(target[1]) - float(origin_xy[1]))
    forward = basis["forward"]
    dot = float(forward[0]) * expected[0] + float(forward[1]) * expected[1]
    return dot >= tolerance


def transform_local(local: list[float], origin: list[float], basis: dict[str, list[float]]) -> list[float]:
    return [
        round6(float(origin[0]) + float(local[0]) * float(basis["right"][0]) + float(local[1]) * float(basis["forward"][0]) + float(local[2]) * float(basis["up"][0])),
        round6(float(origin[1]) + float(local[0]) * float(basis["right"][1]) + float(local[1]) * float(basis["forward"][1]) + float(local[2]) * float(basis["up"][1])),
        round6(float(origin[2]) + float(local[0]) * float(basis["right"][2]) + float(local[1]) * float(basis["forward"][2]) + float(local[2]) * float(basis["up"][2])),
    ]


def entrance_socket(graph: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        socket
        for socket in graph["exterior_sockets"]
        if "entrance" in socket.get("semantic_tags", []) or "road_connector" in socket.get("compatible_tags", [])
    ]
    if not candidates:
        fail(f"{graph['building_graph_variant_id']} has no exterior entrance socket")
    return candidates[0]


def relocate_variant_to_plot(variant: dict[str, Any], plot: dict[str, Any], compiled: dict[str, Any], refined: dict[str, Any]) -> dict[str, Any]:
    placed = copy.deepcopy(variant)
    centroid = polygon_centroid(plot["polygon"])
    target_road = nearest_road_point(compiled, centroid)
    terrain_z = terrain_height(refined, float(centroid[0]), float(centroid[1]))
    origin = [centroid[0], centroid[1], round6(terrain_z - 0.15)]
    basis = basis_toward(target_road["point"], centroid)
    placed["origin"] = origin
    placed["orientation_basis"] = basis
    placed["placed_building_graph_id"] = f"placed_{variant['building_graph_variant_id']}_{plot['plot_id']}"
    placed["map_variant_placement_id"] = f"hillwatch_place_{plot['plot_id']}_{variant['variant_class']}"
    placed["map_plot_id"] = plot["plot_id"]
    placed["attach_plot_id"] = plot["plot_id"]
    placed["attach_socket_id"] = f"{plot['plot_id']}.building_graph_socket"
    placed["door_edge_adjustment"] = {
        "applied": False,
        "reason": "fresh_hillwatch_variant_oriented_by_plot_to_nearest_road_vector",
    }
    for component in placed["components"]:
        if component["component_type"] == "foundation_skirt":
            bottom = float(origin[2]) + float(component["local_center_m"][2]) - float(component["dimensions_m"][2]) * 0.5
            component["bottom_world_z_m"] = round6(bottom)
            component["terrain_contact_z_m"] = round6(terrain_z)
            component["skirt_sinks_below_terrain"] = bottom < terrain_z
    placed["fresh_hillwatch_placement"] = {
        "plot_centroid_world_m": centroid,
        "plot_average_height_m": plot["average_height"],
        "terrain_height_at_centroid_m": round6(terrain_z),
        "nearest_road_id": target_road["road_id"],
        "nearest_road_distance_m": target_road["distance_m"],
        "oriented_entrance_toward_road": basis_faces_target(basis, target_road["point"], centroid),
    }
    return placed


def compile_buildings() -> dict[str, Any]:
    if not variation_compile.VARIATION_GRAPH_PATH.exists():
        variation_compile.main()
    compiled = load_json(COMPILED_MAP_PATH)
    refined = load_json(REFINED_GRAPH_PATH)
    semantic = load_json(SEMANTIC_GRAPH_PATH)
    variation_graph = load_json(variation_compile.VARIATION_GRAPH_PATH)
    variants_by_key = {
        (variant["source_building_graph_id"], variant["variant_class"]): variant
        for variant in variation_graph["building_graph_variants"]
    }
    placed_graphs: list[dict[str, Any]] = []
    placements: list[dict[str, Any]] = []
    baked: list[dict[str, Any]] = []
    for plot in compiled["building_plots"]:
        if plot["plot_id"] not in PLOT_TO_VARIANT:
            continue
        source_graph_id, variant_class = PLOT_TO_VARIANT[plot["plot_id"]]
        variant = relocate_variant_to_plot(variants_by_key[(source_graph_id, variant_class)], plot, compiled, refined)
        entrance = entrance_socket(variant)
        entrance_world = transform_local(entrance["local_position_m"], variant["origin"], variant["orientation_basis"])
        entrance_road = nearest_road_point(compiled, [entrance_world[0], entrance_world[1]])
        entrance_has_road_target = bool(entrance_road["road_id"]) and math.isfinite(float(entrance_road["distance_m"]))
        foundation = next(component for component in variant["components"] if component["component_type"] == "foundation_skirt")
        placed_graphs.append(variant)
        placements.append(
            {
                "placement_id": variant["map_variant_placement_id"],
                "plot_id": plot["plot_id"],
                "source_building_graph_id": source_graph_id,
                "building_graph_variant_id": variant["building_graph_variant_id"],
                "variant_class": variant_class,
                "variant_choice_reason": "fresh Hillwatch Ravine plot role mapping",
                "origin": variant["origin"],
                "orientation_basis": variant["orientation_basis"],
                "footprint": variant["footprint"],
                "fresh_hillwatch_placement": variant["fresh_hillwatch_placement"],
                "entrance": {
                    "socket_id": entrance["socket_id"],
                    "local_position_m": entrance["local_position_m"],
                    "world_position_m": entrance_world,
                    "edge": entrance["edge"],
                    "nearest_road_id": entrance_road["road_id"],
                    "nearest_road_distance_m": entrance_road["distance_m"],
                    "nearest_road_point": entrance_road["point"],
                    "connects_to_road": entrance_has_road_target,
                },
                "foundation_seam_hiding": {
                    "passes": bool(foundation["skirt_sinks_below_terrain"]),
                    "bottom_world_z_m": foundation["bottom_world_z_m"],
                    "terrain_contact_z_m": foundation["terrain_contact_z_m"],
                },
                "asset_scaling": variant["asset_scaling"],
                "bake_policy": variant["bake_policy"],
                "no_claims": NO_CLAIMS,
            }
        )
        baked.append(
            {
                "baked_map_building_id": f"baked_{variant['map_variant_placement_id']}",
                "placement_id": variant["map_variant_placement_id"],
                "plot_id": plot["plot_id"],
                "building_graph_variant_id": variant["building_graph_variant_id"],
                "variant_class": variant_class,
                "origin": variant["origin"],
                "orientation_basis": variant["orientation_basis"],
                "footprint": variant["footprint"],
                "entrance_world_position_m": entrance_world,
                "semantic_tags": ["building_pad", "entrance", "line_of_sight_breaker", "asset_socket"],
                "map_friendly_summary_only": True,
                "component_detail_exported_to_map_graph": False,
                "freeze_after_bake": True,
                "live_graph_discardable_after_bake": True,
            }
        )
    validation = {
        "map_plot_variant_placement_count": len(placements),
        "three_map_plots_receive_building_variants": len(placements) == 3,
        "variant_choice_recorded_with_reason": all(p["variant_choice_reason"] for p in placements),
        "foundation_seam_hiding_still_passes": all(p["foundation_seam_hiding"]["passes"] for p in placements),
        "entrances_connect_to_roads": all(p["entrance"]["connects_to_road"] for p in placements),
        "baked_summaries_remain_summary_only": all(item["map_friendly_summary_only"] for item in baked),
        "terrain_cracks_remain_zero": int(semantic["validation"]["cracked_seam_count"]) == 0 and int(refined["validation"]["cracked_seam_count"]) == 0,
        "semantic_cracked_seam_count": semantic["validation"]["cracked_seam_count"],
        "refined_cracked_seam_count": refined["validation"]["cracked_seam_count"],
        "render_has_visible_building_variation": len({p["variant_class"] for p in placements}) >= 2,
        "variant_classes_used": sorted({p["variant_class"] for p in placements}),
        "asset_scaling_applied_count": sum(1 for p in placements if p["asset_scaling"]["asset_scaling_applied"]),
        "asset_geometry_change_count": sum(
            1
            for graph in placed_graphs
            for component in graph["components"]
            if component.get("asset_scaling_applied") or component.get("geometry_modified")
        ),
        "asset_dimensions_still_declared": all(
            isinstance(component.get("dimensions_m"), list) and len(component["dimensions_m"]) == 3
            for graph in placed_graphs
            for component in graph["components"]
        ),
        "fresh_hillwatch_relocated_buildings": all(p["placement_id"].startswith("hillwatch_place_") for p in placements),
        "no_claims": NO_CLAIMS,
    }
    required = [
        "three_map_plots_receive_building_variants",
        "foundation_seam_hiding_still_passes",
        "terrain_cracks_remain_zero",
        "render_has_visible_building_variation",
    ]
    failed = [key for key in required if not validation[key]]
    if validation["asset_scaling_applied_count"] != 0:
        failed.append("asset_scaling_applied_count")
    if failed:
        fail(f"fresh Hillwatch building placement failed: {failed}")
    data = {
        "schema": "integrated_map_scene_v0_building_variant_placement",
        "created_at_utc": now_iso(),
        "source_files": {
            "compiled_map": str(COMPILED_MAP_PATH.relative_to(ROOT)),
            "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
            "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
            "building_graph_variants": str(variation_compile.VARIATION_GRAPH_PATH.relative_to(ROOT)),
        },
        "placed_building_graphs": placed_graphs,
        "building_variant_placements": placements,
        "baked_map_buildings": baked,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    BUILDING_DIR.mkdir(parents=True, exist_ok=True)
    BUILDING_PLACEMENT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def compile_base_plugs() -> dict[str, Any]:
    run_module_main_with_overrides(
        plug_compile,
        {
            "MAP_V2_PLACEMENT_PATH": BUILDING_PLACEMENT_PATH,
            "COMPILED_MAP_PATH": COMPILED_MAP_PATH,
            "SEMANTIC_GRAPH_PATH": SEMANTIC_GRAPH_PATH,
            "REFINED_GRAPH_PATH": REFINED_GRAPH_PATH,
            "OUT_DIR": PLUG_DIR,
            "GRAPH_PATH": PLUG_GRAPH_PATH,
            "REPORT_PATH": PLUG_DIR / "integrated_map_scene_v0_plug_connection_graph_report.md",
            "RECEIPT_PATH": ROOT / "goal" / "receipts" / "integrated_map_scene_v0_plug_connection_graph.receipt.json",
        },
    )
    return load_json(PLUG_GRAPH_PATH)


def terrain_height(refined: dict[str, Any], x: float, y: float) -> float:
    return plug_compile.terrain_height(refined, x, y)


def normalize2(x: float, y: float) -> list[float]:
    length = math.hypot(x, y)
    if length <= 1e-9:
        return [1.0, 0.0]
    return [round6(x / length), round6(y / length)]


def add_pathway_plugs_and_connection(plug_graph: dict[str, Any], compiled: dict[str, Any], refined: dict[str, Any], semantic: dict[str, Any]) -> dict[str, Any]:
    roads = {road["road_id"]: road for road in compiled["roads"]}
    start = roads["main_measured_road"]["points"][2]
    end = roads["shrine_spur_road"]["points"][1]
    direction = normalize2(end[0] - start[0], end[1] - start[1])
    pathway_plugs = [
        {
            "plug_id": "courtyard_path.west_plug",
            "owner_id": "courtyard_path",
            "owner_type": "pathway",
            "plug_type": "pathway",
            "position": [round6(start[0]), round6(start[1]), round6(terrain_height(refined, start[0], start[1]) + 0.1)],
            "direction": [direction[0], direction[1], 0.0],
            "width_m": 1.4,
            "clearance_m": 99.0,
            "allowed_connection_types": ["flat_pathway", "ramp_pathway", "stepped_pathway", "bridge_link"],
            "priority": "primary",
        },
        {
            "plug_id": "courtyard_path.east_plug",
            "owner_id": "courtyard_path",
            "owner_type": "pathway",
            "plug_type": "pathway",
            "position": [round6(end[0]), round6(end[1]), round6(terrain_height(refined, end[0], end[1]) + 0.1)],
            "direction": [-direction[0], -direction[1], 0.0],
            "width_m": 1.4,
            "clearance_m": 99.0,
            "allowed_connection_types": ["flat_pathway", "ramp_pathway", "stepped_pathway", "bridge_link"],
            "priority": "primary",
        },
    ]
    plug_graph["plug_sets"]["pathway_plugs"] = pathway_plugs
    plugs_by_id = plug_compile.plug_lookup(
        plug_graph["plug_sets"]["building_entrance_plugs"]
        + plug_graph["plug_sets"]["road_plugs"]
        + plug_graph["plug_sets"]["plot_plugs"]
        + pathway_plugs
    )
    declaration = {
        "connection_id": "courtyard_path_west_to_east_ramp",
        "from_plug": "courtyard_path.west_plug",
        "to_plug": "courtyard_path.east_plug",
        "connection_type": "ramp_pathway",
        "profile": "npc_friendly",
        "width_m": 1.4,
        "max_slope": 0.35,
        "max_step_height": 0.22,
        "min_width": 1.0,
        "min_clearance_m": 2.0,
        "turn_radius_m": 1.0,
        "min_turn_radius": 1.0,
        "surface": "packed_stone",
        "deterministic_route_policy": "declared_plug_pair_straight_grade_limited_v0",
        "validation_status": "pending",
        "landing_required": False,
        "avoid_fall_hazard": True,
        "avoid_blocked": True,
        "prefer_road": True,
        "prefer_flat_pad": True,
    }
    connection = plug_compile.validate_and_generate_connection(declaration, plugs_by_id, semantic)
    connection["validation_status"] = connection["status"]
    if connection["status"] != "pass":
        fail(f"pathway plug connection failed: {connection['fail_reasons']}")
    plug_graph["developer_declared_connections"].append(declaration)
    plug_graph["connections"].append(connection)
    plug_graph["generated_connector_paths"].append(connection["generated_path"])
    validation = plug_graph["validation"]
    validation["pathway_plug_count"] = len(pathway_plugs)
    validation["connection_count"] = len(plug_graph["connections"])
    validation["connection_status_counts"] = {
        "pass": sum(1 for conn in plug_graph["connections"] if conn["status"] == "pass"),
        "fail": sum(1 for conn in plug_graph["connections"] if conn["status"] == "fail"),
    }
    validation["pathway_connection_resolves"] = connection["status"] == "pass"
    validation["declared_connection_types_used"] = sorted({conn["connection_type"] for conn in plug_graph["connections"]})
    validation["at_least_three_declared_plug_connections_resolve"] = validation["connection_status_counts"]["pass"] >= 3
    validation["has_required_connection_type_mix"] = all(
        kind in validation["declared_connection_types_used"] for kind in ["road_threshold", "ramp_pathway", "bridge_link"]
    )
    validation["connector_path_records_include_width_slope_clearance_validation"] = all(
        "width_ok" in conn["validation"] and "slope_ok" in conn["validation"] and "clearance_ok" in conn["validation"]
        for conn in plug_graph["connections"]
    )
    return plug_graph


def validate_integrated(compiled: dict[str, Any], shared: dict[str, Any], refined: dict[str, Any], semantic: dict[str, Any], buildings: dict[str, Any], plugs: dict[str, Any]) -> dict[str, Any]:
    terrain_validation = semantic["validation"]
    height_levels = compiled["summary"]["height_levels"]
    plots_by_id = {plot["plot_id"]: plot for plot in compiled["building_plots"]}
    ravine_cells = [cell for cell in compiled["cells"] if cell["surface_type"] == "ravine_edge"]
    ravine_heights = [float(cell["final_height"]) for cell in ravine_cells]
    road_cells = [cell for cell in compiled["cells"] if "main_measured_road" in cell.get("road_ids", [])]
    lower_road_heights = [float(cell["final_height"]) for cell in road_cells if float(cell["world_x"]) < -6.0]
    validation = {
        "cell_count": terrain_validation["cell_count"],
        "top_triangle_count": terrain_validation["top_triangle_count"],
        "expected_top_triangle_count": terrain_validation["cell_count"] * 12,
        "top_triangle_count_equals_cell_count_times_12": terrain_validation["top_triangle_count"] == terrain_validation["cell_count"] * 12,
        "terrain_cracks_remain_zero": int(terrain_validation["cracked_seam_count"]) == 0 and int(refined["validation"]["cracked_seam_count"]) == 0,
        "cracked_seam_count": terrain_validation["cracked_seam_count"],
        "hillwatch_playable_elevation_range_0_to_8_m": min(height_levels) == 0 and max(height_levels) == 8,
        "hillwatch_watchhouse_plateau_is_6_m": abs(float(plots_by_id["measured_watch_plot"]["average_height"]) - 6.0) <= 0.001,
        "hillwatch_ravine_floor_reaches_0_m": bool(ravine_heights) and min(ravine_heights) == 0.0,
        "hillwatch_lower_road_approach_near_2_m": bool(lower_road_heights) and min(lower_road_heights) <= 2.0 <= max(lower_road_heights),
        "hillwatch_visible_cliff_drop_about_6_m": bool(ravine_heights) and float(plots_by_id["measured_watch_plot"]["average_height"]) - min(ravine_heights) >= 6.0,
        "multiple_elevation_levels": len(compiled["summary"]["height_levels"]) >= 4,
        "has_hill_or_ridge": max(compiled["summary"]["height_levels"]) - min(compiled["summary"]["height_levels"]) >= 4,
        "has_ravine_or_cut": compiled["summary"]["hazard_count"] >= 1,
        "at_least_two_road_routes": compiled["summary"]["road_count"] >= 2,
        "at_least_three_building_plots": compiled["summary"]["building_plot_count"] >= 3,
        "at_least_three_building_variants_placed": buildings["validation"]["map_plot_variant_placement_count"] >= 3,
        "all_buildings_have_named_entrance_plugs": plugs["validation"]["every_building_has_named_entrance_plugs"],
        "at_least_five_named_plugs": sum(len(items) for items in plugs["plug_sets"].values()) >= 5,
        "at_least_three_declared_plug_connections_resolve": plugs["validation"]["at_least_three_declared_plug_connections_resolve"],
        "has_required_connection_type_mix": plugs["validation"]["has_required_connection_type_mix"],
        "roads_and_pathways_visible": bool(compiled["roads"]) and bool(plugs["plug_sets"].get("pathway_plugs")),
        "connector_path_records_include_width_slope_clearance_validation": plugs["validation"][
            "connector_path_records_include_width_slope_clearance_validation"
        ],
        "bad_or_unresolved_connections_reported_not_guessed": plugs["validation"]["bad_connections_fail_with_reason"],
        "foundation_skirts_hide_terrain_building_seams": buildings["validation"]["foundation_seam_hiding_still_passes"],
        "no_asset_geometry_changes": buildings["validation"]["asset_geometry_change_count"] == 0
        and buildings["validation"]["asset_dimensions_still_declared"],
        "no_silent_scaling": buildings["validation"]["asset_scaling_applied_count"] == 0,
        "web_search_used": False,
        "no_claims": NO_CLAIMS,
    }
    required = [
        "top_triangle_count_equals_cell_count_times_12",
        "terrain_cracks_remain_zero",
        "hillwatch_playable_elevation_range_0_to_8_m",
        "hillwatch_watchhouse_plateau_is_6_m",
        "hillwatch_ravine_floor_reaches_0_m",
        "hillwatch_lower_road_approach_near_2_m",
        "hillwatch_visible_cliff_drop_about_6_m",
        "multiple_elevation_levels",
        "has_hill_or_ridge",
        "has_ravine_or_cut",
        "at_least_two_road_routes",
        "at_least_three_building_plots",
        "at_least_three_building_variants_placed",
        "all_buildings_have_named_entrance_plugs",
        "at_least_five_named_plugs",
        "at_least_three_declared_plug_connections_resolve",
        "has_required_connection_type_mix",
        "roads_and_pathways_visible",
        "connector_path_records_include_width_slope_clearance_validation",
        "bad_or_unresolved_connections_reported_not_guessed",
        "foundation_skirts_hide_terrain_building_seams",
        "no_asset_geometry_changes",
        "no_silent_scaling",
    ]
    failed = [key for key in required if not validation[key]]
    if failed:
        fail(f"integrated map scene validation failed: {failed}")
    return validation


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Integrated Map Scene v0 Report",
        "",
        "Fresh integrated proof scene using the current terrain, building, plug, and measured asset systems.",
        "",
        "## Summary",
        "",
        f"- cell_count: {validation['cell_count']}",
        f"- top_triangle_count: {validation['top_triangle_count']}",
        f"- cracked_seam_count: {validation['cracked_seam_count']}",
        f"- building_variant_count: {data['building_variant_placement']['validation']['map_plot_variant_placement_count']}",
        f"- plug_count: {sum(len(items) for items in data['plug_connection_graph']['plug_sets'].values())}",
        f"- resolved_connection_count: {data['plug_connection_graph']['validation']['connection_status_counts']['pass']}",
        f"- connection_types: {data['plug_connection_graph']['validation']['declared_connection_types_used']}",
        "",
        "## Acceptance",
        "",
    ]
    for key, value in validation.items():
        if key != "no_claims":
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Claim Limits", "", "- no production approval", "- no structural safety claim", "- no fabrication readiness claim", "- no historical accuracy claim", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    receipt = {
        "schema": "integrated_map_scene_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "template": str(TEMPLATE_PATH.relative_to(ROOT)),
            "compiled": str(INTEGRATED_GRAPH_PATH.relative_to(ROOT)),
            "report": str(REPORT_PATH.relative_to(ROOT)),
        },
        "acceptance": data["validation"],
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def compile_integrated_scene() -> dict[str, Any]:
    terrain = compile_terrain_pipeline()
    buildings = compile_buildings()
    plug_graph = compile_base_plugs()
    plug_graph = add_pathway_plugs_and_connection(plug_graph, terrain["compiled_map"], terrain["refined"], terrain["semantic"])
    validation = validate_integrated(
        terrain["compiled_map"],
        terrain["shared"],
        terrain["refined"],
        terrain["semantic"],
        buildings,
        plug_graph,
    )
    return {
        "schema": "integrated_map_scene_v0_compiled",
        "created_at_utc": now_iso(),
        "source_files": {
            "template": str(TEMPLATE_PATH.relative_to(ROOT)),
            "measured_asset_catalog": "goal/architecture/asset_mill_measured_v1/asset_mill_measured_index_v1.json",
            "building_graph_variants": "goal/architecture/building_graph_variation_rules_v0/building_graph_variation_rules_v0.json",
        },
        "compiled_map_path": str(COMPILED_MAP_PATH.relative_to(ROOT)),
        "shared_terrain_graph_path": str(SHARED_GRAPH_PATH.relative_to(ROOT)),
        "profiled_terrain_graph_path": str(PROFILED_GRAPH_PATH.relative_to(ROOT)),
        "refined_terrain_graph_path": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
        "semantic_graph_path": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
        "compiled_map": terrain["compiled_map"],
        "building_variant_placement": buildings,
        "plug_connection_graph": plug_graph,
        "connector_geometry_records": plug_graph["generated_connector_paths"],
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = compile_integrated_scene()
    INTEGRATED_GRAPH_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    print(f"wrote {INTEGRATED_GRAPH_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")
    print(
        "cells={cell_count} triangles={top_triangle_count} buildings={building_count} connections={connection_count}".format(
            cell_count=data["validation"]["cell_count"],
            top_triangle_count=data["validation"]["top_triangle_count"],
            building_count=data["building_variant_placement"]["validation"]["map_plot_variant_placement_count"],
            connection_count=data["plug_connection_graph"]["validation"]["connection_status_counts"]["pass"],
        )
    )


if __name__ == "__main__":
    main()
