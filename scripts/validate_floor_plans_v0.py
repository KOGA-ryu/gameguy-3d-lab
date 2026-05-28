#!/usr/bin/env python3
"""Validate floor_plan_v0 files against compiled Asset Mill assets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "data" / "architecture" / "floor_plans"
ASSET_INDEX_PATH = ROOT / "goal" / "architecture" / "asset_mill_v0" / "asset_mill_compiled_index_v0.json"
REPORT_PATH = ROOT / "goal" / "architecture" / "floor_plans_v0" / "floor_plan_catalog_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "floor_plans_v0.receipt.json"

EDGE_SIDES = {"north", "south", "east", "west"}
BOUNDARY_TYPES = {"wall", "open", "railing", "low_wall", "void_edge"}
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
        fail(f"{path.relative_to(ROOT)} must contain JSON object")
    return data


def load_asset_ids() -> set[str]:
    index = load_json(ASSET_INDEX_PATH)
    return {asset["asset_id"] for asset in index.get("assets", [])}


def positive(value: Any, context: str) -> None:
    if not isinstance(value, (int, float)) or value <= 0:
        fail(f"{context} must be positive number")


def edge_length(plot: dict[str, Any], side: str) -> float:
    size = plot["size"]
    if side in {"north", "south"}:
        return float(size["width"])
    return float(size["depth"])


def validate_asset_ref(asset_id: str, asset_ids: set[str], context: str) -> None:
    if asset_id not in asset_ids:
        fail(f"{context} references unknown asset `{asset_id}`")


def validate_plan(path: Path, asset_ids: set[str]) -> dict[str, Any]:
    plan = load_json(path)
    if plan.get("schema") != "floor_plan_v0":
        fail(f"{path.relative_to(ROOT)} schema must be floor_plan_v0")
    if plan.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    plots = plan.get("plots")
    if not isinstance(plots, list) or not plots:
        fail(f"{plan.get('plan_id')} requires non-empty plots list")

    plot_ids: set[str] = set()
    opening_count = 0
    feature_count = 0
    edge_count = 0

    for plot in plots:
        plot_id = plot.get("plot_id")
        if not isinstance(plot_id, str):
            fail(f"{plan.get('plan_id')} plot missing plot_id")
        if plot_id in plot_ids:
            fail(f"{plan.get('plan_id')} duplicate plot_id `{plot_id}`")
        plot_ids.add(plot_id)

        size = plot.get("size", {})
        positive(size.get("width"), f"{plot_id}.size.width")
        positive(size.get("depth"), f"{plot_id}.size.depth")
        positive(size.get("height"), f"{plot_id}.size.height")

        floor = plot.get("floor", {})
        validate_asset_ref(floor.get("asset_ref"), asset_ids, f"{plot_id}.floor")

        seen_sides: set[str] = set()
        edges = plot.get("edges")
        if not isinstance(edges, list):
            fail(f"{plot_id} requires edges list")
        for edge in edges:
            side = edge.get("side")
            boundary = edge.get("boundary")
            if side not in EDGE_SIDES:
                fail(f"{plot_id} invalid edge side `{side}`")
            if side in seen_sides:
                fail(f"{plot_id} duplicate edge side `{side}`")
            seen_sides.add(side)
            if boundary not in BOUNDARY_TYPES:
                fail(f"{plot_id}.{side} invalid boundary `{boundary}`")
            if boundary != "open" and "asset_ref" in edge:
                validate_asset_ref(edge["asset_ref"], asset_ids, f"{plot_id}.{side}")
            for opening in edge.get("openings", []):
                width = opening.get("width")
                positive(width, f"{plot_id}.{side}.{opening.get('opening_id')}.width")
                if float(width) >= edge_length(plot, side):
                    fail(f"{plot_id}.{side}.{opening.get('opening_id')} opening width does not fit edge")
                if "height" in opening:
                    positive(opening["height"], f"{plot_id}.{side}.{opening.get('opening_id')}.height")
                opening_count += 1
            edge_count += 1

        for feature in plot.get("features", []):
            validate_asset_ref(feature.get("asset_ref"), asset_ids, f"{plot_id}.{feature.get('feature_id')}")
            feature_count += 1

    for connection in plan.get("connections", []):
        if connection.get("from_plot") not in plot_ids:
            fail(f"{plan.get('plan_id')} connection from_plot unknown")
        if connection.get("to_plot") not in plot_ids:
            fail(f"{plan.get('plan_id')} connection to_plot unknown")

    return {
        "plan_id": plan["plan_id"],
        "path": str(path.relative_to(ROOT)),
        "plot_count": len(plots),
        "edge_count": edge_count,
        "opening_count": opening_count,
        "feature_count": feature_count,
        "summary": plan.get("summary", ""),
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Floor Plans v0 Catalog",
        "",
        "Four machine-readable floor plans for the next plot-to-solid compiler pass.",
        "",
        "| Plan | Plots | Edges | Openings | Features | Purpose |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['plan_id']}` | {row['plot_count']} | {row['edge_count']} | {row['opening_count']} | {row['feature_count']} | {row['summary']} |"
        )
    lines.extend(
        [
            "",
            "## Next Compiler Use",
            "",
            "A `plot_to_solid_assignment_v0` compiler can now read these plots, split walls around openings, scale floor slabs to plot size, place wall segments on edges, and instantiate posts, rails, stairs, pillars, and platforms from compiled Asset Mill solids.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "floor_plans_v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_count": len(rows),
        "plans": rows,
        "asset_index_checked": str(ASSET_INDEX_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "rules": {
            "asset_refs_validated": True,
            "dimensions_positive": True,
            "openings_fit_edges": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True
        },
        "recommended_next_goal": "Build plot_to_solid_assignment_v0 to turn these floor plans into placed building assemblies."
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    asset_ids = load_asset_ids()
    paths = sorted(PLAN_DIR.glob("*.json"))
    if not paths:
        fail(f"no floor plan json files found in {PLAN_DIR.relative_to(ROOT)}")
    rows = [validate_plan(path, asset_ids) for path in paths]
    write_report(rows)
    write_receipt(rows)
    print(f"validated {len(rows)} floor plans")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
