#!/usr/bin/env python3
"""Blender adapter for measured gameguy_asset_v0 JSON.

This consumes an asset pump manifest. It does not read measured source recipes,
run old measured compilers, or make proof-primitive geometry decisions.

Validate with normal Python:

python3 scripts/export_blender_measured_components_preview_v0.py \
  --manifest /tmp/gameguy_measured_asset_pump_v0/manifest.json \
  --validate-only

Export with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/export_blender_measured_components_preview_v0.py -- \
  --manifest /tmp/gameguy_measured_asset_pump_v0/manifest.json \
  --out /tmp/gameguy_measured_components_preview_v0
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from export_blender_asset_preview_v0 import (  # type: ignore
    add_scene_context,
    create_asset_object,
    create_connector_marker,
    fail,
    load_assets_from_manifest,
    make_material,
    material_key,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("/tmp/gameguy_measured_asset_pump_v0/manifest.json")
DEFAULT_OUT = Path("/tmp/gameguy_measured_components_preview_v0")
MEASURED_BUNDLE_SCHEMA = "asset_mill_measured_component_bundle_v0"


def require_measured_assets(manifest_path: Path) -> tuple[dict[str, Any], list[tuple[Path, dict[str, Any]]], dict[str, int]]:
    manifest, assets = load_assets_from_manifest(manifest_path)
    if manifest.get("source_bundle_schema") != MEASURED_BUNDLE_SCHEMA:
        fail(f"manifest source_bundle_schema must be {MEASURED_BUNDLE_SCHEMA}")

    primitive_counts: dict[str, int] = {"cube": 0, "cylinder": 0, "curve": 0}
    version_counts = {"v1": 0, "v2": 0}
    for _, asset in assets:
        asset_id = asset["asset_id"]
        if asset.get("asset_kind") != "measured_component":
            fail(f"{asset_id}.asset_kind must be measured_component")
        if asset.get("source_schema") != MEASURED_BUNDLE_SCHEMA:
            fail(f"{asset_id}.source_schema must be {MEASURED_BUNDLE_SCHEMA}")
        if asset.get("source_operation") != "proof_primitives":
            fail(f"{asset_id}.source_operation must be proof_primitives")
        source_version = asset.get("source_version")
        if source_version not in version_counts:
            fail(f"{asset_id}.source_version must be v1 or v2")
        version_counts[source_version] += 1
        if not isinstance(asset.get("source_refs"), list) or not asset["source_refs"]:
            fail(f"{asset_id}.source_refs must be a non-empty list")
        source_terms = asset.get("source_terms")
        if not isinstance(source_terms, dict):
            fail(f"{asset_id}.source_terms must be an object")
        for field in ("geometry", "profiles", "operators"):
            if not isinstance(source_terms.get(field), list) or not source_terms[field]:
                fail(f"{asset_id}.source_terms.{field} must be a non-empty list")
        parts = asset.get("mesh", {}).get("parts")
        if not isinstance(parts, list) or not parts:
            fail(f"{asset_id}.mesh.parts must be a non-empty list")
        for part_index, part in enumerate(parts):
            if not isinstance(part, dict):
                fail(f"{asset_id}.mesh.parts[{part_index}] must be an object")
            primitive = part.get("source_primitive")
            if primitive not in primitive_counts:
                fail(f"{asset_id}.mesh.parts[{part_index}].source_primitive unsupported: {primitive}")
            primitive_counts[primitive] += 1

    return manifest, assets, version_counts | primitive_counts


def make_report(manifest_path: Path, manifest: dict[str, Any], assets: list[tuple[Path, dict[str, Any]]], counts: dict[str, int], *, generated: bool) -> dict[str, Any]:
    total_vertices = sum(len(asset["mesh"]["vertices"]) for _, asset in assets)
    total_faces = sum(len(asset["mesh"]["faces"]) for _, asset in assets)
    primitive_counts = {key: counts[key] for key in ("cube", "cylinder", "curve")}
    return {
        "schema": "blender_measured_components_preview_adapter_report_v0",
        "adapter": "scripts/export_blender_measured_components_preview_v0.py",
        "source_manifest": str(manifest_path),
        "source_manifest_schema": manifest["schema"],
        "source_bundle_schema": manifest["source_bundle_schema"],
        "asset_schema": "gameguy_asset_v0",
        "asset_count": len(assets),
        "v1_asset_count": counts["v1"],
        "v2_asset_count": counts["v2"],
        "proof_primitive_count": sum(primitive_counts.values()),
        "proof_primitive_counts": primitive_counts,
        "socket_count": sum(len(asset["connectors"]) for _, asset in assets),
        "total_vertices": total_vertices,
        "total_faces": total_faces,
        "generated_outputs_created": generated,
        "rules": {
            "consumes_deterministic_asset_json": True,
            "reads_source_recipes": False,
            "runs_asset_pump": False,
            "imports_old_compiler_scripts": False,
            "runs_old_compiler_scripts": False,
            "source_design_logic": False,
        },
    }


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
        "default": make_material(bpy, "measured_asset_preview_default", (0.58, 0.58, 0.54, 1.0)),
        "walkable": make_material(bpy, "measured_asset_preview_walkable", (0.32, 0.56, 0.38, 1.0)),
        "barrier": make_material(bpy, "measured_asset_preview_barrier", (0.30, 0.42, 0.62, 1.0)),
        "support": make_material(bpy, "measured_asset_preview_support", (0.72, 0.62, 0.38, 1.0)),
        "blocked": make_material(bpy, "measured_asset_preview_blocked", (0.52, 0.42, 0.36, 1.0)),
        "cover": make_material(bpy, "measured_asset_preview_cover", (0.50, 0.50, 0.62, 1.0)),
        "connector": make_material(bpy, "measured_asset_preview_connector", (0.10, 0.38, 0.86, 1.0)),
    }

    columns = max(1, math.ceil(math.sqrt(len(assets))))
    spacing = 4.0
    for index, (_, asset) in enumerate(assets):
        row = index // columns
        col = index % columns
        offset = mathutils.Vector((col * spacing, row * spacing, 0.0))
        obj = create_asset_object(bpy, asset, offset, materials[material_key(asset)])
        obj["measured_component_adapter"] = True
        for connector in asset["connectors"]:
            create_connector_marker(bpy, asset["asset_id"], connector, offset, materials["connector"])

    add_scene_context(bpy, mathutils)
    blend_path = out_root / "measured_components_preview_v0.blend"
    report_path = out_root / "measured_components_preview_v0_report.json"
    report["generated_outputs_created"] = True
    report["blend_path"] = str(blend_path)
    report["object_count"] = len(bpy.context.scene.objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if render:
        render_path = out_root / "measured_components_preview_v0_workbench.png"
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
        report["render_path"] = str(render_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS measured component Blender export: assets={len(assets)} out={out_root}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Preview/export measured gameguy_asset_v0 JSON in Blender.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest, assets, counts = require_measured_assets(manifest_path)
    report = make_report(manifest_path, manifest, assets, counts, generated=False)
    if args.validate_only:
        if args.json_report:
            report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS measured component Blender adapter validation: "
            f"{report['asset_count']} assets, {report['proof_primitive_count']} parts, {report['socket_count']} connectors"
        )
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    run_blender_export(assets, out_root, report, args.render)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
