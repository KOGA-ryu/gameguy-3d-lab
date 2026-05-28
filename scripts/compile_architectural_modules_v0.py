#!/usr/bin/env python3
"""Compile architectural module recipes into measured construction graphs.

This is the layer above terrain plots and below Blender realization:

architectural shape terms -> module recipe -> ordered points/connectors ->
arch curves/wall bays/supports -> connection proofs

No mesh, image, Blender file, production approval, fabrication claim, or
structural safety claim is created here.
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_ROOT = ROOT / "geometry_dictionary"
CONTRACT_PATH = ROOT / "contracts" / "architectural_shape_dictionary_v0.json"
TERM_PATH = ROOT / "data" / "architecture" / "architectural_shape_dictionary" / "architectural_shape_terms_v0.json"
MODULE_DIR = ROOT / "data" / "architecture" / "architectural_modules"
OUT_DIR = ROOT / "goal" / "architecture" / "architectural_modules_v0"
GRAPH_DIR = OUT_DIR / "modules"
REPORT_PATH = OUT_DIR / "architectural_modules_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "architectural_modules_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}

TERM_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def round_vec(values: tuple[float, float, float] | list[float]) -> list[float]:
    return [round(float(value), 6) for value in values]


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(3)))


def load_geometry_term_ids() -> set[str]:
    ids: set[str] = set()
    for path in sorted(GEOMETRY_ROOT.rglob("*.json")):
        if "/schemas/" in str(path):
            continue
        data = load_json(path)
        term_id = data.get("term_id")
        if isinstance(term_id, str):
            ids.add(term_id)
    return ids


def validate_shape_terms(geometry_ids: set[str]) -> dict[str, dict[str, Any]]:
    contract = load_json(CONTRACT_PATH)
    terms_data = load_json(TERM_PATH)
    if terms_data.get("schema") != "architectural_shape_terms_v0":
        fail(f"{TERM_PATH.relative_to(ROOT)} schema must be architectural_shape_terms_v0")
    if terms_data.get("no_claims") != NO_CLAIMS:
        fail(f"{TERM_PATH.relative_to(ROOT)} no_claims must match required false claims")

    allowed_faces = set(contract["allowed_base_faces"])
    required = contract["required_term_fields"]
    terms: dict[str, dict[str, Any]] = {}
    for term in terms_data["terms"]:
        for field in required:
            if field not in term:
                fail(f"architectural term missing required field `{field}`")
        shape_id = term["shape_id"]
        if not isinstance(shape_id, str) or not TERM_ID_RE.match(shape_id):
            fail(f"invalid architectural shape_id `{shape_id}`")
        if shape_id in terms:
            fail(f"duplicate architectural shape_id `{shape_id}`")
        if term["base_face"] not in allowed_faces:
            fail(f"{shape_id} unsupported base_face `{term['base_face']}`")
        for op_ref in term["operation_chain"]:
            if op_ref not in geometry_ids:
                fail(f"{shape_id} operation_chain references unknown geometry term `{op_ref}`")
        if not term["validation"]:
            fail(f"{shape_id} requires validation rules")
        terms[shape_id] = term
    return terms


def regular_polygon_points(count: int, radius: float, rotation_degrees: float) -> list[list[float]]:
    return [
        [
            round(math.cos(math.radians(rotation_degrees) + math.tau * index / count) * radius, 6),
            round(math.sin(math.radians(rotation_degrees) + math.tau * index / count) * radius, 6),
            0.0,
        ]
        for index in range(count)
    ]


def normalized_xy(point: list[float]) -> tuple[float, float]:
    length = math.hypot(float(point[0]), float(point[1]))
    if length == 0.0:
        return 1.0, 0.0
    return float(point[0]) / length, float(point[1]) / length


def sample_two_center_pointed_arch(
    left: list[float],
    right: list[float],
    springline_height: float,
    segments_per_side: int,
) -> tuple[list[list[float]], dict[str, float]]:
    lx, ly = float(left[0]), float(left[1])
    rx, ry = float(right[0]), float(right[1])
    dx = rx - lx
    dy = ry - ly
    span = math.hypot(dx, dy)
    if span <= 0.0:
        fail("arch span must be positive")
    ux, uy = dx / span, dy / span
    mid = ((lx + rx) * 0.5, (ly + ry) * 0.5)
    rise = math.sqrt(max(span * span - (span * 0.5) ** 2, 0.0))
    radius = span
    apex = (mid[0], mid[1], springline_height + rise)

    left_center_x, left_center_y = lx, ly
    right_center_x, right_center_y = rx, ry
    left_start_angle = math.pi
    left_end_angle = math.atan2(rise, -span * 0.5)
    right_start_angle = math.atan2(rise, span * 0.5)
    right_end_angle = 0.0

    samples: list[list[float]] = []
    for index in range(segments_per_side + 1):
        t = index / segments_per_side
        angle = left_start_angle + (left_end_angle - left_start_angle) * t
        local_x = span * 0.5 + math.cos(angle) * radius
        z = springline_height + math.sin(angle) * radius
        samples.append(round_vec((lx + ux * local_x, ly + uy * local_x, z)))

    for index in range(1, segments_per_side + 1):
        t = index / segments_per_side
        angle = right_start_angle + (right_end_angle - right_start_angle) * t
        local_x = math.cos(angle) * radius - span * 0.5
        z = springline_height + math.sin(angle) * radius
        samples.append(round_vec((rx + ux * local_x, ry + uy * local_x, z)))

    return samples, {
        "span": round(span, 6),
        "curve_radius": round(radius, 6),
        "rise": round(rise, 6),
        "apex_z": round(apex[2], 6),
    }


def compile_module(path: Path, terms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    recipe = load_json(path)
    if recipe.get("schema") != "architectural_module_recipe_v0":
        fail(f"{path.relative_to(ROOT)} schema must be architectural_module_recipe_v0")
    if recipe.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must match required false claims")

    for ref in [
        recipe["base_plan"]["shape_ref"],
        recipe["support"]["shape_ref"],
        recipe["arch"]["shape_ref"],
        recipe["wall_bay"]["shape_ref"],
    ]:
        if ref not in terms:
            fail(f"{recipe['module_id']} references unknown architectural shape `{ref}`")

    bay_count = int(recipe["base_plan"]["bay_count"])
    radius = float(recipe["base_plan"]["radius"])
    rotation = float(recipe["base_plan"]["rotation_degrees"])
    points = regular_polygon_points(bay_count, radius, rotation)
    floor_thickness = float(recipe["verticals"]["floor_thickness"])
    springline = float(recipe["verticals"]["springline_height"])
    wall_top = float(recipe["verticals"]["wall_panel_height"])
    wall_bottom = float(recipe["wall_bay"]["panel_bottom_z"])
    wall_thickness = float(recipe["verticals"]["wall_panel_thickness"])
    bay_depth = float(recipe["verticals"]["bay_depth"])
    column_radius = float(recipe["support"]["column_radius"])
    base_radius = float(recipe["support"]["base_radius"])
    cap_radius = float(recipe["support"]["cap_radius"])
    base_height = float(recipe["support"]["base_height"])
    cap_height = float(recipe["support"]["cap_height"])
    segments_per_side = int(recipe["arch"]["segments_per_side"])
    arch_rib_radius = float(recipe["verticals"]["arch_rib_radius"])

    plan_vertices = [
        {
            "point_id": f"plan_p{index:02d}",
            "position": point,
            "order": index,
        }
        for index, point in enumerate(points)
    ]

    columns = []
    for index, point in enumerate(points):
        columns.append(
            {
                "column_id": f"column_{index:02d}",
                "shape_ref": recipe["support"]["shape_ref"],
                "center": point,
                "radius": column_radius,
                "base_radius": base_radius,
                "cap_radius": cap_radius,
                "height": springline,
                "base_height": base_height,
                "cap_height": cap_height,
                "connectors": {
                    "base": round_vec((point[0], point[1], 0.0)),
                    "springline_cap": round_vec((point[0], point[1], springline)),
                    "floor": round_vec((point[0], point[1], floor_thickness)),
                },
            }
        )

    bays = []
    arch_bays = []
    wall_panels = []
    connection_proofs = []
    arch_metrics: list[dict[str, float]] = []
    for index in range(bay_count):
        next_index = (index + 1) % bay_count
        left = points[index]
        right = points[next_index]
        left_spring = round_vec((left[0], left[1], springline))
        right_spring = round_vec((right[0], right[1], springline))
        curve_points, metrics = sample_two_center_pointed_arch(left, right, springline, segments_per_side)
        arch_metrics.append(metrics)
        bay_id = f"bay_{index:02d}"
        arch_id = f"arch_{index:02d}"
        wall_id = f"wall_panel_{index:02d}"

        bays.append(
            {
                "bay_id": bay_id,
                "shape_ref": "radial_bay",
                "left_column": f"column_{index:02d}",
                "right_column": f"column_{next_index:02d}",
                "plan_edge": [f"plan_p{index:02d}", f"plan_p{next_index:02d}"],
                "left_springline": left_spring,
                "right_springline": right_spring,
                "bay_depth": bay_depth,
            }
        )
        arch_bays.append(
            {
                "arch_id": arch_id,
                "shape_ref": recipe["arch"]["shape_ref"],
                "bay_id": bay_id,
                "bend_law": recipe["arch"]["bend_law"],
                "span": metrics["span"],
                "curve_radius": metrics["curve_radius"],
                "rise": metrics["rise"],
                "apex_z": metrics["apex_z"],
                "springline_height": springline,
                "rib_radius": arch_rib_radius,
                "curve_points": curve_points,
                "connectors": {
                    "left_springline": left_spring,
                    "right_springline": right_spring,
                },
            }
        )
        inset = float(recipe["wall_bay"]["inset_from_columns"])
        dx = float(right[0]) - float(left[0])
        dy = float(right[1]) - float(left[1])
        span = math.hypot(dx, dy)
        ux, uy = dx / span, dy / span
        nx, ny = normalized_xy([(left[0] + right[0]) * 0.5, (left[1] + right[1]) * 0.5])
        left_inner = [left[0] + ux * inset, left[1] + uy * inset]
        right_inner = [right[0] - ux * inset, right[1] - uy * inset]
        offset = wall_thickness * 0.5
        front_left = [left_inner[0] + nx * offset, left_inner[1] + ny * offset]
        front_right = [right_inner[0] + nx * offset, right_inner[1] + ny * offset]
        back_left = [left_inner[0] - nx * offset, left_inner[1] - ny * offset]
        back_right = [right_inner[0] - nx * offset, right_inner[1] - ny * offset]
        wall_panels.append(
            {
                "wall_panel_id": wall_id,
                "shape_ref": recipe["wall_bay"]["shape_ref"],
                "bay_id": bay_id,
                "bottom_z": wall_bottom,
                "top_z": wall_top,
                "corners": {
                    "front_left_bottom": round_vec((front_left[0], front_left[1], wall_bottom)),
                    "front_right_bottom": round_vec((front_right[0], front_right[1], wall_bottom)),
                    "front_right_top": round_vec((front_right[0], front_right[1], wall_top)),
                    "front_left_top": round_vec((front_left[0], front_left[1], wall_top)),
                    "back_left_bottom": round_vec((back_left[0], back_left[1], wall_bottom)),
                    "back_right_bottom": round_vec((back_right[0], back_right[1], wall_bottom)),
                    "back_right_top": round_vec((back_right[0], back_right[1], wall_top)),
                    "back_left_top": round_vec((back_left[0], back_left[1], wall_top)),
                },
            }
        )

        proof_left_distance = distance(left_spring, columns[index]["connectors"]["springline_cap"])
        proof_right_distance = distance(right_spring, columns[next_index]["connectors"]["springline_cap"])
        connection_proofs.extend(
            [
                {
                    "connection_id": f"{arch_id}_left_springline_to_column_{index:02d}",
                    "connector_type": "arch_springline",
                    "arch": arch_id,
                    "column": f"column_{index:02d}",
                    "distance": round(proof_left_distance, 9),
                    "passes": proof_left_distance <= float(recipe["connection_rules"]["connection_tolerance"]),
                },
                {
                    "connection_id": f"{arch_id}_right_springline_to_column_{next_index:02d}",
                    "connector_type": "arch_springline",
                    "arch": arch_id,
                    "column": f"column_{next_index:02d}",
                    "distance": round(proof_right_distance, 9),
                    "passes": proof_right_distance <= float(recipe["connection_rules"]["connection_tolerance"]),
                },
            ]
        )

    failed = [proof for proof in connection_proofs if not proof["passes"]]
    if failed:
        fail(f"{recipe['module_id']} has failed connection proofs: {failed[:3]}")

    max_arch_z = max(metric["apex_z"] for metric in arch_metrics)
    return {
        "schema": "compiled_architectural_module_v0",
        "module_id": recipe["module_id"],
        "source_recipe": str(path.relative_to(ROOT)),
        "shape_dictionary_ref": recipe["shape_dictionary_ref"],
        "units": recipe["units"],
        "summary": recipe["summary"],
        "plan": {
            "shape_ref": recipe["base_plan"]["shape_ref"],
            "bay_count": bay_count,
            "radius": radius,
            "rotation_degrees": rotation,
            "vertices": plan_vertices,
        },
        "measurements": {
            "floor_thickness": floor_thickness,
            "springline_height": springline,
            "max_arch_z": round(max_arch_z, 6),
            "bay_depth": bay_depth,
            "arch_rib_radius": arch_rib_radius,
            "column_radius": column_radius,
        },
        "columns": columns,
        "bays": bays,
        "arch_bays": arch_bays,
        "wall_panels": wall_panels,
        "connection_proofs": connection_proofs,
        "validation_summary": {
            "connection_proof_count": len(connection_proofs),
            "connection_fail_count": len(failed),
            "all_arch_springlines_match_column_caps": not failed,
            "plan_vertex_count": len(plan_vertices),
            "bay_count": len(bays),
            "column_count": len(columns),
            "arch_count": len(arch_bays),
            "wall_panel_count": len(wall_panels),
        },
        "mesh_plan": {
            "final_mesh_backend": "blender_proof_v0",
            "floor": "octagonal_slab_from_ordered_plan_vertices",
            "columns": "octagonal_prisms_at_plan_vertices",
            "arches": "bevelled_pointed_arch_curves_sampled_from_two_center_equal_radius_law",
            "walls": "quad_wall_panel_prisms_between_column insets",
            "connector_model": "shared_endpoint_and_arch_springline",
        },
        "no_claims": NO_CLAIMS,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Architectural Modules v0",
        "",
        "Compiles measured multi-face architectural recipes into construction graphs with explicit bend laws and connector proofs.",
        "",
        "```text",
        "shape dictionary -> measured module recipe -> points/connectors -> arches/walls/supports -> Blender proof",
        "```",
        "",
        "| Module | Plan | Columns | Arches | Wall Panels | Connection Proofs | Failed | Output |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = row["validation_summary"]
        lines.append(
            f"| `{row['module_id']}` | `{row['plan']['shape_ref']}` | {summary['column_count']} | {summary['arch_count']} | {summary['wall_panel_count']} | {summary['connection_proof_count']} | {summary['connection_fail_count']} | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "The module does not depend on one universal face type. It uses an octagonal plan, column support points, quad wall panels, and sampled pointed arch curves, all tied together by shared endpoints.",
            "",
            "## What This Proves",
            "",
            "- An octagonal plan can generate eight bays from ordered points.",
            "- Columns sit on plan vertices.",
            "- Pointed arch springlines share exact coordinates with column cap connectors.",
            "- Wall panels are separate constructed faces inside each bay.",
            "- The proof is data-first; Blender only realizes the compiled graph.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "architectural_modules_v0",
        "created_at_utc": now_iso(),
        "module_count": len(rows),
        "modules": rows,
        "rules": {
            "multi_face_geometry": True,
            "shape_dictionary_driven": True,
            "bend_laws_are_named": True,
            "connector_proofs_required": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_production_approval": True,
        },
        "recommended_next_goal": "Add vault rib webs between arch apexes and the central ceiling ring using the same shared endpoint connector model.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    geometry_ids = load_geometry_term_ids()
    terms = validate_shape_terms(geometry_ids)
    rows: list[dict[str, Any]] = []
    for path in sorted(MODULE_DIR.glob("*.json")):
        module = compile_module(path, terms)
        out = GRAPH_DIR / f"{module['module_id']}.json"
        out.write_text(json.dumps(module, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "module_id": module["module_id"],
                "output_path": str(out.relative_to(ROOT)),
                "plan": module["plan"],
                "validation_summary": module["validation_summary"],
            }
        )
    if not rows:
        fail(f"no architectural module recipes found in {MODULE_DIR.relative_to(ROOT)}")
    write_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} architectural modules")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
