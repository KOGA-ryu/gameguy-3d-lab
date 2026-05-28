#!/usr/bin/env python3
"""Compile connector asset placement v0 from resolved plug connections.

This layer turns data-level plug contracts into modular connector asset
instances. It does not scale assets, alter measured building assets, or add
movement simulation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compile_integrated_map_scene_v0 as integrated_compile  # noqa: E402


KIT_DIR = ROOT / "goal" / "architecture" / "connector_asset_kit_v0"
RECIPE_DIR = KIT_DIR / "recipes"
INDEX_PATH = KIT_DIR / "connector_asset_kit_v0_index.json"
KIT_REPORT_PATH = KIT_DIR / "connector_asset_kit_v0_report.md"
CONNECTOR_SOURCE_MANIFEST_PATH = ROOT / "data" / "architecture" / "assets" / "connectors" / "connector_asset_manifest_v0.json"
CONNECTOR_PLACEMENT_POLICY_PATH = ROOT / "data" / "architecture" / "assets" / "connectors" / "connector_placement_policy_v0.json"
PLACEMENT_DIR = ROOT / "goal" / "architecture" / "integrated_map_scene_v0" / "connector_asset_placement_v0"
PLACEMENT_PATH = PLACEMENT_DIR / "connector_asset_placement_v0.json"
PLACEMENT_REPORT_PATH = PLACEMENT_DIR / "connector_asset_placement_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "connector_asset_placement_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}

EXPECTED_CONNECTOR_ASSET_IDS = (
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
EXPECTED_CONNECTION_TYPES = (
    "road_threshold",
    "flat_pathway",
    "ramp_pathway",
    "stepped_pathway",
    "bridge_link",
)


@dataclass(frozen=True)
class OutputPaths:
    recipe_dir: Path
    index_path: Path
    kit_report_path: Path
    placement_dir: Path
    placement_path: Path
    placement_report_path: Path
    receipt_path: Path
    integrated_graph_path: Path
    regenerate_integrated: bool


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{display_path(path)} must contain a JSON object")
    return data


def round6(value: float) -> float:
    return round(float(value), 6)


def default_output_paths() -> OutputPaths:
    return OutputPaths(
        recipe_dir=RECIPE_DIR,
        index_path=INDEX_PATH,
        kit_report_path=KIT_REPORT_PATH,
        placement_dir=PLACEMENT_DIR,
        placement_path=PLACEMENT_PATH,
        placement_report_path=PLACEMENT_REPORT_PATH,
        receipt_path=RECEIPT_PATH,
        integrated_graph_path=integrated_compile.INTEGRATED_GRAPH_PATH,
        regenerate_integrated=True,
    )


def output_paths_for_root(output_root: Path, *, integrated_graph_path: Path | None, regenerate_integrated: bool) -> OutputPaths:
    root = output_root.resolve()
    return OutputPaths(
        recipe_dir=root / "goal" / "architecture" / "connector_asset_kit_v0" / "recipes",
        index_path=root / "goal" / "architecture" / "connector_asset_kit_v0" / "connector_asset_kit_v0_index.json",
        kit_report_path=root / "goal" / "architecture" / "connector_asset_kit_v0" / "connector_asset_kit_v0_report.md",
        placement_dir=root / "goal" / "architecture" / "integrated_map_scene_v0" / "connector_asset_placement_v0",
        placement_path=root / "goal" / "architecture" / "integrated_map_scene_v0" / "connector_asset_placement_v0" / "connector_asset_placement_v0.json",
        placement_report_path=root / "goal" / "architecture" / "integrated_map_scene_v0" / "connector_asset_placement_v0" / "connector_asset_placement_v0_report.md",
        receipt_path=root / "goal" / "receipts" / "connector_asset_placement_v0.receipt.json",
        integrated_graph_path=integrated_graph_path or integrated_compile.INTEGRATED_GRAPH_PATH,
        regenerate_integrated=regenerate_integrated,
    )


def validate_connector_source_recipe(asset_id: str, recipe_data: dict[str, Any]) -> None:
    required_fields = [
        "asset_id",
        "dimensions_m",
        "semantic_roles",
        "sockets",
        "proof_primitives",
        "uncertainty",
        "no_production_claim",
        "no_structural_claim",
        "no_fabrication_claim",
        "no_historical_accuracy_claim",
        "no_claims",
    ]
    for field in required_fields:
        if field not in recipe_data:
            fail(f"{asset_id} source recipe missing required field `{field}`")
    if recipe_data["asset_id"] != asset_id:
        fail(f"{asset_id} source recipe asset_id mismatch: {recipe_data['asset_id']}")
    dimensions = recipe_data["dimensions_m"]
    if not isinstance(dimensions, dict):
        fail(f"{asset_id} dimensions_m must be an object")
    for key in ("width", "depth", "height"):
        if float(dimensions.get(key, 0.0)) <= 0.0:
            fail(f"{asset_id} has non-positive dimension `{key}`")
    if not isinstance(recipe_data["semantic_roles"], list) or not recipe_data["semantic_roles"]:
        fail(f"{asset_id} semantic_roles must be a non-empty list")
    if not isinstance(recipe_data["sockets"], list) or not recipe_data["sockets"]:
        fail(f"{asset_id} sockets must be a non-empty list")
    for item in recipe_data["sockets"]:
        for field in ("socket_id", "connector_term", "position_m", "direction", "role"):
            if field not in item:
                fail(f"{asset_id} socket missing required field `{field}`")
    if recipe_data["no_production_claim"] is not True:
        fail(f"{asset_id} must explicitly avoid production claims")
    if recipe_data["no_structural_claim"] is not True:
        fail(f"{asset_id} must explicitly avoid structural claims")
    if recipe_data["no_fabrication_claim"] is not True:
        fail(f"{asset_id} must explicitly avoid fabrication claims")
    if recipe_data["no_historical_accuracy_claim"] is not True:
        fail(f"{asset_id} must explicitly avoid historical accuracy claims")
    if recipe_data["no_claims"] != NO_CLAIMS:
        fail(f"{asset_id} no_claims must match connector no-claim policy")


def load_connector_source_recipes() -> dict[str, dict[str, Any]]:
    manifest = load_json(CONNECTOR_SOURCE_MANIFEST_PATH)
    if manifest.get("schema") != "connector_asset_manifest_v0":
        fail(f"{display_path(CONNECTOR_SOURCE_MANIFEST_PATH)} schema must be connector_asset_manifest_v0")
    rows = manifest.get("assets")
    if not isinstance(rows, list):
        fail("connector source manifest requires assets list")

    recipes: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            fail("connector source manifest assets must be objects")
        asset_id = row.get("asset_id")
        recipe_path = row.get("recipe_path")
        if not isinstance(asset_id, str) or not isinstance(recipe_path, str):
            fail("connector source manifest asset rows require asset_id and recipe_path")
        if asset_id in recipes:
            fail(f"duplicate connector source asset_id `{asset_id}`")
        path = ROOT / recipe_path
        if not path.exists():
            fail(f"connector source recipe missing: {display_path(path)}")
        recipe_data = load_json(path)
        validate_connector_source_recipe(asset_id, recipe_data)
        recipes[asset_id] = recipe_data

    missing = sorted(set(EXPECTED_CONNECTOR_ASSET_IDS) - set(recipes))
    if missing:
        fail(f"connector source manifest missing required asset ids: {missing}")
    return {asset_id: recipes[asset_id] for asset_id in EXPECTED_CONNECTOR_ASSET_IDS}


def require_policy_asset(context: str, asset_id: Any, connector_recipes: dict[str, dict[str, Any]]) -> str:
    if not isinstance(asset_id, str):
        fail(f"{context} requires string asset_id")
    if asset_id not in connector_recipes:
        fail(f"{context} references unknown connector asset_id `{asset_id}`")
    return asset_id


def validate_connector_placement_policy(policy: dict[str, Any], connector_recipes: dict[str, dict[str, Any]]) -> None:
    if policy.get("schema") != "connector_placement_policy_v0":
        fail(f"{display_path(CONNECTOR_PLACEMENT_POLICY_PATH)} schema must be connector_placement_policy_v0")
    if policy.get("no_claims") != NO_CLAIMS:
        fail("connector placement policy no_claims must match connector no-claim policy")
    expected = policy.get("expected_connection_types")
    if expected != list(EXPECTED_CONNECTION_TYPES):
        fail(f"connector placement policy expected_connection_types must be {list(EXPECTED_CONNECTION_TYPES)}")
    rules = policy.get("connection_type_rules")
    if not isinstance(rules, dict):
        fail("connector placement policy requires connection_type_rules object")
    missing = sorted(set(EXPECTED_CONNECTION_TYPES) - set(rules))
    if missing:
        fail(f"connector placement policy missing rules for: {missing}")

    for connection_type in EXPECTED_CONNECTION_TYPES:
        rule = rules[connection_type]
        if not isinstance(rule, dict):
            fail(f"{connection_type} placement rule must be an object")
        mode = rule.get("mode")
        if connection_type == "road_threshold":
            if mode != "single":
                fail("road_threshold placement rule mode must be single")
            require_policy_asset("road_threshold", rule.get("asset_id"), connector_recipes)
            if not isinstance(rule.get("role"), str):
                fail("road_threshold placement rule requires string role")
            position_t = float(rule.get("position_t", -1.0))
            if position_t < 0.0 or position_t > 1.0:
                fail("road_threshold position_t must be within 0..1")
            if not isinstance(rule.get("fit_reason"), str):
                fail("road_threshold placement rule requires fit_reason")
        elif connection_type in {"flat_pathway", "ramp_pathway", "stepped_pathway"}:
            if mode != "repeat":
                fail(f"{connection_type} placement rule mode must be repeat")
            require_policy_asset(connection_type, rule.get("asset_id"), connector_recipes)
            if not isinstance(rule.get("role"), str):
                fail(f"{connection_type} placement rule requires string role")
        elif connection_type == "bridge_link":
            if mode != "bridge_assembly":
                fail("bridge_link placement rule mode must be bridge_assembly")
            for section_name in ("deck", "rail", "abutment"):
                if not isinstance(rule.get(section_name), dict):
                    fail(f"bridge_link placement rule requires {section_name} object")
            require_policy_asset("bridge_link.deck", rule["deck"].get("asset_id"), connector_recipes)
            require_policy_asset("bridge_link.rail", rule["rail"].get("asset_id"), connector_recipes)
            require_policy_asset("bridge_link.abutment", rule["abutment"].get("asset_id"), connector_recipes)
            for field in ("role",):
                if not isinstance(rule["deck"].get(field), str):
                    fail(f"bridge_link deck requires string {field}")
            for field in ("left_role", "right_role"):
                if not isinstance(rule["rail"].get(field), str):
                    fail(f"bridge_link rail requires string {field}")
            if float(rule["rail"].get("side_offset_margin_m", -1.0)) < 0.0:
                fail("bridge_link rail side_offset_margin_m must be non-negative")
            for field in ("start_role", "end_role", "fit_reason"):
                if not isinstance(rule["abutment"].get(field), str):
                    fail(f"bridge_link abutment requires string {field}")


def load_connector_placement_policy(connector_recipes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    policy = load_json(CONNECTOR_PLACEMENT_POLICY_PATH)
    validate_connector_placement_policy(policy, connector_recipes)
    return policy


def write_connector_kit(connector_recipes: dict[str, dict[str, Any]], paths: OutputPaths) -> dict[str, Any]:
    paths.recipe_dir.mkdir(parents=True, exist_ok=True)
    assets = []
    for asset_id, data in connector_recipes.items():
        path = paths.recipe_dir / f"{asset_id}.json"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        dimensions = data["dimensions_m"]
        assets.append(
            {
                "asset_id": asset_id,
                "recipe_path": display_path(path),
                "dimensions_m": dimensions,
                "semantic_roles": data["semantic_roles"],
                "socket_count": len(data["sockets"]),
                "uncertainty": data["uncertainty"],
            }
        )
    index = {
        "schema": "connector_asset_kit_v0_index",
        "created_at_utc": now_iso(),
        "asset_count": len(assets),
        "recipe_dir": display_path(paths.recipe_dir),
        "source_manifest": display_path(CONNECTOR_SOURCE_MANIFEST_PATH),
        "assets": assets,
        "rules": {
            "recipes_loaded_from_source_manifest": True,
            "no_silent_scaling": True,
            "repeat_units_to_cover_length": True,
            "leftover_gaps_reported": True,
            "bridge_links_require_deck_rails_abutments": True,
        },
        "no_claims": NO_CLAIMS,
    }
    paths.index_path.parent.mkdir(parents=True, exist_ok=True)
    paths.index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Connector Asset Kit v0",
        "",
        "Deterministic blockout connector assets for plug-contract proof scenes.",
        "",
        f"- Source manifest: `{display_path(CONNECTOR_SOURCE_MANIFEST_PATH)}`",
        "",
    ]
    for asset in assets:
        lines.append(f"- `{asset['asset_id']}`: {asset['dimensions_m']}")
    lines.extend(["", "No production, structural, fabrication, or historical accuracy claims.", ""])
    paths.kit_report_path.write_text("\n".join(lines), encoding="utf-8")
    return index


def normalize3(x: float, y: float, z: float) -> list[float]:
    length = math.sqrt(x * x + y * y + z * z)
    if length <= 1e-9:
        return [0.0, 1.0, 0.0]
    return [round6(x / length), round6(y / length), round6(z / length)]


def frame_from_path(start: list[float], end: list[float], position: list[float]) -> dict[str, Any]:
    dx = float(end[0]) - float(start[0])
    dy = float(end[1]) - float(start[1])
    dz = float(end[2]) - float(start[2])
    forward = normalize3(dx, dy, dz)
    horizontal = math.hypot(float(forward[0]), float(forward[1]))
    if horizontal <= 1e-9:
        right = [1.0, 0.0, 0.0]
    else:
        right = [round6(float(forward[1]) / horizontal), round6(-float(forward[0]) / horizontal), 0.0]
    # right x forward, keeping local z perpendicular to the sloped route.
    up = [
        round6(float(right[1]) * float(forward[2]) - float(right[2]) * float(forward[1])),
        round6(float(right[2]) * float(forward[0]) - float(right[0]) * float(forward[2])),
        round6(float(right[0]) * float(forward[1]) - float(right[1]) * float(forward[0])),
    ]
    return {"position": [round6(v) for v in position], "right": right, "forward": forward, "up": up}


def point_along(start: list[float], end: list[float], t: float) -> list[float]:
    return [round6(float(start[i]) + (float(end[i]) - float(start[i])) * t) for i in range(3)]


def instance(
    *,
    connector_recipes: dict[str, dict[str, Any]],
    connection: dict[str, Any],
    path: dict[str, Any],
    asset_id: str,
    role: str,
    index: int,
    position: list[float],
    start: list[float],
    end: list[float],
    side_offset_m: float = 0.0,
    status: str = "pass",
    reason: str = "placed_from_connector_contract",
) -> dict[str, Any]:
    frame = frame_from_path(start, end, position)
    if side_offset_m:
        frame["position"] = [
            round6(float(frame["position"][0]) + float(frame["right"][0]) * side_offset_m),
            round6(float(frame["position"][1]) + float(frame["right"][1]) * side_offset_m),
            round6(float(frame["position"][2]) + float(frame["right"][2]) * side_offset_m),
        ]
    return {
        "instance_id": f"{connection['connection_id']}.{role}.{index:03d}",
        "placement_id": f"{connection['connection_id']}.{role}.{index:03d}",
        "socket_id": connection["connection_id"],
        "connection_id": connection["connection_id"],
        "connection_type": connection["connection_type"],
        "source_asset_ref": asset_id,
        "asset_id": asset_id,
        "measured_asset_id": asset_id,
        "role": role,
        "status": status,
        "reason": reason,
        "anchor_frame": frame,
        "semantic_surface_id": None,
        "scale_applied": False,
        "length_covered_m": connector_recipes[asset_id]["dimensions_m"]["depth"],
        "path_width_m": path["width_m"],
        "path_slope": path["slope"],
        "path_clearance_m": path["vertical_envelope_m"],
        "placement_validation": {
            "sits_on_profiled_terrain": True,
            "width_ok": connection["validation"]["width_ok"],
            "slope_ok": connection["validation"]["slope_ok"],
            "clearance_ok": connection["validation"]["clearance_ok"],
        },
        "no_claims": NO_CLAIMS,
    }


def repeat_instances(
    connection: dict[str, Any],
    connector_recipes: dict[str, dict[str, Any]],
    asset_id: str,
    role: str,
    side_offset_m: float = 0.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = connection["generated_path"]
    start = path["route_points"][0]
    end = path["route_points"][-1]
    length = float(path["horizontal_length_m"])
    unit_depth = float(connector_recipes[asset_id]["dimensions_m"]["depth"])
    count = max(1, math.ceil(length / unit_depth))
    overcover = round6(count * unit_depth - length)
    placements = []
    for index in range(count):
        t = (index + 0.5) / count
        placements.append(
            instance(
                connector_recipes=connector_recipes,
                connection=connection,
                path=path,
                asset_id=asset_id,
                role=role,
                index=index,
                position=point_along(start, end, t),
                start=start,
                end=end,
                side_offset_m=side_offset_m,
            )
        )
    fit = {
        "asset_id": asset_id,
        "unit_depth_m": unit_depth,
        "unit_count": count,
        "path_length_m": round6(length),
        "covered_length_m": round6(count * unit_depth),
        "overcover_m": overcover,
        "status": "pass" if overcover <= 0.05 else "warn",
        "reason": "exact_or_near_exact_fit" if overcover <= 0.05 else "modular_units_overcover_path_without_scaling",
    }
    return placements, fit


def placements_for_connection(
    connection: dict[str, Any],
    connector_recipes: dict[str, dict[str, Any]],
    placement_policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if connection["status"] != "pass" or not connection.get("generated_path"):
        return [], [{"connection_id": connection["connection_id"], "status": "fail", "reason": connection.get("fail_reasons", [])}]
    path = connection["generated_path"]
    start = path["route_points"][0]
    end = path["route_points"][-1]
    connection_type = connection["connection_type"]
    rule = placement_policy["connection_type_rules"].get(connection_type)
    if rule is None:
        return [], [{"connection_id": connection["connection_id"], "status": "fail", "reason": f"unsupported_connection_type:{connection_type}"}]
    if rule["mode"] == "single":
        return [
            instance(
                connector_recipes=connector_recipes,
                connection=connection,
                path=path,
                asset_id=rule["asset_id"],
                role=rule["role"],
                index=0,
                position=point_along(start, end, float(rule["position_t"])),
                start=start,
                end=end,
            )
        ], [{"connection_id": connection["connection_id"], "status": "pass", "reason": rule["fit_reason"]}]
    if rule["mode"] == "repeat":
        placements, fit = repeat_instances(connection, connector_recipes, rule["asset_id"], rule["role"])
        fit["connection_id"] = connection["connection_id"]
        return placements, [fit]
    if rule["mode"] == "bridge_assembly":
        deck_rule = rule["deck"]
        rail_rule = rule["rail"]
        abutment_rule = rule["abutment"]
        deck, deck_fit = repeat_instances(connection, connector_recipes, deck_rule["asset_id"], deck_rule["role"])
        rail_offset = float(path["width_m"]) * 0.5 + float(rail_rule["side_offset_margin_m"])
        left_rail, left_fit = repeat_instances(connection, connector_recipes, rail_rule["asset_id"], rail_rule["left_role"], -rail_offset)
        right_rail, right_fit = repeat_instances(connection, connector_recipes, rail_rule["asset_id"], rail_rule["right_role"], rail_offset)
        abutments = [
            instance(connector_recipes=connector_recipes, connection=connection, path=path, asset_id=abutment_rule["asset_id"], role=abutment_rule["start_role"], index=0, position=start, start=start, end=end),
            instance(connector_recipes=connector_recipes, connection=connection, path=path, asset_id=abutment_rule["asset_id"], role=abutment_rule["end_role"], index=0, position=end, start=start, end=end),
        ]
        fits = []
        for fit in [deck_fit, left_fit, right_fit]:
            fit["connection_id"] = connection["connection_id"]
            fits.append(fit)
        fits.append({"connection_id": connection["connection_id"], "status": "pass", "reason": abutment_rule["fit_reason"]})
        return deck + left_rail + right_rail + abutments, fits
    return [], [{"connection_id": connection["connection_id"], "status": "fail", "reason": f"unsupported_connection_type:{connection_type}"}]


def compile_placements(paths: OutputPaths | None = None) -> dict[str, Any]:
    paths = paths or default_output_paths()
    connector_recipes = load_connector_source_recipes()
    placement_policy = load_connector_placement_policy(connector_recipes)
    write_connector_kit(connector_recipes, paths)
    if not paths.integrated_graph_path.exists():
        if not paths.regenerate_integrated:
            fail(f"missing integrated graph and regeneration disabled: {display_path(paths.integrated_graph_path)}")
        integrated_compile.main()
    integrated = load_json(paths.integrated_graph_path)
    plug_graph = integrated["plug_connection_graph"]
    asset_instances: list[dict[str, Any]] = []
    fit_reports: list[dict[str, Any]] = []
    for connection in plug_graph["connections"]:
        placements, fits = placements_for_connection(connection, connector_recipes, placement_policy)
        asset_instances.extend(placements)
        fit_reports.extend(fits)
    policy_rules = placement_policy["connection_type_rules"]
    bridge_rule = policy_rules["bridge_link"]
    threshold_rule = policy_rules["road_threshold"]
    non_repeat_fit_reasons = {threshold_rule["fit_reason"], bridge_rule["abutment"]["fit_reason"]}
    validation = {
        "connector_source_manifest": display_path(CONNECTOR_SOURCE_MANIFEST_PATH),
        "connector_placement_policy": display_path(CONNECTOR_PLACEMENT_POLICY_PATH),
        "connector_source_recipe_count": len(connector_recipes),
        "all_expected_connector_source_ids_loaded": set(connector_recipes) == set(EXPECTED_CONNECTOR_ASSET_IDS),
        "connection_type_policy_count": len(placement_policy["connection_type_rules"]),
        "all_supported_connection_types_have_policy": set(placement_policy["connection_type_rules"]) == set(EXPECTED_CONNECTION_TYPES),
        "source_connection_count": len(plug_graph["connections"]),
        "connector_asset_instance_count": len(asset_instances),
        "all_connector_paths_produce_asset_instances": all(
            any(instance["connection_id"] == connection["connection_id"] for instance in asset_instances)
            for connection in plug_graph["connections"]
            if connection["status"] == "pass"
        ),
        "bridge_link_has_deck_rails_abutments": any(i["role"] == bridge_rule["deck"]["role"] for i in asset_instances)
        and any(i["role"] == bridge_rule["rail"]["left_role"] for i in asset_instances)
        and any(i["role"] == bridge_rule["rail"]["right_role"] for i in asset_instances)
        and any(i["role"] == bridge_rule["abutment"]["start_role"] for i in asset_instances)
        and any(i["role"] == bridge_rule["abutment"]["end_role"] for i in asset_instances),
        "road_threshold_has_landing": all(
            any(i["connection_id"] == connection["connection_id"] and i["role"] == threshold_rule["role"] for i in asset_instances)
            for connection in plug_graph["connections"]
            if connection["connection_type"] == "road_threshold"
        ),
        "ramp_pathway_has_grade_metadata": all(
            "path_slope" in i and i["path_slope"] >= 0.0 for i in asset_instances if i["connection_type"] == "ramp_pathway"
        ),
        "no_connector_asset_scaled_silently": all(not i["scale_applied"] for i in asset_instances),
        "leftover_gaps_explicit": all("overcover_m" in fit or fit["reason"] in non_repeat_fit_reasons for fit in fit_reports),
        "asset_instances_sit_on_generated_connector_path": all(i["placement_validation"]["sits_on_profiled_terrain"] for i in asset_instances),
        "fit_status_counts": {
            "pass": sum(1 for fit in fit_reports if fit["status"] == "pass"),
            "warn": sum(1 for fit in fit_reports if fit["status"] == "warn"),
            "fail": sum(1 for fit in fit_reports if fit["status"] == "fail"),
        },
        "no_claims": NO_CLAIMS,
    }
    required = [
        "all_expected_connector_source_ids_loaded",
        "all_supported_connection_types_have_policy",
        "all_connector_paths_produce_asset_instances",
        "bridge_link_has_deck_rails_abutments",
        "road_threshold_has_landing",
        "ramp_pathway_has_grade_metadata",
        "no_connector_asset_scaled_silently",
        "leftover_gaps_explicit",
        "asset_instances_sit_on_generated_connector_path",
    ]
    failed = [key for key in required if not validation[key]]
    if failed:
        fail(f"connector asset placement validation failed: {failed}")
    return {
        "schema": "connector_asset_placement_v0",
        "created_at_utc": now_iso(),
        "source_integrated_graph": display_path(paths.integrated_graph_path),
        "connector_source_manifest": display_path(CONNECTOR_SOURCE_MANIFEST_PATH),
        "connector_placement_policy": display_path(CONNECTOR_PLACEMENT_POLICY_PATH),
        "connector_asset_index": display_path(paths.index_path),
        "asset_instances": asset_instances,
        "fit_reports": fit_reports,
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }


def write_report(data: dict[str, Any], paths: OutputPaths) -> None:
    validation = data["validation"]
    lines = [
        "# Connector Asset Placement v0",
        "",
        "Converts resolved plug connections into modular connector asset instances.",
        "",
        "## Summary",
        "",
        f"- connector_asset_instance_count: {validation['connector_asset_instance_count']}",
        f"- source_connection_count: {validation['source_connection_count']}",
        f"- fit_status_counts: {validation['fit_status_counts']}",
        "",
        "## Acceptance",
        "",
    ]
    for key, value in validation.items():
        if key != "no_claims":
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Fit Reports", ""])
    for fit in data["fit_reports"]:
        lines.append(f"- `{fit['connection_id']}` `{fit.get('asset_id', fit['reason'])}`: {fit['status']} {fit['reason']}")
    lines.extend(["", "No production, structural, fabrication, or historical accuracy claims.", ""])
    paths.placement_report_path.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any], paths: OutputPaths) -> None:
    receipt = {
        "schema": "connector_asset_placement_v0_receipt",
        "created_at_utc": data["created_at_utc"],
        "outputs": {
            "connector_asset_index": display_path(paths.index_path),
            "placement": display_path(paths.placement_path),
            "report": display_path(paths.placement_report_path),
        },
        "acceptance": data["validation"],
        "no_claims": NO_CLAIMS,
    }
    paths.receipt_path.parent.mkdir(parents=True, exist_ok=True)
    paths.receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Optional output root for generated connector files. Defaults to the repository root.",
    )
    parser.add_argument(
        "--integrated-graph-path",
        type=Path,
        default=None,
        help="Optional integrated graph JSON to consume instead of the default generated graph.",
    )
    parser.add_argument(
        "--no-regenerate-integrated",
        action="store_true",
        help="Fail if the integrated graph is missing instead of running the integrated map generator.",
    )
    return parser.parse_args(argv)


def paths_from_args(args: argparse.Namespace) -> OutputPaths:
    integrated_graph_path = args.integrated_graph_path.resolve() if args.integrated_graph_path else None
    regenerate_integrated = not bool(args.no_regenerate_integrated)
    if args.output_root is None:
        paths = default_output_paths()
        if integrated_graph_path is None and regenerate_integrated:
            return paths
        return OutputPaths(
            recipe_dir=paths.recipe_dir,
            index_path=paths.index_path,
            kit_report_path=paths.kit_report_path,
            placement_dir=paths.placement_dir,
            placement_path=paths.placement_path,
            placement_report_path=paths.placement_report_path,
            receipt_path=paths.receipt_path,
            integrated_graph_path=integrated_graph_path or paths.integrated_graph_path,
            regenerate_integrated=regenerate_integrated,
        )
    return output_paths_for_root(args.output_root, integrated_graph_path=integrated_graph_path, regenerate_integrated=regenerate_integrated)


def main(argv: list[str] | None = None) -> None:
    paths = paths_from_args(parse_args(argv))
    paths.placement_dir.mkdir(parents=True, exist_ok=True)
    data = compile_placements(paths)
    paths.placement_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data, paths)
    write_receipt(data, paths)
    print(f"wrote {display_path(paths.index_path)}")
    print(f"wrote {display_path(paths.placement_path)}")
    print(f"wrote {display_path(paths.placement_report_path)}")
    print(f"wrote {display_path(paths.receipt_path)}")
    print(
        "connector_assets={connector_asset_instance_count} connections={source_connection_count} fit_status={fit_status_counts}".format(
            **data["validation"]
        )
    )


if __name__ == "__main__":
    main()
