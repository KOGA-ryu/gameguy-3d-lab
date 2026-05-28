#!/usr/bin/env python3
"""Render Building Graph Variation Rules v0 proof scene."""

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

import blender_building_graph_attachment_v0 as attachment_render  # noqa: E402
import blender_building_graph_kit_expansion_v0 as kit_render  # noqa: E402
import blender_measured_asset_placement_v1 as measured_render  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402
import compile_building_graph_variation_rules_v0 as variation_compile  # noqa: E402
import compile_measured_asset_placement_v1 as placement_compile  # noqa: E402


VARIATION_GRAPH_PATH = variation_compile.VARIATION_GRAPH_PATH
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "building_graph_variation_rules_v0.blend"
RENDER_PATH = OUT_DIR / "building_graph_variation_rules_v0_workbench.png"
TOPDOWN_RENDER_PATH = OUT_DIR / "building_graph_variation_rules_v0_topdown.png"
REPORT_PATH = OUT_DIR / "building_graph_variation_rules_v0_report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def add_variant_parent(variant: dict[str, Any], offset: tuple[float, float, float]) -> bpy.types.Object:
    obj = bpy.data.objects.new(variant["building_graph_variant_id"], None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.7
    obj.matrix_world = mathutils.Matrix.Translation(mathutils.Vector(offset))
    for key, value in {
        "building_graph_id": variant["building_graph_variant_id"],
        "building_graph_variant_id": variant["building_graph_variant_id"],
        "source_building_graph_id": variant["source_building_graph_id"],
        "variant_class": variant["variant_class"],
        "attach_socket_id": variant["attach_socket_id"],
        "asset_scaling_applied": variant["asset_scaling"]["asset_scaling_applied"],
        "no_ornament": True,
        "freeze_after_bake": True,
        "live_graph_discardable_after_bake": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_review_floor(size: float, offset: tuple[float, float, float], material: bpy.types.Material, name: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(offset[0], offset[1], offset[2] - 0.035))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (size, size, 0.04)
    obj.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


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


def add_scene_context(render_path: Path) -> None:
    min_x, min_y, min_z, max_x, max_y, max_z = scene_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.light_add(type="AREA", location=(center_x - 5.0, center_y - 7.0, max_z + 9.0))
    light = bpy.context.object
    light.name = "variation_review_key_light"
    light.data.energy = 450.0
    light.data.size = 7.0
    bpy.ops.object.camera_add(location=(center_x - 8.0, center_y - 14.0, max_z + 9.0))
    cam = bpy.context.object
    cam.name = "variation_review_camera"
    direction = mathutils.Vector((center_x, center_y, (min_z + max_z) * 0.42)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.0
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.render.filepath = str(render_path)


def render_topdown() -> None:
    min_x, min_y, _min_z, max_x, max_y, max_z = scene_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.camera_add(location=(center_x, center_y, max_z + 35.0))
    cam = bpy.context.object
    cam.name = "variation_review_topdown_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.04
    direction = mathutils.Vector((center_x, center_y, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(TOPDOWN_RENDER_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not VARIATION_GRAPH_PATH.exists():
        variation_compile.main()
    data = load_json(VARIATION_GRAPH_PATH)
    recipes = placement_compile.load_measured_recipes()
    map_render.clear_scene()
    kit_mats = kit_render.make_materials()
    measured_mats = measured_render.make_measured_materials()
    floor_mat = map_render.make_material("variation_review_floor", (0.24, 0.28, 0.28, 1.0))

    created_components: list[bpy.types.Object] = []
    created_sockets: list[bpy.types.Object] = []
    created_assets: list[bpy.types.Object] = []
    source_order = ["gatehouse_graph_v0", "watch_graph_v0", "shrine_graph_v0"]
    variant_order = ["compact", "standard", "tall"]
    variants = sorted(
        data["building_graph_variants"],
        key=lambda row: (source_order.index(row["source_building_graph_id"]), variant_order.index(row["variant_class"])),
    )
    for index, variant in enumerate(variants):
        row = index // 3
        col = index % 3
        offset = ((col - 1) * 12.5, (1 - row) * 11.0, 0.0)
        add_review_floor(10.5, offset, floor_mat, f"{variant['building_graph_variant_id']}.review_floor")
        parent = add_variant_parent(variant, offset)
        for component in variant["components"]:
            created_components.append(attachment_render.add_component(component, kit_mats, parent))
        for socket in variant["interior_sockets"]:
            created_sockets.append(kit_render.add_socket_marker(socket, kit_mats["interior_socket"], parent))
        for socket in variant["exterior_sockets"]:
            created_sockets.append(kit_render.add_socket_marker(socket, kit_mats["exterior_socket"], parent))
        for socket in variant["internal_asset_sockets"]:
            created_sockets.append(kit_render.add_socket_marker(socket, kit_mats["socket"], parent))
            if socket.get("measured_asset_id") in recipes:
                created_assets.extend(
                    attachment_render.add_measured_asset_under_building(socket, recipes[socket["measured_asset_id"]], measured_mats, parent)
                )

    add_scene_context(RENDER_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.ops.render.render(write_still=True)
    render_topdown()

    component_counts: dict[str, int] = {}
    for obj in created_components:
        kind = str(obj.get("component_type"))
        component_counts[kind] = component_counts.get(kind, 0) + 1
    report = {
        "schema": "building_graph_variation_rules_blender_report_v0",
        "source_variation_graph": str(VARIATION_GRAPH_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "variant_count": data["validation"]["building_graph_variant_count"],
        "component_counts": dict(sorted(component_counts.items())),
        "socket_marker_count": len(created_sockets),
        "building_local_asset_instance_count": sum(1 for obj in created_assets if obj.type == "EMPTY"),
        "mesh_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH"),
        "curve_object_count": sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE"),
        "acceptance": {
            "nine_building_graph_variants_generated": data["validation"]["building_graph_variant_count"] == 9,
            "all_preserve_entrance_connectivity": data["validation"]["all_preserve_entrance_connectivity"],
            "all_preserve_foundation_seam_hiding": data["validation"]["all_preserve_foundation_seam_hiding"],
            "all_local_sockets_inside_or_near_footprint": data["validation"]["all_local_sockets_inside_or_near_footprint"],
            "all_baked_summaries_stay_map_friendly": data["validation"]["all_baked_summaries_stay_map_friendly"],
            "asset_scaling_applied_count": data["validation"]["asset_scaling_applied_count"],
            "no_ornament": data["validation"]["no_ornament"],
        },
        "no_claims": data["no_claims"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"variants={report['variant_count']} meshes={report['mesh_object_count']} curves={report['curve_object_count']}")


if __name__ == "__main__":
    main()
