#!/usr/bin/env python3
"""Validate accessory asset taxonomy source data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = REPO_ROOT / "data/asset_taxonomy/accessories_v0/accessory_asset_taxonomy_v0.json"
TOOL_DICTIONARY_PATH = REPO_ROOT / "data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - CLI defensive detail
        raise SystemExit(f"FAIL could not parse {path}: {exc}") from exc


def fail(message: str) -> None:
    print(f"FAIL accessory asset taxonomy validation: {message}", file=sys.stderr)
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


def validate_known_terms(item_id: str, field: str, values: list[Any], known_values: set[str]) -> None:
    if not all(isinstance(value, str) and value for value in values):
        fail(f"{item_id}.{field} must contain non-empty strings")
    unknown_values = sorted(set(values) - known_values)
    if unknown_values:
        fail(f"{item_id}.{field} unknown: {unknown_values}")


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

    if bundle.get("schema") != "accessory_asset_taxonomy_v0":
        fail("schema must be accessory_asset_taxonomy_v0")

    known_geometry_terms = geometry_terms()
    known_tool_ids = {tool["tool_id"] for tool in tool_dictionary.get("tools", [])}

    status_tiers = bundle.get("accessory_status_tiers")
    if not isinstance(status_tiers, list) or not status_tiers:
        fail("accessory_status_tiers must be a non-empty list")
    status_ids: set[str] = set()
    for status in status_tiers:
        if not isinstance(status, dict):
            fail("each accessory status tier must be an object")
        status_id = require_nonempty_string(status, "<status>", "status_tier_id")
        if status_id in status_ids:
            fail(f"duplicate status_tier_id {status_id}")
        status_ids.add(status_id)
        for field in ("plain_name", "social_read"):
            require_nonempty_string(status, status_id, field)
        for field in ("material_rules", "silhouette_rules", "starter_accessories"):
            require_nonempty_list(status, status_id, field)

    styles = bundle.get("accessory_styles")
    if not isinstance(styles, list) or not styles:
        fail("accessory_styles must be a non-empty list")
    style_ids: set[str] = set()
    for style in styles:
        if not isinstance(style, dict):
            fail("each accessory style must be an object")
        style_id = require_nonempty_string(style, "<style>", "style_id")
        if style_id in style_ids:
            fail(f"duplicate style_id {style_id}")
        style_ids.add(style_id)
        require_nonempty_string(style, style_id, "plain_name")
        for field in ("visual_rules", "geometry_terms", "blender_tool_ids", "drawing_ui_tags"):
            require_nonempty_list(style, style_id, field)
        validate_known_terms(style_id, "geometry_terms", style["geometry_terms"], known_geometry_terms)
        validate_known_terms(style_id, "blender_tool_ids", style["blender_tool_ids"], known_tool_ids)

    families = bundle.get("accessory_families")
    if not isinstance(families, list) or not families:
        fail("accessory_families must be a non-empty list")
    family_ids: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            fail("each accessory family must be an object")
        family_id = require_nonempty_string(family, "<family>", "family_id")
        if family_id in family_ids:
            fail(f"duplicate family_id {family_id}")
        family_ids.add(family_id)
        for field in ("plain_name", "core_function"):
            require_nonempty_string(family, family_id, field)
        for field in ("starter_accessories", "drawing_ui_tags"):
            require_nonempty_list(family, family_id, field)

    accessories = bundle.get("accessory_items")
    if not isinstance(accessories, list) or not accessories:
        fail("accessory_items must be a non-empty list")
    accessory_ids: set[str] = set()
    for accessory in accessories:
        if not isinstance(accessory, dict):
            fail("each accessory item must be an object")
        accessory_id = require_nonempty_string(accessory, "<accessory>", "accessory_id")
        if accessory_id in accessory_ids:
            fail(f"duplicate accessory_id {accessory_id}")
        accessory_ids.add(accessory_id)

        family_id = require_nonempty_string(accessory, accessory_id, "family_id")
        if family_id not in family_ids:
            fail(f"{accessory_id}.family_id unknown: {family_id}")

        for field in ("plain_name", "attachment_mechanics"):
            require_nonempty_string(accessory, accessory_id, field)
        for field in (
            "status_tier_ids",
            "style_ids",
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
            require_nonempty_list(accessory, accessory_id, field)

        validate_known_terms(accessory_id, "status_tier_ids", accessory["status_tier_ids"], status_ids)
        validate_known_terms(accessory_id, "style_ids", accessory["style_ids"], style_ids)
        validate_known_terms(accessory_id, "geometry_terms", accessory["geometry_terms"], known_geometry_terms)
        validate_known_terms(accessory_id, "blender_tool_ids", accessory["blender_tool_ids"], known_tool_ids)
        validate_sources(accessory_id, accessory["source_support"])
        validate_anatomy(accessory_id, accessory["anatomy_parts"])
        validate_lore_hooks(accessory_id, accessory["lore_book_hooks"])

    missing_starters = sorted(
        starter
        for collection in (status_tiers, families)
        for item in collection
        for starter in item["starter_accessories"]
        if starter not in accessory_ids
    )
    if missing_starters:
        fail(f"starter_accessories unknown: {missing_starters}")

    print(
        "PASS accessory asset taxonomy validation: "
        f"status_tiers={len(status_tiers)} styles={len(styles)} families={len(families)} "
        f"accessories={len(accessories)} geometry_terms={len(known_geometry_terms)} tools={len(known_tool_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
