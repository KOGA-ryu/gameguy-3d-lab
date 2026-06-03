#!/usr/bin/env python3
"""Compile pattern-field edge intersections into selectable segments.

This is a source selection layer:

pattern field JSON -> line intersections -> split candidate segments -> JSON/SVG

It does not create mesh, run Blender, or emit repo-local generated media.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "pattern_segment_recipes_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_pattern_segments_v0")
PATTERN_FIELD_COMPILER = ROOT / "scripts" / "compile_pattern_field_v0.py"
DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SCHEMA = "pattern_segment_recipe_bundle_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "building_code_compliance": False,
    "game_engine_integration": False,
}
REQUIRED_RULES = {
    "source_lane": True,
    "deterministic_output": True,
    "no_blender_logic": True,
    "no_mesh_output": True,
    "no_generated_outputs": True,
    "segments_are_selection_source": True,
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_display_path(path: Path) -> str:
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
        fail(f"missing JSON file: {repo_display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {repo_display_path(path)}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"{repo_display_path(path)} must contain a JSON object")
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


def finite_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    return round(float(value), 6)


def positive_float(value: Any, field: str) -> float:
    number = finite_float(value, field)
    if number <= 0.0:
        fail(f"{field} must be positive")
    return number


def require_string_list(value: Any, field: str) -> list[str]:
    items = require_list(value, field)
    if not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def require_false_claims(value: Any, field: str) -> None:
    if require_object(value, field) != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")


def load_pattern_field_compiler() -> ModuleType:
    spec = importlib.util.spec_from_file_location("compile_pattern_field_v0", PATTERN_FIELD_COMPILER)
    if spec is None or spec.loader is None:
        fail(f"could not import {repo_display_path(PATTERN_FIELD_COMPILER)}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_operation_terms() -> set[str]:
    terms: set[str] = set()
    for path in sorted((DICTIONARY_ROOT / "operations").glob("*.json")):
        term = load_json(path)
        term_id = require_string(term.get("term_id"), f"{repo_display_path(path)}.term_id")
        category = require_string(term.get("category"), f"{repo_display_path(path)}.category")
        if category in {"mesh_operation", "composition_operation", "transform"}:
            terms.add(term_id)
    if not terms:
        fail("geometry dictionary operation terms are empty")
    return terms


def validate_selection(value: Any, segment_set_id: str, index: int) -> dict[str, Any]:
    selection = require_object(value, f"{segment_set_id}.selections[{index}]")
    selection_id = require_string(selection.get("selection_id"), f"{segment_set_id}.selections[{index}].selection_id")
    if require_string(selection.get("selection_type"), f"{selection_id}.selection_type") != "segments":
        fail(f"{selection_id}.selection_type must be segments")
    selector = require_object(selection.get("selector"), f"{selection_id}.selector")
    if require_string(selector.get("kind"), f"{selection_id}.selector.kind") != "segment_tag_query":
        fail(f"{selection_id}.selector.kind must be segment_tag_query")
    return {
        "selection_id": selection_id,
        "selection_type": "segments",
        "selector": {"kind": "segment_tag_query", "tag": require_string(selector.get("tag"), f"{selection_id}.selector.tag")},
        "architectural_roles": require_string_list(selection.get("architectural_roles"), f"{selection_id}.architectural_roles"),
    }


def validate_segment_set(value: Any, operations: set[str], index: int) -> dict[str, Any]:
    item = require_object(value, f"segment_sets[{index}]")
    segment_set_id = require_string(item.get("segment_set_id"), f"segment_sets[{index}].segment_set_id")
    operation = require_string(item.get("geometry_operation"), f"{segment_set_id}.geometry_operation")
    if operation not in operations:
        fail(f"{segment_set_id}.geometry_operation references unknown geometry operation: {operation}")
    policy = require_object(item.get("intersection_policy"), f"{segment_set_id}.intersection_policy")
    if require_string(policy.get("scope"), f"{segment_set_id}.intersection_policy.scope") != "all_edges":
        fail(f"{segment_set_id}.intersection_policy.scope must be all_edges")
    if policy.get("include_endpoint_intersections") is not False:
        fail(f"{segment_set_id}.intersection_policy.include_endpoint_intersections must be false in v0")
    tolerance = positive_float(policy.get("deduplicate_tolerance_m"), f"{segment_set_id}.intersection_policy.deduplicate_tolerance_m")
    minimum_segment_length = positive_float(policy.get("minimum_segment_length_m"), f"{segment_set_id}.intersection_policy.minimum_segment_length_m")
    require_false_claims(item.get("no_claims"), f"{segment_set_id}.no_claims")
    return {
        "segment_set_id": segment_set_id,
        "source_field_id": require_string(item.get("source_field_id"), f"{segment_set_id}.source_field_id"),
        "geometry_operation": operation,
        "description": require_string(item.get("description"), f"{segment_set_id}.description"),
        "intersection_policy": {
            "scope": "all_edges",
            "include_endpoint_intersections": False,
            "deduplicate_tolerance_m": tolerance,
            "minimum_segment_length_m": minimum_segment_length,
        },
        "selections": [
            validate_selection(selection, segment_set_id, selection_index)
            for selection_index, selection in enumerate(require_list(item.get("selections"), f"{segment_set_id}.selections"))
        ],
        "validation_expectations": require_object(item.get("validation_expectations"), f"{segment_set_id}.validation_expectations"),
        "no_claims": item["no_claims"],
    }


def validate_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    if bundle.get("schema") != SCHEMA:
        fail(f"bundle schema must be {SCHEMA}")
    if require_object(bundle.get("rules"), "rules") != REQUIRED_RULES:
        fail("bundle rules must match pattern segment source boundaries")
    field_bundle_path = repo_path(bundle.get("source_pattern_field_bundle"), "source_pattern_field_bundle")
    if not field_bundle_path.exists():
        fail(f"source_pattern_field_bundle references missing file: {repo_display_path(field_bundle_path)}")
    operations = load_operation_terms()
    segment_sets_source = require_list(bundle.get("segment_sets"), "segment_sets")
    if bundle.get("segment_set_count") != len(segment_sets_source):
        fail("bundle segment_set_count must match segment_sets length")
    segment_sets = [validate_segment_set(item, operations, index) for index, item in enumerate(segment_sets_source)]
    seen: set[str] = set()
    for segment_set in segment_sets:
        if segment_set["segment_set_id"] in seen:
            fail(f"duplicate segment_set_id: {segment_set['segment_set_id']}")
        seen.add(segment_set["segment_set_id"])
    return segment_sets


def compiled_fields_from_source(field_bundle_path: Path) -> dict[str, dict[str, Any]]:
    module = load_pattern_field_compiler()
    field_bundle = module.load_json(field_bundle_path)
    fields = module.validate_bundle(field_bundle)
    return {field["field_id"]: module.compile_field(field_bundle, field) for field in fields}


def compiled_fields_from_manifest(manifest_path: Path) -> dict[str, dict[str, Any]]:
    manifest = load_json(manifest_path)
    if manifest.get("schema") != "gameguy_pattern_field_manifest_v0":
        fail(f"{repo_display_path(manifest_path)} schema must be gameguy_pattern_field_manifest_v0")
    base = manifest_path.parent
    result: dict[str, dict[str, Any]] = {}
    for index, field_ref in enumerate(require_list(manifest.get("fields"), "pattern_field_manifest.fields")):
        item = require_object(field_ref, f"pattern_field_manifest.fields[{index}]")
        field_id = require_string(item.get("field_id"), f"pattern_field_manifest.fields[{index}].field_id")
        field_path = base / require_string(item.get("path"), f"pattern_field_manifest.fields[{index}].path")
        result[field_id] = load_json(field_path)
    return result


def point_key(point: list[float], tolerance: float) -> tuple[int, int]:
    return (round(point[0] / tolerance), round(point[1] / tolerance))


def distance(a: list[float], b: list[float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def edge_intersection(a1: list[float], a2: list[float], b1: list[float], b2: list[float], tolerance: float) -> tuple[float, list[float]] | None:
    ax = a2[0] - a1[0]
    ay = a2[1] - a1[1]
    bx = b2[0] - b1[0]
    by = b2[1] - b1[1]
    denom = ax * by - ay * bx
    if abs(denom) <= tolerance:
        return None
    cx = b1[0] - a1[0]
    cy = b1[1] - a1[1]
    t = (cx * by - cy * bx) / denom
    u = (cx * ay - cy * ax) / denom
    if t <= tolerance or t >= 1.0 - tolerance or u <= tolerance or u >= 1.0 - tolerance:
        return None
    point = [round(a1[0] + t * ax, 6), round(a1[1] + t * ay, 6)]
    return (round(t, 9), point)


def source_tags(edge: dict[str, Any]) -> list[str]:
    return [f"source:{tag}" for tag in edge["tags"]]


def compile_segment_set(bundle: dict[str, Any], segment_set: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    point_by_id = {point["point_id"]: point["xy_m"] for point in field["points"]}
    tolerance = segment_set["intersection_policy"]["deduplicate_tolerance_m"]
    min_length = segment_set["intersection_policy"]["minimum_segment_length_m"]
    edge_splits: dict[str, list[tuple[float, list[float]]]] = {}
    intersection_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    edges = field["edges"]
    for edge in edges:
        edge_splits[edge["edge_id"]] = [(0.0, point_by_id[edge["from"]]), (1.0, point_by_id[edge["to"]])]
    for left_index, left in enumerate(edges):
        left_a = point_by_id[left["from"]]
        left_b = point_by_id[left["to"]]
        for right in edges[left_index + 1:]:
            # Adjacent source edges already share endpoints; v0 only records interior intersections.
            if {left["from"], left["to"]} & {right["from"], right["to"]}:
                continue
            right_a = point_by_id[right["from"]]
            right_b = point_by_id[right["to"]]
            intersection = edge_intersection(left_a, left_b, right_a, right_b, tolerance)
            if intersection is None:
                continue
            left_t, point = intersection
            right_length = distance(right_a, right_b)
            if right_length <= tolerance:
                continue
            right_t = round(distance(right_a, point) / right_length, 9)
            key = point_key(point, tolerance)
            if key not in intersection_by_key:
                intersection_by_key[key] = {
                    "point_id": f"intersection_{len(intersection_by_key):04d}",
                    "xy_m": point,
                    "source_edge_ids": [],
                }
            intersection_by_key[key]["source_edge_ids"].extend([left["edge_id"], right["edge_id"]])
            edge_splits[left["edge_id"]].append((left_t, point))
            edge_splits[right["edge_id"]].append((right_t, point))
    intersections = []
    for item in intersection_by_key.values():
        item["source_edge_ids"] = sorted(set(item["source_edge_ids"]))
        intersections.append(item)
    intersections.sort(key=lambda item: item["point_id"])
    segments: list[dict[str, Any]] = []
    for edge in edges:
        splits = sorted(edge_splits[edge["edge_id"]], key=lambda split: split[0])
        deduped: list[tuple[float, list[float]]] = []
        seen_split_keys: set[tuple[int, int]] = set()
        for t, point in splits:
            key = point_key(point, tolerance)
            if key in seen_split_keys:
                continue
            seen_split_keys.add(key)
            deduped.append((t, point))
        for index in range(len(deduped) - 1):
            start_t, start = deduped[index]
            end_t, end = deduped[index + 1]
            length = distance(start, end)
            if length < min_length:
                continue
            segment_id = f"segment_{edge['edge_id']}_{index:03d}"
            segments.append(
                {
                    "segment_id": segment_id,
                    "source_edge_id": edge["edge_id"],
                    "source_edge_type": edge["edge_type"],
                    "t_range": [round(start_t, 9), round(end_t, 9)],
                    "start_xy_m": start,
                    "end_xy_m": end,
                    "length_m": round(length, 6),
                    "tags": ["pattern_segment", f"source_edge:{edge['edge_id']}", f"source_edge_type:{edge['edge_type']}", *source_tags(edge)],
                }
            )
    compiled_selections: list[dict[str, Any]] = []
    selected_segment_refs: list[str] = []
    for selection in segment_set["selections"]:
        tag = selection["selector"]["tag"]
        segment_ids = [segment["segment_id"] for segment in segments if tag in segment["tags"]]
        if not segment_ids:
            fail(f"{selection['selection_id']} selected no segments for tag `{tag}`")
        selected_segment_refs.extend(segment_ids)
        compiled_selections.append(
            {
                "selection_id": selection["selection_id"],
                "selection_type": "segments",
                "architectural_roles": selection["architectural_roles"],
                "selector": selection["selector"],
                "segment_ids": segment_ids,
                "selected_count": len(segment_ids),
            }
        )
    compiled = {
        "schema": "gameguy_pattern_segment_graph_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "segment_set_id": segment_set["segment_set_id"],
        "source_field_id": segment_set["source_field_id"],
        "geometry_operation": segment_set["geometry_operation"],
        "description": segment_set["description"],
        "units": bundle.get("units", field.get("units", "abstract_meter")),
        "bounds_m": field["bounds_m"],
        "intersection_policy": segment_set["intersection_policy"],
        "source_edge_count": len(edges),
        "intersections": intersections,
        "segments": segments,
        "selections": compiled_selections,
        "summary": {
            "source_edge_count": len(edges),
            "intersection_point_count": len(intersections),
            "segment_count": len(segments),
            "selection_count": len(compiled_selections),
            "selected_segment_reference_count": len(selected_segment_refs),
            "unique_selected_segment_count": len(set(selected_segment_refs)),
        },
        "rules": {
            "source_segments_only": True,
            "selected_segments_named": True,
            "blender_is_adapter_layer": True,
            "no_mesh_output": True,
            "no_media_output_in_repo": True,
        },
        "validation_expectations": segment_set["validation_expectations"],
        "no_claims": segment_set["no_claims"],
    }
    for key, value in compiled["summary"].items():
        expected_value = segment_set["validation_expectations"].get(key)
        if expected_value is not None and expected_value != value:
            fail(f"{segment_set['segment_set_id']}.validation_expectations.{key} must be {value}")
    return compiled


def compile_all(bundle: dict[str, Any], segment_sets: list[dict[str, Any]], fields_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    compiled = []
    for segment_set in segment_sets:
        field_id = segment_set["source_field_id"]
        if field_id not in fields_by_id:
            fail(f"{segment_set['segment_set_id']} references unknown source_field_id: {field_id}")
        compiled.append(compile_segment_set(bundle, segment_set, fields_by_id[field_id]))
    return compiled


def svg_point(point: list[float], bounds: dict[str, float], scale: float, margin: float) -> tuple[float, float]:
    return margin + point[0] * scale, margin + (bounds["height"] - point[1]) * scale


def svg_line(a: list[float], b: list[float], bounds: dict[str, float], scale: float, margin: float, klass: str) -> str:
    ax, ay = svg_point(a, bounds, scale, margin)
    bx, by = svg_point(b, bounds, scale, margin)
    return f'<line class="{klass}" x1="{ax:.3f}" y1="{ay:.3f}" x2="{bx:.3f}" y2="{by:.3f}" />'


def render_svg(compiled: dict[str, Any]) -> str:
    bounds = compiled["bounds_m"]
    size = 1100
    margin = 70.0
    scale = min((size - margin * 2) / bounds["width"], (size - margin * 2) / bounds["height"])
    selected_ids = {segment_id for selection in compiled["selections"] for segment_id in selection["segment_ids"]}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        "<style>",
        ".bg{fill:#fbfaf6}.sheet{fill:none;stroke:#b9b3a7;stroke-width:1.4}.segment{stroke:#c7c0b5;stroke-width:.9;opacity:.42}.selected{stroke:#1f1f1f;stroke-width:1.7;opacity:.82}.intersection{fill:#b93524;opacity:.8}.label{font:18px monospace;fill:#202020}.small{font:14px monospace;fill:#4b4b4b}",
        "</style>",
        f'<rect class="bg" x="0" y="0" width="{size}" height="{size}" />',
        f'<rect class="sheet" x="{margin:.3f}" y="{margin:.3f}" width="{bounds["width"] * scale:.3f}" height="{bounds["height"] * scale:.3f}" />',
    ]
    for segment in compiled["segments"]:
        if segment["segment_id"] not in selected_ids:
            lines.append(svg_line(segment["start_xy_m"], segment["end_xy_m"], bounds, scale, margin, "segment"))
    for segment in compiled["segments"]:
        if segment["segment_id"] in selected_ids:
            lines.append(svg_line(segment["start_xy_m"], segment["end_xy_m"], bounds, scale, margin, "selected"))
    for point in compiled["intersections"]:
        x, y = svg_point(point["xy_m"], bounds, scale, margin)
        lines.append(f'<circle class="intersection" cx="{x:.3f}" cy="{y:.3f}" r="2.1" />')
    lines.append(f'<text class="label" x="30" y="38">{compiled["segment_set_id"]}</text>')
    lines.append(
        f'<text class="small" x="30" y="62">intersections={compiled["summary"]["intersection_point_count"]} '
        f'segments={compiled["summary"]["segment_count"]} selected={compiled["summary"]["unique_selected_segment_count"]}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def write_outputs(bundle: dict[str, Any], compiled_sets: list[dict[str, Any]], out_root: Path, clean: bool) -> dict[str, Any]:
    if clean and out_root.exists():
        shutil.rmtree(out_root)
    (out_root / "segment_sets").mkdir(parents=True, exist_ok=True)
    (out_root / "svg").mkdir(parents=True, exist_ok=True)
    manifest_sets = []
    for compiled in compiled_sets:
        set_path = out_root / "segment_sets" / f"{compiled['segment_set_id']}.json"
        svg_path = out_root / "svg" / f"{compiled['segment_set_id']}.svg"
        set_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        svg_path.write_text(render_svg(compiled), encoding="utf-8")
        manifest_sets.append(
            {
                "segment_set_id": compiled["segment_set_id"],
                "source_field_id": compiled["source_field_id"],
                "path": f"segment_sets/{compiled['segment_set_id']}.json",
                "svg_path": f"svg/{compiled['segment_set_id']}.svg",
                "intersection_point_count": compiled["summary"]["intersection_point_count"],
                "segment_count": compiled["summary"]["segment_count"],
                "selection_count": compiled["summary"]["selection_count"],
                "unique_selected_segment_count": compiled["summary"]["unique_selected_segment_count"],
            }
        )
    manifest = {
        "schema": "gameguy_pattern_segment_manifest_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "segment_set_count": len(manifest_sets),
        "segment_sets": manifest_sets,
        "rules": {
            "no_blender": True,
            "no_mesh_export_files": True,
            "json_and_svg_preview_only": True,
            "generated_outputs_in_repo": False,
        },
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile pattern field intersections into selectable segments.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--pattern-field-bundle", type=Path, help="Optional pattern field bundle override used when --pattern-field-manifest is absent.")
    parser.add_argument("--pattern-field-manifest", type=Path, help="Optional compiled pattern field manifest to consume.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    bundle = load_json(bundle_path)
    segment_sets = validate_bundle(bundle)
    if args.pattern_field_manifest:
        field_manifest_path = args.pattern_field_manifest if args.pattern_field_manifest.is_absolute() else ROOT / args.pattern_field_manifest
        fields_by_id = compiled_fields_from_manifest(field_manifest_path)
    else:
        field_bundle_path = (
            args.pattern_field_bundle if args.pattern_field_bundle and args.pattern_field_bundle.is_absolute()
            else ROOT / args.pattern_field_bundle if args.pattern_field_bundle
            else repo_path(bundle.get("source_pattern_field_bundle"), "source_pattern_field_bundle")
        )
        fields_by_id = compiled_fields_from_source(field_bundle_path)
    compiled_sets = compile_all(bundle, segment_sets, fields_by_id)
    if args.validate_only:
        segment_count = sum(compiled["summary"]["segment_count"] for compiled in compiled_sets)
        intersection_count = sum(compiled["summary"]["intersection_point_count"] for compiled in compiled_sets)
        print(f"compiled pattern segment sets={len(compiled_sets)} intersections={intersection_count} segments={segment_count} out=<validate-only>")
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = write_outputs(bundle, compiled_sets, out_root, args.clean)
    segment_count = sum(segment_set["segment_count"] for segment_set in manifest["segment_sets"])
    selected_count = sum(segment_set["unique_selected_segment_count"] for segment_set in manifest["segment_sets"])
    intersection_count = sum(segment_set["intersection_point_count"] for segment_set in manifest["segment_sets"])
    print(
        "compiled pattern segment sets="
        f"{manifest['segment_set_count']} intersections={intersection_count} segments={segment_count} selected={selected_count} out={out_root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
