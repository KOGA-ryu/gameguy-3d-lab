#!/usr/bin/env python3
"""Render hex seam policies as explicit terrain mesh behavior.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_hex_seam_policy_v0.py

This proof separates continuous shared terrain from explicit seam meshes:
shared_surface top mesh, split_riser walls, split_cliff walls, chunk_skirts,
and high-elevation socket markers.
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

from blender_topology_site_v0 import clear_scene, create_empty, load_json, make_material, scene_bounds  # noqa: E402


GRAPH_DIR = ROOT / "goal" / "architecture" / "hex_plot_vertex_graph_v0" / "graphs"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "hex_seam_policy_v0.blend"
RENDER_PATH = OUT_DIR / "hex_seam_policy_v0_workbench.png"
REPORT_PATH = OUT_DIR / "hex_seam_policy_v0_report.json"
Z_OFFSET = 0.035


def selected_graph_path() -> Path:
    graph_id = os.environ.get("HEX_GRAPH_ID", "").strip()
    if graph_id:
        path = GRAPH_DIR / f"{graph_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"requested HEX_GRAPH_ID not found: {path}")
        return path
    graph_paths = sorted(GRAPH_DIR.glob("*.json"))
    if not graph_paths:
        raise FileNotFoundError(f"no hex plot vertex graphs found in {GRAPH_DIR}")
    return graph_paths[0]


def output_paths() -> tuple[Path, Path, Path]:
    prefix = os.environ.get("HEX_OUTPUT_PREFIX", "hex_seam_policy_v0").strip() or "hex_seam_policy_v0"
    return (
        OUT_DIR / f"{prefix}.blend",
        OUT_DIR / f"{prefix}_workbench.png",
        OUT_DIR / f"{prefix}_report.json",
    )


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
    return material_names.index(role) if role in material_names else material_names.index("outer_flat")


def make_connected_top_mesh(graph: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    material_order = ["outer_flat", "lower_slope", "upper_slope", "hilltop"]
    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[str, int] = {}
    for vertex in graph["corner_vertices"]:
        vertex_index[vertex["vertex_id"]] = len(vertices)
        vertices.append((float(vertex["world_x"]), float(vertex["world_y"]), float(vertex["final_height"]) + Z_OFFSET))
    for midpoint in graph.get("edge_midpoints", []):
        vertex_index[midpoint["midpoint_id"]] = len(vertices)
        vertices.append((float(midpoint["world_x"]), float(midpoint["world_y"]), float(midpoint["height_m"]) + Z_OFFSET))

    faces: list[tuple[int, ...]] = []
    roles: list[str] = []
    for plot in graph["hex_plots"]:
        center_id = f"center_{plot['cell_id']}"
        vertex_index[center_id] = len(vertices)
        vertices.append((float(plot["center"][0]), float(plot["center"][1]), float(plot["center_height"]) + Z_OFFSET))
        center_index = vertex_index[center_id]
        corners = [vertex_index[vertex_id] for vertex_id in plot["corner_vertex_ids"]]
        midpoint_ids = plot.get("edge_midpoint_ids")
        if midpoint_ids:
            midpoints = [vertex_index[midpoint_id] for midpoint_id in midpoint_ids]
            for i in range(6):
                faces.append((center_index, corners[i], midpoints[i]))
                roles.append(plot["plot_role"])
                faces.append((center_index, midpoints[i], corners[(i + 1) % 6]))
                roles.append(plot["plot_role"])
        else:
            for i in range(6):
                faces.append((center_index, corners[i], corners[(i + 1) % 6]))
                roles.append(plot["plot_role"])

    obj = make_mesh_object(
        f"{graph['graph_id']}.shared_surface_top_mesh",
        vertices,
        faces,
        materials["outer_flat"],
        parent,
        {
            "mesh_role": "shared_surface_top_mesh",
            "surface_join_model": graph["mesh_plan"]["surface_join_model"],
            "seam_policy_model": graph["mesh_plan"]["seam_policy_model"],
            "corner_vertex_count": len(graph["corner_vertices"]),
            "edge_midpoint_count": len(graph.get("edge_midpoints", [])),
            "plot_count": len(graph["hex_plots"]),
        },
    )
    obj.data.materials.clear()
    for name in material_order:
        obj.data.materials.append(materials[name])
    for poly, role in zip(obj.data.polygons, roles, strict=True):
        poly.material_index = role_material_index(role, material_order)
    return obj


def seam_heights(seam: dict[str, Any], plot_by_id: dict[str, dict[str, Any]]) -> tuple[float, float]:
    high_cell = seam.get("high_cell")
    low_cell = seam.get("low_cell")
    if high_cell is None:
        return (0.0, 0.0)
    top = float(plot_by_id[high_cell]["center_height"]) + Z_OFFSET
    if low_cell is None:
        bottom = 0.0
    else:
        bottom = float(plot_by_id[low_cell]["center_height"]) + Z_OFFSET
    if bottom > top:
        bottom, top = top, bottom
    return bottom, top


def make_seam_wall_mesh(
    graph: dict[str, Any],
    seam_policy: str,
    name: str,
    material: bpy.types.Material,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    vertex_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    plot_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for seam in graph["seam_facts"]:
        if seam["seam_policy"] != seam_policy:
            continue
        va = vertex_by_id[seam["corner_vertex_ids"][0]]
        vb = vertex_by_id[seam["corner_vertex_ids"][1]]
        bottom, top = seam_heights(seam, plot_by_id)
        if top <= bottom:
            continue
        start = len(vertices)
        vertices.extend(
            [
                (float(va["world_x"]), float(va["world_y"]), bottom),
                (float(vb["world_x"]), float(vb["world_y"]), bottom),
                (float(vb["world_x"]), float(vb["world_y"]), top),
                (float(va["world_x"]), float(va["world_y"]), top),
            ]
        )
        faces.append((start, start + 1, start + 2, start + 3))
    return make_mesh_object(
        f"{graph['graph_id']}.{name}",
        vertices,
        faces,
        material,
        parent,
        {
            "mesh_role": name,
            "seam_policy": seam_policy,
            "face_count": len(faces),
        },
    )


def lerp2(left: tuple[float, float], right: tuple[float, float], t: float) -> tuple[float, float]:
    return (
        left[0] + (right[0] - left[0]) * t,
        left[1] + (right[1] - left[1]) * t,
    )


def make_fold_meet_halfway_mesh(graph: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> bpy.types.Object:
    vertex_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    plot_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    inset = float(graph["hex_grid"]["radius"]) * 0.28
    fold_width_ratio = inset / max(float(graph["hex_grid"]["radius"]), 0.001)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    fold_count = 0
    for seam in graph["seam_facts"]:
        if seam["seam_policy"] != "fold_meet_halfway":
            continue
        high_cell_id = seam.get("high_cell")
        low_cell_id = seam.get("low_cell")
        if high_cell_id is None or low_cell_id is None:
            continue
        high_plot = plot_by_id[high_cell_id]
        low_plot = plot_by_id[low_cell_id]
        va = vertex_by_id[seam["corner_vertex_ids"][0]]
        vb = vertex_by_id[seam["corner_vertex_ids"][1]]
        edge_a = (float(va["world_x"]), float(va["world_y"]))
        edge_b = (float(vb["world_x"]), float(vb["world_y"]))
        high_center = (float(high_plot["center"][0]), float(high_plot["center"][1]))
        low_center = (float(low_plot["center"][0]), float(low_plot["center"][1]))
        high_z = float(high_plot["center_height"]) + Z_OFFSET + 0.025
        low_z = float(low_plot["center_height"]) + Z_OFFSET + 0.025
        mid_z = float(seam.get("mid_height", (high_z + low_z) * 0.5)) + Z_OFFSET + 0.025

        high_a = lerp2(edge_a, high_center, fold_width_ratio)
        high_b = lerp2(edge_b, high_center, fold_width_ratio)
        low_a = lerp2(edge_a, low_center, fold_width_ratio)
        low_b = lerp2(edge_b, low_center, fold_width_ratio)
        start = len(vertices)
        vertices.extend(
            [
                (high_a[0], high_a[1], high_z),
                (high_b[0], high_b[1], high_z),
                (edge_b[0], edge_b[1], mid_z),
                (edge_a[0], edge_a[1], mid_z),
                (low_a[0], low_a[1], low_z),
                (low_b[0], low_b[1], low_z),
            ]
        )
        faces.append((start, start + 1, start + 2, start + 3))
        faces.append((start + 3, start + 2, start + 5, start + 4))
        fold_count += 1
    return make_mesh_object(
        f"{graph['graph_id']}.fold_meet_halfway_mesh",
        vertices,
        faces,
        material,
        parent,
        {
            "mesh_role": "fold_meet_halfway_mesh",
            "seam_policy": "fold_meet_halfway",
            "fold_count": fold_count,
            "face_count": len(faces),
            "fold_width_ratio": round(fold_width_ratio, 6),
        },
    )


def make_corner_seam_cap_mesh(graph: dict[str, Any], material: bpy.types.Material, parent: bpy.types.Object) -> bpy.types.Object:
    radius = float(graph["hex_grid"]["radius"]) * 0.10
    ring = [
        (
            radius * math.cos(math.radians(30.0 + i * 60.0)),
            radius * math.sin(math.radians(30.0 + i * 60.0)),
        )
        for i in range(6)
    ]
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    cap_count = 0
    for cap in graph.get("corner_seam_caps", []):
        bottom = float(cap["height_min"]) + Z_OFFSET
        top = float(cap["height_max"]) + Z_OFFSET
        if top <= bottom:
            continue
        x = float(cap["world_x"])
        y = float(cap["world_y"])
        start = len(vertices)
        vertices.extend((x + px, y + py, bottom) for px, py in ring)
        vertices.extend((x + px, y + py, top) for px, py in ring)
        for i in range(6):
            j = (i + 1) % 6
            faces.append((start + i, start + j, start + 6 + j, start + 6 + i))
        faces.append(tuple(reversed(range(start, start + 6))))
        faces.append(tuple(range(start + 6, start + 12)))
        cap_count += 1
    return make_mesh_object(
        f"{graph['graph_id']}.corner_seam_cap_mesh",
        vertices,
        faces,
        material,
        parent,
        {
            "mesh_role": "corner_seam_cap_mesh",
            "seam_policy": "corner_seam_cap",
            "cap_count": cap_count,
            "face_count": len(faces),
        },
    )


def make_filtered_socket_marker_mesh(graph: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    radius = float(graph["hex_grid"]["radius"]) * 0.12
    points = [
        (
            radius * math.cos(math.radians(30.0 + i * 60.0)),
            radius * math.sin(math.radians(30.0 + i * 60.0)),
        )
        for i in range(6)
    ]
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    socket_count = 0
    for socket in graph["socket_summary"]["sockets"]:
        x, y, z = [float(v) for v in socket["position"]]
        if z < 2.0:
            continue
        socket_count += 1
        start = len(vertices)
        vertices.extend((x + px, y + py, z + 0.18) for px, py in points)
        faces.append(tuple(range(start, start + 6)))
    return make_mesh_object(
        f"{graph['graph_id']}.high_socket_marker_mesh",
        vertices,
        faces,
        materials["socket"],
        parent,
        {
            "mesh_role": "high_socket_marker_mesh",
            "socket_count": socket_count,
            "filter_rule": "position_z_gte_2m",
        },
    )


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.76, 0.78, 0.80)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -12.0, 16.0))
    light = bpy.context.object
    light.name = "hex_seam_policy_area_light"
    light.data.energy = 760.0
    light.data.size = 12.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((18.0, -24.0, 16.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.08
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
    blend_path, render_path, report_path = output_paths()
    graph = load_json(selected_graph_path())

    materials = {
        "outer_flat": make_material("mat_seam_outer_flat", (0.24, 0.38, 0.33, 1.0)),
        "lower_slope": make_material("mat_seam_lower_slope", (0.33, 0.49, 0.35, 1.0)),
        "upper_slope": make_material("mat_seam_upper_slope", (0.49, 0.58, 0.35, 1.0)),
        "hilltop": make_material("mat_seam_hilltop", (0.65, 0.59, 0.37, 1.0)),
        "split_riser": make_material("mat_split_riser", (0.52, 0.43, 0.32, 1.0)),
        "split_cliff": make_material("mat_split_cliff", (0.36, 0.19, 0.16, 1.0)),
        "fold_meet_halfway": make_material("mat_fold_meet_halfway", (0.40, 0.50, 0.33, 1.0)),
        "corner_cap": make_material("mat_corner_seam_cap", (0.48, 0.39, 0.29, 1.0)),
        "chunk_skirt": make_material("mat_chunk_skirt", (0.18, 0.20, 0.19, 1.0)),
        "socket": make_material("mat_seam_socket", (0.96, 0.60, 0.18, 1.0)),
    }

    created: list[bpy.types.Object] = []
    root = create_empty(
        graph["graph_id"],
        (0.0, 0.0, 0.0),
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        None,
        {
            "graph_id": graph["graph_id"],
            "proof": "hex_seam_policy_v0",
        },
    )
    created.append(root)
    created.append(make_connected_top_mesh(graph, materials, root))
    created.append(make_fold_meet_halfway_mesh(graph, materials["fold_meet_halfway"], root))
    created.append(make_seam_wall_mesh(graph, "split_riser", "split_riser_mesh", materials["split_riser"], root))
    created.append(make_seam_wall_mesh(graph, "split_cliff", "split_cliff_mesh", materials["split_cliff"], root))
    created.append(make_corner_seam_cap_mesh(graph, materials["corner_cap"], root))
    created.append(make_seam_wall_mesh(graph, "chunk_skirt", "chunk_skirt_mesh", materials["chunk_skirt"], root))
    created.append(make_filtered_socket_marker_mesh(graph, materials, root))

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    mesh_faces = {
        obj["mesh_role"]: len(obj.data.polygons)
        for obj in created
        if obj.type == "MESH" and "mesh_role" in obj
    }
    report = {
        "schema": "hex_seam_policy_blender_proof_v0",
        "graph_id": graph["graph_id"],
        "plot_count": len(graph["hex_plots"]),
        "corner_vertex_count": len(graph["corner_vertices"]),
        "edge_midpoint_count": len(graph.get("edge_midpoints", [])),
        "vertex_split_summary": graph["vertex_split_summary"],
        "edge_midpoint_summary": graph.get("edge_midpoint_summary", {}),
        "corner_seam_cap_count": len(graph.get("corner_seam_caps", [])),
        "top_triangle_count": graph["mesh_plan"]["top_triangle_count"],
        "validation": graph.get("validation", {}),
        "edge_summary": graph["edge_summary"],
        "connector_summary": graph["connector_summary"],
        "seam_policy_summary": graph["seam_policy_summary"],
        "delta_band_summary": graph.get("delta_band_summary", {}),
        "profile_rule_summary": graph.get("profile_rule_summary", {}),
        "seam_fact_count": len(graph["seam_facts"]),
        "mesh_faces": mesh_faces,
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "empty_object_count": empty_count,
        "blend_path": str(blend_path.relative_to(ROOT)),
        "render_path": str(render_path.relative_to(ROOT)),
        "rules": {
            "proof_scene_only": True,
            "shared_surface_uses_shared_corner_vertices": True,
            "shared_surface_uses_shared_edge_midpoints": True,
            "top_surface_uses_12_triangle_radial_fan": bool(graph.get("edge_midpoints")),
            "split_riser_edges_emit_vertical_mesh": True,
            "fold_meet_halfway_edges_emit_two_sloped_fold_faces": True,
            "split_cliff_edges_emit_vertical_mesh": True,
            "chunk_boundary_edges_emit_skirt_mesh": True,
            "bottom_faces": 0,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True,
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {blend_path.relative_to(ROOT)}")
    print(f"wrote {render_path.relative_to(ROOT)}")
    print(f"wrote {report_path.relative_to(ROOT)}")
    print(
        f"graph plots={len(graph['hex_plots'])} corners={len(graph['corner_vertices'])} "
        f"seam_facts={len(graph['seam_facts'])}"
    )
    print(f"mesh_faces={mesh_faces}")


if __name__ == "__main__":
    main()
