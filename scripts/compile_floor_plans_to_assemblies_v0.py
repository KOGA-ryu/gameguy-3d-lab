#!/usr/bin/env python3
"""Compile floor_plan_v0 files into placed building assembly JSON.

This connects floor plans to compiled Asset Mill solids:

floor plan plots -> floors, walls, rails, features -> placed asset instances

No Blender, mesh, or render output is created here. This is the data bridge the
Blender realization script can consume.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "data" / "architecture" / "floor_plans"
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
OUT_DIR = ROOT / "goal" / "architecture" / "building_assemblies_v0"
ASSEMBLY_DIR = OUT_DIR / "assemblies"
REPORT_PATH = OUT_DIR / "building_assembly_catalog_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "building_assemblies_v0.receipt.json"


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


def ensure_dirs() -> None:
    ASSEMBLY_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_solids() -> dict[str, dict[str, Any]]:
    solids = {path.stem: load_json(path) for path in sorted(SOLID_DIR.glob("*.json"))}
    if not solids:
        fail(f"no compiled solids found in {SOLID_DIR.relative_to(ROOT)}")
    return solids


def solid_dimensions(solids: dict[str, dict[str, Any]], asset_ref: str) -> dict[str, float]:
    if asset_ref not in solids:
        fail(f"unknown compiled solid asset_ref `{asset_ref}`")
    return solids[asset_ref]["semantic_outputs"]["bounds_role_summary"]["dimensions"]


def scale_for_target(solids: dict[str, dict[str, Any]], asset_ref: str, target: tuple[float, float, float]) -> list[float]:
    dims = solid_dimensions(solids, asset_ref)
    base = (float(dims["width_x"]), float(dims["depth_y"]), float(dims["height_z"]))
    return [round(target[i] / base[i], 6) for i in range(3)]


def edge_axis(side: str) -> str:
    return "x" if side in {"north", "south"} else "y"


def edge_length(plot: dict[str, Any], side: str) -> float:
    size = plot["size"]
    return float(size["width"] if edge_axis(side) == "x" else size["depth"])


def edge_center(plot: dict[str, Any], side: str, along_offset: float, z: float) -> tuple[float, float, float]:
    ox, oy, _ = [float(v) for v in plot["origin"]]
    width = float(plot["size"]["width"])
    depth = float(plot["size"]["depth"])
    if side == "north":
        return (ox + along_offset, oy + depth * 0.5, z)
    if side == "south":
        return (ox + along_offset, oy - depth * 0.5, z)
    if side == "east":
        return (ox + width * 0.5, oy + along_offset, z)
    if side == "west":
        return (ox - width * 0.5, oy + along_offset, z)
    fail(f"unknown edge side `{side}`")


def edge_rotation(side: str) -> list[float]:
    return [0.0, 0.0, 90.0] if side in {"east", "west"} else [0.0, 0.0, 0.0]


def wall_segments(length: float, openings: list[dict[str, Any]]) -> tuple[list[tuple[float, float]], list[dict[str, Any]]]:
    intervals = [(-length * 0.5, length * 0.5)]
    voids: list[dict[str, Any]] = []
    for opening in sorted(openings, key=lambda item: float(item.get("center_offset", 0.0))):
        width = float(opening["width"])
        center = float(opening.get("center_offset", 0.0))
        cut_min = center - width * 0.5
        cut_max = center + width * 0.5
        next_intervals: list[tuple[float, float]] = []
        for a, b in intervals:
            if cut_max <= a or cut_min >= b:
                next_intervals.append((a, b))
                continue
            if cut_min > a:
                next_intervals.append((a, cut_min))
            if cut_max < b:
                next_intervals.append((cut_max, b))
        intervals = next_intervals
        voids.append(
            {
                "opening_id": opening["opening_id"],
                "type": opening["type"],
                "center_offset": round(center, 6),
                "width": round(width, 6),
                "height": round(float(opening.get("height", 0.0)), 6) if "height" in opening else None,
                "range": [round(cut_min, 6), round(cut_max, 6)],
            }
        )
    return [(a, b) for a, b in intervals if b - a > 0.05], voids


def instance(
    *,
    instance_id: str,
    asset_ref: str,
    role: str,
    source_plot: str,
    translation: tuple[float, float, float],
    scale: list[float],
    rotation_degrees: list[float] | None = None,
    semantic_tags: list[str] | None = None,
    source_edge: str | None = None,
    source_feature: str | None = None,
    target_dimensions: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "instance_id": instance_id,
        "asset_ref": asset_ref,
        "role": role,
        "source_plot": source_plot,
        "translation": [round(v, 6) for v in translation],
        "rotation_degrees": rotation_degrees or [0.0, 0.0, 0.0],
        "scale": scale,
        "semantic_tags": semantic_tags or [],
    }
    if source_edge is not None:
        data["source_edge"] = source_edge
    if source_feature is not None:
        data["source_feature"] = source_feature
    if target_dimensions is not None:
        data["target_dimensions"] = {
            "width_x": round(target_dimensions[0], 6),
            "depth_y": round(target_dimensions[1], 6),
            "height_z": round(target_dimensions[2], 6),
        }
    return data


def compile_plot(plan: dict[str, Any], plot: dict[str, Any], solids: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    instances: list[dict[str, Any]] = []
    voids: list[dict[str, Any]] = []
    plot_id = plot["plot_id"]
    ox, oy, oz = [float(v) for v in plot["origin"]]
    width = float(plot["size"]["width"])
    depth = float(plot["size"]["depth"])
    height = float(plot["size"]["height"])

    floor = plot["floor"]
    floor_asset = floor["asset_ref"]
    floor_thickness = float(floor.get("thickness", 0.18))
    floor_target = (width, depth, floor_thickness)
    instances.append(
        instance(
            instance_id=f"{plot_id}_floor",
            asset_ref=floor_asset,
            role="floor",
            source_plot=plot_id,
            translation=(ox, oy, oz),
            scale=scale_for_target(solids, floor_asset, floor_target),
            semantic_tags=["walkable", "collision_proxy"],
            target_dimensions=floor_target,
        )
    )

    wall_base_z = oz + floor_thickness
    for edge in plot["edges"]:
        boundary = edge["boundary"]
        side = edge["side"]
        if boundary == "open":
            continue
        asset_ref = edge.get("asset_ref")
        if not asset_ref:
            continue
        length = edge_length(plot, side)
        segments, edge_voids = wall_segments(length, edge.get("openings", []))
        voids.extend(
            [
                {
                    **void,
                    "source_plot": plot_id,
                    "source_edge": side,
                    "world_center": list(edge_center(plot, side, float(void["center_offset"]), wall_base_z)),
                }
                for void in edge_voids
            ]
        )
        thickness = float(edge.get("thickness", 0.24 if boundary == "railing" else 0.28))
        edge_height = float(edge.get("height", 1.2 if boundary == "railing" else height))
        role = "railing" if boundary == "railing" else "wall"
        tags = ["barrier", "cover", "rail"] if boundary == "railing" else ["blocked", "cover", "line_of_sight_blocker", "collision_proxy"]
        for index, (a, b) in enumerate(segments):
            segment_length = b - a
            center_offset = (a + b) * 0.5
            target = (segment_length, thickness, edge_height)
            instances.append(
                instance(
                    instance_id=f"{plot_id}_{side}_{role}_seg_{index:02d}",
                    asset_ref=asset_ref,
                    role=role,
                    source_plot=plot_id,
                    source_edge=side,
                    translation=edge_center(plot, side, center_offset, wall_base_z),
                    rotation_degrees=edge_rotation(side),
                    scale=scale_for_target(solids, asset_ref, target),
                    semantic_tags=tags,
                    target_dimensions=target,
                )
            )

    for feature in plot.get("features", []):
        asset_ref = feature["asset_ref"]
        position = tuple(float(v) for v in feature["position"])
        role = feature["type"]
        dims = solid_dimensions(solids, asset_ref)
        target = (
            float(feature.get("width", dims["width_x"])),
            float(feature.get("depth", dims["depth_y"])),
            float(feature.get("height", dims["height_z"])),
        )
        facing = feature.get("facing")
        rotation = [0.0, 0.0, 0.0]
        if facing == "east":
            rotation = [0.0, 0.0, 90.0]
        elif facing == "south":
            rotation = [0.0, 0.0, 180.0]
        elif facing == "west":
            rotation = [0.0, 0.0, 270.0]
        instances.append(
            instance(
                instance_id=feature["feature_id"],
                asset_ref=asset_ref,
                role=role,
                source_plot=plot_id,
                source_feature=feature["feature_id"],
                translation=position,
                rotation_degrees=rotation,
                scale=scale_for_target(solids, asset_ref, target),
                semantic_tags=solids[asset_ref]["semantic_outputs"]["semantic_tags"],
                target_dimensions=target,
            )
        )

    return instances, voids


def compile_plan(path: Path, solids: dict[str, dict[str, Any]]) -> dict[str, Any]:
    plan = load_json(path)
    if plan.get("schema") != "floor_plan_v0":
        fail(f"{path.relative_to(ROOT)} schema must be floor_plan_v0")
    if plan.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    all_instances: list[dict[str, Any]] = []
    all_voids: list[dict[str, Any]] = []
    for plot in plan["plots"]:
        plot_instances, plot_voids = compile_plot(plan, plot, solids)
        all_instances.extend(plot_instances)
        all_voids.extend(plot_voids)

    return {
        "schema": "building_assembly_v0",
        "assembly_id": f"{plan['plan_id']}_assembly",
        "source_plan": str(path.relative_to(ROOT)),
        "plan_id": plan["plan_id"],
        "units": plan["units"],
        "summary": plan.get("summary", ""),
        "instance_count": len(all_instances),
        "void_count": len(all_voids),
        "instances": all_instances,
        "voids": all_voids,
        "connections": plan.get("connections", []),
        "no_claims": NO_CLAIMS,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Building Assemblies v0",
        "",
        "Compiled placement data connecting floor plans to measured Asset Mill solids.",
        "",
        "```text",
        "floor_plan_v0 -> floors/walls/rails/features -> placed asset instances -> Blender realization",
        "```",
        "",
        "| Assembly | Instances | Voids | Source Plan | Output |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['assembly_id']}` | {row['instance_count']} | {row['void_count']} | `{row['source_plan']}` | `{row['output_path']}` |")
    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "- Floor plan dimensions now drive asset scale.",
            "- Wall edges are split around doorway gaps.",
            "- Features instantiate compiled posts, stairs, pillars, and rails.",
            "- Output is reusable placement data, not a hand-modeled scene.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    receipt = {
        "receipt_type": "building_assemblies_v0",
        "created_at_utc": now_iso(),
        "assembly_count": len(rows),
        "assemblies": rows,
        "rules": {
            "floor_plan_drives_measurements": True,
            "asset_refs_from_compiled_asset_mill": True,
            "wall_edges_split_around_openings": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
        },
        "recommended_next_goal": "Use Blender to realize building_assembly_v0 JSON into a proof scene.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    solids = load_solids()
    rows: list[dict[str, Any]] = []
    for path in sorted(PLAN_DIR.glob("*.json")):
        assembly = compile_plan(path, solids)
        out = ASSEMBLY_DIR / f"{assembly['assembly_id']}.json"
        out.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "assembly_id": assembly["assembly_id"],
                "source_plan": assembly["source_plan"],
                "instance_count": assembly["instance_count"],
                "void_count": assembly["void_count"],
                "output_path": str(out.relative_to(ROOT)),
            }
        )
    write_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} building assemblies")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
