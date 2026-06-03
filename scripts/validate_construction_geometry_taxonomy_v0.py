#!/usr/bin/env python3
"""Validate the source-language construction geometry taxonomy.

This validator keeps the vocabulary for construction fields, selections,
omissions, promotions, and 2D-to-3D operations machine-readable. It does not
compile graphs, generate assets, execute Blender, or write generated outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "taxonomy" / "construction_geometry" / "construction_geometry_taxonomy_v0.json"
SCHEMA = "construction_geometry_taxonomy_v0"
TERM_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_RULES = {
    "construction_geometry_is_source_language": True,
    "dense_guides_are_not_final_art": True,
    "visible_form_comes_from_selection_and_omission": True,
    "architectural_roles_are_promoted_from_selected_nodes_edges_and_cells": True,
    "3d_generation_uses_declared_lift_sweep_fold_thicken_operations": True,
    "blender_is_adapter_layer": True,
}
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "building_code_compliance": False,
    "game_engine_integration": False,
}
TERM_CATEGORIES = {
    "source_geometry",
    "selection_rule",
    "pattern_unit",
    "historical_pattern_family",
    "generation_operation",
}
SOURCE_TYPES = {
    "academic_project_note",
    "architectural_history_article",
    "architectural_reference_note",
    "book_record",
    "mathematical_glossary",
    "museum_essay",
    "research_article_record",
}
PATH_STATUSES = {"exists", "planned"}
REQUIRED_TERM_IDS = {
    "construction_field",
    "construction_node",
    "construction_edge",
    "construction_cell",
    "guide_line",
    "selected_subgraph",
    "selective_omission",
    "role_promotion",
    "line_promotion",
    "cell_promotion",
    "motif_module",
    "motif_orbit",
    "tracery",
    "muqarnas_cell_plan",
    "lift_operation",
    "fold_operation",
    "sweep_operation",
    "thicken_operation",
    "chamfer_bevel_operation",
    "cascade_order",
}
REQUIRED_CLAIM_IDS = {
    "patterns_come_from_selection_and_omission",
    "repeated_motifs_form_larger_systems",
    "gothic_form_can_be_read_as_procedural_geometry",
    "2d_cell_plans_can_lift_into_vaults",
    "same_master_pattern_can_feed_many_asset_roles",
}


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


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{field} must be a boolean")
    return value


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def validate_sources(bundle: dict[str, Any]) -> set[str]:
    sources = require_list(bundle.get("sources"), "sources")
    expected_count = require_int(bundle.get("source_count"), "source_count", minimum=1)
    if len(sources) != expected_count:
        fail("source_count must match sources length")
    seen: set[str] = set()
    for index, source in enumerate(sources):
        item = require_object(source, f"sources[{index}]")
        source_id = require_string(item.get("source_id"), f"sources[{index}].source_id")
        if source_id in seen:
            fail(f"duplicate source_id: {source_id}")
        seen.add(source_id)
        require_string(item.get("title"), f"{source_id}.title")
        url = require_string(item.get("url"), f"{source_id}.url")
        if not url.startswith("https://"):
            fail(f"{source_id}.url must be https")
        source_type = require_string(item.get("source_type"), f"{source_id}.source_type")
        if source_type not in SOURCE_TYPES:
            fail(f"{source_id}.source_type unsupported: {source_type}")
        require_string(item.get("support_summary"), f"{source_id}.support_summary")
        require_string_list(item.get("relevance"), f"{source_id}.relevance")
    return seen


def validate_source_refs(values: Any, field: str, source_ids: set[str]) -> list[str]:
    refs = require_string_list(values, field)
    unknown = sorted(set(refs) - source_ids)
    if unknown:
        fail(f"{field} references unknown source ids: {unknown}")
    return refs


def validate_term_refs(values: Any, field: str, term_ids: set[str]) -> list[str]:
    refs = require_string_list(values, field)
    unknown = sorted(set(refs) - term_ids)
    if unknown:
        fail(f"{field} references unknown term ids: {unknown}")
    return refs


def validate_terms(bundle: dict[str, Any], source_ids: set[str]) -> set[str]:
    terms = require_list(bundle.get("taxonomy_terms"), "taxonomy_terms")
    expected_count = require_int(bundle.get("taxonomy_term_count"), "taxonomy_term_count", minimum=1)
    if len(terms) != expected_count:
        fail("taxonomy_term_count must match taxonomy_terms length")
    seen: set[str] = set()
    term_relationships: dict[str, list[str]] = {}
    for index, term in enumerate(terms):
        item = require_object(term, f"taxonomy_terms[{index}]")
        term_id = require_string(item.get("term_id"), f"taxonomy_terms[{index}].term_id")
        if not TERM_ID_RE.match(term_id):
            fail(f"invalid term_id: {term_id}")
        if term_id in seen:
            fail(f"duplicate term_id: {term_id}")
        seen.add(term_id)
        require_string(item.get("plain_name"), f"{term_id}.plain_name")
        category = require_string(item.get("category"), f"{term_id}.category")
        if category not in TERM_CATEGORIES:
            fail(f"{term_id}.category unsupported: {category}")
        require_string(item.get("definition"), f"{term_id}.definition")
        require_string(item.get("repo_use"), f"{term_id}.repo_use")
        require_string_list(item.get("future_recipe_fields"), f"{term_id}.future_recipe_fields")
        term_relationships[term_id] = require_string_list(item.get("related_terms"), f"{term_id}.related_terms", allow_empty=True)
        validate_source_refs(item.get("source_support"), f"{term_id}.source_support", source_ids)
    missing = sorted(REQUIRED_TERM_IDS - seen)
    if missing:
        fail(f"missing required construction geometry terms: {missing}")
    for term_id, related in term_relationships.items():
        unknown_related = sorted(set(related) - seen)
        if unknown_related:
            fail(f"{term_id}.related_terms references unknown term ids: {unknown_related}")
    return seen


def validate_claims(bundle: dict[str, Any], source_ids: set[str]) -> set[str]:
    claims = require_list(bundle.get("claim_support"), "claim_support")
    expected_count = require_int(bundle.get("claim_count"), "claim_count", minimum=1)
    if len(claims) != expected_count:
        fail("claim_count must match claim_support length")
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        item = require_object(claim, f"claim_support[{index}]")
        claim_id = require_string(item.get("claim_id"), f"claim_support[{index}].claim_id")
        if claim_id in seen:
            fail(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        require_string(item.get("claim"), f"{claim_id}.claim")
        require_string(item.get("repo_translation"), f"{claim_id}.repo_translation")
        validate_source_refs(item.get("source_support"), f"{claim_id}.source_support", source_ids)
    missing = sorted(REQUIRED_CLAIM_IDS - seen)
    if missing:
        fail(f"missing required claim support records: {missing}")
    return seen


def validate_repo_mappings(bundle: dict[str, Any], term_ids: set[str]) -> set[str]:
    mappings = require_list(bundle.get("repo_mappings"), "repo_mappings")
    expected_count = require_int(bundle.get("repo_mapping_count"), "repo_mapping_count", minimum=1)
    if len(mappings) != expected_count:
        fail("repo_mapping_count must match repo_mappings length")
    seen: set[str] = set()
    for index, mapping in enumerate(mappings):
        item = require_object(mapping, f"repo_mappings[{index}]")
        mapping_id = require_string(item.get("mapping_id"), f"repo_mappings[{index}].mapping_id")
        if mapping_id in seen:
            fail(f"duplicate mapping_id: {mapping_id}")
        seen.add(mapping_id)
        repo_path = Path(require_string(item.get("repo_path"), f"{mapping_id}.repo_path"))
        if repo_path.is_absolute() or ".." in repo_path.parts:
            fail(f"{mapping_id}.repo_path must be a relative repo path")
        path_status = require_string(item.get("path_status"), f"{mapping_id}.path_status")
        if path_status not in PATH_STATUSES:
            fail(f"{mapping_id}.path_status unsupported: {path_status}")
        if path_status == "exists" and not (ROOT / repo_path).exists():
            fail(f"{mapping_id}.repo_path does not exist: {repo_path}")
        validate_term_refs(item.get("taxonomy_terms_used"), f"{mapping_id}.taxonomy_terms_used", term_ids)
        require_string(item.get("status"), f"{mapping_id}.status")
    return seen


def validate_bundle(path: Path) -> dict[str, Any]:
    bundle = load_json(path)
    if bundle.get("schema") != SCHEMA:
        fail(f"{display_path(path)} schema must be {SCHEMA}")
    require_string(bundle.get("bundle_id"), "bundle_id")
    rules = require_object(bundle.get("rules"), "rules")
    for key, expected in REQUIRED_RULES.items():
        if require_bool(rules.get(key), f"rules.{key}") is not expected:
            fail(f"rules.{key} must be {str(expected).lower()}")
    if require_object(bundle.get("no_claims"), "no_claims") != FALSE_CLAIMS:
        fail("no_claims must exactly match required false claim flags")
    source_ids = validate_sources(bundle)
    term_ids = validate_terms(bundle, source_ids)
    claim_ids = validate_claims(bundle, source_ids)
    mapping_ids = validate_repo_mappings(bundle, term_ids)
    return {
        "schema": "construction_geometry_taxonomy_validation_v0",
        "bundle": display_path(path),
        "status": "pass",
        "source_count": len(source_ids),
        "taxonomy_term_count": len(term_ids),
        "claim_count": len(claim_ids),
        "repo_mapping_count": len(mapping_ids),
        "rules": {
            "validates_required_terms": True,
            "validates_source_support": True,
            "validates_claim_support": True,
            "validates_repo_mappings": True,
            "runs_blender": False,
            "creates_generated_outputs": False,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate construction geometry source-language taxonomy.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
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
        "PASS construction geometry taxonomy validation: "
        f"sources={result['source_count']} "
        f"terms={result['taxonomy_term_count']} "
        f"claims={result['claim_count']} "
        f"repo_mappings={result['repo_mapping_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
