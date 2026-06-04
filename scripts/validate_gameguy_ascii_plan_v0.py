#!/usr/bin/env python3
"""Validate measurement-backed ASCII planning artifacts."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "data" / "architecture" / "ascii_plans" / "single_post_ascii_plan_fixture_v0.json"
GEOMETRY_ROOT = ROOT / "geometry_dictionary"
TOOL_DICTIONARY = ROOT / "data" / "architecture" / "asset_mill" / "blender_tools" / "blender_tool_dictionary_v0.json"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
    "building_code_compliance": False,
}
ALLOWED_OPERATION_CATEGORIES = {"mesh_operation", "composition_operation", "transform"}


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


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{field} must be a boolean")
    return value


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{field} must be an integer >= {minimum}")
    return value


def require_number(value: Any, field: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        fail(f"{field} must be >= {minimum}")
    if maximum is not None and number > maximum:
        fail(f"{field} must be <= {maximum}")
    return number


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, field)
    if not allow_empty and not items:
        fail(f"{field} must not be empty")
    return [require_string(item, f"{field}[{index}]") for index, item in enumerate(items)]


def require_number_list(value: Any, field: str, length: int) -> list[float]:
    items = require_list(value, field)
    if len(items) != length:
        fail(f"{field} must contain {length} numbers")
    return [require_number(item, f"{field}[{index}]") for index, item in enumerate(items)]


def load_geometry_terms() -> dict[str, dict[str, Any]]:
    terms: dict[str, dict[str, Any]] = {}
    for path in sorted(GEOMETRY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = require_string(term.get("term_id"), f"{display_path(path)}.term_id")
        terms[term_id] = term
    return terms


def load_tool_ids() -> set[str]:
    dictionary = load_json(TOOL_DICTIONARY)
    if dictionary.get("schema") != "blender_tool_dictionary_v0":
        fail(f"{display_path(TOOL_DICTIONARY)} schema must be blender_tool_dictionary_v0")
    tools = require_list(dictionary.get("tools"), "tool_dictionary.tools")
    return {
        require_string(require_object(tool, f"tool_dictionary.tools[{index}]").get("tool_id"), f"tool_dictionary.tools[{index}].tool_id")
        for index, tool in enumerate(tools)
    }


def validate_operation_hints(values: Any, field: str, geometry_terms: dict[str, dict[str, Any]]) -> set[str]:
    operation_ids = set(require_string_list(values, field))
    for term_id in operation_ids:
        if term_id not in geometry_terms:
            fail(f"{field} references unknown geometry term: {term_id}")
        if geometry_terms[term_id].get("category") not in ALLOWED_OPERATION_CATEGORIES:
            fail(f"{field} must reference operation terms only: {term_id}")
    return operation_ids


def validate_tool_hints(values: Any, field: str, tool_ids: set[str]) -> set[str]:
    hints = set(require_string_list(values, field))
    unknown = sorted(hints - tool_ids)
    if unknown:
        fail(f"{field} references unknown Blender tool IDs: {unknown}")
    return hints


def validate_bbox_cells(value: Any, field: str, rows: int, columns: int) -> None:
    bbox = require_object(value, field)
    row_min = require_int(bbox.get("row_min"), f"{field}.row_min")
    row_max = require_int(bbox.get("row_max"), f"{field}.row_max")
    col_min = require_int(bbox.get("col_min"), f"{field}.col_min")
    col_max = require_int(bbox.get("col_max"), f"{field}.col_max")
    if row_min > row_max or col_min > col_max:
        fail(f"{field} min values must be <= max values")
    if row_max >= rows or col_max >= columns:
        fail(f"{field} exceeds grid bounds")


def validate_plan(path: Path) -> dict[str, Any]:
    plan = load_json(path)
    if plan.get("schema") != "gameguy_ascii_plan_v0":
        fail(f"{display_path(path)} schema must be gameguy_ascii_plan_v0")
    plan_id = require_string(plan.get("plan_id"), f"{display_path(path)}.plan_id")
    require_string(plan.get("status"), f"{plan_id}.status")
    source_ref = require_object(plan.get("source_ref"), f"{plan_id}.source_ref")
    require_string(source_ref.get("source_id"), f"{plan_id}.source_ref.source_id")
    require_string(source_ref.get("source_type"), f"{plan_id}.source_ref.source_type")
    require_string(source_ref.get("path"), f"{plan_id}.source_ref.path")
    require_bool(source_ref.get("accepted_as_style_source"), f"{plan_id}.source_ref.accepted_as_style_source")
    source_resolution = require_object(plan.get("source_resolution_px"), f"{plan_id}.source_resolution_px")
    source_width = require_int(source_resolution.get("width"), f"{plan_id}.source_resolution_px.width", minimum=1)
    source_height = require_int(source_resolution.get("height"), f"{plan_id}.source_resolution_px.height", minimum=1)
    minimum_dimension = require_int(source_resolution.get("minimum_dimension_px"), f"{plan_id}.source_resolution_px.minimum_dimension_px", minimum=1)
    if minimum_dimension != min(source_width, source_height):
        fail(f"{plan_id}.source_resolution_px.minimum_dimension_px must match min(width, height)")
    if minimum_dimension < 960:
        fail(f"{plan_id}.source_resolution_px.minimum_dimension_px must be >= 960")
    grid = require_object(plan.get("grid"), f"{plan_id}.grid")
    columns = require_int(grid.get("columns"), f"{plan_id}.grid.columns", minimum=1)
    rows = require_int(grid.get("rows"), f"{plan_id}.grid.rows", minimum=1)
    require_number(grid.get("cell_width_m"), f"{plan_id}.grid.cell_width_m", minimum=0.000001)
    require_number(grid.get("cell_height_m"), f"{plan_id}.grid.cell_height_m", minimum=0.000001)
    require_number(grid.get("cell_aspect_ratio"), f"{plan_id}.grid.cell_aspect_ratio", minimum=0.000001)
    require_string(grid.get("origin"), f"{plan_id}.grid.origin")
    background_glyph = require_string(grid.get("background_glyph"), f"{plan_id}.grid.background_glyph")
    if len(background_glyph) != 1:
        fail(f"{plan_id}.grid.background_glyph must be exactly one character")
    coordinate_model = require_object(plan.get("coordinate_model"), f"{plan_id}.coordinate_model")
    if require_string(coordinate_model.get("coordinate_space"), f"{plan_id}.coordinate_model.coordinate_space") != "ascii_grid_local_xz":
        fail(f"{plan_id}.coordinate_model.coordinate_space must be ascii_grid_local_xz")
    require_object(coordinate_model.get("axes"), f"{plan_id}.coordinate_model.axes")
    legend = require_list(plan.get("glyph_legend"), f"{plan_id}.glyph_legend")
    glyphs: set[str] = set()
    for index, item_value in enumerate(legend):
        item = require_object(item_value, f"{plan_id}.glyph_legend[{index}]")
        glyph = require_string(item.get("glyph"), f"{plan_id}.glyph_legend[{index}].glyph")
        if len(glyph) != 1:
            fail(f"{plan_id}.glyph_legend[{index}].glyph must be exactly one character")
        if glyph in glyphs:
            fail(f"{plan_id}.glyph_legend has duplicate glyph: {glyph!r}")
        glyphs.add(glyph)
        require_string(item.get("meaning"), f"{plan_id}.glyph_legend[{index}].meaning")
        require_string(item.get("default_role"), f"{plan_id}.glyph_legend[{index}].default_role")
    if background_glyph not in glyphs:
        fail(f"{plan_id}.glyph_legend must include background glyph")
    ascii_rows = require_string_list(plan.get("ascii_rows"), f"{plan_id}.ascii_rows")
    if len(ascii_rows) != rows:
        fail(f"{plan_id}.ascii_rows length must match grid rows")
    for row_index, row in enumerate(ascii_rows):
        if len(row) != columns:
            fail(f"{plan_id}.ascii_rows[{row_index}] must have {columns} characters, found {len(row)}")
        unknown = sorted(set(row) - glyphs)
        if unknown:
            fail(f"{plan_id}.ascii_rows[{row_index}] contains glyphs missing from legend: {unknown}")
    geometry_terms = load_geometry_terms()
    tool_ids = load_tool_ids()
    annotated_cells = require_list(plan.get("annotated_cells"), f"{plan_id}.annotated_cells")
    if not annotated_cells:
        fail(f"{plan_id}.annotated_cells must not be empty")
    cell_ids: set[str] = set()
    region_refs: set[str] = set()
    used_operations: set[str] = set()
    used_tools: set[str] = set()
    for index, cell_value in enumerate(annotated_cells):
        cell = require_object(cell_value, f"{plan_id}.annotated_cells[{index}]")
        cell_id = require_string(cell.get("cell_id"), f"{plan_id}.annotated_cells[{index}].cell_id")
        if cell_id in cell_ids:
            fail(f"{plan_id}.annotated_cells duplicate cell_id: {cell_id}")
        cell_ids.add(cell_id)
        row = require_int(cell.get("row"), f"{cell_id}.row")
        col = require_int(cell.get("col"), f"{cell_id}.col")
        if row >= rows or col >= columns:
            fail(f"{cell_id}.row/col exceeds grid bounds")
        glyph = require_string(cell.get("glyph"), f"{cell_id}.glyph")
        if len(glyph) != 1:
            fail(f"{cell_id}.glyph must be exactly one character")
        if ascii_rows[row][col] != glyph:
            fail(f"{cell_id}.glyph does not match ascii_rows[{row}][{col}]")
        require_number_list(cell.get("source_px_bbox"), f"{cell_id}.source_px_bbox", 4)
        require_number_list(cell.get("local_xz_bbox_m"), f"{cell_id}.local_xz_bbox_m", 4)
        require_number(cell.get("brightness"), f"{cell_id}.brightness", minimum=0, maximum=1)
        require_number(cell.get("edge_strength"), f"{cell_id}.edge_strength", minimum=0, maximum=1)
        require_string(cell.get("edge_direction"), f"{cell_id}.edge_direction")
        require_string(cell.get("geometry_role"), f"{cell_id}.geometry_role")
        region_refs.add(require_string(cell.get("region_id"), f"{cell_id}.region_id"))
        require_string_list(cell.get("measurement_refs"), f"{cell_id}.measurement_refs")
        used_operations.update(validate_operation_hints(cell.get("operation_hints"), f"{cell_id}.operation_hints", geometry_terms))
        used_tools.update(validate_tool_hints(cell.get("blender_tool_hints"), f"{cell_id}.blender_tool_hints", tool_ids))
        require_string(cell.get("depth_intent"), f"{cell_id}.depth_intent")
    regions = require_list(plan.get("regions"), f"{plan_id}.regions")
    region_ids: set[str] = set()
    for index, region_value in enumerate(regions):
        region = require_object(region_value, f"{plan_id}.regions[{index}]")
        region_id = require_string(region.get("region_id"), f"{plan_id}.regions[{index}].region_id")
        if region_id in region_ids:
            fail(f"{plan_id}.regions duplicate region_id: {region_id}")
        region_ids.add(region_id)
        require_string(region.get("label"), f"{region_id}.label")
        validate_bbox_cells(region.get("bbox_cells"), f"{region_id}.bbox_cells", rows, columns)
        require_number_list(region.get("bbox_m"), f"{region_id}.bbox_m", 4)
        require_string_list(region.get("role_tags"), f"{region_id}.role_tags")
        require_bool(region.get("accepted_for_generation"), f"{region_id}.accepted_for_generation")
        used_operations.update(validate_operation_hints(region.get("operation_hints"), f"{region_id}.operation_hints", geometry_terms))
        used_tools.update(validate_tool_hints(region.get("blender_tool_hints"), f"{region_id}.blender_tool_hints", tool_ids))
        require_string_list(region.get("manual_qc"), f"{region_id}.manual_qc")
    missing_regions = sorted(region_refs - region_ids)
    if missing_regions:
        fail(f"{plan_id}.annotated_cells reference unknown regions: {missing_regions}")
    measurement_policy = require_object(plan.get("measurement_policy"), f"{plan_id}.measurement_policy")
    if require_int(measurement_policy.get("minimum_source_dimension_px"), f"{plan_id}.measurement_policy.minimum_source_dimension_px", minimum=1) < 960:
        fail(f"{plan_id}.measurement_policy.minimum_source_dimension_px must be >= 960")
    require_bool(measurement_policy.get("measurement_survives_promotion"), f"{plan_id}.measurement_policy.measurement_survives_promotion")
    require_bool(measurement_policy.get("crop_packets_expected_for_detail"), f"{plan_id}.measurement_policy.crop_packets_expected_for_detail")
    tooling_policy = require_object(plan.get("blender_tooling_policy"), f"{plan_id}.blender_tooling_policy")
    if require_bool(tooling_policy.get("render_contract_allowed"), f"{plan_id}.blender_tooling_policy.render_contract_allowed"):
        fail(f"{plan_id}.blender_tooling_policy.render_contract_allowed must be false for source ASCII plans")
    require_bool(tooling_policy.get("tools_are_hints_until_tool_plan_compile"), f"{plan_id}.blender_tooling_policy.tools_are_hints_until_tool_plan_compile")
    require_bool(tooling_policy.get("ascii_cells_do_not_execute_blender"), f"{plan_id}.blender_tooling_policy.ascii_cells_do_not_execute_blender")
    require_object(plan.get("source_acceptance"), f"{plan_id}.source_acceptance")
    require_string_list(plan.get("validation_expectations"), f"{plan_id}.validation_expectations")
    if plan.get("no_claims") != FALSE_CLAIMS:
        fail(f"{plan_id}.no_claims must match required false claim flags")
    return {
        "schema": "gameguy_ascii_plan_validation_result_v0",
        "plan": display_path(path),
        "status": "pass",
        "columns": columns,
        "rows": rows,
        "annotated_cell_count": len(cell_ids),
        "region_count": len(region_ids),
        "operation_hint_count": len(used_operations),
        "blender_tool_hint_count": len(used_tools),
        "minimum_source_dimension_px": minimum_dimension,
        "render_contract_allowed": False,
        "generated_outputs_created": False,
        "operation_hints": sorted(used_operations),
        "blender_tool_hints": sorted(used_tools),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate gameguy_ascii_plan_v0 sources.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--json-report", type=Path, help="Optional path for validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan_path = args.plan if args.plan.is_absolute() else ROOT / args.plan
    result = validate_plan(plan_path)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS gameguy ASCII plan validation: "
        f"grid={result['columns']}x{result['rows']} "
        f"cells={result['annotated_cell_count']} "
        f"regions={result['region_count']} "
        f"ops={result['operation_hint_count']} "
        f"tools={result['blender_tool_hint_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
