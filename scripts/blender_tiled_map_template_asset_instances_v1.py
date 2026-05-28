#!/usr/bin/env python3
"""Render a Tiled-style map template with real asset-kit instances.

This is the second map-template proof: the map compiler places actual blockout
asset builders at authored sockets instead of showing blue/yellow proxy markers.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_tiled_map_template_asset_instances_v1.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import blender_arch_bay_kit_v1 as arch_bay  # noqa: E402
import blender_architectural_asset_batch_v0 as asset_batch  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402


COMPILED_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "compiled" / "tiled_hex_map_template_v0_compiled.json"
ARCH_BAY_RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "arch_bay_kit_v1.json"
ASSET_BATCH_RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "architectural_asset_batch_v0.json"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "map_gameplay_surface_semantics_asset_instances_v0.blend"
RENDER_PATH = OUT_DIR / "map_gameplay_surface_semantics_asset_instances_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "map_gameplay_surface_semantics_asset_instances_v0_anchor_topdown.png"
REPORT_PATH = OUT_DIR / "map_gameplay_surface_semantics_asset_instances_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def make_arch_bay_materials() -> dict[str, bpy.types.Material]:
    return {
        "stone": map_render.make_material("map_arch_warm_wall_stone", (0.55, 0.51, 0.42, 1.0)),
        "dark": map_render.make_material("map_arch_dark_foundation", (0.32, 0.31, 0.28, 1.0)),
        "stone_gold": map_render.make_material("map_arch_limestone_column", (0.72, 0.64, 0.42, 1.0)),
        "rib": map_render.make_material("map_arch_rib", (0.82, 0.74, 0.52, 1.0)),
        "cap": map_render.make_material("map_arch_capstone", (0.66, 0.62, 0.52, 1.0)),
        "floor": map_render.make_material("map_arch_threshold_floor", (0.30, 0.58, 0.38, 1.0)),
        "shadow": map_render.make_material("map_arch_recess_shadow", (0.20, 0.20, 0.18, 1.0)),
    }


def make_asset_batch_materials() -> dict[str, bpy.types.Material]:
    return {
        "stone": map_render.make_material("map_batch_warm_stone", (0.55, 0.51, 0.42, 1.0)),
        "stone_dark": map_render.make_material("map_batch_dark_stone", (0.36, 0.35, 0.31, 1.0)),
        "stone_gold": map_render.make_material("map_batch_old_limestone", (0.72, 0.64, 0.41, 1.0)),
        "rib": map_render.make_material("map_batch_rib_highlight", (0.84, 0.74, 0.48, 1.0)),
        "barrier": map_render.make_material("map_batch_blue_barrier", (0.28, 0.48, 0.64, 1.0)),
        "walkable": map_render.make_material("map_batch_green_walkable", (0.30, 0.58, 0.38, 1.0)),
        "recess": map_render.make_material("map_batch_recess_shadow", (0.24, 0.23, 0.21, 1.0)),
    }


def make_terrain_materials() -> dict[str, bpy.types.Material]:
    return {
        "grass": map_render.make_material("mat_asset_scene_terrain_grass", (0.23, 0.48, 0.29, 1.0)),
        "road": map_render.make_material("mat_asset_scene_road_stone", (0.48, 0.43, 0.35, 1.0)),
        "stone": map_render.make_material("mat_asset_scene_high_stone", (0.52, 0.51, 0.47, 1.0)),
        "ravine_edge": map_render.make_material("mat_asset_scene_ravine_hazard", (0.42, 0.20, 0.16, 1.0)),
        "building_plot": map_render.make_material("mat_asset_scene_building_plot", (0.62, 0.54, 0.35, 1.0)),
        "side_wall": map_render.make_material("mat_asset_scene_exposed_side_wall", (0.34, 0.32, 0.28, 1.0)),
        "boundary_wall": map_render.make_material("mat_asset_scene_chunk_boundary_wall", (0.22, 0.22, 0.20, 1.0)),
        "semantic_walkable": map_render.make_material("mat_asset_semantic_walkable", (0.30, 0.62, 0.34, 1.0)),
        "semantic_blocked": map_render.make_material("mat_asset_semantic_blocked", (0.28, 0.12, 0.12, 1.0)),
        "semantic_road": map_render.make_material("mat_asset_semantic_road", (0.72, 0.62, 0.30, 1.0)),
        "semantic_building_pad": map_render.make_material("mat_asset_semantic_building_pad", (0.86, 0.72, 0.36, 1.0)),
        "semantic_foundation_edge": map_render.make_material("mat_asset_semantic_foundation_edge", (0.95, 0.55, 0.22, 1.0)),
        "semantic_retaining_edge": map_render.make_material("mat_asset_semantic_retaining_edge", (0.62, 0.24, 0.16, 1.0)),
        "semantic_ledge": map_render.make_material("mat_asset_semantic_ledge", (0.44, 0.36, 0.72, 1.0)),
        "semantic_cliff": map_render.make_material("mat_asset_semantic_cliff", (0.18, 0.18, 0.18, 1.0)),
        "semantic_slope": map_render.make_material("mat_asset_semantic_slope", (0.52, 0.70, 0.34, 1.0)),
        "semantic_choke": map_render.make_material("mat_asset_semantic_choke", (0.82, 0.28, 0.78, 1.0)),
        "semantic_cover_candidate": map_render.make_material("mat_asset_semantic_cover_candidate", (0.22, 0.48, 0.76, 1.0)),
        "semantic_fall_hazard": map_render.make_material("mat_asset_semantic_fall_hazard", (0.88, 0.16, 0.12, 1.0)),
        "semantic_los_breaker": map_render.make_material("mat_asset_semantic_los_breaker", (0.08, 0.10, 0.12, 1.0)),
        "semantic_asset_socket": map_render.make_material("mat_asset_semantic_asset_socket", (0.20, 0.74, 0.82, 1.0)),
        "road_overlay": map_render.make_material("mat_asset_scene_road_overlay", (0.72, 0.67, 0.48, 1.0)),
        "hazard_overlay": map_render.make_material("mat_asset_scene_hazard_overlay", (0.86, 0.20, 0.12, 1.0)),
        "plot_pad": map_render.make_material("mat_asset_scene_plot_pad", (0.78, 0.60, 0.28, 1.0)),
        "anchor_pass": map_render.make_material("mat_anchor_footprint_pass", (0.14, 0.72, 0.36, 1.0)),
        "anchor_warn": map_render.make_material("mat_anchor_footprint_warn", (0.95, 0.72, 0.16, 1.0)),
        "anchor_reject": map_render.make_material("mat_anchor_footprint_reject", (0.95, 0.16, 0.10, 1.0)),
        "anchor_arrow": map_render.make_material("mat_anchor_forward_arrow", (0.08, 0.18, 0.26, 1.0)),
    }


def recipe_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for recipe_path, source_kind in ((ARCH_BAY_RECIPE, "arch_bay_kit_v1"), (ASSET_BATCH_RECIPE, "architectural_asset_batch_v0")):
        recipe = load_json(recipe_path)
        for asset in recipe["assets"]:
            lookup[asset["asset_id"]] = {
                "asset_id": asset["asset_id"],
                "builder_kind": asset["builder_kind"],
                "architectural_role": asset["architectural_role"],
                "semantic_tags": asset["semantic_tags"],
                "source_kind": source_kind,
            }
    return lookup


def add_asset_parent(socket: dict[str, Any], asset: dict[str, Any]) -> bpy.types.Object:
    x, y, z = [float(v) for v in socket["world_position"]]
    frame = socket.get("anchor_frame", {})
    obj = bpy.data.objects.new(f"{socket['socket_id']}.{asset['asset_id']}", None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.35
    obj.location = (x, y, z + 0.12)
    obj.rotation_euler = (0.0, 0.0, math.radians(float(socket.get("orientation_degrees", 0.0))))
    obj.scale = (0.86, 0.86, 0.86)
    for key, value in {
        "socket_id": socket["socket_id"],
        "asset_ref": asset["asset_id"],
        "builder_kind": asset["builder_kind"],
        "source_kind": asset["source_kind"],
        "architectural_role": asset["architectural_role"],
        "semantic_tags": ",".join(asset["semantic_tags"]),
        "surface_height_source": str(frame.get("profiled_surface_source", socket.get("profiled_surface_source", ""))),
        "surface_normal_rule": str(frame.get("surface_normal_rule", socket.get("surface_normal_rule", ""))),
        "surface_forward": ",".join(str(round(float(v), 6)) for v in frame.get("forward", [])),
        "surface_right": ",".join(str(round(float(v), 6)) for v in frame.get("right", [])),
        "surface_up": ",".join(str(round(float(v), 6)) for v in frame.get("up", [])),
        "no_structural_claims": True,
        "no_production_approval": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def instantiate_asset(
    socket: dict[str, Any],
    asset: dict[str, Any],
    arch_mats: dict[str, bpy.types.Material],
    batch_mats: dict[str, bpy.types.Material],
) -> bool:
    parent = add_asset_parent(socket, asset)
    if asset["source_kind"] == "arch_bay_kit_v1":
        builder = arch_bay.BUILDERS.get(asset["builder_kind"])
        if builder is None:
            return False
        builder(parent, arch_mats)
        return True
    builder = asset_batch.BUILDERS.get(asset["builder_kind"])
    if builder is None:
        return False
    builder(parent, batch_mats)
    return True


def scene_mesh_bounds() -> tuple[float, float, float, float, float, float]:
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not mesh_objects:
        return (-16.0, -16.0, 0.0, 16.0, 16.0, 8.0)
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for obj in mesh_objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(float(world.x))
            ys.append(float(world.y))
            zs.append(float(world.z))
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def render_topdown_diagnostics() -> None:
    min_x, min_y, _min_z, max_x, max_y, max_z = scene_mesh_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.camera_add(location=(center_x, center_y, max_z + 28.0), rotation=(0.0, 0.0, 0.0))
    cam = bpy.context.object
    cam.name = "anchor_topdown_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.08
    direction = mathutils.Vector((center_x, center_y, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(TOPDOWN_RENDER_PATH)
    bpy.ops.render.render(write_still=True)


def render_base_layers(compiled: dict[str, Any], materials: dict[str, bpy.types.Material]) -> None:
    map_render.make_terrain_mesh(compiled, materials)
    for road in compiled["roads"]:
        points = []
        for x, y in road["points"]:
            z = map_render.nearest_cell_height(compiled, float(x), float(y)) + 0.09
            points.append((float(x), float(y), z))
        map_render.make_curve(
            f"{road['road_id']}.road_overlay",
            points,
            float(road["width_m"]) * 0.18,
            materials["road_overlay"],
            {"curve_role": "road_overlay", "road_id": road["road_id"]},
        )
    for hazard in compiled["hazards"]:
        points = []
        for x, y in hazard["points"]:
            z = map_render.nearest_cell_height(compiled, float(x), float(y)) + 0.16
            points.append((float(x), float(y), z))
        map_render.make_curve(
            f"{hazard['hazard_id']}.hazard_edge_overlay",
            points,
            0.08,
            materials["hazard_overlay"],
            {"curve_role": "hazard_edge", "hazard_id": hazard["hazard_id"], "hazard_type": hazard["hazard_type"]},
        )
    for plot in compiled["building_plots"]:
        map_render.make_plot_pad(plot, materials["plot_pad"])


def active_asset_sockets(compiled: dict[str, Any], graph: dict[str, Any] | None) -> list[dict[str, Any]]:
    if graph is not None and graph.get("map_template_overlays", {}).get("asset_sockets"):
        return graph["map_template_overlays"]["asset_sockets"]
    return compiled["asset_sockets"]


def add_anchor_diagnostics(socket: dict[str, Any], materials: dict[str, bpy.types.Material]) -> int:
    frame = socket.get("anchor_frame")
    if not isinstance(frame, dict):
        return 0
    status = socket.get("placement_validation", {}).get("status", "warn")
    mat = materials.get(f"anchor_{status}", materials["anchor_warn"])
    position = [float(v) for v in frame["position"]]
    forward = [float(v) for v in frame["forward"][:2]]
    right = [float(v) for v in frame["right"][:2]]
    footprint = frame["footprint"]
    half_w = float(footprint["width_m"]) * 0.5
    half_d = float(footprint["depth_m"]) * 0.5
    z = position[2] + 0.075
    cx, cy = position[0], position[1]
    vertices = [
        (cx - right[0] * half_w - forward[0] * half_d, cy - right[1] * half_w - forward[1] * half_d, z),
        (cx + right[0] * half_w - forward[0] * half_d, cy + right[1] * half_w - forward[1] * half_d, z),
        (cx + right[0] * half_w + forward[0] * half_d, cy + right[1] * half_w + forward[1] * half_d, z),
        (cx - right[0] * half_w + forward[0] * half_d, cy - right[1] * half_w + forward[1] * half_d, z),
    ]
    map_render.make_mesh_object(
        f"{socket['socket_id']}.anchor_footprint_{status}",
        vertices,
        [(0, 1, 2, 3)],
        [mat],
        [0],
        {
            "mesh_role": "anchor_footprint",
            "socket_id": socket["socket_id"],
            "anchor_kind": frame["anchor_kind"],
            "placement_status": status,
            "parent_feature_id": str(frame.get("parent_feature_id", "")),
        },
    )
    arrow_start = (cx, cy, z + 0.04)
    arrow_end = (cx + forward[0] * max(0.65, half_d * 1.6), cy + forward[1] * max(0.65, half_d * 1.6), z + 0.04)
    map_render.make_curve(
        f"{socket['socket_id']}.anchor_forward",
        [arrow_start, arrow_end],
        0.025,
        materials["anchor_arrow"],
        {
            "curve_role": "anchor_forward_direction",
            "socket_id": socket["socket_id"],
            "anchor_kind": frame["anchor_kind"],
        },
    )
    return 2


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    map_render.clear_scene()
    compiled = load_json(COMPILED_PATH)
    graph = map_render.shared_terrain_graph()
    asset_sockets = active_asset_sockets(compiled, graph)
    terrain_mats = make_terrain_materials()
    arch_mats = make_arch_bay_materials()
    batch_mats = make_asset_batch_materials()
    assets = recipe_lookup()

    render_base_layers(compiled, terrain_mats)
    anchor_diagnostic_count = 0
    for socket in asset_sockets:
        anchor_diagnostic_count += add_anchor_diagnostics(socket, terrain_mats)

    placed: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for socket in asset_sockets:
        asset_ref = socket.get("asset_ref")
        asset = assets.get(asset_ref)
        if asset is None:
            missing.append({"socket_id": socket["socket_id"], "asset_ref": asset_ref, "reason": "unknown_asset_ref"})
            continue
        if instantiate_asset(socket, asset, arch_mats, batch_mats):
            placed.append(
                {
                    "socket_id": socket["socket_id"],
                    "asset_ref": asset_ref,
                    "source_kind": asset["source_kind"],
                    "builder_kind": asset["builder_kind"],
                    "world_position": socket["world_position"],
                    "orientation_degrees": socket["orientation_degrees"],
                    "anchor_kind": socket.get("anchor_kind"),
                    "anchor_status": socket.get("placement_validation", {}).get("status"),
                    "parent_feature_id": socket.get("anchor_frame", {}).get("parent_feature_id"),
                }
            )
        else:
            missing.append({"socket_id": socket["socket_id"], "asset_ref": asset_ref, "reason": "missing_builder"})

    map_render.add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    render_topdown_diagnostics()

    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    empty_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "EMPTY")
    anchor_status_counts: dict[str, int] = {}
    for socket in asset_sockets:
        status = socket.get("placement_validation", {}).get("status", "missing")
        anchor_status_counts[status] = anchor_status_counts.get(status, 0) + 1
    report = {
        "schema": "tiled_map_template_asset_instances_report_v1",
        "source_compiled_map": str(COMPILED_PATH.relative_to(ROOT)),
        "active_terrain_graph": str(map_render.active_terrain_graph_path().relative_to(ROOT)) if graph is not None else None,
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_anchor_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "terrain_validation": map_render.terrain_validation_for_report(graph),
        "asset_socket_count": len(asset_sockets),
        "placed_asset_count": len(placed),
        "missing_asset_count": len(missing),
        "placed_assets": placed,
        "missing_assets": missing,
        "anchor_status_counts": dict(sorted(anchor_status_counts.items())),
        "anchor_diagnostic_object_count": anchor_diagnostic_count,
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "empty_object_count": empty_count,
        "rules": {
            "real_asset_kit_instances": True,
            "shared_midpoint_radial_terrain_mesh": graph is not None,
            "gameplay_surface_semantics_graph": bool(graph and graph.get("schema") == "map_gameplay_surface_semantics_graph_v0"),
            "semantic_debug_coloring": bool(graph and graph.get("map_gameplay_surface_semantics_v0")),
            "profile_aware_road_plot_refinement_graph": bool(graph and graph.get("schema") == "profile_aware_road_plot_refined_graph_v0"),
            "profiled_terrain_graph": bool(graph and graph.get("schema") == "map_template_profiled_terrain_graph_v0"),
            "top_triangle_count_equals_cell_count_times_12": bool(graph and graph.get("profile_validation", graph.get("validation", {})).get("top_triangle_count_matches")),
            "cracked_seam_count_is_zero": bool(graph and graph.get("profile_validation", graph.get("validation", {})).get("cracked_seam_count") == 0),
            "debug_render_only": True,
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"placed_assets={len(placed)} missing_assets={len(missing)} meshes={mesh_count} curves={curve_count} empties={empty_count}")


if __name__ == "__main__":
    main()
