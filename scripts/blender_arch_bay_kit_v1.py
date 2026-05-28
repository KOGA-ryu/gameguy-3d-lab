#!/usr/bin/env python3
"""Build Arch Bay Kit v1 in Blender.

This is a fresh visual asset kit focused on arch/opening language. It creates
reviewable blockout geometry only: no production art, structural claims, or
fabrication claims.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "arch_bay_kit_v1.json"
OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "arch_bay_kit_v1.blend"
RENDER_PATH = OUT_DIR / "arch_bay_kit_v1_workbench.png"
REPORT_PATH = OUT_DIR / "arch_bay_kit_v1_report.json"


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


def add_group(name: str, offset: tuple[float, float, float], metadata: dict[str, Any]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.45
    obj.location = offset
    for key, value in metadata.items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def add_cube(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    material: bpy.types.Material,
    parent: bpy.types.Object,
    props: dict[str, Any] | None = None,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    for key, value in (props or {}).items():
        obj[key] = value
    return obj


def add_cylinder(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    vertices: int,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    props: dict[str, Any] | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    obj.parent = parent
    for key, value in (props or {}).items():
        obj[key] = value
    return obj


def add_curve(
    name: str,
    points: list[tuple[float, float, float]],
    bevel_depth: float,
    material: bpy.types.Material,
    parent: bpy.types.Object,
    props: dict[str, Any] | None = None,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points, strict=True):
        point.co = (coord[0], coord[1], coord[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(material)
    obj.parent = parent
    for key, value in (props or {}).items():
        obj[key] = value
    bpy.context.collection.objects.link(obj)
    return obj


def pointed_arch_points(span: float, spring_z: float, rise: float, y: float = -0.12, segments: int = 16) -> list[tuple[float, float, float]]:
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


def round_arch_points(span: float, spring_z: float, y: float = -0.12, segments: int = 28) -> list[tuple[float, float, float]]:
    radius = span * 0.5
    return [
        (
            math.cos(math.pi - math.pi * index / segments) * radius,
            y,
            spring_z + math.sin(math.pi - math.pi * index / segments) * radius,
        )
        for index in range(segments + 1)
    ]


def add_voussoirs(
    parent: bpy.types.Object,
    mats: dict[str, bpy.types.Material],
    points: list[tuple[float, float, float]],
    *,
    every: int = 4,
    block_size: tuple[float, float, float] = (0.22, 0.18, 0.12),
    broken_skip: set[int] | None = None,
) -> None:
    broken_skip = broken_skip or set()
    count = 0
    for index in range(1, len(points) - 1, every):
        if count in broken_skip:
            count += 1
            continue
        x, y, z = points[index]
        px, _py, pz = points[index - 1]
        nx, _ny, nz = points[index + 1]
        tangent = math.atan2(nz - pz, nx - px)
        add_cube(
            "voussoir_block",
            (x, y - 0.05, z),
            block_size,
            mats["cap"],
            parent,
            {"mesh_role": "arch_voussoir"},
            rotation=(0.0, -tangent, 0.0),
        )
        count += 1


def add_side_piers(parent: bpy.types.Object, mats: dict[str, bpy.types.Material], span: float, height: float, thickness: float = 0.34) -> None:
    half = span * 0.5
    for side, x in (("left", -half - thickness * 0.5), ("right", half + thickness * 0.5)):
        add_cube(f"{side}_jamb", (x, 0.0, height * 0.5), (thickness, 0.34, height), mats["stone"], parent, {"mesh_role": "jamb"})
        add_cube(f"{side}_base", (x, 0.0, 0.1), (thickness * 1.35, 0.46, 0.2), mats["dark"], parent, {"mesh_role": "base_block"})
        add_cube(f"{side}_cap", (x, 0.0, height + 0.07), (thickness * 1.25, 0.42, 0.14), mats["dark"], parent, {"mesh_role": "capital_block"})


def build_pointed_arch_doorway(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_side_piers(parent, mats, 1.5, 1.55)
    points = pointed_arch_points(1.5, 1.48, 0.9)
    add_curve("pointed_arch_outer_rib", points, 0.045, mats["rib"], parent, {"bend_law": "pointed_arch"})
    add_voussoirs(parent, mats, points, every=4)
    add_cube("threshold_slab", (0, 0.0, 0.06), (1.95, 0.54, 0.12), mats["floor"], parent, {"mesh_role": "threshold"})


def build_round_arch_doorway(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_side_piers(parent, mats, 1.55, 1.28)
    points = round_arch_points(1.55, 1.26)
    add_curve("round_arch_outer_rib", points, 0.052, mats["rib"], parent, {"bend_law": "semicircular_arch"})
    add_voussoirs(parent, mats, points, every=4, block_size=(0.2, 0.18, 0.11))
    add_cube("round_arch_spandrel_left", (-0.92, 0, 1.78), (0.42, 0.3, 0.55), mats["stone"], parent)
    add_cube("round_arch_spandrel_right", (0.92, 0, 1.78), (0.42, 0.3, 0.55), mats["stone"], parent)


def build_narrow_lancet_window(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("window_back_wall", (0, 0.05, 1.05), (1.25, 0.18, 2.1), mats["stone"], parent)
    points = pointed_arch_points(0.58, 1.1, 0.95, y=-0.11, segments=18)
    add_curve("lancet_outer_rib", points, 0.032, mats["rib"], parent)
    add_curve("lancet_inner_shadow", [(x * 0.72, y - 0.02, z * 0.92 + 0.06) for x, y, z in points], 0.026, mats["shadow"], parent)
    for x in (-0.36, 0.36):
        add_cube("lancet_side_reveal", (x, -0.1, 0.78), (0.08, 0.08, 1.2), mats["rib"], parent)
    add_cube("lancet_sill", (0, -0.12, 0.28), (0.8, 0.12, 0.1), mats["cap"], parent)


def build_double_arcade_bay(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    for x in (-0.95, 0.0, 0.95):
        add_cylinder("arcade_column", (x, 0, 0.78), 0.12, 1.55, 10, mats["stone_gold"], parent)
        add_cube("arcade_column_base", (x, 0, 0.08), (0.34, 0.34, 0.16), mats["dark"], parent)
        add_cube("arcade_column_cap", (x, 0, 1.57), (0.36, 0.36, 0.14), mats["dark"], parent)
    for x in (-0.475, 0.475):
        points = pointed_arch_points(0.82, 1.48, 0.56, segments=12)
        add_curve("arcade_pointed_rib", [(px + x, py, pz) for px, py, pz in points], 0.035, mats["rib"], parent)
    add_cube("arcade_top_band", (0, 0, 2.08), (2.35, 0.28, 0.18), mats["cap"], parent)


def build_columned_arch_portal(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_side_piers(parent, mats, 1.8, 1.55, thickness=0.22)
    for x in (-1.08, 1.08):
        add_cylinder("portal_forward_column", (x, -0.34, 0.86), 0.12, 1.72, 12, mats["stone_gold"], parent)
        add_cube("portal_column_base", (x, -0.34, 0.08), (0.34, 0.34, 0.16), mats["dark"], parent)
        add_cube("portal_column_cap", (x, -0.34, 1.73), (0.34, 0.34, 0.14), mats["dark"], parent)
    outer = pointed_arch_points(1.8, 1.56, 1.0, y=-0.3)
    inner = pointed_arch_points(1.3, 1.42, 0.82, y=-0.36)
    add_curve("portal_outer_arch", outer, 0.052, mats["rib"], parent)
    add_curve("portal_inner_arch", inner, 0.032, mats["cap"], parent)
    add_voussoirs(parent, mats, outer, every=4)


def build_broken_arch_bay(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_side_piers(parent, mats, 1.55, 1.25)
    points = pointed_arch_points(1.55, 1.23, 0.82)
    add_curve("broken_arch_remaining_rib", points[:18], 0.045, mats["rib"], parent, {"damage_state": "partial_arch"})
    add_voussoirs(parent, mats, points, every=4, broken_skip={4, 5, 6})
    add_cube("fallen_arch_block_0", (0.52, -0.1, 0.2), (0.32, 0.24, 0.18), mats["cap"], parent, rotation=(0.0, 0.0, math.radians(18)))
    add_cube("fallen_arch_block_1", (0.86, -0.06, 0.14), (0.28, 0.24, 0.16), mats["cap"], parent, rotation=(0.0, 0.0, math.radians(-12)))


def build_recessed_arch_panel(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("recess_panel_back", (0, 0.04, 1.0), (2.0, 0.22, 2.0), mats["stone"], parent)
    add_cube("recess_shadow_panel", (0, -0.1, 0.92), (1.35, 0.08, 1.2), mats["shadow"], parent)
    points = round_arch_points(1.2, 1.02, y=-0.16)
    add_curve("recess_round_arch_trim", points, 0.04, mats["rib"], parent)
    add_cube("recess_bottom_trim", (0, -0.16, 0.28), (1.45, 0.12, 0.12), mats["cap"], parent)
    for x in (-0.78, 0.78):
        add_cube("recess_side_trim", (x, -0.16, 0.82), (0.1, 0.12, 1.08), mats["cap"], parent)


def build_oculus_arch_bay(parent: bpy.types.Object, mats: dict[str, bpy.types.Material]) -> None:
    add_cube("oculus_wall_panel", (0, 0.04, 1.05), (1.8, 0.18, 2.1), mats["stone"], parent)
    add_cylinder("oculus_outer_ring", (0, -0.11, 1.45), 0.38, 0.08, 28, mats["rib"], parent)
    add_cylinder("oculus_inner_shadow", (0, -0.16, 1.45), 0.24, 0.06, 28, mats["shadow"], parent)
    points = pointed_arch_points(1.25, 0.62, 0.9, y=-0.14)
    add_curve("oculus_lower_arch_reveal", points, 0.032, mats["cap"], parent)
    add_cube("oculus_sill", (0, -0.14, 0.32), (1.05, 0.12, 0.12), mats["cap"], parent)


BUILDERS: dict[str, Callable[[bpy.types.Object, dict[str, bpy.types.Material]], None]] = {
    "pointed_arch_doorway": build_pointed_arch_doorway,
    "round_arch_doorway": build_round_arch_doorway,
    "narrow_lancet_window": build_narrow_lancet_window,
    "double_arcade_bay": build_double_arcade_bay,
    "columned_arch_portal": build_columned_arch_portal,
    "broken_arch_bay": build_broken_arch_bay,
    "recessed_arch_panel": build_recessed_arch_panel,
    "oculus_arch_bay": build_oculus_arch_bay,
}


def scene_bounds() -> tuple[mathutils.Vector, mathutils.Vector]:
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    if not objs:
        return mathutils.Vector((0, 0, 0)), mathutils.Vector((1, 1, 1))
    corners: list[mathutils.Vector] = []
    for obj in objs:
        for corner in obj.bound_box:
            corners.append(obj.matrix_world @ mathutils.Vector(corner))
    mins = mathutils.Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    maxs = mathutils.Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return mins, maxs


def add_scene_context() -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -8.0, 8.0))
    light = bpy.context.object
    light.name = "arch_bay_kit_area_light"
    light.data.energy = 700.0
    light.data.size = 7.0
    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((7.5, -11.0, 7.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.38
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
    recipe = load_json(RECIPE_PATH)
    mats = {
        "stone": make_material("mat_warm_wall_stone", (0.55, 0.51, 0.42, 1.0)),
        "dark": make_material("mat_dark_foundation", (0.32, 0.31, 0.28, 1.0)),
        "stone_gold": make_material("mat_limestone_column", (0.72, 0.64, 0.42, 1.0)),
        "rib": make_material("mat_arch_rib", (0.82, 0.74, 0.52, 1.0)),
        "cap": make_material("mat_capstone", (0.66, 0.62, 0.52, 1.0)),
        "floor": make_material("mat_threshold_floor", (0.30, 0.58, 0.38, 1.0)),
        "shadow": make_material("mat_recess_shadow", (0.20, 0.20, 0.18, 1.0)),
    }

    created_assets: list[dict[str, Any]] = []
    cols = 4
    spacing_x = 3.15
    spacing_y = 3.1
    for index, asset in enumerate(recipe["assets"]):
        col = index % cols
        row = index // cols
        offset = ((col - 1.5) * spacing_x, (0.5 - row) * spacing_y, 0.0)
        parent = add_group(
            asset["asset_id"],
            offset,
            {
                "asset_id": asset["asset_id"],
                "architectural_role": asset["architectural_role"],
                "builder_kind": asset["builder_kind"],
                "semantic_tags": ",".join(asset["semantic_tags"]),
                "no_structural_claims": True,
                "no_production_approval": True,
            },
        )
        BUILDERS[asset["builder_kind"]](parent, mats)
        created_assets.append({
            "asset_id": asset["asset_id"],
            "builder_kind": asset["builder_kind"],
            "architectural_role": asset["architectural_role"],
            "semantic_tags": asset["semantic_tags"],
        })

    add_scene_context()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)
    mesh_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "MESH")
    curve_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "CURVE")
    empty_count = sum(1 for obj in bpy.context.scene.objects if obj.type == "EMPTY")
    report = {
        "schema": "arch_bay_kit_blender_report_v1",
        "source_recipe": str(RECIPE_PATH.relative_to(ROOT)),
        "blend_path": str(BLEND_PATH.relative_to(ROOT)),
        "render_path": str(RENDER_PATH.relative_to(ROOT)),
        "asset_count": len(created_assets),
        "mesh_object_count": mesh_count,
        "curve_object_count": curve_count,
        "empty_object_count": empty_count,
        "assets": created_assets,
        "rules": {
            "fresh_visual_batch": True,
            "proof_scene_only": True,
            "no_structural_claims": True,
            "no_production_approval": True,
            "no_fabrication_claims": True
        }
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BLEND_PATH.relative_to(ROOT)}")
    print(f"wrote {RENDER_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"assets={len(created_assets)} mesh={mesh_count} curves={curve_count} empties={empty_count}")


if __name__ == "__main__":
    main()
