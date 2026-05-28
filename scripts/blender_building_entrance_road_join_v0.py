#!/usr/bin/env python3
"""Render Building Entrance And Road Join v0 proof scene."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import bpy


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import blender_building_graph_attachment_v0 as attachment_render  # noqa: E402
import blender_building_graph_kit_expansion_v0 as kit_render  # noqa: E402
import blender_measured_asset_placement_v1 as measured_render  # noqa: E402
import blender_tiled_map_template_asset_instances_v1 as map_assets  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402
import compile_building_entrance_road_join_v0 as join_compile  # noqa: E402
import compile_measured_asset_placement_v1 as measured_compile  # noqa: E402


COMPILED_MAP_PATH = join_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = join_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = join_compile.REFINED_GRAPH_PATH
JOIN_GRAPH_PATH = join_compile.JOIN_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "building_entrance_road_join_v0.blend"
RENDER_PATH = OUT_DIR / "building_entrance_road_join_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "building_entrance_road_join_v0_topdown.png"
REPORT_PATH = OUT_DIR / "building_entrance_road_join_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def add_join_parent(graph: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(graph["placed_building_graph_id"], None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.7
    obj.matrix_world = attachment_render.frame_matrix(graph["origin"], graph["orientation_basis"])
    join = graph["entrance_road_join"]
    for key, value in {
        "building_graph_id": graph["placed_building_graph_id"],
        "placed_building_graph_id": graph["placed_building_graph_id"],
        "building_graph_variant_id": graph["building_graph_variant_id"],
        "map_variant_placement_id": graph["map_variant_placement_id"],
        "map_plot_id": graph["map_plot_id"],
        "variant_class": graph["variant_class"],
        "selected_entrance_edge": join["selected_entrance_edge"],
        "road_join_rule": join["selection_rule"],
        "road_to_door_distance_m": join["road_to_door_distance_m"],
        "freeze_after_bake": True,
        "live_graph_discardable_after_bake": True,
        "no_ornament": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_threshold_connector(connector: dict[str, Any], material: bpy.types.Material) -> bpy.types.Object:
    points = connector["polyline_world_m"]
    right = connector["connector_right_world_xy"]
    half_width = float(connector["width_m"]) * 0.5
    vertices: list[tuple[float, float, float]] = []
    for x, y, z in points:
        rx = float(right[0]) * half_width
        ry = float(right[1]) * half_width
        vertices.append((float(x) - rx, float(y) - ry, float(z) + 0.09))
        vertices.append((float(x) + rx, float(y) + ry, float(z) + 0.09))
    faces = []
    for index in range(len(points) - 1):
        left_a = index * 2
        right_a = left_a + 1
        left_b = left_a + 2
        right_b = left_a + 3
        faces.append((left_a, left_b, right_b, right_a))
    mesh = bpy.data.meshes.new(f"{connector['connector_id']}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(connector["connector_id"], mesh)
    obj.data.materials.append(material)
    for key, value in {
        "connector_type": connector["connector_type"],
        "building_graph_id": connector["building_graph_id"],
        "nearest_road_id": connector["nearest_road"]["road_id"],
        "road_to_door_distance_m": connector["length_m"],
        "landing_width_m": connector["landing_width_m"],
        "landing_depth_m": connector["landing_depth_m"],
        "doorway_faces_road_direction": connector["doorway_faces_road_direction"],
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_landing_pad(connector: dict[str, Any], material: bpy.types.Material) -> bpy.types.Object:
    start = [float(value) for value in connector["landing_inner_world_m"]]
    outer = [float(value) for value in connector["landing_outer_world_m"]]
    right = [float(value) for value in connector["connector_right_world_xy"]]
    half_width = float(connector["landing_width_m"]) * 0.5
    z_lift = 0.095
    vertices = [
        (start[0] - right[0] * half_width, start[1] - right[1] * half_width, start[2] + z_lift),
        (start[0] + right[0] * half_width, start[1] + right[1] * half_width, start[2] + z_lift),
        (outer[0] + right[0] * half_width, outer[1] + right[1] * half_width, outer[2] + z_lift),
        (outer[0] - right[0] * half_width, outer[1] - right[1] * half_width, outer[2] + z_lift),
    ]
    mesh = bpy.data.meshes.new(f"{connector['connector_id']}_landing_mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(f"{connector['connector_id']}.landing_pad", mesh)
    obj.data.materials.append(material)
    obj["connector_type"] = "threshold_landing_pad"
    obj["building_graph_id"] = connector["building_graph_id"]
    obj["nearest_road_id"] = connector["nearest_road"]["road_id"]
    obj["landing_width_m"] = connector["landing_width_m"]
    obj["landing_depth_m"] = connector["landing_depth_m"]
    bpy.context.collection.objects.link(obj)
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not JOIN_GRAPH_PATH.exists():
        join_compile.main()
    join = load_json(JOIN_GRAPH_PATH)
    compiled = load_json(COMPILED_MAP_PATH)
    recipes = measured_compile.load_measured_recipes()

    map_render.SEMANTIC_TERRAIN_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    map_render.REFINED_TERRAIN_GRAPH_PATH = REFINED_GRAPH_PATH
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    kit_mats = kit_render.make_materials()
    measured_mats = measured_render.make_measured_materials()
    threshold_mat = map_render.make_material("entrance_road_join_threshold_connector", (0.88, 0.76, 0.46, 1.0))
    landing_mat = map_render.make_material("entrance_road_join_landing_pad", (0.94, 0.82, 0.52, 1.0))
    map_assets.render_base_layers(compiled, terrain_mats)

    connector_objects = []
    for connector in join["threshold_connectors"]:
        connector_objects.append(add_threshold_connector(connector, threshold_mat))
        connector_objects.append(add_landing_pad(connector, landing_mat))
    created_components: list[bpy.types.Object] = []
    created_socket_markers: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    for graph in join["placed_building_graphs"]:
        parent = add_join_parent(graph)
        for component in graph["components"]:
            created_components.append(attachment_render.add_component(component, kit_mats, parent))
        for socket in graph["interior_sockets"]:
            created_socket_markers.append(kit_render.add_socket_marker(socket, kit_mats["interior_socket"], parent))
        for socket in graph["exterior_sockets"]:
            created_socket_markers.append(kit_render.add_socket_marker(socket, kit_mats["exterior_socket"], parent))
        for socket in graph["internal_asset_sockets"]:
            created_socket_markers.append(kit_render.add_socket_marker(socket, kit_mats["socket"], parent))
            if socket.get("measured_asset_id") in recipes:
                created_assets.extend(
                    attachment_render.add_measured_asset_under_building(socket, recipes[socket["measured_asset_id"]], measured_mats, parent)
                )

    map_render.add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    attachment_render.TOPDOWN_RENDER_PATH = TOPDOWN_RENDER_PATH
    attachment_render.render_topdown()

    component_counts: dict[str, int] = {}
    for obj in created_components:
        kind = str(obj.get("component_type"))
        component_counts[kind] = component_counts.get(kind, 0) + 1
    report = {
        "schema": "building_entrance_road_join_blender_report_v0",
        "source_join_graph": str(JOIN_GRAPH_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "building_count": join["validation"]["building_count"],
        "component_counts": dict(sorted(component_counts.items())),
        "threshold_connector_count": len(connector_objects),
        "socket_marker_count": len(created_socket_markers),
        "building_local_asset_instance_count": sum(1 for obj in created_assets if obj.type == "EMPTY"),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "curve_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE"),
        "acceptance": {
            "every_building_selects_entrance_edge_from_nearest_road_or_spur": join["validation"][
                "every_building_selects_entrance_edge_from_nearest_road_or_spur"
            ],
            "entrance_edge_changes_are_rule_driven_not_special_cased": join["validation"][
                "entrance_edge_changes_are_rule_driven_not_special_cased"
            ],
            "each_entrance_gets_threshold_landing_connector": join["validation"]["each_entrance_gets_threshold_landing_connector"],
            "doorway_faces_road_direction": join["validation"]["doorway_faces_road_direction"],
            "all_entrances_stay_connected": join["validation"]["all_entrances_stay_connected"],
            "foundation_seam_hiding_remains_valid": join["validation"]["foundation_seam_hiding_remains_valid"],
            "terrain_cracks_remain_zero": join["validation"]["terrain_cracks_remain_zero"],
        },
        "no_claims": join["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        "buildings={building_count} connectors={threshold_connector_count} meshes={mesh_object_count} curves={curve_object_count}".format(
            **report
        )
    )


if __name__ == "__main__":
    main()
