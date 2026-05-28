#!/usr/bin/env python3
"""Compile measured Asset Mill component recipes v1.

The recipes are local grammar assets only. They reference the local geometry
dictionary and local measurement/range packets as proportion hints; they do not
claim historical accuracy, structural safety, fabrication readiness, or
production approval.
"""

from __future__ import annotations

import json
import math
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

OUT_ROOT = ROOT / "goal" / "architecture" / "asset_mill_measured_v1"
RECIPE_DIR = OUT_ROOT / "recipes"
REPORT_DIR = OUT_ROOT / "reports"
INDEX_PATH = OUT_ROOT / "asset_mill_measured_index_v1.json"
REPORT_PATH = REPORT_DIR / "asset_mill_measured_components_v1_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "asset_mill_measured_components_v1.receipt.json"

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


def bounds_from_dimensions(dim: dict[str, float]) -> dict[str, list[float]]:
    width = float(dim["width"])
    depth = float(dim["depth"])
    height = float(dim["height"])
    return {
        "min": [round(-width * 0.5, 6), round(-depth * 0.5, 6), 0.0],
        "max": [round(width * 0.5, 6), round(depth * 0.5, 6), round(height, 6)],
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
        "schema": "asset_mill_measured_component_recipe_v1",
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
        "validation_expectations": validation_expectations,
        "proof_primitives": proof_primitives,
        "notes": notes or [],
        "no_production_claim": True,
        "no_structural_claim": True,
        "no_fabrication_claim": True,
        "no_historical_accuracy_claim": True,
        "no_claims": NO_CLAIMS,
    }


def cube_part(name: str, loc: tuple[float, float, float], dim: tuple[float, float, float], mat: str = "stone") -> dict[str, Any]:
    return {
        "primitive": "cube",
        "name": name,
        "location_m": [round(v, 6) for v in loc],
        "dimensions_m": [round(v, 6) for v in dim],
        "material_role": mat,
    }


def cyl_part(name: str, loc: tuple[float, float, float], radius: float, depth: float, vertices: int, mat: str = "stone") -> dict[str, Any]:
    return {
        "primitive": "cylinder",
        "name": name,
        "location_m": [round(v, 6) for v in loc],
        "radius_m": round(radius, 6),
        "depth_m": round(depth, 6),
        "vertices": vertices,
        "material_role": mat,
    }


def curve_part(name: str, curve_kind: str, span: float, spring_z: float, rise: float, y: float, bevel: float, mat: str = "rib") -> dict[str, Any]:
    return {
        "primitive": "curve",
        "name": name,
        "curve_kind": curve_kind,
        "span_m": round(span, 6),
        "spring_z_m": round(spring_z, 6),
        "rise_m": round(rise, 6),
        "y_m": round(y, 6),
        "bevel_depth_m": round(bevel, 6),
        "material_role": mat,
    }


