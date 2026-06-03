#!/usr/bin/env python3
"""Compile source-owned asset polish recipes into deterministic JSON plans.

This compiler does not import Blender and does not create mesh/media outputs.
It turns architectural target language into an asset_polish_tool_plan_v0 record
that a later Blender adapter can execute.
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
DEFAULT_RECIPE = ROOT / "data" / "architecture" / "asset_mill" / "polish_recipes" / "asset_polish_tool_plan_recipes_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_asset_polish_tool_plan_v0")
GEOMETRY_DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SOURCE_SCHEMA = "asset_polish_tool_plan_recipe_bundle_v0"
PLAN_RECIPE_SCHEMA = "asset_polish_tool_plan_recipe_v0"
PLAN_SCHEMA = "asset_polish_tool_plan_v0"
MANIFEST_SCHEMA = "asset_polish_tool_plan_manifest_v0"
TOOL_DICTIONARY_SCHEMA = "blender_tool_dictionary_v0"
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
    "game_engine_integration": False,
}
ALLOWED_OPERATIONS = {
    "bevel_edges",
    "boolean_cut",
    "chamfer_edges",
    "extrude_along_normals",
    "inset_faces",
    "material_assign",
    "sweep_profile",
    "uv_unwrap",
    "weighted_normals",
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def repo_path(value: Any, field: str) -> Path:
    text = require_string(value, field)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        fail(f"{field} must be a relative repo path")
    return ROOT / path


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


def require_number(value: Any, field: str, *, positive: bool = False, nonzero: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number):
        fail(f"{field} must be finite")
    if positive and number <= 0.0:
        fail(f"{field} must be positive")
    if nonzero and number == 0.0:
        fail(f"{field} must be non-zero")
    return round(number, 6)


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    if not allow_empty and not value:
        fail(f"{field} must not be empty")
    return value


def require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    result = []
    for index, item in enumerate(require_list(value, field, allow_empty=allow_empty)):
        result.append(require_string(item, f"{field}[{index}]"))
    return result


def validate_false_claims(value: Any, field: str) -> dict[str, bool]:
    claims = require_object(value, field)
    if claims != FALSE_CLAIMS:
        fail(f"{field} must exactly match required false claim flags")
    return dict(claims)


def load_geometry_terms() -> set[str]:
    terms: set[str] = set()
    for path in sorted(GEOMETRY_DICTIONARY_ROOT.rglob("*.json")):
        if "schemas" in path.parts:
            continue
        term = load_json(path)
        term_id = require_string(term.get("term_id"), f"{display_path(path)}.term_id")
        terms.add(term_id)
    if "asset_polish_tool_plan" not in terms:
        fail("geometry dictionary must define asset_polish_tool_plan")
    return terms


def require_known_terms(values: Any, known: set[str], field: str) -> list[str]:
    result = require_string_list(values, field)
    for index, term in enumerate(result):
        if term not in known:
            fail(f"{field}[{index}] uses unknown geometry dictionary term `{term}`")
    return result


def validate_tool_dictionary(dictionary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if dictionary.get("schema") != TOOL_DICTIONARY_SCHEMA:
        fail(f"tool dictionary schema must be {TOOL_DICTIONARY_SCHEMA}")
    tools = require_list(dictionary.get("tools"), "tool_dictionary.tools")
    if dictionary.get("tool_count") != len(tools):
        fail("tool_dictionary.tool_count must match tools length")
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(tools):
        tool = require_object(item, f"tool_dictionary.tools[{index}]")
        tool_id = require_string(tool.get("tool_id"), f"tool_dictionary.tools[{index}].tool_id")
        if tool_id in result:
            fail(f"duplicate tool_id `{tool_id}`")
        require_string(tool.get("stage"), f"{tool_id}.stage")
        require_bool(tool.get("deterministic"), f"{tool_id}.deterministic")
        result[tool_id] = tool
    return result


def validate_dimensions(value: Any, field: str) -> dict[str, float]:
    dimensions = require_object(value, field)
    return {
        "width": require_number(dimensions.get("width"), f"{field}.width", positive=True),
        "depth": require_number(dimensions.get("depth"), f"{field}.depth", positive=True),
        "height": require_number(dimensions.get("height"), f"{field}.height", positive=True),
    }


def validate_target(value: Any, index: int) -> dict[str, Any]:
    target = require_object(value, f"targets[{index}]")
    target_id = require_string(target.get("target_id"), f"targets[{index}].target_id")
    selector = require_object(target.get("selector"), f"{target_id}.selector")
    require_string(selector.get("kind"), f"{target_id}.selector.kind")
    normalized = {
        "target_id": target_id,
        "architectural_terms": require_string_list(target.get("architectural_terms"), f"{target_id}.architectural_terms"),
        "source_part_ids": require_string_list(target.get("source_part_ids"), f"{target_id}.source_part_ids"),
        "selector": selector,
        "material_role": require_string(target.get("material_role"), f"{target_id}.material_role"),
    }
    return normalized


def validate_step_params(operation: str, params: dict[str, Any], field: str) -> dict[str, Any]:
    normalized = dict(params)
    if operation in {"bevel_edges", "chamfer_edges"}:
        require_number(params.get("width_m"), f"{field}.width_m", positive=True)
        require_int(params.get("segments"), f"{field}.segments", minimum=1)
        profile = require_number(params.get("profile"), f"{field}.profile")
        if not 0.0 <= profile <= 1.0:
            fail(f"{field}.profile must be between 0 and 1")
        require_bool(params.get("harden_normals"), f"{field}.harden_normals")
    elif operation == "inset_faces":
        require_number(params.get("inset_m"), f"{field}.inset_m", positive=True)
        require_number(params.get("depth_m"), f"{field}.depth_m", nonzero=True)
        require_string(params.get("panel_mode"), f"{field}.panel_mode")
        require_string_list(params.get("apply_to_faces"), f"{field}.apply_to_faces")
    elif operation == "extrude_along_normals":
        require_number(params.get("depth_m"), f"{field}.depth_m", nonzero=True)
        require_number(params.get("lip_width_m"), f"{field}.lip_width_m", positive=True)
        require_string(params.get("lip_profile"), f"{field}.lip_profile")
    elif operation == "boolean_cut":
        require_string(params.get("solver"), f"{field}.solver")
        require_number(params.get("cut_depth_m"), f"{field}.cut_depth_m", positive=True)
        require_bool(params.get("leave_shadow_panel"), f"{field}.leave_shadow_panel")
        require_bool(params.get("cleanup_cutters"), f"{field}.cleanup_cutters")
    elif operation == "sweep_profile":
        require_string(params.get("profile"), f"{field}.profile")
        require_number(params.get("projection_m"), f"{field}.projection_m", positive=True)
        require_number(params.get("height_m"), f"{field}.height_m", positive=True)
        require_bool(params.get("fill_caps"), f"{field}.fill_caps")
    elif operation == "material_assign":
        material_map = require_object(params.get("material_map"), f"{field}.material_map")
        if not material_map:
            fail(f"{field}.material_map must not be empty")
        for key, value in material_map.items():
            require_string(key, f"{field}.material_map key")
            require_string(value, f"{field}.material_map.{key}")
    elif operation == "weighted_normals":
        require_bool(params.get("keep_sharp"), f"{field}.keep_sharp")
        require_number(params.get("weight"), f"{field}.weight", positive=True)
    elif operation == "uv_unwrap":
        method = require_string(params.get("method"), f"{field}.method")
        if method not in {"smart_uv_project", "uv_unwrap"}:
            fail(f"{field}.method must be smart_uv_project or uv_unwrap")
        require_number(params.get("island_margin"), f"{field}.island_margin", positive=True)
        require_number(params.get("angle_limit_degrees"), f"{field}.angle_limit_degrees", positive=True)
    else:
        fail(f"{field} uses unsupported operation `{operation}`")
    return normalized


def validate_step(value: Any, index: int, target_ids: set[str], tool_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    step = require_object(value, f"sequence[{index}]")
    step_id = require_string(step.get("step_id"), f"sequence[{index}].step_id")
    operation = require_string(step.get("operation"), f"{step_id}.operation")
    if operation not in ALLOWED_OPERATIONS:
        fail(f"{step_id}.operation uses unsupported operation `{operation}`")
    tool_id = require_string(step.get("tool_id"), f"{step_id}.tool_id")
    if tool_id not in tool_map:
        fail(f"{step_id}.tool_id uses unknown tool `{tool_id}`")
    target = require_string(step.get("target"), f"{step_id}.target")
    if target not in target_ids:
        fail(f"{step_id}.target references unknown target `{target}`")
    params = validate_step_params(operation, require_object(step.get("params"), f"{step_id}.params"), f"{step_id}.params")
    tool = tool_map[tool_id]
    return {
        "step_index": index,
        "step_id": step_id,
        "operation": operation,
        "tool_id": tool_id,
        "stage": tool["stage"],
        "target": target,
        "params": params,
        "deterministic": bool(tool["deterministic"]),
    }


def validate_material_slots(value: Any) -> list[dict[str, str]]:
    result = []
    seen: set[str] = set()
    for index, item in enumerate(require_list(value, "material_slots")):
        slot = require_object(item, f"material_slots[{index}]")
        slot_id = require_string(slot.get("slot_id"), f"material_slots[{index}].slot_id")
        if slot_id in seen:
            fail(f"duplicate material slot `{slot_id}`")
        seen.add(slot_id)
        result.append(
            {
                "slot_id": slot_id,
                "material_role": require_string(slot.get("material_role"), f"material_slots[{index}].material_role"),
            }
        )
    return result


def compile_plan(recipe: dict[str, Any], geometry_terms: set[str], tool_map: dict[str, dict[str, Any]], terminology_reference: str) -> dict[str, Any]:
    if recipe.get("schema") != PLAN_RECIPE_SCHEMA:
        fail(f"plan recipe schema must be {PLAN_RECIPE_SCHEMA}")
    recipe_id = require_string(recipe.get("recipe_id"), "recipe_id")
    source_asset = require_object(recipe.get("source_asset"), f"{recipe_id}.source_asset")
    target_map: dict[str, dict[str, Any]] = {}
    for index, target_value in enumerate(require_list(recipe.get("targets"), f"{recipe_id}.targets")):
        target = validate_target(target_value, index)
        if target["target_id"] in target_map:
            fail(f"{recipe_id} duplicate target `{target['target_id']}`")
        target_map[target["target_id"]] = target
    steps = []
    seen_steps: set[str] = set()
    for index, step_value in enumerate(require_list(recipe.get("sequence"), f"{recipe_id}.sequence")):
        step = validate_step(step_value, index, set(target_map), tool_map)
        if step["step_id"] in seen_steps:
            fail(f"{recipe_id} duplicate step `{step['step_id']}`")
        seen_steps.add(step["step_id"])
        steps.append(step)
    geometry = require_known_terms(recipe.get("geometry_terms_used"), geometry_terms, f"{recipe_id}.geometry_terms_used")
    operations = require_known_terms(recipe.get("operations"), geometry_terms, f"{recipe_id}.operations")
    if "asset_polish_tool_plan" not in geometry or "asset_polish_tool_plan" not in operations:
        fail(f"{recipe_id} must declare asset_polish_tool_plan in geometry_terms_used and operations")
    expectations = require_object(recipe.get("validation_expectations"), f"{recipe_id}.validation_expectations")
    if expectations.get("target_count") != len(target_map):
        fail(f"{recipe_id}.validation_expectations.target_count must match targets")
    if expectations.get("step_count") != len(steps):
        fail(f"{recipe_id}.validation_expectations.step_count must match sequence")
    material_slots = validate_material_slots(recipe.get("material_slots"))
    if expectations.get("material_slot_count") != len(material_slots):
        fail(f"{recipe_id}.validation_expectations.material_slot_count must match material_slots")
    required_ops = set(require_string_list(expectations.get("required_operations"), f"{recipe_id}.validation_expectations.required_operations"))
    observed_ops = {step["operation"] for step in steps}
    if not required_ops.issubset(observed_ops):
        fail(f"{recipe_id}.validation_expectations.required_operations are not all present")
    dimensions = validate_dimensions(recipe.get("dimensions_m"), f"{recipe_id}.dimensions_m")
    no_claims = validate_false_claims(recipe.get("no_claims"), f"{recipe_id}.no_claims")
    stage_order = []
    for step in steps:
        if step["stage"] not in stage_order:
            stage_order.append(step["stage"])
    unique_tools = sorted({step["tool_id"] for step in steps})
    return {
        "schema": PLAN_SCHEMA,
        "plan_id": require_string(recipe.get("plan_id"), f"{recipe_id}.plan_id") + "_compiled",
        "source_recipe_id": recipe_id,
        "source_asset": {
            "asset_schema": require_string(source_asset.get("asset_schema"), f"{recipe_id}.source_asset.asset_schema"),
            "asset_id": require_string(source_asset.get("asset_id"), f"{recipe_id}.source_asset.asset_id"),
            "source_bundle": require_string(source_asset.get("source_bundle"), f"{recipe_id}.source_asset.source_bundle"),
            "source_bundle_schema": require_string(source_asset.get("source_bundle_schema"), f"{recipe_id}.source_asset.source_bundle_schema"),
            "source_asset_kind": require_string(source_asset.get("source_asset_kind"), f"{recipe_id}.source_asset.source_asset_kind"),
        },
        "asset_family": require_string(recipe.get("asset_family"), f"{recipe_id}.asset_family"),
        "style": require_string(recipe.get("style"), f"{recipe_id}.style"),
        "target_readiness": require_string(recipe.get("target_readiness"), f"{recipe_id}.target_readiness"),
        "units": "abstract_meter",
        "dimensions_m": dimensions,
        "terminology_reference": terminology_reference,
        "geometry_terms_used": geometry,
        "operations": operations,
        "terminology_terms": require_string_list(recipe.get("terminology_terms"), f"{recipe_id}.terminology_terms"),
        "targets": list(target_map.values()),
        "material_slots": material_slots,
        "steps": steps,
        "summary": {
            "target_count": len(target_map),
            "step_count": len(steps),
            "unique_tool_count": len(unique_tools),
            "unique_tools": unique_tools,
            "operation_count": len(observed_ops),
            "operations": sorted(observed_ops),
            "stage_order": stage_order,
            "non_deterministic_step_count": sum(1 for step in steps if not step["deterministic"]),
        },
        "rules": {
            "compiler_executes_blender": False,
            "writes_generated_media_or_mesh": False,
            "source_recipe_owns_design_decisions": True,
            "blender_adapter_executes_compiled_plan_only": True,
        },
        "no_claims": no_claims,
    }


def validate_bundle(bundle: dict[str, Any], recipe_path: Path) -> tuple[list[dict[str, Any]], str]:
    if bundle.get("schema") != SOURCE_SCHEMA:
        fail(f"{display_path(recipe_path)} schema must be {SOURCE_SCHEMA}")
    require_string(bundle.get("bundle_id"), "bundle_id")
    rules = require_object(bundle.get("rules"), "rules")
    for key in (
        "source_recipe_only",
        "deterministic_compiler",
        "no_blender_execution",
        "no_generated_media",
        "no_mesh_export",
        "blender_adapter_executes_compiled_plan_only",
    ):
        if require_bool(rules.get(key), f"rules.{key}") is not True:
            fail(f"rules.{key} must be true")
    dictionary_path = repo_path(bundle.get("tool_dictionary"), "tool_dictionary")
    terminology_path = repo_path(bundle.get("terminology_reference"), "terminology_reference")
    if not terminology_path.exists():
        fail(f"terminology_reference does not exist: {display_path(terminology_path)}")
    tool_map = validate_tool_dictionary(load_json(dictionary_path))
    geometry_terms = load_geometry_terms()
    recipes = require_list(bundle.get("plans"), "plans")
    if bundle.get("plan_count") != len(recipes):
        fail("plan_count must match plans length")
    plans = [compile_plan(recipe, geometry_terms, tool_map, display_path(terminology_path)) for recipe in recipes]
    return plans, display_path(terminology_path)


def build_manifest(recipe_path: Path, bundle: dict[str, Any], plans: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": MANIFEST_SCHEMA,
        "source_bundle": display_path(recipe_path),
        "source_bundle_schema": SOURCE_SCHEMA,
        "plan_schema": PLAN_SCHEMA,
        "plan_count": len(plans),
        "plans": [
            {
                "plan_id": plan["plan_id"],
                "source_recipe_id": plan["source_recipe_id"],
                "source_asset_id": plan["source_asset"]["asset_id"],
                "asset_family": plan["asset_family"],
                "path": f"plans/{plan['plan_id']}.json",
                "target_count": plan["summary"]["target_count"],
                "step_count": plan["summary"]["step_count"],
                "unique_tool_count": plan["summary"]["unique_tool_count"],
            }
            for plan in plans
        ],
        "rules": {
            "no_blender": True,
            "no_media": True,
            "no_mesh_export_files": True,
            "source_recipe_owns_design_decisions": True,
        },
        "source_rules": bundle["rules"],
    }


def compile_bundle(recipe_path: Path, out_root: Path, *, clean: bool, validate_only: bool) -> dict[str, Any]:
    bundle = load_json(recipe_path)
    plans, _terminology_reference = validate_bundle(bundle, recipe_path)
    manifest = build_manifest(recipe_path, bundle, plans)
    if not validate_only:
        if clean and out_root.exists():
            shutil.rmtree(out_root)
        for row, plan in zip(manifest["plans"], plans):
            write_json(out_root / row["path"], plan)
        write_json(out_root / "manifest.json", manifest)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile source asset polish recipes into deterministic JSON plans.")
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    recipe_path = args.recipe if args.recipe.is_absolute() else ROOT / args.recipe
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = compile_bundle(recipe_path, out_root, clean=args.clean, validate_only=args.validate_only)
    print(
        "PASS asset polish tool-plan compile: "
        f"plans={manifest['plan_count']} "
        f"steps={sum(row['step_count'] for row in manifest['plans'])} "
        f"targets={sum(row['target_count'] for row in manifest['plans'])} "
        f"out={'<validate-only>' if args.validate_only else out_root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
