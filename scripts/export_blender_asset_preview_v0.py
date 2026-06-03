#!/usr/bin/env python3
"""Blender adapter for deterministic gameguy_asset_v0 JSON.

This script consumes asset pump output. It does not read source recipes and it
does not make source design decisions.

Validate with normal Python:

python3 scripts/export_blender_asset_preview_v0.py \
  --manifest /tmp/gameguy_asset_pump_v0/manifest.json \
  --validate-only

Export with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/export_blender_asset_preview_v0.py -- \
  --manifest /tmp/gameguy_asset_pump_v0/manifest.json \
  --out /tmp/gameguy_blender_asset_preview_v0
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("/tmp/gameguy_asset_pump_v0/manifest.json")
DEFAULT_OUT = Path("/tmp/gameguy_blender_asset_preview_v0")


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def require_vector(value: Any, field: str, length: int = 3) -> None:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")


def validate_asset(asset: dict[str, Any], path: Path) -> None:
    asset_id = asset.get("asset_id")
    if asset.get("schema") != "gameguy_asset_v0":
        fail(f"{path} schema must be gameguy_asset_v0")
    if not isinstance(asset_id, str) or not asset_id:
        fail(f"{path} asset_id must be a non-empty string")
    mesh = asset.get("mesh")
    if not isinstance(mesh, dict):
        fail(f"{asset_id}.mesh must be an object")
    if mesh.get("coordinate_space") != "local_xyz_m":
        fail(f"{asset_id}.mesh.coordinate_space must be local_xyz_m")
    vertices = mesh.get("vertices")
    faces = mesh.get("faces")
    if not isinstance(vertices, list) or len(vertices) < 3:
        fail(f"{asset_id}.mesh.vertices must contain at least 3 vertices")
    if not isinstance(faces, list) or not faces:
        fail(f"{asset_id}.mesh.faces must contain at least one face")
    for vertex_index, vertex in enumerate(vertices):
        require_vector(vertex, f"{asset_id}.mesh.vertices[{vertex_index}]")
    for face_index, face in enumerate(faces):
        if not isinstance(face, list) or len(face) < 3:
            fail(f"{asset_id}.mesh.faces[{face_index}] must contain at least 3 vertex indexes")
        for item in face:
            if not isinstance(item, int) or isinstance(item, bool) or item < 0 or item >= len(vertices):
                fail(f"{asset_id}.mesh.faces[{face_index}] contains invalid vertex index `{item}`")

    for connector_index, connector in enumerate(asset.get("connectors", [])):
        if not isinstance(connector, dict):
            fail(f"{asset_id}.connectors[{connector_index}] must be an object")
        if not isinstance(connector.get("connector_id"), str) or not connector["connector_id"]:
            fail(f"{asset_id}.connectors[{connector_index}].connector_id must be a non-empty string")
        require_vector(connector.get("position_m"), f"{asset_id}.connectors[{connector_index}].position_m")
        require_vector(connector.get("direction"), f"{asset_id}.connectors[{connector_index}].direction")


def load_assets_from_manifest(manifest_path: Path) -> tuple[dict[str, Any], list[tuple[Path, dict[str, Any]]]]:
    manifest = load_json_object(manifest_path)
    if manifest.get("schema") != "gameguy_asset_pump_manifest_v0":
        fail("manifest schema must be gameguy_asset_pump_manifest_v0")
    rows = manifest.get("assets")
    if not isinstance(rows, list) or not rows:
        fail("manifest assets must be a non-empty list")

    assets: list[tuple[Path, dict[str, Any]]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"manifest.assets[{index}] must be an object")
        rel_path = row.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            fail(f"manifest.assets[{index}].path must be a non-empty string")
        asset_path = manifest_path.parent / rel_path
        asset = load_json_object(asset_path)
        validate_asset(asset, asset_path)
        asset_id = asset["asset_id"]
        if asset_id in seen_ids:
            fail(f"duplicate asset_id in manifest assets: {asset_id}")
        seen_ids.add(asset_id)
        assets.append((asset_path, asset))
    if isinstance(manifest.get("asset_count"), int) and manifest["asset_count"] != len(assets):
        fail("manifest asset_count must match assets length")
    return manifest, assets


def make_report(manifest_path: Path, manifest: dict[str, Any], assets: list[tuple[Path, dict[str, Any]]], *, generated: bool) -> dict[str, Any]:
    total_vertices = sum(len(asset["mesh"]["vertices"]) for _, asset in assets)
    total_faces = sum(len(asset["mesh"]["faces"]) for _, asset in assets)
    return {
        "schema": "blender_asset_preview_adapter_report_v0",
        "adapter": "scripts/export_blender_asset_preview_v0.py",
        "source_manifest": str(manifest_path),
        "source_manifest_schema": manifest["schema"],
        "asset_schema": "gameguy_asset_v0",
        "asset_count": len(assets),
        "total_vertices": total_vertices,
        "total_faces": total_faces,
        "generated_outputs_created": generated,
        "rules": {
            "consumes_deterministic_asset_json": True,
            "reads_source_recipes": False,
            "runs_asset_pump": False,
            "source_design_logic": False,
        },
    }


def material_key(asset: dict[str, Any]) -> str:
    tags = set(asset.get("semantic_tags", []))
    if "walkable" in tags:
        return "walkable"
    if "barrier" in tags or "rail" in tags:
        return "barrier"
    if "support" in tags:
        return "support"
    if "blocked" in tags or "line_of_sight_blocker" in tags:
        return "blocked"
    if "cover" in tags:
        return "cover"
    return "default"


def run_blender_export(assets: list[tuple[Path, dict[str, Any]]], out_root: Path, report: dict[str, Any], render: bool) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail("Blender export requires Blender Python. Use --validate-only with normal Python.")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    materials = {
        "default": make_material(bpy, "asset_preview_default", (0.58, 0.58, 0.54, 1.0)),
        "walkable": make_material(bpy, "asset_preview_walkable", (0.32, 0.56, 0.38, 1.0)),
        "barrier": make_material(bpy, "asset_preview_barrier", (0.30, 0.42, 0.62, 1.0)),
        "support": make_material(bpy, "asset_preview_support", (0.72, 0.62, 0.38, 1.0)),
        "blocked": make_material(bpy, "asset_preview_blocked", (0.52, 0.42, 0.36, 1.0)),
        "cover": make_material(bpy, "asset_preview_cover", (0.50, 0.50, 0.62, 1.0)),
        "connector": make_material(bpy, "asset_preview_connector", (0.10, 0.38, 0.86, 1.0)),
    }

    columns = max(1, math.ceil(math.sqrt(len(assets))))
    spacing = 3.6
    created = []
    for index, (_, asset) in enumerate(assets):
        row = index // columns
        col = index % columns
        offset = mathutils.Vector((col * spacing, row * spacing, 0.0))
        created.append(create_asset_object(bpy, asset, offset, materials[material_key(asset)]))
        for connector in asset["connectors"]:
            create_connector_marker(bpy, asset["asset_id"], connector, offset, materials["connector"])

    add_scene_context(bpy, mathutils)
    blend_path = out_root / "asset_preview_v0.blend"
    report_path = out_root / "asset_preview_v0_report.json"
    report["generated_outputs_created"] = True
    report["blend_path"] = str(blend_path)
    report["object_count"] = len(bpy.context.scene.objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if render:
        render_path = out_root / "asset_preview_v0_workbench.png"
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS Blender asset preview export: assets={len(created)} out={out_root}")


def make_material(bpy: Any, name: str, color: tuple[float, float, float, float]) -> Any:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def create_asset_object(bpy: Any, asset: dict[str, Any], offset: Any, material: Any) -> Any:
    mesh_data = asset["mesh"]
    vertices = [tuple(float(value) + float(offset[index]) for index, value in enumerate(vertex)) for vertex in mesh_data["vertices"]]
    faces = [tuple(int(index) for index in face) for face in mesh_data["faces"]]
    mesh = bpy.data.meshes.new(f"{asset['asset_id']}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(asset["asset_id"], mesh)
    obj.data.materials.append(material)
    obj["asset_id"] = asset["asset_id"]
    obj["asset_schema"] = asset["schema"]
    obj["architectural_role"] = asset["architectural_role"]
    obj["semantic_tags"] = ",".join(asset["semantic_tags"])
    obj["source_operation"] = asset["source_operation"]
    obj["adapter_only"] = True
    obj["no_production_approval"] = True
    obj["no_structural_safety"] = True
    bpy.context.collection.objects.link(obj)
    return obj


def create_connector_marker(bpy: Any, asset_id: str, connector: dict[str, Any], offset: Any, material: Any) -> Any:
    position = connector["position_m"]
    location = tuple(float(position[index]) + float(offset[index]) for index in range(3))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.045, location=location)
    obj = bpy.context.object
    obj.name = f"{asset_id}.{connector['connector_id']}"
    obj.data.materials.append(material)
    obj["asset_id"] = asset_id
    obj["connector_id"] = connector["connector_id"]
    obj["adapter_only"] = True
    return obj


def add_scene_context(bpy: Any, mathutils: Any) -> None:
    bpy.context.scene.world.color = (0.78, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(5.0, -7.0, 8.0))
    light = bpy.context.object
    light.name = "asset_preview_area_light"
    light.data.energy = 500.0
    light.data.size = 6.0

    objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if objs:
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
    parser = argparse.ArgumentParser(description="Preview/export deterministic gameguy_asset_v0 JSON in Blender.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true", help="Validate asset JSON without importing bpy or writing outputs.")
    parser.add_argument("--render", action="store_true", help="Write a Workbench PNG render in Blender mode.")
    parser.add_argument("--json-report", type=Path, help="Optional validation report path for validate-only mode.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest, assets = load_assets_from_manifest(manifest_path)
    report = make_report(manifest_path, manifest, assets, generated=False)

    if args.validate_only:
        if args.json_report:
            report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS Blender asset adapter validation: "
            f"{report['asset_count']} assets, {report['total_vertices']} vertices, {report['total_faces']} faces"
        )
        return 0

    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    run_blender_export(assets, out_root, report, args.render)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
