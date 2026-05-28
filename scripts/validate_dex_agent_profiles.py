#!/usr/bin/env python3
"""Validate Dex agent profile catalog and profile AGENTS files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "goal" / "dex_workflow" / "agent_profile_catalog_v0.json"
RECEIPT_PATH = ROOT / "goal" / "dex_workflow" / "agent_profile_receipt.json"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    if not CATALOG_PATH.exists():
        fail(f"missing catalog: {CATALOG_PATH.relative_to(ROOT)}")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    profiles = catalog.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        fail("catalog profiles must be a non-empty list")

    seen_ids: set[str] = set()
    missing_paths: list[str] = []
    empty_profiles: list[str] = []

    for profile in profiles:
        profile_id = profile.get("profile_id")
        dex_id = profile.get("dex_id")
        path_value = profile.get("path")
        work_type = profile.get("work_type")

        if not all(isinstance(value, str) and value for value in [profile_id, dex_id, path_value, work_type]):
            fail(f"profile has missing required string fields: {profile}")
        if profile_id in seen_ids:
            fail(f"duplicate profile_id: {profile_id}")
        seen_ids.add(profile_id)

        path = ROOT / path_value
        if not path.exists():
            missing_paths.append(path_value)
            continue
        if path.name != "AGENTS.md":
            fail(f"profile path must end in AGENTS.md: {path_value}")
        if not path.read_text(encoding="utf-8").strip():
            empty_profiles.append(path_value)

    if missing_paths:
        fail("missing profile paths: " + ", ".join(missing_paths))
    if empty_profiles:
        fail("empty profile files: " + ", ".join(empty_profiles))

    if RECEIPT_PATH.exists():
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        expected = receipt.get("profile_count")
        if expected != len(profiles):
            fail(f"receipt profile_count {expected} != catalog count {len(profiles)}")

    print(f"PASS: {len(profiles)} dex agent profiles validated")


if __name__ == "__main__":
    main()
