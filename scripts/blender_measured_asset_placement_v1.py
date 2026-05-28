#!/usr/bin/env python3
"""Render Measured Asset Placement v1 proof scene.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_measured_asset_placement_v1.py

This is a deterministic placement proof only. It uses existing measured
component recipes and existing map sockets; it does not create production,
structural, fabrication, or historical-accuracy claims.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import blender_tiled_map_template_asset_instances_v1 as map_assets  # noqa: E402
import blender_tiled_map_template_v0 as map_render  # noqa: E402
import compile_measured_asset_placement_v1 as placement_compile  # noqa: E402


COMPILED_PATH = Path(os.environ.get("MEASURED_PLACEMENT_COMPILED_PATH", ROOT / "goal" / "architecture" / "map_templates_v0" / "compiled" / "tiled_hex_map_template_v0_compiled.json"))
PLACEMENT_PATH = Path(os.environ.get("MEASURED_PLACEMENT_PATH", ROOT / "goal" / "architecture" / "measured_asset_placement_v1" / "measured_asset_placement_v1.json"))
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = Path(os.environ.get("MEASURED_PLACEMENT_BLEND_PATH", OUT_DIR / "measured_asset_placement_v1.blend"))
RENDER_PATH = Path(os.environ.get("MEASURED_PLACEMENT_RENDER_PATH", OUT_DIR / "measured_asset_placement_v1_workbench.png"))
TOPDOWN_RENDER_PATH = Path(os.environ.get("MEASURED_PLACEMENT_TOPDOWN_PATH", OUT_DIR / "measured_asset_placement_v1_anchor_topdown.png"))
REPORT_PATH = Path(os.environ.get("MEASURED_PLACEMENT_REPORT_PATH", OUT_DIR / "measured_asset_placement_v1_report.json"))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def make_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def make_measured_materials() -> dict[str, bpy.types.Material]:
    return {
        "stone": make_material("placed_measured_warm_stone", (0.56, 0.52, 0.44, 1.0)),
        "support": make_material("placed_measured_support_limestone", (0.75, 0.66, 0.42, 1.0)),
        "walkable": make_material("placed_measured_walkable", (0.30, 0.56, 0.36, 1.0)),
        "rib": make_material("placed_measured_arch_rib", (0.82, 0.72, 0.48, 1.0)),
        "cap": make_material("placed_measured_cap", (0.62, 0.58, 0.50, 1.0)),
        "rail": make_material("placed_measured_rail", (0.30, 0.46, 0.62, 1.0)),
        "socket": make_material("placed_measured_socket", (0.12, 0.40, 0.86, 1.0)),
    }


def placement_matrix(frame: dict[str, Any]) -> mathutils.Matrix:
    right = [float(value) for value in frame["right"]]
    forward = [float(value) for value in frame["forward"]]
    up = [float(value) for value in frame["up"]]
    pos = [float(value) for value in frame["position"]]
    return mathutils.Matrix(
        (
            (right[0], forward[0], up[0], pos[0]),
            (right[1], forward[1], up[1], pos[1]),
            (right[2], forward[2], up[2], pos[2]),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def add_parent(placement: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(f"{placement['socket_id']}.{placement['measured_asset_id']}", None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.28
    obj.matrix_world = placement_matrix(placement["anchor_frame"])
    for key, value in {
        "placement_id": placement["placement_id"],
        "socket_id": placement["socket_id"],
        "source_asset_ref": placement["source_asset_ref"],
        "measured_asset_id": placement["measured_asset_id"],
        "placement_status": placement["status"],
        "semantic_surface_id": str(placement.get("semantic_surface_id")),
        "orientation_uses_anchor_frame": True,
        "sits_on_profiled_terrain": bool(placement["placement_validation"]["sits_on_profiled_terrain"]),
        "no_structural_claims": True,
        "no_production_approval": True,
        "no_fabrication_claims": True,
        "no_historical_accuracy_claim": True,
    }.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_cube(part: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    loc = tuple(float(value) for value in part["location_m"])
    dims = tuple(float(value) for value in part["dimensions_m"])
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = f"{parent.name}.{part['name']}"
    obj.dimensions = dims
    obj.data.materials.append(materials[part.get("material_role", "stone")])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["measured_asset_id"] = parent["measured_asset_id"]
    obj["socket_id"] = parent["socket_id"]
    return obj


def add_cylinder(part: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    loc = tuple(float(value) for value in part["location_m"])
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=int(part["vertices"]),
        radius=float(part["radius_m"]),
        depth=float(part["depth_m"]),
        location=loc,
    )
    obj = bpy.context.object
    obj.name = f"{parent.name}.{part['name']}"
    obj.data.materials.append(materials[part.get("material_role", "stone")])
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["measured_asset_id"] = parent["measured_asset_id"]
    obj["socket_id"] = parent["socket_id"]
    return obj


def pointed_arch_points(span: float, spring_z: float, rise: float, y: float, segments: int = 18) -> list[tuple[float, float, float]]:
    half = span * 0.5
    points: list[tuple[float, float, float]] = []
    for index in range(segments + 1):
        t = index / segments
        x = -half + half * t
        z = spring_z + rise * (1.0 - (1.0 - t) ** 2)
        points.append((x, y, z))
    for index in range(1, segments + 1):
        t = index / segments
        x = half * t
        z = spring_z + rise * (1.0 - t**2)
        points.append((x, y, z))
    return points


def round_arch_points(span: float, spring_z: float, y: float, segments: int = 28) -> list[tuple[float, float, float]]:
    radius = span * 0.5
    return [
        (
            math.cos(math.pi - math.pi * index / segments) * radius,
            y,
            spring_z + math.sin(math.pi - math.pi * index / segments) * radius,
        )
        for index in range(segments + 1)
    ]


def add_curve(part: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    if part["curve_kind"] == "round":
        points = round_arch_points(float(part["span_m"]), float(part["spring_z_m"]), float(part["y_m"]))
    else:
        points = pointed_arch_points(float(part["span_m"]), float(part["spring_z_m"]), float(part["rise_m"]), float(part["y_m"]))
    curve = bpy.data.curves.new(f"{parent.name}.{part['name']}_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = float(part["bevel_depth_m"])
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points, strict=True):
        point.co = (coord[0], coord[1], coord[2], 1.0)
    obj = bpy.data.objects.new(f"{parent.name}.{part['name']}", curve)
    obj.data.materials.append(materials[part.get("material_role", "rib")])
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["measured_asset_id"] = parent["measured_asset_id"]
    obj["socket_id"] = parent["socket_id"]
    bpy.context.collection.objects.link(obj)
    return obj


def add_socket_markers(recipe: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> list[bpy.types.Object]:
    markers: list[bpy.types.Object] = []
    for item in recipe["sockets"]:
        loc = tuple(float(value) for value in item["position_m"])
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=5, radius=0.045, location=loc)
        obj = bpy.context.object
        obj.name = f"{parent.name}.{item['socket_id']}"
        obj.data.materials.append(materials["socket"])
        obj.parent = parent
        obj.matrix_parent_inverse.identity()
        obj["socket_marker_for"] = parent["socket_id"]
        obj["connector_term"] = item["connector_term"]
        markers.append(obj)
    return markers


def create_measured_asset(placement: dict[str, Any], recipe: dict[str, Any], materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    parent = add_parent(placement)
    created: list[bpy.types.Object] = [parent]
    for part in recipe["proof_primitives"]:
        if part["primitive"] == "cube":
            created.append(add_cube(part, materials, parent))
        elif part["primitive"] == "cylinder":
            created.append(add_cylinder(part, materials, parent))
        elif part["primitive"] == "curve":
            created.append(add_curve(part, materials, parent))
        else:
            raise ValueError(f"{recipe['asset_id']} unsupported primitive {part['primitive']}")
    created.extend(add_socket_markers(recipe, materials, parent))
    return created


def scene_mesh_bounds() -> tuple[float, float, float, float, float, float]:
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


def render_topdown_diagnostics() -> None:
    min_x, min_y, _min_z, max_x, max_y, max_z = scene_mesh_bounds()
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    span = max(max_x - min_x, max_y - min_y)
    bpy.ops.object.camera_add(location=(center_x, center_y, max_z + 30.0), rotation=(0.0, 0.0, 0.0))
    cam = bpy.context.object
    cam.name = "measured_anchor_topdown_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.08
    direction = mathutils.Vector((center_x, center_y, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(TOPDOWN_RENDER_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if os.environ.get("MEASURED_PLACEMENT_SEMANTIC_GRAPH_PATH"):
        map_render.SEMANTIC_TERRAIN_GRAPH_PATH = Path(os.environ["MEASURED_PLACEMENT_SEMANTIC_GRAPH_PATH"])
    if os.environ.get("MEASURED_PLACEMENT_REFINED_GRAPH_PATH"):
        map_render.REFINED_TERRAIN_GRAPH_PATH = Path(os.environ["MEASURED_PLACEMENT_REFINED_GRAPH_PATH"])
    if not PLACEMENT_PATH.exists():
        placement_compile.main()
    placement_data = load_json(PLACEMENT_PATH)
    compiled = load_json(COMPILED_PATH)
    recipes = placement_compile.load_measured_recipes()
    map_render.clear_scene()
    terrain_mats = map_assets.make_terrain_materials()
    measured_mats = make_measured_materials()
    map_assets.render_base_layers(compiled, terrain_mats)

    created: list[bpy.types.Object] = []
    anchor_diagnostic_count = 0
    for placement in placement_data["placements"]:
        frame = dict(placement["anchor_frame"])
        frame["anchor_kind"] = placement["anchor_kind"]
        frame["parent_feature_id"] = placement.get("anchor_ref", "")
        socket_like = {
            "socket_id": placement["socket_id"],
            "anchor_frame": frame,
            "placement_validation": {"status": placement["status"]},
        }
        anchor_diagnostic_count += map_assets.add_anchor_diagnostics(socket_like, terrain_mats)
        if placement["measured_asset_id"] is None:
            continue
        created.extend(create_measured_asset(placement, recipes[placement["measured_asset_id"]], measured_mats))

    map_render.add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    render_topdown_diagnostics()

    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    empty_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "EMPTY")
    measured_mesh_counts = {
        placement["socket_id"]: sum(
            1
            for obj in created
            if obj.get("socket_id") == placement["socket_id"] and obj.type in {"MESH", "CURVE"}
        )
        for placement in placement_data["placements"]
    }
    report = {
        "schema": "measured_asset_placement_blender_report_v1",
        "source_placement_file": str(PLACEMENT_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "topdown_anchor_render_path": str(TOPDOWN_RENDER_PATH.relative_to(ROOT)),
        "placement_attempt_count": placement_data["validation"]["placement_attempt_count"],
        "missing_measured_asset_id_count": placement_data["validation"]["missing_measured_asset_id_count"],
        "status_counts": placement_data["validation"]["status_counts"],
        "placed_measured_asset_count": sum(1 for p in placement_data["placements"] if p.get("measured_asset_id")),
        "measured_mesh_counts": measured_mesh_counts,
        "every_mesh_exists": all(count > 0 for count in measured_mesh_counts.values()),
        "anchor_diagnostic_object_count": anchor_diagnostic_count,
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "empty_object_count": empty_count,
        "rules": {
            "measured_asset_placement_v1": True,
            "replacement_for_placeholder_map_asset_instances": True,
            "orientation_uses_anchor_forward_right_up": True,
            "profiled_anchor_height_used": True,
            "anchor_diagnostics_deterministic": True,
            "web_search_used": False,
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_historical_accuracy_claim": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {TOPDOWN_RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"placed={report['placed_measured_asset_count']} mesh={mesh_count} curves={curve_count} empties={empty_count}")


if __name__ == "__main__":
    main()