def measured_assets() -> list[dict[str, Any]]:
    local_ratio_doc = ("local_ratio_doc", str(RATIO_RANGES_PATH.relative_to(ROOT)))
    weak_doc = ("local_ratio_doc", str(WEAK_AREAS_PATH.relative_to(ROOT)))
    source_quality = ("local_policy_doc", str(SOURCE_QUALITY_PATH.relative_to(ROOT)))
    geometry_links = ("local_link_file", str(GEOMETRY_LINKS_PATH.relative_to(ROOT)))
    semantic_links = ("local_link_file", str(SEMANTIC_LINKS_PATH.relative_to(ROOT)))

    assets: list[dict[str, Any]] = []

    assets.append(
        base_asset(
            "measured_rectangular_wall_block_v1",
            dimensions={"width": 2.2, "depth": 0.34, "height": 1.6},
            source_measurement_refs=source_refs("habs_tn181_splayed_support_opening_ratio_v0", weak_doc, source_quality),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "bevel_edges", "socket", "floor", "ceiling", "north", "south", "east", "west", "blocked", "cover", "line_of_sight_blocker", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={
                "module": "scaled wall grammar block using local opening measurement as bay-scale hint",
                "depth_to_width": round(0.34 / 2.2, 6),
                "height_to_width": round(1.6 / 2.2, 6),
                "weak_area_note": "wall thickness to span is explicitly weak in v0; this is a game blockout ratio only.",
            },
            uncertainty={"level": "high", "reason": "wall thickness evidence is weak; dimensions are gameplay-scaled grammar values"},
            sockets=[
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("ceiling_stack", "ceiling", [0, 0, 1.6], [0, 0, 1], "stack"),
                socket("north_join", "north", [0, 0.17, 0.8], [0, 1, 0], "wall_join"),
                socket("south_join", "south", [0, -0.17, 0.8], [0, -1, 0], "wall_join"),
            ],
            semantic_roles=["blocked", "cover", "line_of_sight_blocker", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "socket_count_min": 2},
            proof_primitives=[cube_part("wall_block", (0, 0, 0.8), (2.2, 0.34, 1.6), "stone")],
        )
    )

    assets.append(
        base_asset(
            "measured_floor_slab_v1",
            dimensions={"width": 2.4, "depth": 2.4, "height": 0.18},
            source_measurement_refs=source_refs("habs_tn181_round_recess_window_dimensions_v0", local_ratio_doc, source_quality),
            geometry_terms_used=["rectangle", "width", "height", "extrude", "socket", "floor", "ceiling", "north", "south", "east", "west", "walkable", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["extrude"],
            ratio_basis={
                "module": "square floor bay scaled from local bay-width examples for game construction",
                "thickness_to_width": round(0.18 / 2.4, 6),
            },
            uncertainty={"level": "medium", "reason": "slab thickness is a gameplay-scaled proportion, not a measured structural value"},
            sockets=[
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("top_walkable", "ceiling", [0, 0, 0.18], [0, 0, 1], "walkable_surface"),
                socket("north_tile_join", "north", [0, 1.2, 0.09], [0, 1, 0], "tile_join"),
                socket("east_tile_join", "east", [1.2, 0, 0.09], [1, 0, 0], "tile_join"),
            ],
            semantic_roles=["walkable", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "walkable_top": True},
            proof_primitives=[cube_part("floor_slab", (0, 0, 0.09), (2.4, 2.4, 0.18), "walkable")],
        )
    )

    assets.append(
        base_asset(
            "measured_square_pier_v1",
            dimensions={"width": 0.46, "depth": 0.46, "height": 3.22},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", "palladio_corinthian_column_ratio_v0", weak_doc, geometry_links),
            geometry_terms_used=["square", "width", "height", "aspect_ratio", "extrude", "bevel_edges", "floor", "ceiling", "column_cap", "support", "blocked", "collision_proxy"],
            profile_terms=["square"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"height_to_width": 7.0, "source_band": "column height/diameter 7.0-9.0 used as support grammar hint"},
            uncertainty={"level": "medium", "reason": "pier-specific support width to bay span is weak; column ratio used as fallback grammar"},
            sockets=[
                socket("base", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("cap", "column_cap", [0, 0, 3.22], [0, 0, 1], "cap_attachment"),
            ],
            semantic_roles=["support", "blocked", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "height_to_width_in_local_column_band": True},
            proof_primitives=[cube_part("square_pier", (0, 0, 1.61), (0.46, 0.46, 3.22), "support")],
        )
    )

    assets.append(
        base_asset(
            "measured_round_column_v1",
            dimensions={"width": 0.42, "depth": 0.42, "height": 3.0, "diameter": 0.42, "radius": 0.21},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", "palladio_corinthian_column_ratio_v0", local_ratio_doc),
            geometry_terms_used=["circle", "diameter", "radius", "height", "aspect_ratio", "extrude", "radial", "floor", "ceiling", "column_cap", "support", "blocked", "collision_proxy"],
            profile_terms=["circle"],
            operations=["extrude"],
            ratio_basis={"height_to_diameter": round(3.0 / 0.42, 6), "source_band": "local column height/diameter 7.0-9.0"},
            uncertainty={"level": "low", "reason": "column height/diameter ratio is locally source-backed, but base/capital details remain simplified"},
            sockets=[
                socket("base", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("cap", "column_cap", [0, 0, 3.0], [0, 0, 1], "cap_attachment"),
                socket("radial_center", "radial", [0, 0, 1.5], [1, 0, 0], "radial_array_anchor"),
            ],
            semantic_roles=["support", "blocked", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "height_to_diameter_in_local_column_band": True},
            proof_primitives=[cyl_part("round_column", (0, 0, 1.5), 0.21, 3.0, 32, "support")],
        )
    )

    assets.append(
        base_asset(
            "measured_octagon_column_v1",
            dimensions={"width": 0.48, "depth": 0.48, "height": 3.36, "diameter": 0.48, "radius": 0.24},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", "ely_octagon_width_height_v0", local_ratio_doc),
            geometry_terms_used=["octagon", "diameter", "radius", "height", "aspect_ratio", "extrude", "radial", "floor", "ceiling", "column_cap", "support", "blocked", "collision_proxy"],
            profile_terms=["octagon"],
            operations=["extrude"],
            ratio_basis={"height_to_diameter": 7.0, "octagonal_plan_reference": "octagon records guide profile choice only, not historical scale"},
            uncertainty={"level": "medium", "reason": "octagonal profile is source-motivated but column subdivision remains simplified"},
            sockets=[
                socket("base", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("cap", "column_cap", [0, 0, 3.36], [0, 0, 1], "cap_attachment"),
                socket("radial_center", "radial", [0, 0, 1.68], [1, 0, 0], "radial_array_anchor"),
            ],
            semantic_roles=["support", "blocked", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "octagon_profile": True},
            proof_primitives=[cyl_part("octagon_column", (0, 0, 1.68), 0.24, 3.36, 8, "support")],
        )
    )

    assets.append(
        base_asset(
            "measured_base_plinth_v1",
            dimensions={"width": 0.78, "depth": 0.78, "height": 0.28},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", "palladio_corinthian_column_ratio_v0", weak_doc),
            geometry_terms_used=["square", "width", "height", "extrude", "bevel_edges", "floor", "ceiling", "support", "collision_proxy"],
            profile_terms=["square"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"plinth_width_to_round_column_diameter": round(0.78 / 0.42, 6), "source_note": "base subdivision not measured in v0; local column ratios only bound the attached support"},
            uncertainty={"level": "high", "reason": "base/capital subdivision is explicitly weak in local notes"},
            sockets=[
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("column_seat", "ceiling", [0, 0, 0.28], [0, 0, 1], "column_base_attachment"),
            ],
            semantic_roles=["support", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "has_column_socket": True},
            proof_primitives=[cube_part("base_plinth", (0, 0, 0.14), (0.78, 0.78, 0.28), "cap")],
        )
    )

    assets.append(
        base_asset(
            "measured_cap_block_v1",
            dimensions={"width": 0.68, "depth": 0.68, "height": 0.22},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", "palladio_corinthian_column_ratio_v0", weak_doc),
            geometry_terms_used=["square", "width", "height", "extrude", "bevel_edges", "floor", "ceiling", "column_cap", "support", "collision_proxy"],
            profile_terms=["square"],
            operations=["extrude", "bevel_edges"],
            ratio_basis={"cap_width_to_round_column_diameter": round(0.68 / 0.42, 6), "source_note": "capital height is not measured in v0; this is a simplified cap socket component"},
            uncertainty={"level": "high", "reason": "capital subdivision is explicitly weak in local notes"},
            sockets=[
                socket("column_receive", "floor", [0, 0, 0], [0, 0, -1], "column_cap_attachment"),
                socket("ceiling_stack", "ceiling", [0, 0, 0.22], [0, 0, 1], "stack"),
            ],
            semantic_roles=["support", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "has_column_socket": True},
            proof_primitives=[cube_part("cap_block", (0, 0, 0.11), (0.68, 0.68, 0.22), "cap")],
        )
    )

    assets.append(
        base_asset(
            "measured_pointed_arch_doorway_v1",
            dimensions={"width": 2.4, "depth": 0.48, "height": 2.9, "opening_width": 1.3, "springline_height": 1.55, "arch_rise": round(1.3 * 0.866, 6)},
            source_measurement_refs=source_refs("pointed_arch_equilateral_rule_v0", "amiens_gothic_nave_span_height_v0", "chartres_gothic_nave_span_height_v0", local_ratio_doc, semantic_links),
            geometry_terms_used=["pointed_arch_profile", "rectangle", "width", "height", "aspect_ratio", "extrude", "compound_asset", "socket", "arch_springline", "floor", "north", "south", "blocked", "line_of_sight_blocker", "collision_proxy"],
            profile_terms=["pointed_arch_profile", "rectangle"],
            operations=["compound_asset", "extrude"],
            ratio_basis={"rise_to_opening_span": 0.866, "construction_basis": "local equilateral pointed arch rule", "nave_height_examples_are_envelope_hints_only": True},
            uncertainty={"level": "medium", "reason": "rise/span is source-backed; frame thickness and jamb sizes are gameplay-scaled"},
            sockets=[
                socket("threshold", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("portal", "socket", [0, -0.25, 0.9], [0, -1, 0], "doorway_connection"),
                socket("springline_left", "arch_springline", [-0.65, -0.24, 1.55], [-1, 0, 0], "arch_rule_marker"),
                socket("springline_right", "arch_springline", [0.65, -0.24, 1.55], [1, 0, 0], "arch_rule_marker"),
            ],
            semantic_roles=["blocked", "line_of_sight_blocker", "collision_proxy", "panel_socket"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "has_portal_socket": True},
            proof_primitives=[
                cube_part("left_jamb", (-0.86, 0, 0.775), (0.36, 0.48, 1.55), "stone"),
                cube_part("right_jamb", (0.86, 0, 0.775), (0.36, 0.48, 1.55), "stone"),
                cube_part("threshold", (0, 0, 0.06), (1.8, 0.56, 0.12), "walkable"),
                curve_part("pointed_arch_rib", "pointed", 1.3, 1.55, 1.1258, -0.26, 0.055, "rib"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_round_arch_bay_v1",
            dimensions={"width": 2.6, "depth": 0.48, "height": 2.45, "opening_width": 1.5, "springline_height": 1.25, "arch_rise": 0.75},
            source_measurement_refs=source_refs("round_arch_semicircular_rule_v0", "pont_du_gard_upper_arcade_span_v0", "habs_tn181_round_recess_window_dimensions_v0", local_ratio_doc),
            geometry_terms_used=["arch_profile", "circle", "rectangle", "width", "height", "aspect_ratio", "extrude", "compound_asset", "socket", "arch_springline", "floor", "north", "south", "blocked", "line_of_sight_blocker", "collision_proxy"],
            profile_terms=["arch_profile", "circle", "rectangle"],
            operations=["compound_asset", "extrude"],
            ratio_basis={"rise_to_opening_span": 0.5, "construction_basis": "local semicircular arch rule"},
            uncertainty={"level": "medium", "reason": "semicircular rise/span is source-backed; frame sizes are simplified"},
            sockets=[
                socket("bay_floor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("opening", "socket", [0, -0.25, 0.85], [0, -1, 0], "bay_connection"),
                socket("springline_left", "arch_springline", [-0.75, -0.24, 1.25], [-1, 0, 0], "arch_rule_marker"),
                socket("springline_right", "arch_springline", [0.75, -0.24, 1.25], [1, 0, 0], "arch_rule_marker"),
            ],
            semantic_roles=["blocked", "line_of_sight_blocker", "collision_proxy", "panel_socket"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "has_opening_socket": True},
            proof_primitives=[
                cube_part("left_pier", (-0.98, 0, 0.625), (0.36, 0.48, 1.25), "stone"),
                cube_part("right_pier", (0.98, 0, 0.625), (0.36, 0.48, 1.25), "stone"),
                curve_part("round_arch_rib", "round", 1.5, 1.25, 0.75, -0.26, 0.055, "rib"),
                cube_part("low_spandrel_left", (-1.08, 0, 1.85), (0.32, 0.42, 0.62), "stone"),
                cube_part("low_spandrel_right", (1.08, 0, 1.85), (0.32, 0.42, 0.62), "stone"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_lancet_window_bay_v1",
            dimensions={"width": 1.35, "depth": 0.32, "height": 2.65, "opening_width": 0.55, "springline_height": 0.95, "arch_rise": 0.7},
            source_measurement_refs=source_refs("pointed_arch_lancet_constraint_v0", "pointed_arch_equilateral_rule_v0", local_ratio_doc, weak_doc),
            geometry_terms_used=["pointed_arch_profile", "rectangle", "width", "height", "aspect_ratio", "extrude", "compound_asset", "socket", "arch_springline", "floor", "blocked", "line_of_sight_blocker", "decorative_only", "collision_proxy"],
            profile_terms=["pointed_arch_profile", "rectangle"],
            operations=["compound_asset", "extrude"],
            ratio_basis={"rise_to_opening_span": round(0.7 / 0.55, 6), "construction_basis": "lancet constraint is greater than equilateral rise/span"},
            uncertainty={"level": "medium", "reason": "lancet relation is local constraint-based; frame measurements remain weak"},
            sockets=[
                socket("wall_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
                socket("window_opening", "socket", [0, -0.18, 1.05], [0, -1, 0], "line_of_sight_frame"),
                socket("springline", "arch_springline", [0, -0.16, 0.95], [0, 0, 1], "arch_rule_marker"),
            ],
            semantic_roles=["line_of_sight_blocker", "decorative_only", "collision_proxy", "panel_socket"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "lancet_rise_above_equilateral": True},
            proof_primitives=[
                cube_part("window_back_wall", (0, 0.05, 1.325), (1.35, 0.18, 2.65), "stone"),
                curve_part("lancet_rib", "pointed", 0.55, 0.95, 0.7, -0.16, 0.032, "rib"),
                cube_part("sill", (0, -0.16, 0.32), (0.78, 0.12, 0.12), "cap"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_rail_unit_v1",
            dimensions={"width": 1.8, "depth": 0.2, "height": 1.05},
            source_measurement_refs=source_refs("vitruvius_doric_column_ratio_v0", local_ratio_doc, weak_doc),
            geometry_terms_used=["rectangle", "capsule", "width", "height", "extrude", "array_linear", "east", "west", "floor", "barrier", "rail", "cover", "collision_proxy"],
            profile_terms=["rectangle", "capsule"],
            operations=["compound_asset", "extrude", "array_linear"],
            ratio_basis={"post_height_to_post_width": round(1.05 / 0.16, 6), "source_note": "column ratio informs slender vertical post grammar only"},
            uncertainty={"level": "high", "reason": "rail dimensions are gameplay barrier values; no local railing measurement packet exists"},
            sockets=[
                socket("left_repeat", "west", [-0.9, 0, 0.52], [-1, 0, 0], "repeat"),
                socket("right_repeat", "east", [0.9, 0, 0.52], [1, 0, 0], "repeat"),
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
            ],
            semantic_roles=["barrier", "rail", "cover", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "has_repeat_sockets": True},
            proof_primitives=[
                cube_part("left_post", (-0.78, 0, 0.5), (0.16, 0.16, 1.0), "support"),
                cube_part("right_post", (0.78, 0, 0.5), (0.16, 0.16, 1.0), "support"),
                cube_part("top_rail", (0, 0, 0.92), (1.72, 0.12, 0.12), "rail"),
                cube_part("mid_rail", (0, 0, 0.55), (1.62, 0.08, 0.08), "rail"),
            ],
        )
    )

    assets.append(
        base_asset(
            "measured_stair_block_run_v1",
            dimensions={"width": 1.2, "depth": 1.6, "height": 0.72, "step_rise": 0.18, "step_run": 0.4},
            source_measurement_refs=source_refs(weak_doc, local_ratio_doc, source_quality),
            geometry_terms_used=["rectangle", "height", "length", "extrude", "array_linear", "floor", "ceiling", "north", "south", "walkable", "vertical_transition", "collision_proxy"],
            profile_terms=["rectangle"],
            operations=["compound_asset", "extrude", "array_linear"],
            ratio_basis={"steps": 4, "rise_to_run": round(0.18 / 0.4, 6), "source_note": "stair_tower is fetch_needed in v0; this is a gameplay traversal blockout"},
            uncertainty={"level": "high", "reason": "local notes explicitly mark stair dimensions as fetch_needed"},
            sockets=[
                socket("lower_landing", "south", [0, -0.8, 0.0], [0, -1, 0], "route_entry"),
                socket("upper_landing", "north", [0, 0.8, 0.72], [0, 1, 0], "route_exit"),
                socket("floor_anchor", "floor", [0, 0, 0], [0, 0, -1], "placement"),
            ],
            semantic_roles=["walkable", "vertical_transition", "collision_proxy"],
            validation_expectations={"nonzero_bounds": True, "known_geometry_terms": True, "has_route_sockets": True},
            proof_primitives=[
                cube_part("step_00", (0, -0.6, 0.09), (1.2, 0.4, 0.18), "walkable"),
                cube_part("step_01", (0, -0.2, 0.27), (1.2, 0.4, 0.18), "walkable"),
                cube_part("step_02", (0, 0.2, 0.45), (1.2, 0.4, 0.18), "walkable"),
                cube_part("step_03", (0, 0.6, 0.63), (1.2, 0.4, 0.18), "walkable"),
            ],
        )
    )

    return assets


def validate_source_refs(asset: dict[str, Any], measurement_ids: set[str]) -> None:
    refs = asset["source_measurement_refs"]
    if not refs:
        fail(f"{asset['asset_id']} needs at least one local measurement or ratio source")
    for ref in refs:
        ref_type = ref["ref_type"]
        value = ref["ref"]
        if ref_type == "measurement_id":
            if value not in measurement_ids:
                fail(f"{asset['asset_id']} references unknown measurement_id `{value}`")
        elif ref_type in {"local_ratio_doc", "local_policy_doc", "local_link_file"}:
            if not (ROOT / value).exists():
                fail(f"{asset['asset_id']} references missing local file `{value}`")
        else:
            fail(f"{asset['asset_id']} has unsupported ref_type `{ref_type}`")


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
        "no_production_claim",
        "no_structural_claim",
    ]
    for field in required:
        if field not in asset:
            fail(f"{asset.get('asset_id')} missing required field `{field}`")
    if asset["no_production_claim"] is not True or asset["no_structural_claim"] is not True or asset.get("no_fabrication_claim") is not True:
        fail(f"{asset['asset_id']} no-claim booleans must be true")
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
    dims = asset["dimensions_m"]
    for key in ("width", "depth", "height"):
        if float(dims.get(key, 0.0)) <= 0.0:
            fail(f"{asset['asset_id']} has non-positive dimension `{key}`")
    if not asset["sockets"]:
        fail(f"{asset['asset_id']} should expose at least one useful socket")
    connector_terms = {term_id for term_id, term in terms.items() if term["category"] == "connector"}
    for item in asset["sockets"]:
        if item["connector_term"] not in connector_terms:
            fail(f"{asset['asset_id']} socket {item['socket_id']} uses unknown connector `{item['connector_term']}`")


def write_recipes(assets: list[dict[str, Any]]) -> dict[str, str]:
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for asset in assets:
        path = RECIPE_DIR / f"{asset['asset_id']}.json"
        path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
        paths[asset["asset_id"]] = str(path.relative_to(ROOT))
    return paths


def write_index(assets: list[dict[str, Any]], paths: dict[str, str]) -> None:
    index = {
        "schema": "asset_mill_measured_index_v1",
        "created_at_utc": now_iso(),
        "asset_count": len(assets),
        "recipe_dir": str(RECIPE_DIR.relative_to(ROOT)),
        "source_files": [
            str(MEASUREMENT_PATH.relative_to(ROOT)),
            str(MEASUREMENT_SOURCES_PATH.relative_to(ROOT)),
            str(GEOMETRY_LINKS_PATH.relative_to(ROOT)),
            str(SEMANTIC_LINKS_PATH.relative_to(ROOT)),
            str(RATIO_RANGES_PATH.relative_to(ROOT)),
            str(SOURCE_QUALITY_PATH.relative_to(ROOT)),
            str(WEAK_AREAS_PATH.relative_to(ROOT)),
        ],
        "assets": [
            {
                "asset_id": asset["asset_id"],
                "recipe_path": paths[asset["asset_id"]],
                "dimensions_m": asset["dimensions_m"],
                "geometry_terms_used": asset["geometry_terms_used"],
                "source_measurement_refs": asset["source_measurement_refs"],
                "semantic_roles": asset["semantic_roles"],
                "socket_count": len(asset["sockets"]),
                "uncertainty": asset["uncertainty"],
            }
            for asset in assets
        ],
        "rules": {
            "local_sources_only": True,
            "web_search_used": False,
            "measurements_are_ratio_hints_only": True,
            "no_unknown_geometry_terms": True,
            "no_fake_historical_source_claim": True,
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
        },
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def write_report(assets: list[dict[str, Any]], paths: dict[str, str]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Asset Mill Measured Components v1",
        "",
        "Measured component recipes built from local geometry dictionary terms and local measurement/range packets only.",
        "",
        "Measurements are used as grammar references and ratio hints only. These assets do not claim historical accuracy, structural safety, fabrication readiness, or production approval.",
        "",
        "## Outputs",
        "",
        f"- Recipe directory: `{RECIPE_DIR.relative_to(ROOT)}`",
        f"- Index: `{INDEX_PATH.relative_to(ROOT)}`",
        f"- Receipt: `{RECEIPT_PATH.relative_to(ROOT)}`",
        "",
        "## Components",
        "",
        "| Asset | Dimensions m | Terms | Source refs | Uncertainty | Sockets | Recipe |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for asset in assets:
        dims = asset["dimensions_m"]
        dim_text = f"{dims['width']} x {dims['depth']} x {dims['height']}"
        terms = ", ".join(asset["geometry_terms_used"][:6])
        if len(asset["geometry_terms_used"]) > 6:
            terms += ", ..."
        refs = ", ".join(ref["ref"] for ref in asset["source_measurement_refs"][:3])
        uncertainty = asset["uncertainty"]["level"]
        lines.append(f"| `{asset['asset_id']}` | {dim_text} | {terms} | {refs} | {uncertainty} | {len(asset['sockets'])} | `{paths[asset['asset_id']]}` |")
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "- every asset references known geometry dictionary terms: true",
            "- every asset references at least one local measurement or ratio source: true",
            "- every asset has nonzero bounds: true",
            "- sockets are present where useful: true",
            "- no unknown geometry terms: true",
            "- no web search: true",
            "- no fake historical/source claim: true",
            "- no structural/fabrication/production approval: true",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(assets: list[dict[str, Any]], paths: dict[str, str]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "asset_mill_measured_components_v1",
        "created_at_utc": now_iso(),
        "asset_count": len(assets),
        "recipes": paths,
        "index": str(INDEX_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "source_files": [
            str(MEASUREMENT_PATH.relative_to(ROOT)),
            str(MEASUREMENT_SOURCES_PATH.relative_to(ROOT)),
            str(RATIO_RANGES_PATH.relative_to(ROOT)),
            str(SOURCE_QUALITY_PATH.relative_to(ROOT)),
            str(WEAK_AREAS_PATH.relative_to(ROOT)),
        ],
        "acceptance": {
            "every_asset_references_known_geometry_terms": True,
            "every_asset_references_local_measurement_or_ratio_source": True,
            "every_asset_has_nonzero_bounds": True,
            "sockets_present_where_useful": True,
            "no_unknown_geometry_terms": True,
            "web_search_used": False,
            "no_fake_historical_source_claim": True,
            "no_structural_fabrication_or_production_approval": True,
        },
        "no_claims": NO_CLAIMS,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    terms = load_dictionary_terms()
    measurements = load_json(MEASUREMENT_PATH)["measurements"]
    measurement_ids = {item["measurement_id"] for item in measurements}
    assets = measured_assets()
    ids = set()
    for asset in assets:
        if asset["asset_id"] in ids:
            fail(f"duplicate asset_id `{asset['asset_id']}`")
        ids.add(asset["asset_id"])
        validate_recipe(asset, terms, measurement_ids)
    paths = write_recipes(assets)
    write_index(assets, paths)
    write_report(assets, paths)
    write_receipt(assets, paths)
    print(f"wrote {len(assets)} measured component recipes")
    print(f"index: {INDEX_PATH.relative_to(ROOT)}")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
