#!/usr/bin/env python3
"""Audit where folded hex terrain deformation comes from.

This is a diagnostic pass over compiled terrain and the plot vertex graph. It
does not create meshes or art. It records whether deformation is caused by the
source heightfield, fold offsets, neighbor height deltas, shared corner
averaging, or hard seam vertex sharing.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "goal" / "architecture" / "hex_terrain_fold_sites_v0" / "sites"
GRAPH_DIR = ROOT / "goal" / "architecture" / "hex_plot_vertex_graph_v0" / "graphs"
OUT_DIR = ROOT / "goal" / "architecture" / "hex_deformation_audit_v0"
AUDIT_DIR = OUT_DIR / "audits"
REPORT_PATH = OUT_DIR / "hex_deformation_audit_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "hex_deformation_audit_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}


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


def edge_signature(edge: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(edge["corner_vertex_ids"]))


def audit_pair(source_path: Path, graph_path: Path) -> dict[str, Any]:
    source = load_json(source_path)
    graph = load_json(graph_path)
    if source.get("schema") != "hex_terrain_fold_site_assembly_v0":
        fail(f"{source_path.relative_to(ROOT)} schema must be hex_terrain_fold_site_assembly_v0")
    if graph.get("schema") != "hex_plot_vertex_graph_v0":
        fail(f"{graph_path.relative_to(ROOT)} schema must be hex_plot_vertex_graph_v0")
    if source.get("no_claims") != NO_CLAIMS or graph.get("no_claims") != NO_CLAIMS:
        fail("source and graph no_claims must match required false claims")

    source_cell_by_id = {cell["cell_id"]: cell for cell in source["hex_cells"]}
    plot_by_id = {plot["cell_id"]: plot for plot in graph["hex_plots"]}
    vertex_by_id = {vertex["vertex_id"]: vertex for vertex in graph["corner_vertices"]}

    hard_seam_edges = 0
    hard_seam_edges_with_shared_vertices = 0
    hard_seam_errors: list[dict[str, Any]] = []
    for plot in graph["hex_plots"]:
        for edge in plot["edges"]:
            if edge["seam_policy"] not in {"split_riser", "split_cliff", "fold_meet_halfway"} or edge["neighbor"] is None:
                continue
            hard_seam_edges += 1
            neighbor = plot_by_id[edge["neighbor"]]
            neighbor_edges = [candidate for candidate in neighbor["edges"] if candidate["neighbor"] == plot["cell_id"]]
            if not neighbor_edges:
                hard_seam_errors.append(
                    {
                        "cell_id": plot["cell_id"],
                        "neighbor": edge["neighbor"],
                        "reason": "neighbor_reciprocal_edge_missing",
                    }
                )
                continue
            if edge_signature(edge) == edge_signature(neighbor_edges[0]):
                hard_seam_edges_with_shared_vertices += 1
                hard_seam_errors.append(
                    {
                        "cell_id": plot["cell_id"],
                        "neighbor": edge["neighbor"],
                        "seam_policy": edge["seam_policy"],
                        "reason": "hard_seam_still_shares_corner_vertex_ids",
                        "corner_vertex_ids": edge["corner_vertex_ids"],
                    }
                )

    cell_diagnostics: list[dict[str, Any]] = []
    max_corner_center_error = 0.0
    max_neighbor_delta = 0.0
    max_abs_fold_offset = 0.0
    cells_over_corner_error_025 = 0
    for plot in graph["hex_plots"]:
        source_cell = source_cell_by_id[plot["cell_id"]]
        center_height = float(plot["center_height"])
        corner_heights = [float(vertex_by_id[vertex_id]["final_height"]) for vertex_id in plot["corner_vertex_ids"]]
        corner_errors = [height - center_height for height in corner_heights]
        max_cell_corner_error = max((abs(value) for value in corner_errors), default=0.0)
        if max_cell_corner_error > 0.25:
            cells_over_corner_error_025 += 1
        deltas = [
            abs(float(edge["height_delta_to_neighbor"]))
            for edge in plot["edges"]
            if edge["height_delta_to_neighbor"] is not None
        ]
        max_cell_neighbor_delta = max(deltas, default=0.0)
        max_neighbor_delta = max(max_neighbor_delta, max_cell_neighbor_delta)
        max_corner_center_error = max(max_corner_center_error, max_cell_corner_error)
        max_abs_fold_offset = max(max_abs_fold_offset, abs(float(source_cell["fold_offset"])))
        seam_policy_counts: dict[str, int] = {}
        edge_profile_counts: dict[str, int] = {}
        for edge in plot["edges"]:
            seam_policy_counts[edge["seam_policy"]] = seam_policy_counts.get(edge["seam_policy"], 0) + 1
            edge_profile_counts[edge["edge_profile"]] = edge_profile_counts.get(edge["edge_profile"], 0) + 1
        cell_diagnostics.append(
            {
                "cell_id": plot["cell_id"],
                "q": plot["q"],
                "r": plot["r"],
                "s": plot["s"],
                "base_height": source_cell["base_height"],
                "fold_offset": source_cell["fold_offset"],
                "final_height": plot["center_height"],
                "plot_role": plot["plot_role"],
                "max_neighbor_delta": round(max_cell_neighbor_delta, 6),
                "corner_height_min": round(min(corner_heights), 6),
                "corner_height_max": round(max(corner_heights), 6),
                "max_corner_center_error": round(max_cell_corner_error, 6),
                "edge_profile_counts": dict(sorted(edge_profile_counts.items())),
                "seam_policy_counts": dict(sorted(seam_policy_counts.items())),
            }
        )

    vertex_height_ranges: list[float] = []
    for vertex in graph["corner_vertices"]:
        heights = [float(source_cell_by_id[cell_id]["final_height"]) for cell_id in vertex["adjacent_cells"]]
        if heights:
            vertex_height_ranges.append(max(heights) - min(heights))
    max_shared_vertex_source_height_range = max(vertex_height_ranges, default=0.0)

    worst_cells = sorted(
        cell_diagnostics,
        key=lambda item: (item["max_corner_center_error"], item["max_neighbor_delta"], abs(float(item["fold_offset"]))),
        reverse=True,
    )[:12]

    diagnosis = []
    if hard_seam_edges_with_shared_vertices:
        diagnosis.append("hard_seam_vertex_sharing_still_present")
    else:
        diagnosis.append("hard_seams_have_split_corner_vertices")
    if max_corner_center_error > 0.5:
        diagnosis.append("corner_averaging_or_smooth_slope_causes_visible_surface_deformation")
    if max_neighbor_delta > 1.0:
        diagnosis.append("terrain_contains_cliff_scale_height_deltas")
    if max_abs_fold_offset > 2.0:
        diagnosis.append("fold_offsets_are_primary_height_driver")

    return {
        "schema": "hex_terrain_deformation_audit_v0",
        "site_id": source["site_id"],
        "graph_id": graph["graph_id"],
        "source_terrain_assembly": str(source_path.relative_to(ROOT)),
        "source_plot_vertex_graph": str(graph_path.relative_to(ROOT)),
        "summary": {
            "cell_count": len(graph["hex_plots"]),
            "raw_corner_key_count": graph["vertex_split_summary"]["raw_corner_key_count"],
            "emitted_corner_vertex_count": graph["vertex_split_summary"]["emitted_corner_vertex_count"],
            "split_raw_corner_count": graph["vertex_split_summary"]["split_raw_corner_count"],
            "split_extra_vertex_count": graph["vertex_split_summary"]["split_extra_vertex_count"],
            "corner_seam_cap_count": len(graph.get("corner_seam_caps", [])),
            "max_abs_fold_offset": round(max_abs_fold_offset, 6),
            "max_neighbor_delta": round(max_neighbor_delta, 6),
            "max_corner_center_error": round(max_corner_center_error, 6),
            "cells_over_corner_error_0_25": cells_over_corner_error_025,
            "max_shared_vertex_source_height_range": round(max_shared_vertex_source_height_range, 6),
            "hard_seam_directed_edge_count": hard_seam_edges,
            "hard_seam_edges_with_shared_vertices": hard_seam_edges_with_shared_vertices,
            "seam_fact_count": len(graph["seam_facts"]),
            "diagnosis": diagnosis,
        },
        "hard_seam_errors": hard_seam_errors,
        "worst_cells_by_corner_error": worst_cells,
        "cell_diagnostics": cell_diagnostics,
        "correction_rules": {
            "flat_or_smooth_edges": "may_share_averaged_corner_vertices",
            "hard_step_edges": "must_split_corner_vertices_and_emit_split_riser",
            "fold_meet_halfway_edges": "must_split_corner_vertices_and_emit_two_sloped_fold_faces",
            "cliff_edges": "must_split_corner_vertices_and_emit_split_cliff",
            "chunk_boundary_edges": "emit_chunk_skirt",
        },
        "no_claims": NO_CLAIMS,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Hex Terrain Deformation Audit v0",
        "",
        "Diagnostic pass for why terrain shape changes between source heightfield, fold offsets, plot corner vertices, and seam policy meshes.",
        "",
        "| Site | Cells | Raw Corners | Emitted Vertices | Split Corners | Corner Caps | Max Fold | Max Neighbor Delta | Max Corner Error | Hard Seam Shared Errors | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = row["summary"]
        lines.append(
            f"| `{row['site_id']}` | {summary['cell_count']} | {summary['raw_corner_key_count']} | {summary['emitted_corner_vertex_count']} | {summary['split_raw_corner_count']} | {summary['corner_seam_cap_count']} | {summary['max_abs_fold_offset']} | {summary['max_neighbor_delta']} | {summary['max_corner_center_error']} | {summary['hard_seam_edges_with_shared_vertices']} | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Correction Applied",
            "",
            "Corner vertices are now seam-aware. Continuous flat/smooth terrain may average shared corner vertices. Hard steps and cliffs split duplicate vertices at the same XY before the seam mesh connects them.",
            "",
            "## What To Inspect",
            "",
            "- `max_abs_fold_offset`: whether folds are driving terrain too aggressively.",
            "- `max_neighbor_delta`: whether adjacent cells contain cliff-scale height jumps.",
            "- `max_corner_center_error`: whether shared/smooth corner averaging is visibly deforming cell surfaces.",
            "- `hard_seam_edges_with_shared_vertices`: must remain `0`; otherwise hard seams are still sagging through shared vertices.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "hex_terrain_deformation_audit_v0",
        "created_at_utc": now_iso(),
        "audit_count": len(rows),
        "audits": rows,
        "rules": {
            "diagnostic_only": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "hard_seams_must_not_share_corner_vertices": True,
            "split_corners_emit_corner_caps": True,
            "fold_offsets_reported": True,
            "corner_center_errors_reported": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
        },
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for source_path in sorted(SOURCE_DIR.glob("*_assembly.json")):
        site_id = source_path.name.removesuffix("_assembly.json")
        graph_path = GRAPH_DIR / f"{site_id}_plot_vertex_graph.json"
        if not graph_path.exists():
            fail(f"missing graph for {source_path.relative_to(ROOT)}: {graph_path.relative_to(ROOT)}")
        audit = audit_pair(source_path, graph_path)
        out = AUDIT_DIR / f"{site_id}_deformation_audit.json"
        out.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "site_id": audit["site_id"],
                "graph_id": audit["graph_id"],
                "summary": audit["summary"],
                "output_path": str(out.relative_to(ROOT)),
            }
        )
    if not rows:
        fail(f"no terrain assemblies found in {SOURCE_DIR.relative_to(ROOT)}")
    write_report(rows)
    write_receipt(rows)
    print(f"wrote {len(rows)} deformation audits")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
