#!/usr/bin/env python3
"""Render Map Template v2 Building Variant Placement proof scene."""

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
import compile_map_template_v2_building_variant_placement as placement_compile  # noqa: E402
import compile_measured_asset_placement_v1 as measured_compile  # noqa: E402


COMPILED_MAP_PATH = placement_compile.COMPILED_MAP_PATH
SEMANTIC_GRAPH_PATH = placement_compile.SEMANTIC_GRAPH_PATH
REFINED_GRAPH_PATH = placement_compile.REFINED_GRAPH_PATH
PLACEMENT_PATH = placement_compile.PLACEMENT_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "map_template_v2_building_variant_placement.blend"
RENDER_PATH = OUT_DIR / "map_template_v2_building_variant_placement_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "map_template_v2_building_variant_placement_topdown.png"
REPORT_PATH = OUT_DIR / "map_template_v2_building_variant_placement_report.json"


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
        "door_edge_adjustment_applied": graph["door_edge_adjustment"]["applied"],
        "asset_scaling_applied": graph["asset_scaling"]["asset_scaling_applied"],
        "freeze_after_bake": True,
        "live_graph_discardable_after_bake": True,
        "no_ornament": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PLACEMENT_PATH.exists():
        placement_compile.main()
    placement = load_json(PLACEMENT_PATH)
    compiled = load_json(COMPILED_MAP_PATH)
    recipes = measured_compile.load_measured_recipes()

    map_render.SEMANTIC_TERRAIN_GRAPH_PATH = SEMANTIC_GRAPH_PATH
    map_render.REFINED_TERRAIN_GRAPH_PATH = REFINED_GRAPH_PATH
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    kit_mats = kit_render.make_materials()
    measured_mats = measured_render.make_measured_materials()
    map_assets.render_base_layers(compiled, terrain_mats)

    created_components: list[bpy.types.Object] = []
    created_socket_markers: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    for graph in placement["placed_building_graphs"]:
        parent = add_variant_parent(graph)
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
        "schema": "map_template_v2_building_variant_placement_blender_report",
        "source_placement_graph": str(PLACEMENT_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "building_variant_placement_count": placement["validation"]["map_plot_variant_placement_count"],
        "variant_classes_used": placement["validation"]["variant_classes_used"],
        "component_counts": dict(sorted(component_counts.items())),
        "socket_marker_count": len(created_socket_markers),
        "building_local_asset_instance_count": sum(1 for obj in created_assets if obj.type == "EMPTY"),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "curve_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE"),
        "acceptance": {
            "three_map_plots_receive_building_variants": placement["validation"]["three_map_plots_receive_building_variants"],
            "variant_choice_recorded_with_reason": placement["validation"]["variant_choice_recorded_with_reason"],
            "foundation_seam_hiding_still_passes": placement["validation"]["foundation_seam_hiding_still_passes"],
            "entrances_connect_to_roads": placement["validation"]["entrances_connect_to_roads"],
            "baked_summaries_remain_summary_only": placement["validation"]["baked_summaries_remain_summary_only"],
            "terrain_cracks_remain_zero": placement["validation"]["terrain_cracks_remain_zero"],
            "render_has_visible_building_variation": placement["validation"]["render_has_visible_building_variation"],
        },
        "no_claims": placement["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        "placements={building_variant_placement_count} variants={variant_classes_used} meshes={mesh_object_count}".format(
            **report
        )
    )


if __name__ == "__main__":
    main()
