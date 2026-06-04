#!/usr/bin/env python3
"""Join and export a completed asset polish Blender execution scene.

This is an adapter: it consumes a completed asset_polish_blender_execution
report plus the saved pre-join .blend. It does not read source recipes, run
the asset pump, or choose new design operations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_asset_polish_blender_execution_report_v0 import validate_report as validate_polish_execution_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXECUTION_REPORT = Path("/tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json")
DEFAULT_OUT = Path("/tmp/gameguy_asset_polish_join_export_v0")
REPORT_SCHEMA = "asset_polish_join_export_report_v0"
POLISH_EXECUTION_SCHEMA = "asset_polish_blender_execution_report_v0"
JOINED_OBJECT_NAME = "blocky_fence_post_polished_joined_v0"
UV_LAYER_NAME = "polish_uv0"


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
        fail(f"JSON must be an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def is_under_tmp(path: Path) -> bool:
    try:
        path.resolve().relative_to(Path("/tmp").resolve())
    except ValueError:
        return False
    return True


def source_material_slots(execution_report: dict[str, Any]) -> list[str]:
    material_assignment = require_object(execution_report.get("material_assignment"), "execution_report.material_assignment")
    face_counts = require_object(material_assignment.get("assigned_faces_by_slot"), "execution_report.material_assignment.assigned_faces_by_slot")
    return sorted(str(name) for name in face_counts)


def validate_source_execution_report(execution_report_path: Path, blend_path: Path | None) -> dict[str, Any]:
    report = load_json(execution_report_path)
    validate_polish_execution_report(report)
    if report.get("schema") != POLISH_EXECUTION_SCHEMA:
        fail(f"source execution report schema must be {POLISH_EXECUTION_SCHEMA}")
    if report.get("future_step_count") != 0 or report.get("skipped_future_step_count") != 0:
        fail("source polish execution report must have no future/skipped steps before join/export")
    if report.get("executed_step_count") != report.get("supported_step_count"):
        fail("source polish execution report must execute all supported steps")
    source_blend = Path(require_string(report.get("blend_path"), "execution_report.blend_path"))
    if blend_path is not None and blend_path != source_blend:
        fail("explicit --blend must match execution_report.blend_path")
    if not source_blend.exists():
        fail(f"source blend is missing: {source_blend}")
    if not is_under_tmp(source_blend):
        fail("source blend must be under /tmp")
    return report


def base_report(execution_report_path: Path, execution_report: dict[str, Any], out_root: Path, *, generated: bool) -> dict[str, Any]:
    source_blend = require_string(execution_report.get("blend_path"), "execution_report.blend_path")
    material_slots = source_material_slots(execution_report)
    return {
        "schema": REPORT_SCHEMA,
        "adapter": "scripts/export_asset_polish_joined_v0.py",
        "source_execution_report": str(execution_report_path),
        "source_execution_schema": execution_report["schema"],
        "source_blend": source_blend,
        "plan_id": execution_report["plan_id"],
        "source_recipe_id": execution_report["source_recipe_id"],
        "source_asset_id": execution_report["source_asset_id"],
        "asset_id": execution_report["asset_id"],
        "generated_outputs_created": generated,
        "out_root": str(out_root),
        "source_supported_step_count": execution_report["supported_step_count"],
        "source_future_step_count": execution_report["future_step_count"],
        "source_executed_step_count": execution_report["executed_step_count"],
        "source_skipped_future_step_count": execution_report["skipped_future_step_count"],
        "source_mesh_object_count": execution_report["mesh_object_count"],
        "source_uv_loop_count": execution_report["uv_unwrap_loop_count"],
        "source_material_slot_count": len(material_slots),
        "source_material_slots": material_slots,
        "unique_tools": ["export_gltf", "join_objects", "save_blend_file"],
        "prejoin_objects": [],
        "joined_object": {},
        "quality_pass": {
            "source_polish_execution_complete": execution_report["future_step_count"] == 0
            and execution_report["executed_step_count"] == execution_report["supported_step_count"],
            "joined_single_mesh_object": False,
            "material_slots_preserved": False,
            "uv_layer_preserved": False,
            "export_written": False,
            "outputs_under_tmp": is_under_tmp(out_root),
            "source_recipe_not_read": True,
            "source_asset_json_not_mutated": True,
        },
        "rules": {
            "consumes_asset_polish_blender_execution_report_v0": True,
            "consumes_completed_polish_blend": True,
            "reads_source_recipe": False,
            "runs_asset_pump": False,
            "executes_design_logic": False,
            "joins_existing_polish_meshes_only": True,
            "generated_outputs_stay_under_tmp": True,
        },
    }


def visible_mesh_objects(bpy: Any) -> list[Any]:
    return [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not obj.hide_get() and not obj.hide_viewport and not obj.name.startswith("Preview_")
    ]


def active_uv_loop_count(obj: Any) -> int:
    active = obj.data.uv_layers.active
    if active is None:
        return 0
    if hasattr(active, "data"):
        return len(active.data)
    if hasattr(active, "uv"):
        return len(active.uv)
    return 0


def material_face_counts(obj: Any) -> dict[str, int]:
    material_names = [slot.material.name if slot.material else "none" for slot in obj.material_slots]
    counts: dict[str, int] = {}
    for polygon in obj.data.polygons:
        material_name = material_names[polygon.material_index] if polygon.material_index < len(material_names) else "none"
        counts[material_name] = counts.get(material_name, 0) + 1
    return dict(sorted(counts.items()))


def mesh_object_report(obj: Any) -> dict[str, Any]:
    active_uv = obj.data.uv_layers.active
    return {
        "object": obj.name,
        "vertex_count": len(obj.data.vertices),
        "face_count": len(obj.data.polygons),
        "material_slot_count": len(obj.material_slots),
        "material_slots": [slot.material.name if slot.material else "none" for slot in obj.material_slots],
        "uv_layer_count": len(obj.data.uv_layers),
        "active_uv_layer": active_uv.name if active_uv else None,
        "uv_loop_count": active_uv_loop_count(obj),
        "asset_polish_generated": bool(obj.get("asset_polish_generated", False)),
    }


def normalize_joined_uv_layer(joined_obj: Any) -> int:
    active = joined_obj.data.uv_layers.active
    if active is None and len(joined_obj.data.uv_layers) > 0:
        active = joined_obj.data.uv_layers[0]
        joined_obj.data.uv_layers.active = active
    if active is not None:
        active.name = UV_LAYER_NAME
    return active_uv_loop_count(joined_obj)


def export_glb(bpy: Any, joined_obj: Any, glb_path: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    joined_obj.select_set(True)
    bpy.context.view_layer.objects.active = joined_obj
    try:
        bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True)
    except TypeError:
        bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB")


def run_blender_join_export(execution_report_path: Path, execution_report: dict[str, Any], out_root: Path, *, export: bool) -> None:
    try:
        import bpy  # type: ignore
    except ModuleNotFoundError:
        fail("Join/export requires Blender Python. Use --validate-only with normal Python.")

    source_blend = Path(execution_report["blend_path"])
    out_root.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(out_root):
        fail("--out must be under /tmp")

    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    meshes = visible_mesh_objects(bpy)
    if len(meshes) < 2:
        fail("join/export requires at least two visible mesh objects in the pre-join blend")
    prejoin = [mesh_object_report(obj) for obj in meshes]
    missing_uv = [row["object"] for row in prejoin if row["uv_loop_count"] <= 0]
    if missing_uv:
        fail(f"pre-join mesh objects are missing UV data: {missing_uv}")
    prejoin_uv_loop_count = sum(int(row["uv_loop_count"]) for row in prejoin)
    generated_prejoin_count = sum(1 for row in prejoin if row["asset_polish_generated"])

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    joined_obj = bpy.context.object
    joined_obj.name = JOINED_OBJECT_NAME
    joined_obj.data.name = f"{JOINED_OBJECT_NAME}_mesh"
    joined_obj["asset_id"] = execution_report["asset_id"]
    joined_obj["source_plan_id"] = execution_report["plan_id"]
    joined_obj["source_recipe_id"] = execution_report["source_recipe_id"]
    joined_obj["asset_polish_joined"] = True

    uv_loop_count = normalize_joined_uv_layer(joined_obj)
    if not any(modifier.type == "WEIGHTED_NORMAL" for modifier in joined_obj.modifiers):
        modifier = joined_obj.modifiers.new(name="joined_weighted_normals", type="WEIGHTED_NORMAL")
        if hasattr(modifier, "keep_sharp"):
            modifier.keep_sharp = True

    source_slots = set(source_material_slots(execution_report))
    joined_material_names = {slot.material.name for slot in joined_obj.material_slots if slot.material is not None}
    material_slots_preserved = source_slots.issubset(joined_material_names)
    joined_blend_path = out_root / "asset_polish_joined_v0.blend"
    glb_path = out_root / f"{JOINED_OBJECT_NAME}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(joined_blend_path))
    export_written = False
    glb_file_size = 0
    if export:
        export_glb(bpy, joined_obj, glb_path)
        export_written = glb_path.exists() and glb_path.stat().st_size > 0
        glb_file_size = glb_path.stat().st_size if glb_path.exists() else 0

    report = base_report(execution_report_path, execution_report, out_root, generated=True)
    mesh_count_after = len(visible_mesh_objects(bpy))
    joined_report = mesh_object_report(joined_obj)
    joined_report.update(
        {
            "material_face_counts": material_face_counts(joined_obj),
            "weighted_normal_modifier_count": sum(1 for modifier in joined_obj.modifiers if modifier.type == "WEIGHTED_NORMAL"),
        }
    )
    report.update(
        {
            "prejoin_mesh_object_count": len(prejoin),
            "prejoin_asset_polish_generated_object_count": generated_prejoin_count,
            "prejoin_uv_loop_count": prejoin_uv_loop_count,
            "prejoin_objects": prejoin,
            "joined_mesh_object_count": mesh_count_after,
            "joined_object_name": joined_obj.name,
            "joined_blend_path": str(joined_blend_path),
            "glb_path": str(glb_path) if export else None,
            "glb_file_size_bytes": glb_file_size,
            "joined_object": joined_report,
        }
    )
    report["quality_pass"] = {
        "source_polish_execution_complete": execution_report["future_step_count"] == 0
        and execution_report["executed_step_count"] == execution_report["supported_step_count"],
        "joined_single_mesh_object": mesh_count_after == 1,
        "material_slots_preserved": material_slots_preserved,
        "uv_layer_preserved": joined_report["active_uv_layer"] == UV_LAYER_NAME and uv_loop_count >= prejoin_uv_loop_count,
        "export_written": export_written,
        "outputs_under_tmp": is_under_tmp(joined_blend_path) and (not export or is_under_tmp(glb_path)),
        "source_recipe_not_read": True,
        "source_asset_json_not_mutated": True,
    }
    report_path = out_root / "asset_polish_join_export_report_v0.json"
    write_json(report_path, report)
    print(
        "PASS asset polish join/export: "
        f"prejoin_meshes={len(prejoin)} joined_meshes={mesh_count_after} "
        f"uv_loops={uv_loop_count} glb_written={str(export_written).lower()} out={out_root}"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Join and export a completed asset polish Blender execution scene.")
    parser.add_argument("--execution-report", type=Path, default=DEFAULT_EXECUTION_REPORT)
    parser.add_argument("--blend", type=Path, help="Optional explicit source .blend path; must match the execution report.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--export-glb", action="store_true")
    parser.add_argument("--json-report", type=Path, help="Report path for --validate-only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    execution_report_path = args.execution_report if args.execution_report.is_absolute() else ROOT / args.execution_report
    blend_path = args.blend if args.blend is None or args.blend.is_absolute() else ROOT / args.blend
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    execution_report = validate_source_execution_report(execution_report_path, blend_path)
    if args.validate_only:
        report = base_report(execution_report_path, execution_report, out_root, generated=False)
        report_path = args.json_report if args.json_report else out_root / "asset_polish_join_export_validate_only_report_v0.json"
        report_path = report_path if report_path.is_absolute() else ROOT / report_path
        write_json(report_path, report)
        print(
            "PASS asset polish join/export validation: "
            f"source_meshes={execution_report['mesh_object_count']} "
            f"source_uv_loops={execution_report['uv_unwrap_loop_count']} "
            f"future={execution_report['future_step_count']}"
        )
        return 0
    run_blender_join_export(execution_report_path, execution_report, out_root, export=args.export_glb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
