#!/usr/bin/env python3
"""Validate asset polish join/export reports.

This validator checks the post-polish join/export report without importing
Blender or reading source recipes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = Path("/tmp/gameguy_asset_polish_join_export_v0/asset_polish_join_export_report_v0.json")
REPORT_SCHEMA = "asset_polish_join_export_report_v0"
POLISH_EXECUTION_SCHEMA = "asset_polish_blender_execution_report_v0"
REQUIRED_UNIQUE_TOOLS = {"export_gltf", "join_objects", "save_blend_file"}
REQUIRED_RULES = {
    "consumes_asset_polish_blender_execution_report_v0": True,
    "consumes_completed_polish_blend": True,
    "reads_source_recipe": False,
    "runs_asset_pump": False,
    "executes_design_logic": False,
    "joins_existing_polish_meshes_only": True,
    "generated_outputs_stay_under_tmp": True,
}
REQUIRED_QUALITY_FLAGS = {
    "source_polish_execution_complete",
    "joined_single_mesh_object",
    "material_slots_preserved",
    "uv_layer_preserved",
    "export_written",
    "outputs_under_tmp",
    "source_recipe_not_read",
    "source_asset_json_not_mutated",
}


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


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{field} must be a boolean")
    return value


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_string_list(value: Any, field: str) -> list[str]:
    result = []
    for index, item in enumerate(require_list(value, field)):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def is_under_root(path_text: str, root: Path) -> bool:
    path = Path(path_text)
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def validate_no_repo_generated_outputs(report: dict[str, Any]) -> None:
    for field in ("joined_blend_path", "glb_path"):
        value = report.get(field)
        if value is None:
            continue
        if is_under_root(require_string(value, field), ROOT):
            fail(f"{field} must not point inside the repo")


def validate_rules(report: dict[str, Any]) -> None:
    rules = require_object(report.get("rules"), "rules")
    for key, expected in REQUIRED_RULES.items():
        if rules.get(key) is not expected:
            fail(f"rules.{key} must be {str(expected).lower()}")


def validate_quality(report: dict[str, Any]) -> None:
    quality = require_object(report.get("quality_pass"), "quality_pass")
    for key in sorted(REQUIRED_QUALITY_FLAGS):
        if quality.get(key) is not True:
            fail(f"quality_pass.{key} must be true")


def validate_counts(report: dict[str, Any]) -> None:
    if require_int(report.get("source_future_step_count"), "source_future_step_count", minimum=0) != 0:
        fail("source_future_step_count must be 0")
    if require_int(report.get("source_skipped_future_step_count"), "source_skipped_future_step_count", minimum=0) != 0:
        fail("source_skipped_future_step_count must be 0")
    if require_int(report.get("source_executed_step_count"), "source_executed_step_count", minimum=1) != require_int(
        report.get("source_supported_step_count"),
        "source_supported_step_count",
        minimum=1,
    ):
        fail("source_executed_step_count must match source_supported_step_count")
    source_meshes = require_int(report.get("source_mesh_object_count"), "source_mesh_object_count", minimum=2)
    prejoin_meshes = require_int(report.get("prejoin_mesh_object_count"), "prejoin_mesh_object_count", minimum=2)
    if prejoin_meshes != source_meshes:
        fail("prejoin_mesh_object_count must match source_mesh_object_count")
    if require_int(report.get("prejoin_asset_polish_generated_object_count"), "prejoin_asset_polish_generated_object_count", minimum=1) < 1:
        fail("prejoin_asset_polish_generated_object_count must include generated polish meshes")
    if require_int(report.get("joined_mesh_object_count"), "joined_mesh_object_count", minimum=1) != 1:
        fail("joined_mesh_object_count must be 1")
    source_uv_loops = require_int(report.get("source_uv_loop_count"), "source_uv_loop_count", minimum=1)
    prejoin_uv_loops = require_int(report.get("prejoin_uv_loop_count"), "prejoin_uv_loop_count", minimum=1)
    if prejoin_uv_loops != source_uv_loops:
        fail("prejoin_uv_loop_count must match source_uv_loop_count")
    joined_object = require_object(report.get("joined_object"), "joined_object")
    require_string(joined_object.get("object"), "joined_object.object")
    if require_int(joined_object.get("uv_loop_count"), "joined_object.uv_loop_count", minimum=1) < source_uv_loops:
        fail("joined_object.uv_loop_count must preserve source UV loops")
    if require_string(joined_object.get("active_uv_layer"), "joined_object.active_uv_layer") != "polish_uv0":
        fail("joined_object.active_uv_layer must be polish_uv0")
    source_material_slots = require_string_list(report.get("source_material_slots"), "source_material_slots")
    if require_int(report.get("source_material_slot_count"), "source_material_slot_count", minimum=1) != len(set(source_material_slots)):
        fail("source_material_slot_count must match source_material_slots")
    joined_material_slots = require_string_list(joined_object.get("material_slots"), "joined_object.material_slots")
    missing_materials = sorted(set(source_material_slots) - set(joined_material_slots))
    if missing_materials:
        fail(f"joined_object.material_slots must preserve source material slots: {missing_materials}")
    require_object(joined_object.get("material_face_counts"), "joined_object.material_face_counts")
    if require_int(report.get("glb_file_size_bytes"), "glb_file_size_bytes", minimum=1) <= 0:
        fail("glb_file_size_bytes must be positive")


def validate_prejoin_objects(report: dict[str, Any]) -> None:
    prejoin_objects = require_list(report.get("prejoin_objects"), "prejoin_objects")
    if len(prejoin_objects) != report["prejoin_mesh_object_count"]:
        fail("prejoin_objects length must match prejoin_mesh_object_count")
    generated_count = 0
    for index, item in enumerate(prejoin_objects):
        obj = require_object(item, f"prejoin_objects[{index}]")
        require_string(obj.get("object"), f"prejoin_objects[{index}].object")
        require_int(obj.get("face_count"), f"prejoin_objects[{index}].face_count", minimum=1)
        require_int(obj.get("uv_loop_count"), f"prejoin_objects[{index}].uv_loop_count", minimum=1)
        require_string(obj.get("active_uv_layer"), f"prejoin_objects[{index}].active_uv_layer")
        if require_bool(obj.get("asset_polish_generated"), f"prejoin_objects[{index}].asset_polish_generated"):
            generated_count += 1
    if generated_count < 1:
        fail("prejoin_objects must include at least one generated polish object")


def validate_report(report: dict[str, Any]) -> None:
    if report.get("schema") != REPORT_SCHEMA:
        fail(f"schema must be {REPORT_SCHEMA}")
    if report.get("source_execution_schema") != POLISH_EXECUTION_SCHEMA:
        fail(f"source_execution_schema must be {POLISH_EXECUTION_SCHEMA}")
    require_string(report.get("adapter"), "adapter")
    require_string(report.get("source_execution_report"), "source_execution_report")
    require_string(report.get("source_blend"), "source_blend")
    require_string(report.get("plan_id"), "plan_id")
    source_asset_id = require_string(report.get("source_asset_id"), "source_asset_id")
    asset_id = require_string(report.get("asset_id"), "asset_id")
    if asset_id != source_asset_id:
        fail("asset_id must match source_asset_id")
    if require_bool(report.get("generated_outputs_created"), "generated_outputs_created") is not True:
        fail("generated_outputs_created must be true")
    require_string(report.get("out_root"), "out_root")
    require_string(report.get("joined_object_name"), "joined_object_name")
    require_string(report.get("joined_blend_path"), "joined_blend_path")
    require_string(report.get("glb_path"), "glb_path")
    unique_tools = set(require_string_list(report.get("unique_tools"), "unique_tools"))
    if not REQUIRED_UNIQUE_TOOLS.issubset(unique_tools):
        fail("unique_tools must include join/export tool families")
    validate_no_repo_generated_outputs(report)
    validate_rules(report)
    validate_quality(report)
    validate_counts(report)
    validate_prejoin_objects(report)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an asset polish join/export report.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    validate_report(load_json(args.report))
    print("PASS asset polish join/export report validation: joined_meshes=1 glb_written=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
