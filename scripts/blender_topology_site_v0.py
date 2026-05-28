#!/usr/bin/env python3
"""Realize topology_site_assembly_v0 JSON in Blender.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_topology_site_v0.py

This creates one proof scene where a compiled building assembly is planted on a
cliff-edge topology site through a foundation adapter.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "goal" / "architecture" / "topology_sites_v0" / "sites"
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "topology_site_cliff_ledge_v0.blend"
RENDER_PATH = OUT_DIR / "topology_site_cliff_ledge_v0_workbench.png"
REPORT_PATH = OUT_DIR / "topology_site_cliff_ledge_v0_report.json"


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


def euler_from_degrees(degrees: list[float]) -> tuple[float, float, float]:
    return tuple(math.radians(float(v)) for v in degrees)  # type: ignore[return-value]


def material_for_tags(materials: dict[str, bpy.types.Material], tags: list[str], role: str = "") -> bpy.types.Material:
    tag_set = set(tags)
    if role == "foundation":
        return materials["foundation"]
    if role == "retaining_wall":
        return materials["retaining_wall"]
    if "fall_edge" in tag_set:
        return materials["hazard"]
    if "route" in tag_set or "approach_vector" in tag_set:
        return materials["road"]
    if "walkable" in tag_set and "height_advantage" in tag_set:
        return materials["upper_terrain"]
    if "walkable" in tag_set:
        return materials["lower_terrain"]
    if "barrier" in tag_set or "rail" in tag_set:
        return materials["barrier"]
    if "support" in tag_set:
        return materials["support"]
    if "blocked" in tag_set or "line_of_sight_blocker" in tag_set:
        return materials["blocked"]
    return materials["default"]


def create_empty(
    name: str,
    location: tuple[float, float, float],
    rotation_degrees: list[float],
    scale: list[float],
    parent: bpy.types.Object | None,
    custom_props: dict[str, Any],
) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.45
    if parent is not None:
        obj.parent = parent
    obj.location = location
    obj.rotation_euler = euler_from_degrees(rotation_degrees)
    obj.scale = tuple(float(v) for v in scale)
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def create_box_mesh(
    name: str,
    center: list[float],
    size: list[float],
    material: bpy.types.Material,
    custom_props: dict[str, Any],
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    sx, sy, sz = [float(v) for v in size]
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    verts = [
        (-hx, -hy, -hz),
        (hx, -hy, -hz),
        (hx, hy, -hz),
        (-hx, hy, -hz),
        (-hx, -hy, hz),
        (hx, -hy, hz),
        (hx, hy, hz),
        (-hx, hy, hz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = tuple(float(v) for v in center)
    if parent is not None:
        obj.parent = parent
    obj.data.materials.append(material)
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def make_mesh_from_sections(
    name: str,
    sections: list[dict[str, Any]],
    material: bpy.types.Material,
    location: tuple[float, float, float],
    rotation_degrees: list[float],
    scale: list[float],
    parent: bpy.types.Object | None,
    custom_props: dict[str, Any],
) -> bpy.types.Object:
    if len(sections) < 2:
        raise ValueError(f"{name} requires at least two sections")
    counts = {len(section["points"]) for section in sections}
    if len(counts) != 1:
        raise ValueError(f"{name} section vertex counts must match")
    count = counts.pop()
    if count < 3:
        raise ValueError(f"{name} sections require at least 3 points")

    vertices: list[tuple[float, float, float]] = []
    for section in sections:
        z = float(section["at"])
        for point in section["points"]:
            vertices.append((float(point[0]), float(point[1]), z))

    faces: list[tuple[int, ...]] = []
    faces.append(tuple(reversed(range(count))))
    top_start = (len(sections) - 1) * count
    faces.append(tuple(top_start + i for i in range(count)))
    for section_index in range(len(sections) - 1):
        start_a = section_index * count
        start_b = (section_index + 1) * count
        for i in range(count):
            j = (i + 1) % count
            faces.append((start_a + i, start_a + j, start_b + j, start_b + i))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    if parent is not None:
        obj.parent = parent
    obj.location = location
    obj.rotation_euler = euler_from_degrees(rotation_degrees)
    obj.scale = tuple(float(v) for v in scale)
    obj.data.materials.append(material)
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def create_asset(
    *,
    asset_ref: str,
    solids: dict[str, dict[str, Any]],
    materials: dict[str, bpy.types.Material],
    location: tuple[float, float, float],
    rotation_degrees: list[float],
    scale: list[float],
    parent: bpy.types.Object | None,
    name: str,
    semantic_tags: list[str],
    source_instance: dict[str, Any] | None = None,
) -> list[bpy.types.Object]:
    solid = solids[asset_ref]
    operation = solid["operation"]
    role = source_instance.get("role", "") if source_instance else ""
    custom_props = {
        "asset_ref": asset_ref,
        "operation": operation,
        "architectural_role": solid["architectural_role"],
        "semantic_tags": ",".join(semantic_tags),
        "no_structural_claims": True,
        "no_production_approval": True,
    }
    if source_instance is not None:
        custom_props["instance_id"] = source_instance["instance_id"]
        custom_props["role"] = source_instance["role"]
        custom_props["topology_source"] = source_instance.get("topology_source", "")

    if operation in {"extrude", "loft_sections"}:
        material = material_for_tags(materials, semantic_tags, role)
        return [
            make_mesh_from_sections(
                name,
                solid["geometry_outputs"]["sections"],
                material,
                location,
                rotation_degrees,
                scale,
                parent,
                custom_props,
            )
        ]

    if operation == "compound_asset":
        empty = create_empty(name, location, rotation_degrees, scale, parent, custom_props)
        created = [empty]
        for component in solid["geometry_outputs"]["component_refs"]:
            t = component["translation"]
            created.extend(
                create_asset(
                    asset_ref=component["asset_ref"],
                    solids=solids,
                    materials=materials,
                    location=(float(t[0]), float(t[1]), float(t[2])),
                    rotation_degrees=[0.0, 0.0, 0.0],
                    scale=[1.0, 1.0, 1.0],
                    parent=empty,
                    name=f"{name}.{component['instance_id']}.{component['asset_ref']}",
                    semantic_tags=semantic_tags,
                )
            )
        return created

    raise ValueError(f"{asset_ref} unsupported operation {operation}")


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not objs:
        return mathutils.Vector((0, 0, 0)), mathutils.Vector((1, 1, 1))
    mins = mathutils.Vector(
        (
            min((o.matrix_world @ mathutils.Vector(corner)).x for o in objs for corner in o.bound_box),
            min((o.matrix_world @ mathutils.Vector(corner)).y for o in objs for corner in o.bound_box),
            min((o.matrix_world @ mathutils.Vector(corner)).z for o in objs for corner in o.bound_box),
        )
    )
    maxs = mathutils.Vector(
        (
            max((o.matrix_world @ mathutils.Vector(corner)).x for o in objs for corner in o.bound_box),
            max((o.matrix_world @ mathutils.Vector(corner)).y for o in objs for corner in o.bound_box),
            max((o.matrix_world @ mathutils.Vector(corner)).z for o in objs for corner in o.bound_box),
        )
    )
    return mins, maxs


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -8.0, 10.0))
    light = bpy.context.object
    light.name = "topology_site_area_light"
    light.data.energy = 650.0
    light.data.size = 9.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((9.5, -15.0, 8.5)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.25
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
        "default": make_material("mat_default", (0.62, 0.60, 0.54, 1.0)),
        "upper_terrain": make_material("mat_upper_terrain", (0.29, 0.48, 0.31, 1.0)),
        "lower_terrain": make_material("mat_lower_terrain", (0.31, 0.36, 0.30, 1.0)),
        "road": make_material("mat_road", (0.36, 0.32, 0.25, 1.0)),
        "hazard": make_material("mat_fall_edge", (0.88, 0.22, 0.16, 1.0)),
        "foundation": make_material("mat_foundation", (0.42, 0.41, 0.38, 1.0)),
        "retaining_wall": make_material("mat_retaining_wall", (0.33, 0.31, 0.28, 1.0)),
        "walkable": make_material("mat_walkable", (0.22, 0.64, 0.34, 1.0)),
        "blocked": make_material("mat_blocked", (0.62, 0.54, 0.42, 1.0)),
        "cover": make_material("mat_cover", (0.90, 0.58, 0.26, 1.0)),
        "support": make_material("mat_support", (0.92, 0.77, 0.30, 1.0)),
        "barrier": make_material("mat_barrier", (0.26, 0.56, 0.88, 1.0)),
    }
    solids = {path.stem: load_json(path) for path in sorted(SOLID_DIR.glob("*.json"))}
    site_paths = sorted(SITE_DIR.glob("*_assembly.json"))
    if not site_paths:
        raise FileNotFoundError(f"no compiled topology site assemblies found in {SITE_DIR}")
    site = load_json(site_paths[0])

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
            "affordance_fact_count": site["affordance_fact_count"],
        },
    )
    created.append(root)

    for terrain in site["terrain_primitives"]:
        mat = material_for_tags(materials, terrain["semantic_tags"])
        created.append(
            create_box_mesh(
                f"{site['site_id']}.{terrain['terrain_id']}",
                terrain["center"],
                terrain["size"],
                mat,
                {
                    "terrain_id": terrain["terrain_id"],
                    "topology_type": terrain["topology_type"],
                    "semantic_tags": ",".join(terrain["semantic_tags"]),
                },
                root,
            )
        )

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

    for fact in site["affordance_facts"]:
        if fact["affordance"] == "fall_edge":
            created.append(
                create_box_mesh(
                    f"{site['site_id']}.{fact['fact_id']}_marker",
                    [0.0, -4.72, 1.72],
                    [8.4, 0.08, 0.22],
                    materials["hazard"],
                    {"affordance": fact["affordance"], "fact_id": fact["fact_id"]},
                    root,
                )
            )

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    report = {
        "schema": "topology_site_blender_proof_v0",
        "site_id": site["site_id"],
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "empty_object_count": empty_count,
        "terrain_primitive_count": site["terrain_primitive_count"],
        "foundation_instance_count": site["foundation_instance_count"],
        "building_instance_count": site["building_instance_count"],
        "affordance_fact_count": site["affordance_fact_count"],
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "rules": {
            "proof_scene_only": True,
            "topology_drives_building_site": True,
            "foundation_adapter_present": True,
            "affordance_facts_visualized": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"objects_created={len(created)} mesh={mesh_count} empty={empty_count}")


if __name__ == "__main__":
    main()
