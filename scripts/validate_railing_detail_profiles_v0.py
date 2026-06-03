#!/usr/bin/env python3
"""Validate source-only 2D railing detail profiles.

The bundle validated here says which 2D shapes belong on railing/post/panel
regions and which Blender tools may execute them later. It does not compile
tool plans, run Blender, or write generated assets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "profile_sources" / "railing_detail_profiles_v0.json"
GEOMETRY_ROOT = ROOT / "geometry_dictionary"
TOOL_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
    "building_code_compliance": False,
}
REQUIRED_RULES = {
    "source_profile_only": True,
    "no_blender_execution": True,
    "no_generated_outputs": True,
    "shape_placement_required": True,
    "blender_tool_sequence_declared": True,
    "geometry_terms_must_exist": True,
    "details_compile_before_adapter": True,
}
PROFILE_FAMILIES = {
    "frame_profile",
    "panel_cutout_profile",
    "face_recess_profile",
    "repeating_trim_profile",
    "side_molding_profile",
    "transition_profile",
    "post_cross_section_profile",
}
REFERENCE_TYPES = {"user_supplied_image"}
COORDINATE_SPACES = {"local_xy", "local_xz"}
TARGET_ASSET_FAMILIES = {
    "banister_post",
    "column",
    "door_frame",
    "fence_post",
    "guard_panel",
    "rail_segment",
    "window_frame",
}
ALLOWED_OPERATION_CATEGORIES = {"mesh_operation", "composition_operation", "transform"}


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


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def load_geometry_terms() -> dict[str, dict[str, Any]]:
    terms: dict[str, dict[str, Any]] = {}
    for path in sorted(GEOMETRY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = term.get("term_id")
        if not isinstance(term_id, str) or not term_id:
            fail(f"{display_path(path)} missing term_id")
        terms[term_id] = term
    return terms


def load_tool_dictionary() -> tuple[dict[str, dict[str, Any]], list[str]]:
    dictionary = load_json(TOOL_DICTIONARY)
    stages = require_string_list(dictionary.get("stages"), "tool_dictionary.stages")
    tools = require_list(dictionary.get("tools"), "tool_dictionary.tools")
    by_id: dict[str, dict[str, Any]] = {}
    for index, tool in enumerate(tools):
        item = require_object(tool, f"tool_dictionary.tools[{index}]")
        tool_id = require_string(item.get("tool_id"), f"tool_dictionary.tools[{index}].tool_id")
        if tool_id in by_id:
            fail(f"duplicate Blender tool_id: {tool_id}")
        stage = require_string(item.get("stage"), f"tool_dictionary.tools[{index}].stage")
        if stage not in stages:
            fail(f"{tool_id}.stage references unknown stage: {stage}")
        by_id[tool_id] = item
    if dictionary.get("tool_count") != len(by_id):
        fail("tool_dictionary.tool_count must match unique tools")
    return by_id, stages


def validate_references(bundle: dict[str, Any]) -> set[str]:
    references = require_list(bundle.get("references"), "references")
    if not references:
        fail("references must not be empty")
    seen: set[str] = set()
    for index, reference in enumerate(references):
        item = require_object(reference, f"references[{index}]")
        reference_id = require_string(item.get("reference_id"), f"references[{index}].reference_id")
        if reference_id in seen:
            fail(f"duplicate reference_id: {reference_id}")
        seen.add(reference_id)
        source_type = require_string(item.get("source_type"), f"{reference_id}.source_type")
        if source_type not in REFERENCE_TYPES:
            fail(f"{reference_id}.source_type unsupported: {source_type}")
        require_string(item.get("observed_subject"), f"{reference_id}.observed_subject")
        require_string(item.get("access_date"), f"{reference_id}.access_date")
        if require_string(item.get("use_policy"), f"{reference_id}.use_policy") != "morphology_reference_only":
            fail(f"{reference_id}.use_policy must be morphology_reference_only")
    return seen


def validate_term_list(values: Any, field: str, terms: dict[str, dict[str, Any]], allowed_categories: set[str] | None = None) -> list[str]:
    items = require_string_list(values, field)
    unknown = sorted(set(items) - set(terms))
    if unknown:
        fail(f"{field} references unknown geometry terms: {unknown}")
    if allowed_categories is not None:
        wrong = sorted(term_id for term_id in items if terms[term_id].get("category") not in allowed_categories)
        if wrong:
            fail(f"{field} references terms from unsupported categories: {wrong}")
    return items


def validate_where_used(values: Any, field: str) -> int:
    placements = require_list(values, field)
    if not placements:
        fail(f"{field} must not be empty")
    for index, value in enumerate(placements):
        item = require_object(value, f"{field}[{index}]")
        family = require_string(item.get("target_asset_family"), f"{field}[{index}].target_asset_family")
        if family not in TARGET_ASSET_FAMILIES:
            fail(f"{field}[{index}].target_asset_family unsupported: {family}")
        require_string(item.get("placement_region"), f"{field}[{index}].placement_region")
        require_string(item.get("detail_role"), f"{field}[{index}].detail_role")
        require_string(item.get("application_method"), f"{field}[{index}].application_method")
    return len(placements)


def validate_tool_sequence(values: Any, field: str, tools: dict[str, dict[str, Any]]) -> list[str]:
    steps = require_list(values, field)
    if not steps:
        fail(f"{field} must not be empty")
    tool_ids: list[str] = []
    for index, value in enumerate(steps):
        item = require_object(value, f"{field}[{index}]")
        stage = require_string(item.get("stage"), f"{field}[{index}].stage")
        tool_id = require_string(item.get("tool_id"), f"{field}[{index}].tool_id")
        if tool_id not in tools:
            fail(f"{field}[{index}].tool_id references unknown Blender tool: {tool_id}")
        actual_stage = tools[tool_id]["stage"]
        if actual_stage != stage:
            fail(f"{field}[{index}] stage must match tool dictionary: {tool_id} is {actual_stage}, not {stage}")
        require_string(item.get("use"), f"{field}[{index}].use")
        tool_ids.append(tool_id)
    return tool_ids


def validate_profile(value: Any, index: int, reference_ids: set[str], terms: dict[str, dict[str, Any]], tools: dict[str, dict[str, Any]]) -> tuple[str, str, int, list[str]]:
    profile = require_object(value, f"profiles[{index}]")
    profile_id = require_string(profile.get("profile_id"), f"profiles[{index}].profile_id")
    family = require_string(profile.get("profile_family"), f"{profile_id}.profile_family")
    if family not in PROFILE_FAMILIES:
        fail(f"{profile_id}.profile_family unsupported: {family}")
    source_reference_id = require_string(profile.get("source_reference_id"), f"{profile_id}.source_reference_id")
    if source_reference_id not in reference_ids:
        fail(f"{profile_id}.source_reference_id references unknown reference: {source_reference_id}")
    shape = require_object(profile.get("source_2d_shape"), f"{profile_id}.source_2d_shape")
    shape_term = require_string(shape.get("term_id"), f"{profile_id}.source_2d_shape.term_id")
    if shape_term not in terms:
        fail(f"{profile_id}.source_2d_shape.term_id references unknown geometry term: {shape_term}")
    if terms[shape_term].get("category") != "profile_primitive":
        fail(f"{profile_id}.source_2d_shape.term_id must be a profile primitive")
    coordinate_space = require_string(shape.get("coordinate_space"), f"{profile_id}.source_2d_shape.coordinate_space")
    if coordinate_space not in COORDINATE_SPACES:
        fail(f"{profile_id}.source_2d_shape.coordinate_space unsupported: {coordinate_space}")
    require_string(shape.get("control_policy"), f"{profile_id}.source_2d_shape.control_policy")
    placement_count = validate_where_used(profile.get("where_used"), f"{profile_id}.where_used")
    validate_term_list(profile.get("geometry_terms_used"), f"{profile_id}.geometry_terms_used", terms)
    validate_term_list(profile.get("profile_terms"), f"{profile_id}.profile_terms", terms, {"profile_primitive"})
    if shape_term not in profile["profile_terms"]:
        fail(f"{profile_id}.profile_terms must include source_2d_shape.term_id")
    validate_term_list(profile.get("operations"), f"{profile_id}.operations", terms, ALLOWED_OPERATION_CATEGORIES)
    tool_ids = validate_tool_sequence(profile.get("blender_tool_sequence"), f"{profile_id}.blender_tool_sequence", tools)
    controls = require_object(profile.get("shape_controls"), f"{profile_id}.shape_controls")
    require_string(controls.get("dominant_silhouette"), f"{profile_id}.shape_controls.dominant_silhouette")
    require_string(controls.get("detail_density"), f"{profile_id}.shape_controls.detail_density")
    require_string_list(controls.get("edit_knobs"), f"{profile_id}.shape_controls.edit_knobs")
    if profile.get("no_claims") != FALSE_CLAIMS:
        fail(f"{profile_id}.no_claims must match required false claim flags")
    return profile_id, family, placement_count, tool_ids


def validate_railing_sequence(
    value: Any,
    profile_ids: set[str],
    tools: dict[str, dict[str, Any]],
    stage_order: list[str],
) -> tuple[int, set[str]]:
    sequence = require_list(value, "railing_detail_sequence")
    if not sequence:
        fail("railing_detail_sequence must not be empty")
    stage_indexes = {stage: index for index, stage in enumerate(stage_order)}
    previous_stage_index = -1
    covered_profiles: set[str] = set()
    seen_sequence_ids: set[str] = set()
    for index, value in enumerate(sequence):
        item = require_object(value, f"railing_detail_sequence[{index}]")
        sequence_id = require_string(item.get("sequence_id"), f"railing_detail_sequence[{index}].sequence_id")
        if sequence_id in seen_sequence_ids:
            fail(f"duplicate railing_detail_sequence sequence_id: {sequence_id}")
        seen_sequence_ids.add(sequence_id)
        stage = require_string(item.get("stage"), f"{sequence_id}.stage")
        if stage not in stage_indexes:
            fail(f"{sequence_id}.stage references unknown stage: {stage}")
        if stage_indexes[stage] < previous_stage_index:
            fail(f"{sequence_id}.stage is out of canonical stage order")
        previous_stage_index = stage_indexes[stage]
        sequence_profile_ids = require_string_list(item.get("profile_ids"), f"{sequence_id}.profile_ids")
        missing_profiles = sorted(set(sequence_profile_ids) - profile_ids)
        if missing_profiles:
            fail(f"{sequence_id}.profile_ids references unknown profiles: {missing_profiles}")
        covered_profiles.update(sequence_profile_ids)
        tool_ids = require_string_list(item.get("tool_ids"), f"{sequence_id}.tool_ids")
        for tool_id in tool_ids:
            if tool_id not in tools:
                fail(f"{sequence_id}.tool_ids references unknown Blender tool: {tool_id}")
            actual_stage = tools[tool_id]["stage"]
            if actual_stage != stage:
                fail(f"{sequence_id}.tool_ids stage mismatch: {tool_id} is {actual_stage}, not {stage}")
        require_string(item.get("purpose"), f"{sequence_id}.purpose")
    missing_coverage = sorted(profile_ids - covered_profiles)
    if missing_coverage:
        fail(f"railing_detail_sequence does not cover profiles: {missing_coverage}")
    return len(sequence), covered_profiles


def validate_bundle(path: Path) -> dict[str, Any]:
    bundle = load_json(path)
    if bundle.get("schema") != "asset_mill_railing_detail_profile_bundle_v0":
        fail("bundle schema must be asset_mill_railing_detail_profile_bundle_v0")
    if bundle.get("bundle_id") != "railing_detail_profiles_v0":
        fail("bundle_id must be railing_detail_profiles_v0")
    if bundle.get("status") != "source_profile_only":
        fail("status must be source_profile_only")
    if bundle.get("rules") != REQUIRED_RULES:
        fail("rules must match railing detail source-profile boundaries")
    if bundle.get("no_claims") != FALSE_CLAIMS:
        fail("bundle no_claims must match required false claim flags")
    reference_ids = validate_references(bundle)
    terms = load_geometry_terms()
    tools, stage_order = load_tool_dictionary()
    profiles = require_list(bundle.get("profiles"), "profiles")
    if bundle.get("profile_count") != len(profiles):
        fail("profile_count must match profiles length")
    profile_ids: set[str] = set()
    family_counts = {family: 0 for family in PROFILE_FAMILIES}
    placement_count = 0
    used_tools: set[str] = set()
    for index, profile in enumerate(profiles):
        profile_id, family, profile_placement_count, tool_ids = validate_profile(profile, index, reference_ids, terms, tools)
        if profile_id in profile_ids:
            fail(f"duplicate profile_id: {profile_id}")
        profile_ids.add(profile_id)
        family_counts[family] += 1
        placement_count += profile_placement_count
        used_tools.update(tool_ids)
    sequence_count, covered_profiles = validate_railing_sequence(bundle.get("railing_detail_sequence"), profile_ids, tools, stage_order)
    require_string_list(bundle.get("missing_steps_made_explicit"), "missing_steps_made_explicit")
    return {
        "schema": "railing_detail_profile_validation_result_v0",
        "status": "pass",
        "bundle_path": display_path(path),
        "reference_count": len(reference_ids),
        "profile_count": len(profiles),
        "profile_family_counts": {family: count for family, count in sorted(family_counts.items())},
        "placement_count": placement_count,
        "sequence_count": sequence_count,
        "sequence_covered_profile_count": len(covered_profiles),
        "candidate_tool_count": len(used_tools),
        "generated_outputs_created": False,
        "rules": {
            "source_profile_only": True,
            "runs_asset_pump": False,
            "runs_tool_plan_compiler": False,
            "runs_blender": False,
            "imports_blender": False,
            "geometry_terms_checked": True,
            "candidate_blender_tools_checked": True,
            "placement_regions_checked": True,
            "stage_order_checked": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate railing 2D detail profile sources.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--json-report", type=Path, help="Optional path for validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    result = validate_bundle(bundle_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS railing detail profile validation: "
        f"profiles={result['profile_count']} placements={result['placement_count']} "
        f"sequence={result['sequence_count']} tools={result['candidate_tool_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
