#!/usr/bin/env python3
"""Create a Blender smoke-test scene from compiled Asset Mill solids.

Run with Blender, not normal Python:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_asset_mill_smoke_test_v0.py

This consumes measured JSON from goal/architecture/asset_mill_v0/solids and
creates simple mesh objects. It is a bridge test only, not production art,
fabrication output, or structural validation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_v0" / "asset_mill_compiled_index_v0.json"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "asset_mill_smoke_test_v0.blend"
RENDER_PATH = OUT_DIR / "asset_mill_smoke_test_v0_workbench.png"
REPORT_PATH = OUT_DIR / "asset_mill_smoke_test_v0_report.json"


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


def material_for_semantics(materials: dict[str, bpy.types.Material], tags: list[str]) -> bpy.types.Material:
    tag_set = set(tags)
    if "walkable" in tag_set:
        return materials["walkable"]
    if "barrier" in tag_set or "rail" in tag_set:
        return materials["barrier"]
    if "support" in tag_set:
        return materials["support"]
    if "blocked" in tag_set or "line_of_sight_blocker" in tag_set:
        return materials["blocked"]
    if "cover" in tag_set:
        return materials["cover"]
    return materials["default"]


def make_mesh_from_sections(
    name: str,
    sections: list[dict[str, Any]],
    material: bpy.types.Material,
    location: tuple[float, float, float],
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
    obj.location = location
    obj.data.materials.append(material)
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def create_empty(name: str, location: tuple[float, float, float], custom_props: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.25
    obj.location = location
    for key, value in custom_props.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def create_asset(
    asset_id: str,
    solids: dict[str, dict[str, Any]],
    materials: dict[str, bpy.types.Material],
    location: tuple[float, float, float],
    parent: bpy.types.Object | None = None,
    name_prefix: str = "",
) -> list[bpy.types.Object]:
    solid = solids[asset_id]
    tags = solid["semantic_outputs"]["semantic_tags"]
    material = material_for_semantics(materials, tags)
    operation = solid["operation"]
    display_name = f"{name_prefix}{asset_id}"
    custom_props = {
        "asset_id": solid["asset_id"],
        "operation": operation,
        "architectural_role": solid["architectural_role"],
        "semantic_tags": ",".join(tags),
        "source_recipe": solid["source_recipe"],
        "no_structural_claims": True,
        "no_production_approval": True,
    }

    if operation in {"extrude", "loft_sections"}:
        obj = make_mesh_from_sections(
            display_name,
            solid["geometry_outputs"]["sections"],
            material,
            location,
            parent,
            custom_props,
        )
        return [obj]

    if operation == "compound_asset":
        empty = create_empty(display_name, location, custom_props)
        if parent is not None:
            empty.parent = parent
        objects = [empty]
        for component in solid["geometry_outputs"]["component_refs"]:
            t = component["translation"]
            child_objects = create_asset(
                component["asset_ref"],
                solids,
                materials,
                (float(t[0]), float(t[1]), float(t[2])),
                parent=empty,
                name_prefix=f"{asset_id}.{component['instance_id']}.",
            )
            objects.extend(child_objects)
        return objects

    raise ValueError(f"{asset_id} unsupported operation {operation}")


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(3.0, -5.0, 6.0))
    light = bpy.context.object
    light.name = "asset_mill_area_light"
    light.data.energy = 450.0
    light.data.size = 5.0

    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((8.0, -11.0, 7.2)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.65
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1100
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objs:
        return mathutils.Vector((0.0, 0.0, 0.0)), mathutils.Vector((1.0, 1.0, 1.0))
    mins = mathutils.Vector(
        (
            min((obj.matrix_world @ mathutils.Vector(corner)).x for obj in objs for corner in obj.bound_box),
            min((obj.matrix_world @ mathutils.Vector(corner)).y for obj in objs for corner in obj.bound_box),
            min((obj.matrix_world @ mathutils.Vector(corner)).z for obj in objs for corner in obj.bound_box),
        )
    )
    maxs = mathutils.Vector(
        (
            max((obj.matrix_world @ mathutils.Vector(corner)).x for obj in objs for corner in obj.bound_box),
            max((obj.matrix_world @ mathutils.Vector(corner)).y for obj in objs for corner in obj.bound_box),
            max((obj.matrix_world @ mathutils.Vector(corner)).z for obj in objs for corner in obj.bound_box),
        )
    )
    return mins, maxs


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()

    materials = {
        "default": make_material("geometry_default", (0.55, 0.50, 0.42, 1.0)),
        "walkable": make_material("semantic_walkable", (0.26, 0.52, 0.32, 1.0)),
        "blocked": make_material("semantic_blocked", (0.50, 0.45, 0.36, 1.0)),
        "cover": make_material("semantic_cover", (0.58, 0.47, 0.28, 1.0)),
        "support": make_material("semantic_support", (0.80, 0.66, 0.38, 1.0)),
        "barrier": make_material("semantic_barrier", (0.30, 0.46, 0.62, 1.0)),
    }

    index = load_json(INDEX_PATH)
    solids = {path.stem: load_json(path) for path in sorted(SOLID_DIR.glob("*.json"))}

    created: list[bpy.types.Object] = []
    spacing_x = 3.0
    spacing_y = 3.0
    cols = 4
    for index_i, asset in enumerate(index["assets"]):
        asset_id = asset["asset_id"]
        col = index_i % cols
        row = index_i // cols
        location = (col * spacing_x, row * spacing_y, 0.0)
        created.extend(create_asset(asset_id, solids, materials, location))

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    mesh_count = sum(1 for obj in created if obj.type == "MESH")
    empty_count = sum(1 for obj in created if obj.type == "EMPTY")
    report = {
        "schema": "asset_mill_blender_smoke_test_v0",
        "source_index": str(INDEX_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "asset_count": len(index["assets"]),
        "objects_created": len(created),
        "mesh_object_count": mesh_count,
        "empty_object_count": empty_count,
        "rules": {
            "bridge_test_only": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True
        }
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"objects_created={len(created)} mesh={mesh_count} empty={empty_count}")


if __name__ == "__main__":
    main()
