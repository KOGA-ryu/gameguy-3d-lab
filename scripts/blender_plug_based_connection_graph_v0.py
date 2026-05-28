#!/usr/bin/env python3
"""Render Plug-Based Connection Graph v0 proof scene."""

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
import compile_measured_asset_placement_v1 as measured_compile  # noqa: E402
import compile_plug_based_connection_graph_v0 as plug_compile  # noqa: E402


COMPILED_MAP_PATH = plug_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = plug_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = plug_compile.REFINED_GRAPH_PATH
GRAPH_PATH = plug_compile.GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "plug_based_connection_graph_v0.blend"
RENDER_PATH = OUT_DIR / "plug_based_connection_graph_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "plug_based_connection_graph_v0_topdown.png"
REPORT_PATH = OUT_DIR / "plug_based_connection_graph_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def add_variant_parent(graph: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(graph["placed_building_graph_id"], None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.7
    obj.matrix_world = attachment_render.frame_matrix(graph["origin"], graph["orientation_basis"])
    for key, value in {
        "building_graph_id": graph["placed_building_graph_id"],
        "placed_building_graph_id": graph["placed_building_graph_id"],
        "building_graph_variant_id": graph["building_graph_variant_id"],
        "map_variant_placement_id": graph["map_variant_placement_id"],
        "map_plot_id": graph["map_plot_id"],
        "variant_class": graph["variant_class"],
        "freeze_after_bake": True,
        "live_graph_discardable_after_bake": True,
        "no_ornament": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def make_plug_materials() -> dict[str, bpy.types.Material]:
    return {
        "building_entrance": map_render.make_material("plug_building_entrance", (0.02, 0.88, 0.28, 1.0)),
        "road_threshold": map_render.make_material("plug_road_threshold", (1.0, 0.82, 0.08, 1.0)),
        "road_endpoint": map_render.make_material("plug_road_endpoint", (0.95, 0.48, 0.08, 1.0)),
        "plot_access": map_render.make_material("plug_plot_access", (0.56, 0.25, 0.95, 1.0)),
        "connector_strip": map_render.make_material("plug_connector_strip", (0.06, 0.78, 0.95, 1.0)),
        "connector_centerline": map_render.make_material("plug_connector_centerline", (0.02, 0.08, 0.12, 1.0)),
        "union_vertical_envelope": map_render.make_material("plug_union_vertical_envelope", (0.02, 0.55, 0.78, 1.0)),
        "plug_direction": map_render.make_material("plug_direction_arrow", (0.04, 0.16, 0.22, 1.0)),
    }


def plug_material_key(plug: dict[str, Any]) -> str:
    if plug["owner_type"] == "building_graph":
        return "building_entrance"
    if plug["plug_type"] == "road_threshold":
        return "road_threshold"
    if plug["plug_type"] == "road_endpoint":
        return "road_endpoint"
    return "plot_access"


def add_plug_marker(plug: dict[str, Any], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    x, y, z = [float(value) for value in plug["position"]]
    radius = 0.3 if plug["owner_type"] == "building_graph" else 0.24
    debug_lift_m = 0.72
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=(x, y, z + debug_lift_m))
    obj = bpy.context.object
    obj.name = f"{plug['plug_id']}.plug_marker"
    obj.data.materials.append(materials[plug_material_key(plug)])
    for key, value in {
        "plug_id": plug["plug_id"],
        "owner_id": plug["owner_id"],
        "owner_type": plug["owner_type"],
        "plug_type": plug["plug_type"],
        "width_m": plug["width_m"],
        "clearance_m": plug["clearance_m"],
        "allowed_connection_types": ",".join(plug["allowed_connection_types"]),
        "priority": plug["priority"],
        "debug_lift_m": debug_lift_m,
    }.items():
        obj[key] = value

    dx, dy, _dz = [float(value) for value in plug["direction"]]
    points = [(x, y, z + debug_lift_m + 0.13), (x + dx * 0.62, y + dy * 0.62, z + debug_lift_m + 0.13)]
    map_render.make_curve(
        f"{plug['plug_id']}.plug_direction",
        points,
        0.035,
        materials["plug_direction"],
        {"plug_id": plug["plug_id"], "curve_role": "plug_direction"},
    )
    return obj


def normalize2(x: float, y: float) -> tuple[float, float]:
    length = (x * x + y * y) ** 0.5
    if length <= 1e-9:
        return (1.0, 0.0)
    return (x / length, y / length)


def add_connector_strip(path: dict[str, Any], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    points = [[float(value) for value in point] for point in path["route_points"]]
    start = points[0]
    end = points[-1]
    forward = normalize2(end[0] - start[0], end[1] - start[1])
    right = (-forward[1], forward[0])
    half_width = float(path["width_m"]) * 0.5
    debug_lift_m = 0.52
    vertices: list[tuple[float, float, float]] = []
    for x, y, z in points:
        vertices.append((x - right[0] * half_width, y - right[1] * half_width, z + debug_lift_m))
        vertices.append((x + right[0] * half_width, y + right[1] * half_width, z + debug_lift_m))
    faces = []
    for index in range(len(points) - 1):
        left_a = index * 2
        right_a = left_a + 1
        left_b = left_a + 2
        right_b = left_a + 3
        faces.append((left_a, left_b, right_b, right_a))
    mesh = bpy.data.meshes.new(f"{path['path_id']}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(path["path_id"], mesh)
    obj.data.materials.append(materials["connector_strip"])
    for key, value in {
        "path_id": path["path_id"],
        "route_policy": path["route_policy"],
        "surface": path["surface"],
        "width_m": path["width_m"],
        "horizontal_length_m": path["horizontal_length_m"],
        "slope": path["slope"],
        "debug_lift_m": debug_lift_m,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    centerline = [(x, y, z + debug_lift_m + 0.05) for x, y, z in points]
    map_render.make_curve(
        f"{path['path_id']}.centerline",
        centerline,
        0.025,
        materials["connector_centerline"],
        {"path_id": path["path_id"], "curve_role": "connector_centerline"},
    )
    return obj


def add_union_vertical_envelope(path: dict[str, Any], materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    if not path.get("door_measurement_rules_applied"):
        return []
    points = [[float(value) for value in point] for point in path["route_points"]]
    start = points[0]
    end = points[-1]
    forward = normalize2(end[0] - start[0], end[1] - start[1])
    right = (-forward[1], forward[0])
    half_width = float(path["width_m"]) * 0.5
    height = float(path["vertical_envelope_m"])
    created: list[bpy.types.Object] = []
    for index, (x, y, z) in enumerate(points):
        for side_name, side in (("left", -1.0), ("right", 1.0)):
            px = x + right[0] * half_width * side
            py = y + right[1] * half_width * side
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, z + height * 0.5))
            obj = bpy.context.object
            obj.name = f"{path['path_id']}.{side_name}_clearance_post_{index:02d}"
            obj.dimensions = (0.12, 0.12, height)
            obj.data.materials.append(materials["union_vertical_envelope"])
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            obj["path_id"] = path["path_id"]
            obj["debug_role"] = "union_vertical_envelope"
            obj["vertical_envelope_m"] = path["vertical_envelope_m"]
            obj["vertical_overbuild_margin_m"] = path["vertical_overbuild_margin_m"]
            obj["dimension_source"] = path["dimension_source"]
            created.append(obj)
    return created


def all_plugs(graph: dict[str, Any]) -> list[dict[str, Any]]:
    plug_sets = graph["plug_sets"]
    return plug_sets["building_entrance_plugs"] + plug_sets["road_plugs"] + plug_sets["plot_plugs"]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plug_compile.main()
    graph = load_json(GRAPH_PATH)
    compiled = load_json(COMPILED_MAP_PATH)
    recipes = measured_compile.load_measured_recipes()

    map_render.SEMANTIC_TERRAIN_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    map_render.REFINED_TERRAIN_GRAPH_PATH = REFINED_GRAPH_PATH
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    kit_mats = kit_render.make_materials()
    measured_mats = measured_render.make_measured_materials()
    plug_mats = make_plug_materials()
    map_assets.render_base_layers(compiled, terrain_mats)

    connector_objects = [add_connector_strip(path, plug_mats) for path in graph["generated_connector_paths"]]
    union_envelope_objects: list[bpy.types.Object] = []
    for path in graph["generated_connector_paths"]:
        union_envelope_objects.extend(add_union_vertical_envelope(path, plug_mats))
    plug_markers = [add_plug_marker(plug, plug_mats) for plug in all_plugs(graph)]

    created_components: list[bpy.types.Object] = []
    created_socket_markers: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    for placed_graph in graph["placed_building_graphs"]:
        parent = add_variant_parent(placed_graph)
        for component in placed_graph["components"]:
            created_components.append(attachment_render.add_component(component, kit_mats, parent))
        for socket in placed_graph["interior_sockets"]:
            created_socket_markers.append(kit_render.add_socket_marker(socket, kit_mats["interior_socket"], parent))
        for socket in placed_graph["exterior_sockets"]:
            created_socket_markers.append(kit_render.add_socket_marker(socket, kit_mats["exterior_socket"], parent))
        for socket in placed_graph["internal_asset_sockets"]:
            created_socket_markers.append(kit_render.add_socket_marker(socket, kit_mats["socket"], parent))
            if socket.get("measured_asset_id") in recipes:
                created_assets.extend(
                    attachment_render.add_measured_asset_under_building(
                        socket,
                        recipes[socket["measured_asset_id"]],
                        measured_mats,
                        parent,
                    )
                )

    map_render.add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    attachment_render.TOPDOWN_RENDER_PATH = TOPDOWN_RENDER_PATH
    attachment_render.render_topdown()

    report = {
        "schema": "plug_based_connection_graph_blender_report_v0",
        "source_connection_graph": str(GRAPH_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "building_entrance_plug_count": graph["validation"]["building_entrance_plug_count"],
        "road_plug_count": graph["validation"]["road_plug_count"],
        "plot_plug_count": graph["validation"]["plot_plug_count"],
        "connector_path_count": len(connector_objects),
        "building_union_connector_count": sum(
            1 for path in graph["generated_connector_paths"] if path.get("door_measurement_rules_applied")
        ),
        "union_vertical_envelope_marker_count": len(union_envelope_objects),
        "plug_marker_count": len(plug_markers),
        "socket_marker_count": len(created_socket_markers),
        "building_local_asset_instance_count": sum(1 for obj in created_assets if obj.type == "EMPTY"),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "curve_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE"),
        "acceptance": {
            "every_building_has_named_entrance_plugs": graph["validation"]["every_building_has_named_entrance_plugs"],
            "roads_expose_named_plug_candidates": graph["validation"]["roads_expose_named_plug_candidates"],
            "connections_are_declared_as_plug_pairs": graph["validation"]["connections_are_declared_as_plug_pairs"],
            "connection_type_is_configurable": graph["validation"]["connection_type_is_configurable"],
            "paths_generated_from_plug_contracts": graph["validation"]["paths_generated_from_plug_contracts"],
            "paths_validate_width_slope_clearance": graph["validation"]["paths_validate_width_slope_clearance"],
            "bad_connections_fail_with_reason": graph["validation"]["bad_connections_fail_with_reason"],
            "render_shows_plugs_and_connector_paths": bool(plug_markers) and bool(connector_objects),
            "building_union_uses_door_plug_contracts": graph["validation"]["building_union_uses_door_plug_contracts"],
            "building_union_records_length_and_elevation_gap": graph["validation"][
                "building_union_records_length_and_elevation_gap"
            ],
            "building_union_vertical_envelope_overbuilt": graph["validation"]["building_union_vertical_envelope_overbuilt"],
            "terrain_cracks_remain_zero": graph["validation"]["terrain_cracks_remain_zero"],
        },
        "no_claims": graph["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        "plugs={plug_marker_count} connectors={connector_path_count} meshes={mesh_object_count} curves={curve_object_count}".format(
            **report
        )
    )


if __name__ == "__main__":
    main()
