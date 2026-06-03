#!/usr/bin/env python3
"""Validate reference-led asset dissection packets.

The validator keeps reference packets source-side. It does not download images,
run Blender, generate geometry, or write mesh/media outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "data" / "architecture" / "asset_mill" / "reference_packets" / "gothic_panel_guard_reference_v0.json"
DEFAULT_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
GEOMETRY_DICTIONARY_ROOT = ROOT / "geometry_dictionary"
PACKET_SCHEMA = "asset_reference_dissection_packet_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
    "building_code_compliance": False,
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


def require_url(value: Any, field: str) -> str:
    url = require_string(value, field)
    if not url.startswith("https://"):
        fail(f"{field} must be an https URL")
    return url


def load_geometry_terms() -> set[str]:
    terms: set[str] = set()
    for path in sorted(GEOMETRY_DICTIONARY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = require_string(term.get("term_id"), f"{display_path(path)}.term_id")
        if term_id in terms:
            fail(f"duplicate geometry dictionary term `{term_id}`")
        terms.add(term_id)
    if not terms:
        fail("geometry dictionary must contain terms")
    return terms


def validate_tool_dictionary(dictionary: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if dictionary.get("schema") != "blender_tool_dictionary_v0":
        fail("tool dictionary schema must be blender_tool_dictionary_v0")
    stages = require_string_list(dictionary.get("stages"), "dictionary.stages")
    tools = require_list(dictionary.get("tools"), "dictionary.tools")
    if dictionary.get("tool_count") != len(tools):
        fail("dictionary.tool_count must match tools length")
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(tools):
        tool = require_object(item, f"dictionary.tools[{index}]")
        tool_id = require_string(tool.get("tool_id"), f"dictionary.tools[{index}].tool_id")
        if tool_id in result:
            fail(f"duplicate tool_id `{tool_id}`")
        stage = require_string(tool.get("stage"), f"{tool_id}.stage")
        if stage not in stages:
            fail(f"{tool_id}.stage uses unknown stage `{stage}`")
        require_bool(tool.get("deterministic"), f"{tool_id}.deterministic")
        require_string(tool.get("execution_lane"), f"{tool_id}.execution_lane")
        result[tool_id] = tool
    return result, stages


def validate_false_claims(value: Any) -> None:
    claims = require_object(value, "no_claims")
    if claims != FALSE_CLAIMS:
        fail("no_claims must exactly match required false claim flags")


def validate_rules(packet: dict[str, Any]) -> None:
    rules = require_object(packet.get("rules"), "rules")
    required = {
        "reference_first": True,
        "morphology_reference_only": True,
        "no_direct_texture_copy": True,
        "no_mesh_copy": True,
        "no_code_compliance_claim": True,
        "blender_tool_choices_declared": True,
        "generated_outputs_in_repo": False,
    }
    if rules != required:
        fail("rules must match the reference-dissection boundary")


def validate_reference(packet: dict[str, Any]) -> None:
    reference = require_object(packet.get("reference"), "reference")
    require_string(reference.get("source_id"), "reference.source_id")
    require_string(reference.get("title"), "reference.title")
    require_string(reference.get("author"), "reference.author")
    require_url(reference.get("source_page_url"), "reference.source_page_url")
    image_url = require_url(reference.get("image_url"), "reference.image_url")
    if Path(image_url).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and image_url.startswith(str(ROOT)):
        fail("reference.image_url must not point to a repo-local image")
    require_string(reference.get("license_or_access_note"), "reference.license_or_access_note")
    require_string(reference.get("access_date"), "reference.access_date")
    if reference.get("use_policy") != "morphology_reference_only":
        fail("reference.use_policy must be morphology_reference_only")


def validate_components(packet: dict[str, Any], geometry_terms: set[str], tool_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    components = require_list(packet.get("components"), "components")
    if require_int(packet.get("component_count"), "component_count", minimum=1) != len(components):
        fail("component_count must match components length")
    seen_component_ids: set[str] = set()
    used_terms: set[str] = set()
    used_tools: set[str] = set()
    for component_index, item in enumerate(components):
        component = require_object(item, f"components[{component_index}]")
        component_id = require_string(component.get("component_id"), f"components[{component_index}].component_id")
        if component_id in seen_component_ids:
            fail(f"duplicate component_id `{component_id}`")
        seen_component_ids.add(component_id)
        require_string(component.get("observed_reference_shape"), f"{component_id}.observed_reference_shape")
        require_string(component.get("generation_role"), f"{component_id}.generation_role")
        for term_index, term in enumerate(require_string_list(component.get("geometry_terms_used"), f"{component_id}.geometry_terms_used")):
            if term not in geometry_terms:
                fail(f"{component_id}.geometry_terms_used[{term_index}] uses unknown geometry term `{term}`")
            used_terms.add(term)
        tools = require_list(component.get("candidate_blender_tools"), f"{component_id}.candidate_blender_tools")
        if not tools:
            fail(f"{component_id}.candidate_blender_tools must not be empty")
        for tool_index, tool_value in enumerate(tools):
            tool_choice = require_object(tool_value, f"{component_id}.candidate_blender_tools[{tool_index}]")
            tool_id = require_string(tool_choice.get("tool_id"), f"{component_id}.candidate_blender_tools[{tool_index}].tool_id")
            if tool_id not in tool_map:
                fail(f"{component_id}.candidate_blender_tools[{tool_index}] uses unknown tool_id `{tool_id}`")
            v0_use = require_string(tool_choice.get("v0_use"), f"{component_id}.candidate_blender_tools[{tool_index}].v0_use")
            if v0_use not in {"preferred", "supporting", "later_reference_only"}:
                fail(f"{component_id}.candidate_blender_tools[{tool_index}].v0_use is invalid")
            if v0_use in {"preferred", "supporting"} and tool_map[tool_id].get("deterministic") is not True:
                fail(f"{component_id}.candidate_blender_tools[{tool_index}] uses nondeterministic v0 tool `{tool_id}`")
            require_string(tool_choice.get("use"), f"{component_id}.candidate_blender_tools[{tool_index}].use")
            used_tools.add(tool_id)
    return {"component_count": len(components), "geometry_term_count": len(used_terms), "tool_count": len(used_tools)}


def validate_tool_sequence(packet: dict[str, Any], tool_map: dict[str, dict[str, Any]], stages: list[str]) -> int:
    stage_indexes = {stage: index for index, stage in enumerate(stages)}
    previous_stage = -1
    used_tools: set[str] = set()
    sequence = require_list(packet.get("blender_tool_sequence_proposal"), "blender_tool_sequence_proposal")
    if not sequence:
        fail("blender_tool_sequence_proposal must not be empty")
    for sequence_index, item in enumerate(sequence):
        step = require_object(item, f"blender_tool_sequence_proposal[{sequence_index}]")
        stage = require_string(step.get("stage"), f"blender_tool_sequence_proposal[{sequence_index}].stage")
        if stage not in stage_indexes:
            fail(f"blender_tool_sequence_proposal[{sequence_index}].stage uses unknown stage `{stage}`")
        if stage_indexes[stage] < previous_stage:
            fail("blender_tool_sequence_proposal must follow dictionary stage order")
        previous_stage = stage_indexes[stage]
        for tool_index, tool_id in enumerate(require_string_list(step.get("tool_ids"), f"blender_tool_sequence_proposal[{sequence_index}].tool_ids")):
            if tool_id not in tool_map:
                fail(f"blender_tool_sequence_proposal[{sequence_index}].tool_ids[{tool_index}] uses unknown tool_id `{tool_id}`")
            if tool_map[tool_id]["stage"] != stage:
                fail(f"blender_tool_sequence_proposal[{sequence_index}].tool_ids[{tool_index}] stage must be `{tool_map[tool_id]['stage']}`")
            if tool_map[tool_id].get("deterministic") is not True:
                fail(f"blender_tool_sequence_proposal[{sequence_index}].tool_ids[{tool_index}] must be deterministic for v0")
            used_tools.add(tool_id)
        require_string(step.get("reason"), f"blender_tool_sequence_proposal[{sequence_index}].reason")
    return len(used_tools)


def validate_future_tools(packet: dict[str, Any], tool_map: dict[str, dict[str, Any]]) -> int:
    future_tools = require_list(packet.get("future_reference_only_tools", []), "future_reference_only_tools")
    for index, item in enumerate(future_tools):
        future = require_object(item, f"future_reference_only_tools[{index}]")
        tool_id = require_string(future.get("tool_id"), f"future_reference_only_tools[{index}].tool_id")
        if tool_id not in tool_map:
            fail(f"future_reference_only_tools[{index}] uses unknown tool_id `{tool_id}`")
        if tool_map[tool_id].get("execution_lane") != "reference_only":
            fail(f"future_reference_only_tools[{index}] must use a reference_only dictionary tool")
        require_string(future.get("use"), f"future_reference_only_tools[{index}].use")
    return len(future_tools)


def validate_packet(packet_path: Path, dictionary_path: Path) -> dict[str, Any]:
    packet = load_json(packet_path)
    dictionary = load_json(dictionary_path)
    geometry_terms = load_geometry_terms()
    tool_map, stages = validate_tool_dictionary(dictionary)
    if packet.get("schema") != PACKET_SCHEMA:
        fail(f"{display_path(packet_path)} schema must be {PACKET_SCHEMA}")
    require_string(packet.get("packet_id"), "packet_id")
    require_string(packet.get("purpose"), "purpose")
    validate_reference(packet)
    require_object(packet.get("asset_target"), "asset_target")
    validate_rules(packet)
    component_summary = validate_components(packet, geometry_terms, tool_map)
    sequence_tool_count = validate_tool_sequence(packet, tool_map, stages)
    future_tool_count = validate_future_tools(packet, tool_map)
    if not require_list(packet.get("review_questions"), "review_questions"):
        fail("review_questions must not be empty")
    require_object(packet.get("next_generation_goal"), "next_generation_goal")
    validate_false_claims(packet.get("no_claims"))
    return {
        "schema": "asset_reference_dissection_packet_validation_result_v0",
        "packet": display_path(packet_path),
        "packet_id": packet["packet_id"],
        "component_count": component_summary["component_count"],
        "geometry_term_count": component_summary["geometry_term_count"],
        "component_tool_count": component_summary["tool_count"],
        "sequence_tool_count": sequence_tool_count,
        "future_reference_only_tool_count": future_tool_count,
        "generated_outputs_created": False,
        "rules": {
            "downloads_reference_images": False,
            "runs_blender": False,
            "creates_media_or_mesh": False,
            "validates_geometry_terms": True,
            "validates_blender_tool_ids": True,
            "requires_deterministic_v0_tools": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate reference-led asset dissection packets.")
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet_path = args.packet if args.packet.is_absolute() else ROOT / args.packet
    dictionary_path = args.dictionary if args.dictionary.is_absolute() else ROOT / args.dictionary
    result = validate_packet(packet_path, dictionary_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS reference dissection packet validation: "
        f"components={result['component_count']} tools={result['component_tool_count']} "
        f"terms={result['geometry_term_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
