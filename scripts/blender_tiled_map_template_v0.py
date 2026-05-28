#!/usr/bin/env python3
"""Render compiled Tiled-style map templates in Blender.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_tiled_map_template_v0.py

This creates a debug scene with:
- one visible-face terrain mesh
- road/path overlays
- building plot pads
- hazard edges
- asset socket proxy geometry
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
COMPILED_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "compiled" / "tiled_hex_map_template_v0_compiled.json"
SHARED_TERRAIN_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "shared_terrain" / "tiled_hex_map_template_v0_shared_terrain_graph.json"
PROFILED_TERRAIN_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "profiled_terrain" / "tiled_hex_map_template_v0_profiled_terrain_graph.json"
REFINED_TERRAIN_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "road_plot_refined" / "tiled_hex_map_template_v0_road_plot_refined_graph.json"
SEMANTIC_TERRAIN_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "gameplay_surface_semantics" / "tiled_hex_map_template_v0_gameplay_surface_semantics_graph.json"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "map_gameplay_surface_semantics_v0.blend"
RENDER_PATH = OUT_DIR / "map_gameplay_surface_semantics_v0_workbench.png"
REPORT_PATH = OUT_DIR / "map_gameplay_surface_semantics_v0_report.json"


AXIAL_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
EDGE_CORNER_PAIRS = [(5, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
DEFAULT_HEX_RADIUS = 0.55


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


def hex_corners(cx: float, cy: float, z: float, radius: float = DEFAULT_HEX_RADIUS) -> list[tuple[float, float, float]]:
    return [
        (
            cx + radius * math.cos(math.radians(30.0 + 60.0 * index)),
            cy + radius * math.sin(math.radians(30.0 + 60.0 * index)),
            z,
        )
        for index in range(6)
    ]


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


def terrain_material_index(surface_type: str) -> int:
    order = [
        "grass",
        "road",
        "stone",
        "ravine_edge",
        "building_plot",
        "side_wall",
        "boundary_wall",
        "semantic_walkable",
        "semantic_blocked",
        "semantic_road",
        "semantic_building_pad",
        "semantic_foundation_edge",
        "semantic_retaining_edge",
        "semantic_ledge",
        "semantic_cliff",
        "semantic_slope",
        "semantic_choke",
        "semantic_cover_candidate",
        "semantic_fall_hazard",
        "semantic_los_breaker",
        "semantic_asset_socket",
    ]
    return order.index(surface_type) if surface_type in order else order.index("stone")


def shared_terrain_graph() -> dict[str, Any] | None:
    if SEMANTIC_TERRAIN_GRAPH_PATH.exists():
        return load_json(SEMANTIC_TERRAIN_GRAPH_PATH)
    if REFINED_TERRAIN_GRAPH_PATH.exists():
        return load_json(REFINED_TERRAIN_GRAPH_PATH)
    if PROFILED_TERRAIN_GRAPH_PATH.exists():
        return load_json(PROFILED_TERRAIN_GRAPH_PATH)
    if not SHARED_TERRAIN_GRAPH_PATH.exists():
        return None
    return load_json(SHARED_TERRAIN_GRAPH_PATH)


def graph_height_for_vertex(row: dict[str, Any]) -> float:
    return float(row.get("refined_height_m", row.get("profiled_height_m", row.get("height_m", row.get("final_height", 0.0)))))


def graph_height_for_plot(plot: dict[str, Any]) -> float:
    return float(plot.get("refined_center_height_m", plot.get("profiled_center_height_m", plot.get("center_height", 0.0))))


def active_terrain_graph_path() -> Path:
    if SEMANTIC_TERRAIN_GRAPH_PATH.exists():
        return SEMANTIC_TERRAIN_GRAPH_PATH
    if REFINED_TERRAIN_GRAPH_PATH.exists():
        return REFINED_TERRAIN_GRAPH_PATH
    if PROFILED_TERRAIN_GRAPH_PATH.exists():
        return PROFILED_TERRAIN_GRAPH_PATH
    return SHARED_TERRAIN_GRAPH_PATH


def terrain_validation_for_report(graph: dict[str, Any] | None) -> dict[str, Any] | None:
    if graph is None:
        return None
    return graph.get("map_gameplay_surface_semantics_v0", {}).get(
        "validation",
        graph.get("profile_aware_road_plot_refinement_v0", {}).get(
            "validation",
            graph.get("map_template_profile_application_v0", {}).get(
                "validation",
                graph.get("profile_validation", graph.get("validation")),
            ),
        ),
    )


def make_shared_terrain_mesh(graph: dict[str, Any], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    material_order_names = [
        "grass",
        "road",
        "stone",
        "ravine_edge",
        "building_plot",
        "side_wall",
        "boundary_wall",
        "semantic_walkable",
        "semantic_blocked",
        "semantic_road",
        "semantic_building_pad",
        "semantic_foundation_edge",
        "semantic_retaining_edge",
        "semantic_ledge",
        "semantic_cliff",
        "semantic_slope",
        "semantic_choke",
        "semantic_cover_candidate",
        "semantic_fall_hazard",
        "semantic_los_breaker",
        "semantic_asset_socket",
    ]
    material_order = [materials[name] for name in material_order_names]
    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[str, int] = {}
    for vertex in graph["corner_vertices"]:
        vertex_index[vertex["vertex_id"]] = len(vertices)
        vertices.append((float(vertex["world_x"]), float(vertex["world_y"]), graph_height_for_vertex(vertex)))
    for midpoint in graph["edge_midpoints"]:
        vertex_index[midpoint["midpoint_id"]] = len(vertices)
        vertices.append((float(midpoint["world_x"]), float(midpoint["world_y"]), graph_height_for_vertex(midpoint)))

    plot_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []
    for plot in graph["hex_plots"]:
        center_id = f"center_{plot['cell_id']}"
        vertex_index[center_id] = len(vertices)
        vertices.append((float(plot["center"][0]), float(plot["center"][1]), graph_height_for_plot(plot)))
        center_index = vertex_index[center_id]
        corner_indices = [vertex_index[vertex_id] for vertex_id in plot["corner_vertex_ids"]]
        midpoint_indices = [vertex_index[midpoint_id] for midpoint_id in plot["edge_midpoint_ids"]]
        material_index = terrain_material_index(str(plot.get("semantic_debug_surface_type", plot.get("surface_type", "stone"))))
        for i in range(6):
            faces.append((center_index, corner_indices[i], midpoint_indices[i]))
            material_indices.append(material_index)
            faces.append((center_index, midpoint_indices[i], corner_indices[(i + 1) % 6]))
            material_indices.append(material_index)

    corner_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}
    for seam in graph["seam_facts"]:
        if seam["seam_policy"] not in {"split_cliff", "split_riser", "chunk_skirt"}:
            continue
        high_cell = seam.get("high_cell")
        low_cell = seam.get("low_cell")
        if high_cell is None:
            continue
        top = graph_height_for_plot(plot_by_id[high_cell])
        bottom = 0.0 if low_cell is None else graph_height_for_plot(plot_by_id[low_cell])
        if top <= bottom:
            continue
        va = corner_by_id[seam["corner_vertex_ids"][0]]
        vb = corner_by_id[seam["corner_vertex_ids"][1]]
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
        material_indices.append(terrain_material_index("boundary_wall" if low_cell is None else "side_wall"))

    return make_mesh_object(
        f"{graph['graph_id']}.shared_midpoint_terrain_mesh",
        vertices,
        faces,
        material_order,
        material_indices,
        {
            "mesh_role": "shared_midpoint_terrain_mesh",
            "graph_id": graph["graph_id"],
            "cell_count": len(graph["hex_plots"]),
            "top_triangle_count": graph["mesh_plan"]["top_triangle_count"],
            "cracked_seam_count": graph.get("profile_validation", graph.get("validation", {})).get("cracked_seam_count", 0),
            "height_source": graph["mesh_plan"].get("height_source", "height_m"),
            "no_internal_same_height_walls": True,
        },
    )


def make_terrain_mesh(compiled: dict[str, Any], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    graph = shared_terrain_graph()
    if graph is not None:
        return make_shared_terrain_mesh(graph, materials)

    cells = compiled["cells"]
    by_coord = {(cell["q"], cell["r"]): cell for cell in cells}
    hex_radius = float(compiled.get("hex_radius_m", DEFAULT_HEX_RADIUS))
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []

    for cell in cells:
        cx = float(cell["world_x"])
        cy = float(cell["world_y"])
        top_z = float(cell["final_height"])
        corners = hex_corners(cx, cy, top_z, hex_radius)
        start = len(vertices)
        vertices.extend(corners)
        faces.append(tuple(start + i for i in range(6)))
        material_indices.append(terrain_material_index(cell["surface_type"]))

        for direction_index, (dq, dr) in enumerate(AXIAL_DIRECTIONS):
            neighbor = by_coord.get((cell["q"] + dq, cell["r"] + dr))
            if neighbor is not None and float(neighbor["final_height"]) >= top_z:
                continue
            bottom_z = float(neighbor["final_height"]) if neighbor is not None else 0.0
            if top_z <= bottom_z:
                continue
            ca, cb = EDGE_CORNER_PAIRS[direction_index]
            top_a = corners[ca]
            top_b = corners[cb]
            side_start = len(vertices)
            vertices.extend(
                [
                    (top_a[0], top_a[1], bottom_z),
                    (top_b[0], top_b[1], bottom_z),
                    top_b,
                    top_a,
                ]
            )
            faces.append((side_start, side_start + 1, side_start + 2, side_start + 3))
            material_indices.append(terrain_material_index("boundary_wall" if neighbor is None else "side_wall"))

    material_order = [
        materials["grass"],
        materials["road"],
        materials["stone"],
        materials["ravine_edge"],
        materials["building_plot"],
        materials["side_wall"],
        materials["boundary_wall"],
    ]
    return make_mesh_object(
        f"{compiled['template_id']}.visible_face_terrain_mesh",
        vertices,
        faces,
        material_order,
        material_indices,
        {
            "mesh_role": "visible_face_terrain_mesh",
            "template_id": compiled["template_id"],
            "cell_count": len(cells),
            "no_internal_same_height_walls": True,
        },
    )


def make_curve(
    name: str,
    points: list[tuple[float, float, float]],
    bevel_depth: float,
    material: bpy.types.Material,
    props: dict[str, Any],
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for spline_point, point in zip(spline.points, points, strict=True):
        spline_point.co = (point[0], point[1], point[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    for key, value in props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def make_plot_pad(plot: dict[str, Any], material: bpy.types.Material) -> bpy.types.Object:
    polygon = [(float(x), float(y)) for x, y in plot["polygon"]]
    cx = sum(x for x, _y in polygon) / len(polygon)
    cy = sum(y for _x, y in polygon) / len(polygon)
    graph = shared_terrain_graph()
    if graph is not None:
        nearest = min(graph["hex_plots"], key=lambda item: math.hypot(float(item["center"][0]) - cx, float(item["center"][1]) - cy))
        z = graph_height_for_plot(nearest) + 0.08
    else:
        z = float(plot["average_height"]) + 0.08
    vertices = [(x, y, z) for x, y in polygon]
    faces = [tuple(range(len(vertices)))]
    return make_mesh_object(
        f"{plot['plot_id']}.building_plot_pad",
        vertices,
        faces,
        [material],
        [0],
        {
            "mesh_role": "building_plot_pad",
            "plot_id": plot["plot_id"],
            "floor_plan_ref": plot.get("floor_plan_ref", ""),
            "recommended_asset_kit": plot.get("recommended_asset_kit", ""),
        },
    )


def add_cube(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    material: bpy.types.Material,
    props: dict[str, Any],
    rotation_z_degrees: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=(0.0, 0.0, math.radians(rotation_z_degrees)))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for key, value in props.items():
        obj[key] = value
    return obj


def add_cylinder(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    vertices: int,
    material: bpy.types.Material,
    props: dict[str, Any],
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    for key, value in props.items():
        obj[key] = value
    return obj


def add_socket_proxy(socket: dict[str, Any], material: bpy.types.Material, accent: bpy.types.Material) -> list[bpy.types.Object]:
    x, y, z = [float(v) for v in socket["world_position"]]
    z += 0.18
    orientation = float(socket.get("orientation_degrees", 0.0))
    asset_ref = str(socket.get("asset_ref", "unknown"))
    props = {
        "mesh_role": "asset_socket_proxy",
        "socket_id": socket["socket_id"],
        "asset_ref": asset_ref,
        "socket_type": socket.get("socket_type", ""),
        "orientation_degrees": orientation,
    }
    created: list[bpy.types.Object] = []
    if "bridge" in asset_ref:
        created.append(add_cube(f"{socket['socket_id']}.bridge_proxy", (x, y, z + 0.08), (1.9, 0.34, 0.16), material, props, orientation))
        created.append(add_cube(f"{socket['socket_id']}.bridge_rail_a", (x, y - 0.26, z + 0.38), (1.9, 0.08, 0.12), accent, props, orientation))
        created.append(add_cube(f"{socket['socket_id']}.bridge_rail_b", (x, y + 0.26, z + 0.38), (1.9, 0.08, 0.12), accent, props, orientation))
        return created
    if "stair" in asset_ref:
        for i in range(4):
            created.append(add_cube(f"{socket['socket_id']}.stair_step_{i}", (x + i * 0.22, y, z + i * 0.08), (0.24, 0.55, 0.10), material, props, orientation))
        return created
    if any(token in asset_ref for token in ["arch", "doorway", "portal", "window", "oculus"]):
        created.append(add_cube(f"{socket['socket_id']}.left_jamb", (x - 0.28, y, z + 0.45), (0.12, 0.18, 0.9), material, props, orientation))
        created.append(add_cube(f"{socket['socket_id']}.right_jamb", (x + 0.28, y, z + 0.45), (0.12, 0.18, 0.9), material, props, orientation))
        created.append(add_cube(f"{socket['socket_id']}.arch_header", (x, y, z + 0.91), (0.72, 0.18, 0.14), accent, props, orientation))
        return created
    created.append(add_cylinder(f"{socket['socket_id']}.socket_marker", (x, y, z + 0.2), 0.16, 0.4, 8, material, props))
    return created


def cell_height_lookup(compiled: dict[str, Any]) -> dict[str, float]:
    return {cell["cell_id"]: float(cell["final_height"]) for cell in compiled["cells"]}


def nearest_cell_height(compiled: dict[str, Any], x: float, y: float) -> float:
    graph = shared_terrain_graph()
    if graph is not None:
        plot = min(graph["hex_plots"], key=lambda item: math.hypot(float(item["center"][0]) - x, float(item["center"][1]) - y))
        return graph_height_for_plot(plot)
    cell = min(compiled["cells"], key=lambda item: math.hypot(float(item["world_x"]) - x, float(item["world_y"]) - y))
    return float(cell["final_height"])


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.72, 0.75, 0.78)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -12.0, 14.0))
    light = bpy.context.object
    light.name = "tiled_map_template_area_light"
    light.data.energy = 800.0
    light.data.size = 9.0

    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    corners: list[mathutils.Vector] = []
    for obj in objs:
        if obj.type == "MESH":
            corners.extend(obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box)
    if corners:
        mins = mathutils.Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
        maxs = mathutils.Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    else:
        mins = mathutils.Vector((-16, -16, 0))
        maxs = mathutils.Vector((16, 16, 4))
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((16.0, -21.0, 16.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.18
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    compiled = load_json(COMPILED_PATH)
    graph = shared_terrain_graph()
    mats = {
        "grass": make_material("mat_terrain_grass", (0.23, 0.48, 0.29, 1.0)),
        "road": make_material("mat_road_stone", (0.48, 0.43, 0.35, 1.0)),
        "stone": make_material("mat_high_stone", (0.52, 0.51, 0.47, 1.0)),
        "ravine_edge": make_material("mat_ravine_hazard", (0.42, 0.20, 0.16, 1.0)),
        "building_plot": make_material("mat_building_plot", (0.62, 0.54, 0.35, 1.0)),
        "side_wall": make_material("mat_exposed_side_wall", (0.34, 0.32, 0.28, 1.0)),
        "boundary_wall": make_material("mat_chunk_boundary_wall", (0.22, 0.22, 0.20, 1.0)),
        "semantic_walkable": make_material("mat_semantic_walkable", (0.30, 0.62, 0.34, 1.0)),
        "semantic_blocked": make_material("mat_semantic_blocked", (0.28, 0.12, 0.12, 1.0)),
        "semantic_road": make_material("mat_semantic_road", (0.72, 0.62, 0.30, 1.0)),
        "semantic_building_pad": make_material("mat_semantic_building_pad", (0.86, 0.72, 0.36, 1.0)),
        "semantic_foundation_edge": make_material("mat_semantic_foundation_edge", (0.95, 0.55, 0.22, 1.0)),
        "semantic_retaining_edge": make_material("mat_semantic_retaining_edge", (0.62, 0.24, 0.16, 1.0)),
        "semantic_ledge": make_material("mat_semantic_ledge", (0.44, 0.36, 0.72, 1.0)),
        "semantic_cliff": make_material("mat_semantic_cliff", (0.18, 0.18, 0.18, 1.0)),
        "semantic_slope": make_material("mat_semantic_slope", (0.52, 0.70, 0.34, 1.0)),
        "semantic_choke": make_material("mat_semantic_choke", (0.82, 0.28, 0.78, 1.0)),
        "semantic_cover_candidate": make_material("mat_semantic_cover_candidate", (0.22, 0.48, 0.76, 1.0)),
        "semantic_fall_hazard": make_material("mat_semantic_fall_hazard", (0.88, 0.16, 0.12, 1.0)),
        "semantic_los_breaker": make_material("mat_semantic_los_breaker", (0.08, 0.10, 0.12, 1.0)),
        "semantic_asset_socket": make_material("mat_semantic_asset_socket", (0.20, 0.74, 0.82, 1.0)),
        "road_overlay": make_material("mat_road_overlay", (0.72, 0.67, 0.48, 1.0)),
        "hazard_overlay": make_material("mat_hazard_overlay", (0.86, 0.20, 0.12, 1.0)),
        "plot_pad": make_material("mat_plot_pad", (0.78, 0.60, 0.28, 1.0)),
        "socket": make_material("mat_asset_socket_proxy", (0.36, 0.52, 0.82, 1.0)),
        "socket_accent": make_material("mat_asset_socket_accent", (0.82, 0.72, 0.42, 1.0)),
    }

    make_terrain_mesh(compiled, mats)

    for road in compiled["roads"]:
        points = []
        for x, y in road["points"]:
            z = nearest_cell_height(compiled, float(x), float(y)) + 0.09
            points.append((float(x), float(y), z))
        make_curve(
            f"{road['road_id']}.road_overlay",
            points,
            float(road["width_m"]) * 0.18,
            mats["road_overlay"],
            {"curve_role": "road_overlay", "road_id": road["road_id"]},
        )

    for hazard in compiled["hazards"]:
        points = []
        for x, y in hazard["points"]:
            z = nearest_cell_height(compiled, float(x), float(y)) + 0.16
            points.append((float(x), float(y), z))
        make_curve(
            f"{hazard['hazard_id']}.hazard_edge_overlay",
            points,
            0.08,
            mats["hazard_overlay"],
            {"curve_role": "hazard_edge", "hazard_id": hazard["hazard_id"], "hazard_type": hazard["hazard_type"]},
        )

    for plot in compiled["building_plots"]:
        make_plot_pad(plot, mats["plot_pad"])

    socket_proxy_count = 0
    for socket in compiled["asset_sockets"]:
        socket_proxy_count += len(add_socket_proxy(socket, mats["socket"], mats["socket_accent"]))

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    report = {
        "schema": "tiled_map_template_blender_report_v0",
        "source_compiled_map": str(COMPILED_PATH.relative_to(ROOT)),
        "active_terrain_graph": str(active_terrain_graph_path().relative_to(ROOT)) if graph is not None else None,
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "cell_count": compiled["summary"]["cell_count"],
        "terrain_validation": terrain_validation_for_report(graph),
        "road_count": compiled["summary"]["road_count"],
        "building_plot_count": compiled["summary"]["building_plot_count"],
        "hazard_count": compiled["summary"]["hazard_count"],
        "asset_socket_count": compiled["summary"]["asset_socket_count"],
        "socket_proxy_object_count": socket_proxy_count,
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "rules": {
            "debug_render_only": True,
            "visible_face_terrain_mesh": graph is None,
            "shared_midpoint_radial_terrain_mesh": graph is not None,
            "gameplay_surface_semantics_graph": bool(graph and graph.get("schema") == "map_gameplay_surface_semantics_graph_v0"),
            "semantic_debug_coloring": bool(graph and graph.get("map_gameplay_surface_semantics_v0")),
            "profile_aware_road_plot_refinement_graph": bool(graph and graph.get("schema") == "profile_aware_road_plot_refined_graph_v0"),
            "profiled_terrain_graph": bool(graph and graph.get("schema") == "map_template_profiled_terrain_graph_v0"),
            "top_triangle_count_equals_cell_count_times_12": bool(graph and graph.get("profile_validation", graph.get("validation", {})).get("top_triangle_count_matches")),
            "cracked_seam_count_is_zero": bool(graph and graph.get("profile_validation", graph.get("validation", {})).get("cracked_seam_count") == 0),
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"cells={compiled['summary']['cell_count']} meshes={mesh_count} curves={curve_count} socket_proxy_objects={socket_proxy_count}")


if __name__ == "__main__":
    main()
