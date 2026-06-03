#!/usr/bin/env python3
"""Compile construction graph cell-selection recipes into deterministic JSON.

This is the middle source layer:

construction graph JSON -> closed ring-band cells -> named cell selections

It intentionally does not execute Blender, create mesh exports, or write
repo-local generated media. JSON and SVG previews are written under /tmp by
default.
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
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "sacred_geometry" / "construction_cell_selection_recipes_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_construction_cell_selection_v0")
SACRED_GRAPH_COMPILER = ROOT / "scripts" / "compile_sacred_graph_v0.py"
DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SCHEMA = "construction_cell_selection_recipe_bundle_v0"
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
    "cells_are_selection_source": True,
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


def integer_at_least(value: Any, minimum: int, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def require_false_claims(value: Any, field: str) -> None:
    if require_object(value, field) != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")


def load_sacred_graph_compiler() -> ModuleType:
    spec = importlib.util.spec_from_file_location("compile_sacred_graph_v0", SACRED_GRAPH_COMPILER)
    if spec is None or spec.loader is None:
        fail(f"could not import {repo_display_path(SACRED_GRAPH_COMPILER)}")
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


def validate_selector(selector: dict[str, Any], field: str) -> dict[str, Any]:
    kind = require_string(selector.get("kind"), f"{field}.kind")
    band_id = require_string(selector.get("band_id"), f"{field}.band_id")
    if kind == "cell_orbit":
        return {
            "kind": kind,
            "band_id": band_id,
            "start_index": integer_at_least(selector.get("start_index"), 0, f"{field}.start_index"),
            "step": integer_at_least(selector.get("step"), 1, f"{field}.step"),
            "count": integer_at_least(selector.get("count"), 1, f"{field}.count"),
        }
    if kind == "cell_indices":
        indices = [
            integer_at_least(value, 0, f"{field}.indices[{index}]")
            for index, value in enumerate(require_list(selector.get("indices"), f"{field}.indices"))
        ]
        if not indices:
            fail(f"{field}.indices must not be empty")
        return {"kind": kind, "band_id": band_id, "indices": indices}
    fail(f"{field}.kind unsupported: {kind}")


def validate_selections(value: Any, field: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, selection_value in enumerate(require_list(value, field)):
        item = require_object(selection_value, f"{field}[{index}]")
        selection_id = require_string(item.get("selection_id"), f"{field}[{index}].selection_id")
        if selection_id in seen:
            fail(f"{field} duplicate selection_id: {selection_id}")
        seen.add(selection_id)
        if require_string(item.get("selection_type"), f"{selection_id}.selection_type") != "cells":
            fail(f"{selection_id}.selection_type must be cells")
        cascade_order = require_object(item.get("cascade_order"), f"{selection_id}.cascade_order")
        result.append(
            {
                "selection_id": selection_id,
                "selection_type": "cells",
                "selector": validate_selector(require_object(item.get("selector"), f"{selection_id}.selector"), f"{selection_id}.selector"),
                "architectural_roles": require_string_list(item.get("architectural_roles"), f"{selection_id}.architectural_roles"),
                "cascade_order": {
                    "kind": require_string(cascade_order.get("kind"), f"{selection_id}.cascade_order.kind"),
                    "tier_start": integer_at_least(cascade_order.get("tier_start"), 0, f"{selection_id}.cascade_order.tier_start"),
                    "tier_step": integer_at_least(cascade_order.get("tier_step"), 1, f"{selection_id}.cascade_order.tier_step"),
                },
            }
        )
    return result


def validate_selection_set(value: Any, operations: set[str], index: int) -> dict[str, Any]:
    item = require_object(value, f"selection_sets[{index}]")
    selection_set_id = require_string(item.get("selection_set_id"), f"selection_sets[{index}].selection_set_id")
    operation = require_string(item.get("geometry_operation"), f"{selection_set_id}.geometry_operation")
    if operation not in operations:
        fail(f"{selection_set_id}.geometry_operation references unknown geometry operation: {operation}")
    cell_derivation = require_object(item.get("cell_derivation"), f"{selection_set_id}.cell_derivation")
    if require_string(cell_derivation.get("kind"), f"{selection_set_id}.cell_derivation.kind") != "ring_band_radial_cells":
        fail(f"{selection_set_id}.cell_derivation.kind must be ring_band_radial_cells")
    if require_string(cell_derivation.get("ring_band_mode"), f"{selection_set_id}.cell_derivation.ring_band_mode") != "adjacent_rings":
        fail(f"{selection_set_id}.cell_derivation.ring_band_mode must be adjacent_rings")
    if cell_derivation.get("include_center_fan") is not False:
        fail(f"{selection_set_id}.cell_derivation.include_center_fan must be false in v0")
    require_false_claims(item.get("no_claims"), f"{selection_set_id}.no_claims")
    return {
        "selection_set_id": selection_set_id,
        "source_graph_id": require_string(item.get("source_graph_id"), f"{selection_set_id}.source_graph_id"),
        "geometry_operation": operation,
        "description": require_string(item.get("description"), f"{selection_set_id}.description"),
        "cell_derivation": {
            "kind": "ring_band_radial_cells",
            "ring_band_mode": "adjacent_rings",
            "include_center_fan": False,
        },
        "selections": validate_selections(item.get("selections"), f"{selection_set_id}.selections"),
        "validation_expectations": require_object(item.get("validation_expectations"), f"{selection_set_id}.validation_expectations"),
        "no_claims": item["no_claims"],
    }


def validate_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    if bundle.get("schema") != SCHEMA:
        fail(f"bundle schema must be {SCHEMA}")
    if require_object(bundle.get("rules"), "rules") != REQUIRED_RULES:
        fail("bundle rules must match construction cell selection source boundaries")
    graph_bundle_path = repo_path(bundle.get("source_graph_bundle"), "source_graph_bundle")
    if not graph_bundle_path.exists():
        fail(f"source_graph_bundle references missing file: {repo_display_path(graph_bundle_path)}")
    operations = load_operation_terms()
    selection_sets_source = require_list(bundle.get("selection_sets"), "selection_sets")
    if bundle.get("selection_set_count") != len(selection_sets_source):
        fail("bundle selection_set_count must match selection_sets length")
    selection_sets = [validate_selection_set(item, operations, index) for index, item in enumerate(selection_sets_source)]
    seen: set[str] = set()
    for selection_set in selection_sets:
        if selection_set["selection_set_id"] in seen:
            fail(f"duplicate selection_set_id: {selection_set['selection_set_id']}")
        seen.add(selection_set["selection_set_id"])
    return selection_sets


def compiled_graphs_from_source(graph_bundle_path: Path) -> dict[str, dict[str, Any]]:
    module = load_sacred_graph_compiler()
    graph_bundle = module.load_json(graph_bundle_path)
    graphs = module.validate_bundle(graph_bundle)
    return {graph["graph_id"]: module.compile_graph(graph_bundle, graph) for graph in graphs}


def compiled_graphs_from_manifest(manifest_path: Path) -> dict[str, dict[str, Any]]:
    manifest = load_json(manifest_path)
    if manifest.get("schema") != "gameguy_sacred_graph_manifest_v0":
        fail(f"{repo_display_path(manifest_path)} schema must be gameguy_sacred_graph_manifest_v0")
    base = manifest_path.parent
    result: dict[str, dict[str, Any]] = {}
    for index, graph_ref in enumerate(require_list(manifest.get("graphs"), "graph_manifest.graphs")):
        item = require_object(graph_ref, f"graph_manifest.graphs[{index}]")
        graph_id = require_string(item.get("graph_id"), f"graph_manifest.graphs[{index}].graph_id")
        graph_path = base / require_string(item.get("path"), f"graph_manifest.graphs[{index}].path")
        result[graph_id] = load_json(graph_path)
    return result


def band_id(inner_ring_id: str, outer_ring_id: str) -> str:
    return f"{inner_ring_id}_to_{outer_ring_id}"


def polygon_area(points: list[list[float]]) -> float:
    area = 0.0
    for index, point in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        area += point[0] * nxt[1] - nxt[0] * point[1]
    return round(abs(area) * 0.5, 9)


def centroid(points: list[list[float]]) -> list[float]:
    return [
        round(sum(point[0] for point in points) / len(points), 6),
        round(sum(point[1] for point in points) / len(points), 6),
    ]


def derive_cells(graph: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    divisions = integer_at_least(graph.get("divisions"), 3, f"{graph.get('graph_id', '<graph>')}.divisions")
    rings = require_list(graph.get("rings"), f"{graph['graph_id']}.rings")
    if len(rings) < 2:
        fail(f"{graph['graph_id']} requires at least two rings for cell derivation")
    point_by_id = {point["point_id"]: point["xy_m"] for point in require_list(graph.get("points"), f"{graph['graph_id']}.points")}
    bands: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    for ring_index in range(len(rings) - 1):
        inner_ring_id = require_string(require_object(rings[ring_index], f"{graph['graph_id']}.rings[{ring_index}]").get("ring_id"), f"rings[{ring_index}].ring_id")
        outer_ring_id = require_string(require_object(rings[ring_index + 1], f"{graph['graph_id']}.rings[{ring_index + 1}]").get("ring_id"), f"rings[{ring_index + 1}].ring_id")
        current_band_id = band_id(inner_ring_id, outer_ring_id)
        band_cells: list[str] = []
        for radial_index in range(divisions):
            nxt = (radial_index + 1) % divisions
            point_ids = [
                f"{inner_ring_id}_p_{radial_index:02d}",
                f"{inner_ring_id}_p_{nxt:02d}",
                f"{outer_ring_id}_p_{nxt:02d}",
                f"{outer_ring_id}_p_{radial_index:02d}",
            ]
            missing = [point_id for point_id in point_ids if point_id not in point_by_id]
            if missing:
                fail(f"{graph['graph_id']} missing point ids for cell derivation: {missing}")
            vertices = [point_by_id[point_id] for point_id in point_ids]
            cell_id = f"cell_{current_band_id}_{radial_index:02d}"
            band_cells.append(cell_id)
            cells.append(
                {
                    "cell_id": cell_id,
                    "band_id": current_band_id,
                    "inner_ring_id": inner_ring_id,
                    "outer_ring_id": outer_ring_id,
                    "radial_index": radial_index,
                    "next_radial_index": nxt,
                    "point_ids": point_ids,
                    "vertices_xy_m": vertices,
                    "centroid_xy_m": centroid(vertices),
                    "area_m2": polygon_area(vertices),
                    "edge_refs": [
                        f"ring_{inner_ring_id}_{radial_index:02d}_{nxt:02d}",
                        f"radial_{nxt:02d}_{inner_ring_id}_to_{outer_ring_id}",
                        f"ring_{outer_ring_id}_{radial_index:02d}_{nxt:02d}",
                        f"radial_{radial_index:02d}_{inner_ring_id}_to_{outer_ring_id}",
                    ],
                    "tags": [
                        "construction_cell",
                        f"band:{current_band_id}",
                        f"radial_index:{radial_index:02d}",
                        f"inner_ring:{inner_ring_id}",
                        f"outer_ring:{outer_ring_id}",
                    ],
                }
            )
        bands.append(
            {
                "band_id": current_band_id,
                "inner_ring_id": inner_ring_id,
                "outer_ring_id": outer_ring_id,
                "cell_ids": band_cells,
                "cell_count": len(band_cells),
            }
        )
    return bands, cells


def select_cell_ids(selector: dict[str, Any], bands: dict[str, dict[str, Any]], divisions: int) -> list[str]:
    selected_band_id = selector["band_id"]
    if selected_band_id not in bands:
        fail(f"selector references unknown band_id: {selected_band_id}")
    if selector["kind"] == "cell_orbit":
        result = []
        seen_indices: set[int] = set()
        index = selector["start_index"] % divisions
        for _ in range(selector["count"]):
            if index in seen_indices:
                fail(f"{selected_band_id} cell_orbit repeats radial index {index:02d}; reduce count or change step")
            seen_indices.add(index)
            result.append(f"cell_{selected_band_id}_{index:02d}")
            index = (index + selector["step"]) % divisions
        return result
    if selector["kind"] == "cell_indices":
        return [f"cell_{selected_band_id}_{index % divisions:02d}" for index in selector["indices"]]
    fail(f"selector kind unsupported: {selector['kind']}")


def compile_selection_set(bundle: dict[str, Any], selection_set: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    bands, cells = derive_cells(graph)
    band_by_id = {band["band_id"]: band for band in bands}
    cell_ids = {cell["cell_id"] for cell in cells}
    compiled_selections: list[dict[str, Any]] = []
    selected_cell_references: list[str] = []
    for selection in selection_set["selections"]:
        selected_ids = select_cell_ids(selection["selector"], band_by_id, graph["divisions"])
        unknown = sorted(set(selected_ids) - cell_ids)
        if unknown:
            fail(f"{selection['selection_id']} selected unknown cells: {unknown}")
        selected_cell_references.extend(selected_ids)
        compiled_selections.append(
            {
                "selection_id": selection["selection_id"],
                "selection_type": "cells",
                "architectural_roles": selection["architectural_roles"],
                "selector": selection["selector"],
                "cell_ids": selected_ids,
                "selected_count": len(selected_ids),
                "cascade_order": selection["cascade_order"],
            }
        )
    compiled = {
        "schema": "gameguy_construction_cell_selection_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "selection_set_id": selection_set["selection_set_id"],
        "source_graph_id": selection_set["source_graph_id"],
        "geometry_operation": selection_set["geometry_operation"],
        "description": selection_set["description"],
        "units": bundle.get("units", graph.get("units", "abstract_meter")),
        "cell_derivation": selection_set["cell_derivation"],
        "bands": bands,
        "cells": cells,
        "selections": compiled_selections,
        "summary": {
            "band_count": len(bands),
            "cell_count": len(cells),
            "selection_count": len(compiled_selections),
            "selected_cell_reference_count": len(selected_cell_references),
            "unique_selected_cell_count": len(set(selected_cell_references)),
        },
        "rules": {
            "source_cells_only": True,
            "selected_cells_named": True,
            "blender_is_adapter_layer": True,
            "no_mesh_output": True,
            "no_media_output_in_repo": True,
        },
        "validation_expectations": selection_set["validation_expectations"],
        "no_claims": selection_set["no_claims"],
    }
    for key, value in compiled["summary"].items():
        expected_value = selection_set["validation_expectations"].get(key)
        if expected_value is not None and expected_value != value:
            fail(f"{selection_set['selection_set_id']}.validation_expectations.{key} must be {value}")
    return compiled


def svg_point(point: list[float], scale: float, origin: float) -> tuple[float, float]:
    return origin + point[0] * scale, origin - point[1] * scale


def render_svg(compiled: dict[str, Any]) -> str:
    all_points = [vertex for cell in compiled["cells"] for vertex in cell["vertices_xy_m"]]
    radius = max(abs(value) for point in all_points for value in point) + 0.08
    size = 960
    center = size * 0.5
    scale = (size * 0.42) / radius
    selected: dict[str, str] = {}
    palette = ["#c76d3d", "#4f8aa0", "#8b6bb0", "#769b56", "#b08c44"]
    for index, selection in enumerate(compiled["selections"]):
        color = palette[index % len(palette)]
        for cell_id in selection["cell_ids"]:
            selected[cell_id] = color
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="960" viewBox="0 0 960 960">',
        "<style>",
        ".bg{fill:#fbfaf6}.cell{fill:none;stroke:#c7c0b5;stroke-width:1}.selected{stroke:#202020;stroke-width:1.6;opacity:.72}.label{font:18px monospace;fill:#202020}.small{font:14px monospace;fill:#4b4b4b}",
        "</style>",
        '<rect class="bg" x="0" y="0" width="960" height="960" />',
    ]
    for cell in compiled["cells"]:
        points = " ".join(
            f"{x:.3f},{y:.3f}"
            for x, y in (svg_point(vertex, scale, center) for vertex in cell["vertices_xy_m"])
        )
        fill = selected.get(cell["cell_id"])
        if fill:
            lines.append(f'<polygon class="selected" points="{points}" fill="{fill}" />')
        else:
            lines.append(f'<polygon class="cell" points="{points}" />')
    lines.append(f'<text class="label" x="28" y="42">{compiled["selection_set_id"]}</text>')
    lines.append(f'<text class="small" x="28" y="68">cells={compiled["summary"]["cell_count"]} selected={compiled["summary"]["unique_selected_cell_count"]}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def compile_all(bundle: dict[str, Any], selection_sets: list[dict[str, Any]], graphs_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []
    for selection_set in selection_sets:
        graph_id = selection_set["source_graph_id"]
        if graph_id not in graphs_by_id:
            fail(f"{selection_set['selection_set_id']} references unknown source_graph_id: {graph_id}")
        compiled.append(compile_selection_set(bundle, selection_set, graphs_by_id[graph_id]))
    return compiled


def write_outputs(bundle: dict[str, Any], compiled_sets: list[dict[str, Any]], out_root: Path, clean: bool) -> dict[str, Any]:
    if clean and out_root.exists():
        shutil.rmtree(out_root)
    (out_root / "cell_sets").mkdir(parents=True, exist_ok=True)
    (out_root / "svg").mkdir(parents=True, exist_ok=True)
    manifest_sets = []
    for compiled in compiled_sets:
        set_path = out_root / "cell_sets" / f"{compiled['selection_set_id']}.json"
        svg_path = out_root / "svg" / f"{compiled['selection_set_id']}.svg"
        set_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        svg_path.write_text(render_svg(compiled), encoding="utf-8")
        manifest_sets.append(
            {
                "selection_set_id": compiled["selection_set_id"],
                "source_graph_id": compiled["source_graph_id"],
                "path": f"cell_sets/{compiled['selection_set_id']}.json",
                "svg_path": f"svg/{compiled['selection_set_id']}.svg",
                "band_count": compiled["summary"]["band_count"],
                "cell_count": compiled["summary"]["cell_count"],
                "selection_count": compiled["summary"]["selection_count"],
                "unique_selected_cell_count": compiled["summary"]["unique_selected_cell_count"],
            }
        )
    manifest = {
        "schema": "gameguy_construction_cell_selection_manifest_v0",
        "source_bundle_schema": bundle["schema"],
        "source_bundle_id": bundle["bundle_id"],
        "selection_set_count": len(manifest_sets),
        "selection_sets": manifest_sets,
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
    parser = argparse.ArgumentParser(description="Compile construction cell selections from sacred graph output.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--graph-bundle", type=Path, help="Optional source graph bundle override used when --graph-manifest is absent.")
    parser.add_argument("--graph-manifest", type=Path, help="Optional compiled sacred graph manifest to consume.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    bundle = load_json(bundle_path)
    selection_sets = validate_bundle(bundle)
    if args.graph_manifest:
        graph_manifest_path = args.graph_manifest if args.graph_manifest.is_absolute() else ROOT / args.graph_manifest
        graphs_by_id = compiled_graphs_from_manifest(graph_manifest_path)
    else:
        graph_bundle_path = (
            args.graph_bundle if args.graph_bundle and args.graph_bundle.is_absolute()
            else ROOT / args.graph_bundle if args.graph_bundle
            else repo_path(bundle.get("source_graph_bundle"), "source_graph_bundle")
        )
        graphs_by_id = compiled_graphs_from_source(graph_bundle_path)
    compiled_sets = compile_all(bundle, selection_sets, graphs_by_id)
    if args.validate_only:
        cell_count = sum(compiled["summary"]["cell_count"] for compiled in compiled_sets)
        print(f"compiled construction cell selections={len(compiled_sets)} cells={cell_count} out=<validate-only>")
        return 0
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = write_outputs(bundle, compiled_sets, out_root, args.clean)
    cell_count = sum(selection_set["cell_count"] for selection_set in manifest["selection_sets"])
    selected_count = sum(selection_set["unique_selected_cell_count"] for selection_set in manifest["selection_sets"])
    print(
        "compiled construction cell selections="
        f"{manifest['selection_set_count']} cells={cell_count} selected={selected_count} out={out_root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
