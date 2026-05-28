#!/usr/bin/env python3
"""Compile Asset Mill Measured Components v2.

v2 extends the local measured asset catalog without replacing v1. Recipes are
deterministic grammar assets using local measurement/range packets as proportion
hints only. They do not claim production approval, structural safety,
fabrication readiness, or historical accuracy.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DICT_ROOT = ROOT / "geometry_dictionary"
MEASUREMENT_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "extracted_measurements_v0.json"
MEASUREMENT_SOURCES_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "measurement_sources_v0.json"
GEOMETRY_LINKS_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "measurement_geometry_term_links_v0.json"
SEMANTIC_LINKS_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "measurement_semantic_role_links_v0.json"
RATIO_RANGES_PATH = ROOT / "docs" / "research" / "architectural_measurements" / "recommended_ratio_ranges_v0.md"
SOURCE_QUALITY_PATH = ROOT / "docs" / "research" / "architectural_measurements" / "source_quality_notes_v0.md"
WEAK_AREAS_PATH = ROOT / "docs" / "research" / "architectural_measurements" / "weak_measurement_areas_v0.md"
V1_INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v1" / "asset_mill_measured_index_v1.json"
ORIENTATION_REPORT_PATH = ROOT / "goal" / "architecture" / "asset_mill_measured_v2" / "asset_dex_orientation_report.md"

OUT_ROOT = ROOT / "goal" / "architecture" / "asset_mill_measured_v2"
RECIPE_DIR = OUT_ROOT / "recipes"
REPORT_DIR = OUT_ROOT / "reports"
INDEX_PATH = OUT_ROOT / "asset_mill_measured_index_v2.json"
REPORT_PATH = REPORT_DIR / "asset_mill_measured_components_v2_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "asset_mill_measured_components_v2.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "historical_accuracy": False,
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


def load_dictionary_terms() -> dict[str, dict[str, Any]]:
    terms: dict[str, dict[str, Any]] = {}
    for path in sorted(DICT_ROOT.rglob("*.json")):
        if "/schemas/" in str(path):
            continue
        term = load_json(path)
        terms[term["term_id"]] = term
    return terms


def source_refs(*items: Any) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, tuple):
            refs.append({"ref_type": item[0], "ref": item[1]})
        else:
            refs.append({"ref_type": "measurement_id", "ref": item})
    return refs


def socket(socket_id: str, connector_term: str, position: list[float], direction: list[float], role: str) -> dict[str, Any]:
    return {
        "socket_id": socket_id,
        "connector_term": connector_term,
        "position_m": [round(float(value), 6) for value in position],
        "direction": [round(float(value), 6) for value in direction],
        "role": role,
    }


def bounds_from_dimensions(dimensions: dict[str, float]) -> dict[str, list[float]]:
    width = float(dimensions["width"])
    depth = float(dimensions["depth"])
    height = float(dimensions["height"])
    return {
        "min": [round(-width * 0.5, 6), round(-depth * 0.5, 6), 0.0],
        "max": [round(width * 0.5, 6), round(depth * 0.5, 6), round(height, 6)],
    }


def cube_part(name: str, loc: tuple[float, float, float], dim: tuple[float, float, float], mat: str = "stone") -> dict[str, Any]:
    return {
        "primitive": "cube",
        "name": name,
        "location_m": [round(float(v), 6) for v in loc],
        "dimensions_m": [round(float(v), 6) for v in dim],
        "material_role": mat,
    }


def cyl_part(name: str, loc: tuple[float, float, float], radius: float, depth: float, vertices: int, mat: str = "stone") -> dict[str, Any]:
    return {
        "primitive": "cylinder",
        "name": name,
        "location_m": [round(float(v), 6) for v in loc],
        "radius_m": round(float(radius), 6),
        "depth_m": round(float(depth), 6),
        "vertices": int(vertices),
        "material_role": mat,
    }


def base_asset(
    asset_id: str,
    *,
    dimensions: dict[str, float],
    source_measurement_refs: list[dict[str, str]],
    geometry_terms_used: list[str],
    profile_terms: list[str],
    operations: list[str],
    ratio_basis: dict[str, Any],
    uncertainty: dict[str, Any],
    sockets: list[dict[str, Any]],
    semantic_roles: list[str],
    validation_expectations: dict[str, Any],
    proof_primitives: list[dict[str, Any]],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema": "asset_mill_measured_component_recipe_v2",
        "asset_id": asset_id,
        "source_measurement_refs": source_measurement_refs,
        "geometry_terms_used": geometry_terms_used,
        "profile_terms": profile_terms,
        "operations": operations,
        "dimensions_m": {key: round(float(value), 6) for key, value in dimensions.items()},
        "bounds_m": bounds_from_dimensions(dimensions),
        "ratio_basis": ratio_basis,
        "uncertainty": uncertainty,
        "sockets": sockets,
        "semantic_roles": semantic_roles,
        "validation_expectations": validation_expectations | {"no_silent_scaling": True},
        "proof_primitives": proof_primitives,
        "notes": notes or [],
        "no_production_claim": True,
        "no_structural_claim": True,
        "no_fabrication_claim": True,
        "no_historical_accuracy_claim": True,
        "no_claims": NO_CLAIMS,
    }


def measured_assets() -> list[dict[str, Any]]:
    local_ratio_doc = ("local_ratio_doc", str(RATIO_RANGES_PATH.relative_to(ROOT)))
    weak_doc = ("local_ratio_doc", str(WEAK_AREAS_PATH.relative_to(ROOT)))
    source_quality = ("local_policy_doc", str(SOURCE_QUALITY_PATH.relative_to(ROOT)))
    geometry_links = ("local_link_file", str(GEOMETRY_LINKS_PATH.relative_to(ROOT)))
    semantic_links = ("local_link_file", str(SEMANTIC_LINKS_PATH.relative_to(ROOT)))
    v1_catalog = ("local_asset_catalog", str(V1_INDEX_PATH.relative_to(ROOT)))
    orientation = ("local_policy_doc", str(ORIENTATION_REPORT_PATH.relative_to(ROOT)))

    assets: list[dict[str, Any]] = []

    assets.append(
        base_asset(
            "measured_wall_segment_v2",
            dimensions={"width": 2.2, "depth": 0.34, "height": 1.6},
            source_measurement_refs=source_refs("habs_tn181_splayed_support_opening_ratio_v0", weak_doc, source_quality, v1_catalog, orientation),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "bevel_edges", "socket", "floor", "ceiling", "north", "south", "east", "west", "blocked", "cover", "line_of_sight_blocker", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"module": "v2 wall segment keeps v1 wall-block envelope for direct building-graph compatibility", "depth_to_width": round(0.34 / 2.2, 6), "height_to_width": round(1.6 / 2.2, 6)},
            uncertainty={"level": "high", "reason": "wall thickness remains a local gameplay grammar value with weak measurement support"},
            sockets=[
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("ceiling_stack", "ceiling", [0, 0, 1.6], [0, 0, 1], "stack"),
                socket("west_repeat", "west", [-1.1, 0, 0.8], [-1, 0, 0], "wall_repeat"),
                socket("east_repeat", "east", [1.1, 0, 0.8], [1, 0, 0], "wall_repeat"),
            ],
            semantic_roles=["blocked", "cover", "line_of_sight_blocker", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "repeat_sockets_present": True},
            proof_primitives=[
                cube_part("wall_core", (0, 0, 0.8), (2.2, 0.34, 1.6), "stone"),
                cube_part("top_trim", (0, -0.19, 1.52), (2.24, 0.08, 0.12), "trim"),
                cube_part("base_trim", (0, -0.19, 0.12), (2.24, 0.08, 0.12), "trim"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_corner_post_v2",
            dimensions={"width": 0.52, "depth": 0.52, "height": 2.2},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", "palladio_corinthian_column_ratio_v0", weak_doc, geometry_links, v1_catalog),
            geometry_terms_used=["square", "width", "height", "aspect_ratio", "extrude", "bevel_edges", "floor", "ceiling", "column_cap", "support", "blocked", "collision_proxy"],
            profile_terms=["square"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"height_to_width": round(2.2 / 0.52, 6), "basis": "shorter corner post for wall-height building graph corners, not a column-order claim"},
            uncertainty={"level": "medium", "reason": "support grammar is source-bounded, but corner post height is chosen for v2 wall compatibility"},
            sockets=[
                socket("base", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("cap", "column_cap", [0, 0, 2.2], [0, 0, 1], "cap_attachment"),
                socket("north_wall_join", "north", [0, 0.26, 0.8], [0, 1, 0], "wall_join"),
                socket("east_wall_join", "east", [0.26, 0, 0.8], [1, 0, 0], "wall_join"),
            ],
            semantic_roles=["support", "blocked", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "corner_join_sockets_present": True},
            proof_primitives=[
                cube_part("corner_post_shaft", (0, 0, 1.1), (0.46, 0.46, 2.2), "support"),
                cube_part("corner_post_base", (0, 0, 0.1), (0.52, 0.52, 0.2), "cap"),
                cube_part("corner_post_cap", (0, 0, 2.12), (0.52, 0.52, 0.16), "cap"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_door_frame_v2",
            dimensions={"width": 2.2, "depth": 0.48, "height": 2.4, "opening_width": 1.2, "opening_height": 1.95},
            source_measurement_refs=source_refs("habs_tn181_round_recess_window_dimensions_v0", "pointed_arch_equilateral_rule_v0", local_ratio_doc, semantic_links, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "aspect_ratio", "extrude", "compound_asset", "socket", "floor", "north", "south", "blocked", "line_of_sight_blocker", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["compound_asset", "extrude"],
            ratio_basis={"opening_width_to_total_width": round(1.2 / 2.2, 6), "basis": "rectangular portal frame for building graph entrance sockets"},
            uncertainty={"level": "medium", "reason": "opening ratios are locally bounded, while frame/jamb massing is simplified"},
            sockets=[
                socket("threshold", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("portal_front", "socket", [0, -0.25, 0.9], [0, -1, 0], "doorway_connection"),
                socket("north_wall_join", "north", [0, 0.24, 1.0], [0, 1, 0], "wall_join"),
                socket("south_wall_join", "south", [0, -0.24, 1.0], [0, -1, 0], "wall_join"),
            ],
            semantic_roles=["blocked", "line_of_sight_blocker", "collision_proxy", "panel_socket"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "portal_socket_present": True},
            proof_primitives=[
                cube_part("left_jamb", (-0.78, 0, 0.98), (0.34, 0.48, 1.96), "stone"),
                cube_part("right_jamb", (0.78, 0, 0.98), (0.34, 0.48, 1.96), "stone"),
                cube_part("top_lintel", (0, 0, 2.18), (2.2, 0.48, 0.28), "cap"),
                cube_part("threshold_slab", (0, 0, 0.06), (1.62, 0.56, 0.12), "walkable"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_window_frame_v2",
            dimensions={"width": 1.35, "depth": 0.32, "height": 1.8, "opening_width": 0.62, "opening_height": 1.05},
            source_measurement_refs=source_refs("habs_tn181_round_recess_window_dimensions_v0", "pointed_arch_lancet_constraint_v0", local_ratio_doc, weak_doc, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "aspect_ratio", "extrude", "compound_asset", "socket", "floor", "blocked", "line_of_sight_blocker", "decorative_only", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["compound_asset", "extrude"],
            ratio_basis={"opening_width_to_total_width": round(0.62 / 1.35, 6), "basis": "small wall-mounted frame for window sockets"},
            uncertainty={"level": "medium", "reason": "window envelope is locally source-inspired; frame bands are simplified"},
            sockets=[
                socket("wall_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("window_opening", "socket", [0, -0.18, 0.95], [0, -1, 0], "line_of_sight_frame"),
                socket("top_stack", "ceiling", [0, 0, 1.8], [0, 0, 1], "stack"),
            ],
            semantic_roles=["line_of_sight_blocker", "decorative_only", "collision_proxy", "panel_socket"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "window_socket_present": True},
            proof_primitives=[
                cube_part("window_backer", (0, 0.05, 0.9), (1.35, 0.18, 1.8), "stone"),
                cube_part("left_reveal", (-0.43, -0.12, 0.9), (0.1, 0.12, 1.2), "trim"),
                cube_part("right_reveal", (0.43, -0.12, 0.9), (0.1, 0.12, 1.2), "trim"),
                cube_part("sill", (0, -0.13, 0.3), (0.86, 0.14, 0.12), "cap"),
                cube_part("head", (0, -0.13, 1.5), (0.86, 0.14, 0.12), "cap"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_foundation_skirt_v2",
            dimensions={"width": 2.8, "depth": 0.62, "height": 0.32},
            source_measurement_refs=source_refs("habs_tn181_splayed_support_opening_ratio_v0", weak_doc, source_quality, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "bevel_edges", "floor", "ceiling", "north", "south", "support", "blocked", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"height_to_width": round(0.32 / 2.8, 6), "basis": "foundation skirt hides terrain contact and exposes stack sockets"},
            uncertainty={"level": "high", "reason": "foundation skirt is a terrain-contact blockout, not a structural foundation claim"},
            sockets=[
                socket("terrain_contact", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("wall_stack", "ceiling", [0, 0, 0.32], [0, 0, 1], "wall_stack"),
                socket("north_edge", "north", [0, 0.31, 0.16], [0, 1, 0], "edge_join"),
                socket("south_edge", "south", [0, -0.31, 0.16], [0, -1, 0], "edge_join"),
            ],
            semantic_roles=["support", "blocked", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "stack_socket_present": True},
            proof_primitives=[cube_part("foundation_skirt", (0, 0, 0.16), (2.8, 0.62, 0.32), "support")],
        )
    )

    assets.append(
        base_asset(
            "measured_threshold_step_v2",
            dimensions={"width": 1.8, "depth": 0.74, "height": 0.22},
            source_measurement_refs=source_refs("habs_tn181_round_recess_window_dimensions_v0", local_ratio_doc, source_quality, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "socket", "floor", "ceiling", "north", "south", "walkable", "vertical_transition", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude"],
            ratio_basis={"height_to_depth": round(0.22 / 0.74, 6), "basis": "single explicit threshold step for entrance transitions"},
            uncertainty={"level": "high", "reason": "stair/threshold proportions remain gameplay traversal blockout values"},
            sockets=[
                socket("lower_entry", "south", [0, -0.37, 0.0], [0, -1, 0], "route_entry"),
                socket("upper_exit", "north", [0, 0.37, 0.22], [0, 1, 0], "route_exit"),
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("top_walkable", "ceiling", [0, 0, 0.22], [0, 0, 1], "walkable_surface"),
            ],
            semantic_roles=["walkable", "vertical_transition", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "route_sockets_present": True},
            proof_primitives=[cube_part("threshold_step", (0, 0, 0.11), (1.8, 0.74, 0.22), "walkable")],
        )
    )

    assets.append(
        base_asset(
            "measured_low_retaining_wall_v2",
            dimensions={"width": 1.6, "depth": 0.3, "height": 0.75},
            source_measurement_refs=source_refs("habs_tn181_splayed_support_opening_ratio_v0", weak_doc, source_quality, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "bevel_edges", "floor", "ceiling", "east", "west", "support", "cover", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"height_to_width": round(0.75 / 1.6, 6), "basis": "low terrain-edge blocker compatible with connector retaining wall language"},
            uncertainty={"level": "high", "reason": "retaining wall is a visual/terrain edge marker, not a structural design"},
            sockets=[
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("top_stack", "ceiling", [0, 0, 0.75], [0, 0, 1], "stack"),
                socket("left_repeat", "west", [-0.8, 0, 0.375], [-1, 0, 0], "repeat"),
                socket("right_repeat", "east", [0.8, 0, 0.375], [1, 0, 0], "repeat"),
            ],
            semantic_roles=["support", "cover", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "repeat_sockets_present": True},
            proof_primitives=[
                cube_part("retaining_wall_core", (0, 0, 0.375), (1.6, 0.3, 0.75), "stone"),
                cube_part("retaining_wall_cap", (0, 0, 0.79), (1.72, 0.36, 0.08), "cap"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_roof_cap_block_v2",
            dimensions={"width": 2.6, "depth": 2.6, "height": 0.24},
            source_measurement_refs=source_refs("habs_tn181_round_recess_window_dimensions_v0", local_ratio_doc, weak_doc, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "bevel_edges", "floor", "ceiling", "north", "south", "east", "west", "cover", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"height_to_width": round(0.24 / 2.6, 6), "basis": "flat roof cap placeholder that remains an explicit non-scaled block"},
            uncertainty={"level": "high", "reason": "roof cap is a placeholder massing component, not a roof construction claim"},
            sockets=[
                socket("wall_receive", "floor", [0, 0, 0], [0, 0, -1], "wall_stack_receive"),
                socket("top_marker", "ceiling", [0, 0, 0.24], [0, 0, 1], "top_surface"),
                socket("north_edge", "north", [0, 1.3, 0.12], [0, 1, 0], "edge_join"),
                socket("east_edge", "east", [1.3, 0, 0.12], [1, 0, 0], "edge_join"),
            ],
            semantic_roles=["cover", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "edge_sockets_present": True},
            proof_primitives=[
                cube_part("roof_cap_plate", (0, 0, 0.12), (2.6, 2.6, 0.24), "cap"),
                cube_part("roof_cap_center_marker", (0, 0, 0.29), (1.3, 1.3, 0.06), "trim"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_trim_strip_v2",
            dimensions={"width": 1.8, "depth": 0.12, "height": 0.12},
            source_measurement_refs=source_refs("habs_tn181_round_recess_window_dimensions_v0", weak_doc, source_quality, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "array_linear", "east", "west", "floor", "decorative_only", "panel_socket", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude", "array_linear"],
            ratio_basis={"height_to_width": round(0.12 / 1.8, 6), "basis": "repeatable facade trim strip with explicit repeat sockets"},
            uncertainty={"level": "high", "reason": "trim is decorative grammar only and has no measurement-backed detailing"},
            sockets=[
                socket("left_repeat", "west", [-0.9, 0, 0.06], [-1, 0, 0], "repeat"),
                socket("right_repeat", "east", [0.9, 0, 0.06], [1, 0, 0], "repeat"),
                socket("back_anchor", "floor", [0, 0, 0], [0, 0, -1], "mount"),
            ],
            semantic_roles=["decorative_only", "panel_socket", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "repeat_sockets_present": True},
            proof_primitives=[cube_part("trim_strip", (0, 0, 0.06), (1.8, 0.12, 0.12), "trim")],
        )
    )

    assets.append(
        base_asset(
            "measured_small_buttress_block_v2",
            dimensions={"width": 0.82, "depth": 0.68, "height": 1.1},
            source_measurement_refs=source_refs("habs_tn181_splayed_support_opening_ratio_v0", weak_doc, geometry_links, semantic_links, v1_catalog),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "compound_asset", "bevel_edges", "floor", "ceiling", "socket", "support", "cover", "blocked", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["compound_asset", "extrude", "bevel_edges"],
            ratio_basis={"projection_to_height": round(0.68 / 1.1, 6), "basis": "small wall-side support mass for facade rhythm; no structural claim"},
            uncertainty={"level": "high", "reason": "buttress block is a simplified support marker with weak local measurement backing"},
            sockets=[
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("wall_mount", "socket", [0, -0.34, 0.55], [0, -1, 0], "wall_mount"),
                socket("top_stack", "ceiling", [0, 0, 1.1], [0, 0, 1], "stack"),
            ],
            semantic_roles=["support", "cover", "blocked", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "wall_mount_socket_present": True},
            proof_primitives=[
                cube_part("buttress_foot", (0, 0.08, 0.16), (0.82, 0.68, 0.32), "support"),
                cube_part("buttress_body", (0, -0.04, 0.62), (0.58, 0.48, 0.72), "stone"),
                cube_part("buttress_cap", (0, -0.08, 1.02), (0.64, 0.42, 0.16), "cap"),
            ],
        )
    )

    return assets


def validate_source_refs(asset: dict[str, Any], measurement_ids: set[str]) -> None:
    if not asset["source_measurement_refs"]:
        fail(f"{asset['asset_id']} needs at least one local measurement or ratio source")
    for ref in asset["source_measurement_refs"]:
        ref_type = ref["ref_type"]
        value = ref["ref"]
        if ref_type == "measurement_id":
            if value not in measurement_ids:
                fail(f"{asset['asset_id']} references unknown measurement_id `{value}`")
        elif ref_type in {"local_ratio_doc", "local_policy_doc", "local_link_file", "local_asset_catalog"}:
            if not (ROOT / value).exists():
                fail(f"{asset['asset_id']} references missing local file `{value}`")
        else:
            fail(f"{asset['asset_id']} has unsupported ref_type `{ref_type}`")


def validate_proof_primitives(asset: dict[str, Any]) -> None:
    if not asset["proof_primitives"]:
        fail(f"{asset['asset_id']} needs at least one proof primitive")
    for part in asset["proof_primitives"]:
        primitive = part.get("primitive")
        if primitive == "cube":
            dims = part.get("dimensions_m", [])
            if len(dims) != 3 or any(float(value) <= 0.0 for value in dims):
                fail(f"{asset['asset_id']} cube {part.get('name')} has non-positive dimensions")
        elif primitive == "cylinder":
            if float(part.get("radius_m", 0.0)) <= 0.0 or float(part.get("depth_m", 0.0)) <= 0.0 or int(part.get("vertices", 0)) < 3:
                fail(f"{asset['asset_id']} cylinder {part.get('name')} has invalid dimensions")
        elif primitive == "curve":
            if float(part.get("span_m", 0.0)) <= 0.0 or float(part.get("bevel_depth_m", 0.0)) <= 0.0:
                fail(f"{asset['asset_id']} curve {part.get('name')} has invalid dimensions")
        else:
            fail(f"{asset['asset_id']} uses unsupported proof primitive `{primitive}`")


def validate_recipe(asset: dict[str, Any], terms: dict[str, dict[str, Any]], measurement_ids: set[str]) -> None:
    required = [
        "asset_id",
        "source_measurement_refs",
        "geometry_terms_used",
        "profile_terms",
        "operations",
        "dimensions_m",
        "ratio_basis",
        "uncertainty",
        "sockets",
        "semantic_roles",
        "validation_expectations",
        "proof_primitives",
        "no_production_claim",
        "no_structural_claim",
        "no_fabrication_claim",
        "no_historical_accuracy_claim",
    ]
    for field in required:
        if field not in asset:
            fail(f"{asset.get('asset_id')} missing required field `{field}`")
    if asset["schema"] != "asset_mill_measured_component_recipe_v2":
        fail(f"{asset['asset_id']} must use v2 recipe schema")
    if asset["no_production_claim"] is not True or asset["no_structural_claim"] is not True or asset["no_fabrication_claim"] is not True or asset["no_historical_accuracy_claim"] is not True:
        fail(f"{asset['asset_id']} no-claim booleans must be true")
    if asset["no_claims"] != NO_CLAIMS:
        fail(f"{asset['asset_id']} no_claims must match required false claims")
    validate_source_refs(asset, measurement_ids)
    unknown = sorted(set(asset["geometry_terms_used"]) - set(terms))
    if unknown:
        fail(f"{asset['asset_id']} references unknown geometry terms: {unknown}")
    unknown_profiles = sorted(set(asset["profile_terms"]) - set(terms))
    if unknown_profiles:
        fail(f"{asset['asset_id']} references unknown profile terms: {unknown_profiles}")
    unknown_operations = sorted(set(asset["operations"]) - set(terms))
    if unknown_operations:
        fail(f"{asset['asset_id']} references unknown operations: {unknown_operations}")
    semantic_terms = {term_id for term_id, term in terms.items() if term["category"] == "semantic_geometry"}
    unknown_semantics = sorted(set(asset["semantic_roles"]) - semantic_terms)
    if unknown_semantics:
        fail(f"{asset['asset_id']} has unknown semantic roles: {unknown_semantics}")
    dims = asset["dimensions_m"]
    for key in ("width", "depth", "height"):
        if float(dims.get(key, 0.0)) <= 0.0:
            fail(f"{asset['asset_id']} has non-positive dimension `{key}`")
    connector_terms = {term_id for term_id, term in terms.items() if term["category"] == "connector"}
    if not asset["sockets"]:
        fail(f"{asset['asset_id']} should expose at least one useful socket")
    for item in asset["sockets"]:
        if item["connector_term"] not in connector_terms:
            fail(f"{asset['asset_id']} socket {item['socket_id']} uses unknown connector `{item['connector_term']}`")
    validate_proof_primitives(asset)


def write_recipes(assets: list[dict[str, Any]]) -> dict[str, str]:
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for asset in assets:
        path = RECIPE_DIR / f"{asset['asset_id']}.json"
        path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
        paths[asset["asset_id"]] = str(path.relative_to(ROOT))
    return paths


def source_files() -> list[str]:
    return [
        str(MEASUREMENT_PATH.relative_to(ROOT)),
        str(MEASUREMENT_SOURCES_PATH.relative_to(ROOT)),
        str(GEOMETRY_LINKS_PATH.relative_to(ROOT)),
        str(SEMANTIC_LINKS_PATH.relative_to(ROOT)),
        str(RATIO_RANGES_PATH.relative_to(ROOT)),
        str(SOURCE_QUALITY_PATH.relative_to(ROOT)),
        str(WEAK_AREAS_PATH.relative_to(ROOT)),
        str(V1_INDEX_PATH.relative_to(ROOT)),
        str(ORIENTATION_REPORT_PATH.relative_to(ROOT)),
    ]


def write_index(assets: list[dict[str, Any]], paths: dict[str, str]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    index = {
        "schema": "asset_mill_measured_index_v2",
        "created_at_utc": now_iso(),
        "asset_count": len(assets),
        "recipe_dir": str(RECIPE_DIR.relative_to(ROOT)),
        "source_files": source_files(),
        "assets": [
            {
                "asset_id": asset["asset_id"],
                "recipe_path": paths[asset["asset_id"]],
                "dimensions_m": asset["dimensions_m"],
                "geometry_terms_used": asset["geometry_terms_used"],
                "source_measurement_refs": asset["source_measurement_refs"],
                "semantic_roles": asset["semantic_roles"],
                "socket_count": len(asset["sockets"]),
                "proof_primitive_count": len(asset["proof_primitives"]),
                "uncertainty": asset["uncertainty"],
            }
            for asset in assets
        ],
        "rules": {
            "extends_v1_without_replacing": True,
            "v1_catalog_left_untouched": True,
            "local_sources_only": True,
            "web_search_used": False,
            "measurements_are_ratio_hints_only": True,
            "no_unknown_geometry_terms": True,
            "no_new_geometry_terms": True,
            "no_silent_scaling": True,
            "no_fake_historical_source_claim": True,
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_historical_accuracy_claim": True,
        },
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def write_report(assets: list[dict[str, Any]], paths: dict[str, str]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Asset Mill Measured Components v2",
        "",
        "Measured component recipes built as a versioned extension of v1. v1 remains untouched.",
        "",
        "Measurements are local grammar references and ratio hints only. These assets do not claim historical accuracy, structural safety, fabrication readiness, or production approval.",
        "",
        "## Outputs",
        "",
        f"- Recipe directory: `{RECIPE_DIR.relative_to(ROOT)}`",
        f"- Index: `{INDEX_PATH.relative_to(ROOT)}`",
        f"- Receipt: `{RECEIPT_PATH.relative_to(ROOT)}`",
        "",
        "## Components",
        "",
        "| Asset | Dimensions m | Terms | Source refs | Uncertainty | Sockets | Proof primitives | Recipe |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for asset in assets:
        dims = asset["dimensions_m"]
        dim_text = f"{dims['width']} x {dims['depth']} x {dims['height']}"
        terms = ", ".join(asset["geometry_terms_used"][:6])
        if len(asset["geometry_terms_used"]) > 6:
            terms += ", ..."
        refs = ", ".join(ref["ref"] for ref in asset["source_measurement_refs"][:3])
        lines.append(
            f"| `{asset['asset_id']}` | {dim_text} | {terms} | {refs} | {asset['uncertainty']['level']} | {len(asset['sockets'])} | {len(asset['proof_primitives'])} | `{paths[asset['asset_id']]}` |"
        )
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "- all v2 recipes validate: true",
            "- every asset references known geometry dictionary terms: true",
            "- every asset has nonzero bounds: true",
            "- every asset has at least one proof primitive: true",
            "- no new geometry terms: true",
            "- no silent scaling: true",
            "- v1 remains untouched: true",
            "- no web search: true",
            "- no production, structural, fabrication, or historical accuracy claims: true",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(assets: list[dict[str, Any]], paths: dict[str, str]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "asset_mill_measured_components_v2",
        "created_at_utc": now_iso(),
        "asset_count": len(assets),
        "recipes": paths,
        "index": str(INDEX_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "source_files": source_files(),
        "acceptance": {
            "all_v2_recipes_validate": True,
            "every_asset_references_known_geometry_terms": True,
            "every_asset_has_nonzero_bounds": True,
            "every_asset_has_proof_primitives": True,
            "no_unknown_geometry_terms": True,
            "no_new_geometry_terms": True,
            "no_silent_scaling": True,
            "v1_remains_untouched": True,
            "web_search_used": False,
            "no_structural_fabrication_production_or_historical_claims": True,
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    terms = load_dictionary_terms()
    measurements = load_json(MEASUREMENT_PATH)["measurements"]
    measurement_ids = {item["measurement_id"] for item in measurements}
    assets = measured_assets()
    ids: set[str] = set()
    for asset in assets:
        if asset["asset_id"] in ids:
            fail(f"duplicate asset_id `{asset['asset_id']}`")
        ids.add(asset["asset_id"])
        validate_recipe(asset, terms, measurement_ids)
    paths = write_recipes(assets)
    write_index(assets, paths)
    write_report(assets, paths)
    write_receipt(assets, paths)
    print(f"wrote {len(assets)} measured v2 component recipes")
    print(f"index: {INDEX_PATH.relative_to(ROOT)}")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

