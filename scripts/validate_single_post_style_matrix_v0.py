#!/usr/bin/env python3
"""Validate the source-only single-post style matrix.

The matrix turns the human post atlas into checked source data: one reusable
post role, multiple style variants, legal geometry terms, legal Blender tool
IDs, and no full railing generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "data" / "architecture" / "component_style_sheets" / "railings" / "single_post_style_matrix_v0.json"
GEOMETRY_ROOT = ROOT / "geometry_dictionary"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
    "building_code_compliance": False,
}
REQUIRED_RULES = {
    "source_matrix_only": True,
    "single_post_only": True,
    "no_full_railing": True,
    "rail_socket_hint_only": True,
    "variants_share_anatomy": True,
    "source_shapes_must_be_geometry_terms": True,
    "operations_must_be_geometry_terms": True,
    "blender_tools_must_be_known": True,
    "blender_stage_order_must_hold": True,
    "no_blender_execution": True,
    "no_generated_outputs": True,
}
REQUIRED_ANATOMY = {
    "plinth",
    "base",
    "shaft",
    "collar",
    "cap",
    "finial",
    "rail_socket_hint",
    "face_panel",
    "side_detail",
    "material_regions",
}
ALLOWED_SHAPE_CATEGORIES = {"profile_primitive", "measurement"}
ALLOWED_OPERATION_CATEGORIES = {"mesh_operation", "composition_operation", "transform"}
ALLOWED_COMPONENTS = {"newel_post", "intermediate_post"}
ALLOWED_COMPILE_TARGETS = {"gameguy_asset_v0", "gameguy_tool_plan_v0"}


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


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def repo_path(value: Any, field: str) -> Path:
    text = require_string(value, field)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        fail(f"{field} must be a relative repo path")
    return ROOT / path


def load_geometry_terms() -> dict[str, dict[str, Any]]:
    terms: dict[str, dict[str, Any]] = {}
    for path in sorted(GEOMETRY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = require_string(term.get("term_id"), f"{display_path(path)}.term_id")
        if term_id in terms:
            fail(f"duplicate geometry term_id: {term_id}")
        terms[term_id] = term
    return terms


def load_tool_dictionary(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    dictionary = load_json(path)
    if dictionary.get("schema") != "blender_tool_dictionary_v0":
        fail(f"{display_path(path)} schema must be blender_tool_dictionary_v0")
    stages = require_string_list(dictionary.get("stages"), "tool_dictionary.stages")
    tools = require_list(dictionary.get("tools"), "tool_dictionary.tools")
    by_id: dict[str, dict[str, Any]] = {}
    for index, tool in enumerate(tools):
        item = require_object(tool, f"tool_dictionary.tools[{index}]")
        tool_id = require_string(item.get("tool_id"), f"tool_dictionary.tools[{index}].tool_id")
        if tool_id in by_id:
            fail(f"duplicate Blender tool_id: {tool_id}")
        stage = require_string(item.get("stage"), f"{tool_id}.stage")
        if stage not in stages:
            fail(f"{tool_id}.stage references unknown stage: {stage}")
        by_id[tool_id] = item
    if dictionary.get("tool_count") != len(by_id):
        fail("tool_dictionary.tool_count must match tools length")
    return by_id, stages


def load_taxonomy(path: Path) -> tuple[set[str], dict[str, set[str]], set[str]]:
    taxonomy = load_json(path)
    if taxonomy.get("schema") != "component_domain_taxonomy_bundle_v0":
        fail(f"{display_path(path)} schema must be component_domain_taxonomy_bundle_v0")
    domains = require_list(taxonomy.get("domains"), "domain_taxonomy.domains")
    domain_ids: set[str] = set()
    components_by_domain: dict[str, set[str]] = {}
    for index, domain in enumerate(domains):
        item = require_object(domain, f"domain_taxonomy.domains[{index}]")
        domain_id = require_string(item.get("domain_id"), f"domain_taxonomy.domains[{index}].domain_id")
        domain_ids.add(domain_id)
        components = require_list(item.get("components"), f"{domain_id}.components")
        components_by_domain[domain_id] = {
            require_string(require_object(component, f"{domain_id}.components[{component_index}]").get("component_id"), f"{domain_id}.components[{component_index}].component_id")
            for component_index, component in enumerate(components)
        }
    style_families = set(require_string_list(taxonomy.get("style_families"), "domain_taxonomy.style_families"))
    return domain_ids, components_by_domain, style_families


def validate_source_shapes(values: Any, field: str, geometry_terms: dict[str, dict[str, Any]]) -> set[str]:
    shapes = require_list(values, field)
    if not shapes:
        fail(f"{field} must not be empty")
    used: set[str] = set()
    for index, shape in enumerate(shapes):
        item = require_object(shape, f"{field}[{index}]")
        term_id = require_string(item.get("term_id"), f"{field}[{index}].term_id")
        if term_id not in geometry_terms:
            fail(f"{field}[{index}].term_id references unknown geometry term: {term_id}")
        category = geometry_terms[term_id].get("category")
        if category not in ALLOWED_SHAPE_CATEGORIES:
            fail(f"{field}[{index}].term_id must be a profile or measurement term: {term_id}")
        require_string(item.get("shape_role"), f"{field}[{index}].shape_role")
        require_string(item.get("control_policy"), f"{field}[{index}].control_policy")
        used.add(term_id)
    return used


def validate_operations(values: Any, field: str, geometry_terms: dict[str, dict[str, Any]]) -> set[str]:
    operations = require_string_list(values, field)
    used: set[str] = set()
    for term_id in operations:
        if term_id not in geometry_terms:
            fail(f"{field} references unknown geometry term: {term_id}")
        category = geometry_terms[term_id].get("category")
        if category not in ALLOWED_OPERATION_CATEGORIES:
            fail(f"{field} must reference operation or transform terms only: {term_id}")
        used.add(term_id)
    return used


def validate_tool_sequence(values: Any, field: str, tools: dict[str, dict[str, Any]], stage_order: list[str]) -> set[str]:
    steps = require_list(values, field)
    if not steps:
        fail(f"{field} must not be empty")
    stage_indexes = {stage: index for index, stage in enumerate(stage_order)}
    previous_stage_index = -1
    used: set[str] = set()
    for index, step in enumerate(steps):
        item = require_object(step, f"{field}[{index}]")
        stage = require_string(item.get("stage"), f"{field}[{index}].stage")
        tool_id = require_string(item.get("tool_id"), f"{field}[{index}].tool_id")
        if tool_id not in tools:
            fail(f"{field}[{index}].tool_id references unknown Blender tool: {tool_id}")
        actual_stage = tools[tool_id]["stage"]
        if actual_stage != stage:
            fail(f"{field}[{index}] stage must match tool dictionary: {tool_id} is {actual_stage}, not {stage}")
        current_stage_index = stage_indexes[stage]
        if current_stage_index < previous_stage_index:
            fail(f"{field}[{index}].stage is out of canonical stage order")
        previous_stage_index = current_stage_index
        require_string(item.get("use"), f"{field}[{index}].use")
        used.add(tool_id)
    return used


def validate_variant(
    value: Any,
    index: int,
    matrix_domain: str,
    components_by_domain: dict[str, set[str]],
    style_families: set[str],
    geometry_terms: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    stage_order: list[str],
) -> tuple[str, set[str], set[str], set[str]]:
    variant = require_object(value, f"style_variants[{index}]")
    style_id = require_string(variant.get("style_id"), f"style_variants[{index}].style_id")
    require_string(variant.get("plain_name"), f"{style_id}.plain_name")
    require_string(variant.get("visual_read"), f"{style_id}.visual_read")
    domain = require_string(variant.get("domain"), f"{style_id}.domain")
    if domain != matrix_domain:
        fail(f"{style_id}.domain must match matrix domain {matrix_domain}")
    component = require_string(variant.get("component"), f"{style_id}.component")
    if component not in ALLOWED_COMPONENTS:
        fail(f"{style_id}.component must be one of {sorted(ALLOWED_COMPONENTS)}")
    if component not in components_by_domain.get(domain, set()):
        fail(f"{style_id}.component references unknown taxonomy component: {domain}.{component}")
    style_family = require_string(variant.get("style_family"), f"{style_id}.style_family")
    if style_family not in style_families:
        fail(f"{style_id}.style_family is not declared in component domain taxonomy")
    require_string(variant.get("post_role"), f"{style_id}.post_role")
    shape_ids = validate_source_shapes(variant.get("source_shapes"), f"{style_id}.source_shapes", geometry_terms)
    operation_ids = validate_operations(variant.get("operations"), f"{style_id}.operations", geometry_terms)
    tool_ids = validate_tool_sequence(variant.get("blender_tool_sequence"), f"{style_id}.blender_tool_sequence", tools, stage_order)
    require_string_list(variant.get("edit_knobs"), f"{style_id}.edit_knobs")
    require_string_list(variant.get("do_not_do_rules"), f"{style_id}.do_not_do_rules")
    require_string_list(variant.get("manual_inspection_notes"), f"{style_id}.manual_inspection_notes")
    if require_string(variant.get("promotion_status"), f"{style_id}.promotion_status") != "matrix_candidate_only":
        fail(f"{style_id}.promotion_status must be matrix_candidate_only")
    targets = set(require_string_list(variant.get("compile_targets"), f"{style_id}.compile_targets"))
    unsupported_targets = sorted(targets - ALLOWED_COMPILE_TARGETS)
    if unsupported_targets:
        fail(f"{style_id}.compile_targets unsupported: {unsupported_targets}")
    if variant.get("no_claims") != FALSE_CLAIMS:
        fail(f"{style_id}.no_claims must match required false claim flags")
    return style_id, shape_ids, operation_ids, tool_ids


def validate_matrix(path: Path) -> dict[str, Any]:
    matrix = load_json(path)
    if matrix.get("schema") != "single_post_style_matrix_v0":
        fail(f"{display_path(path)} schema must be single_post_style_matrix_v0")
    matrix_id = require_string(matrix.get("matrix_id"), f"{display_path(path)}.matrix_id")
    if matrix.get("status") != "source_style_matrix_only":
        fail(f"{matrix_id}.status must be source_style_matrix_only")
    if matrix.get("rules") != REQUIRED_RULES:
        fail(f"{matrix_id}.rules must match required source boundaries")
    if matrix.get("no_claims") != FALSE_CLAIMS:
        fail(f"{matrix_id}.no_claims must match required false claim flags")
    domain = require_string(matrix.get("domain"), f"{matrix_id}.domain")
    taxonomy_path = repo_path(matrix.get("domain_taxonomy_ref"), f"{matrix_id}.domain_taxonomy_ref")
    domain_ids, components_by_domain, style_families = load_taxonomy(taxonomy_path)
    if domain not in domain_ids:
        fail(f"{matrix_id}.domain references unknown domain: {domain}")
    geometry_dictionary_path = repo_path(matrix.get("geometry_dictionary"), f"{matrix_id}.geometry_dictionary")
    if geometry_dictionary_path != GEOMETRY_ROOT:
        fail(f"{matrix_id}.geometry_dictionary must reference geometry_dictionary")
    geometry_terms = load_geometry_terms()
    tool_dictionary_path = repo_path(matrix.get("tool_dictionary"), f"{matrix_id}.tool_dictionary")
    tools, stage_order = load_tool_dictionary(tool_dictionary_path)
    envelope = require_object(matrix.get("shared_post_envelope"), f"{matrix_id}.shared_post_envelope")
    required_anatomy = set(require_string_list(envelope.get("required_anatomy"), f"{matrix_id}.shared_post_envelope.required_anatomy"))
    missing_anatomy = sorted(REQUIRED_ANATOMY - required_anatomy)
    if missing_anatomy:
        fail(f"{matrix_id}.shared_post_envelope.required_anatomy missing required terms: {missing_anatomy}")
    if require_string(envelope.get("rail_socket_policy"), f"{matrix_id}.shared_post_envelope.rail_socket_policy") != "hint_only_no_rail_generated":
        fail(f"{matrix_id}.shared_post_envelope.rail_socket_policy must be hint_only_no_rail_generated")
    require_string(envelope.get("height_class"), f"{matrix_id}.shared_post_envelope.height_class")
    require_string(envelope.get("detail_budget"), f"{matrix_id}.shared_post_envelope.detail_budget")
    require_string(envelope.get("decal_policy"), f"{matrix_id}.shared_post_envelope.decal_policy")
    require_string(envelope.get("finish_policy"), f"{matrix_id}.shared_post_envelope.finish_policy")
    expected_count = require_int(matrix.get("style_variant_count"), f"{matrix_id}.style_variant_count", minimum=1)
    variants = require_list(matrix.get("style_variants"), f"{matrix_id}.style_variants")
    if len(variants) != expected_count:
        fail(f"{matrix_id}.style_variant_count must match style_variants length")
    style_ids: set[str] = set()
    used_shapes: set[str] = set()
    used_operations: set[str] = set()
    used_tools: set[str] = set()
    for index, variant in enumerate(variants):
        style_id, shape_ids, operation_ids, tool_ids = validate_variant(
            variant,
            index,
            domain,
            components_by_domain,
            style_families,
            geometry_terms,
            tools,
            stage_order,
        )
        if style_id in style_ids:
            fail(f"duplicate style_id: {style_id}")
        style_ids.add(style_id)
        used_shapes.update(shape_ids)
        used_operations.update(operation_ids)
        used_tools.update(tool_ids)
    require_string(matrix.get("next_promotion_target"), f"{matrix_id}.next_promotion_target")
    return {
        "schema": "single_post_style_matrix_validation_result_v0",
        "matrix": display_path(path),
        "status": "pass",
        "domain": domain,
        "style_variant_count": len(style_ids),
        "source_shape_terms": sorted(used_shapes),
        "source_shape_term_count": len(used_shapes),
        "operation_terms": sorted(used_operations),
        "operation_term_count": len(used_operations),
        "blender_tools": sorted(used_tools),
        "blender_tool_count": len(used_tools),
        "generated_outputs_created": False,
        "rules": {
            "runs_asset_pump": False,
            "runs_tool_plan_compiler": False,
            "runs_blender": False,
            "imports_blender": False,
            "validates_domain_taxonomy": True,
            "validates_geometry_terms": True,
            "validates_blender_tools": True,
            "validates_stage_order": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the single-post style matrix.")
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--json-report", type=Path, help="Optional path for validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    matrix_path = args.matrix if args.matrix.is_absolute() else ROOT / args.matrix
    result = validate_matrix(matrix_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS single post style matrix validation: "
        f"variants={result['style_variant_count']} "
        f"shapes={result['source_shape_term_count']} "
        f"operations={result['operation_term_count']} "
        f"tools={result['blender_tool_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
