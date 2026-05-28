#!/usr/bin/env python3
"""Validate mosaic dungeon tile contract JSON files.

This intentionally uses only the Python standard library so the harness works
before any art or Aseprite-specific dependencies exist.
"""

from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "asset_id",
    "source_image_path",
    "source_title",
    "source_author_or_culture",
    "source_date_or_period",
    "source_url",
    "source_license",
    "source_license_url",
    "source_institution",
    "motif_type",
    "target_tile_size_px",
    "tile_category",
    "palette_id",
    "allowed_palette",
    "required_layers",
    "animation_tags_or_export_tags",
    "seamless_required",
    "border_padding_px",
    "export_targets",
    "review_status",
    "notes",
]

ALLOWED_MOTIF_TYPES = {
    "floor_fill",
    "border_straight",
    "border_corner",
    "threshold",
    "center_medallion",
    "wall_symbol",
    "damaged_variant",
    "faction_emblem",
}

ALLOWED_TARGET_SIZES = {
    "16x16",
    "32x32",
    "64x64",
    "128x128",
    "256x256",
    "512x512",
    "1024x1024",
    "2048x2048",
    "4096x4096",
}

REQUIRED_LAYERS = [
    "reference",
    "crop_grid",
    "rough_trace",
    "clean_tesserae",
    "palette_blocks",
    "grout_lines",
    "damage_overlay",
    "seam_test",
    "export",
]

REQUIRED_EXPORT_TAGS = [
    "floor_clean",
    "floor_cracked",
    "floor_overgrown",
    "border_straight",
    "border_corner",
    "threshold",
    "centerpiece",
]

ALLOWED_REVIEW_STATUSES = {
    "source_pending",
    "source_verified",
    "trace_started",
    "trace_ready_for_review",
    "approved",
    "rejected",
    "exported",
}

PRODUCTION_REVIEW_STATUSES = {
    "source_verified",
    "trace_started",
    "trace_ready_for_review",
    "approved",
    "exported",
}

PRODUCTION_LICENSE_ALLOWLIST = {
    "CC0",
    "Public Domain",
    "Open Access - Public Domain",
    "Wikimedia Commons - license verified",
}


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def _require_list(name: str, value: Any, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    return value


def _find_pending_values(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, str):
        if value.startswith("PENDING_"):
            return [path]
        return []

    if isinstance(value, dict):
        pending_paths: list[str] = []
        for key, item in value.items():
            pending_paths.extend(_find_pending_values(item, f"{path}.{key}"))
        return pending_paths

    if isinstance(value, list):
        pending_paths = []
        for index, item in enumerate(value):
            pending_paths.extend(_find_pending_values(item, f"{path}[{index}]"))
        return pending_paths

    return []


def validate_contract(path: Path, mode: str = "draft") -> list[str]:
    errors: list[str] = []

    try:
        data = _read_json(path)
    except ValueError as exc:
        return [str(exc)]

    if not isinstance(data, dict):
        return ["contract root must be a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    for field in [
        "asset_id",
        "source_image_path",
        "source_title",
        "source_author_or_culture",
        "source_date_or_period",
        "source_url",
        "source_license",
        "source_license_url",
        "source_institution",
        "tile_category",
        "palette_id",
        "review_status",
        "notes",
    ]:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    motif_type = data.get("motif_type")
    if motif_type not in ALLOWED_MOTIF_TYPES:
        errors.append(
            f"unknown motif_type {motif_type!r}; expected one of {sorted(ALLOWED_MOTIF_TYPES)}"
        )

    target_size = data.get("target_tile_size_px")
    if target_size not in ALLOWED_TARGET_SIZES:
        errors.append(
            f"unknown target_tile_size_px {target_size!r}; expected one of {sorted(ALLOWED_TARGET_SIZES)}"
        )

    review_status = data.get("review_status")
    if review_status not in ALLOWED_REVIEW_STATUSES:
        errors.append(
            f"unknown review_status {review_status!r}; expected one of {sorted(ALLOWED_REVIEW_STATUSES)}"
        )

    if not isinstance(data.get("seamless_required"), bool):
        errors.append("seamless_required must be a boolean")

    if not isinstance(data.get("border_padding_px"), int) or data.get("border_padding_px") < 0:
        errors.append("border_padding_px must be a non-negative integer")

    allowed_palette = _require_list("allowed_palette", data.get("allowed_palette"), errors)
    if not allowed_palette:
        errors.append("allowed_palette must contain at least one color")
    for color in allowed_palette:
        if not isinstance(color, str) or len(color) != 7 or not color.startswith("#"):
            errors.append(f"allowed_palette contains invalid color value: {color!r}")

    required_layers = _require_list("required_layers", data.get("required_layers"), errors)
    missing_layers = [layer for layer in REQUIRED_LAYERS if layer not in required_layers]
    if missing_layers:
        errors.append(f"required_layers missing: {', '.join(missing_layers)}")

    export_tags = _require_list(
        "animation_tags_or_export_tags", data.get("animation_tags_or_export_tags"), errors
    )
    missing_tags = [tag for tag in REQUIRED_EXPORT_TAGS if tag not in export_tags]
    if missing_tags:
        errors.append(f"animation_tags_or_export_tags missing: {', '.join(missing_tags)}")

    export_targets = _require_list("export_targets", data.get("export_targets"), errors)
    if not export_targets:
        errors.append("export_targets must contain at least one target")
    for index, target in enumerate(export_targets):
        if not isinstance(target, dict):
            errors.append(f"export_targets[{index}] must be an object")
            continue
        if not isinstance(target.get("kind"), str) or not target.get("kind"):
            errors.append(f"export_targets[{index}].kind must be a non-empty string")
        if not isinstance(target.get("path"), str) or not target.get("path"):
            errors.append(f"export_targets[{index}].path must be a non-empty string")

    if mode == "production":
        pending_paths = _find_pending_values(data)
        for pending_path in pending_paths:
            errors.append(f"production mode rejects PENDING_ value at {pending_path}")

        if review_status not in PRODUCTION_REVIEW_STATUSES:
            errors.append(
                "production mode review_status must be one of "
                f"{sorted(PRODUCTION_REVIEW_STATUSES)}; got {review_status!r}"
            )

        source_license = data.get("source_license")
        if source_license not in PRODUCTION_LICENSE_ALLOWLIST:
            errors.append(
                "production mode source_license must be one of "
                f"{sorted(PRODUCTION_LICENSE_ALLOWLIST)}; got {source_license!r}"
            )

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate mosaic dungeon tile contract JSON files."
    )
    parser.add_argument(
        "--mode",
        choices=["draft", "production"],
        default="draft",
        help="validation mode; draft allows PENDING_ metadata, production rejects it",
    )
    parser.add_argument("contracts", nargs="+", help="contract JSON files to validate")
    args = parser.parse_args(argv[1:])

    if not args.contracts:
        parser.print_usage(sys.stderr)
        return 2

    failed = False
    for raw_path in args.contracts:
        path = Path(raw_path)
        errors = validate_contract(path, mode=args.mode)
        if errors:
            failed = True
            print(f"FAIL {path} [{args.mode}]")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK {path} [{args.mode}]")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
