#!/usr/bin/env python3
"""Render Terrain Profile Bending v0 proof scenes.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_terrain_profile_bending_v0.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
PROFILED_GRAPH_DIR = ROOT / "goal" / "architecture" / "terrain_profile_bending_v0" / "profiled_graphs"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "terrain_profile_bending_v0.blend"
RENDER_PATH = OUT_DIR / "terrain_profile_bending_v0_workbench.png"
REPORT_PATH = OUT_DIR / "terrain_profile_bending_v0_report.json"
Z_OFFSET = 0.04


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def make_mesh_object(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    materials: list[bpy.types.Material],
    material_indices: list[int],
    props: dict[str, Any],
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    for material in materials:
        obj.data.materials.append(material)
    for poly, material_index in zip(obj.data.polygons, material_indices, strict=True):
        poly.material_index = material_index
    for key, value in props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def material_index_for_law(law: str) -> int:
    order = ["soft_slope", "road_grade", "flat_pad", "terrace_step", "ravine_fold", "cliff_fault", "side_wall", "boundary_wall"]
    return order.index(law) if law in order else order.index("soft_slope")


def add_graph_mesh(graph: dict[str, Any], offset_x: float, materials: list[bpy.types.Material]) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[str, int] = {}
    for vertex in graph["corner_vertices"]:
        vertex_index[vertex["vertex_id"]] = len(vertices)
        vertices.append((float(vertex["world_x"]) + offset_x, float(vertex["world_y"]), float(vertex["profiled_height_m"]) + Z_OFFSET))
    for midpoint in graph["edge_midpoints"]:
        vertex_index[midpoint["midpoint_id"]] = len(vertices)
        vertices.append((float(midpoint["world_x"]) + offset_x, float(midpoint["world_y"]), float(midpoint["profiled_height_m"]) + Z_OFFSET))

    plot_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []
    for plot in graph["hex_plots"]:
        center_id = f"center_{plot['cell_id']}"
        vertex_index[center_id] = len(vertices)
        vertices.append((float(plot["center"][0]) + offset_x, float(plot["center"][1]), float(plot["profiled_center_height_m"]) + Z_OFFSET))
        center_index = vertex_index[center_id]
        corners = [vertex_index[vertex_id] for vertex_id in plot["corner_vertex_ids"]]
        midpoints = [vertex_index[midpoint_id] for midpoint_id in plot["edge_midpoint_ids"]]
        law_index = material_index_for_law(plot["profile_law"])
        for i in range(6):
            faces.append((center_index, corners[i], midpoints[i]))
            material_indices.append(law_index)
            faces.append((center_index, midpoints[i], corners[(i + 1) % 6]))
            material_indices.append(law_index)

    corner_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    for seam in graph["seam_facts"]:
        if seam["seam_policy"] not in {"split_cliff", "split_riser", "chunk_skirt"}:
            continue
        high_cell = seam.get("high_cell")
        low_cell = seam.get("low_cell")
        if high_cell is None:
            continue
        high_plot = plot_by_id[high_cell]
        top = float(high_plot["profiled_center_height_m"]) + Z_OFFSET
        bottom = 0.0 if low_cell is None else float(plot_by_id[low_cell]["profiled_center_height_m"]) + Z_OFFSET
        if top <= bottom:
            continue
        va = corner_by_id[seam["corner_vertex_ids"][0]]
        vb = corner_by_id[seam["corner_vertex_ids"][1]]
        start = len(vertices)
        vertices.extend(
            [
                (float(va["world_x"]) + offset_x, float(va["world_y"]), bottom),
                (float(vb["world_x"]) + offset_x, float(vb["world_y"]), bottom),
                (float(vb["world_x"]) + offset_x, float(vb["world_y"]), top),
                (float(va["world_x"]) + offset_x, float(va["world_y"]), top),
            ]
        )
        faces.append((start, start + 1, start + 2, start + 3))
        material_indices.append(material_index_for_law("boundary_wall" if low_cell is None else "side_wall"))

    return make_mesh_object(
        f"{graph['graph_id']}.profiled_mesh",
        vertices,
        faces,
        materials,
        material_indices,
        {
            "mesh_role": "terrain_profile_bending_v0_mesh",
            "graph_id": graph["graph_id"],
            "top_triangle_count": graph["mesh_plan"]["top_triangle_count"],
            "cracked_seam_count": graph["profile_validation"]["cracked_seam_count"],
            "profile_law_counts": json.dumps(graph["profile_summary"]["profile_law_counts"], sort_keys=True),
        },
    )


def add_label(text: str, x: float, y: float, z: float, material: bpy.types.Material) -> None:
    bpy.ops.object.text_add(location=(x, y, z), rotation=(math.radians(70.0), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = f"{text}.label"
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = 0.42
    obj.data.materials.append(material)


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not mesh_objects:
        return mathutils.Vector((-8, -8, 0)), mathutils.Vector((8, 8, 4))
    points: list[mathutils.Vector] = []
    for obj in mesh_objects:
        points.extend(obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box)
    mins = mathutils.Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maxs = mathutils.Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return mins, maxs


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.76, 0.78, 0.80)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -15.0, 18.0))
    light = bpy.context.object
    light.name = "terrain_profile_bending_area_light"
    light.data.energy = 900.0
    light.data.size = 14.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((9.0, -28.0, 17.0)))
    cam = bpy.context.object
    cam.name = "terrain_profile_bending_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 0.86
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 2200
    bpy.context.scene.render.resolution_y = 1100
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    materials = [
        make_material("mat_profile_soft_slope", (0.29, 0.54, 0.34, 1.0)),
        make_material("mat_profile_road_grade", (0.70, 0.64, 0.46, 1.0)),
        make_material("mat_profile_flat_pad", (0.78, 0.62, 0.30, 1.0)),
        make_material("mat_profile_terrace_step", (0.52, 0.51, 0.46, 1.0)),
        make_material("mat_profile_ravine_fold", (0.42, 0.18, 0.16, 1.0)),
        make_material("mat_profile_cliff_fault", (0.30, 0.23, 0.20, 1.0)),
        make_material("mat_profile_side_wall", (0.34, 0.31, 0.27, 1.0)),
        make_material("mat_profile_boundary_wall", (0.20, 0.21, 0.20, 1.0)),
    ]
    label_material = make_material("mat_profile_label", (0.06, 0.08, 0.08, 1.0))

    graphs = [load_json(path) for path in sorted(PROFILED_GRAPH_DIR.glob("*_profiled_graph.json"))]
    created = []
    for index, graph in enumerate(graphs):
        offset_x = index * 9.0
        created.append(add_graph_mesh(graph, offset_x, materials))
        add_label(graph["source_shared_graph_id"].replace("_plot_vertex_graph", ""), offset_x, -4.4, 0.2, label_material)

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    report = {
        "schema": "terrain_profile_bending_blender_report_v0",
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "profiled_graph_count": len(graphs),
        "graphs": [
            {
                "graph_id": graph["source_shared_graph_id"],
                "profile_law_counts": graph["profile_summary"]["profile_law_counts"],
                "profile_validation": graph["profile_validation"],
            }
            for graph in graphs
        ],
        "mesh_object_count": len(created),
        "rules": {
            "uses_profiled_center_heights": True,
            "uses_profiled_corner_heights": True,
            "uses_profiled_edge_midpoint_heights": True,
            "renders_split_cliff_and_boundary_walls": True,
            "debug_render_only": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"profiled_graphs={len(graphs)} meshes={len(created)}")


if __name__ == "__main__":
    main()
