#!/usr/bin/env python3
"""Validate generated gameguy_asset_v0 JSON.

This validates asset pump output directly. It does not read source recipes,
run Blender, create reports by default, or write mesh/media artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("/tmp/gameguy_asset_pump_v0/manifest.json")
CONTRACT_PATH = ROOT / "contracts" / "gameguy_asset_v0.json"
ASSET_SCHEMA = "gameguy_asset_v0"
MANIFEST_SCHEMA = "gameguy_asset_pump_manifest_v0"
MEASURED_SOURCE_SCHEMA = "asset_mill_measured_component_bundle_v0"
REQUIRED_FALSE_CLAIMS = {
    "production_approval",
    "structural_safety",
    "fabrication_ready",
    "gym_museum_approval",
}
FORBIDDEN_OUTPUT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".blend",
    ".blend1",
    ".obj",
    ".gltf",
    ".glb",
    ".fbx",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_vector(value: Any, field: str, length: int = 3) -> list[float]:
    items = require_list(value, field)
    if len(items) != length:
        fail(f"{field} must contain {length} numbers")
    result = []
    for index, item in enumerate(items):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")
        result.append(round(float(item), 6))
    return result


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    result = []
    for index, item in enumerate(items):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def require_bounds(value: Any, field: str) -> dict[str, list[float]]:
    bounds = require_object(value, field)
    min_values = require_vector(bounds.get("min"), f"{field}.min")
    max_values = require_vector(bounds.get("max"), f"{field}.max")
    for axis, (min_value, max_value) in enumerate(zip(min_values, max_values, strict=True)):
        if min_value >= max_value:
            fail(f"{field} axis {axis} min must be less than max")
    return {"min": min_values, "max": max_values}


def dimensions_from_bounds(bounds_m: dict[str, list[float]]) -> dict[str, float]:
    return {
        "width": round(bounds_m["max"][0] - bounds_m["min"][0], 6),
        "depth": round(bounds_m["max"][1] - bounds_m["min"][1], 6),
        "height": round(bounds_m["max"][2] - bounds_m["min"][2], 6),
    }


def require_dimensions(value: Any, field: str) -> dict[str, float]:
    dimensions = require_object(value, field)
    result = {}
    for key in ("width", "depth", "height"):
        item = dimensions.get(key)
        if not finite_number(item):
            fail(f"{field}.{key} must be a finite number")
        item = round(float(item), 6)
        if item <= 0.0:
            fail(f"{field}.{key} must be positive")
        result[key] = item
    return result


def mesh_bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    if not vertices:
        fail("mesh vertices must not be empty")
    return {
        "min": [round(min(vertex[axis] for vertex in vertices), 6) for axis in range(3)],
        "max": [round(max(vertex[axis] for vertex in vertices), 6) for axis in range(3)],
    }


def require_normalized_direction(value: Any, field: str) -> list[float]:
    direction = require_vector(value, field)
    length = math.sqrt(sum(item * item for item in direction))
    if not math.isclose(length, 1.0, rel_tol=0.0, abs_tol=1e-6):
        fail(f"{field} must be normalized")
    return direction


def validate_no_claims(value: Any, field: str) -> None:
    claims = require_object(value, field)
    for key in REQUIRED_FALSE_CLAIMS:
        if claims.get(key) is not False:
            fail(f"{field}.{key} must be false")
    for key, claim in claims.items():
        if not isinstance(key, str) or not isinstance(claim, bool):
            fail(f"{field} must contain boolean claim flags")
        if claim is not False:
            fail(f"{field}.{key} must be false")


def validate_mesh(asset_id: str, mesh: Any, measured: bool) -> tuple[int, int, int]:
    mesh_obj = require_object(mesh, f"{asset_id}.mesh")
    if mesh_obj.get("coordinate_space") != "local_xyz_m":
        fail(f"{asset_id}.mesh.coordinate_space must be local_xyz_m")

    vertices_raw = require_list(mesh_obj.get("vertices"), f"{asset_id}.mesh.vertices")
    if len(vertices_raw) < 3:
        fail(f"{asset_id}.mesh.vertices must contain at least 3 vertices")
    vertices = [require_vector(vertex, f"{asset_id}.mesh.vertices[{index}]") for index, vertex in enumerate(vertices_raw)]

    faces = require_list(mesh_obj.get("faces"), f"{asset_id}.mesh.faces")
    if not faces:
        fail(f"{asset_id}.mesh.faces must not be empty")
    for face_index, face in enumerate(faces):
        face_items = require_list(face, f"{asset_id}.mesh.faces[{face_index}]")
        if len(face_items) < 3:
            fail(f"{asset_id}.mesh.faces[{face_index}] must contain at least 3 vertex indexes")
        for item in face_items:
            if not isinstance(item, int) or isinstance(item, bool) or item < 0 or item >= len(vertices):
                fail(f"{asset_id}.mesh.faces[{face_index}] contains invalid vertex index `{item}`")

    parts = require_list(mesh_obj.get("parts"), f"{asset_id}.mesh.parts")
    if measured and not parts:
        fail(f"{asset_id}.mesh.parts must be non-empty for measured assets")
    for part_index, part in enumerate(parts):
        part_obj = require_object(part, f"{asset_id}.mesh.parts[{part_index}]")
        require_string(part_obj.get("part_id"), f"{asset_id}.mesh.parts[{part_index}].part_id")
        require_string(part_obj.get("source_primitive"), f"{asset_id}.mesh.parts[{part_index}].source_primitive")
        vertex_range = require_list(part_obj.get("vertex_range"), f"{asset_id}.mesh.parts[{part_index}].vertex_range")
        face_range = require_list(part_obj.get("face_range"), f"{asset_id}.mesh.parts[{part_index}].face_range")
        validate_range(vertex_range, len(vertices), f"{asset_id}.mesh.parts[{part_index}].vertex_range")
        validate_range(face_range, len(faces), f"{asset_id}.mesh.parts[{part_index}].face_range")

    calculated_bounds = mesh_bounds(vertices)
    if "bounds_m" in mesh_obj:
        declared_mesh_bounds = require_bounds(mesh_obj["bounds_m"], f"{asset_id}.mesh.bounds_m")
        if declared_mesh_bounds != calculated_bounds:
            fail(f"{asset_id}.mesh.bounds_m must match mesh vertices")

    return len(vertices), len(faces), len(parts)


def validate_range(value: list[Any], upper_bound: int, field: str) -> None:
    if len(value) != 2:
        fail(f"{field} must contain two indexes")
    start, end = value
    if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool):
        fail(f"{field} must contain integer indexes")
    if start < 0 or end < start or end >= upper_bound:
        fail(f"{field} must be within generated mesh indexes")


def validate_connectors(asset_id: str, value: Any) -> int:
    connectors = require_list(value, f"{asset_id}.connectors")
    seen = set()
    for index, connector in enumerate(connectors):
        connector_obj = require_object(connector, f"{asset_id}.connectors[{index}]")
        connector_id = require_string(connector_obj.get("connector_id"), f"{asset_id}.connectors[{index}].connector_id")
        if connector_id in seen:
            fail(f"{asset_id}.connectors duplicate connector_id: {connector_id}")
        seen.add(connector_id)
        require_vector(connector_obj.get("position_m"), f"{asset_id}.connectors[{index}].position_m")
        require_normalized_direction(connector_obj.get("direction"), f"{asset_id}.connectors[{index}].direction")
        if "connector_term" in connector_obj:
            require_string(connector_obj.get("connector_term"), f"{asset_id}.connectors[{index}].connector_term")
        if "role" in connector_obj:
            require_string(connector_obj.get("role"), f"{asset_id}.connectors[{index}].role")
    return len(connectors)


def validate_components(asset_id: str, value: Any) -> int:
    components = require_list(value, f"{asset_id}.components")
    seen = set()
    for index, component in enumerate(components):
        component_obj = require_object(component, f"{asset_id}.components[{index}]")
        instance_id = require_string(component_obj.get("instance_id"), f"{asset_id}.components[{index}].instance_id")
        if instance_id in seen:
            fail(f"{asset_id}.components duplicate instance_id: {instance_id}")
        seen.add(instance_id)
        require_string(component_obj.get("asset_ref"), f"{asset_id}.components[{index}].asset_ref")
        require_vector(component_obj.get("translation_m"), f"{asset_id}.components[{index}].translation_m")
    return len(components)


def validate_source_terms(asset_id: str, value: Any, measured: bool) -> None:
    source_terms = require_object(value, f"{asset_id}.source_terms")
    for field in ("geometry", "profiles", "operators"):
        require_string_list(source_terms.get(field), f"{asset_id}.source_terms.{field}", allow_empty=not measured)


def validate_asset(asset: dict[str, Any], path: Path, required_fields: list[str]) -> dict[str, int]:
    asset_id = require_string(asset.get("asset_id"), f"{path}.asset_id")
    if asset.get("schema") != ASSET_SCHEMA:
        fail(f"{asset_id}.schema must be {ASSET_SCHEMA}")
    for field in required_fields:
        if field not in asset:
            fail(f"{asset_id} missing required field {field}")

    source_schema = require_string(asset.get("source_schema"), f"{asset_id}.source_schema")
    measured = source_schema == MEASURED_SOURCE_SCHEMA or asset.get("asset_kind") == "measured_component"
    if measured and source_schema != MEASURED_SOURCE_SCHEMA:
        fail(f"{asset_id}.source_schema must be {MEASURED_SOURCE_SCHEMA} for measured assets")
    require_string(asset.get("source_operation"), f"{asset_id}.source_operation")
    require_string(asset.get("asset_kind"), f"{asset_id}.asset_kind")
    require_string(asset.get("architectural_role"), f"{asset_id}.architectural_role")
    require_string_list(asset.get("generation_use"), f"{asset_id}.generation_use")
    require_string_list(asset.get("semantic_tags"), f"{asset_id}.semantic_tags")
    require_string_list(asset.get("child_slots"), f"{asset_id}.child_slots", allow_empty=True)

    bounds_m = require_bounds(asset.get("bounds_m"), f"{asset_id}.bounds_m")
    dimensions_m = require_dimensions(asset.get("dimensions_m"), f"{asset_id}.dimensions_m")
    if dimensions_from_bounds(bounds_m) != dimensions_m:
        fail(f"{asset_id}.dimensions_m must match bounds_m span")

    vertex_count, face_count, part_count = validate_mesh(asset_id, asset.get("mesh"), measured)
    connector_count = validate_connectors(asset_id, asset.get("connectors"))
    component_count = validate_components(asset_id, asset.get("components"))
    validate_no_claims(asset.get("no_claims"), f"{asset_id}.no_claims")
    require_list(asset.get("source_refs"), f"{asset_id}.source_refs")
    validate_source_terms(asset_id, asset.get("source_terms"), measured)
    require_object(asset.get("validation_expectations"), f"{asset_id}.validation_expectations")

    if measured:
        if asset.get("source_operation") != "proof_primitives":
            fail(f"{asset_id}.source_operation must be proof_primitives for measured assets")
        if not asset["source_refs"]:
            fail(f"{asset_id}.source_refs must be non-empty for measured assets")
        if asset.get("source_version") not in {"v1", "v2"}:
            fail(f"{asset_id}.source_version must be v1 or v2 for measured assets")
        require_string(asset.get("source_script"), f"{asset_id}.source_script")
        for connector_index, connector in enumerate(asset["connectors"]):
            require_string(connector.get("connector_term"), f"{asset_id}.connectors[{connector_index}].connector_term")
            require_string(connector.get("role"), f"{asset_id}.connectors[{connector_index}].role")

    return {
        "vertices": vertex_count,
        "faces": face_count,
        "parts": part_count,
        "connectors": connector_count,
        "components": component_count,
        "measured": int(measured),
    }


def manifest_asset_path(manifest_path: Path, rel_path: str, field: str) -> Path:
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        fail(f"{field} must be a relative path inside the pump output root")
    asset_path = manifest_path.parent / rel_path
    try:
        asset_path.resolve().relative_to(manifest_path.parent.resolve())
    except ValueError:
        fail(f"{field} must stay inside the pump output root")
    return asset_path


def validate_output_root(manifest_path: Path) -> None:
    for path in manifest_path.parent.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_OUTPUT_SUFFIXES:
            fail(f"generated media/mesh output is not allowed in asset pump output: {path}")


def load_required_fields() -> list[str]:
    contract = load_json(CONTRACT_PATH)
    fields = contract.get("required_fields")
    if not isinstance(fields, list) or not fields:
        fail(f"{CONTRACT_PATH} required_fields must be a non-empty list")
    return [require_string(field, "contracts.gameguy_asset_v0.required_fields[]") for field in fields]


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        fail(f"manifest schema must be {MANIFEST_SCHEMA}")
    require_string(manifest.get("source_bundle"), "manifest.source_bundle")
    require_string(manifest.get("source_bundle_schema"), "manifest.source_bundle_schema")
    if manifest.get("asset_schema") != ASSET_SCHEMA:
        fail(f"manifest.asset_schema must be {ASSET_SCHEMA}")
    rows = require_list(manifest.get("assets"), "manifest.assets")
    if not rows:
        fail("manifest.assets must not be empty")
    if manifest.get("asset_count") != len(rows):
        fail("manifest.asset_count must match assets length")
    rules = require_object(manifest.get("rules"), "manifest.rules")
    for key in ("no_reports", "no_receipts", "no_blender", "no_media", "no_mesh_export_files", "geometry_dictionary_terms_enforced"):
        if rules.get(key) is not True:
            fail(f"manifest.rules.{key} must be true")

    required_fields = load_required_fields()
    totals = {
        "asset_count": 0,
        "measured_asset_count": 0,
        "total_vertices": 0,
        "total_faces": 0,
        "total_parts": 0,
        "total_connectors": 0,
        "total_components": 0,
    }
    seen_ids = set()
    for index, row in enumerate(rows):
        row_obj = require_object(row, f"manifest.assets[{index}]")
        asset_id = require_string(row_obj.get("asset_id"), f"manifest.assets[{index}].asset_id")
        if asset_id in seen_ids:
            fail(f"duplicate asset_id in manifest: {asset_id}")
        seen_ids.add(asset_id)
        asset_path = manifest_asset_path(manifest_path, require_string(row_obj.get("path"), f"manifest.assets[{index}].path"), f"manifest.assets[{index}].path")
        asset = load_json(asset_path)
        counts = validate_asset(asset, asset_path, required_fields)
        if asset["asset_id"] != asset_id:
            fail(f"manifest asset_id {asset_id} does not match {asset_path}")
        for key in ("asset_kind", "architectural_role", "dimensions_m"):
            if row_obj.get(key) != asset.get(key):
                fail(f"manifest.assets[{index}].{key} must match generated asset")
        if row_obj.get("vertex_count") != counts["vertices"]:
            fail(f"manifest.assets[{index}].vertex_count must match generated asset")
        if row_obj.get("face_count") != counts["faces"]:
            fail(f"manifest.assets[{index}].face_count must match generated asset")
        totals["asset_count"] += 1
        totals["measured_asset_count"] += counts["measured"]
        totals["total_vertices"] += counts["vertices"]
        totals["total_faces"] += counts["faces"]
        totals["total_parts"] += counts["parts"]
        totals["total_connectors"] += counts["connectors"]
        totals["total_components"] += counts["components"]

    validate_output_root(manifest_path)
    return {
        "schema": "gameguy_asset_v0_validation_result_v0",
        "status": "pass",
        "manifest": str(manifest_path),
        "source_bundle_schema": manifest["source_bundle_schema"],
        "asset_schema": ASSET_SCHEMA,
        **totals,
        "generated_outputs_created": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated gameguy_asset_v0 asset pump output.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-report", type=Path, help="Optional path for a validation report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    report = validate_manifest(manifest_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS gameguy_asset_v0 validation: "
        f"{report['asset_count']} assets, {report['total_vertices']} vertices, {report['total_faces']} faces"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
