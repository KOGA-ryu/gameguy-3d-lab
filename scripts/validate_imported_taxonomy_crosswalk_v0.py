#!/usr/bin/env python3
"""Validate imported asset taxonomy shape crosswalk source data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CROSSWALK_PATH = REPO_ROOT / "data/asset_taxonomy/normalized_domains_v0/shape_type_crosswalk_v0.json"
MANIFEST_PATH = REPO_ROOT / "data/asset_taxonomy/imported_taxonomy_manifest_v0.json"
TOOL_DICTIONARY_PATH = REPO_ROOT / "data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json"

PROMOTION_STATUS = {"candidate", "needs_source_schema", "needs_tool_card", "defer"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive CLI detail
        raise SystemExit(f"FAIL could not parse {path}: {exc}") from exc


def geometry_terms() -> set[str]:
    terms: set[str] = set()
    for folder in (
        "geometry_dictionary/profiles",
        "geometry_dictionary/operations",
        "geometry_dictionary/connectors",
        "geometry_dictionary/measurements",
        "geometry_dictionary/semantic",
    ):
        for path in (REPO_ROOT / folder).glob("*.json"):
            terms.add(path.stem)
    return terms


def fail(message: str) -> None:
    print(f"FAIL imported taxonomy crosswalk validation: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_nonempty_list(entry: dict[str, Any], field: str) -> list[Any]:
    value = entry.get(field)
    if not isinstance(value, list) or not value:
        fail(f"{entry.get('crosswalk_id', '<unknown>')}.{field} must be a non-empty list")
    return value


def main() -> int:
    crosswalk = load_json(CROSSWALK_PATH)
    manifest = load_json(MANIFEST_PATH)
    tool_dictionary = load_json(TOOL_DICTIONARY_PATH)

    if crosswalk.get("schema") != "imported_shape_type_crosswalk_v0":
        fail("schema must be imported_shape_type_crosswalk_v0")

    if crosswalk.get("source_manifest") != "data/asset_taxonomy/imported_taxonomy_manifest_v0.json":
        fail("source_manifest must point to imported taxonomy manifest")

    known_sources = {seed["seed_id"] for seed in manifest.get("seeds", [])}
    known_geometry_terms = geometry_terms()
    known_tool_ids = {tool["tool_id"] for tool in tool_dictionary.get("tools", [])}
    entries = crosswalk.get("entries")
    if not isinstance(entries, list) or not entries:
        fail("entries must be a non-empty list")

    seen_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            fail("each entry must be an object")

        crosswalk_id = entry.get("crosswalk_id")
        if not isinstance(crosswalk_id, str) or not crosswalk_id:
            fail("crosswalk_id must be a non-empty string")
        if crosswalk_id in seen_ids:
            fail(f"duplicate crosswalk_id {crosswalk_id}")
        seen_ids.add(crosswalk_id)

        for field in ("imported_terms", "source_domains", "geometry_terms", "blender_tool_ids", "tool_card_refs", "source_fields_needed", "asset_families", "drafting_tags"):
            require_nonempty_list(entry, field)

        unknown_sources = sorted(set(entry["source_domains"]) - known_sources)
        if unknown_sources:
            fail(f"{crosswalk_id}.source_domains unknown: {unknown_sources}")

        unknown_geometry = sorted(set(entry["geometry_terms"]) - known_geometry_terms)
        if unknown_geometry:
            fail(f"{crosswalk_id}.geometry_terms unknown: {unknown_geometry}")

        unknown_tools = sorted(set(entry["blender_tool_ids"]) - known_tool_ids)
        if unknown_tools:
            fail(f"{crosswalk_id}.blender_tool_ids unknown: {unknown_tools}")

        missing_docs = [doc for doc in entry["tool_card_refs"] if not (REPO_ROOT / doc).exists()]
        if missing_docs:
            fail(f"{crosswalk_id}.tool_card_refs missing: {missing_docs}")

        status = entry.get("promotion_status")
        if status not in PROMOTION_STATUS:
            fail(f"{crosswalk_id}.promotion_status must be one of {sorted(PROMOTION_STATUS)}")

        if not isinstance(entry.get("normalized_intent"), str) or not entry["normalized_intent"]:
            fail(f"{crosswalk_id}.normalized_intent must be a non-empty string")

    print(
        "PASS imported taxonomy crosswalk validation: "
        f"entries={len(entries)} sources={len(known_sources)} geometry_terms={len(known_geometry_terms)} tools={len(known_tool_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

