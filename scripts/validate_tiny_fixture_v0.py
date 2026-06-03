#!/usr/bin/env python3
"""Validate the canonical tiny architecture source fixture.

This checks source JSON only. It does not run compilers, Blender, renderers,
mesh exporters, movement simulation, or pathfinding.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "data" / "architecture" / "test_fixtures" / "tiny_map_building_connector_fixture_v0.json"
DEFAULT_MANIFEST = ROOT / "data" / "architecture" / "assets" / "connectors" / "connector_asset_manifest_v0.json"
DEFAULT_POLICY = ROOT / "data" / "architecture" / "assets" / "connectors" / "connector_placement_policy_v0.json"

FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
    "movement_or_pathfinding_correctness": False,
}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    field: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "field": self.field, "message": self.message}


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def issue(path: Path, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(display_path(path), field, message)


def load_json_object(path: Path, errors: list[ValidationIssue], label: str) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(issue(path, "$", f"{label} JSON is missing"))
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(issue(path, "$", f"{label} JSON is malformed: {exc.msg} at line {exc.lineno}, column {exc.colno}"))
        return None
    if not isinstance(data, dict):
        errors.append(issue(path, "$", f"{label} JSON must contain an object"))
        return None
    return data


def require_list(path: Path, field: str, value: Any, errors: list[ValidationIssue]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(issue(path, field, "field must be a list"))
        return []
    return value


def require_object(path: Path, field: str, value: Any, errors: list[ValidationIssue]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(issue(path, field, "field must be an object"))
        return None
    return value


def require_string(path: Path, field: str, value: Any, errors: list[ValidationIssue]) -> str | None:
    if not isinstance(value, str) or not value:
        errors.append(issue(path, field, "field must be a non-empty string"))
        return None
    return value


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_vector(path: Path, field: str, value: Any, errors: list[ValidationIssue], length: int = 3) -> None:
    if not isinstance(value, list) or len(value) != length:
        errors.append(issue(path, field, f"field must be a {length}-number list"))
        return
    for index, item in enumerate(value):
        if not is_finite_number(item):
            errors.append(issue(path, f"{field}[{index}]", "vector item must be a finite number"))


def load_manifest_asset_ids(path: Path, errors: list[ValidationIssue]) -> set[str]:
    manifest = load_json_object(path, errors, "connector manifest")
    if manifest is None:
        return set()
    if manifest.get("schema") != "connector_asset_manifest_v0":
        errors.append(issue(path, "schema", "manifest schema must be connector_asset_manifest_v0"))
    asset_ids: set[str] = set()
    for index, row in enumerate(require_list(path, "assets", manifest.get("assets"), errors)):
        row_obj = require_object(path, f"assets[{index}]", row, errors)
        if row_obj is None:
            continue
        asset_id = require_string(path, f"assets[{index}].asset_id", row_obj.get("asset_id"), errors)
        if asset_id:
            if asset_id in asset_ids:
                errors.append(issue(path, f"assets[{index}].asset_id", f"duplicate connector asset ID `{asset_id}`"))
            asset_ids.add(asset_id)
    if isinstance(manifest.get("asset_count"), int) and manifest["asset_count"] != len(asset_ids):
        errors.append(issue(path, "asset_count", "asset_count must match unique connector asset IDs"))
    return asset_ids


def load_policy_connection_types(path: Path, errors: list[ValidationIssue]) -> set[str]:
    policy = load_json_object(path, errors, "connector placement policy")
    if policy is None:
        return set()
    if policy.get("schema") != "connector_placement_policy_v0":
        errors.append(issue(path, "schema", "placement policy schema must be connector_placement_policy_v0"))
    rules = require_object(path, "connection_type_rules", policy.get("connection_type_rules"), errors)
    if rules is None:
        return set()
    expected = require_list(path, "expected_connection_types", policy.get("expected_connection_types"), errors)
    connection_types = set(rules)
    for connection_type in expected:
        if isinstance(connection_type, str) and connection_type not in connection_types:
            errors.append(issue(path, "expected_connection_types", f"expected connection type lacks a rule: {connection_type}"))
    return connection_types


def validate_cells(path: Path, fixture: dict[str, Any], errors: list[ValidationIssue]) -> dict[str, dict[str, Any]]:
    cells_by_id: dict[str, dict[str, Any]] = {}
    coords: set[tuple[int, int]] = set()
    cells = require_list(path, "cells", fixture.get("cells"), errors)
    if len(cells) >= 12:
        errors.append(issue(path, "cells", "tiny fixture must contain fewer than 12 cells"))

    layout = require_object(path, "cell_layout", fixture.get("cell_layout"), errors)
    if layout is not None:
        if layout.get("grid") != "axial_hex":
            errors.append(issue(path, "cell_layout.grid", "grid must be axial_hex"))
        if layout.get("cell_count") != len(cells):
            errors.append(issue(path, "cell_layout.cell_count", "cell_count must match cells length"))
        if not is_finite_number(layout.get("hex_radius_m")) or float(layout["hex_radius_m"]) <= 0.0:
            errors.append(issue(path, "cell_layout.hex_radius_m", "hex radius must be a positive finite number"))

    for index, cell in enumerate(cells):
        field = f"cells[{index}]"
        cell_obj = require_object(path, field, cell, errors)
        if cell_obj is None:
            continue
        cell_id = require_string(path, f"{field}.cell_id", cell_obj.get("cell_id"), errors)
        q = cell_obj.get("q")
        r = cell_obj.get("r")
        if not isinstance(q, int) or isinstance(q, bool):
            errors.append(issue(path, f"{field}.q", "q must be an integer"))
        if not isinstance(r, int) or isinstance(r, bool):
            errors.append(issue(path, f"{field}.r", "r must be an integer"))
        if not is_finite_number(cell_obj.get("height_m")):
            errors.append(issue(path, f"{field}.height_m", "height_m must be a finite number"))
        require_string(path, f"{field}.role", cell_obj.get("role"), errors)
        if cell_id:
            if cell_id in cells_by_id:
                errors.append(issue(path, f"{field}.cell_id", f"duplicate cell ID `{cell_id}`"))
            cells_by_id[cell_id] = cell_obj
        if isinstance(q, int) and isinstance(r, int):
            coord = (q, r)
            if coord in coords:
                errors.append(issue(path, field, f"duplicate axial coordinate {coord}"))
            coords.add(coord)
    return cells_by_id


def collect_plugs(path: Path, fixture: dict[str, Any], cells_by_id: dict[str, dict[str, Any]], errors: list[ValidationIssue]) -> set[str]:
    plug_ids: set[str] = set()
    for building_index, building in enumerate(require_list(path, "buildings", fixture.get("buildings"), errors)):
        building_field = f"buildings[{building_index}]"
        building_obj = require_object(path, building_field, building, errors)
        if building_obj is None:
            continue
        require_string(path, f"{building_field}.building_id", building_obj.get("building_id"), errors)
        plot_cell = require_string(path, f"{building_field}.plot_cell", building_obj.get("plot_cell"), errors)
        if plot_cell and plot_cell not in cells_by_id:
            errors.append(issue(path, f"{building_field}.plot_cell", f"unknown cell ID `{plot_cell}`"))
        for cell_id in require_list(path, f"{building_field}.footprint_cells", building_obj.get("footprint_cells"), errors):
            if not isinstance(cell_id, str) or cell_id not in cells_by_id:
                errors.append(issue(path, f"{building_field}.footprint_cells", f"unknown footprint cell ID `{cell_id}`"))
        for plug_index, plug in enumerate(require_list(path, f"{building_field}.plugs", building_obj.get("plugs"), errors)):
            validate_plug(path, f"{building_field}.plugs[{plug_index}]", plug, cells_by_id, plug_ids, errors)

    for plug_index, plug in enumerate(require_list(path, "road_plugs", fixture.get("road_plugs"), errors)):
        validate_plug(path, f"road_plugs[{plug_index}]", plug, cells_by_id, plug_ids, errors)

    return plug_ids


def validate_plug(
    path: Path,
    field: str,
    plug: Any,
    cells_by_id: dict[str, dict[str, Any]],
    plug_ids: set[str],
    errors: list[ValidationIssue],
) -> None:
    plug_obj = require_object(path, field, plug, errors)
    if plug_obj is None:
        return
    plug_id = require_string(path, f"{field}.plug_id", plug_obj.get("plug_id"), errors)
    for key in ("owner_id", "owner_type", "plug_type"):
        require_string(path, f"{field}.{key}", plug_obj.get(key), errors)
    cell_id = require_string(path, f"{field}.cell_id", plug_obj.get("cell_id"), errors)
    if cell_id and cell_id not in cells_by_id:
        errors.append(issue(path, f"{field}.cell_id", f"unknown cell ID `{cell_id}`"))
    validate_vector(path, f"{field}.position_m", plug_obj.get("position_m"), errors)
    validate_vector(path, f"{field}.direction", plug_obj.get("direction"), errors)
    for key in ("width_m", "clearance_m"):
        if not is_finite_number(plug_obj.get(key)) or float(plug_obj[key]) <= 0.0:
            errors.append(issue(path, f"{field}.{key}", "field must be a positive finite number"))
    if not require_list(path, f"{field}.allowed_connection_types", plug_obj.get("allowed_connection_types"), errors):
        errors.append(issue(path, f"{field}.allowed_connection_types", "plug must allow at least one connection type"))
    if plug_id:
        if plug_id in plug_ids:
            errors.append(issue(path, f"{field}.plug_id", f"duplicate plug ID `{plug_id}`"))
        plug_ids.add(plug_id)


def validate_height_changes(path: Path, fixture: dict[str, Any], cells_by_id: dict[str, dict[str, Any]], errors: list[ValidationIssue]) -> None:
    changes = require_list(path, "terrain_height_changes", fixture.get("terrain_height_changes"), errors)
    if not changes:
        errors.append(issue(path, "terrain_height_changes", "fixture must include at least one explicit height change"))
    for index, change in enumerate(changes):
        field = f"terrain_height_changes[{index}]"
        change_obj = require_object(path, field, change, errors)
        if change_obj is None:
            continue
        require_string(path, f"{field}.height_change_id", change_obj.get("height_change_id"), errors)
        from_cell = require_string(path, f"{field}.from_cell", change_obj.get("from_cell"), errors)
        to_cell = require_string(path, f"{field}.to_cell", change_obj.get("to_cell"), errors)
        require_string(path, f"{field}.intended_connection_type", change_obj.get("intended_connection_type"), errors)
        if not is_finite_number(change_obj.get("delta_m")):
            errors.append(issue(path, f"{field}.delta_m", "delta_m must be a finite number"))
            continue
        if from_cell in cells_by_id and to_cell in cells_by_id:
            expected = round(float(cells_by_id[to_cell]["height_m"]) - float(cells_by_id[from_cell]["height_m"]), 6)
            actual = round(float(change_obj["delta_m"]), 6)
            if actual != expected:
                errors.append(issue(path, f"{field}.delta_m", f"delta_m is {actual} but cell heights imply {expected}"))


def validate_segments(
    path: Path,
    fixture: dict[str, Any],
    cells_by_id: dict[str, dict[str, Any]],
    plug_ids: set[str],
    connector_asset_ids: set[str],
    connection_types: set[str],
    errors: list[ValidationIssue],
) -> None:
    segments = require_list(path, "connector_path_segments", fixture.get("connector_path_segments"), errors)
    if not segments:
        errors.append(issue(path, "connector_path_segments", "fixture must include at least one connector path segment"))
    for index, segment in enumerate(segments):
        field = f"connector_path_segments[{index}]"
        segment_obj = require_object(path, field, segment, errors)
        if segment_obj is None:
            continue
        require_string(path, f"{field}.segment_id", segment_obj.get("segment_id"), errors)
        from_plug = require_string(path, f"{field}.from_plug", segment_obj.get("from_plug"), errors)
        to_plug = require_string(path, f"{field}.to_plug", segment_obj.get("to_plug"), errors)
        if from_plug and from_plug not in plug_ids:
            errors.append(issue(path, f"{field}.from_plug", f"unknown plug ID `{from_plug}`"))
        if to_plug and to_plug not in plug_ids:
            errors.append(issue(path, f"{field}.to_plug", f"unknown plug ID `{to_plug}`"))
        connection_type = require_string(path, f"{field}.connection_type", segment_obj.get("connection_type"), errors)
        if connection_type and connection_type not in connection_types:
            errors.append(issue(path, f"{field}.connection_type", f"unknown policy connection type `{connection_type}`"))
        connector_asset_id = require_string(path, f"{field}.connector_asset_id", segment_obj.get("connector_asset_id"), errors)
        if connector_asset_id and connector_asset_id not in connector_asset_ids:
            errors.append(issue(path, f"{field}.connector_asset_id", f"unknown connector asset ID `{connector_asset_id}`"))
        if segment_obj.get("connector_manifest_ref") != display_path(DEFAULT_MANIFEST):
            errors.append(issue(path, f"{field}.connector_manifest_ref", "segment must reference the source connector manifest"))
        if segment_obj.get("placement_policy_ref") != display_path(DEFAULT_POLICY):
            errors.append(issue(path, f"{field}.placement_policy_ref", "segment must reference the source placement policy"))
        if segment_obj.get("no_silent_scaling") is not True:
            errors.append(issue(path, f"{field}.no_silent_scaling", "segment must explicitly forbid silent scaling"))
        route_cells = require_list(path, f"{field}.route_cells", segment_obj.get("route_cells"), errors)
        if len(route_cells) < 2:
            errors.append(issue(path, f"{field}.route_cells", "route must contain at least two cells"))
        for cell_id in route_cells:
            if not isinstance(cell_id, str) or cell_id not in cells_by_id:
                errors.append(issue(path, f"{field}.route_cells", f"unknown route cell ID `{cell_id}`"))


def validate_fixture(path: Path, manifest_path: Path = DEFAULT_MANIFEST, policy_path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    errors: list[ValidationIssue] = []
    fixture = load_json_object(path, errors, "tiny fixture")
    connector_asset_ids = load_manifest_asset_ids(manifest_path, errors)
    connection_types = load_policy_connection_types(policy_path, errors)

    cells_by_id: dict[str, dict[str, Any]] = {}
    plug_ids: set[str] = set()
    if fixture is not None:
        if fixture.get("schema") != "tiny_map_building_connector_fixture_v0":
            errors.append(issue(path, "schema", "fixture schema must be tiny_map_building_connector_fixture_v0"))
        if fixture.get("fixture_id") != "tiny_map_building_connector_fixture_v0":
            errors.append(issue(path, "fixture_id", "fixture_id must be tiny_map_building_connector_fixture_v0"))
        if fixture.get("source_only") is not True:
            errors.append(issue(path, "source_only", "fixture must be marked source_only"))
        if fixture.get("deterministic_ids") is not True:
            errors.append(issue(path, "deterministic_ids", "fixture must require deterministic IDs"))
        if fixture.get("no_claims") != FALSE_CLAIMS:
            errors.append(issue(path, "no_claims", "fixture no_claims must exactly match required false flags"))
        cells_by_id = validate_cells(path, fixture, errors)
        validate_height_changes(path, fixture, cells_by_id, errors)
        plug_ids = collect_plugs(path, fixture, cells_by_id, errors)
        validate_segments(path, fixture, cells_by_id, plug_ids, connector_asset_ids, connection_types, errors)

    return {
        "schema": "tiny_fixture_validation_result_v0",
        "status": "pass" if not errors else "fail",
        "fixture_path": display_path(path),
        "connector_manifest_path": display_path(manifest_path),
        "placement_policy_path": display_path(policy_path),
        "cell_count": len(cells_by_id),
        "plug_count": len(plug_ids),
        "connector_asset_count": len(connector_asset_ids),
        "connection_type_count": len(connection_types),
        "source_only": True,
        "generated_outputs_created": False,
        "errors": [item.as_dict() for item in errors],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the canonical tiny architecture fixture.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    args = parser.parse_args()

    fixture = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
    manifest = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    policy = args.policy if args.policy.is_absolute() else ROOT / args.policy
    result = validate_fixture(fixture, manifest, policy)

    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if result["status"] == "pass":
        print(
            "PASS tiny fixture validation: "
            f"{result['cell_count']} cells, {result['plug_count']} plugs, "
            f"{result['connection_type_count']} policy connection types"
        )
        return 0

    print(f"FAIL tiny fixture validation: {len(result['errors'])} error(s)", file=sys.stderr)
    for item in result["errors"]:
        print(f"- {item['path']}::{item['field']}: {item['message']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
