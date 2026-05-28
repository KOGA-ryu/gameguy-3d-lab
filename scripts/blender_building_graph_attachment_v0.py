#!/usr/bin/env python3
"""Render Building Graph Attachment v0 proof scene.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_building_graph_attachment_v0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import blender_measured_asset_placement_v1 as measured_render  # noqa: E402
import blender_tiled_map_template_asset_instances_v1 as map_assets  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402
import compile_building_graph_attachment_v0 as attachment_compile  # noqa: E402
import compile_measured_asset_placement_v1 as placement_compile  # noqa: E402


COMPILED_MAP_PATH = attachment_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = attachment_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = attachment_compile.REFINED_GRAPH_PATH
ATTACHMENT_PATH = attachment_compile.ATTACHMENT_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "building_graph_attachment_v0.blend"
RENDER_PATH = OUT_DIR / "building_graph_attachment_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "building_graph_attachment_v0_anchor_topdown.png"
REPORT_PATH = OUT_DIR / "building_graph_attachment_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def make_materials() -> dict[str, bpy.types.Material]:
    return {
        "foundation": map_render.make_material("building_graph_foundation_skirt", (0.22, 0.21, 0.19, 1.0)),
        "floor": map_render.make_material("building_graph_floor_slab", (0.43, 0.52, 0.38, 1.0)),
        "wall": map_render.make_material("building_graph_outer_wall", (0.58, 0.54, 0.46, 1.0)),
        "roof": map_render.make_material("building_graph_roof_placeholder", (0.30, 0.28, 0.25, 1.0)),
        "socket": map_render.make_material("building_graph_local_socket", (0.10, 0.58, 0.88, 1.0)),
        "entrance": map_render.make_material("building_graph_entrance_marker", (0.12, 0.82, 0.34, 1.0)),
    }


def frame_matrix(origin: list[float], basis: dict[str, list[float]]) -> mathutils.Matrix:
    right = [float(value) for value in basis["right"]]
    forward = [float(value) for value in basis["forward"]]
    up = [float(value) for value in basis["up"]]
    pos = [float(value) for value in origin]
    return mathutils.Matrix(
        (
            (right[0], forward[0], up[0], pos[0]),
            (right[1], forward[1], up[1], pos[1]),
            (right[2], forward[2], up[2], pos[2]),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def local_frame_matrix(position: list[float], frame: dict[str, list[float]]) -> mathutils.Matrix:
    right = [float(value) for value in frame["right"]]
    forward = [float(value) for value in frame["forward"]]
    up = [float(value) for value in frame["up"]]
    pos = [float(value) for value in position]
    return mathutils.Matrix(
        (
            (right[0], forward[0], up[0], pos[0]),
            (right[1], forward[1], up[1], pos[1]),
            (right[2], forward[2], up[2], pos[2]),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def add_building_parent(graph: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(graph["building_graph_id"], None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.65
    obj.matrix_world = frame_matrix(graph["origin"], graph["orientation_basis"])
    for key, value in {
        "building_graph_id": graph["building_graph_id"],
        "attach_socket_id": graph["attach_socket_id"],
        "attach_plot_id": graph["attach_plot_id"],
        "orientation": graph["orientation"],
        "base_offset_m": graph["base_offset_m"],
        "foundation_overlap_m": graph["foundation_overlap_m"],
        "freeze_after_bake": graph["freeze_after_bake"],
        "live_graph_discardable_after_bake": graph["live_graph_discardable_after_bake"],
        "no_structural_claims": True,
        "no_production_approval": True,
        "no_fabrication_claims": True,
        "no_historical_accuracy_claim": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_component(component: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    loc = tuple(float(value) for value in component["local_center_m"])
    dims = tuple(float(value) for value in component["dimensions_m"])
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = f"{parent.name}.{component['component_id']}"
    obj.dimensions = dims
    obj.data.materials.append(materials[component["material_role"]])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["building_graph_id"] = parent["building_graph_id"]
    obj["component_id"] = component["component_id"]
    obj["component_type"] = component["component_type"]
    obj["semantic_tags"] = ",".join(component["semantic_tags"])
    if component["component_id"] == "foundation_skirt":
        obj["skirt_sinks_below_terrain"] = bool(component["skirt_sinks_below_terrain"])
        obj["bottom_world_z_m"] = float(component["bottom_world_z_m"])
        obj["terrain_contact_z_m"] = float(component["terrain_contact_z_m"])
    return obj


def add_local_socket_marker(socket: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.09, location=tuple(socket["local_position_m"]))
    obj = bpy.context.object
    obj.name = f"{parent.name}.{socket['socket_id']}.marker"
    obj.data.materials.append(materials["socket"])
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["building_graph_id"] = parent["building_graph_id"]
    obj["source_map_socket_id"] = socket["source_map_socket_id"]
    obj["placement_space"] = socket["placement_space"]
    return obj


def add_asset_parent(socket: dict[str, Any], building_parent: bpy.types.Object) -> bpy.types.Object:
    obj = bpy.data.objects.new(f"{building_parent.name}.{socket['source_map_socket_id']}.{socket['measured_asset_id']}", None)
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.28
    obj.parent = building_parent
    obj.matrix_parent_inverse.identity()
    obj.matrix_local = local_frame_matrix(socket["local_position_m"], socket["local_frame"])
    for key, value in {
        "building_graph_id": building_parent["building_graph_id"],
        "socket_id": socket["source_map_socket_id"],
        "source_map_socket_id": socket["source_map_socket_id"],
        "measured_asset_id": socket["measured_asset_id"],
        "placement_space": socket["placement_space"],
        "asset_placement_status": socket["asset_placement_status"],
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_measured_asset_under_building(
    socket: dict[str, Any],
    recipe: dict[str, Any],
    measured_materials: dict[str, bpy.types.Material],
    building_parent: bpy.types.Object,
) -> list[bpy.types.Object]:
    parent = add_asset_parent(socket, building_parent)
    created: list[bpy.types.Object] = [parent]
    for part in recipe["proof_primitives"]:
        if part["primitive"] == "cube":
            created.append(measured_render.add_cube(part, measured_materials, parent))
        elif part["primitive"] == "cylinder":
            created.append(measured_render.add_cylinder(part, measured_materials, parent))
        elif part["primitive"] == "curve":
            created.append(measured_render.add_curve(part, measured_materials, parent))
        else:
            raise ValueError(f"{recipe['asset_id']} unsupported primitive {part['primitive']}")
    created.extend(measured_render.add_socket_markers(recipe, measured_materials, parent))
    return created


def scene_bounds() -> tuple[float, float, float, float, float, float]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    if not objs:
        return (-16.0, -16.0, 0.0, 16.0, 16.0, 8.0)
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for obj in objs:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(float(world.x))
            ys.append(float(world.y))
            zs.append(float(world.z))
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def render_topdown() -> None:
    min_x, min_y, _min_z, max_x, max_y, max_z = scene_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.camera_add(location=(center_x, center_y, max_z + 30.0), rotation=(0.0, 0.0, 0.0))
    cam = bpy.context.object
    cam.name = "building_graph_attachment_topdown_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.08
    direction = mathutils.Vector((center_x, center_y, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(TOPDOWN_RENDER_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not ATTACHMENT_PATH.exists():
        attachment_compile.main()
    compiled = load_json(COMPILED_MAP_PATH)
    attachment = load_json(ATTACHMENT_PATH)
    recipes = placement_compile.load_measured_recipes()

    map_render.SEMANTIC_TERRAIN_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    map_render.REFINED_TERRAIN_GRAPH_PATH = REFINED_GRAPH_PATH
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    building_mats = make_materials()
    measured_mats = measured_render.make_measured_materials()
    map_assets.render_base_layers(compiled, terrain_mats)

    created_components: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    for graph in attachment["building_graphs"]:
        parent = add_building_parent(graph)
        for component in graph["components"]:
            created_components.append(add_component(component, building_mats, parent))
        for socket in graph["internal_asset_sockets"]:
            add_local_socket_marker(socket, building_mats, parent)
            recipe = recipes[socket["measured_asset_id"]]
            created_assets.extend(add_measured_asset_under_building(socket, recipe, measured_mats, parent))

    map_render.add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    render_topdown()

    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    building_empty_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "EMPTY" and obj.get("building_graph_id"))
    asset_instance_count = sum(
        1
        for obj in created_assets
        if obj.type == "EMPTY" and str(obj.get("placement_space")) == "building_graph_local"
    )
    report = {
        "schema": "building_graph_attachment_blender_report_v0",
        "source_attachment_file": str(ATTACHMENT_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "building_graph_count": attachment["validation"]["building_graph_count"],
        "baked_building_count": attachment["validation"]["baked_building_count"],
        "foundation_skirt_sinks_below_terrain": attachment["validation"]["foundation_skirt_sinks_below_terrain"],
        "building_assets_place_relative_to_building_graph": attachment["validation"]["building_assets_place_relative_to_building_graph"],
        "map_graph_sees_final_building_contract_only": attachment["validation"]["map_graph_sees_final_building_contract_only"],
        "baked_output_can_discard_live_building_graph": attachment["validation"]["baked_output_can_discard_live_building_graph"],
        "component_object_count": len(created_components),
        "building_local_asset_instance_count": asset_instance_count,
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "building_empty_count": building_empty_count,
        "every_building_has_visible_components": all(
            any(obj.get("building_graph_id") == graph["building_graph_id"] for obj in created_components)
            for graph in attachment["building_graphs"]
        ),
        "no_claims": attachment["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        "building_graphs={building_graph_count} local_assets={building_local_asset_instance_count} "
        "meshes={mesh_object_count} curves={curve_object_count}".format(**report)
    )


if __name__ == "__main__":
    main()
