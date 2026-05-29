#!/usr/bin/env python3
"""Validate connector source recipes and placement policy.

This validator checks source JSON only. It does not run connector generation,
Blender, renderers, or mesh output.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_ROOT = ROOT / "data" / "architecture" / "assets" / "connectors"
MANIFEST_PATH = CONNECTOR_ROOT / "connector_asset_manifest_v0.json"
POLICY_PATH = CONNECTOR_ROOT / "connector_placement_policy_v0.json"

REQUIRED_CONNECTION_TYPES = (
    "road_threshold",
    "flat_pathway",
    "ramp_pathway",
    "stepped_pathway",
    "bridge_link",
)

REQUIRED_CONNECTOR_IDS = (
    "measured_pathway_slab_unit_v1",
    "measured_threshold_landing_v1",
    "measured_ramp_pathway_unit_v1",
    "measured_stepped_pathway_unit_v1",
    "measured_bridge_deck_unit_v1",
    "measured_bridge_abutment_v1",
    "measured_bridge_rail_unit_v1",
    "measured_retaining_wall_unit_v1",
    "measured_curb_edge_unit_v1",
)

REQUIRED_RECIPE_FIELDS = (
    "schema",
    "asset_id",
    "dimensions_m",
    "sockets",
    "semantic_roles",
    "proof_primitives",
    "no_claims",
)


@dataclass
class ValidationIssue:
    path: str
    field: str
    message: str
    asset_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "path": self.path,
            "field": self.field,
            "message": self.message,
        }
        if self.asset_id:
            data["asset_id"] = self.asset_id
        return data


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def issue(path: Path, field: str, message: str, *, asset_id: str | None = None) -> ValidationIssue:
    return ValidationIssue(display_path(path), field, message, asset_id)


def load_json_object(path: Path, errors: list[ValidationIssue], *, label: str) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(issue(path, "$", f"{label} JSON is missing"))
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append(issue(path, "$", f"{label} JSON is malformed: {exc.msg} at line {exc.lineno}, column {exc.colno}"))
        return None
    if not isinstance(data, dict):
        errors.append(issue(path, "$", f"{label} JSON must contain an object"))
        return None
    return data


def require_object(path: Path, field: str, value: Any, errors: list[ValidationIssue], *, asset_id: str | None = None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(issue(path, field, "field must be an object", asset_id=asset_id))
        return None
    return value


def require_string(path: Path, field: str, value: Any, errors: list[ValidationIssue], *, asset_id: str | None = None) -> str | None:
    if not isinstance(value, str) or not value:
        errors.append(issue(path, field, "field must be a non-empty string", asset_id=asset_id))
        return None
    return value


def require_list(path: Path, field: str, value: Any, errors: list[ValidationIssue], *, asset_id: str | None = None) -> list[Any] | None:
    if not isinstance(value, list):
        errors.append(issue(path, field, "field must be a list", asset_id=asset_id))
        return None
    return value


def validate_dimensions(path: Path, asset_id: str, dimensions: Any, errors: list[ValidationIssue]) -> None:
    data = require_object(path, "dimensions_m", dimensions, errors, asset_id=asset_id)
    if data is None:
        return
    for key in ("width", "depth", "height"):
        value = data.get(key)
        if not isinstance(value, (int, float)) or float(value) <= 0.0:
            errors.append(issue(path, f"dimensions_m.{key}", "dimension must be a positive number", asset_id=asset_id))


def validate_recipe(path: Path, expected_asset_id: str, errors: list[ValidationIssue]) -> dict[str, Any] | None:
    recipe = load_json_object(path, errors, label=f"recipe {expected_asset_id}")
    if recipe is None:
        return None

    for field in REQUIRED_RECIPE_FIELDS:
        if field not in recipe:
            errors.append(issue(path, field, "recipe is missing required field", asset_id=expected_asset_id))

    actual_asset_id = recipe.get("asset_id")
    if actual_asset_id != expected_asset_id:
        errors.append(issue(path, "asset_id", f"recipe asset_id `{actual_asset_id}` does not match manifest asset_id `{expected_asset_id}`", asset_id=expected_asset_id))

    if recipe.get("schema") != "connector_asset_component_recipe_v0":
        errors.append(issue(path, "schema", "recipe schema must be connector_asset_component_recipe_v0", asset_id=expected_asset_id))

    validate_dimensions(path, expected_asset_id, recipe.get("dimensions_m"), errors)

    sockets = require_list(path, "sockets", recipe.get("sockets"), errors, asset_id=expected_asset_id)
    if sockets is not None and not sockets:
        errors.append(issue(path, "sockets", "recipe must define at least one socket", asset_id=expected_asset_id))

    semantic_roles = require_list(path, "semantic_roles", recipe.get("semantic_roles"), errors, asset_id=expected_asset_id)
    if semantic_roles is not None and not semantic_roles:
        errors.append(issue(path, "semantic_roles", "recipe must define at least one semantic role", asset_id=expected_asset_id))

    proof_primitives = require_list(path, "proof_primitives", recipe.get("proof_primitives"), errors, asset_id=expected_asset_id)
    if proof_primitives is not None and not proof_primitives:
        errors.append(issue(path, "proof_primitives", "recipe must define at least one proof primitive record", asset_id=expected_asset_id))

    no_claims = require_object(path, "no_claims", recipe.get("no_claims"), errors, asset_id=expected_asset_id)
    if no_claims is not None:
        for key in ("production_approval", "structural_safety", "fabrication_ready", "historical_accuracy"):
            if no_claims.get(key) is not False:
                errors.append(issue(path, f"no_claims.{key}", "no-claim flag must be false", asset_id=expected_asset_id))

    return recipe


def load_manifest(errors: list[ValidationIssue]) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
    manifest = load_json_object(MANIFEST_PATH, errors, label="connector manifest")
    if manifest is None:
        return {}, None

    if manifest.get("schema") != "connector_asset_manifest_v0":
        errors.append(issue(MANIFEST_PATH, "schema", "connector manifest schema must be connector_asset_manifest_v0"))

    rows = require_list(MANIFEST_PATH, "assets", manifest.get("assets"), errors)
    if rows is None:
        return {}, manifest

    recipes: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for index, row in enumerate(rows):
        row_field = f"assets[{index}]"
        row_obj = require_object(MANIFEST_PATH, row_field, row, errors)
        if row_obj is None:
            continue
        asset_id = require_string(MANIFEST_PATH, f"{row_field}.asset_id", row_obj.get("asset_id"), errors)
        recipe_path_value = require_string(MANIFEST_PATH, f"{row_field}.recipe_path", row_obj.get("recipe_path"), errors, asset_id=asset_id)
        if asset_id is None or recipe_path_value is None:
            continue
        if asset_id in seen:
            errors.append(issue(MANIFEST_PATH, f"{row_field}.asset_id", f"duplicate connector asset ID `{asset_id}`", asset_id=asset_id))
            continue
        seen.add(asset_id)

        recipe_path = ROOT / recipe_path_value
        if not recipe_path.exists():
            errors.append(issue(MANIFEST_PATH, f"{row_field}.recipe_path", f"manifest-listed recipe file does not exist: {recipe_path_value}", asset_id=asset_id))
            continue
        recipe = validate_recipe(recipe_path, asset_id, errors)
        if recipe is not None:
            recipes[asset_id] = recipe

    for asset_id in REQUIRED_CONNECTOR_IDS:
        if asset_id not in seen:
            errors.append(issue(MANIFEST_PATH, "assets", f"required connector asset ID is missing: {asset_id}", asset_id=asset_id))

    if isinstance(manifest.get("asset_count"), int) and manifest["asset_count"] != len(rows):
        errors.append(issue(MANIFEST_PATH, "asset_count", f"asset_count is {manifest['asset_count']} but assets list contains {len(rows)}"))

    return recipes, manifest


def iter_policy_asset_refs(value: Any, prefix: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            field = f"{prefix}.{key}" if prefix else key
            if key == "asset_id" and isinstance(item, str):
                refs.append((field, item))
            else:
                refs.extend(iter_policy_asset_refs(item, field))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            refs.extend(iter_policy_asset_refs(item, f"{prefix}[{index}]"))
    return refs


def validate_policy(errors: list[ValidationIssue], known_asset_ids: set[str]) -> dict[str, Any] | None:
    policy = load_json_object(POLICY_PATH, errors, label="connector placement policy")
    if policy is None:
        return None

    if policy.get("schema") != "connector_placement_policy_v0":
        errors.append(issue(POLICY_PATH, "schema", "placement policy schema must be connector_placement_policy_v0"))

    expected_types = require_list(POLICY_PATH, "expected_connection_types", policy.get("expected_connection_types"), errors)
    if expected_types is not None:
        for connection_type in REQUIRED_CONNECTION_TYPES:
            if connection_type not in expected_types:
                errors.append(issue(POLICY_PATH, "expected_connection_types", f"required connection type is missing: {connection_type}"))

    rules = require_object(POLICY_PATH, "connection_type_rules", policy.get("connection_type_rules"), errors)
    if rules is None:
        return policy

    for connection_type in REQUIRED_CONNECTION_TYPES:
        if connection_type not in rules:
            errors.append(issue(POLICY_PATH, f"connection_type_rules.{connection_type}", "connection type has no placement rule"))
        elif not isinstance(rules[connection_type], dict):
            errors.append(issue(POLICY_PATH, f"connection_type_rules.{connection_type}", "placement rule must be an object"))

    for field, asset_id in iter_policy_asset_refs(rules, "connection_type_rules"):
        if asset_id not in known_asset_ids:
            errors.append(issue(POLICY_PATH, field, f"placement policy references unknown connector asset ID `{asset_id}`", asset_id=asset_id))

    bridge = rules.get("bridge_link")
    if isinstance(bridge, dict):
        for role in ("deck", "rail", "abutment"):
            value = bridge.get(role)
            if not isinstance(value, dict):
                errors.append(issue(POLICY_PATH, f"connection_type_rules.bridge_link.{role}", "bridge rule must define this object"))
            elif "asset_id" not in value:
                errors.append(issue(POLICY_PATH, f"connection_type_rules.bridge_link.{role}.asset_id", "bridge rule lacks required asset_id reference"))

    return policy


def run_validation() -> dict[str, Any]:
    errors: list[ValidationIssue] = []
    recipes, manifest = load_manifest(errors)
    policy = validate_policy(errors, set(recipes))

    result = {
        "schema": "connector_source_validation_result_v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "fail",
        "manifest_path": display_path(MANIFEST_PATH),
        "placement_policy_path": display_path(POLICY_PATH),
        "required_connector_ids": list(REQUIRED_CONNECTOR_IDS),
        "required_connection_types": list(REQUIRED_CONNECTION_TYPES),
        "manifest_loaded": manifest is not None,
        "placement_policy_loaded": policy is not None,
        "recipe_count_loaded": len(recipes),
        "connector_ids_loaded": sorted(recipes),
        "errors": [item.as_dict() for item in errors],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate connector source manifest, recipes, and placement policy.")
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    args = parser.parse_args()

    result = run_validation()
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if result["status"] == "pass":
        print(
            "PASS connector source validation: "
            f"{result['recipe_count_loaded']} recipes, "
            f"{len(result['required_connection_types'])} required connection types"
        )
        return 0

    print(f"FAIL connector source validation: {len(result['errors'])} error(s)", file=sys.stderr)
    for item in result["errors"]:
        asset = f" asset_id={item['asset_id']}" if "asset_id" in item else ""
        print(f"- {item['path']}::{item['field']}{asset}: {item['message']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
