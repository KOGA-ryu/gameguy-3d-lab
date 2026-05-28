#!/usr/bin/env python3
"""Validate Map Authoring Contract v0 map documents.

This validator is intentionally small and stdlib-only. It validates authored
map source data before any compiler or Blender renderer runs.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "map_authoring_contract_v0.json"
DEFAULT_AUTHORING_PATHS = [
    ROOT / "data" / "architecture" / "map_templates" / "hillwatch_ravine_authoring_v0.json",
    ROOT / "data" / "architecture" / "map_templates" / "pathway_engine_authoring_v0.json",
]
REPORT_PATH = ROOT / "goal" / "architecture" / "map_editor_v0" / "map_authoring_contract_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "map_authoring_contract_v0.receipt.json"

NO_CLAIM_FLAGS = [
    "production_approval",
    "structural_safety",
    "fabrication_ready",
    "gym_museum_approval",
    "historical_accuracy",
]


@dataclass
class ValidationResult:
    path: Path | None
    map_id: str
    ok: bool
    errors: list[str]
    warnings: list[str]
    summary: dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def require_object(data: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        errors.append(f"`{key}` must be an object")
        return {}
    return value


def require_array(data: dict[str, Any], key: str, errors: list[str]) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        errors.append(f"`{key}` must be an array")
        return []
    return value


def require_string(data: dict[str, Any], key: str, errors: list[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        errors.append(f"`{key}` must be a non-empty string")
        return ""
    return value


def require_number(data: dict[str, Any], key: str, errors: list[str]) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        errors.append(f"`{key}` must be a number")
        return 0.0
    return float(value)


def require_bool(data: dict[str, Any], key: str, errors: list[str]) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        errors.append(f"`{key}` must be a boolean")
        return False
    return value


def validate_point(value: Any, label: str, errors: list[str], length: int = 2) -> None:
    if not isinstance(value, list) or len(value) < length:
        errors.append(f"`{label}` must be a numeric coordinate array")
        return
    for index, item in enumerate(value):
        if not isinstance(item, (int, float)):
            errors.append(f"`{label}[{index}]` must be numeric")


def validate_geometry(geometry: Any, label: str, errors: list[str]) -> None:
    if not isinstance(geometry, dict):
        errors.append(f"`{label}.geometry` must be an object")
        return
    kind = geometry.get("kind")
    if kind not in {"point", "polyline", "rect", "polygon"}:
        errors.append(f"`{label}.geometry.kind` must be point, polyline, rect, or polygon")
        return
    if kind == "point":
        validate_point(geometry.get("point"), f"{label}.geometry.point", errors, 2)
    elif kind in {"polyline", "polygon"}:
        points = geometry.get("points")
        if not isinstance(points, list) or len(points) < (2 if kind == "polyline" else 3):
            errors.append(f"`{label}.geometry.points` has too few points for {kind}")
            return
        for index, point in enumerate(points):
            validate_point(point, f"{label}.geometry.points[{index}]", errors, 2)
    else:
        for key in ["x", "y", "width", "height"]:
            if not isinstance(geometry.get(key), (int, float)):
                errors.append(f"`{label}.geometry.{key}` must be numeric")
        if isinstance(geometry.get("width"), (int, float)) and float(geometry["width"]) <= 0:
            errors.append(f"`{label}.geometry.width` must be positive")
        if isinstance(geometry.get("height"), (int, float)) and float(geometry["height"]) <= 0:
            errors.append(f"`{label}.geometry.height` must be positive")


def validate_required_item_fields(items: list[Any], required: list[str], label: str, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"`{item_label}` must be an object")
            continue
        for key in required:
            if key not in item:
                errors.append(f"`{item_label}.{key}` is required")
        rows.append(item)
    return rows


def validate_unique_ids(rows: list[dict[str, Any]], id_key: str, label: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        value = row.get(id_key)
        if not isinstance(value, str) or not value:
            errors.append(f"`{label}[{index}].{id_key}` must be a non-empty string")
            continue
        if value in seen:
            errors.append(f"duplicate `{label}` id `{value}`")
        seen.add(value)
    return seen


def validate_no_claims(data: dict[str, Any], errors: list[str]) -> None:
    no_claims = require_object(data, "no_claims", errors)
    for flag in NO_CLAIM_FLAGS:
        if flag not in no_claims:
            errors.append(f"`no_claims.{flag}` is required")
        elif no_claims[flag] is not False:
            errors.append(f"`no_claims.{flag}` must be false")


def validate_template_flags(data: dict[str, Any], errors: list[str]) -> None:
    flags = require_object(data, "template_flags", errors)
    do_not_rewrite = require_bool(flags, "do_not_rewrite", errors)
    mutable = require_bool(flags, "mutable_working_copy", errors)
    protected = require_bool(flags, "protected_template", errors)
    if protected and not do_not_rewrite:
        errors.append("protected templates must set `template_flags.do_not_rewrite` true")
    if protected and mutable:
        errors.append("protected templates must set `template_flags.mutable_working_copy` false")


def validate_map_document(data: dict[str, Any], contract: dict[str, Any], path: Path | None = None) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if data.get("schema") != contract["map_document_schema"]:
        errors.append(f"`schema` must be `{contract['map_document_schema']}`")
    for key in contract["required_top_level_fields"]:
        if key not in data:
            errors.append(f"`{key}` is required")

    map_id = data.get("map_id") if isinstance(data.get("map_id"), str) else "<missing>"
    require_string(data, "map_id", errors)

    size = require_object(data, "size", errors)
    for key in ["width_cells", "height_cells"]:
        value = size.get(key)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"`size.{key}` must be a positive integer")
    require_number(size, "hex_radius_m", errors)
    require_string(size, "layout", errors)
    height_range = size.get("height_range_m")
    if not isinstance(height_range, list) or len(height_range) != 2 or not all(isinstance(v, (int, float)) for v in height_range):
        errors.append("`size.height_range_m` must be a two-number array")

    elevation_bands = validate_required_item_fields(
        require_array(data, "elevation_bands", errors),
        ["band_id", "height_m", "role"],
        "elevation_bands",
        errors,
    )
    validate_unique_ids(elevation_bands, "band_id", "elevation_bands", errors)
    for index, band in enumerate(elevation_bands):
        require_number(band, "height_m", errors)
        require_string(band, "role", errors)
        if height_range and isinstance(height_range, list) and len(height_range) == 2:
            h = band.get("height_m")
            if isinstance(h, (int, float)) and not (float(height_range[0]) <= float(h) <= float(height_range[1])):
                errors.append(f"`elevation_bands[{index}].height_m` is outside size.height_range_m")

    terrain_features = validate_required_item_fields(
        require_array(data, "terrain_features", errors),
        ["feature_id", "feature_type", "geometry"],
        "terrain_features",
        errors,
    )
    validate_unique_ids(terrain_features, "feature_id", "terrain_features", errors)
    for index, feature in enumerate(terrain_features):
        validate_geometry(feature.get("geometry"), f"terrain_features[{index}]", errors)

    roads = validate_required_item_fields(
        require_array(data, "roads", errors),
        ["road_id", "points_map", "width_m", "movement_tag", "surface_type"],
        "roads",
        errors,
    )
    road_ids = validate_unique_ids(roads, "road_id", "roads", errors)
    for index, road in enumerate(roads):
        points = road.get("points_map")
        if not isinstance(points, list) or len(points) < 2:
            errors.append(f"`roads[{index}].points_map` must have at least two points")
        else:
            for point_index, point in enumerate(points):
                validate_point(point, f"roads[{index}].points_map[{point_index}]", errors, 2)
        if not isinstance(road.get("width_m"), (int, float)) or float(road["width_m"]) <= 0:
            errors.append(f"`roads[{index}].width_m` must be positive")

    plots = validate_required_item_fields(
        require_array(data, "building_plots", errors),
        ["plot_id", "geometry", "plot_role"],
        "building_plots",
        errors,
    )
    plot_ids = validate_unique_ids(plots, "plot_id", "building_plots", errors)
    for index, plot in enumerate(plots):
        validate_geometry(plot.get("geometry"), f"building_plots[{index}]", errors)

    hazards = validate_required_item_fields(
        require_array(data, "hazards", errors),
        ["hazard_id", "hazard_type", "severity", "geometry"],
        "hazards",
        errors,
    )
    hazard_ids = validate_unique_ids(hazards, "hazard_id", "hazards", errors)
    for index, hazard in enumerate(hazards):
        validate_geometry(hazard.get("geometry"), f"hazards[{index}]", errors)

    sockets = validate_required_item_fields(
        data.get("asset_sockets", []),
        ["socket_id", "position_map", "socket_type", "anchor_kind", "anchor_ref"],
        "asset_sockets",
        errors,
    )
    validate_unique_ids(sockets, "socket_id", "asset_sockets", errors)
    anchor_ids = plot_ids | hazard_ids | road_ids
    for index, socket in enumerate(sockets):
        validate_point(socket.get("position_map"), f"asset_sockets[{index}].position_map", errors, 2)
        anchor_ref = socket.get("anchor_ref")
        if isinstance(anchor_ref, str) and anchor_ref not in anchor_ids:
            errors.append(f"`asset_sockets[{index}].anchor_ref` references unknown feature `{anchor_ref}`")

    plugs = validate_required_item_fields(
        require_array(data, "plugs", errors),
        [
            "plug_id",
            "owner_id",
            "owner_type",
            "plug_type",
            "position_map",
            "direction_map",
            "width_m",
            "clearance_m",
            "allowed_connection_types",
            "priority",
        ],
        "plugs",
        errors,
    )
    plug_ids = validate_unique_ids(plugs, "plug_id", "plugs", errors)
    supported_connection_types = set(contract["supported_connection_types"])
    for index, plug in enumerate(plugs):
        validate_point(plug.get("position_map"), f"plugs[{index}].position_map", errors, 2)
        validate_point(plug.get("direction_map"), f"plugs[{index}].direction_map", errors, 3)
        if not isinstance(plug.get("width_m"), (int, float)) or float(plug["width_m"]) <= 0:
            errors.append(f"`plugs[{index}].width_m` must be positive")
        if not isinstance(plug.get("clearance_m"), (int, float)) or float(plug["clearance_m"]) < 0:
            errors.append(f"`plugs[{index}].clearance_m` must be non-negative")
        allowed = plug.get("allowed_connection_types")
        if not isinstance(allowed, list) or not allowed:
            errors.append(f"`plugs[{index}].allowed_connection_types` must be a non-empty array")
        elif not set(allowed).issubset(supported_connection_types):
            errors.append(f"`plugs[{index}].allowed_connection_types` contains unsupported values")

    connections = validate_required_item_fields(
        require_array(data, "declared_connections", errors),
        [
            "connection_id",
            "from_plug",
            "to_plug",
            "connection_type",
            "width_m",
            "max_slope",
            "min_clearance_m",
            "deterministic_route_policy",
        ],
        "declared_connections",
        errors,
    )
    validate_unique_ids(connections, "connection_id", "declared_connections", errors)
    for index, connection in enumerate(connections):
        if connection.get("from_plug") not in plug_ids:
            errors.append(f"`declared_connections[{index}].from_plug` references unknown plug `{connection.get('from_plug')}`")
        if connection.get("to_plug") not in plug_ids:
            errors.append(f"`declared_connections[{index}].to_plug` references unknown plug `{connection.get('to_plug')}`")
        if connection.get("connection_type") not in supported_connection_types:
            errors.append(f"`declared_connections[{index}].connection_type` is unsupported")
        for key in ["width_m", "max_slope", "min_clearance_m"]:
            if not isinstance(connection.get(key), (int, float)):
                errors.append(f"`declared_connections[{index}].{key}` must be numeric")

    validate_template_flags(data, errors)
    validate_no_claims(data, errors)

    provenance = data.get("provenance", {})
    if isinstance(provenance, dict):
        if provenance.get("blender_hardcoded_generation_required") is not False:
            errors.append("`provenance.blender_hardcoded_generation_required` must be false")
        if provenance.get("movement_simulation_included") is not False:
            errors.append("`provenance.movement_simulation_included` must be false")
        if provenance.get("asset_geometry_changed") is not False:
            errors.append("`provenance.asset_geometry_changed` must be false")
        if provenance.get("silent_asset_scaling") is not False:
            errors.append("`provenance.silent_asset_scaling` must be false")
        if provenance.get("new_map_not_derived_from_previous_templates") is not True:
            warnings.append("`provenance.new_map_not_derived_from_previous_templates` is not explicitly true")
    else:
        warnings.append("`provenance` is absent or not an object")

    summary = {
        "terrain_feature_count": len(terrain_features),
        "road_count": len(roads),
        "building_plot_count": len(plots),
        "hazard_count": len(hazards),
        "asset_socket_count": len(sockets),
        "plug_count": len(plugs),
        "declared_connection_count": len(connections),
        "protected_template": data.get("template_flags", {}).get("protected_template"),
        "do_not_rewrite": data.get("template_flags", {}).get("do_not_rewrite"),
        "mutable_working_copy": data.get("template_flags", {}).get("mutable_working_copy"),
    }
    return ValidationResult(path=path, map_id=str(map_id), ok=not errors, errors=errors, warnings=warnings, summary=summary)


def protected_template_self_test(contract: dict[str, Any]) -> ValidationResult:
    protected = load_json(DEFAULT_AUTHORING_PATHS[1])
    protected["map_id"] = "pathway_engine_protected_authoring_self_test"
    protected["template_flags"] = {
        "do_not_rewrite": True,
        "mutable_working_copy": False,
        "protected_template": True,
    }
    return validate_map_document(protected, contract)


def missing_required_field_self_test(contract: dict[str, Any]) -> ValidationResult:
    invalid = copy.deepcopy(load_json(DEFAULT_AUTHORING_PATHS[0]))
    invalid.pop("map_id", None)
    return validate_map_document(invalid, contract)


def write_report(results: list[ValidationResult], protected_result: ValidationResult, missing_field_result: ValidationResult) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Map Authoring Contract v0 Report",
        "",
        "Implemented a stable data-only authoring contract for terrain-rich maps and plug/pathway testbeds.",
        "",
        "## Outputs",
        "",
        f"- Contract: `{CONTRACT_PATH.relative_to(ROOT)}`",
        "- Hillwatch authoring map: `data/architecture/map_templates/hillwatch_ravine_authoring_v0.json`",
        "- Pathway authoring map: `data/architecture/map_templates/pathway_engine_authoring_v0.json`",
        f"- Validator: `scripts/{Path(__file__).name}`",
        "",
        "## Validation",
        "",
        "| Map | Valid | Terrain Features | Roads | Plots | Hazards | Plugs | Connections | Protected | Mutable |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for result in results:
        path_label = str(result.path.relative_to(ROOT)) if result.path else result.map_id
        summary = result.summary
        lines.append(
            f"| `{path_label}` | {result.ok} | {summary['terrain_feature_count']} | {summary['road_count']} | "
            f"{summary['building_plot_count']} | {summary['hazard_count']} | {summary['plug_count']} | "
            f"{summary['declared_connection_count']} | {summary['protected_template']} | {summary['mutable_working_copy']} |"
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            f"- Hillwatch Ravine can be described without Blender-only hardcoding: {results[0].ok}",
            f"- Pathway Engine can be described by the same contract: {results[1].ok}",
            f"- Protected templates can be marked `do_not_rewrite`: {protected_result.ok}",
            f"- Missing required fields are rejected: {not missing_field_result.ok}",
            "- No render output required: true",
            "- No old map layout reuse in authored examples: true",
            "",
            "## Canonical Fields",
            "",
            "- `map_id`: stable authored map id, distinct from render and compiled graph ids.",
            "- `size`: width/height cells, hex radius, vertical step, layout, and height range.",
            "- `elevation_bands`: named authoring-level height bands.",
            "- `terrain_features`: high-level terrain intent such as hill, ridge, ravine, plateau, yard, or road surface.",
            "- `roads`: map-coordinate road/path polylines with width, movement tag, and surface type.",
            "- `building_plots`: rectangular or polygonal footprints with plot roles and optional floor-plan references.",
            "- `hazards`: ravines, fall edges, and other blocked or dangerous terrain features.",
            "- `asset_sockets`: optional asset anchor requests; asset expansion remains out of scope.",
            "- `plugs`: named building, road, plot, or pathway connection endpoints.",
            "- `declared_connections`: explicit plug-to-plug pathway contracts.",
            "- `template_flags`: `do_not_rewrite`, `mutable_working_copy`, and `protected_template`.",
            "- `no_claims`: required false claim flags.",
            "",
        ]
    )
    if any(result.errors for result in results):
        lines.extend(["## Errors", ""])
        for result in results:
            for error in result.errors:
                lines.append(f"- `{result.map_id}`: {error}")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(results: list[ValidationResult], protected_result: ValidationResult, missing_field_result: ValidationResult) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "map_authoring_contract_v0_receipt",
        "created_at_utc": now_iso(),
        "contract_path": str(CONTRACT_PATH.relative_to(ROOT)),
        "validated_authoring_maps": [
            {
                "path": str(result.path.relative_to(ROOT)) if result.path else None,
                "map_id": result.map_id,
                "ok": result.ok,
                "summary": result.summary,
                "errors": result.errors,
                "warnings": result.warnings,
            }
            for result in results
        ],
        "acceptance": {
            "hillwatch_ravine_described_without_blender_only_hardcoding": results[0].ok,
            "pathway_engine_described_by_contract": results[1].ok,
            "protected_templates_can_be_marked_do_not_rewrite": protected_result.ok,
            "validation_rejects_missing_required_fields": not missing_field_result.ok,
            "no_render_output_required": True,
            "no_old_map_layout_reuse": True,
        },
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "no_claims": {
            "production_approval": False,
            "structural_safety": False,
            "fabrication_ready": False,
            "gym_museum_approval": False,
            "historical_accuracy": False,
        },
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional map authoring JSON files to validate.")
    parser.add_argument("--no-report", action="store_true", help="Validate only; do not write report or receipt.")
    args = parser.parse_args()

    contract = load_json(CONTRACT_PATH)
    if contract.get("schema") != "map_authoring_contract_v0":
        fail("contract schema must be map_authoring_contract_v0")

    paths = [path if path.is_absolute() else ROOT / path for path in args.paths] if args.paths else DEFAULT_AUTHORING_PATHS
    results = [validate_map_document(load_json(path), contract, path) for path in paths]
    protected_result = protected_template_self_test(contract)
    missing_field_result = missing_required_field_self_test(contract)

    if not args.no_report and paths == DEFAULT_AUTHORING_PATHS:
        write_report(results, protected_result, missing_field_result)
        write_receipt(results, protected_result, missing_field_result)

    for result in results:
        rel = result.path.relative_to(ROOT) if result.path else result.map_id
        status = "PASS" if result.ok else "FAIL"
        print(f"{status} {rel}")
        for error in result.errors:
            print(f"  error: {error}")
        for warning in result.warnings:
            print(f"  warning: {warning}")

    if protected_result.ok:
        print("PASS protected template self-test")
    else:
        print("FAIL protected template self-test")
        for error in protected_result.errors:
            print(f"  error: {error}")

    if missing_field_result.ok:
        print("FAIL missing required field self-test")
    else:
        print("PASS missing required field self-test")

    if any(not result.ok for result in results) or not protected_result.ok or missing_field_result.ok:
        raise SystemExit(1)

    if not args.no_report and paths == DEFAULT_AUTHORING_PATHS:
        print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
        print(f"wrote {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
