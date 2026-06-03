#!/usr/bin/env python3
"""Validate topology_dictionary_v0 and topology site recipes."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_ROOT = ROOT / "topology_dictionary"
SCHEMA_PATH = TOPOLOGY_ROOT / "schemas" / "topology_term.schema.json"
TERMS_PATH = TOPOLOGY_ROOT / "terms" / "topology_terms_v0.json"
SITE_DIR = ROOT / "data" / "architecture" / "topology_sites"
ASSEMBLY_DIR = ROOT / "goal" / "architecture" / "building_assemblies_v0" / "assemblies"
SOLID_DIR = ROOT / "goal" / "architecture" / "asset_mill_v0" / "solids"
REPORT_PATH = TOPOLOGY_ROOT / "topology_dictionary_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "topology_dictionary_v0.receipt.json"

TERM_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
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


def load_terms() -> dict[str, dict[str, Any]]:
    schema = load_json(SCHEMA_PATH)
    allowed_categories = set(schema["allowed_categories"])
    required_fields = schema["required_fields"]
    bundle = load_json(TERMS_PATH)
    terms = bundle.get("terms")
    if not isinstance(terms, list) or not terms:
        fail(f"{TERMS_PATH.relative_to(ROOT)} requires non-empty terms list")
    if bundle.get("no_claims") != NO_CLAIMS:
        fail(f"{TERMS_PATH.relative_to(ROOT)} no_claims must exactly match required false claims")

    result: dict[str, dict[str, Any]] = {}
    for term in terms:
        if not isinstance(term, dict):
            fail("topology term entries must be objects")
        for field in required_fields:
            if field not in term:
                fail(f"topology term missing required field `{field}`")
        term_id = term["term_id"]
        category = term["category"]
        if not isinstance(term_id, str) or not TERM_ID_RE.match(term_id):
            fail(f"invalid topology term_id `{term_id}`")
        if category not in allowed_categories:
            fail(f"{term_id} has unsupported category `{category}`")
        if term_id in result:
            fail(f"duplicate topology term `{term_id}`")
        for list_field in ("combat_affordances", "geometry_requirements", "possible_geomorph_processes", "validation"):
            if not isinstance(term.get(list_field), list) or not term[list_field]:
                fail(f"{term_id} requires non-empty `{list_field}`")
        result[term_id] = term
    return result


def load_available_ids(directory: Path) -> set[str]:
    return {path.stem for path in directory.glob("*.json")}


def validate_site(path: Path, terms: dict[str, dict[str, Any]], assemblies: set[str], solids: set[str]) -> dict[str, Any]:
    site = load_json(path)
    if site.get("schema") != "topology_site_recipe_v0":
        fail(f"{path.relative_to(ROOT)} schema must be topology_site_recipe_v0")
    if site.get("no_claims") != NO_CLAIMS:
        fail(f"{path.relative_to(ROOT)} no_claims must exactly match required false claims")

    site_id = site.get("site_id")
    if not isinstance(site_id, str) or not TERM_ID_RE.match(site_id):
        fail(f"{path.relative_to(ROOT)} requires valid site_id")

    for term_id in site.get("topology_terms", []):
        if term_id not in terms:
            fail(f"{site_id} references unknown topology term `{term_id}`")

    terrain_count = 0
    for terrain in site.get("terrain_primitives", []):
        terrain_count += 1
        topology_type = terrain.get("topology_type")
        if topology_type not in terms:
            fail(f"{site_id} terrain references unknown topology_type `{topology_type}`")
        size = terrain.get("size")
        if not isinstance(size, list) or len(size) != 3 or any(float(v) <= 0 for v in size):
            fail(f"{site_id}.{terrain.get('terrain_id')} requires positive size[3]")

    placement = site.get("building_placement", {})
    source_assembly = placement.get("source_assembly_id")
    if source_assembly not in assemblies:
        fail(f"{site_id} references missing source_assembly_id `{source_assembly}`")
    if placement.get("site_type") not in terms:
        fail(f"{site_id} references unknown site_type `{placement.get('site_type')}`")

    foundation = site.get("foundation_adapter", {})
    adapter_type = foundation.get("adapter_type")
    if adapter_type not in terms:
        fail(f"{site_id} references unknown adapter_type `{adapter_type}`")
    foundation_count = 0
    for inst in foundation.get("asset_instances", []):
        foundation_count += 1
        if inst.get("asset_ref") not in solids:
            fail(f"{site_id} foundation references missing asset_ref `{inst.get('asset_ref')}`")

    route_count = len(site.get("routes", []))
    affordance_count = 0
    for fact in site.get("affordance_facts", []):
        affordance_count += 1
        affordance = fact.get("affordance")
        if affordance not in terms:
            fail(f"{site_id} affordance fact references unknown term `{affordance}`")

    if terrain_count == 0 or route_count == 0 or affordance_count == 0:
        fail(f"{site_id} requires terrain, routes, and affordance facts")

    return {
        "site_id": site_id,
        "source_path": str(path.relative_to(ROOT)),
        "terrain_count": terrain_count,
        "foundation_count": foundation_count,
        "route_count": route_count,
        "affordance_count": affordance_count,
    }


def write_report(terms: dict[str, dict[str, Any]], site_rows: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for term in terms.values():
        counts[term["category"]] = counts.get(term["category"], 0) + 1

    lines = [
        "# Topology Dictionary v0",
        "",
        "Terrain/topology vocabulary that connects tactical affordance requirements to visible terrain shape contracts.",
        "",
        "```text",
        "AI affordance graph -> topology requirements -> terrain/site recipes -> building placement -> Blender proof",
        "```",
        "",
        "## Term Counts",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    for category in sorted(counts):
        lines.append(f"| `{category}` | {counts[category]} |")
    lines.extend(["", f"Total terms: `{len(terms)}`", "", "## Site Recipes", "", "| Site | Terrain | Foundation | Routes | Affordances |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in site_rows:
        lines.append(
            f"| `{row['site_id']}` | {row['terrain_count']} | {row['foundation_count']} | {row['route_count']} | {row['affordance_count']} |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "Topology is not decoration. Every site recipe must emit traversal, visibility, or combat affordance facts that later systems can consume.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(terms: dict[str, dict[str, Any]], site_rows: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "topology_dictionary_v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "term_count": len(terms),
        "site_recipe_count": len(site_rows),
        "site_recipes": site_rows,
        "rules": {
            "site_recipes_reject_unknown_topology_terms": True,
            "source_building_assemblies_must_exist": True,
            "foundation_assets_must_exist": True,
            "terrain_primitives_emit_affordances": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True
        },
        "recommended_next_goal": "Compile cliff_ledge_tollhouse_site_v0 into topology_site_assembly_v0 and render a Blender proof scene.",
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    terms = load_terms()
    assemblies = load_available_ids(ASSEMBLY_DIR)
    solids = load_available_ids(SOLID_DIR)
    if not assemblies:
        fail("no building assemblies found; run compile_floor_plans_to_assemblies_v0.py first")
    if not solids:
        fail("no Asset Mill solids found; run asset_pump_v0.py with simple_solids_v0.json first")

    site_rows = [validate_site(path, terms, assemblies, solids) for path in sorted(SITE_DIR.glob("*.json"))]
    if not site_rows:
        fail(f"no topology site recipes found in {SITE_DIR.relative_to(ROOT)}")

    write_report(terms, site_rows)
    write_receipt(terms, site_rows)
    print(f"validated {len(terms)} topology dictionary terms")
    print(f"validated {len(site_rows)} topology site recipes")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
