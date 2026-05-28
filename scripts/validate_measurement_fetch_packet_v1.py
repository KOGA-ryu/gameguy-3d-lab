#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_ROOT = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements"
SOURCES_PATH = PACKET_ROOT / "measurement_sources_v1.json"
MEASUREMENTS_PATH = PACKET_ROOT / "extracted_measurements_v1.json"
PARTS_PATH = PACKET_ROOT / "measurement_parts_taxonomy_v1.json"
GEOMETRY_LINKS_PATH = PACKET_ROOT / "measurement_geometry_term_links_v1.json"
SEMANTIC_LINKS_PATH = PACKET_ROOT / "measurement_semantic_role_links_v1.json"
REPORT_PATH = ROOT / "docs" / "research" / "architectural_measurements" / "measurement_extraction_report_v1.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "architectural_measurement_extraction_v1.receipt.json"
VALIDATION_RECEIPT_PATH = ROOT / "factory" / "receipts" / "measurement" / "measurement_fetch_packet_v1.validation_receipt.json"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"missing required file {path.relative_to(ROOT)}")


def validate_sources(sources: dict[str, Any]) -> list[str]:
    if sources.get("schema") != "architectural_measurement_sources_fetch_packet_v1":
        fail("measurement_sources_v1 schema mismatch")
    source_records = sources.get("primary_source_websites")
    if not isinstance(source_records, list) or len(source_records) < 6:
        fail("measurement_sources_v1 requires at least 6 primary_source_websites")
    ids: list[str] = []
    for source in source_records:
        for field in ["source_id", "source_title", "source_url", "source_type", "use_for", "note"]:
            if field not in source:
                fail(f"source record missing {field}")
        if source["source_id"] in ids:
            fail(f"duplicate source_id {source['source_id']}")
        ids.append(source["source_id"])
    policy = sources.get("source_policy", {})
    for key in [
        "prefer_measured_drawings_over_photos",
        "do_not_download_or_reuse_protected_images",
        "no_structural_safety_claims",
        "no_cultural_authenticity_claims",
        "no_fabrication_claims",
    ]:
        if policy.get(key) is not True:
            fail(f"source_policy.{key} must be true")
    return ids


def validate_measurements(measurements: dict[str, Any]) -> tuple[str, int]:
    if measurements.get("schema") != "architectural_extracted_measurements_fetch_packet_v1":
        fail("extracted_measurements_v1 schema mismatch")
    records = measurements.get("measurements")
    if not isinstance(records, list):
        fail("extracted_measurements_v1 measurements must be a list")
    if records:
        status = "ready_for_compile"
    else:
        status = "awaiting_research_dex_fetch"
    if measurements.get("status") != status:
        fail(f"extracted_measurements_v1 status must be {status}")
    required_counts = measurements.get("first_fetch_batch_required_counts")
    if not isinstance(required_counts, dict) or len(required_counts) < 5:
        fail("first_fetch_batch_required_counts must include first batch targets")
    if not measurements.get("measurement_names_to_extract"):
        fail("measurement_names_to_extract must be non-empty")
    return status, len(records)


def validate_taxonomy(parts: dict[str, Any], geometry_links: dict[str, Any], semantic_links: dict[str, Any]) -> int:
    if parts.get("schema") != "measurement_parts_taxonomy_v1":
        fail("measurement_parts_taxonomy_v1 schema mismatch")
    object_classes = parts.get("object_classes")
    if not isinstance(object_classes, list) or len(object_classes) < 20:
        fail("measurement_parts_taxonomy_v1 requires broad object class coverage")
    for item in object_classes:
        for field in ["object_class", "source_priority", "extract", "parts"]:
            if field not in item:
                fail(f"object class record missing {field}")
    if geometry_links.get("schema") != "measurement_geometry_term_links_v1":
        fail("measurement_geometry_term_links_v1 schema mismatch")
    if semantic_links.get("schema") != "measurement_semantic_role_links_v1":
        fail("measurement_semantic_role_links_v1 schema mismatch")
    return len(object_classes)


def main() -> None:
    for path in [SOURCES_PATH, MEASUREMENTS_PATH, PARTS_PATH, GEOMETRY_LINKS_PATH, SEMANTIC_LINKS_PATH, REPORT_PATH, RECEIPT_PATH]:
        require_file(path)
    sources = load_json(SOURCES_PATH)
    measurements = load_json(MEASUREMENTS_PATH)
    parts = load_json(PARTS_PATH)
    geometry_links = load_json(GEOMETRY_LINKS_PATH)
    semantic_links = load_json(SEMANTIC_LINKS_PATH)
    source_ids = validate_sources(sources)
    status, measurement_count = validate_measurements(measurements)
    object_class_count = validate_taxonomy(parts, geometry_links, semantic_links)

    VALIDATION_RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "measurement_fetch_packet_validation_receipt_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "blocked" if status == "awaiting_research_dex_fetch" else "pass",
        "blocked_reason": "awaiting researched measurement records" if measurement_count == 0 else None,
        "next_actor": "Research Dex" if measurement_count == 0 else "Measurement Compiler",
        "source_count": len(source_ids),
        "measurement_count": measurement_count,
        "object_class_count": object_class_count,
        "packet_files": [
            str(SOURCES_PATH.relative_to(ROOT)),
            str(MEASUREMENTS_PATH.relative_to(ROOT)),
            str(PARTS_PATH.relative_to(ROOT)),
            str(GEOMETRY_LINKS_PATH.relative_to(ROOT)),
            str(SEMANTIC_LINKS_PATH.relative_to(ROOT)),
        ],
        "rules": {
            "fetch_request_only": measurement_count == 0,
            "no_production_approval": True,
            "no_structural_safety_claims": True,
            "no_cultural_authenticity_claims": True,
            "no_fabrication_claims": True
        }
    }
    VALIDATION_RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"validated measurement fetch packet v1: {status}")
    print(f"sources: {len(source_ids)}")
    print(f"measurements: {measurement_count}")
    print(f"object_classes: {object_class_count}")
    print(f"receipt: {VALIDATION_RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
