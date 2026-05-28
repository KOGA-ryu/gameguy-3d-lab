#!/usr/bin/env python3
"""Render Integrated Map Scene v0 proof scene."""

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
import blender_plug_based_connection_graph_v0 as plug_render  # noqa: E402
import blender_tiled_map_template_asset_instances_v1 as map_assets  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402
import compile_connector_asset_placement_v0 as connector_compile  # noqa: E402
import compile_integrated_map_scene_v0 as integrated_compile  # noqa: E402
import compile_measured_asset_placement_v1 as measured_compile  # noqa: E402


INTEGRATED_GRAPH_PATH = integrated_compile.INTEGRATED_GRAPH_PATH
COMPILED_MAP_PATH = integrated_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = integrated_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = integrated_compile.REFINED_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "integrated_map_scene_v0.blend"
RENDER_PATH = OUT_DIR / "integrated_map_scene_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "integrated_map_scene_v0_topdown.png"
REPORT_PATH = OUT_DIR / "integrated_map_scene_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def all_plugs(plug_graph: dict[str, Any]) -> list[dict[str, Any]]:
    plugs: list[dict[str, Any]] = []
    for plug_set in plug_graph["plug_sets"].values():
        plugs.extend(plug_set)
    return plugs


def load_connector_recipes() -> dict[str, dict[str, Any]]:
    connector_compile.write_connector_kit()
    recipes: dict[str, dict[str, Any]] = {}
    for path in sorted(connector_compile.RECIPE_DIR.glob("*.json")):
        data = load_json(path)
        recipes[data["asset_id"]] = data
    return recipes


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    integrated_compile.main()
    connector_compile.main()
    graph = load_json(INTEGRATED_GRAPH_PATH)
    compiled = load_json(COMPILED_MAP_PATH)
    recipes = measured_compile.load_measured_recipes()
    connector_placement = load_json(connector_compile.PLACEMENT_PATH)
    connector_recipes = load_connector_recipes()
    plug_graph = graph["plug_connection_graph"]

    map_render.SEMANTIC_TERRAIN_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    map_render.REFINED_TERRAIN_GRAPH_PATH = REFINED_GRAPH_PATH
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    kit_mats = kit_render.make_materials()
    measured_mats = measured_render.make_measured_materials()
    plug_mats = plug_render.make_plug_materials()
    map_assets.render_base_layers(compiled, terrain_mats)

    connector_objects = [plug_render.add_connector_strip(path, plug_mats) for path in plug_graph["generated_connector_paths"]]
    union_envelope_objects = []
    for path in plug_graph["generated_connector_paths"]:
        union_envelope_objects.extend(plug_render.add_union_vertical_envelope(path, plug_mats))
    plug_markers = [plug_render.add_plug_marker(plug, plug_mats) for plug in all_plugs(plug_graph)]

    created_components: list[bpy.types.Object] = []
    created_socket_markers: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    created_connector_assets: list[bpy.types.Object] = []
    for placement in connector_placement["asset_instances"]:
        recipe = connector_recipes[placement["asset_id"]]
        created_connector_assets.extend(measured_render.create_measured_asset(placement, recipe, measured_mats))

    for placed_graph in graph["building_variant_placement"]["placed_building_graphs"]:
        parent = plug_render.add_variant_parent(placed_graph)
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
        "schema": "integrated_map_scene_v0_blender_report",
        "source_integrated_graph": str(INTEGRATED_GRAPH_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "building_variant_count": graph["building_variant_placement"]["validation"]["map_plot_variant_placement_count"],
        "plug_marker_count": len(plug_markers),
        "connector_path_count": len(connector_objects),
        "connector_asset_instance_count": connector_placement["validation"]["connector_asset_instance_count"],
        "connector_asset_mesh_object_count": sum(1 for obj in created_connector_assets if obj.type == "MESH"),
        "union_vertical_envelope_marker_count": len(union_envelope_objects),
        "socket_marker_count": len(created_socket_markers),
        "building_local_asset_instance_count": sum(1 for obj in created_assets if obj.type == "EMPTY"),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "curve_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE"),
        "acceptance": {
            "terrain_cracks_remain_zero": graph["validation"]["terrain_cracks_remain_zero"],
            "top_triangle_count_equals_cell_count_times_12": graph["validation"][
                "top_triangle_count_equals_cell_count_times_12"
            ],
            "at_least_three_building_variants_placed": graph["validation"]["at_least_three_building_variants_placed"],
            "all_buildings_have_named_entrance_plugs": graph["validation"]["all_buildings_have_named_entrance_plugs"],
            "at_least_three_declared_plug_connections_resolve": graph["validation"][
                "at_least_three_declared_plug_connections_resolve"
            ],
            "roads_and_pathways_visible": graph["validation"]["roads_and_pathways_visible"],
            "foundation_skirts_hide_terrain_building_seams": graph["validation"][
                "foundation_skirts_hide_terrain_building_seams"
            ],
            "render_shows_plugs_and_connector_paths": bool(plug_markers) and bool(connector_objects),
            "connector_assets_rendered": connector_placement["validation"]["connector_asset_instance_count"] > 0
            and any(obj.type == "MESH" for obj in created_connector_assets),
            "bridge_link_has_deck_rails_abutments": connector_placement["validation"]["bridge_link_has_deck_rails_abutments"],
            "road_threshold_has_landing": connector_placement["validation"]["road_threshold_has_landing"],
            "no_connector_asset_scaled_silently": connector_placement["validation"]["no_connector_asset_scaled_silently"],
        },
        "no_claims": graph["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        "buildings={building_variant_count} plugs={plug_marker_count} connectors={connector_path_count} meshes={mesh_object_count}".format(
            **report
        )
    )


if __name__ == "__main__":
    main()
