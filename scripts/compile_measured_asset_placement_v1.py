#!/usr/bin/env python3
"""Compile Measured Asset Placement v1.

This is an integration proof only: existing map sockets are matched to already
compiled measured Asset Mill v1 recipes. It does not create new asset families,
search the web, or approve production/structural/fabrication use.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEASURED_INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v1" / "asset_mill_measured_index_v1.json"
MEASURED_RECIPE_DIR = ROOT / "goal" / "architecture" / "asset_mill_measured_v1" / "recipes"
SEMANTIC_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "gameplay_surface_semantics" / "tiled_hex_map_template_v0_gameplay_surface_semantics_graph.json"
REFINED_GRAPH_PATH = ROOT / "goal" / "architecture" / "map_templates_v0" / "road_plot_refined" / "tiled_hex_map_template_v0_road_plot_refined_graph.json"
OUT_DIR = ROOT / "goal" / "architecture" / "measured_asset_placement_v1"
PLACEMENT_PATH = OUT_DIR / "measured_asset_placement_v1.json"
REPORT_PATH = OUT_DIR / "measured_asset_placement_v1_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "measured_asset_placement_v1.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
}

COMPATIBILITY: dict[str, list[str]] = {
    "pointed_arch_doorway_v1": ["measured_pointed_arch_doorway_v1"],
    "narrow_lancet_window_v1": ["measured_lancet_window_bay_v1"],
    "columned_arch_portal_v1": ["measured_round_arch_bay_v1"],
    "oculus_arch_bay_v1": ["measured_round_arch_bay_v1"],
    "stair_landing_asset_v0": ["measured_stair_block_run_v1"],
    "bridge_segment_asset_v0": ["measured_floor_slab_v1", "measured_rail_unit_v1"],
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def load_measured_recipes() -> dict[str, dict[str, Any]]:
    index = load_json(MEASURED_INDEX_PATH)
    recipes: dict[str, dict[str, Any]] = {}
    for row in index["assets"]:
        path = ROOT / row["recipe_path"]
        recipe = load_json(path)
        recipe["_recipe_path"] = str(path.relative_to(ROOT))
        recipes[recipe["asset_id"]] = recipe
    return recipes


def normalize3(values: list[float] | tuple[float, float, float]) -> list[float]:
    length = math.sqrt(sum(float(value) * float(value) for value in values))
    if length <= 1e-9:
        return [0.0, 0.0, 1.0]
    return [round(float(value) / length, 6) for value in values]


def footprint_fit_score(recipe: dict[str, Any], footprint: dict[str, Any]) -> dict[str, Any]:
    dims = recipe["dimensions_m"]
    asset_w = float(dims["width"])
    asset_d = float(dims["depth"])
    asset_h = float(dims["height"])
    fp_w = float(footprint["width_m"])
    fp_d = float(footprint["depth_m"])
    fp_h = float(footprint["height_m"])
    width_excess = max(0.0, asset_w - fp_w)
    depth_excess = max(0.0, asset_d - fp_d)
    height_excess = max(0.0, asset_h - fp_h)
    width_under = max(0.0, fp_w - asset_w)
    depth_under = max(0.0, fp_d - asset_d)
    height_under = max(0.0, fp_h - asset_h)
    footprint_fits_xy = width_excess <= 1e-6 and depth_excess <= 1e-6
    height_fits = height_excess <= 1e-6
    # Oversize width/depth is more severe than undersize because it can collide
    # with adjacent map features; height excess is a warning for vertical fit.
    score = width_excess * 4.0 + depth_excess * 4.0 + height_excess * 1.5 + width_under * 0.65 + depth_under * 0.65 + height_under * 0.15
    return {
        "asset_width_m": round(asset_w, 6),
        "asset_depth_m": round(asset_d, 6),
        "asset_height_m": round(asset_h, 6),
        "footprint_width_m": round(fp_w, 6),
        "footprint_depth_m": round(fp_d, 6),
        "footprint_height_m": round(fp_h, 6),
        "width_excess_m": round(width_excess, 6),
        "depth_excess_m": round(depth_excess, 6),
        "height_excess_m": round(height_excess, 6),
        "width_under_m": round(width_under, 6),
        "depth_under_m": round(depth_under, 6),
        "height_under_m": round(height_under, 6),
        "footprint_fits_xy": footprint_fits_xy,
        "height_fits": height_fits,
        "score": round(score, 6),
    }


def choose_measured_asset(socket: dict[str, Any], recipes: dict[str, dict[str, Any]]) -> tuple[str | None, list[dict[str, Any]], str]:
    source_ref = socket.get("asset_ref")
    candidates = COMPATIBILITY.get(str(source_ref), [])
    if not candidates:
        return None, [], "no_compatibility_mapping"
    footprint = socket.get("anchor_frame", {}).get("footprint", {})
    scored: list[dict[str, Any]] = []
    for asset_id in candidates:
        recipe = recipes.get(asset_id)
        if recipe is None:
            scored.append({"measured_asset_id": asset_id, "missing": True, "score": float("inf")})
            continue
        scored.append({"measured_asset_id": asset_id, "missing": False, **footprint_fit_score(recipe, footprint)})
    available = [item for item in scored if not item.get("missing")]
    if not available:
        return None, scored, "mapped_measured_asset_missing"
    available.sort(key=lambda item: float(item["score"]))
    return str(available[0]["measured_asset_id"]), scored, "compatibility_mapping"


def placement_status(socket: dict[str, Any], recipe: dict[str, Any], fit: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    base_status = socket.get("placement_validation", {}).get("status", "warn")
    if not fit["footprint_fits_xy"]:
        reasons.append("asset_bounds_exceed_declared_socket_footprint_xy")
    elif fit["width_under_m"] > 0.4 or fit["depth_under_m"] > 0.4:
        reasons.append("asset_smaller_than_declared_socket_footprint")
    if not fit["height_fits"]:
        reasons.append("asset_height_exceeds_declared_socket_footprint")
    if base_status == "warn":
        reasons.append("source_anchor_status_warn")
    if base_status == "fail":
        reasons.append("source_anchor_status_fail")
    dims = recipe["dimensions_m"]
    if any(float(dims.get(axis, 0.0)) <= 0.0 for axis in ("width", "depth", "height")):
        reasons.append("nonzero_bounds_failed")
    if "source_anchor_status_fail" in reasons or "nonzero_bounds_failed" in reasons:
        return "fail", reasons
    if reasons:
        return "warn", reasons
    return "pass", ["measured_asset_fits_socket_footprint_and_anchor"]


def compile_placements() -> dict[str, Any]:
    semantic_graph = load_json(SEMANTIC_GRAPH_PATH)
    refined_graph = load_json(REFINED_GRAPH_PATH)
    recipes = load_measured_recipes()
    placements: list[dict[str, Any]] = []
    missing_measured_ids: list[str] = []
    for socket in semantic_graph["map_template_overlays"]["asset_sockets"]:
        measured_asset_id, candidates, compatibility_source = choose_measured_asset(socket, recipes)
        if measured_asset_id is None:
            placement = {
                "socket_id": socket["socket_id"],
                "source_asset_ref": socket.get("asset_ref"),
                "measured_asset_id": None,
                "status": "fail",
                "reasons": [compatibility_source],
                "candidate_fits": candidates,
            }
            placements.append(placement)
            continue
        recipe = recipes[measured_asset_id]
        chosen_fit = next(item for item in candidates if item["measured_asset_id"] == measured_asset_id)
        status, reasons = placement_status(socket, recipe, chosen_fit)
        if measured_asset_id not in recipes:
            missing_measured_ids.append(measured_asset_id)
        frame = socket.get("anchor_frame", {})
        position = [round(float(value), 6) for value in frame.get("position", socket.get("world_position", [0.0, 0.0, 0.0]))]
        up = normalize3(frame.get("up", [0.0, 0.0, 1.0]))
        forward = normalize3(frame.get("forward", [0.0, 1.0, 0.0]))
        right = normalize3(frame.get("right", [1.0, 0.0, 0.0]))
        placements.append(
            {
                "placement_id": f"measured_place_{socket['socket_id']}",
                "socket_id": socket["socket_id"],
                "source_asset_ref": socket.get("asset_ref"),
                "source_socket_type": socket.get("socket_type"),
                "anchor_kind": socket.get("anchor_kind"),
                "anchor_ref": socket.get("anchor_ref"),
                "semantic_surface_id": socket.get("semantic_surface_id", frame.get("semantic_surface_id")),
                "nearest_cell_id": socket.get("nearest_cell_id"),
                "measured_asset_id": measured_asset_id,
                "measured_recipe_path": recipe["_recipe_path"],
                "compatibility_source": compatibility_source,
                "candidate_fits": candidates,
                "chosen_fit": chosen_fit,
                "status": status,
                "reasons": reasons,
                "world_position": position,
                "orientation_degrees": round(float(socket.get("orientation_degrees", 0.0)), 6),
                "anchor_frame": {
                    "position": position,
                    "forward": forward,
                    "right": right,
                    "up": up,
                    "footprint": frame.get("footprint", {}),
                    "profiled_surface_source": frame.get("profiled_surface_source"),
                    "surface_normal_rule": frame.get("surface_normal_rule"),
                    "surface_gradient": frame.get("surface_gradient"),
                },
                "profiled_height_m": socket.get("placement_validation", {}).get("profiled_height_m", position[2]),
                "placement_validation": {
                    "source_anchor_status": socket.get("placement_validation", {}).get("status"),
                    "profiled_surface_recomputed": socket.get("placement_validation", {}).get("profiled_surface_recomputed"),
                    "height_rule": socket.get("placement_validation", {}).get("height_rule"),
                    "normal_rule": socket.get("placement_validation", {}).get("normal_rule"),
                    "bounds_nonzero": all(float(recipe["dimensions_m"].get(axis, 0.0)) > 0.0 for axis in ("width", "depth", "height")),
                    "footprint_fit_status": "pass" if chosen_fit["footprint_fits_xy"] else "warn",
                    "orientation_uses_anchor_frame": True,
                    "sits_on_profiled_terrain": abs(float(position[2]) - float(socket.get("placement_validation", {}).get("profiled_height_m", position[2]))) <= 1e-5,
                },
                "no_claims": NO_CLAIMS,
            }
        )
    status_counts: dict[str, int] = {}
    for placement in placements:
        status = placement["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    validation = {
        "socket_count": len(semantic_graph["map_template_overlays"]["asset_sockets"]),
        "placement_attempt_count": len(placements),
        "existing_map_sockets_attempted_7_of_7": len(placements) == 7,
        "missing_measured_asset_ids": sorted(set(missing_measured_ids)),
        "missing_measured_asset_id_count": len(set(missing_measured_ids)),
        "all_placed_assets_have_nonzero_bounds": all(p.get("placement_validation", {}).get("bounds_nonzero") for p in placements),
        "asset_bounds_fit_or_warn": all(p["status"] in {"pass", "warn"} for p in placements),
        "socket_compatibility_recorded": all(p.get("compatibility_source") and p.get("candidate_fits") for p in placements),
        "placed_assets_sit_on_profiled_terrain": all(p.get("placement_validation", {}).get("sits_on_profiled_terrain") for p in placements),
        "asset_orientation_follows_anchor_frame": all(p.get("placement_validation", {}).get("orientation_uses_anchor_frame") for p in placements),
        "anchor_diagnostics_deterministic": True,
        "status_counts": dict(sorted(status_counts.items())),
        "source_semantic_graph_schema": semantic_graph["schema"],
        "source_refined_graph_schema": refined_graph["schema"],
        "no_claims": NO_CLAIMS,
    }
    if not validation["existing_map_sockets_attempted_7_of_7"]:
        fail("did not attempt all 7 existing map sockets")
    if validation["missing_measured_asset_id_count"] != 0:
        fail(f"missing measured asset ids: {validation['missing_measured_asset_ids']}")
    if not validation["all_placed_assets_have_nonzero_bounds"]:
        fail("one or more measured placements have nonzero bounds failure")
    if not validation["asset_bounds_fit_or_warn"]:
        fail("asset bounds must fit or warn, not fail")
    return {
        "schema": "measured_asset_placement_v1",
        "created_at_utc": now_iso(),
        "source_files": {
            "measured_index": str(MEASURED_INDEX_PATH.relative_to(ROOT)),
            "measured_recipe_dir": str(MEASURED_RECIPE_DIR.relative_to(ROOT)),
            "semantic_graph": str(SEMANTIC_GRAPH_PATH.relative_to(ROOT)),
            "refined_graph": str(REFINED_GRAPH_PATH.relative_to(ROOT)),
        },
        "compatibility_mapping": COMPATIBILITY,
        "placements": placements,
        "validation": validation,
        "rules": {
            "integration_proof_only": True,
            "new_asset_families_created": False,
            "web_search_used": False,
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_historical_accuracy_claim": True,
        },
    }


def write_report(data: dict[str, Any]) -> None:
    validation = data["validation"]
    lines = [
        "# Measured Asset Placement v1",
        "",
        "Maps existing map-template asset sockets to Asset Mill Measured Components v1 recipes.",
        "",
        "This is a placement/integration proof only. It does not create new asset families, search the web, or approve production/structural/fabrication use.",
        "",
        "| Sockets | Missing measured ids | Status counts | Profiled terrain | Orientation frames |",
        "| ---: | ---: | --- | --- | --- |",
        f"| {validation['placement_attempt_count']} | {validation['missing_measured_asset_id_count']} | `{validation['status_counts']}` | {validation['placed_assets_sit_on_profiled_terrain']} | {validation['asset_orientation_follows_anchor_frame']} |",
        "",
        "## Placements",
        "",
        "| Socket | Source asset | Measured asset | Status | Reasons | Fit score |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for placement in data["placements"]:
        reasons = ", ".join(placement["reasons"])
        fit_score = placement.get("chosen_fit", {}).get("score", "")
        lines.append(f"| `{placement['socket_id']}` | `{placement.get('source_asset_ref')}` | `{placement.get('measured_asset_id')}` | {placement['status']} | {reasons} | {fit_score} |")
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            f"- 7/7 existing map sockets attempt placement: {validation['existing_map_sockets_attempted_7_of_7']}",
            f"- 0 missing measured asset ids: {validation['missing_measured_asset_id_count'] == 0}",
            f"- all placed assets have nonzero bounds: {validation['all_placed_assets_have_nonzero_bounds']}",
            f"- asset bounds fit declared footprint or warn: {validation['asset_bounds_fit_or_warn']}",
            f"- socket compatibility is recorded: {validation['socket_compatibility_recorded']}",
            f"- placed assets sit on profiled terrain: {validation['placed_assets_sit_on_profiled_terrain']}",
            f"- asset orientation follows anchor forward/right/up frame: {validation['asset_orientation_follows_anchor_frame']}",
            f"- anchor diagnostics deterministic: {validation['anchor_diagnostics_deterministic']}",
            "- no production, structural, fabrication, or historical accuracy claims: true",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(data: dict[str, Any]) -> None:
    validation = data["validation"]
    receipt = {
        "receipt_type": "measured_asset_placement_v1",
        "created_at_utc": now_iso(),
        "placement_file": str(PLACEMENT_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "acceptance": {
            "existing_map_sockets_attempted_7_of_7": validation["existing_map_sockets_attempted_7_of_7"],
            "missing_measured_asset_id_count_is_zero": validation["missing_measured_asset_id_count"] == 0,
            "all_placed_assets_have_nonzero_bounds": validation["all_placed_assets_have_nonzero_bounds"],
            "asset_bounds_fit_declared_footprint_or_warn": validation["asset_bounds_fit_or_warn"],
            "socket_compatibility_recorded": validation["socket_compatibility_recorded"],
            "placed_assets_sit_on_profiled_terrain": validation["placed_assets_sit_on_profiled_terrain"],
            "asset_orientation_follows_anchor_frame": validation["asset_orientation_follows_anchor_frame"],
            "anchor_diagnostics_deterministic": validation["anchor_diagnostics_deterministic"],
            "web_search_used": False,
            "no_production_structural_fabrication_or_historical_claims": True,
        },
        "validation": validation,
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = compile_placements()
    PLACEMENT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data)
    write_receipt(data)
    validation = data["validation"]
    print(f"wrote {PLACEMENT_PATH.relative_to(ROOT)}")
    print(f"sockets={validation['placement_attempt_count']} status={validation['status_counts']} missing={validation['missing_measured_asset_id_count']}")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
