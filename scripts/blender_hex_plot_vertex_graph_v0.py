#!/usr/bin/env python3
"""Render hex_plot_vertex_graph_v0 as a connected shared-corner terrain surface.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_hex_plot_vertex_graph_v0.py

This is the visual proof that hexes are now plots with shared corner vertices,
edge profiles, connectors, and sockets instead of isolated flat cells.
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


GRAPH_DIR = ROOT / "goal" / "architecture" / "hex_plot_vertex_graph_v0" / "graphs"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "hex_plot_vertex_graph_v0.blend"
RENDER_PATH = OUT_DIR / "hex_plot_vertex_graph_v0_workbench.png"
REPORT_PATH = OUT_DIR / "hex_plot_vertex_graph_v0_report.json"


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
        vertices.append((float(vertex["world_x"]), float(vertex["world_y"]), float(vertex["final_height"]) + 0.035))

    faces: list[tuple[int, ...]] = []
    roles: list[str] = []
    for plot in graph["hex_plots"]:
        center_id = f"center_{plot['cell_id']}"
        vertex_index[center_id] = len(vertices)
        vertices.append((float(plot["center"][0]), float(plot["center"][1]), float(plot["center_height"]) + 0.035))
        center_index = vertex_index[center_id]
        corners = [vertex_index[vertex_id] for vertex_id in plot["corner_vertex_ids"]]
        for i in range(6):
            faces.append((center_index, corners[i], corners[(i + 1) % 6]))
            roles.append(plot["plot_role"])

    obj = make_mesh_object(
        f"{graph['graph_id']}.connected_top_mesh",
        vertices,
        faces,
        materials["outer_flat"],
        parent,
        {
            "mesh_role": "connected_top_mesh",
            "surface_join_model": graph["mesh_plan"]["surface_join_model"],
            "corner_vertex_count": len(graph["corner_vertices"]),
            "plot_count": len(graph["hex_plots"]),
        },
    )
    obj.data.materials.clear()
    for name in material_order:
        obj.data.materials.append(materials[name])
    for poly, role in zip(obj.data.polygons, roles, strict=True):
        poly.material_index = role_material_index(role, material_order)
    return obj


def make_boundary_side_mesh(graph: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    vertex_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for plot in graph["hex_plots"]:
        for edge in plot["edges"]:
            if edge["edge_profile"] != "chunk_boundary":
                continue
            va = vertex_by_id[edge["corner_vertex_ids"][0]]
            vb = vertex_by_id[edge["corner_vertex_ids"][1]]
            top_a = float(va["final_height"]) + 0.035
            top_b = float(vb["final_height"]) + 0.035
            start = len(vertices)
            vertices.extend(
                [
                    (float(va["world_x"]), float(va["world_y"]), 0.0),
                    (float(vb["world_x"]), float(vb["world_y"]), 0.0),
                    (float(vb["world_x"]), float(vb["world_y"]), top_b),
                    (float(va["world_x"]), float(va["world_y"]), top_a),
                ]
            )
            faces.append((start, start + 1, start + 2, start + 3))
    return make_mesh_object(
        f"{graph['graph_id']}.boundary_side_mesh",
        vertices,
        faces,
        materials["side_wall"],
        parent,
        {
            "mesh_role": "boundary_side_mesh",
            "face_count": len(faces),
        },
    )


def make_edge_marker_mesh(graph: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    vertex_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    vertices: list[tuple[float, float, float]] = []
    edges_out: list[tuple[int, int]] = []
    seen: set[tuple[str, str]] = set()
    for plot in graph["hex_plots"]:
        for edge in plot["edges"]:
            if edge["edge_profile"] not in {"hard_step", "cliff_drop"}:
                continue
            a, b = edge["corner_vertex_ids"]
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            va = vertex_by_id[a]
            vb = vertex_by_id[b]
            start = len(vertices)
            vertices.extend(
                [
                    (float(va["world_x"]), float(va["world_y"]), float(va["final_height"]) + 0.12),
                    (float(vb["world_x"]), float(vb["world_y"]), float(vb["final_height"]) + 0.12),
                ]
            )
            edges_out.append((start, start + 1))
    mesh = bpy.data.meshes.new(f"{graph['graph_id']}.hard_seam_marker_mesh")
    mesh.from_pydata(vertices, edges_out, [])
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(f"{graph['graph_id']}.hard_seam_marker_mesh", mesh)
    obj.parent = parent
    obj.data.materials.append(materials["hard_seam"])
    obj["mesh_role"] = "hard_seam_marker_mesh"
    obj["edge_count"] = len(edges_out)
    bpy.context.collection.objects.link(obj)
    return obj


def make_socket_marker_mesh(graph: dict[str, Any], materials: dict[str, bpy.types.Material], parent: bpy.types.Object) -> bpy.types.Object:
    radius = float(graph["hex_grid"]["radius"]) * 0.16
    points = [
        (
            radius * math.cos(math.radians(30.0 + i * 60.0)),
            radius * math.sin(math.radians(30.0 + i * 60.0)),
        )
        for i in range(6)
    ]
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for socket in graph["socket_summary"]["sockets"]:
        x, y, z = [float(v) for v in socket["position"]]
        start = len(vertices)
        vertices.extend((x + px, y + py, z + 0.14) for px, py in points)
        faces.append(tuple(range(start, start + 6)))
    return make_mesh_object(
        f"{graph['graph_id']}.socket_marker_mesh",
        vertices,
        faces,
        materials["socket"],
        parent,
        {
            "mesh_role": "socket_marker_mesh",
            "socket_count": graph["socket_summary"]["socket_count"],
        },
    )


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -11.0, 15.0))
    light = bpy.context.object
    light.name = "hex_plot_vertex_graph_area_light"
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
    graph_paths = sorted(GRAPH_DIR.glob("*.json"))
    if not graph_paths:
        raise FileNotFoundError(f"no hex plot vertex graphs found in {GRAPH_DIR}")
    graph = load_json(graph_paths[0])

    materials = {
        "outer_flat": make_material("mat_plot_outer_flat", (0.25, 0.38, 0.33, 1.0)),
        "lower_slope": make_material("mat_plot_lower_slope", (0.34, 0.48, 0.34, 1.0)),
        "upper_slope": make_material("mat_plot_upper_slope", (0.46, 0.56, 0.35, 1.0)),
        "hilltop": make_material("mat_plot_hilltop", (0.62, 0.58, 0.38, 1.0)),
        "side_wall": make_material("mat_plot_boundary_side_wall", (0.22, 0.24, 0.22, 1.0)),
        "hard_seam": make_material("mat_plot_hard_seam", (0.91, 0.28, 0.12, 1.0)),
        "socket": make_material("mat_plot_socket", (0.95, 0.55, 0.20, 1.0)),
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
            "corner_vertex_count": len(graph["corner_vertices"]),
            "plot_count": len(graph["hex_plots"]),
        },
    )
    created.append(root)
    created.append(make_connected_top_mesh(graph, materials, root))
    created.append(make_boundary_side_mesh(graph, materials, root))
    created.append(make_edge_marker_mesh(graph, materials, root))
    created.append(make_socket_marker_mesh(graph, materials, root))

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    report = {
        "schema": "hex_plot_vertex_graph_blender_proof_v0",
        "graph_id": graph["graph_id"],
        "plot_count": len(graph["hex_plots"]),
        "corner_vertex_count": len(graph["corner_vertices"]),
        "top_triangle_count": graph["mesh_plan"]["top_triangle_count"],
        "socket_count": graph["socket_summary"]["socket_count"],
        "edge_summary": graph["edge_summary"],
        "connector_summary": graph["connector_summary"],
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "empty_object_count": empty_count,
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "rules": {
            "proof_scene_only": True,
            "hex_cells_are_plots": True,
            "shared_corner_vertices": True,
            "triangle_fan_top_mesh": True,
            "edge_profiles_visualized": True,
            "sockets_visualized": True,
            "hard_seam_splitting_deferred": True,
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
        f"graph plots={len(graph['hex_plots'])} corners={len(graph['corner_vertices'])} "
        f"sockets={graph['socket_summary']['socket_count']}"
    )
    print(f"objects_created={len(created)} mesh={mesh_count} empty={empty_count}")


if __name__ == "__main__":
    main()
