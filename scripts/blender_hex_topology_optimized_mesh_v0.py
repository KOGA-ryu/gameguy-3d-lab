#!/usr/bin/env python3
"""Render hex_topology_site_assembly_v0 as optimized terrain meshes.

This converts the hex terrain from object-per-cell proof into visibility-based
terrain meshing:

- one top mesh containing all visible hex top faces
- one side-wall mesh containing only exposed elevation boundaries
- one fall-marker mesh for debug affordance markers
- existing building/foundation assets remain separate for inspection

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_hex_topology_optimized_mesh_v0.py
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

from blender_topology_site_v0 import (  # noqa: E402
    clear_scene,
    create_asset,
    create_empty,
    load_json,
    make_material,
    scene_bounds,
)


SITE_DIR = ROOT / "goal" / "architecture" / "hex_topology_sites_v0" / "sites"
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "hex_topology_optimized_mesh_v0.blend"
RENDER_PATH = OUT_DIR / "hex_topology_optimized_mesh_v0_workbench.png"
REPORT_PATH = OUT_DIR / "hex_topology_optimized_mesh_v0_report.json"

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
    fallback = material_names.index("plateau")
    if role in material_names:
        return material_names.index(role)
    if role == "buildable_pad":
        return material_names.index("buildable")
    if role == "narrow_ledge":
        return material_names.index("ledge")
    if role == "lower_basin":
        return material_names.index("basin")
    return fallback


def make_top_mesh(
    site: dict[str, Any],
    materials: dict[str, bpy.types.Material],
    radius: float,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    material_order = ["basin", "terrace", "ledge", "plateau", "buildable", "road"]
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    face_roles: list[str] = []
    points = hex_points(radius)
    for cell in site["hex_cells"]:
        cx, cy = [float(v) for v in cell["center"]]
        z = float(cell["elevation"]) + 0.035
        start = len(vertices)
        vertices.extend((cx + x, cy + y, z) for x, y in points)
        faces.append(tuple(range(start, start + 6)))
        face_roles.append(cell["terrain_role"])

    obj = make_mesh_object(
        f"{site['site_id']}.terrain_top_mesh",
        vertices,
        faces,
        materials["plateau"],
        parent,
        {
            "mesh_role": "terrain_top_mesh",
            "hex_cell_count": site["cell_summary"]["cell_count"],
            "visible_face_rule": "top_faces_always_visible",
        },
    )
    obj.data.materials.clear()
    for name in material_order:
        obj.data.materials.append(materials[name])
    for poly, role in zip(obj.data.polygons, face_roles, strict=True):
        poly.material_index = role_material_index(role, material_order)
    return obj


def make_side_wall_mesh(
    site: dict[str, Any],
    materials: dict[str, bpy.types.Material],
    radius: float,
    parent: bpy.types.Object,
) -> tuple[bpy.types.Object, dict[str, int]]:
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
        cx, cy = [float(v) for v in cell["center"]]
        top_z = float(cell["elevation"]) + 0.035
        for side_index, (dq, dr) in enumerate(AXIAL_DIRECTIONS):
            neighbor = cells.get((cell["q"] + dq, cell["r"] + dr))
            if neighbor is None:
                bottom_z = -0.12
                stats["outer_boundary_side_faces"] += 1
            else:
                neighbor_top = float(neighbor["elevation"]) + 0.035
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
        f"{site['site_id']}.terrain_visible_side_wall_mesh",
        vertices,
        faces,
        materials["side_wall"],
        parent,
        {
            "mesh_role": "terrain_visible_side_wall_mesh",
            "visible_face_rule": "side_faces_only_when_neighbor_lower_or_missing",
        },
    )
    return obj, stats


def make_fall_marker_mesh(
    site: dict[str, Any],
    materials: dict[str, bpy.types.Material],
    radius: float,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    cells_by_id = {cell["cell_id"]: cell for cell in site["hex_cells"]}
    high_cell_ids = sorted({edge["high_cell"] for edge in site["fall_edges"]})
    marker_radius = radius * 0.28
    points = hex_points(marker_radius)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for cell_id in high_cell_ids:
        cell = cells_by_id[cell_id]
        cx, cy = [float(v) for v in cell["center"]]
        z = float(cell["elevation"]) + 0.18
        start = len(vertices)
        vertices.extend((cx + x, cy + y, z) for x, y in points)
        faces.append(tuple(range(start, start + 6)))
    return make_mesh_object(
        f"{site['site_id']}.fall_edge_marker_mesh",
        vertices,
        faces,
        materials["fall"],
        parent,
        {
            "mesh_role": "fall_edge_marker_mesh",
            "marker_count": len(high_cell_ids),
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
    mesh = bpy.data.meshes.new("standard_32m_cube_bounds_mesh")
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
    bpy.ops.object.light_add(type="AREA", location=(0.0, -10.0, 14.0))
    light = bpy.context.object
    light.name = "hex_optimized_area_light"
    light.data.energy = 700.0
    light.data.size = 11.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((18.0, -24.0, 17.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.12
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
        "plateau": make_material("mat_opt_plateau", (0.30, 0.50, 0.34, 1.0)),
        "buildable": make_material("mat_opt_buildable", (0.36, 0.58, 0.39, 1.0)),
        "road": make_material("mat_opt_road", (0.39, 0.33, 0.25, 1.0)),
        "ledge": make_material("mat_opt_ledge", (0.55, 0.53, 0.39, 1.0)),
        "terrace": make_material("mat_opt_terrace", (0.42, 0.47, 0.36, 1.0)),
        "basin": make_material("mat_opt_basin", (0.24, 0.34, 0.32, 1.0)),
        "side_wall": make_material("mat_opt_visible_side_wall", (0.23, 0.27, 0.23, 1.0)),
        "fall": make_material("mat_opt_fall_edge", (0.90, 0.18, 0.12, 1.0)),
        "bounds": make_material("mat_opt_cube_bounds", (0.08, 0.08, 0.08, 1.0)),
        "foundation": make_material("mat_foundation", (0.42, 0.41, 0.38, 1.0)),
        "retaining_wall": make_material("mat_retaining_wall", (0.33, 0.31, 0.28, 1.0)),
        "hazard": make_material("mat_fall_edge", (0.88, 0.22, 0.16, 1.0)),
        "upper_terrain": make_material("mat_upper_terrain", (0.29, 0.48, 0.31, 1.0)),
        "lower_terrain": make_material("mat_lower_terrain", (0.31, 0.36, 0.30, 1.0)),
        "barrier": make_material("mat_barrier", (0.26, 0.56, 0.88, 1.0)),
        "support": make_material("mat_support", (0.92, 0.77, 0.30, 1.0)),
        "blocked": make_material("mat_blocked", (0.62, 0.54, 0.42, 1.0)),
        "cover": make_material("mat_cover", (0.90, 0.58, 0.26, 1.0)),
        "walkable": make_material("mat_walkable", (0.22, 0.64, 0.34, 1.0)),
        "default": make_material("mat_default", (0.62, 0.60, 0.54, 1.0)),
    }
    solids = {path.stem: load_json(path) for path in sorted(SOLID_DIR.glob("*.json"))}
    site_paths = sorted(SITE_DIR.glob("*_assembly.json"))
    if not site_paths:
        raise FileNotFoundError(f"no compiled hex topology site assemblies found in {SITE_DIR}")
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
            "fall_edge_count": len(site["fall_edges"]),
        },
    )
    created.append(root)
    created.append(add_cube_bounds(site, materials, root))
    created.append(make_top_mesh(site, materials, radius, root))
    side_mesh, side_stats = make_side_wall_mesh(site, materials, radius, root)
    created.append(side_mesh)
    created.append(make_fall_marker_mesh(site, materials, radius, root))

    for inst in site["foundation_instances"]:
        t = inst["translation"]
        created.extend(
            create_asset(
                asset_ref=inst["asset_ref"],
                solids=solids,
                materials=materials,
                location=(float(t[0]), float(t[1]), float(t[2])),
                rotation_degrees=inst["rotation_degrees"],
                scale=inst["scale"],
                parent=root,
                name=f"{site['site_id']}.{inst['instance_id']}",
                semantic_tags=inst["semantic_tags"],
                source_instance=inst,
            )
        )

    for inst in site["building_instances"]:
        t = inst["translation"]
        created.extend(
            create_asset(
                asset_ref=inst["asset_ref"],
                solids=solids,
                materials=materials,
                location=(float(t[0]), float(t[1]), float(t[2])),
                rotation_degrees=inst["rotation_degrees"],
                scale=inst["scale"],
                parent=root,
                name=f"{site['site_id']}.{inst['instance_id']}",
                semantic_tags=inst["semantic_tags"],
                source_instance=inst,
            )
        )

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    top_face_count = site["cell_summary"]["cell_count"]
    terrain_face_count = top_face_count + side_stats["visible_side_faces"]
    naive_side_face_count = side_stats["candidate_side_faces"]
    report = {
        "schema": "hex_topology_optimized_mesh_blender_proof_v0",
        "site_id": site["site_id"],
        "map_cube_id": site["map_cube"]["map_cube_id"],
        "cell_count": site["cell_summary"]["cell_count"],
        "top_face_count": top_face_count,
        "side_face_stats": side_stats,
        "terrain_face_count": terrain_face_count,
        "naive_prism_side_face_count": naive_side_face_count,
        "side_face_reduction_count": naive_side_face_count - side_stats["visible_side_faces"],
        "side_face_reduction_ratio": round((naive_side_face_count - side_stats["visible_side_faces"]) / naive_side_face_count, 6),
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "empty_object_count": empty_count,
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "rules": {
            "proof_scene_only": True,
            "terrain_top_mesh_single_object": True,
            "terrain_side_wall_mesh_single_object": True,
            "no_internal_same_height_walls": True,
            "side_faces_only_when_neighbor_lower_or_missing": True,
            "bottom_faces_omitted": True,
            "building_assembly_reused": True,
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
        "terrain faces="
        f"{terrain_face_count} top={top_face_count} visible_sides={side_stats['visible_side_faces']} "
        f"hidden_sides={side_stats['hidden_internal_side_faces']}"
    )
    print(f"objects_created={len(created)} mesh={mesh_count} empty={empty_count}")


if __name__ == "__main__":
    main()
