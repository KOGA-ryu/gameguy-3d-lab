#!/usr/bin/env python3
"""Validate promoted measured Asset Mill component source recipes.

This validator checks source JSON only. It does not run the old measured
component compilers and does not write generated recipes, reports, receipts,
Blender files, renders, or mesh exports.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "measured_components_v0.json"
DICT_ROOT = ROOT / "geometry_dictionary"
MEASUREMENT_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "extracted_measurements_v0.json"
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


def load_terms() -> dict[str, dict[str, Any]]:
    terms: dict[str, dict[str, Any]] = {}
    for path in sorted(DICT_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = term.get("term_id")
        if not isinstance(term_id, str) or not term_id:
            fail(f"{display_path(path)} missing term_id")
        terms[term_id] = term
    return terms


def load_measurement_ids() -> set[str]:
    measurements = load_json(MEASUREMENT_PATH).get("measurements")
    if not isinstance(measurements, list):
        fail(f"{display_path(MEASUREMENT_PATH)} measurements must be a list")
    ids = set()
    for item in measurements:
        if not isinstance(item, dict) or not isinstance(item.get("measurement_id"), str):
            fail("measurement records must include measurement_id")
        ids.add(item["measurement_id"])
    return ids


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def validate_vector(value: Any, field: str, length: int = 3) -> None:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")


def validate_dimensions(asset: dict[str, Any], field: str) -> None:
    dims = require_object(asset.get("dimensions_m"), f"{field}.dimensions_m")
    for key in ("width", "depth", "height"):
        if not finite_number(dims.get(key)) or float(dims[key]) <= 0.0:
            fail(f"{field}.dimensions_m.{key} must be a positive finite number")


def validate_source_ref(ref: Any, field: str, measurement_ids: set[str]) -> None:
    ref_obj = require_object(ref, field)
    ref_type = require_string(ref_obj.get("ref_type"), f"{field}.ref_type")
    value = require_string(ref_obj.get("ref"), f"{field}.ref")
    if value.startswith("goal/"):
        fail(f"{field}.ref must not reference generated goal output")
    if ref_type == "measurement_id":
        if value not in measurement_ids:
            fail(f"{field}.ref references unknown measurement_id `{value}`")
    elif ref_type in {"local_ratio_doc", "local_policy_doc", "local_link_file"}:
        if not (ROOT / value).exists():
            fail(f"{field}.ref references missing local file `{value}`")
    elif ref_type == "source_bundle_version":
        if value not in {"measured_components_v0.v1_assets", "measured_components_v0.v2_assets"}:
            fail(f"{field}.ref has unknown source bundle reference `{value}`")
    else:
        fail(f"{field}.ref_type has unsupported value `{ref_type}`")


def validate_proof_primitive(part: Any, field: str) -> None:
    item = require_object(part, field)
    primitive = require_string(item.get("primitive"), f"{field}.primitive")
    require_string(item.get("name"), f"{field}.name")
    if primitive == "cube":
        validate_vector(item.get("location_m"), f"{field}.location_m")
        validate_vector(item.get("dimensions_m"), f"{field}.dimensions_m")
        if any(float(value) <= 0.0 for value in item["dimensions_m"]):
            fail(f"{field}.dimensions_m values must be positive")
    elif primitive == "cylinder":
        validate_vector(item.get("location_m"), f"{field}.location_m")
        if not finite_number(item.get("radius_m")) or float(item["radius_m"]) <= 0.0:
            fail(f"{field}.radius_m must be positive")
        if not finite_number(item.get("depth_m")) or float(item["depth_m"]) <= 0.0:
            fail(f"{field}.depth_m must be positive")
        if not isinstance(item.get("vertices"), int) or item["vertices"] < 3:
            fail(f"{field}.vertices must be an integer >= 3")
    elif primitive == "curve":
        for key in ("span_m", "spring_z_m", "rise_m", "y_m", "bevel_depth_m"):
            if not finite_number(item.get(key)):
                fail(f"{field}.{key} must be a finite number")
        if float(item["span_m"]) <= 0.0 or float(item["bevel_depth_m"]) <= 0.0:
            fail(f"{field} curve span and bevel must be positive")
    else:
        fail(f"{field}.primitive unsupported: {primitive}")


def validate_asset(asset: Any, index: int, terms: dict[str, dict[str, Any]], measurement_ids: set[str]) -> tuple[str, str]:
    item = require_object(asset, f"assets[{index}]")
    asset_id = require_string(item.get("asset_id"), f"assets[{index}].asset_id")
    source_version = require_string(item.get("source_version"), f"{asset_id}.source_version")
    if source_version not in {"v1", "v2"}:
        fail(f"{asset_id}.source_version must be v1 or v2")
    expected_schema = f"asset_mill_measured_component_recipe_{source_version}"
    if item.get("schema") != expected_schema:
        fail(f"{asset_id}.schema must be {expected_schema}")
    if require_string(item.get("source_script"), f"{asset_id}.source_script") not in {
        "scripts/compile_asset_mill_measured_components_v1.py",
        "scripts/compile_asset_mill_measured_components_v2.py",
    }:
        fail(f"{asset_id}.source_script must reference an original measured compiler")
    validate_dimensions(item, asset_id)
    if item.get("bounds_m") != bounds_from_dimensions(item["dimensions_m"]):
        fail(f"{asset_id}.bounds_m must match dimensions_m")
    for ref_index, ref in enumerate(require_list(item.get("source_measurement_refs"), f"{asset_id}.source_measurement_refs")):
        validate_source_ref(ref, f"{asset_id}.source_measurement_refs[{ref_index}]", measurement_ids)
    if not item["source_measurement_refs"]:
        fail(f"{asset_id}.source_measurement_refs must not be empty")
    known_terms = set(terms)
    for term_field in ("geometry_terms_used", "profile_terms", "operations"):
        values = require_list(item.get(term_field), f"{asset_id}.{term_field}")
        if not values:
            fail(f"{asset_id}.{term_field} must not be empty")
        unknown = sorted(set(require_string(value, f"{asset_id}.{term_field}[]") for value in values) - known_terms)
        if unknown:
            fail(f"{asset_id}.{term_field} references unknown geometry terms: {unknown}")
    semantic_terms = {term_id for term_id, term in terms.items() if term["category"] == "semantic_geometry"}
    semantic_roles = require_list(item.get("semantic_roles"), f"{asset_id}.semantic_roles")
    unknown_semantics = sorted(set(require_string(value, f"{asset_id}.semantic_roles[]") for value in semantic_roles) - semantic_terms)
    if unknown_semantics:
        fail(f"{asset_id}.semantic_roles references unknown semantic roles: {unknown_semantics}")
    connector_terms = {term_id for term_id, term in terms.items() if term["category"] == "connector"}
    sockets = require_list(item.get("sockets"), f"{asset_id}.sockets")
    if not sockets:
        fail(f"{asset_id}.sockets must not be empty")
    for socket_index, socket in enumerate(sockets):
        socket_obj = require_object(socket, f"{asset_id}.sockets[{socket_index}]")
        require_string(socket_obj.get("socket_id"), f"{asset_id}.sockets[{socket_index}].socket_id")
        connector_term = require_string(socket_obj.get("connector_term"), f"{asset_id}.sockets[{socket_index}].connector_term")
        if connector_term not in connector_terms:
            fail(f"{asset_id}.sockets[{socket_index}].connector_term is unknown: {connector_term}")
        validate_vector(socket_obj.get("position_m"), f"{asset_id}.sockets[{socket_index}].position_m")
        validate_vector(socket_obj.get("direction"), f"{asset_id}.sockets[{socket_index}].direction")
        require_string(socket_obj.get("role"), f"{asset_id}.sockets[{socket_index}].role")
    proof_primitives = require_list(item.get("proof_primitives"), f"{asset_id}.proof_primitives")
    if not proof_primitives:
        fail(f"{asset_id}.proof_primitives must not be empty")
    for part_index, part in enumerate(proof_primitives):
        validate_proof_primitive(part, f"{asset_id}.proof_primitives[{part_index}]")
    if item.get("no_claims") != {key: FALSE_CLAIMS[key] for key in ("production_approval", "structural_safety", "fabrication_ready", "gym_museum_approval", "historical_accuracy")}:
        fail(f"{asset_id}.no_claims must match required measured component false claims")
    return asset_id, source_version


def bounds_from_dimensions(dimensions: dict[str, Any]) -> dict[str, list[float]]:
    width = float(dimensions["width"])
    depth = float(dimensions["depth"])
    height = float(dimensions["height"])
    return {
        "min": [round(-width * 0.5, 6), round(-depth * 0.5, 6), 0.0],
        "max": [round(width * 0.5, 6), round(depth * 0.5, 6), round(height, 6)],
    }


def validate_bundle(path: Path) -> dict[str, Any]:
    bundle = load_json(path)
    if bundle.get("schema") != "asset_mill_measured_component_bundle_v0":
        fail("bundle schema must be asset_mill_measured_component_bundle_v0")
    if bundle.get("bundle_id") != "measured_components_v0":
        fail("bundle_id must be measured_components_v0")
    if bundle.get("no_claims") != FALSE_CLAIMS:
        fail("bundle no_claims must match required false claims")
    terms = load_terms()
    measurement_ids = load_measurement_ids()
    assets = require_list(bundle.get("assets"), "assets")
    seen: set[str] = set()
    version_counts = {"v1": 0, "v2": 0}
    for index, asset in enumerate(assets):
        asset_id, source_version = validate_asset(asset, index, terms, measurement_ids)
        if asset_id in seen:
            fail(f"duplicate measured component asset_id: {asset_id}")
        seen.add(asset_id)
        version_counts[source_version] += 1
    if bundle.get("asset_count") != len(assets):
        fail("asset_count must match assets length")
    if bundle.get("v1_asset_count") != version_counts["v1"]:
        fail("v1_asset_count must match v1 assets")
    if bundle.get("v2_asset_count") != version_counts["v2"]:
        fail("v2_asset_count must match v2 assets")
    return {
        "schema": "measured_component_source_validation_result_v0",
        "status": "pass",
        "bundle_path": display_path(path),
        "asset_count": len(assets),
        "v1_asset_count": version_counts["v1"],
        "v2_asset_count": version_counts["v2"],
        "generated_outputs_created": False,
        "rules": {
            "no_goal_references": True,
            "geometry_terms_checked": True,
            "measurement_refs_checked": True,
            "proof_primitives_are_preview_hints_only": True,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate promoted measured component source recipes.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--json-report", type=Path, help="Optional path for validation report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    result = validate_bundle(bundle_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS measured component source validation: "
        f"assets={result['asset_count']} v1={result['v1_asset_count']} v2={result['v2_asset_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
