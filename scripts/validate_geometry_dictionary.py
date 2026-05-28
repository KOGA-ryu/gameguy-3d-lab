#!/usr/bin/env python3
"""Validate geometry_dictionary_v0 and Asset Mill dictionary references."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DICTIONARY_ROOT = ROOT / "geometry_dictionary"
SCHEMA_PATH = DICTIONARY_ROOT / "schemas" / "geometry_term.schema.json"
ASSET_RECIPE_PATH = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json"
REPORT_PATH = DICTIONARY_ROOT / "geometry_dictionary_v0_report.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "geometry_dictionary_v0.receipt.json"

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


def dictionary_paths() -> list[Path]:
    return sorted(
        path
        for path in DICTIONARY_ROOT.rglob("*.json")
        if "/schemas/" not in str(path)
    )


def load_terms() -> dict[str, dict[str, Any]]:
    schema = load_json(SCHEMA_PATH)
    allowed_categories = set(schema["allowed_categories"])
    required_fields = schema["required_fields"]
    terms: dict[str, dict[str, Any]] = {}
    for path in dictionary_paths():
        term = load_json(path)
        rel = path.relative_to(ROOT)
        for field in required_fields:
            if field not in term:
                fail(f"{rel} missing required field `{field}`")
        term_id = term["term_id"]
        category = term["category"]
        if not isinstance(term_id, str) or not TERM_ID_RE.match(term_id):
            fail(f"{rel} has invalid term_id `{term_id}`")
        if category not in allowed_categories:
            fail(f"{rel} has unsupported category `{category}`")
        if term_id in terms:
            fail(f"duplicate term_id `{term_id}` in {rel}")
        if not isinstance(term.get("validation"), list) or not term["validation"]:
            fail(f"{rel} requires non-empty validation list")
        term["_path"] = str(rel)
        terms[term_id] = term
    return terms


def terms_by_category(terms: dict[str, dict[str, Any]], *categories: str) -> set[str]:
    wanted = set(categories)
    return {term_id for term_id, term in terms.items() if term["category"] in wanted}


def validate_asset_recipes(terms: dict[str, dict[str, Any]]) -> None:
    if not ASSET_RECIPE_PATH.exists():
        fail(f"missing asset recipe bundle: {ASSET_RECIPE_PATH.relative_to(ROOT)}")
    bundle = load_json(ASSET_RECIPE_PATH)
    assets = bundle.get("assets")
    if not isinstance(assets, list):
        fail("asset recipe bundle requires assets list")

    profile_terms = terms_by_category(terms, "profile_primitive")
    operation_terms = terms_by_category(terms, "mesh_operation", "composition_operation", "transform")
    semantic_terms = terms_by_category(terms, "semantic_geometry")
    connector_terms = terms_by_category(terms, "connector")

    asset_ids: set[str] = set()
    for asset in assets:
        asset_id = asset.get("asset_id")
        if not isinstance(asset_id, str):
            fail("asset missing string asset_id")
        if asset_id in asset_ids:
            fail(f"duplicate asset_id `{asset_id}`")
        asset_ids.add(asset_id)

        operation = asset.get("operation")
        if operation not in operation_terms:
            fail(f"{asset_id} uses unknown operation `{operation}`")

        for connector in asset.get("connectors", []):
            if connector not in connector_terms:
                fail(f"{asset_id} uses unknown connector `{connector}`")

        for tag in asset.get("semantic_tags", []):
            if tag not in semantic_terms:
                fail(f"{asset_id} uses unknown semantic tag `{tag}`")

        if operation == "extrude":
            validate_profile_ref(asset_id, asset.get("profile"), profile_terms)
        elif operation == "loft_sections":
            sections = asset.get("sections", [])
            if not isinstance(sections, list) or len(sections) < 2:
                fail(f"{asset_id} loft_sections requires at least two sections")
            for index, section in enumerate(sections):
                validate_profile_ref(f"{asset_id}.sections[{index}]", section.get("profile"), profile_terms)
        elif operation == "compound_asset":
            components = asset.get("components", [])
            if not isinstance(components, list) or not components:
                fail(f"{asset_id} compound_asset requires non-empty components")
            for component in components:
                ref = component.get("asset_ref")
                if ref not in asset_ids:
                    fail(f"{asset_id} references unknown or later asset_ref `{ref}`")


def validate_profile_ref(context: str, profile: Any, profile_terms: set[str]) -> None:
    if not isinstance(profile, dict):
        fail(f"{context} requires profile object")
    ptype = profile.get("type")
    if ptype not in profile_terms:
        fail(f"{context} uses unknown profile type `{ptype}`")
    params = profile.get("params")
    if not isinstance(params, dict):
        fail(f"{context} profile requires params object")


def write_report(terms: dict[str, dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for term in terms.values():
        counts[term["category"]] = counts.get(term["category"], 0) + 1

    lines = [
        "# Geometry Dictionary v0",
        "",
        "Machine-readable geometry vocabulary for profile primitives, measurements, operations, connectors, semantic geometry, and validation terms.",
        "",
        "The rule is strict: Asset Mill recipes may only use profile, operation, connector, and semantic terms that exist in this dictionary.",
        "",
        "## Counts",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    for category in sorted(counts):
        lines.append(f"| `{category}` | {counts[category]} |")

    lines.extend(
        [
            "",
            f"Total terms: `{len(terms)}`",
            "",
            "## Asset Mill Enforcement",
            "",
            f"- Checked recipe bundle: `{ASSET_RECIPE_PATH.relative_to(ROOT)}`",
            "- Validated profile primitive references.",
            "- Validated operation references.",
            "- Validated connector references.",
            "- Validated semantic geometry tags.",
            "",
            "## Purpose",
            "",
            "- Codex cannot invent geometry words inside recipes.",
            "- Blender scripts can look up each term and know expected params, outputs, and validation.",
            "- Validators can reject fake geometry before it reaches generation.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(terms: dict[str, dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "geometry_dictionary_v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "term_count": len(terms),
        "dictionary_root": str(DICTIONARY_ROOT.relative_to(ROOT)),
        "asset_recipe_checked": str(ASSET_RECIPE_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "rules": {
            "machine_readable": True,
            "asset_recipes_reject_unknown_profiles": True,
            "asset_recipes_reject_unknown_operations": True,
            "asset_recipes_reject_unknown_connectors": True,
            "asset_recipes_reject_unknown_semantic_tags": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_production_approval": True
        },
        "recommended_next_goal": "Make plot_to_solid_assignment_v0 reference geometry dictionary terms and compiled Asset Mill solids."
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    terms = load_terms()
    validate_asset_recipes(terms)
    write_report(terms)
    write_receipt(terms)
    print(f"validated {len(terms)} geometry dictionary terms")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
