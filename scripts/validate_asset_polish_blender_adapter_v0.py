#!/usr/bin/env python3
"""Validate asset_polish_tool_plan_v0 for a future Blender adapter.

This script is intentionally validate-only. It does not import Blender, create
meshes, apply modifiers, render media, export files, or mutate source assets.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = Path("/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json")
DEFAULT_TOOL_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
DEFAULT_REPORT = Path("/tmp/gameguy_asset_polish_blender_adapter_v0/asset_polish_blender_adapter_validation_report_v0.json")
PLAN_SCHEMA = "asset_polish_tool_plan_v0"
TOOL_DICTIONARY_SCHEMA = "blender_tool_dictionary_v0"
REPORT_SCHEMA = "asset_polish_blender_adapter_validation_report_v0"
SUPPORTED_OPERATIONS = {"bevel_edges", "boolean_cut", "chamfer_edges", "extrude_along_normals", "inset_faces", "material_assign", "sweep_profile", "uv_unwrap", "weighted_normals"}
SUPPORTED_TOOLS = {"curve_bevel_profile", "extrude_faces", "inset_faces", "material_assign_by_part", "modifier_bevel", "modifier_boolean", "modifier_weighted_normal", "uv_smart_project", "uv_unwrap"}
FUTURE_OPERATIONS: set[str] = set()
FUTURE_TOOLS: set[str] = set()
KNOWN_OPERATIONS = SUPPORTED_OPERATIONS | FUTURE_OPERATIONS
KNOWN_SELECTOR_KINDS = {
    "all_visible_hard_edges",
    "all_visible_mesh_parts",
    "edge_band",
    "edge_role",
    "face_border",
    "part_ids",
    "side_faces",
}
FIRST_EXECUTION_SELECTOR_KINDS = {"all_visible_hard_edges", "all_visible_mesh_parts", "edge_band", "edge_role", "face_border", "part_ids", "side_faces"}
SIDE_FACES = {"front", "back", "left", "right"}
GEOMETRY_STAGE_NAMES = {"assembly", "base_form", "shape_refinement", "sculpt_detail", "retopo_cleanup"}
REQUIRED_TOP_LEVEL_FIELDS = (
    "schema",
    "plan_id",
    "source_recipe_id",
    "source_asset",
    "dimensions_m",
    "targets",
    "steps",
    "material_slots",
    "summary",
    "rules",
    "no_claims",
)


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {display_path(path)}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"{display_path(path)} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def add_error(errors: list[str], field: str, message: str) -> None:
    errors.append(f"{field}: {message}")


def as_string(value: Any, field: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value:
        add_error(errors, field, "must be a non-empty string")
        return None
    return value


def as_bool(value: Any, field: str, errors: list[str]) -> bool | None:
    if not isinstance(value, bool):
        add_error(errors, field, "must be a boolean")
        return None
    return value


def as_object(value: Any, field: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        add_error(errors, field, "must be an object")
        return None
    return value


def as_list(value: Any, field: str, errors: list[str], *, allow_empty: bool = False) -> list[Any] | None:
    if not isinstance(value, list):
        add_error(errors, field, "must be a list")
        return None
    if not allow_empty and not value:
        add_error(errors, field, "must not be empty")
        return None
    return value


def as_string_list(value: Any, field: str, errors: list[str], *, allow_empty: bool = False) -> list[str] | None:
    items = as_list(value, field, errors, allow_empty=allow_empty)
    if items is None:
        return None
    result: list[str] = []
    for index, item in enumerate(items):
        text = as_string(item, f"{field}[{index}]", errors)
        if text is not None:
            result.append(text)
    return result


def as_number(value: Any, field: str, errors: list[str], *, positive: bool = False, nonzero: bool = False) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        add_error(errors, field, "must be a number")
        return None
    number = float(value)
    if not math.isfinite(number):
        add_error(errors, field, "must be finite")
        return None
    if positive and number <= 0.0:
        add_error(errors, field, "must be positive")
    if nonzero and number == 0.0:
        add_error(errors, field, "must be non-zero")
    return number


def as_int(value: Any, field: str, errors: list[str], *, minimum: int = 0) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        add_error(errors, field, "must be an integer")
        return None
    if value < minimum:
        add_error(errors, field, f"must be >= {minimum}")
    return value


def load_tool_dictionary(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    dictionary = load_json(path)
    errors: list[str] = []
    if dictionary.get("schema") != TOOL_DICTIONARY_SCHEMA:
        fail(f"tool dictionary schema must be {TOOL_DICTIONARY_SCHEMA}")
    stages = as_string_list(dictionary.get("stages"), "tool_dictionary.stages", errors)
    tools = as_list(dictionary.get("tools"), "tool_dictionary.tools", errors)
    if errors:
        fail("; ".join(errors))
    tool_map: dict[str, dict[str, Any]] = {}
    assert tools is not None
    for index, value in enumerate(tools):
        tool = as_object(value, f"tool_dictionary.tools[{index}]", errors)
        if tool is None:
            continue
        tool_id = as_string(tool.get("tool_id"), f"tool_dictionary.tools[{index}].tool_id", errors)
        if tool_id is None:
            continue
        if tool_id in tool_map:
            fail(f"duplicate tool_id `{tool_id}`")
        tool_map[tool_id] = tool
    if errors:
        fail("; ".join(errors))
    assert stages is not None
    return tool_map, stages


def validate_dimensions(plan: dict[str, Any], errors: list[str]) -> None:
    dimensions = as_object(plan.get("dimensions_m"), "dimensions_m", errors)
    if dimensions is None:
        return
    for key in ("width", "depth", "height"):
        as_number(dimensions.get(key), f"dimensions_m.{key}", errors, positive=True)


def validate_selector(
    target_id: str,
    selector: dict[str, Any],
    target_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> tuple[str | None, str | None]:
    kind = as_string(selector.get("kind"), f"{target_id}.selector.kind", errors)
    if kind is None:
        return None, None
    if kind not in KNOWN_SELECTOR_KINDS:
        add_error(errors, f"{target_id}.selector.kind", f"unknown selector `{kind}`")
        return kind, None
    from_target = None
    if kind == "edge_role":
        as_string(selector.get("edge_role"), f"{target_id}.selector.edge_role", errors)
    elif kind == "side_faces":
        faces = as_string_list(selector.get("faces"), f"{target_id}.selector.faces", errors)
        if faces is not None:
            invalid = [face for face in faces if face not in SIDE_FACES]
            if invalid:
                add_error(errors, f"{target_id}.selector.faces", f"unknown side faces {invalid}")
    elif kind == "face_border":
        from_target = as_string(selector.get("from_target"), f"{target_id}.selector.from_target", errors)
        if from_target and from_target not in target_ids:
            add_error(errors, f"{target_id}.selector.from_target", f"references unknown target `{from_target}`")
    elif kind == "part_ids":
        as_string_list(selector.get("part_ids"), f"{target_id}.selector.part_ids", errors)
    elif kind == "edge_band":
        as_string(selector.get("band"), f"{target_id}.selector.band", errors)
    if kind not in FIRST_EXECUTION_SELECTOR_KINDS:
        warnings.append(f"{target_id}.selector.kind `{kind}` is recognized but not executable in the first future execution slice")
    return kind, from_target


def target_name_warnings(target_id: str, warnings: list[str]) -> None:
    parts = target_id.split(".")
    vague_tokens = {"edges", "faces", "parts", "target"}
    if len(parts) < 3 or target_id in vague_tokens:
        warnings.append(f"{target_id} is too vague for a stable polish target name")


def validate_targets(plan: dict[str, Any], errors: list[str], warnings: list[str]) -> tuple[set[str], list[dict[str, Any]], dict[str, str]]:
    target_ids: set[str] = set()
    target_reports: list[dict[str, Any]] = []
    selector_kinds: dict[str, str] = {}
    targets = as_list(plan.get("targets"), "targets", errors)
    if targets is None:
        return target_ids, target_reports, selector_kinds
    pending: list[tuple[str, dict[str, Any], list[str]]] = []
    for index, value in enumerate(targets):
        target = as_object(value, f"targets[{index}]", errors)
        if target is None:
            continue
        target_id = as_string(target.get("target_id"), f"targets[{index}].target_id", errors)
        if target_id is None:
            continue
        if target_id in target_ids:
            add_error(errors, target_id, "duplicate target_id")
        target_ids.add(target_id)
        source_part_ids = as_string_list(target.get("source_part_ids"), f"{target_id}.source_part_ids", errors)
        as_string_list(target.get("architectural_terms"), f"{target_id}.architectural_terms", errors)
        as_string(target.get("material_role"), f"{target_id}.material_role", errors)
        selector = as_object(target.get("selector"), f"{target_id}.selector", errors)
        target_name_warnings(target_id, warnings)
        pending.append((target_id, selector or {}, source_part_ids or []))
    for target_id, selector, source_part_ids in pending:
        selector_kind, from_target = validate_selector(target_id, selector, target_ids, errors, warnings)
        if selector_kind is not None:
            selector_kinds[target_id] = selector_kind
        target_reports.append(
            {
                "target_id": target_id,
                "selector_kind": selector_kind,
                "source_part_count": len(source_part_ids),
                "from_target": from_target,
                "validation_status": "fail" if any(error.startswith(target_id) for error in errors) else "pass",
            }
        )
    return target_ids, target_reports, selector_kinds


def report_param(report: list[dict[str, Any]], step_id: str, field: str, status: str, value: Any) -> None:
    report.append({"step_id": step_id, "field": field, "status": status, "value": value})


def validate_step_params(step_id: str, operation: str, params: dict[str, Any], errors: list[str], warnings: list[str]) -> list[dict[str, Any]]:
    param_reports: list[dict[str, Any]] = []
    if operation in {"bevel_edges", "chamfer_edges"}:
        width = as_number(params.get("width_m"), f"{step_id}.params.width_m", errors, positive=True)
        segments = as_int(params.get("segments"), f"{step_id}.params.segments", errors, minimum=1)
        profile = as_number(params.get("profile"), f"{step_id}.params.profile", errors)
        as_bool(params.get("harden_normals"), f"{step_id}.params.harden_normals", errors)
        if profile is not None and not 0.0 <= profile <= 1.0:
            add_error(errors, f"{step_id}.params.profile", "must be between 0 and 1")
        report_param(param_reports, step_id, "width_m", "checked", width)
        report_param(param_reports, step_id, "segments", "checked", segments)
    elif operation == "inset_faces":
        as_number(params.get("inset_m"), f"{step_id}.params.inset_m", errors, positive=True)
        as_number(params.get("depth_m"), f"{step_id}.params.depth_m", errors, nonzero=True)
        as_string(params.get("panel_mode"), f"{step_id}.params.panel_mode", errors)
        as_string_list(params.get("apply_to_faces"), f"{step_id}.params.apply_to_faces", errors)
    elif operation == "extrude_along_normals":
        depth = as_number(params.get("depth_m"), f"{step_id}.params.depth_m", errors, nonzero=True)
        lip_width = as_number(params.get("lip_width_m"), f"{step_id}.params.lip_width_m", errors, positive=True)
        as_string(params.get("lip_profile"), f"{step_id}.params.lip_profile", errors)
        if depth is not None and lip_width is not None and abs(depth) > lip_width:
            warnings.append(f"{step_id}.params.depth_m is greater than lip_width_m; verify the lip is intentionally tall/deep")
        report_param(param_reports, step_id, "depth_m", "checked", depth)
        report_param(param_reports, step_id, "lip_width_m", "checked", lip_width)
    elif operation == "boolean_cut":
        solver = as_string(params.get("solver"), f"{step_id}.params.solver", errors)
        if solver is not None and solver not in {"EXACT", "FAST"}:
            add_error(errors, f"{step_id}.params.solver", "must be EXACT or FAST")
        as_number(params.get("cut_depth_m"), f"{step_id}.params.cut_depth_m", errors, positive=True)
        as_bool(params.get("leave_shadow_panel"), f"{step_id}.params.leave_shadow_panel", errors)
        as_bool(params.get("cleanup_cutters"), f"{step_id}.params.cleanup_cutters", errors)
    elif operation == "sweep_profile":
        as_string(params.get("profile"), f"{step_id}.params.profile", errors)
        projection = as_number(params.get("projection_m"), f"{step_id}.params.projection_m", errors, positive=True)
        height = as_number(params.get("height_m"), f"{step_id}.params.height_m", errors, positive=True)
        lip_width = params.get("lip_width_m")
        if lip_width is not None:
            width = as_number(lip_width, f"{step_id}.params.lip_width_m", errors, positive=True)
            if projection is not None and width is not None and projection > width:
                warnings.append(f"{step_id}.params.projection_m is greater than lip_width_m; verify the lip projection")
        as_bool(params.get("fill_caps"), f"{step_id}.params.fill_caps", errors)
        report_param(param_reports, step_id, "projection_m", "checked", projection)
        report_param(param_reports, step_id, "height_m", "checked", height)
    elif operation == "material_assign":
        material_map = as_object(params.get("material_map"), f"{step_id}.params.material_map", errors)
        if material_map is not None:
            if not material_map:
                add_error(errors, f"{step_id}.params.material_map", "must not be empty")
            for key, value in material_map.items():
                as_string(key, f"{step_id}.params.material_map key", errors)
                as_string(value, f"{step_id}.params.material_map.{key}", errors)
    elif operation == "weighted_normals":
        as_bool(params.get("keep_sharp"), f"{step_id}.params.keep_sharp", errors)
        weight = as_number(params.get("weight"), f"{step_id}.params.weight", errors, positive=True)
        if weight is not None and not 1.0 <= weight <= 100.0:
            add_error(errors, f"{step_id}.params.weight", "must be between 1 and 100")
        report_param(param_reports, step_id, "weight", "checked", weight)
    elif operation == "uv_unwrap":
        method = as_string(params.get("method"), f"{step_id}.params.method", errors)
        if method is not None and method not in {"smart_uv_project", "uv_unwrap"}:
            add_error(errors, f"{step_id}.params.method", "must be smart_uv_project or uv_unwrap")
        as_number(params.get("island_margin"), f"{step_id}.params.island_margin", errors, positive=True)
        angle = as_number(params.get("angle_limit_degrees"), f"{step_id}.params.angle_limit_degrees", errors, positive=True)
        if angle is not None and angle > 180.0:
            add_error(errors, f"{step_id}.params.angle_limit_degrees", "must be <= 180")
    return param_reports


def adapter_status(operation: str, tool_id: str) -> str:
    if operation in SUPPORTED_OPERATIONS or tool_id in SUPPORTED_TOOLS:
        return "supported"
    if operation in FUTURE_OPERATIONS or tool_id in FUTURE_TOOLS:
        return "future"
    return "unknown"


def validate_steps(
    plan: dict[str, Any],
    tool_map: dict[str, dict[str, Any]],
    stage_order: list[str],
    target_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int, int]:
    step_reports: list[dict[str, Any]] = []
    operation_reports: list[dict[str, Any]] = []
    param_reports: list[dict[str, Any]] = []
    stage_reports: list[dict[str, Any]] = []
    steps = as_list(plan.get("steps"), "steps", errors)
    if steps is None:
        return step_reports, operation_reports, param_reports, stage_reports, 0, 0
    step_ids: set[str] = set()
    supported_count = 0
    future_count = 0
    stage_ranks = {stage: index for index, stage in enumerate(stage_order)}
    last_rank = -1
    uv_seen_at: int | None = None
    for index, value in enumerate(steps):
        step = as_object(value, f"steps[{index}]", errors)
        if step is None:
            continue
        step_id = as_string(step.get("step_id"), f"steps[{index}].step_id", errors) or f"steps[{index}]"
        if step_id in step_ids:
            add_error(errors, step_id, "duplicate step_id")
        step_ids.add(step_id)
        step_index = as_int(step.get("step_index"), f"{step_id}.step_index", errors)
        if step_index is not None and step_index != index:
            add_error(errors, f"{step_id}.step_index", "must match steps array index")
        operation = as_string(step.get("operation"), f"{step_id}.operation", errors) or ""
        tool_id = as_string(step.get("tool_id"), f"{step_id}.tool_id", errors) or ""
        target = as_string(step.get("target"), f"{step_id}.target", errors) or ""
        params = as_object(step.get("params"), f"{step_id}.params", errors) or {}
        deterministic = as_bool(step.get("deterministic"), f"{step_id}.deterministic", errors)
        if operation and operation not in KNOWN_OPERATIONS:
            add_error(errors, f"{step_id}.operation", f"unknown operation `{operation}`")
        tool = tool_map.get(tool_id)
        if tool is None:
            add_error(errors, f"{step_id}.tool_id", f"unknown tool_id `{tool_id}`")
            stage = None
        else:
            stage = as_string(tool.get("stage"), f"{step_id}.tool.stage", errors)
        if target and target not in target_ids:
            add_error(errors, f"{step_id}.target", f"references unknown target `{target}`")
        param_reports.extend(validate_step_params(step_id, operation, params, errors, warnings))
        status = adapter_status(operation, tool_id)
        if status == "supported":
            supported_count += 1
        elif status == "future":
            future_count += 1
            warnings.append(f"{step_id} uses recognized but unsupported validate-only-v0 operation/tool `{operation}`/`{tool_id}`")
        else:
            add_error(errors, step_id, f"unknown operation/tool pair `{operation}`/`{tool_id}`")
        if stage is not None:
            rank = stage_ranks.get(stage)
            if rank is None:
                add_error(errors, f"{step_id}.stage", f"unknown stage `{stage}`")
            else:
                if rank < last_rank:
                    warnings.append(f"{step_id} stage `{stage}` appears after a later-stage operation; review polish sequence order")
                last_rank = max(last_rank, rank)
                stage_reports.append({"step_id": step_id, "stage": stage, "rank": rank})
                if uv_seen_at is not None and stage in GEOMETRY_STAGE_NAMES:
                    warnings.append(f"{step_id} changes geometry after UV step index {uv_seen_at}; UV should remain after final geometry")
                if stage == "uv_mapping":
                    uv_seen_at = index
        step_reports.append(
            {
                "step_id": step_id,
                "step_index": index,
                "operation": operation,
                "tool_id": tool_id,
                "target": target,
                "tool_stage": stage,
                "deterministic": deterministic,
                "adapter_status": status,
            }
        )
        operation_reports.append(
            {
                "step_id": step_id,
                "operation": operation,
                "tool_id": tool_id,
                "tool_stage": stage,
                "adapter_status": status,
            }
        )
    return step_reports, operation_reports, param_reports, stage_reports, supported_count, future_count


def validate_terminology_reference(plan: dict[str, Any], warnings: list[str]) -> str | None:
    reference = plan.get("terminology_reference")
    if reference is None:
        warnings.append("terminology_reference is missing; adapter can still validate but provenance is weaker")
        return None
    if not isinstance(reference, str) or not reference:
        warnings.append("terminology_reference is present but not a non-empty string")
        return None
    path = Path(reference)
    if path.is_absolute() or ".." in path.parts:
        warnings.append(f"terminology_reference `{reference}` is not a relative repo path")
        return reference
    if not (ROOT / path).exists():
        warnings.append(f"terminology_reference `{reference}` does not exist")
    return reference


def base_report(plan: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    status = "fail" if errors else "warn" if warnings else "pass"
    return {
        "schema": REPORT_SCHEMA,
        "plan_id": plan.get("plan_id"),
        "source_recipe_id": plan.get("source_recipe_id"),
        "source_asset_id": (plan.get("source_asset") or {}).get("asset_id") if isinstance(plan.get("source_asset"), dict) else None,
        "validation_status": status,
        "supported_step_count": 0,
        "future_step_count": 0,
        "errors": errors,
        "warnings": warnings,
        "step_reports": [],
        "target_reports": [],
        "operation_reports": [],
        "param_reports": [],
        "stage_reports": [],
        "rules": {
            "validate_only": True,
            "imports_blender": False,
            "creates_meshes": False,
            "renders_media": False,
            "exports_files": False,
            "mutates_source_assets": False,
        },
    }


def validate_plan(plan: dict[str, Any], tool_map: dict[str, dict[str, Any]], stage_order: list[str]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in plan]
    if missing:
        errors.append(f"missing top-level fields: {missing}")
        return base_report(plan, errors, warnings)
    if plan.get("schema") != PLAN_SCHEMA:
        errors.append(f"schema must be {PLAN_SCHEMA}")
        return base_report(plan, errors, warnings)
    as_string(plan.get("plan_id"), "plan_id", errors)
    as_string(plan.get("source_recipe_id"), "source_recipe_id", errors)
    source_asset = as_object(plan.get("source_asset"), "source_asset", errors)
    if source_asset is not None:
        as_string(source_asset.get("asset_schema"), "source_asset.asset_schema", errors)
        as_string(source_asset.get("asset_id"), "source_asset.asset_id", errors)
    validate_dimensions(plan, errors)
    terminology_reference = validate_terminology_reference(plan, warnings)
    target_ids, target_reports, _selector_kinds = validate_targets(plan, errors, warnings)
    step_reports, operation_reports, param_reports, stage_reports, supported_count, future_count = validate_steps(
        plan,
        tool_map,
        stage_order,
        target_ids,
        errors,
        warnings,
    )
    report = base_report(plan, errors, warnings)
    report.update(
        {
            "terminology_reference": terminology_reference,
            "validation_status": "fail" if errors else "warn" if warnings else "pass",
            "supported_step_count": supported_count,
            "future_step_count": future_count,
            "step_reports": step_reports,
            "target_reports": target_reports,
            "operation_reports": operation_reports,
            "param_reports": param_reports,
            "stage_reports": stage_reports,
        }
    )
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate asset_polish_tool_plan_v0 for future Blender adapter execution.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--tool-dictionary", type=Path, default=DEFAULT_TOOL_DICTIONARY)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
    dictionary_path = args.tool_dictionary if args.tool_dictionary.is_absolute() else ROOT / args.tool_dictionary
    report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
    tool_map, stage_order = load_tool_dictionary(dictionary_path)
    report = validate_plan(load_json(plan_path), tool_map, stage_order)
    write_json(report_path, report)
    status = report["validation_status"]
    message = (
        f"{status.upper()} asset polish Blender adapter validation: "
        f"status={status} supported={report['supported_step_count']} "
        f"future={report['future_step_count']} "
        f"warnings={len(report['warnings'])} errors={len(report['errors'])}"
    )
    if status == "fail":
        print(message, file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
