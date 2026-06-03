#!/usr/bin/env python3
"""Compile multi-center 2D pattern field recipes into JSON and SVG previews.

This is a construction drawing layer:

pattern field recipe -> rosette modules + guide lines + selected traces -> JSON/SVG

It does not create mesh, run Blender, or emit repo-local generated media.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "pattern_field_recipes_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_pattern_field_v0")
DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SCHEMA = "pattern_field_recipe_bundle_v0"
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
    "field_is_construction_source": True,
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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


def integer_at_least(value: Any, minimum: int, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def finite_vector(value: Any, field: str, length: int = 2) -> list[float]:
    items = require_list(value, field)
    if len(items) != length:
        fail(f"{field} must contain {length} numbers")
    return [finite_float(item, f"{field}[{index}]") for index, item in enumerate(items)]


def require_string_list(value: Any, field: str) -> list[str]:
    items = require_list(value, field)
    if not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def require_false_claims(value: Any, field: str) -> None:
    if require_object(value, field) != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")


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


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def validate_ring(module_id: str, value: Any, index: int) -> dict[str, Any]:
    ring = require_object(value, f"{module_id}.rings[{index}]")
    return {
        "ring_id": require_string(ring.get("ring_id"), f"{module_id}.rings[{index}].ring_id"),
        "radius_m": positive_float(ring.get("radius_m"), f"{module_id}.rings[{index}].radius_m"),
        "role_hint": require_string(ring.get("role_hint"), f"{module_id}.rings[{index}].role_hint"),
    }


def validate_star_trace(module_id: str, divisions: int, ring_ids: set[str], value: Any, index: int) -> dict[str, Any]:
    trace = require_object(value, f"{module_id}.star_traces[{index}]")
    trace_id = require_string(trace.get("trace_id"), f"{module_id}.star_traces[{index}].trace_id")
    ring_id = require_string(trace.get("ring_id"), f"{module_id}.star_traces[{index}].ring_id")
    if ring_id not in ring_ids:
        fail(f"{module_id}.star_traces[{index}].ring_id references unknown ring: {ring_id}")
    step = integer_at_least(trace.get("step"), 1, f"{module_id}.star_traces[{index}].step")
    if step >= divisions:
        fail(f"{module_id}.star_traces[{index}].step must be less than divisions")
    if gcd(step, divisions) != 1:
        fail(f"{module_id}.star_traces[{index}].step must be coprime with divisions")
    return {
        "trace_id": trace_id,
        "ring_id": ring_id,
        "step": step,
        "selected": bool(trace.get("selected", False)),
        "role_hint": require_string(trace.get("role_hint"), f"{module_id}.star_traces[{index}].role_hint"),
    }


def validate_module(value: Any, field_id: str, index: int) -> dict[str, Any]:
    module = require_object(value, f"{field_id}.modules[{index}]")
    module_id = require_string(module.get("module_id"), f"{field_id}.modules[{index}].module_id")
    if require_string(module.get("module_type"), f"{module_id}.module_type") != "radial_rosette":
        fail(f"{module_id}.module_type must be radial_rosette")
    divisions = integer_at_least(module.get("divisions"), 3, f"{module_id}.divisions")
    rings = [validate_ring(module_id, ring, ring_index) for ring_index, ring in enumerate(require_list(module.get("rings"), f"{module_id}.rings"))]
    if len(rings) < 1:
        fail(f"{module_id}.rings must not be empty")
    seen_rings: set[str] = set()
    previous_radius = 0.0
    for ring in rings:
        if ring["ring_id"] in seen_rings:
            fail(f"{module_id}.rings duplicate ring_id: {ring['ring_id']}")
        seen_rings.add(ring["ring_id"])
        if ring["radius_m"] <= previous_radius:
            fail(f"{module_id}.rings radius_m must increase")
        previous_radius = ring["radius_m"]
    traces = [
        validate_star_trace(module_id, divisions, seen_rings, trace, trace_index)
        for trace_index, trace in enumerate(require_list(module.get("star_traces", []), f"{module_id}.star_traces"))
    ]
    return {
        "module_id": module_id,
        "module_type": "radial_rosette",
        "divisions": divisions,
        "rings": rings,
        "star_traces": traces,
    }


def validate_instance(value: Any, field_id: str, index: int, module_ids: set[str], bounds: dict[str, float]) -> dict[str, Any]:
    instance = require_object(value, f"{field_id}.instances[{index}]")
    instance_id = require_string(instance.get("instance_id"), f"{field_id}.instances[{index}].instance_id")
    module_id = require_string(instance.get("module_id"), f"{instance_id}.module_id")
    if module_id not in module_ids:
        fail(f"{instance_id}.module_id references unknown module: {module_id}")
    center = finite_vector(instance.get("center_m"), f"{instance_id}.center_m", 2)
    if not (0.0 <= center[0] <= bounds["width"] and 0.0 <= center[1] <= bounds["height"]):
        fail(f"{instance_id}.center_m must be inside bounds")
    return {
        "instance_id": instance_id,
        "module_id": module_id,
        "center_m": center,
        "role_hint": require_string(instance.get("role_hint"), f"{instance_id}.role_hint"),
    }


def validate_connector(value: Any, field_id: str, index: int, instance_ids: set[str]) -> dict[str, Any]:
    connector = require_object(value, f"{field_id}.connector_lines[{index}]")
    connector_id = require_string(connector.get("connector_id"), f"{field_id}.connector_lines[{index}].connector_id")
    from_id = require_string(connector.get("from_instance_id"), f"{connector_id}.from_instance_id")
    to_id = require_string(connector.get("to_instance_id"), f"{connector_id}.to_instance_id")
    if from_id not in instance_ids:
        fail(f"{connector_id}.from_instance_id references unknown instance: {from_id}")
    if to_id not in instance_ids:
        fail(f"{connector_id}.to_instance_id references unknown instance: {to_id}")
    if from_id == to_id:
        fail(f"{connector_id} must connect two different instances")
    return {
        "connector_id": connector_id,
        "from_instance_id": from_id,
        "to_instance_id": to_id,
        "selected": bool(connector.get("selected", False)),
        "role_hint": require_string(connector.get("role_hint"), f"{connector_id}.role_hint"),
    }


def validate_selection(value: Any, field_id: str, index: int) -> dict[str, Any]:
    selection = require_object(value, f"{field_id}.selections[{index}]")
    selection_id = require_string(selection.get("selection_id"), f"{field_id}.selections[{index}].selection_id")
    if require_string(selection.get("selection_type"), f"{selection_id}.selection_type") != "edges":
        fail(f"{selection_id}.selection_type must be edges")
    selector = require_object(selection.get("selector"), f"{selection_id}.selector")
    if require_string(selector.get("kind"), f"{selection_id}.selector.kind") != "edge_tag_query":
        fail(f"{selection_id}.selector.kind must be edge_tag_query")
    return {
        "selection_id": selection_id,
        "selection_type": "edges",
        "selector": {"kind": "edge_tag_query", "tag": require_string(selector.get("tag"), f"{selection_id}.selector.tag")},
        "architectural_roles": require_string_list(selection.get("architectural_roles"), f"{selection_id}.architectural_roles"),
    }


def validate_field(value: Any, operations: set[str], index: int) -> dict[str, Any]:
    field = require_object(value, f"fields[{index}]")
    field_id = require_string(field.get("field_id"), f"fields[{index}].field_id")
    operation = require_string(field.get("geometry_operation"), f"{field_id}.geometry_operation")
    if operation not in operations:
        fail(f"{field_id}.geometry_operation references unknown geometry operation: {operation}")
    bounds_source = require_object(field.get("bounds_m"), f"{field_id}.bounds_m")
    bounds = {
        "width": positive_float(bounds_source.get("width"), f"{field_id}.bounds_m.width"),
        "height": positive_float(bounds_source.get("height"), f"{field_id}.bounds_m.height"),
    }
    modules = [validate_module(module, field_id, module_index) for module_index, module in enumerate(require_list(field.get("modules"), f"{field_id}.modules"))]
    module_ids = {module["module_id"] for module in modules}
    if len(module_ids) != len(modules):
        fail(f"{field_id}.modules module_ids must be unique")
    instances = [
        validate_instance(instance, field_id, instance_index, module_ids, bounds)
        for instance_index, instance in enumerate(require_list(field.get("instances"), f"{field_id}.instances"))
    ]
    instance_ids = {instance["instance_id"] for instance in instances}
    if len(instance_ids) != len(instances):
        fail(f"{field_id}.instances instance_ids must be unique")
    connectors = [
        validate_connector(connector, field_id, connector_index, instance_ids)
        for connector_index, connector in enumerate(require_list(field.get("connector_lines", []), f"{field_id}.connector_lines"))
    ]
    selections = [
        validate_selection(selection, field_id, selection_index)
        for selection_index, selection in enumerate(require_list(field.get("selections"), f"{field_id}.selections"))
    ]
    require_false_claims(field.get("no_claims"), f"{field_id}.no_claims")
    return {
        "field_id": field_id,
        "geometry_operation": operation,
        "description": require_string(field.get("description"), f"{field_id}.description"),
        "bounds_m": bounds,
        "modules": modules,
        "instances": instances,
        "connector_lines": connectors,
        "selections": selections,
        "validation_expectations": require_object(field.get("validation_expectations"), f"{field_id}.validation_expectations"),
        "no_claims": field["no_claims"],
    }


def validate_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    if bundle.get("schema") != SCHEMA:
        fail(f"bundle schema must be {SCHEMA}")
    if require_object(bundle.get("rules"), "rules") != REQUIRED_RULES:
        fail("bundle rules must match pattern field source boundaries")
    operations = load_operation_terms()
    fields_source = require_list(bundle.get("fields"), "fields")
    if bundle.get("field_count") != len(fields_source):
        fail("bundle field_count must match fields length")
    fields = [validate_field(field, operations, index) for index, field in enumerate(fields_source)]
    seen: set[str] = set()
    for field in fields:
        if field["field_id"] in seen:
            fail(f"duplicate field_id: {field['field_id']}")
        seen.add(field["field_id"])
    return fields


def point_on_circle(center: list[float], radius: float, index: int, divisions: int) -> list[float]:
    angle = math.tau * index / divisions
    return [
        round(center[0] + math.cos(angle) * radius, 6),
        round(center[1] + math.sin(angle) * radius, 6),
    ]


def edge_record(edge_id: str, a: str, b: str, edge_type: str, tags: list[str]) -> dict[str, Any]:
    return {"edge_id": edge_id, "from": a, "to": b, "edge_type": edge_type, "tags": tags}


def compile_field(bundle: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    module_by_id = {module["module_id"]: module for module in field["modules"]}
    point_by_id: dict[str, list[float]] = {}
    points: list[dict[str, Any]] = []
    circles: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for instance in field["instances"]:
        instance_id = instance["instance_id"]
        module = module_by_id[instance["module_id"]]
        center_id = f"{instance_id}_center"
        point_by_id[center_id] = instance["center_m"]
        points.append(
            {
                "point_id": center_id,
                "xy_m": instance["center_m"],
                "instance_id": instance_id,
                "module_id": module["module_id"],
                "tags": ["center", f"instance:{instance_id}", f"module:{module['module_id']}"],
            }
        )
        for ring in module["rings"]:
            ring_id = ring["ring_id"]
            circles.append(
                {
                    "circle_id": f"{instance_id}_{ring_id}_circle",
                    "instance_id": instance_id,
                    "ring_id": ring_id,
                    "center_point_id": center_id,
                    "radius_m": ring["radius_m"],
                    "role_hint": ring["role_hint"],
                    "tags": ["guide_circle", f"instance:{instance_id}", f"ring:{ring_id}"],
                }
            )
            for index in range(module["divisions"]):
                point_id = f"{instance_id}_{ring_id}_p_{index:02d}"
                xy = point_on_circle(instance["center_m"], ring["radius_m"], index, module["divisions"])
                point_by_id[point_id] = xy
                points.append(
                    {
                        "point_id": point_id,
                        "xy_m": xy,
                        "instance_id": instance_id,
                        "module_id": module["module_id"],
                        "ring_id": ring_id,
                        "division_index": index,
                        "tags": ["ring_point", f"instance:{instance_id}", f"module:{module['module_id']}", f"ring:{ring_id}"],
                    }
                )
                nxt = (index + 1) % module["divisions"]
                edges.append(
                    edge_record(
                        f"{instance_id}_{ring_id}_ring_{index:02d}_{nxt:02d}",
                        point_id,
                        f"{instance_id}_{ring_id}_p_{nxt:02d}",
                        "ring",
                        ["guide", "ring", f"instance:{instance_id}", f"module:{module['module_id']}", f"ring:{ring_id}"],
                    )
                )
        outer_ring_id = module["rings"][-1]["ring_id"]
        for index in range(module["divisions"]):
            edges.append(
                edge_record(
                    f"{instance_id}_radial_{index:02d}",
                    center_id,
                    f"{instance_id}_{outer_ring_id}_p_{index:02d}",
                    "radial",
                    ["guide", "radial", f"instance:{instance_id}", f"module:{module['module_id']}"],
                )
            )
        for trace in module["star_traces"]:
            for index in range(module["divisions"]):
                target = (index + trace["step"]) % module["divisions"]
                selected_tag = f"selected:{trace['role_hint']}" if trace["selected"] else "guide"
                edges.append(
                    edge_record(
                        f"{instance_id}_{trace['trace_id']}_{index:02d}_{target:02d}",
                        f"{instance_id}_{trace['ring_id']}_p_{index:02d}",
                        f"{instance_id}_{trace['ring_id']}_p_{target:02d}",
                        "star_trace",
                        [
                            "star_trace",
                            selected_tag,
                            f"instance:{instance_id}",
                            f"module:{module['module_id']}",
                            f"ring:{trace['ring_id']}",
                            f"trace:{trace['trace_id']}",
                        ],
                    )
                )
    instance_center_id = {instance["instance_id"]: f"{instance['instance_id']}_center" for instance in field["instances"]}
    for connector in field["connector_lines"]:
        tags = ["connector", "guide", f"connector:{connector['connector_id']}"]
        if connector["selected"]:
            tags.append("selected:connector")
        edges.append(
            edge_record(
                connector["connector_id"],
                instance_center_id[connector["from_instance_id"]],
                instance_center_id[connector["to_instance_id"]],
                "connector",
                tags,
            )
        )
    compiled_selections: list[dict[str, Any]] = []
    selected_edge_refs: list[str] = []
    for selection in field["selections"]:
        tag = selection["selector"]["tag"]
        edge_ids = [edge["edge_id"] for edge in edges if tag in edge["tags"]]
        if not edge_ids:
            fail(f"{selection['selection_id']} selected no edges for tag `{tag}`")
        selected_edge_refs.extend(edge_ids)
        compiled_selections.append(
            {
                "selection_id": selection["selection_id"],
                "selection_type": "edges",
                "architectural_roles": selection["architectural_roles"],
                "selector": selection["selector"],
                "edge_ids": edge_ids,
                "selected_count": len(edge_ids),
            }
        )
    compiled = {
        "schema": "gameguy_pattern_field_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "field_id": field["field_id"],
        "geometry_operation": field["geometry_operation"],
        "description": field["description"],
        "units": bundle.get("units", "abstract_meter"),
        "bounds_m": field["bounds_m"],
        "modules": field["modules"],
        "instances": field["instances"],
        "circles": circles,
        "points": points,
        "edges": edges,
        "selections": compiled_selections,
        "summary": {
            "instance_count": len(field["instances"]),
            "circle_count": len(circles),
            "point_count": len(points),
            "edge_count": len(edges),
            "selection_count": len(compiled_selections),
            "selected_edge_reference_count": len(selected_edge_refs),
            "unique_selected_edge_count": len(set(selected_edge_refs)),
        },
        "rules": {
            "source_field_only": True,
            "selected_edges_named": True,
            "blender_is_adapter_layer": True,
            "no_mesh_output": True,
            "no_media_output_in_repo": True,
        },
        "validation_expectations": field["validation_expectations"],
        "no_claims": field["no_claims"],
    }
    for key, value in compiled["summary"].items():
        expected_value = field["validation_expectations"].get(key)
        if expected_value is not None and expected_value != value:
            fail(f"{field['field_id']}.validation_expectations.{key} must be {value}")
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
    point_by_id = {point["point_id"]: point["xy_m"] for point in compiled["points"]}
    selected_edge_ids = {edge_id for selection in compiled["selections"] for edge_id in selection["edge_ids"]}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        "<style>",
        ".bg{fill:#fbfaf6}.sheet{fill:none;stroke:#b9b3a7;stroke-width:1.4}.circle{fill:none;stroke:#c9c1b6;stroke-width:1;opacity:.55}.guide{stroke:#b9b3a7;stroke-width:.9;opacity:.5}.connector{stroke:#9b958c;stroke-width:1;opacity:.45}.selected{stroke:#1f1f1f;stroke-width:1.7;opacity:.78}.center{fill:#202020}.label{font:18px monospace;fill:#202020}.small{font:14px monospace;fill:#4b4b4b}",
        "</style>",
        f'<rect class="bg" x="0" y="0" width="{size}" height="{size}" />',
        f'<rect class="sheet" x="{margin:.3f}" y="{margin:.3f}" width="{bounds["width"] * scale:.3f}" height="{bounds["height"] * scale:.3f}" />',
    ]
    for circle in compiled["circles"]:
        cx, cy = svg_point(point_by_id[circle["center_point_id"]], bounds, scale, margin)
        lines.append(f'<circle class="circle" cx="{cx:.3f}" cy="{cy:.3f}" r="{circle["radius_m"] * scale:.3f}" />')
    for edge in compiled["edges"]:
        if edge["edge_id"] in selected_edge_ids:
            continue
        klass = "connector" if edge["edge_type"] == "connector" else "guide"
        lines.append(svg_line(point_by_id[edge["from"]], point_by_id[edge["to"]], bounds, scale, margin, klass))
    for edge in compiled["edges"]:
        if edge["edge_id"] in selected_edge_ids:
            lines.append(svg_line(point_by_id[edge["from"]], point_by_id[edge["to"]], bounds, scale, margin, "selected"))
    for point in compiled["points"]:
        if "center" in point["tags"]:
            x, y = svg_point(point["xy_m"], bounds, scale, margin)
            lines.append(f'<circle class="center" cx="{x:.3f}" cy="{y:.3f}" r="3.2" />')
    lines.append(f'<text class="label" x="30" y="38">{compiled["field_id"]}</text>')
    lines.append(
        f'<text class="small" x="30" y="62">instances={compiled["summary"]["instance_count"]} '
        f'edges={compiled["summary"]["edge_count"]} selected={compiled["summary"]["unique_selected_edge_count"]}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def write_outputs(bundle: dict[str, Any], compiled_fields: list[dict[str, Any]], out_root: Path, clean: bool) -> dict[str, Any]:
    if clean and out_root.exists():
        shutil.rmtree(out_root)
    (out_root / "fields").mkdir(parents=True, exist_ok=True)
    (out_root / "svg").mkdir(parents=True, exist_ok=True)
    manifest_fields = []
    for compiled in compiled_fields:
        field_path = out_root / "fields" / f"{compiled['field_id']}.json"
        svg_path = out_root / "svg" / f"{compiled['field_id']}.svg"
        field_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        svg_path.write_text(render_svg(compiled), encoding="utf-8")
        manifest_fields.append(
            {
                "field_id": compiled["field_id"],
                "path": f"fields/{compiled['field_id']}.json",
                "svg_path": f"svg/{compiled['field_id']}.svg",
                "instance_count": compiled["summary"]["instance_count"],
                "edge_count": compiled["summary"]["edge_count"],
                "selection_count": compiled["summary"]["selection_count"],
                "unique_selected_edge_count": compiled["summary"]["unique_selected_edge_count"],
            }
        )
    manifest = {
        "schema": "gameguy_pattern_field_manifest_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "field_count": len(manifest_fields),
        "fields": manifest_fields,
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
    parser = argparse.ArgumentParser(description="Compile multi-center pattern field source recipes.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    bundle = load_json(bundle_path)
    fields = validate_bundle(bundle)
    compiled_fields = [compile_field(bundle, field) for field in fields]
    if args.validate_only:
        edge_count = sum(field["summary"]["edge_count"] for field in compiled_fields)
        print(f"compiled pattern fields={len(compiled_fields)} edges={edge_count} out=<validate-only>")
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = write_outputs(bundle, compiled_fields, out_root, args.clean)
    edge_count = sum(field["edge_count"] for field in manifest["fields"])
    selected_count = sum(field["unique_selected_edge_count"] for field in manifest["fields"])
    print(f"compiled pattern fields={manifest['field_count']} edges={edge_count} selected={selected_count} out={out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
