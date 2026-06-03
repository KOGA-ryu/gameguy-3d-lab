#!/usr/bin/env python3
"""Validate the canonical deterministic asset generation registry.

This is a source-boundary validator. It does not run the asset pump, compile
tool plans, execute Blender, or write generated mesh/media outputs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "architecture" / "asset_mill" / "asset_generation_registry_v0.json"
PIPELINE_SCRIPT = ROOT / "scripts" / "validate_generation_pipeline_v0.py"
REGISTRY_SCHEMA = "asset_generation_registry_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def repo_path(value: Any, field: str) -> Path:
    text = require_string(value, field)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        fail(f"{field} must be a relative repo path")
    return ROOT / path


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


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    result = []
    for index, item in enumerate(items):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def load_pipeline_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_generation_pipeline_v0", PIPELINE_SCRIPT)
    if spec is None or spec.loader is None:
        fail(f"could not import {display_path(PIPELINE_SCRIPT)}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pipeline_labels() -> set[str]:
    module = load_pipeline_module()
    steps = module.build_command_steps(include_blender=True, skip_unit_tests=False, blender_path=module.DEFAULT_BLENDER)
    return {step.label for step in steps}


def script_path(value: Any, field: str) -> Path:
    path = repo_path(value, field)
    if path.suffix != ".py":
        fail(f"{field} must reference a Python script")
    if not path.exists():
        fail(f"{field} references missing script: {display_path(path)}")
    return path


def assert_no_blender_import(path: Path, field: str) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("import bpy") or stripped.startswith("from bpy"):
            fail(f"{field} must not import Blender: {display_path(path)}")


def validate_asset_count(bundle: dict[str, Any], expected: int, field: str) -> None:
    assets = require_list(bundle.get("assets"), f"{field}.assets")
    if len(assets) != expected:
        fail(f"{field}.expected_asset_count must match assets length")
    if "asset_count" in bundle and bundle["asset_count"] != expected:
        fail(f"{field}.expected_asset_count must match bundle asset_count")


def validate_pipeline_labels(labels: Any, known_labels: set[str], field: str) -> list[str]:
    values = require_string_list(labels, field)
    missing = [label for label in values if label not in known_labels]
    if missing:
        fail(f"{field} references unknown pipeline labels: {missing}")
    return values


def validate_geometry_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"canonical_geometry_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"canonical_geometry_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"canonical_geometry_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"canonical_geometry_bundles[{index}].bundle_id")
    if "bundle_id" in bundle and bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(bundle_ref.get("expected_asset_count"), f"canonical_geometry_bundles[{index}].expected_asset_count", minimum=1)
    validate_asset_count(bundle, expected_count, f"canonical_geometry_bundles[{index}]")
    compiler = script_path(bundle_ref.get("compiler"), f"canonical_geometry_bundles[{index}].compiler")
    validator = script_path(bundle_ref.get("validator"), f"canonical_geometry_bundles[{index}].validator")
    assert_no_blender_import(compiler, f"canonical_geometry_bundles[{index}].compiler")
    assert_no_blender_import(validator, f"canonical_geometry_bundles[{index}].validator")
    if "source_validator" in bundle_ref:
        source_validator = script_path(bundle_ref.get("source_validator"), f"canonical_geometry_bundles[{index}].source_validator")
        assert_no_blender_import(source_validator, f"canonical_geometry_bundles[{index}].source_validator")
    if "adapter_validate_only" in bundle_ref:
        script_path(bundle_ref.get("adapter_validate_only"), f"canonical_geometry_bundles[{index}].adapter_validate_only")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"canonical_geometry_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "asset_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_tool_plan_bundle(item: Any, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, "canonical_tool_plan_bundle")
    path = repo_path(bundle_ref.get("path"), "canonical_tool_plan_bundle.path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), "canonical_tool_plan_bundle.schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), "canonical_tool_plan_bundle.bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(bundle_ref.get("expected_asset_count"), "canonical_tool_plan_bundle.expected_asset_count", minimum=1)
    validate_asset_count(bundle, expected_count, "canonical_tool_plan_bundle")
    dictionary_path = repo_path(bundle_ref.get("tool_dictionary"), "canonical_tool_plan_bundle.tool_dictionary")
    dictionary = load_json(dictionary_path)
    expected_dictionary_schema = require_string(bundle_ref.get("tool_dictionary_schema"), "canonical_tool_plan_bundle.tool_dictionary_schema")
    if dictionary.get("schema") != expected_dictionary_schema:
        fail(f"{display_path(dictionary_path)} schema must be {expected_dictionary_schema}")
    expected_tool_count = require_int(bundle_ref.get("expected_tool_count"), "canonical_tool_plan_bundle.expected_tool_count", minimum=1)
    if dictionary.get("tool_count") != expected_tool_count:
        fail("canonical_tool_plan_bundle.expected_tool_count must match tool dictionary")
    sequence_policy_path = repo_path(bundle_ref.get("sequence_policy"), "canonical_tool_plan_bundle.sequence_policy")
    sequence_policy = load_json(sequence_policy_path)
    expected_sequence_policy_schema = require_string(bundle_ref.get("sequence_policy_schema"), "canonical_tool_plan_bundle.sequence_policy_schema")
    if sequence_policy.get("schema") != expected_sequence_policy_schema:
        fail(f"{display_path(sequence_policy_path)} schema must be {expected_sequence_policy_schema}")
    if sequence_policy.get("tool_dictionary") != dictionary.get("dictionary_id"):
        fail("canonical_tool_plan_bundle.sequence_policy must reference the canonical tool dictionary")
    if sequence_policy.get("stage_order") != dictionary.get("stages"):
        fail("canonical_tool_plan_bundle.sequence_policy stage_order must match tool dictionary")
    if sequence_policy.get("no_claims") != FALSE_CLAIMS:
        fail("canonical_tool_plan_bundle.sequence_policy no_claims must match required false claim flags")
    geometry_dictionary_path = repo_path(bundle_ref.get("geometry_dictionary"), "canonical_tool_plan_bundle.geometry_dictionary")
    if not geometry_dictionary_path.is_dir():
        fail("canonical_tool_plan_bundle.geometry_dictionary must reference the geometry_dictionary directory")
    for term_name in ("profile_operation_stack", "finish_tool_stack"):
        term_path = geometry_dictionary_path / "operations" / f"{term_name}.json"
        if not term_path.exists():
            fail(f"canonical_tool_plan_bundle.geometry_dictionary must contain operations/{term_name}.json")
    expected_family_policy_count = require_int(
        bundle_ref.get("expected_asset_family_policy_count"),
        "canonical_tool_plan_bundle.expected_asset_family_policy_count",
        minimum=1,
    )
    family_policies = require_list(sequence_policy.get("asset_family_policies"), "canonical_tool_plan_bundle.sequence_policy.asset_family_policies")
    if sequence_policy.get("asset_family_policy_count") != expected_family_policy_count:
        fail("canonical_tool_plan_bundle.expected_asset_family_policy_count must match sequence policy")
    if len(family_policies) != expected_family_policy_count:
        fail("canonical_tool_plan_bundle.expected_asset_family_policy_count must match asset_family_policies length")
    compiler = script_path(bundle_ref.get("compiler"), "canonical_tool_plan_bundle.compiler")
    validator = script_path(bundle_ref.get("validator"), "canonical_tool_plan_bundle.validator")
    script_path(bundle_ref.get("adapter"), "canonical_tool_plan_bundle.adapter")
    report_validator = script_path(bundle_ref.get("execution_report_validator"), "canonical_tool_plan_bundle.execution_report_validator")
    assert_no_blender_import(compiler, "canonical_tool_plan_bundle.compiler")
    assert_no_blender_import(validator, "canonical_tool_plan_bundle.validator")
    assert_no_blender_import(report_validator, "canonical_tool_plan_bundle.execution_report_validator")
    plan_ids = require_string_list(bundle_ref.get("default_plan_ids"), "canonical_tool_plan_bundle.default_plan_ids")
    if len(plan_ids) != expected_count:
        fail("canonical_tool_plan_bundle.default_plan_ids must match expected_asset_count")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, "canonical_tool_plan_bundle.pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "asset_count": expected_count,
        "tool_count": expected_tool_count,
        "geometry_dictionary": display_path(geometry_dictionary_path),
        "asset_family_policy_count": expected_family_policy_count,
        "default_plan_count": len(plan_ids),
        "pipeline_label_count": len(labels),
    }


def validate_source_asset_polish_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_asset_polish_plan_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_asset_polish_plan_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_asset_polish_plan_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_asset_polish_plan_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(
        bundle_ref.get("expected_plan_count"),
        f"source_asset_polish_plan_bundles[{index}].expected_plan_count",
        minimum=1,
    )
    plans = require_list(bundle.get("plans"), f"source_asset_polish_plan_bundles[{index}].plans")
    if len(plans) != expected_count:
        fail(f"source_asset_polish_plan_bundles[{index}].expected_plan_count must match plans length")
    if bundle.get("plan_count") != expected_count:
        fail(f"source_asset_polish_plan_bundles[{index}].expected_plan_count must match bundle plan_count")
    dictionary_path = repo_path(bundle_ref.get("tool_dictionary"), f"source_asset_polish_plan_bundles[{index}].tool_dictionary")
    dictionary = load_json(dictionary_path)
    expected_dictionary_schema = require_string(
        bundle_ref.get("tool_dictionary_schema"),
        f"source_asset_polish_plan_bundles[{index}].tool_dictionary_schema",
    )
    if dictionary.get("schema") != expected_dictionary_schema:
        fail(f"{display_path(dictionary_path)} schema must be {expected_dictionary_schema}")
    geometry_dictionary_path = repo_path(bundle_ref.get("geometry_dictionary"), f"source_asset_polish_plan_bundles[{index}].geometry_dictionary")
    if not (geometry_dictionary_path / "operations" / "asset_polish_tool_plan.json").exists():
        fail("source_asset_polish_plan_bundles geometry_dictionary must contain operations/asset_polish_tool_plan.json")
    compiler = script_path(bundle_ref.get("compiler"), f"source_asset_polish_plan_bundles[{index}].compiler")
    validator = script_path(bundle_ref.get("validator"), f"source_asset_polish_plan_bundles[{index}].validator")
    adapter = script_path(bundle_ref.get("adapter_validate_only"), f"source_asset_polish_plan_bundles[{index}].adapter_validate_only")
    assert_no_blender_import(compiler, f"source_asset_polish_plan_bundles[{index}].compiler")
    assert_no_blender_import(validator, f"source_asset_polish_plan_bundles[{index}].validator")
    assert_no_blender_import(adapter, f"source_asset_polish_plan_bundles[{index}].adapter_validate_only")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_asset_polish_plan_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "plan_count": expected_count,
        "tool_dictionary": display_path(dictionary_path),
        "adapter_validate_only": display_path(adapter),
        "pipeline_label_count": len(labels),
    }


def validate_source_profile_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_profile_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_profile_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_profile_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_profile_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(bundle_ref.get("expected_profile_count"), f"source_profile_bundles[{index}].expected_profile_count", minimum=1)
    profiles = require_list(bundle.get("profiles"), f"source_profile_bundles[{index}].profiles")
    if len(profiles) != expected_count:
        fail(f"source_profile_bundles[{index}].expected_profile_count must match profiles length")
    if bundle.get("profile_count") != expected_count:
        fail(f"source_profile_bundles[{index}].expected_profile_count must match bundle profile_count")
    validator = script_path(bundle_ref.get("validator"), f"source_profile_bundles[{index}].validator")
    assert_no_blender_import(validator, f"source_profile_bundles[{index}].validator")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_profile_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "profile_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_source_graph_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_graph_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_graph_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_graph_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_graph_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(bundle_ref.get("expected_graph_count"), f"source_graph_bundles[{index}].expected_graph_count", minimum=1)
    graphs = require_list(bundle.get("graphs"), f"source_graph_bundles[{index}].graphs")
    if len(graphs) != expected_count:
        fail(f"source_graph_bundles[{index}].expected_graph_count must match graphs length")
    if bundle.get("graph_count") != expected_count:
        fail(f"source_graph_bundles[{index}].expected_graph_count must match bundle graph_count")
    compiler = script_path(bundle_ref.get("compiler"), f"source_graph_bundles[{index}].compiler")
    assert_no_blender_import(compiler, f"source_graph_bundles[{index}].compiler")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_graph_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "graph_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_source_cell_selection_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_cell_selection_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_cell_selection_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_cell_selection_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_cell_selection_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(
        bundle_ref.get("expected_selection_set_count"),
        f"source_cell_selection_bundles[{index}].expected_selection_set_count",
        minimum=1,
    )
    selection_sets = require_list(bundle.get("selection_sets"), f"source_cell_selection_bundles[{index}].selection_sets")
    if len(selection_sets) != expected_count:
        fail(f"source_cell_selection_bundles[{index}].expected_selection_set_count must match selection_sets length")
    if bundle.get("selection_set_count") != expected_count:
        fail(f"source_cell_selection_bundles[{index}].expected_selection_set_count must match bundle selection_set_count")
    compiler = script_path(bundle_ref.get("compiler"), f"source_cell_selection_bundles[{index}].compiler")
    assert_no_blender_import(compiler, f"source_cell_selection_bundles[{index}].compiler")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_cell_selection_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "selection_set_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_source_pattern_field_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_pattern_field_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_pattern_field_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_pattern_field_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_pattern_field_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(
        bundle_ref.get("expected_field_count"),
        f"source_pattern_field_bundles[{index}].expected_field_count",
        minimum=1,
    )
    fields = require_list(bundle.get("fields"), f"source_pattern_field_bundles[{index}].fields")
    if len(fields) != expected_count:
        fail(f"source_pattern_field_bundles[{index}].expected_field_count must match fields length")
    if bundle.get("field_count") != expected_count:
        fail(f"source_pattern_field_bundles[{index}].expected_field_count must match bundle field_count")
    compiler = script_path(bundle_ref.get("compiler"), f"source_pattern_field_bundles[{index}].compiler")
    assert_no_blender_import(compiler, f"source_pattern_field_bundles[{index}].compiler")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_pattern_field_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "field_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_source_pattern_segment_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_pattern_segment_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_pattern_segment_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_pattern_segment_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_pattern_segment_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(
        bundle_ref.get("expected_segment_set_count"),
        f"source_pattern_segment_bundles[{index}].expected_segment_set_count",
        minimum=1,
    )
    segment_sets = require_list(bundle.get("segment_sets"), f"source_pattern_segment_bundles[{index}].segment_sets")
    if len(segment_sets) != expected_count:
        fail(f"source_pattern_segment_bundles[{index}].expected_segment_set_count must match segment_sets length")
    if bundle.get("segment_set_count") != expected_count:
        fail(f"source_pattern_segment_bundles[{index}].expected_segment_set_count must match bundle segment_set_count")
    compiler = script_path(bundle_ref.get("compiler"), f"source_pattern_segment_bundles[{index}].compiler")
    assert_no_blender_import(compiler, f"source_pattern_segment_bundles[{index}].compiler")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_pattern_segment_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "segment_set_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_source_taxonomy_bundle(item: Any, index: int, known_labels: set[str]) -> dict[str, Any]:
    bundle_ref = require_object(item, f"source_taxonomy_bundles[{index}]")
    path = repo_path(bundle_ref.get("path"), f"source_taxonomy_bundles[{index}].path")
    bundle = load_json(path)
    expected_schema = require_string(bundle_ref.get("schema"), f"source_taxonomy_bundles[{index}].schema")
    if bundle.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    bundle_id = require_string(bundle_ref.get("bundle_id"), f"source_taxonomy_bundles[{index}].bundle_id")
    if bundle.get("bundle_id") != bundle_id:
        fail(f"{display_path(path)} bundle_id must be {bundle_id}")
    expected_count = require_int(bundle_ref.get("expected_term_count"), f"source_taxonomy_bundles[{index}].expected_term_count", minimum=1)
    terms = require_list(bundle.get("taxonomy_terms"), f"source_taxonomy_bundles[{index}].taxonomy_terms")
    if len(terms) != expected_count:
        fail(f"source_taxonomy_bundles[{index}].expected_term_count must match taxonomy_terms length")
    if bundle.get("taxonomy_term_count") != expected_count:
        fail(f"source_taxonomy_bundles[{index}].expected_term_count must match bundle taxonomy_term_count")
    validator = script_path(bundle_ref.get("validator"), f"source_taxonomy_bundles[{index}].validator")
    assert_no_blender_import(validator, f"source_taxonomy_bundles[{index}].validator")
    labels = validate_pipeline_labels(bundle_ref.get("pipeline_labels"), known_labels, f"source_taxonomy_bundles[{index}].pipeline_labels")
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "schema": expected_schema,
        "term_count": expected_count,
        "pipeline_label_count": len(labels),
    }


def validate_reference_recipe(item: Any, index: int, canonical_paths: set[str]) -> dict[str, Any]:
    reference = require_object(item, f"reference_only_recipe_bundles[{index}]")
    path = repo_path(reference.get("path"), f"reference_only_recipe_bundles[{index}].path")
    if display_path(path) in canonical_paths:
        fail(f"reference_only_recipe_bundles[{index}].path must not also be canonical")
    data = load_json(path)
    expected_schema = require_string(reference.get("schema"), f"reference_only_recipe_bundles[{index}].schema")
    if data.get("schema") != expected_schema:
        fail(f"{display_path(path)} schema must be {expected_schema}")
    status = require_string(reference.get("status"), f"reference_only_recipe_bundles[{index}].status")
    if status not in {"reference_only", "superseded"}:
        fail(f"reference_only_recipe_bundles[{index}].status must be reference_only or superseded")
    require_string(reference.get("reason"), f"reference_only_recipe_bundles[{index}].reason")
    if status == "superseded":
        superseded_by = repo_path(reference.get("superseded_by"), f"reference_only_recipe_bundles[{index}].superseded_by")
        if not superseded_by.exists():
            fail(f"reference_only_recipe_bundles[{index}].superseded_by references missing file")
    return {"path": display_path(path), "schema": expected_schema, "status": status}


def validate_registry(path: Path) -> dict[str, Any]:
    registry = load_json(path)
    if registry.get("schema") != REGISTRY_SCHEMA:
        fail(f"{display_path(path)} schema must be {REGISTRY_SCHEMA}")
    if registry.get("no_claims") != FALSE_CLAIMS:
        fail("no_claims must exactly match required false claim flags")
    rules = require_object(registry.get("rules"), "rules")
    for key in (
        "source_recipes_compile_to_deterministic_json",
        "blender_is_adapter_layer",
        "canonical_compilers_do_not_import_blender",
        "generated_outputs_stay_under_tmp",
        "reference_only_recipes_are_not_pipeline_inputs",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")
    known_labels = pipeline_labels()
    geometry_results = [
        validate_geometry_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("canonical_geometry_bundles"), "canonical_geometry_bundles"))
    ]
    if not geometry_results:
        fail("canonical_geometry_bundles must not be empty")
    geometry_paths = {result["path"] for result in geometry_results}
    if len(geometry_paths) != len(geometry_results):
        fail("canonical_geometry_bundles paths must be unique")
    tool_plan_result = validate_tool_plan_bundle(registry.get("canonical_tool_plan_bundle"), known_labels)
    source_asset_polish_results = [
        validate_source_asset_polish_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_asset_polish_plan_bundles"), "source_asset_polish_plan_bundles"))
    ]
    source_asset_polish_paths = {result["path"] for result in source_asset_polish_results}
    if len(source_asset_polish_paths) != len(source_asset_polish_results):
        fail("source_asset_polish_plan_bundles paths must be unique")
    source_profile_results = [
        validate_source_profile_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_profile_bundles"), "source_profile_bundles"))
    ]
    source_profile_paths = {result["path"] for result in source_profile_results}
    if len(source_profile_paths) != len(source_profile_results):
        fail("source_profile_bundles paths must be unique")
    source_graph_results = [
        validate_source_graph_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_graph_bundles"), "source_graph_bundles"))
    ]
    source_graph_paths = {result["path"] for result in source_graph_results}
    if len(source_graph_paths) != len(source_graph_results):
        fail("source_graph_bundles paths must be unique")
    source_cell_selection_results = [
        validate_source_cell_selection_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_cell_selection_bundles"), "source_cell_selection_bundles"))
    ]
    source_cell_selection_paths = {result["path"] for result in source_cell_selection_results}
    if len(source_cell_selection_paths) != len(source_cell_selection_results):
        fail("source_cell_selection_bundles paths must be unique")
    source_pattern_field_results = [
        validate_source_pattern_field_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_pattern_field_bundles"), "source_pattern_field_bundles"))
    ]
    source_pattern_field_paths = {result["path"] for result in source_pattern_field_results}
    if len(source_pattern_field_paths) != len(source_pattern_field_results):
        fail("source_pattern_field_bundles paths must be unique")
    source_pattern_segment_results = [
        validate_source_pattern_segment_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_pattern_segment_bundles"), "source_pattern_segment_bundles"))
    ]
    source_pattern_segment_paths = {result["path"] for result in source_pattern_segment_results}
    if len(source_pattern_segment_paths) != len(source_pattern_segment_results):
        fail("source_pattern_segment_bundles paths must be unique")
    source_taxonomy_results = [
        validate_source_taxonomy_bundle(item, index, known_labels)
        for index, item in enumerate(require_list(registry.get("source_taxonomy_bundles"), "source_taxonomy_bundles"))
    ]
    source_taxonomy_paths = {result["path"] for result in source_taxonomy_results}
    if len(source_taxonomy_paths) != len(source_taxonomy_results):
        fail("source_taxonomy_bundles paths must be unique")
    canonical_paths = (
        geometry_paths
        | {tool_plan_result["path"]}
        | source_asset_polish_paths
        | source_profile_paths
        | source_graph_paths
        | source_cell_selection_paths
        | source_pattern_field_paths
        | source_pattern_segment_paths
        | source_taxonomy_paths
    )
    reference_results = [
        validate_reference_recipe(item, index, canonical_paths)
        for index, item in enumerate(require_list(registry.get("reference_only_recipe_bundles"), "reference_only_recipe_bundles"))
    ]
    quality_gates = require_object(registry.get("quality_gates"), "quality_gates")
    for field in ("pipeline_validator", "script_orbit_audit", "generated_output_guard"):
        script_path(quality_gates.get(field), f"quality_gates.{field}")
    required_pipeline_rules = require_object(quality_gates.get("required_pipeline_rules"), "quality_gates.required_pipeline_rules")
    expected_rules = {
        "generated_outputs_in_repo": False,
        "blender_is_adapter_layer": True,
        "source_recipes_compile_to_deterministic_json": True,
        "quality_validation_gate": True,
    }
    if required_pipeline_rules != expected_rules:
        fail("quality_gates.required_pipeline_rules must match canonical pipeline rules")
    return {
        "schema": "asset_generation_registry_validation_result_v0",
        "registry": display_path(path),
        "status": "pass",
        "canonical_geometry_bundle_count": len(geometry_results),
        "canonical_geometry_asset_count": sum(result["asset_count"] for result in geometry_results),
        "canonical_tool_plan_bundle": tool_plan_result,
        "source_asset_polish_plan_bundle_count": len(source_asset_polish_results),
        "source_asset_polish_plan_count": sum(result["plan_count"] for result in source_asset_polish_results),
        "source_profile_bundle_count": len(source_profile_results),
        "source_profile_count": sum(result["profile_count"] for result in source_profile_results),
        "source_graph_bundle_count": len(source_graph_results),
        "source_graph_count": sum(result["graph_count"] for result in source_graph_results),
        "source_cell_selection_bundle_count": len(source_cell_selection_results),
        "source_cell_selection_set_count": sum(result["selection_set_count"] for result in source_cell_selection_results),
        "source_pattern_field_bundle_count": len(source_pattern_field_results),
        "source_pattern_field_count": sum(result["field_count"] for result in source_pattern_field_results),
        "source_pattern_segment_bundle_count": len(source_pattern_segment_results),
        "source_pattern_segment_set_count": sum(result["segment_set_count"] for result in source_pattern_segment_results),
        "source_taxonomy_bundle_count": len(source_taxonomy_results),
        "source_taxonomy_term_count": sum(result["term_count"] for result in source_taxonomy_results),
        "reference_only_recipe_count": len(reference_results),
        "pipeline_label_count": len(known_labels),
        "generated_outputs_created": False,
        "rules": {
            "runs_asset_pump": False,
            "runs_tool_plan_compiler": False,
            "runs_blender": False,
            "imports_blender": False,
            "creates_media_or_mesh": False,
            "validates_pipeline_label_coverage": True,
            "validates_source_asset_polish_plan_boundaries": True,
            "validates_source_profile_boundaries": True,
            "validates_source_graph_boundaries": True,
            "validates_source_cell_selection_boundaries": True,
            "validates_source_pattern_field_boundaries": True,
            "validates_source_pattern_segment_boundaries": True,
            "validates_source_taxonomy_boundaries": True,
            "validates_reference_only_boundaries": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the canonical deterministic asset generation registry.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    registry_path = args.registry if args.registry.is_absolute() else ROOT / args.registry
    result = validate_registry(registry_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS asset generation registry validation: "
        f"geometry_bundles={result['canonical_geometry_bundle_count']} "
        f"geometry_assets={result['canonical_geometry_asset_count']} "
        f"source_profiles={result['source_profile_count']} "
        f"source_asset_polish_plans={result['source_asset_polish_plan_count']} "
        f"source_graphs={result['source_graph_count']} "
        f"source_cell_selections={result['source_cell_selection_set_count']} "
        f"source_pattern_fields={result['source_pattern_field_count']} "
        f"source_pattern_segments={result['source_pattern_segment_set_count']} "
        f"source_taxonomies={result['source_taxonomy_term_count']} "
        f"reference_only={result['reference_only_recipe_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
