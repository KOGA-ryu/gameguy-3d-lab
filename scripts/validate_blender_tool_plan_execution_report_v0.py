#!/usr/bin/env python3
"""Validate Blender execution reports for compiled gameguy_tool_plan_v0 plans.

This validates the adapter's report after Blender has run. It does not import
Blender, run the tool-plan compiler, read source recipes, or create mesh/media
artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = Path("/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json")
REPORT_SCHEMA = "blender_tool_plan_execution_report_v0"
PLAN_SCHEMA = "gameguy_tool_plan_v0"
REQUIRED_RULES: dict[str, bool] = {
    "consumes_gameguy_tool_plan_v0": True,
    "reads_source_intent_recipe": False,
    "runs_tool_plan_compiler": False,
    "imports_asset_pump": False,
    "executes_only_supported_deterministic_steps": True,
    "source_design_logic": False,
}
REQUIRED_COMMON_QUALITY_FLAGS = {
    "material_regions_preserved",
    "topology_cleanup_attempted",
}
REQUIRED_BANISTER_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "explicit_socket_boolean_targets",
    "socket_cutters_removed",
}
REQUIRED_FENCE_POST_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "explicit_socket_boolean_targets",
    "socket_cutters_removed",
}
REQUIRED_COLUMN_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "socket_boolean_not_required",
}
REQUIRED_RAIL_SEGMENT_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "socket_boolean_not_required",
}
REQUIRED_WINDOW_FRAME_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "socket_boolean_not_required",
}
REQUIRED_DOOR_FRAME_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "socket_boolean_not_required",
}
REQUIRED_GUARD_PANEL_QUALITY_FLAGS = REQUIRED_COMMON_QUALITY_FLAGS | {
    "socket_boolean_not_required",
}
REQUIRED_BANISTER_MATERIAL_ROLES = ("base", "cap", "shaft", "rib", "socket_shadow")
REQUIRED_FENCE_POST_MATERIAL_ROLES = ("base", "cap", "shaft", "rib", "socket_shadow")
REQUIRED_COLUMN_MATERIAL_ROLES = ("base", "cap", "transition", "shaft", "rib")
REQUIRED_RAIL_SEGMENT_MATERIAL_ROLES = ("body", "base", "cap", "connector", "rib")
REQUIRED_WINDOW_FRAME_MATERIAL_ROLES = ("frame",)
REQUIRED_DOOR_FRAME_MATERIAL_ROLES = ("frame",)
REQUIRED_GUARD_PANEL_MATERIAL_ROLES = ("pier", "base", "cap", "panel", "coping", "trim", "recess", "finial", "collar")
REQUIRED_SOCKET_CUTTERS = ("east_socket_cutter", "west_socket_cutter")


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


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{field} must be a boolean")
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
    items = require_list(value, field)
    result = []
    for index, item in enumerate(items):
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
    for field in ("blend_path", "render_path", "export_path"):
        value = report.get(field)
        if value is None:
            continue
        path_text = require_string(value, field)
        if is_under_root(path_text, ROOT):
            fail(f"{field} must not point inside the repo")


def validate_rules(report: dict[str, Any]) -> None:
    rules = require_object(report.get("rules"), "rules")
    for key, expected in REQUIRED_RULES.items():
        if rules.get(key) is not expected:
            fail(f"rules.{key} must be {str(expected).lower()}")


def validate_execution_counts(report: dict[str, Any]) -> None:
    step_count = require_int(report.get("step_count"), "step_count", minimum=1)
    supported_step_count = require_int(report.get("supported_step_count"), "supported_step_count", minimum=1)
    executed_step_count = require_int(report.get("executed_step_count"), "executed_step_count", minimum=1)
    skipped_step_count = require_int(report.get("skipped_step_count"), "skipped_step_count")
    unique_tool_count = require_int(report.get("unique_tool_count"), "unique_tool_count", minimum=1)
    unique_tools = require_string_list(report.get("unique_tools"), "unique_tools")
    if supported_step_count != step_count:
        fail("supported_step_count must match step_count")
    if executed_step_count != step_count:
        fail("executed_step_count must match step_count")
    if skipped_step_count != 0:
        fail("skipped_step_count must be 0 for an execution quality report")
    if unique_tool_count != len(set(unique_tools)):
        fail("unique_tool_count must match unique_tools")


def validate_quality_flags(report: dict[str, Any], asset_family: str) -> None:
    quality_pass = require_object(report.get("quality_pass"), "quality_pass")
    if quality_pass.get("asset_family_quality_profile") != asset_family:
        fail("quality_pass.asset_family_quality_profile must match asset_family")
    if asset_family == "banister_post":
        required_flags = REQUIRED_BANISTER_QUALITY_FLAGS
    elif asset_family == "fence_post":
        required_flags = REQUIRED_FENCE_POST_QUALITY_FLAGS
    elif asset_family == "column":
        required_flags = REQUIRED_COLUMN_QUALITY_FLAGS
    elif asset_family == "rail_segment":
        required_flags = REQUIRED_RAIL_SEGMENT_QUALITY_FLAGS
    elif asset_family == "window_frame":
        required_flags = REQUIRED_WINDOW_FRAME_QUALITY_FLAGS
    elif asset_family == "door_frame":
        required_flags = REQUIRED_DOOR_FRAME_QUALITY_FLAGS
    elif asset_family == "guard_panel":
        required_flags = REQUIRED_GUARD_PANEL_QUALITY_FLAGS
    else:
        fail(f"unsupported asset_family quality profile `{asset_family}`")
    for key in sorted(required_flags):
        if quality_pass.get(key) is not True:
            fail(f"quality_pass.{key} must be true")


def validate_material_regions(report: dict[str, Any], min_material_roles: int, required_roles: tuple[str, ...]) -> dict[str, int]:
    regions = require_object(report.get("material_regions"), "material_regions")
    material_slot_count = require_int(regions.get("material_slot_count"), "material_regions.material_slot_count", minimum=min_material_roles)
    face_counts_raw = require_object(regions.get("face_counts_by_role"), "material_regions.face_counts_by_role")
    face_counts: dict[str, int] = {}
    for role, value in face_counts_raw.items():
        if not isinstance(role, str) or not role:
            fail("material region roles must be non-empty strings")
        face_counts[role] = require_int(value, f"material_regions.face_counts_by_role.{role}", minimum=1)
    for role in required_roles:
        if role not in face_counts:
            fail(f"material_regions.face_counts_by_role must include `{role}`")
    if len(face_counts_raw) < min_material_roles:
        fail(f"material_regions.face_counts_by_role must contain at least {min_material_roles} roles")
    final_object = require_object(report.get("final_object"), "final_object")
    final_slot_count = require_int(final_object.get("material_slot_count"), "final_object.material_slot_count", minimum=min_material_roles)
    if final_slot_count != material_slot_count:
        fail("final_object.material_slot_count must match material_regions.material_slot_count")
    return face_counts


def validate_socket_pass(report: dict[str, Any], min_socket_panels: int) -> None:
    socket_pass = require_object(report.get("socket_pass"), "socket_pass")
    if socket_pass.get("operation") != "DIFFERENCE":
        fail("socket_pass.operation must be DIFFERENCE")
    if socket_pass.get("solver_requested") != "EXACT":
        fail("socket_pass.solver_requested must be EXACT")
    target_names = require_string_list(socket_pass.get("target_names"), "socket_pass.target_names")
    if target_names != ["post_core"]:
        fail("socket_pass.target_names must be [`post_core`]")
    cutter_names = require_string_list(socket_pass.get("cutter_names"), "socket_pass.cutter_names")
    for cutter in REQUIRED_SOCKET_CUTTERS:
        if cutter not in cutter_names:
            fail(f"socket_pass.cutter_names must include `{cutter}`")
    applied_count = require_int(socket_pass.get("applied_modifier_count"), "socket_pass.applied_modifier_count", minimum=len(REQUIRED_SOCKET_CUTTERS))
    if applied_count != len(cutter_names):
        fail("socket_pass.applied_modifier_count must match socket_pass.cutter_names length")
    failed_count = require_int(socket_pass.get("failed_modifier_count"), "socket_pass.failed_modifier_count")
    if failed_count != 0:
        fail("socket_pass.failed_modifier_count must be 0")
    panel_count = require_int(socket_pass.get("socket_shadow_panel_count"), "socket_pass.socket_shadow_panel_count", minimum=min_socket_panels)
    if panel_count < len(REQUIRED_SOCKET_CUTTERS):
        fail("socket_pass.socket_shadow_panel_count must cover both socket cutters")
    if require_bool(socket_pass.get("cutter_objects_removed"), "socket_pass.cutter_objects_removed") is not True:
        fail("socket_pass.cutter_objects_removed must be true")
    removed = require_string_list(socket_pass.get("removed_cutter_names"), "socket_pass.removed_cutter_names")
    for cutter in REQUIRED_SOCKET_CUTTERS:
        if cutter not in removed:
            fail(f"socket_pass.removed_cutter_names must include `{cutter}`")


def validate_socket_not_required(report: dict[str, Any]) -> None:
    socket_pass = require_object(report.get("socket_pass", {}), "socket_pass")
    if socket_pass:
        fail("socket_pass must be empty when socket booleans are not required")


def validate_topology(report: dict[str, Any], max_non_manifold_edges: int) -> None:
    validation = require_object(report.get("validation"), "validation")
    before = require_int(validation.get("non_manifold_edge_count_before_cleanup"), "validation.non_manifold_edge_count_before_cleanup")
    after = require_int(validation.get("non_manifold_edge_count"), "validation.non_manifold_edge_count")
    if before > max_non_manifold_edges:
        fail(f"validation.non_manifold_edge_count_before_cleanup must be <= {max_non_manifold_edges}")
    if after > max_non_manifold_edges:
        fail(f"validation.non_manifold_edge_count must be <= {max_non_manifold_edges}")
    cleanup = require_object(report.get("topology_cleanup"), "topology_cleanup")
    if cleanup.get("attempted") is not True:
        fail("topology_cleanup.attempted must be true")
    cleanup_before = require_int(cleanup.get("non_manifold_edge_count_before"), "topology_cleanup.non_manifold_edge_count_before")
    cleanup_after = require_int(cleanup.get("non_manifold_edge_count_after"), "topology_cleanup.non_manifold_edge_count_after")
    if cleanup_before != before or cleanup_after != after:
        fail("topology_cleanup non-manifold counts must match validation counts")


def validate_final_object(report: dict[str, Any]) -> None:
    final_object = require_object(report.get("final_object"), "final_object")
    require_string(final_object.get("name"), "final_object.name")
    require_int(final_object.get("vertex_count"), "final_object.vertex_count", minimum=3)
    require_int(final_object.get("edge_count"), "final_object.edge_count", minimum=3)
    require_int(final_object.get("face_count"), "final_object.face_count", minimum=1)


def validate_report(report_path: Path, *, max_non_manifold_edges: int, min_material_roles: int, min_socket_panels: int) -> dict[str, Any]:
    report = load_json(report_path)
    if report.get("schema") != REPORT_SCHEMA:
        fail(f"{report_path} schema must be {REPORT_SCHEMA}")
    if report.get("plan_schema") != PLAN_SCHEMA:
        fail(f"{report_path} plan_schema must be {PLAN_SCHEMA}")
    if report.get("adapter") != "scripts/execute_blender_tool_plan_v0.py":
        fail("adapter must be scripts/execute_blender_tool_plan_v0.py")
    if report.get("generated_outputs_created") is not True:
        fail("generated_outputs_created must be true for a Blender execution report")
    if report.get("render_requested") is not True:
        fail("render_requested must be true for a quality execution report")
    if report.get("export_requested") is not True:
        fail("export_requested must be true for a quality execution report")
    asset_family = require_string(report.get("asset_family"), "asset_family")
    validate_rules(report)
    validate_execution_counts(report)
    validate_quality_flags(report, asset_family)
    if asset_family == "banister_post":
        face_counts = validate_material_regions(report, min_material_roles, REQUIRED_BANISTER_MATERIAL_ROLES)
        validate_socket_pass(report, min_socket_panels)
        socket_shadow_panel_count = report["socket_pass"]["socket_shadow_panel_count"]
    elif asset_family == "fence_post":
        face_counts = validate_material_regions(report, min_material_roles, REQUIRED_FENCE_POST_MATERIAL_ROLES)
        validate_socket_pass(report, min_socket_panels)
        socket_shadow_panel_count = report["socket_pass"]["socket_shadow_panel_count"]
    elif asset_family == "column":
        face_counts = validate_material_regions(report, len(REQUIRED_COLUMN_MATERIAL_ROLES), REQUIRED_COLUMN_MATERIAL_ROLES)
        validate_socket_not_required(report)
        socket_shadow_panel_count = 0
    elif asset_family == "rail_segment":
        face_counts = validate_material_regions(report, len(REQUIRED_RAIL_SEGMENT_MATERIAL_ROLES), REQUIRED_RAIL_SEGMENT_MATERIAL_ROLES)
        validate_socket_not_required(report)
        socket_shadow_panel_count = 0
    elif asset_family == "window_frame":
        face_counts = validate_material_regions(report, len(REQUIRED_WINDOW_FRAME_MATERIAL_ROLES), REQUIRED_WINDOW_FRAME_MATERIAL_ROLES)
        validate_socket_not_required(report)
        socket_shadow_panel_count = 0
    elif asset_family == "door_frame":
        face_counts = validate_material_regions(report, len(REQUIRED_DOOR_FRAME_MATERIAL_ROLES), REQUIRED_DOOR_FRAME_MATERIAL_ROLES)
        validate_socket_not_required(report)
        socket_shadow_panel_count = 0
    elif asset_family == "guard_panel":
        face_counts = validate_material_regions(report, len(REQUIRED_GUARD_PANEL_MATERIAL_ROLES), REQUIRED_GUARD_PANEL_MATERIAL_ROLES)
        validate_socket_not_required(report)
        socket_shadow_panel_count = 0
    else:
        fail(f"unsupported asset_family quality profile `{asset_family}`")
    validate_topology(report, max_non_manifold_edges)
    validate_final_object(report)
    validate_no_repo_generated_outputs(report)
    return {
        "schema": "blender_tool_plan_execution_quality_validation_v0",
        "report": str(report_path),
        "plan_id": report.get("plan_id"),
        "asset_id": report.get("asset_id"),
        "step_count": report.get("step_count"),
        "unique_tool_count": report.get("unique_tool_count"),
        "non_manifold_edge_count": report["validation"]["non_manifold_edge_count"],
        "material_role_count": len(face_counts),
        "socket_shadow_panel_count": socket_shadow_panel_count,
        "generated_outputs_in_repo": False,
        "rules": {
            "reads_source_intent_recipe": False,
            "runs_tool_plan_compiler": False,
            "imports_blender": False,
            "creates_media_or_mesh": False,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Blender tool-plan execution report.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    parser.add_argument("--max-non-manifold-edges", type=int, default=0)
    parser.add_argument("--min-material-roles", type=int, default=5)
    parser.add_argument("--min-socket-panels", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    result = validate_report(
        report_path,
        max_non_manifold_edges=args.max_non_manifold_edges,
        min_material_roles=args.min_material_roles,
        min_socket_panels=args.min_socket_panels,
    )
    if args.json_report:
        output_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS Blender tool-plan execution quality validation: "
        f"steps={result['step_count']} non_manifold={result['non_manifold_edge_count']} "
        f"material_roles={result['material_role_count']} socket_panels={result['socket_shadow_panel_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
