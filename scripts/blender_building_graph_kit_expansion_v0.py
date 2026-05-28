#!/usr/bin/env python3
"""Render Building Graph Kit Expansion v0 proof scene."""

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
import blender_measured_asset_placement_v1 as measured_render  # noqa: E402
import blender_tiled_map_template_asset_instances_v1 as map_assets  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402
import compile_building_graph_attachment_v0 as attachment_compile  # noqa: E402
import compile_building_graph_kit_expansion_v0 as kit_compile  # noqa: E402
import compile_measured_asset_placement_v1 as placement_compile  # noqa: E402


COMPILED_MAP_PATH = attachment_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = attachment_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = attachment_compile.REFINED_GRAPH_PATH
KIT_GRAPH_PATH = kit_compile.KIT_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "building_graph_kit_expansion_v0.blend"
RENDER_PATH = OUT_DIR / "building_graph_kit_expansion_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "building_graph_kit_expansion_v0_anchor_topdown.png"
REPORT_PATH = OUT_DIR / "building_graph_kit_expansion_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def make_materials() -> dict[str, bpy.types.Material]:
    return {
        "foundation": map_render.make_material("kit_foundation_skirt", (0.18, 0.17, 0.15, 1.0)),
        "floor": map_render.make_material("kit_floor_slab", (0.40, 0.50, 0.38, 1.0)),
        "wall": map_render.make_material("kit_wall_segment", (0.56, 0.53, 0.46, 1.0)),
        "post": map_render.make_material("kit_corner_post", (0.68, 0.61, 0.46, 1.0)),
        "door_bay": map_render.make_material("kit_door_bay", (0.34, 0.48, 0.38, 1.0)),
        "window_bay": map_render.make_material("kit_window_bay", (0.32, 0.48, 0.62, 1.0)),
        "roof": map_render.make_material("kit_roof_cap_placeholder", (0.30, 0.29, 0.26, 1.0)),
        "socket": map_render.make_material("kit_socket_marker", (0.05, 0.58, 0.90, 1.0)),
        "interior_socket": map_render.make_material("kit_interior_socket", (0.62, 0.36, 0.78, 1.0)),
        "exterior_socket": map_render.make_material("kit_exterior_socket", (0.08, 0.70, 0.34, 1.0)),
    }


def add_socket_marker(socket: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.11, location=tuple(socket["local_position_m"]))
    obj = bpy.context.object
    obj.name = f"{parent.name}.{socket['socket_id']}.marker"
    obj.data.materials.append(material)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["building_graph_id"] = parent["building_graph_id"]
    obj["socket_id"] = socket["socket_id"]
    obj["socket_type"] = socket["socket_type"]
    obj["placement_space"] = socket["placement_space"]
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not KIT_GRAPH_PATH.exists():
        kit_compile.main()
    compiled = load_json(COMPILED_MAP_PATH)
    kit = load_json(KIT_GRAPH_PATH)
    recipes = placement_compile.load_measured_recipes()

    map_render.SEMANTIC_TERRAIN_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    map_render.REFINED_TERRAIN_GRAPH_PATH = REFINED_GRAPH_PATH
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    kit_mats = make_materials()
    measured_mats = measured_render.make_measured_materials()
    map_assets.render_base_layers(compiled, terrain_mats)

    created_components: list[bpy.types.Object] = []
    created_socket_markers: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    for graph in kit["building_graphs"]:
        parent = attachment_render.add_building_parent(graph)
        for component in graph["components"]:
            created_components.append(attachment_render.add_component(component, kit_mats, parent))
        for socket in graph["interior_sockets"]:
            created_socket_markers.append(add_socket_marker(socket, kit_mats["interior_socket"], parent))
        for socket in graph["exterior_sockets"]:
            created_socket_markers.append(add_socket_marker(socket, kit_mats["exterior_socket"], parent))
        for socket in graph["internal_asset_sockets"]:
            created_socket_markers.append(add_socket_marker(socket, kit_mats["socket"], parent))
            recipe = recipes[socket["measured_asset_id"]]
            created_assets.extend(attachment_render.add_measured_asset_under_building(socket, recipe, measured_mats, parent))

    map_render.add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    attachment_render.TOPDOWN_RENDER_PATH = TOPDOWN_RENDER_PATH
    attachment_render.render_topdown()

    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    asset_instance_count = sum(
        1
        for obj in created_assets
        if obj.type == "EMPTY" and str(obj.get("placement_space")) == "building_graph_local"
    )
    component_counts: dict[str, int] = {}
    for component in created_components:
        kind = str(component.get("component_type"))
        component_counts[kind] = component_counts.get(kind, 0) + 1
    report = {
        "schema": "building_graph_kit_expansion_blender_report_v0",
        "source_kit_graph": str(KIT_GRAPH_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "building_graph_count": kit["validation"]["building_graph_count"],
        "component_counts": dict(sorted(component_counts.items())),
        "socket_marker_count": len(created_socket_markers),
        "building_local_asset_instance_count": asset_instance_count,
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "every_building_has_visible_components": all(
            any(obj.get("building_graph_id") == graph["building_graph_id"] for obj in created_components)
            for graph in kit["building_graphs"]
        ),
        "acceptance": {
            "three_building_graphs_generated": kit["validation"]["building_graph_count"] == 3,
            "foundation_skirt_still_hides_terrain_seam": kit["validation"]["foundation_skirt_still_hides_terrain_seam"],
            "local_assets_place_relative_to_building_graph_coordinates": kit["validation"]["local_assets_place_relative_to_building_graph_coordinates"],
            "baked_map_exposes_only_summarized_building_records": kit["validation"]["baked_map_exposes_only_summarized_building_records"],
            "live_building_graph_remains_discardable_after_bake": kit["validation"]["live_building_graph_remains_discardable_after_bake"],
        },
        "no_claims": kit["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        "building_graphs={building_graph_count} components={component_count} sockets={socket_count} meshes={mesh_object_count}".format(
            building_graph_count=report["building_graph_count"],
            component_count=len(created_components),
            socket_count=len(created_socket_markers),
            mesh_object_count=report["mesh_object_count"],
        )
    )


if __name__ == "__main__":
    main()
