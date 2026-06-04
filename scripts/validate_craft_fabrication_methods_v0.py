#!/usr/bin/env python3
"""Validate craft fabrication method source data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
METHODS_PATH = REPO_ROOT / "data/architecture/taxonomy/craft_methods/craft_fabrication_methods_v0.json"
TOOL_DICTIONARY_PATH = REPO_ROOT / "data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - CLI defensive detail
        raise SystemExit(f"FAIL could not parse {path}: {exc}") from exc


def fail(message: str) -> None:
    print(f"FAIL craft fabrication method validation: {message}", file=sys.stderr)
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


def require_nonempty_list(method: dict[str, Any], field: str) -> list[Any]:
    value = method.get(field)
    if not isinstance(value, list) or not value:
        fail(f"{method.get('method_id', '<unknown>')}.{field} must be a non-empty list")
    return value


def main() -> int:
    bundle = load_json(METHODS_PATH)
    tool_dictionary = load_json(TOOL_DICTIONARY_PATH)

    if bundle.get("schema") != "craft_fabrication_methods_v0":
        fail("schema must be craft_fabrication_methods_v0")

    known_geometry_terms = geometry_terms()
    known_tool_ids = {tool["tool_id"] for tool in tool_dictionary.get("tools", [])}

    methods = bundle.get("methods")
    if not isinstance(methods, list) or not methods:
        fail("methods must be a non-empty list")

    seen: set[str] = set()
    for method in methods:
        if not isinstance(method, dict):
            fail("each method must be an object")
        method_id = method.get("method_id")
        if not isinstance(method_id, str) or not method_id:
            fail("method_id must be a non-empty string")
        if method_id in seen:
            fail(f"duplicate method_id {method_id}")
        seen.add(method_id)

        for field in (
            "source_support",
            "real_tools",
            "real_sequence",
            "asset_families",
            "drawing_ui_tags",
            "geometry_terms",
            "blender_tool_ids",
            "source_fields_needed",
            "operator_checks",
        ):
            require_nonempty_list(method, field)

        for source in method["source_support"]:
            if not isinstance(source, dict):
                fail(f"{method_id}.source_support entries must be objects")
            if not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
                fail(f"{method_id}.source_support.url must be https URL")
            if not isinstance(source.get("support_summary"), str) or not source["support_summary"]:
                fail(f"{method_id}.source_support.support_summary must be non-empty")

        unknown_geometry = sorted(set(method["geometry_terms"]) - known_geometry_terms)
        if unknown_geometry:
            fail(f"{method_id}.geometry_terms unknown: {unknown_geometry}")

        unknown_tools = sorted(set(method["blender_tool_ids"]) - known_tool_ids)
        if unknown_tools:
            fail(f"{method_id}.blender_tool_ids unknown: {unknown_tools}")

        for field in ("plain_name", "craft_domain", "mechanics", "repo_use"):
            if not isinstance(method.get(field), str) or not method[field]:
                fail(f"{method_id}.{field} must be a non-empty string")

    print(
        "PASS craft fabrication method validation: "
        f"methods={len(methods)} geometry_terms={len(known_geometry_terms)} tools={len(known_tool_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

