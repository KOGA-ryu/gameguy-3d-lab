#!/usr/bin/env python3
"""Render hex_terrain_fold_site_assembly_v0 as an optimized folded terrain mesh.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_hex_terrain_fold_site_v0.py

This renders the round hill proof:

- one top mesh using final_height
- one visible side-wall mesh using final_height
- one fold influence marker mesh
- no object-per-cell terrain
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

from blender_topology_site_v0 import clear_scene, create_empty, load_json, make_material, scene_bounds  # noqa: E402


SITE_DIR = ROOT / "goal" / "architecture" / "hex_terrain_fold_sites_v0" / "sites"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "round_hill_fold_site_v0.blend"
RENDER_PATH = OUT_DIR / "round_hill_fold_site_v0_workbench.png"
REPORT_PATH = OUT_DIR / "round_hill_fold_site_v0_report.json"

AXIAL_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]


def hex_points(radius: float) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos(math.radians(30.0 + i * 60.0)),
            radius * math.sin(math.radians(30.0 + i * 60.0)),
        )
        for i in range(6)
    ]


def make_mesh_object(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    material: bpy.types.Material,
    parent: bpy.types.Object | None,
    custom_props: dict[str, Any],
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    if parent is not None:
        obj.parent = parent
    obj.data.materials.append(material)
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def role_material_index(role: str, material_names: list[str]) -> int:
    if role in material_names:
        return material_names.index(role)
    return material_names.index("outer_flat")


def make_top_mesh(site: dict[str, Any], materials: dict[str, bpy.types.Material], radius: float, parent: bpy.types.Object) -> bpy.types.Object:
    material_order = ["outer_flat", "lower_slope", "upper_slope", "hilltop"]
    points = hex_points(radius)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    roles: list[str] = []
    for cell in site["hex_cells"]:
        cx = float(cell["world_x"])
        cy = float(cell["world_y"])
        z = float(cell["final_height"]) + 0.035
        start = len(vertices)
        vertices.extend((cx + x, cy + y, z) for x, y in points)
        faces.append(tuple(range(start, start + 6)))
        roles.append(cell["topology_role"])

    obj = make_mesh_object(
        f"{site['site_id']}.terrain_top_mesh",
        vertices,
        faces,
        materials["outer_flat"],
        parent,
        {
            "mesh_role": "terrain_top_mesh",
            "height_source": "final_height",
            "cell_count": site["cell_summary"]["cell_count"],
        },
    )
    obj.data.materials.clear()
    for name in material_order:
        obj.data.materials.append(materials[name])
    for poly, role in zip(obj.data.polygons, roles, strict=True):
        poly.material_index = role_material_index(role, material_order)
    return obj


def make_side_wall_mesh(site: dict[str, Any], materials: dict[str, bpy.types.Material], radius: float, parent: bpy.types.Object) -> tuple[bpy.types.Object, dict[str, int]]:
    points = hex_points(radius)
    cells = {(cell["q"], cell["r"]): cell for cell in site["hex_cells"]}
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    stats = {
        "candidate_side_faces": len(site["hex_cells"]) * 6,
        "visible_side_faces": 0,
        "hidden_internal_side_faces": 0,
        "outer_boundary_side_faces": 0,
        "partial_height_side_faces": 0,
    }
    for cell in site["hex_cells"]:
        cx = float(cell["world_x"])
        cy = float(cell["world_y"])
        top_z = float(cell["final_height"]) + 0.035
        for side_index, (dq, dr) in enumerate(AXIAL_DIRECTIONS):
            neighbor = cells.get((cell["q"] + dq, cell["r"] + dr))
            if neighbor is None:
                bottom_z = 0.0
                stats["outer_boundary_side_faces"] += 1
            else:
                neighbor_top = float(neighbor["final_height"]) + 0.035
                if neighbor_top >= top_z:
                    stats["hidden_internal_side_faces"] += 1
                    continue
                bottom_z = neighbor_top
                stats["partial_height_side_faces"] += 1

            a = points[side_index]
            b = points[(side_index + 1) % 6]
            start = len(vertices)
            vertices.extend(
                [
                    (cx + a[0], cy + a[1], bottom_z),
                    (cx + b[0], cy + b[1], bottom_z),
                    (cx + b[0], cy + b[1], top_z),
                    (cx + a[0], cy + a[1], top_z),
                ]
            )
            faces.append((start, start + 1, start + 2, start + 3))
            stats["visible_side_faces"] += 1

    obj = make_mesh_object(
        f"{site['site_id']}.visible_side_wall_mesh",
        vertices,
        faces,
        materials["side_wall"],
        parent,
        {
            "mesh_role": "visible_side_wall_mesh",
            "visible_face_rule": "neighbor_lower_or_missing_only",
        },
    )
    return obj, stats


def make_fold_marker_mesh(site: dict[str, Any], materials: dict[str, bpy.types.Material], radius: float, parent: bpy.types.Object) -> bpy.types.Object:
    marker_points = hex_points(radius * 0.25)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for cell in site["hex_cells"]:
        if not cell["fold_contributions"]:
            continue
        cx = float(cell["world_x"])
        cy = float(cell["world_y"])
        z = float(cell["final_height"]) + 0.12
        start = len(vertices)
        vertices.extend((cx + x, cy + y, z) for x, y in marker_points)
        faces.append(tuple(range(start, start + 6)))
    return make_mesh_object(
        f"{site['site_id']}.fold_influence_marker_mesh",
        vertices,
        faces,
        materials["fold_marker"],
        parent,
        {
            "mesh_role": "fold_influence_marker_mesh",
            "folded_cell_count": site["cell_summary"]["folded_cell_count"],
        },
    )


def add_cube_bounds(site: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    bounds = site["map_cube"]["coordinate_range"]
    x_min, x_max = [float(v) for v in bounds["x"]]
    y_min, y_max = [float(v) for v in bounds["y"]]
    z_min, z_max = [float(v) for v in bounds["z"]]
    verts = [
        (x_min, y_min, z_min),
        (x_max, y_min, z_min),
        (x_max, y_max, z_min),
        (x_min, y_max, z_min),
        (x_min, y_min, z_max),
        (x_max, y_min, z_max),
        (x_max, y_max, z_max),
        (x_min, y_max, z_max),
    ]
    edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]
    mesh = bpy.data.meshes.new("round_hill_cube_bounds_mesh")
    mesh.from_pydata(verts, edges, [])
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new("standard_32m_cube_bounds", mesh)
    obj.parent = parent
    obj.data.materials.append(materials["bounds"])
    obj["map_cube_id"] = site["map_cube"]["map_cube_id"]
    bpy.context.collection.objects.link(obj)
    return obj


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -11.0, 15.0))
    light = bpy.context.object
    light.name = "round_hill_area_light"
    light.data.energy = 700.0
    light.data.size = 11.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((18.0, -23.0, 15.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.10
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 1700
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    materials = {
        "outer_flat": make_material("mat_hill_outer_flat", (0.25, 0.38, 0.33, 1.0)),
        "lower_slope": make_material("mat_hill_lower_slope", (0.34, 0.48, 0.34, 1.0)),
        "upper_slope": make_material("mat_hill_upper_slope", (0.46, 0.56, 0.35, 1.0)),
        "hilltop": make_material("mat_hilltop", (0.62, 0.58, 0.38, 1.0)),
        "side_wall": make_material("mat_hill_side_wall", (0.25, 0.27, 0.23, 1.0)),
        "fold_marker": make_material("mat_fold_marker", (0.85, 0.38, 0.18, 1.0)),
        "bounds": make_material("mat_round_hill_cube_bounds", (0.08, 0.08, 0.08, 1.0)),
    }
    site_paths = sorted(SITE_DIR.glob("*_assembly.json"))
    if not site_paths:
        raise FileNotFoundError(f"no compiled hex terrain fold assemblies found in {SITE_DIR}")
    site = load_json(site_paths[0])
    radius = float(site["hex_grid"]["radius"]) * 0.96

    created: list[bpy.types.Object] = []
    root = create_empty(
        site["site_id"],
        (0.0, 0.0, 0.0),
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        None,
        {
            "site_id": site["site_id"],
            "schema": site["schema"],
            "cell_count": site["cell_summary"]["cell_count"],
            "folded_cell_count": site["cell_summary"]["folded_cell_count"],
        },
    )
    created.append(root)
    created.append(add_cube_bounds(site, materials, root))
    created.append(make_top_mesh(site, materials, radius, root))
    side_mesh, side_stats = make_side_wall_mesh(site, materials, radius, root)
    created.append(side_mesh)
    created.append(make_fold_marker_mesh(site, materials, radius, root))

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    report = {
        "schema": "round_hill_fold_site_blender_proof_v0",
        "site_id": site["site_id"],
        "map_cube_id": site["map_cube"]["map_cube_id"],
        "cell_count": site["cell_summary"]["cell_count"],
        "folded_cell_count": site["cell_summary"]["folded_cell_count"],
        "buildable_cell_count": site["cell_summary"]["buildable_cell_count"],
        "min_final_height": site["cell_summary"]["min_final_height"],
        "max_final_height": site["cell_summary"]["max_final_height"],
        "base_edge_summary": site["base_edge_summary"],
        "final_edge_summary": site["final_edge_summary"],
        "side_face_stats": side_stats,
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "empty_object_count": empty_count,
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "rules": {
            "proof_scene_only": True,
            "base_height_preserved": True,
            "final_height_rendered": True,
            "fold_markers_rendered": True,
            "terrain_top_mesh_single_object": True,
            "terrain_side_wall_mesh_single_object": True,
            "no_internal_same_height_walls": True,
            "bottom_faces_omitted": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(
        f"round hill cells={site['cell_summary']['cell_count']} "
        f"folded={site['cell_summary']['folded_cell_count']} "
        f"height={site['cell_summary']['min_final_height']:.2f}-{site['cell_summary']['max_final_height']:.2f}"
    )
    print(f"objects_created={len(created)} mesh={mesh_count} empty={empty_count}")


if __name__ == "__main__":
    main()
