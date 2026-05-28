#!/usr/bin/env python3
"""Compile topology_site_recipe_v0 into terrain/building site assembly JSON."""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "data" / "architecture" / "topology_sites"
ASSEMBLY_DIR = ROOT / "goal" / "architecture" / "building_assemblies_v0" / "assemblies"
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
OUT_DIR = ROOT / "goal" / "architecture" / "topology_sites_v0"
COMPILED_DIR = OUT_DIR / "sites"
REPORT_PATH = OUT_DIR / "topology_site_catalog_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "topology_sites_v0.receipt.json"

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


def rotate_xy(x: float, y: float, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    return (x * c - y * s, x * s + y * c)


def solid_dimensions(solids: dict[str, dict[str, Any]], asset_ref: str) -> dict[str, float]:
    if asset_ref not in solids:
        fail(f"unknown compiled solid asset_ref `{asset_ref}`")
    return solids[asset_ref]["semantic_outputs"]["bounds_role_summary"]["dimensions"]


def scale_for_target(solids: dict[str, dict[str, Any]], asset_ref: str, target: tuple[float, float, float]) -> list[float]:
    dims = solid_dimensions(solids, asset_ref)
    base = (float(dims["width_x"]), float(dims["depth_y"]), float(dims["height_z"]))
    return [round(target[i] / base[i], 6) for i in range(3)]


def transform_instance(inst: dict[str, Any], origin: list[float], rotation_z: float, elevation: float) -> dict[str, Any]:
    lx, ly, lz = [float(v) for v in inst["translation"]]
    rx, ry = rotate_xy(lx, ly, rotation_z)
    rotation = list(inst.get("rotation_degrees", [0.0, 0.0, 0.0]))
    rotation[2] = round(float(rotation[2]) + rotation_z, 6)
    transformed = dict(inst)
    transformed["instance_id"] = f"building_{inst['instance_id']}"
    transformed["translation"] = [
        round(float(origin[0]) + rx, 6),
        round(float(origin[1]) + ry, 6),
        round(elevation + lz, 6),
    ]
    transformed["rotation_degrees"] = rotation
    transformed["topology_source"] = "building_placement"
    return transformed


def compile_foundation(site: dict[str, Any], solids: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []
    for inst in site["foundation_adapter"]["asset_instances"]:
        target = tuple(float(v) for v in inst["target_dimensions"])
        compiled.append(
            {
                "instance_id": inst["instance_id"],
                "asset_ref": inst["asset_ref"],
                "role": inst["role"],
                "translation": [round(float(v), 6) for v in inst["translation"]],
                "rotation_degrees": inst.get("rotation_degrees", [0.0, 0.0, 0.0]),
                "scale": scale_for_target(solids, inst["asset_ref"], target),
                "semantic_tags": inst.get("semantic_tags", []),
                "target_dimensions": {
                    "width_x": round(target[0], 6),
                    "depth_y": round(target[1], 6),
                    "height_z": round(target[2], 6),
                },
                "topology_source": "foundation_adapter",
            }
        )
    return compiled


def compile_site(path: Path, solids: dict[str, dict[str, Any]]) -> dict[str, Any]:
    site = load_json(path)
    if site.get("schema") != "topology_site_recipe_v0":
        fail(f"{path.relative_to(ROOT)} schema must be topology_site_recipe_v0")
    if site.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    placement = site["building_placement"]
    assembly_path = ASSEMBLY_DIR / f"{placement['source_assembly_id']}.json"
    if not assembly_path.exists():
        fail(f"missing source assembly `{placement['source_assembly_id']}`")
    building = load_json(assembly_path)
    origin = [float(v) for v in placement["origin"]]
    rotation_z = float(placement.get("rotation_degrees", [0.0, 0.0, 0.0])[2])
    elevation = float(placement["elevation"])

    building_instances = [transform_instance(inst, origin, rotation_z, elevation) for inst in building["instances"]]
    foundation_instances = compile_foundation(site, solids)

    return {
        "schema": "topology_site_assembly_v0",
        "site_id": site["site_id"],
        "source_recipe": str(path.relative_to(ROOT)),
        "summary": site.get("summary", ""),
        "units": site["units"],
        "topology_terms": site["topology_terms"],
        "source_building_assembly": placement["source_assembly_id"],
        "building_placement": placement,
        "terrain_primitive_count": len(site["terrain_primitives"]),
        "foundation_instance_count": len(foundation_instances),
        "building_instance_count": len(building_instances),
        "route_count": len(site["routes"]),
        "affordance_fact_count": len(site["affordance_facts"]),
        "terrain_primitives": site["terrain_primitives"],
        "foundation_instances": foundation_instances,
        "building_instances": building_instances,
        "routes": site["routes"],
        "affordance_facts": site["affordance_facts"],
        "no_claims": NO_CLAIMS,
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Topology Sites v0",
        "",
        "Compiled terrain/site assemblies connecting topology recipes to existing building assemblies.",
        "",
        "```text",
        "topology_site_recipe_v0 -> terrain primitives + foundation adapter + placed building instances + affordance facts",
        "```",
        "",
        "| Site | Terrain | Foundation | Building Instances | Routes | Affordances | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['site_id']}` | {row['terrain_primitive_count']} | {row['foundation_instance_count']} | {row['building_instance_count']} | {row['route_count']} | {row['affordance_fact_count']} | `{row['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "- Terrain topology can demand building placement through a site contract.",
            "- A building assembly can be planted at a topology-derived elevation.",
            "- A foundation adapter can mediate between terrain and building footprint.",
            "- The compiled site emits route and affordance facts for later AI graph integration.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "topology_sites_v0",
        "created_at_utc": now_iso(),
        "site_count": len(rows),
        "sites": rows,
        "rules": {
            "topology_drives_site_contract": True,
            "building_assembly_reused": True,
            "foundation_adapter_present": True,
            "affordance_facts_emitted": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True
        },
        "recommended_next_goal": "Render topology_site_assembly_v0 in Blender to prove terrain and building contact.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    solids = {path.stem: load_json(path) for path in sorted(SOLID_DIR.glob("*.json"))}
    if not solids:
        fail("no Asset Mill solids found; run compile_asset_mill_solids_v0.py first")

    rows: list[dict[str, Any]] = []
    for path in sorted(SITE_DIR.glob("*.json")):
        compiled = compile_site(path, solids)
        out = COMPILED_DIR / f"{compiled['site_id']}_assembly.json"
        out.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "site_id": compiled["site_id"],
                "terrain_primitive_count": compiled["terrain_primitive_count"],
                "foundation_instance_count": compiled["foundation_instance_count"],
                "building_instance_count": compiled["building_instance_count"],
                "route_count": compiled["route_count"],
                "affordance_fact_count": compiled["affordance_fact_count"],
                "output_path": str(out.relative_to(ROOT)),
            }
        )

    write_report(rows)
    write_receipt(rows)
    print(f"compiled {len(rows)} topology site assemblies")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
