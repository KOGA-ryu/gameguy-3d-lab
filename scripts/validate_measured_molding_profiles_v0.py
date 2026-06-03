#!/usr/bin/env python3
"""Validate source-only measured molding and compound-pier profiles.

This validator checks the reference/profile layer only. It does not run the
asset pump, compile tool plans, execute Blender, or write media/mesh outputs.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "profile_sources" / "measured_molding_profiles_v0.json"
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
    "measurements_are_reference_hints": True,
    "blender_tool_choices_declared": True,
    "geometry_terms_must_exist": True,
}
PROFILE_FAMILIES = {
    "side_molding_profile": "local_xz",
    "shaft_channel_cross_section": "local_xy",
    "compound_pier_cross_section": "local_xy",
}
REFERENCE_TYPES = {"user_supplied_image"}
UNITS = {"cm", "normalized"}


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


def finite_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0.0


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


def load_tool_ids() -> set[str]:
    dictionary = load_json(TOOL_DICTIONARY)
    tools = require_list(dictionary.get("tools"), "tool_dictionary.tools")
    ids = set()
    for index, tool in enumerate(tools):
        item = require_object(tool, f"tool_dictionary.tools[{index}]")
        ids.add(require_string(item.get("tool_id"), f"tool_dictionary.tools[{index}].tool_id"))
    if dictionary.get("tool_count") != len(ids):
        fail("tool_dictionary.tool_count must match unique tools")
    return ids


def validate_positive_measurements(value: Any, field: str) -> int:
    if isinstance(value, dict):
        if not value:
            fail(f"{field} must not be empty")
        count = 0
        for key, child in value.items():
            require_string(key, f"{field}.key")
            count += validate_positive_measurements(child, f"{field}.{key}")
        return count
    if isinstance(value, list):
        if not value:
            fail(f"{field} must not be empty")
        return sum(validate_positive_measurements(child, f"{field}[{index}]") for index, child in enumerate(value))
    if not finite_positive_number(value):
        fail(f"{field} must be a positive finite number")
    return 1


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


def validate_candidate_tools(values: Any, field: str, known_tools: set[str]) -> list[str]:
    items = require_list(values, field)
    if not items:
        fail(f"{field} must not be empty")
    used_tools = []
    for index, value in enumerate(items):
        item = require_object(value, f"{field}[{index}]")
        tool_id = require_string(item.get("tool_id"), f"{field}[{index}].tool_id")
        if tool_id not in known_tools:
            fail(f"{field}[{index}].tool_id references unknown Blender tool: {tool_id}")
        require_string(item.get("v0_use"), f"{field}[{index}].v0_use")
        require_string(item.get("use"), f"{field}[{index}].use")
        used_tools.append(tool_id)
    return used_tools


def validate_profile(
    value: Any,
    index: int,
    reference_ids: set[str],
    terms: dict[str, dict[str, Any]],
    known_tools: set[str],
) -> tuple[str, str, int, list[str]]:
    profile = require_object(value, f"profiles[{index}]")
    profile_id = require_string(profile.get("profile_id"), f"profiles[{index}].profile_id")
    family = require_string(profile.get("profile_family"), f"{profile_id}.profile_family")
    if family not in PROFILE_FAMILIES:
        fail(f"{profile_id}.profile_family unsupported: {family}")
    source_reference_id = require_string(profile.get("source_reference_id"), f"{profile_id}.source_reference_id")
    if source_reference_id not in reference_ids:
        fail(f"{profile_id}.source_reference_id references unknown reference: {source_reference_id}")
    coordinate_space = require_string(profile.get("coordinate_space"), f"{profile_id}.coordinate_space")
    expected_space = PROFILE_FAMILIES[family]
    if coordinate_space != expected_space:
        fail(f"{profile_id}.coordinate_space must be {expected_space} for {family}")
    units = require_string(profile.get("units"), f"{profile_id}.units")
    if units not in UNITS:
        fail(f"{profile_id}.units unsupported: {units}")
    measurement_count = validate_positive_measurements(profile.get("source_measurements_cm"), f"{profile_id}.source_measurements_cm")
    shape_controls = require_object(profile.get("shape_controls"), f"{profile_id}.shape_controls")
    for key in ("dominant_silhouette", "intended_profile_points", "curve_handling"):
        require_string(shape_controls.get(key), f"{profile_id}.shape_controls.{key}")
    validate_term_list(profile.get("geometry_terms_used"), f"{profile_id}.geometry_terms_used", terms)
    validate_term_list(profile.get("profile_terms"), f"{profile_id}.profile_terms", terms, {"profile_primitive"})
    validate_term_list(profile.get("operations"), f"{profile_id}.operations", terms, {"mesh_operation", "composition_operation"})
    used_tools = validate_candidate_tools(profile.get("candidate_blender_tools"), f"{profile_id}.candidate_blender_tools", known_tools)
    require_string_list(profile.get("implementation_notes"), f"{profile_id}.implementation_notes")
    if profile.get("no_claims") != FALSE_CLAIMS:
        fail(f"{profile_id}.no_claims must match required false claim flags")
    return profile_id, family, measurement_count, used_tools


def validate_bundle(path: Path) -> dict[str, Any]:
    bundle = load_json(path)
    if bundle.get("schema") != "asset_mill_measured_molding_profile_bundle_v0":
        fail("bundle schema must be asset_mill_measured_molding_profile_bundle_v0")
    if bundle.get("bundle_id") != "measured_molding_profiles_v0":
        fail("bundle_id must be measured_molding_profiles_v0")
    if bundle.get("status") != "source_profile_only":
        fail("status must be source_profile_only")
    if bundle.get("rules") != REQUIRED_RULES:
        fail("rules must match measured molding source-profile boundaries")
    if bundle.get("no_claims") != FALSE_CLAIMS:
        fail("bundle no_claims must match required false claim flags")
    reference_ids = validate_references(bundle)
    terms = load_geometry_terms()
    known_tools = load_tool_ids()
    profiles = require_list(bundle.get("profiles"), "profiles")
    if bundle.get("profile_count") != len(profiles):
        fail("profile_count must match profiles length")
    seen_profiles: set[str] = set()
    family_counts: dict[str, int] = {family: 0 for family in PROFILE_FAMILIES}
    measurement_count = 0
    used_tools: set[str] = set()
    for index, profile in enumerate(profiles):
        profile_id, family, profile_measurement_count, profile_tools = validate_profile(profile, index, reference_ids, terms, known_tools)
        if profile_id in seen_profiles:
            fail(f"duplicate profile_id: {profile_id}")
        seen_profiles.add(profile_id)
        family_counts[family] += 1
        measurement_count += profile_measurement_count
        used_tools.update(profile_tools)
    return {
        "schema": "measured_molding_profile_validation_result_v0",
        "status": "pass",
        "bundle_path": display_path(path),
        "reference_count": len(reference_ids),
        "profile_count": len(profiles),
        "profile_family_counts": family_counts,
        "measurement_count": measurement_count,
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
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate measured molding profile sources.")
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
        "PASS measured molding profile validation: "
        f"profiles={result['profile_count']} references={result['reference_count']} "
        f"tools={result['candidate_tool_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
