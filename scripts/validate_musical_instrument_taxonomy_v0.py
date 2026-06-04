#!/usr/bin/env python3
"""Validate musical instrument asset taxonomy source data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = (
    REPO_ROOT
    / "data/asset_taxonomy/musical_instruments_v0/musical_instrument_asset_taxonomy_v0.json"
)
TOOL_DICTIONARY_PATH = REPO_ROOT / "data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - CLI defensive detail
        raise SystemExit(f"FAIL could not parse {path}: {exc}") from exc


def fail(message: str) -> None:
    print(f"FAIL musical instrument taxonomy validation: {message}", file=sys.stderr)
    raise SystemExit(1)


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


def require_nonempty_string(item: dict[str, Any], item_id: str, field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        fail(f"{item_id}.{field} must be a non-empty string")
    return value


def require_nonempty_list(item: dict[str, Any], item_id: str, field: str) -> list[Any]:
    value = item.get(field)
    if not isinstance(value, list) or not value:
        fail(f"{item_id}.{field} must be a non-empty list")
    return value


def validate_sources(item_id: str, sources: list[Any]) -> None:
    for source in sources:
        if not isinstance(source, dict):
            fail(f"{item_id}.source_support entries must be objects")
        if not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
            fail(f"{item_id}.source_support.url must be https URL")
        for field in ("label", "support_summary"):
            if not isinstance(source.get(field), str) or not source[field]:
                fail(f"{item_id}.source_support.{field} must be non-empty")


def validate_anatomy(item_id: str, anatomy_parts: list[Any]) -> None:
    seen_parts: set[str] = set()
    for part in anatomy_parts:
        if not isinstance(part, dict):
            fail(f"{item_id}.anatomy_parts entries must be objects")
        part_id = part.get("part_id")
        if not isinstance(part_id, str) or not part_id:
            fail(f"{item_id}.anatomy_parts.part_id must be a non-empty string")
        if part_id in seen_parts:
            fail(f"{item_id}.anatomy_parts duplicate part_id {part_id}")
        seen_parts.add(part_id)
        for field in ("plain_name", "geometry_role"):
            if not isinstance(part.get(field), str) or not part[field]:
                fail(f"{item_id}.anatomy_parts.{part_id}.{field} must be non-empty")


def validate_lore_hooks(item_id: str, hooks: list[Any]) -> None:
    for hook in hooks:
        if not isinstance(hook, dict):
            fail(f"{item_id}.lore_book_hooks entries must be objects")
        for field in ("book_title", "player_reward", "detail_prompt"):
            if not isinstance(hook.get(field), str) or not hook[field]:
                fail(f"{item_id}.lore_book_hooks.{field} must be non-empty")


def main() -> int:
    bundle = load_json(TAXONOMY_PATH)
    tool_dictionary = load_json(TOOL_DICTIONARY_PATH)

    if bundle.get("schema") != "musical_instrument_asset_taxonomy_v0":
        fail("schema must be musical_instrument_asset_taxonomy_v0")

    known_geometry_terms = geometry_terms()
    known_tool_ids = {tool["tool_id"] for tool in tool_dictionary.get("tools", [])}

    families = bundle.get("instrument_families")
    if not isinstance(families, list) or not families:
        fail("instrument_families must be a non-empty list")

    family_ids: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            fail("each instrument family must be an object")
        family_id = require_nonempty_string(family, "<family>", "family_id")
        if family_id in family_ids:
            fail(f"duplicate family_id {family_id}")
        family_ids.add(family_id)
        for field in ("plain_name", "core_mechanics"):
            require_nonempty_string(family, family_id, field)
        for field in ("starter_instruments", "drawing_ui_tags"):
            require_nonempty_list(family, family_id, field)

    instruments = bundle.get("instruments")
    if not isinstance(instruments, list) or not instruments:
        fail("instruments must be a non-empty list")

    instrument_ids: set[str] = set()
    for instrument in instruments:
        if not isinstance(instrument, dict):
            fail("each instrument must be an object")
        instrument_id = require_nonempty_string(instrument, "<instrument>", "instrument_id")
        if instrument_id in instrument_ids:
            fail(f"duplicate instrument_id {instrument_id}")
        instrument_ids.add(instrument_id)

        family_id = require_nonempty_string(instrument, instrument_id, "family_id")
        if family_id not in family_ids:
            fail(f"{instrument_id}.family_id unknown: {family_id}")

        for field in ("plain_name", "sound_mechanics"):
            require_nonempty_string(instrument, instrument_id, field)

        for field in (
            "source_support",
            "game_use_roles",
            "anatomy_parts",
            "materials",
            "real_tools",
            "craft_sequence",
            "geometry_terms",
            "blender_tool_ids",
            "drawing_ui_tags",
            "source_fields_needed",
            "operator_checks",
            "lore_book_hooks",
            "deferred_details",
        ):
            require_nonempty_list(instrument, instrument_id, field)

        validate_sources(instrument_id, instrument["source_support"])
        validate_anatomy(instrument_id, instrument["anatomy_parts"])
        validate_lore_hooks(instrument_id, instrument["lore_book_hooks"])

        unknown_geometry = sorted(set(instrument["geometry_terms"]) - known_geometry_terms)
        if unknown_geometry:
            fail(f"{instrument_id}.geometry_terms unknown: {unknown_geometry}")

        unknown_tools = sorted(set(instrument["blender_tool_ids"]) - known_tool_ids)
        if unknown_tools:
            fail(f"{instrument_id}.blender_tool_ids unknown: {unknown_tools}")

    missing_starters = sorted(
        starter
        for family in families
        for starter in family["starter_instruments"]
        if starter not in instrument_ids
    )
    if missing_starters:
        fail(f"starter_instruments unknown: {missing_starters}")

    print(
        "PASS musical instrument taxonomy validation: "
        f"families={len(families)} instruments={len(instruments)} "
        f"geometry_terms={len(known_geometry_terms)} tools={len(known_tool_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
