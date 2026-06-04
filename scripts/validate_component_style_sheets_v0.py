#!/usr/bin/env python3
"""Validate source-only architectural component style sheets.

Component style sheets sit between taxonomy and recipes. They say how a named
architectural component should be shaped, which geometry terms it uses, and
which Blender tools may execute the look later. This validator does not compile
recipes, run Blender, or write generated assets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "architecture" / "component_style_sheets" / "component_style_sheet_registry_v0.json"
GEOMETRY_ROOT = ROOT / "geometry_dictionary"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
    "building_code_compliance": False,
}
REQUIRED_REGISTRY_RULES = {
    "style_sheets_are_source_only": True,
    "style_sheets_bind_taxonomy_to_shapes": True,
    "style_sheets_declare_blender_tools": True,
    "style_sheets_do_not_execute_blender": True,
    "style_sheets_do_not_generate_assets": True,
}
REQUIRED_TAXONOMY_RULES = {
    "taxonomy_names_components_only": True,
    "styles_define_geometry_later": True,
    "component_style_sheets_bind_shapes_to_taxonomy": True,
    "blender_tools_are_declared_in_style_sheets": True,
    "recipes_compile_after_style_selection": True,
}
REQUIRED_BUNDLE_RULES = {
    "taxonomy_component_required": True,
    "geometric_shaping_ledger_required": True,
    "source_shapes_must_be_geometry_terms": True,
    "operations_must_be_geometry_terms": True,
    "blender_tools_must_be_known": True,
    "blender_stage_order_must_hold": True,
    "no_blender_execution": True,
    "no_generated_outputs": True,
}
ALLOWED_SOURCE_TYPES = {
    "architectural_reference",
    "architectural_glossary",
    "art_architecture_glossary",
    "user_reference",
}
ALLOWED_SHAPE_CATEGORIES = {"profile_primitive", "measurement"}
ALLOWED_OPERATION_CATEGORIES = {"mesh_operation", "composition_operation", "transform"}
ALLOWED_COMPILE_TARGETS = {"gameguy_asset_v0", "gameguy_tool_plan_v0"}


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
        stage = require_string(item.get("stage"), f"tool_dictionary.tools[{index}].stage")
        if stage not in stages:
            fail(f"{tool_id}.stage references unknown stage: {stage}")
        by_id[tool_id] = item
    if dictionary.get("tool_count") != len(by_id):
        fail("tool_dictionary.tool_count must match unique tools")
    return by_id, stages


def validate_domain_taxonomy(path: Path) -> tuple[set[str], dict[str, set[str]], set[str], int]:
    taxonomy = load_json(path)
    if taxonomy.get("schema") != "component_domain_taxonomy_bundle_v0":
        fail(f"{display_path(path)} schema must be component_domain_taxonomy_bundle_v0")
    if taxonomy.get("rules") != REQUIRED_TAXONOMY_RULES:
        fail("component domain taxonomy rules must match required source boundaries")
    if taxonomy.get("no_claims") != FALSE_CLAIMS:
        fail("component domain taxonomy no_claims must match required false claim flags")
    domains = require_list(taxonomy.get("domains"), "domain_taxonomy.domains")
    if taxonomy.get("domain_count") != len(domains):
        fail("domain_taxonomy.domain_count must match domains length")
    domain_ids: set[str] = set()
    components_by_domain: dict[str, set[str]] = {}
    component_total = 0
    for index, domain in enumerate(domains):
        item = require_object(domain, f"domain_taxonomy.domains[{index}]")
        domain_id = require_string(item.get("domain_id"), f"domain_taxonomy.domains[{index}].domain_id")
        if domain_id in domain_ids:
            fail(f"duplicate domain_id: {domain_id}")
        domain_ids.add(domain_id)
        require_string(item.get("plain_name"), f"{domain_id}.plain_name")
        require_string(item.get("role"), f"{domain_id}.role")
        components = require_list(item.get("components"), f"{domain_id}.components")
        if item.get("component_count") != len(components):
            fail(f"{domain_id}.component_count must match components length")
        component_ids: set[str] = set()
        for component_index, component in enumerate(components):
            component_item = require_object(component, f"{domain_id}.components[{component_index}]")
            component_id = require_string(component_item.get("component_id"), f"{domain_id}.components[{component_index}].component_id")
            if component_id in component_ids:
                fail(f"duplicate component_id in {domain_id}: {component_id}")
            component_ids.add(component_id)
            require_string(component_item.get("plain_name"), f"{domain_id}.{component_id}.plain_name")
            require_string(component_item.get("role"), f"{domain_id}.{component_id}.role")
        components_by_domain[domain_id] = component_ids
        component_total += len(component_ids)
    if taxonomy.get("component_total_count") != component_total:
        fail("domain_taxonomy.component_total_count must match component list total")
    style_families = set(require_string_list(taxonomy.get("style_families"), "domain_taxonomy.style_families"))
    if taxonomy.get("style_family_count") != len(style_families):
        fail("domain_taxonomy.style_family_count must match style_families length")
    return domain_ids, components_by_domain, style_families, component_total


def validate_sources(bundle: dict[str, Any]) -> set[str]:
    sources = require_list(bundle.get("sources"), "style_bundle.sources")
    if bundle.get("source_count") != len(sources):
        fail("style_bundle.source_count must match sources length")
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        item = require_object(source, f"style_bundle.sources[{index}]")
        source_id = require_string(item.get("source_id"), f"style_bundle.sources[{index}].source_id")
        if source_id in source_ids:
            fail(f"duplicate source_id: {source_id}")
        source_ids.add(source_id)
        require_string(item.get("title"), f"{source_id}.title")
        source_type = require_string(item.get("source_type"), f"{source_id}.source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            fail(f"{source_id}.source_type unsupported: {source_type}")
        url = require_string(item.get("url"), f"{source_id}.url")
        if source_type != "user_reference" and not url.startswith("https://"):
            fail(f"{source_id}.url must be https unless it is a user_reference")
        require_string(item.get("support_summary"), f"{source_id}.support_summary")
        if require_string(item.get("use_policy"), f"{source_id}.use_policy") != "morphology_reference_only":
            fail(f"{source_id}.use_policy must be morphology_reference_only")
    return source_ids


def validate_source_shapes(
    values: Any,
    field: str,
    geometry_terms: dict[str, dict[str, Any]],
) -> set[str]:
    shapes = require_list(values, field)
    if not shapes:
        fail(f"{field} must not be empty")
    term_ids: set[str] = set()
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
        term_ids.add(term_id)
    return term_ids


def validate_operations(
    values: Any,
    field: str,
    geometry_terms: dict[str, dict[str, Any]],
) -> set[str]:
    operations = require_string_list(values, field)
    operation_ids: set[str] = set()
    for term_id in operations:
        if term_id not in geometry_terms:
            fail(f"{field} references unknown geometry term: {term_id}")
        category = geometry_terms[term_id].get("category")
        if category not in ALLOWED_OPERATION_CATEGORIES:
            fail(f"{field} must reference operation/transform terms only: {term_id}")
        operation_ids.add(term_id)
    return operation_ids


def validate_tool_sequence(
    values: Any,
    field: str,
    tools: dict[str, dict[str, Any]],
    stage_order: list[str],
) -> set[str]:
    steps = require_list(values, field)
    if not steps:
        fail(f"{field} must not be empty")
    stage_indexes = {stage: index for index, stage in enumerate(stage_order)}
    previous_stage_index = -1
    tool_ids: set[str] = set()
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
        tool_ids.add(tool_id)
    return tool_ids


def validate_ledger_entry(
    value: Any,
    field: str,
    geometry_terms: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    stage_order: list[str],
) -> tuple[set[str], set[str], set[str]]:
    ledger = require_object(value, field)
    require_string(ledger.get("part"), f"{field}.part")
    require_string(ledger.get("taxonomy_name"), f"{field}.taxonomy_name")
    require_string(ledger.get("role"), f"{field}.role")
    source_shape_ids = validate_source_shapes(ledger.get("source_shapes"), f"{field}.source_shapes", geometry_terms)
    operation_ids = validate_operations(ledger.get("operations"), f"{field}.operations", geometry_terms)
    require_string_list(ledger.get("construction_rules"), f"{field}.construction_rules")
    require_string_list(ledger.get("edit_knobs"), f"{field}.edit_knobs")
    tool_ids = validate_tool_sequence(ledger.get("blender_tool_sequence"), f"{field}.blender_tool_sequence", tools, stage_order)
    return source_shape_ids, operation_ids, tool_ids


def validate_style_sheet(
    value: Any,
    index: int,
    bundle_domain: str,
    bundle_style_family: str,
    components_by_domain: dict[str, set[str]],
    style_families: set[str],
    source_ids: set[str],
    geometry_terms: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    stage_order: list[str],
) -> tuple[str, int, set[str], set[str], set[str]]:
    style = require_object(value, f"style_sheets[{index}]")
    style_id = require_string(style.get("style_id"), f"style_sheets[{index}].style_id")
    require_string(style.get("plain_name"), f"{style_id}.plain_name")
    domain = require_string(style.get("domain"), f"{style_id}.domain")
    if domain != bundle_domain:
        fail(f"{style_id}.domain must match bundle domain {bundle_domain}")
    component = require_string(style.get("component"), f"{style_id}.component")
    if component not in components_by_domain.get(domain, set()):
        fail(f"{style_id}.component references unknown taxonomy component: {domain}.{component}")
    style_family = require_string(style.get("style_family"), f"{style_id}.style_family")
    if style_family != bundle_style_family:
        fail(f"{style_id}.style_family must match bundle style family {bundle_style_family}")
    if style_family not in style_families:
        fail(f"{style_id}.style_family is not declared in component domain taxonomy")
    require_string(style.get("style_intent"), f"{style_id}.style_intent")
    source_support = set(require_string_list(style.get("source_support"), f"{style_id}.source_support"))
    unknown_sources = sorted(source_support - source_ids)
    if unknown_sources:
        fail(f"{style_id}.source_support references unknown sources: {unknown_sources}")
    require_string_list(style.get("component_anatomy"), f"{style_id}.component_anatomy")
    targets = set(require_string_list(style.get("compile_targets"), f"{style_id}.compile_targets"))
    unsupported_targets = sorted(targets - ALLOWED_COMPILE_TARGETS)
    if unsupported_targets:
        fail(f"{style_id}.compile_targets unsupported: {unsupported_targets}")
    if style.get("no_claims") != FALSE_CLAIMS:
        fail(f"{style_id}.no_claims must match required false claim flags")
    entries = require_list(style.get("geometric_shaping_ledger"), f"{style_id}.geometric_shaping_ledger")
    if not entries:
        fail(f"{style_id}.geometric_shaping_ledger must not be empty")
    shape_ids: set[str] = set()
    operation_ids: set[str] = set()
    tool_ids: set[str] = set()
    seen_parts: set[str] = set()
    for ledger_index, entry in enumerate(entries):
        part = require_object(entry, f"{style_id}.geometric_shaping_ledger[{ledger_index}]").get("part")
        part_name = require_string(part, f"{style_id}.geometric_shaping_ledger[{ledger_index}].part")
        if part_name in seen_parts:
            fail(f"{style_id}.geometric_shaping_ledger has duplicate part: {part_name}")
        seen_parts.add(part_name)
        entry_shape_ids, entry_operation_ids, entry_tool_ids = validate_ledger_entry(
            entry,
            f"{style_id}.geometric_shaping_ledger[{ledger_index}]",
            geometry_terms,
            tools,
            stage_order,
        )
        shape_ids.update(entry_shape_ids)
        operation_ids.update(entry_operation_ids)
        tool_ids.update(entry_tool_ids)
    return style_id, len(entries), shape_ids, operation_ids, tool_ids


def validate_bundle(
    path: Path,
    expected_count: int,
    expected_domain: str,
    expected_style_family: str,
    taxonomy_path: Path,
    components_by_domain: dict[str, set[str]],
    style_families: set[str],
    geometry_terms: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    stage_order: list[str],
) -> dict[str, Any]:
    bundle = load_json(path)
    if bundle.get("schema") != "component_style_sheet_bundle_v0":
        fail(f"{display_path(path)} schema must be component_style_sheet_bundle_v0")
    bundle_id = require_string(bundle.get("bundle_id"), f"{display_path(path)}.bundle_id")
    if bundle.get("status") != "source_style_sheet_only":
        fail(f"{bundle_id}.status must be source_style_sheet_only")
    if bundle.get("domain") != expected_domain:
        fail(f"{bundle_id}.domain must match registry domain {expected_domain}")
    if bundle.get("style_family") != expected_style_family:
        fail(f"{bundle_id}.style_family must match registry style family {expected_style_family}")
    if bundle.get("domain_taxonomy_ref") != display_path(taxonomy_path):
        fail(f"{bundle_id}.domain_taxonomy_ref must reference the registry domain taxonomy")
    if bundle.get("rules") != REQUIRED_BUNDLE_RULES:
        fail(f"{bundle_id}.rules must match required style sheet source boundaries")
    if bundle.get("no_claims") != FALSE_CLAIMS:
        fail(f"{bundle_id}.no_claims must match required false claim flags")
    source_ids = validate_sources(bundle)
    style_sheets = require_list(bundle.get("style_sheets"), f"{bundle_id}.style_sheets")
    if len(style_sheets) != expected_count:
        fail(f"{bundle_id}.expected_style_sheet_count must match style_sheets length")
    if bundle.get("style_sheet_count") != expected_count:
        fail(f"{bundle_id}.style_sheet_count must match registry expected count")
    style_ids: set[str] = set()
    total_ledger_entries = 0
    used_shapes: set[str] = set()
    used_operations: set[str] = set()
    used_tools: set[str] = set()
    for index, style_sheet in enumerate(style_sheets):
        style_id, ledger_count, shape_ids, operation_ids, tool_ids = validate_style_sheet(
            style_sheet,
            index,
            expected_domain,
            expected_style_family,
            components_by_domain,
            style_families,
            source_ids,
            geometry_terms,
            tools,
            stage_order,
        )
        if style_id in style_ids:
            fail(f"duplicate style_id: {style_id}")
        style_ids.add(style_id)
        total_ledger_entries += ledger_count
        used_shapes.update(shape_ids)
        used_operations.update(operation_ids)
        used_tools.update(tool_ids)
    return {
        "bundle_id": bundle_id,
        "path": display_path(path),
        "domain": expected_domain,
        "style_family": expected_style_family,
        "source_count": len(source_ids),
        "style_sheet_count": len(style_ids),
        "ledger_entry_count": total_ledger_entries,
        "source_shape_terms": sorted(used_shapes),
        "source_shape_term_count": len(used_shapes),
        "operation_terms": sorted(used_operations),
        "operation_term_count": len(used_operations),
        "blender_tools": sorted(used_tools),
        "blender_tool_count": len(used_tools),
    }


def validate_registry(path: Path) -> dict[str, Any]:
    registry = load_json(path)
    if registry.get("schema") != "component_style_sheet_registry_v0":
        fail(f"{display_path(path)} schema must be component_style_sheet_registry_v0")
    if registry.get("rules") != REQUIRED_REGISTRY_RULES:
        fail("component style sheet registry rules must match required source boundaries")
    if registry.get("no_claims") != FALSE_CLAIMS:
        fail("component style sheet registry no_claims must match required false claim flags")
    taxonomy_path = repo_path(registry.get("domain_taxonomy"), "domain_taxonomy")
    taxonomy_schema = require_string(registry.get("domain_taxonomy_schema"), "domain_taxonomy_schema")
    if taxonomy_schema != "component_domain_taxonomy_bundle_v0":
        fail("domain_taxonomy_schema must be component_domain_taxonomy_bundle_v0")
    domain_ids, components_by_domain, style_families, component_total = validate_domain_taxonomy(taxonomy_path)
    geometry_dictionary_path = repo_path(registry.get("geometry_dictionary"), "geometry_dictionary")
    if geometry_dictionary_path != GEOMETRY_ROOT:
        fail("geometry_dictionary must reference geometry_dictionary")
    geometry_terms = load_geometry_terms()
    tool_dictionary_path = repo_path(registry.get("tool_dictionary"), "tool_dictionary")
    tools, stage_order = load_tool_dictionary(tool_dictionary_path)
    tool_dictionary_schema = require_string(registry.get("tool_dictionary_schema"), "tool_dictionary_schema")
    if tool_dictionary_schema != "blender_tool_dictionary_v0":
        fail("tool_dictionary_schema must be blender_tool_dictionary_v0")
    bundle_refs = require_list(registry.get("style_sheet_bundles"), "style_sheet_bundles")
    if registry.get("style_sheet_bundle_count") != len(bundle_refs):
        fail("style_sheet_bundle_count must match style_sheet_bundles length")
    bundle_results = []
    paths: set[str] = set()
    for index, bundle_ref in enumerate(bundle_refs):
        item = require_object(bundle_ref, f"style_sheet_bundles[{index}]")
        bundle_id = require_string(item.get("bundle_id"), f"style_sheet_bundles[{index}].bundle_id")
        bundle_path = repo_path(item.get("path"), f"{bundle_id}.path")
        display_bundle_path = display_path(bundle_path)
        if display_bundle_path in paths:
            fail(f"duplicate style sheet bundle path: {display_bundle_path}")
        paths.add(display_bundle_path)
        if require_string(item.get("schema"), f"{bundle_id}.schema") != "component_style_sheet_bundle_v0":
            fail(f"{bundle_id}.schema must be component_style_sheet_bundle_v0")
        domain = require_string(item.get("domain"), f"{bundle_id}.domain")
        if domain not in domain_ids:
            fail(f"{bundle_id}.domain references unknown domain: {domain}")
        style_family = require_string(item.get("style_family"), f"{bundle_id}.style_family")
        if style_family not in style_families:
            fail(f"{bundle_id}.style_family references unknown style family: {style_family}")
        expected_count = require_int(item.get("expected_style_sheet_count"), f"{bundle_id}.expected_style_sheet_count", minimum=1)
        validator_path = repo_path(item.get("validator"), f"{bundle_id}.validator")
        if validator_path != Path(__file__).resolve():
            fail(f"{bundle_id}.validator must reference scripts/validate_component_style_sheets_v0.py")
        require_string_list(item.get("pipeline_labels"), f"{bundle_id}.pipeline_labels")
        bundle_results.append(
            validate_bundle(
                bundle_path,
                expected_count,
                domain,
                style_family,
                taxonomy_path,
                components_by_domain,
                style_families,
                geometry_terms,
                tools,
                stage_order,
            )
        )
    used_shapes = {term for result in bundle_results for term in result["source_shape_terms"]}
    used_operations = {term for result in bundle_results for term in result["operation_terms"]}
    used_tools = {tool for result in bundle_results for tool in result["blender_tools"]}
    return {
        "schema": "component_style_sheet_validation_result_v0",
        "registry": display_path(path),
        "status": "pass",
        "domain_count": len(domain_ids),
        "taxonomy_component_count": component_total,
        "style_family_count": len(style_families),
        "style_sheet_bundle_count": len(bundle_results),
        "style_sheet_count": sum(result["style_sheet_count"] for result in bundle_results),
        "ledger_entry_count": sum(result["ledger_entry_count"] for result in bundle_results),
        "source_count": sum(result["source_count"] for result in bundle_results),
        "source_shape_term_count": len(used_shapes),
        "operation_term_count": len(used_operations),
        "blender_tool_count": len(used_tools),
        "style_sheet_bundles": bundle_results,
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
    parser = argparse.ArgumentParser(description="Validate component style sheet sources.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--json-report", type=Path, help="Optional path for validation report.")
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
        "PASS component style sheet validation: "
        f"domains={result['domain_count']} components={result['taxonomy_component_count']} "
        f"style_sheets={result['style_sheet_count']} ledger_entries={result['ledger_entry_count']} "
        f"sources={result['source_count']} tools={result['blender_tool_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
