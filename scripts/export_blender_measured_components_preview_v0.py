#!/usr/bin/env python3
"""Blender adapter for promoted measured component source recipes.

This consumes data/architecture/asset_mill/recipes/measured_components_v0.json.
It does not import or run the old measured component compiler scripts.

Validate with normal Python:

python3 scripts/export_blender_measured_components_preview_v0.py --validate-only

Export with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/export_blender_measured_components_preview_v0.py -- \
  --out /tmp/gameguy_measured_components_preview_v0
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_measured_components_preview_v0")


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"{path} must contain a JSON object")
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_vector(value: Any, field: str, length: int = 3) -> None:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")


def validate_primitive(asset_id: str, part: Any, field: str) -> str:
    if not isinstance(part, dict):
        fail(f"{field} must be an object")
    primitive = part.get("primitive")
    if primitive not in {"cube", "cylinder", "curve"}:
        fail(f"{field}.primitive unsupported for {asset_id}: {primitive}")
    if not isinstance(part.get("name"), str) or not part["name"]:
        fail(f"{field}.name must be a non-empty string")
    if primitive == "cube":
        validate_vector(part.get("location_m"), f"{field}.location_m")
        validate_vector(part.get("dimensions_m"), f"{field}.dimensions_m")
        if any(float(value) <= 0.0 for value in part["dimensions_m"]):
            fail(f"{field}.dimensions_m values must be positive")
    elif primitive == "cylinder":
        validate_vector(part.get("location_m"), f"{field}.location_m")
        if not finite_number(part.get("radius_m")) or float(part["radius_m"]) <= 0.0:
            fail(f"{field}.radius_m must be positive")
        if not finite_number(part.get("depth_m")) or float(part["depth_m"]) <= 0.0:
            fail(f"{field}.depth_m must be positive")
        if not isinstance(part.get("vertices"), int) or part["vertices"] < 3:
            fail(f"{field}.vertices must be >= 3")
    elif primitive == "curve":
        for key in ("span_m", "spring_z_m", "rise_m", "y_m", "bevel_depth_m"):
            if not finite_number(part.get(key)):
                fail(f"{field}.{key} must be a finite number")
        if float(part["span_m"]) <= 0.0 or float(part["bevel_depth_m"]) <= 0.0:
            fail(f"{field} curve span and bevel must be positive")
    return primitive


def load_measured_components(bundle_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    bundle = load_json(bundle_path)
    if bundle.get("schema") != "asset_mill_measured_component_bundle_v0":
        fail("bundle schema must be asset_mill_measured_component_bundle_v0")
    assets = bundle.get("assets")
    if not isinstance(assets, list) or not assets:
        fail("bundle assets must be a non-empty list")
    primitive_counts = {"cube": 0, "cylinder": 0, "curve": 0}
    seen: set[str] = set()
    for asset_index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            fail(f"assets[{asset_index}] must be an object")
        asset_id = asset.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            fail(f"assets[{asset_index}].asset_id must be a non-empty string")
        if asset_id in seen:
            fail(f"duplicate measured component asset_id: {asset_id}")
        seen.add(asset_id)
        if asset.get("source_script", "").startswith("scripts/compile_asset_mill_measured_components_") is not True:
            fail(f"{asset_id}.source_script must preserve compiler provenance")
        if not isinstance(asset.get("proof_primitives"), list) or not asset["proof_primitives"]:
            fail(f"{asset_id}.proof_primitives must be a non-empty list")
        if not isinstance(asset.get("sockets"), list):
            fail(f"{asset_id}.sockets must be a list")
        for primitive_index, part in enumerate(asset["proof_primitives"]):
            primitive = validate_primitive(asset_id, part, f"{asset_id}.proof_primitives[{primitive_index}]")
            primitive_counts[primitive] += 1
    if bundle.get("asset_count") != len(assets):
        fail("bundle asset_count must match assets length")
    return bundle, assets, primitive_counts


def make_report(bundle_path: Path, bundle: dict[str, Any], assets: list[dict[str, Any]], primitive_counts: dict[str, int], *, generated: bool) -> dict[str, Any]:
    return {
        "schema": "blender_measured_components_preview_adapter_report_v0",
        "adapter": "scripts/export_blender_measured_components_preview_v0.py",
        "source_bundle": str(bundle_path),
        "source_bundle_schema": bundle["schema"],
        "asset_count": len(assets),
        "v1_asset_count": bundle["v1_asset_count"],
        "v2_asset_count": bundle["v2_asset_count"],
        "proof_primitive_count": sum(primitive_counts.values()),
        "proof_primitive_counts": primitive_counts,
        "socket_count": sum(len(asset["sockets"]) for asset in assets),
        "generated_outputs_created": generated,
        "rules": {
            "consumes_promoted_source_catalog": True,
            "imports_old_compiler_scripts": False,
            "runs_old_compiler_scripts": False,
            "proof_primitives_are_preview_hints_only": True,
            "source_design_logic": False,
        },
    }


def material_key(asset: dict[str, Any]) -> str:
    roles = set(asset.get("semantic_roles", []))
    if "walkable" in roles:
        return "walkable"
    if "barrier" in roles or "rail" in roles:
        return "barrier"
    if "support" in roles:
        return "support"
    if "blocked" in roles or "line_of_sight_blocker" in roles:
        return "blocked"
    if "cover" in roles:
        return "cover"
    if "decorative_only" in roles or "panel_socket" in roles:
        return "decorative"
    return "default"


def run_blender_export(assets: list[dict[str, Any]], out_root: Path, report: dict[str, Any], render: bool) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Blender export requires Blender Python. Use --validate-only with normal Python.")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    materials = make_materials(bpy)

    columns = max(1, math.ceil(math.sqrt(len(assets))))
    spacing = 4.0
    object_count = 0
    for index, asset in enumerate(assets):
        row = index // columns
        col = index % columns
        offset = mathutils.Vector((col * spacing, row * spacing, 0.0))
        parent = create_asset_empty(bpy, asset, offset)
        object_count += 1
        material = materials[material_key(asset)]
        for part in asset["proof_primitives"]:
            create_primitive(bpy, part, offset, parent, material)
            object_count += 1
        for socket in asset["sockets"]:
            create_socket_marker(bpy, socket, offset, parent, materials["socket"])
            object_count += 1

    add_scene_context(bpy, mathutils)
    blend_path = out_root / "measured_components_preview_v0.blend"
    report_path = out_root / "measured_components_preview_v0_report.json"
    report["generated_outputs_created"] = True
    report["blend_path"] = str(blend_path)
    report["object_count"] = object_count
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if render:
        render_path = out_root / "measured_components_preview_v0_workbench.png"
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS measured component Blender export: assets={len(assets)} out={out_root}")


def make_materials(bpy: Any) -> dict[str, Any]:
    colors = {
        "default": (0.58, 0.58, 0.54, 1.0),
        "walkable": (0.32, 0.56, 0.38, 1.0),
        "barrier": (0.30, 0.42, 0.62, 1.0),
        "support": (0.72, 0.62, 0.38, 1.0),
        "blocked": (0.52, 0.42, 0.36, 1.0),
        "cover": (0.50, 0.50, 0.62, 1.0),
        "decorative": (0.62, 0.50, 0.66, 1.0),
        "socket": (0.10, 0.38, 0.86, 1.0),
    }
    mats = {}
    for key, color in colors.items():
        mat = bpy.data.materials.new(f"measured_preview_{key}")
        mat.diffuse_color = color
        mats[key] = mat
    return mats


def create_asset_empty(bpy: Any, asset: dict[str, Any], offset: Any) -> Any:
    obj = bpy.data.objects.new(asset["asset_id"], None)
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.24
    obj.location = offset
    obj["asset_id"] = asset["asset_id"]
    obj["source_version"] = asset["source_version"]
    obj["adapter_only"] = True
    obj["no_production_approval"] = True
    obj["no_structural_safety"] = True
    bpy.context.collection.objects.link(obj)
    return obj


def create_primitive(bpy: Any, part: dict[str, Any], offset: Any, parent: Any, material: Any) -> Any:
    primitive = part["primitive"]
    if primitive == "cube":
        loc = tuple(float(part["location_m"][index]) + float(offset[index]) for index in range(3))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        obj = bpy.context.object
        obj.dimensions = tuple(float(value) for value in part["dimensions_m"])
        obj.data.materials.append(material)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    elif primitive == "cylinder":
        loc = tuple(float(part["location_m"][index]) + float(offset[index]) for index in range(3))
        bpy.ops.mesh.primitive_cylinder_add(vertices=int(part["vertices"]), radius=float(part["radius_m"]), depth=float(part["depth_m"]), location=loc)
        obj = bpy.context.object
        obj.data.materials.append(material)
    elif primitive == "curve":
        curve = bpy.data.curves.new(f"{parent.name}.{part['name']}_curve", type="CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = float(part["bevel_depth_m"])
        curve.bevel_resolution = 4
        points = curve_points(part, offset)
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for point, coord in zip(spline.points, points, strict=True):
            point.co = (coord[0], coord[1], coord[2], 1.0)
        obj = bpy.data.objects.new(f"{parent.name}.{part['name']}", curve)
        obj.data.materials.append(material)
        bpy.context.collection.objects.link(obj)
    else:
        raise ValueError(f"unsupported primitive: {primitive}")
    obj.name = f"{parent.name}.{part['name']}"
    obj.parent = parent
    obj["asset_id"] = parent.name
    obj["proof_primitive"] = primitive
    obj["adapter_only"] = True
    return obj


def curve_points(part: dict[str, Any], offset: Any) -> list[tuple[float, float, float]]:
    span = float(part["span_m"])
    spring_z = float(part["spring_z_m"])
    rise = float(part["rise_m"])
    y = float(part["y_m"])
    points: list[tuple[float, float, float]] = []
    if part.get("curve_kind") == "round":
        radius = span * 0.5
        for index in range(29):
            angle = math.pi - math.pi * index / 28
            points.append((math.cos(angle) * radius + float(offset[0]), y + float(offset[1]), spring_z + math.sin(angle) * radius + float(offset[2])))
    else:
        half = span * 0.5
        for index in range(19):
            t = index / 18
            points.append((-half + half * t + float(offset[0]), y + float(offset[1]), spring_z + rise * (1.0 - (1.0 - t) ** 2) + float(offset[2])))
        for index in range(1, 19):
            t = index / 18
            points.append((half * t + float(offset[0]), y + float(offset[1]), spring_z + rise * (1.0 - t**2) + float(offset[2])))
    return points


def create_socket_marker(bpy: Any, socket: dict[str, Any], offset: Any, parent: Any, material: Any) -> Any:
    position = socket["position_m"]
    loc = tuple(float(position[index]) + float(offset[index]) for index in range(3))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.045, location=loc)
    obj = bpy.context.object
    obj.name = f"{parent.name}.{socket['socket_id']}"
    obj.data.materials.append(material)
    obj.parent = parent
    obj["asset_id"] = parent.name
    obj["socket_id"] = socket["socket_id"]
    obj["connector_term"] = socket["connector_term"]
    obj["adapter_only"] = True
    return obj


def add_scene_context(bpy: Any, mathutils: Any) -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(5.0, -7.0, 8.0))
    light = bpy.context.object
    light.name = "measured_components_area_light"
    light.data.energy = 520.0
    light.data.size = 6.0
    objs = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    if objs:
        mins = mathutils.Vector((min((obj.matrix_world @ mathutils.Vector(corner)).x for obj in objs for corner in obj.bound_box), min((obj.matrix_world @ mathutils.Vector(corner)).y for obj in objs for corner in obj.bound_box), min((obj.matrix_world @ mathutils.Vector(corner)).z for obj in objs for corner in obj.bound_box)))
        maxs = mathutils.Vector((max((obj.matrix_world @ mathutils.Vector(corner)).x for obj in objs for corner in obj.bound_box), max((obj.matrix_world @ mathutils.Vector(corner)).y for obj in objs for corner in obj.bound_box), max((obj.matrix_world @ mathutils.Vector(corner)).z for obj in objs for corner in obj.bound_box)))
    else:
        mins = mathutils.Vector((0.0, 0.0, 0.0))
        maxs = mathutils.Vector((1.0, 1.0, 1.0))
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z, 1.0)
    bpy.ops.object.camera_add(location=center + mathutils.Vector((8.0, -10.0, 7.0)))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.55
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1100
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Preview/export promoted measured component source recipes in Blender.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    bundle, assets, primitive_counts = load_measured_components(bundle_path)
    report = make_report(bundle_path, bundle, assets, primitive_counts, generated=False)
    if args.validate_only:
        if args.json_report:
            report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS measured component Blender adapter validation: "
            f"{report['asset_count']} assets, {report['proof_primitive_count']} primitives, {report['socket_count']} sockets"
        )
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    run_blender_export(assets, out_root, report, args.render)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
