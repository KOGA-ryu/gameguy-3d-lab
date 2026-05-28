#!/usr/bin/env python3
"""Validate architectural measurement source and extraction records.

This guards the handoff from research Dex into the construction grammar:

source records -> extracted measurements -> validated source refs / units /
confidence / no-copy rules
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "contracts" / "architectural_measurement_source_v0.json"
MEASUREMENT_CONTRACT = ROOT / "contracts" / "architectural_measurement_record_v0.json"
SOURCE_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "measurement_sources_v0.json"
MEASUREMENT_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "extracted_measurements_v0.json"
OUT_DIR = ROOT / "goal" / "architecture" / "architectural_taxonomy_v0"
REPORT_PATH = OUT_DIR / "architectural_measurement_validation_report_v0.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "architectural_measurement_validation_v0.receipt.json"

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "artwork_reused": False,
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


def require_fields(context: str, row: dict[str, Any], fields: list[str]) -> None:
    for field in fields:
        if field not in row:
            fail(f"{context} missing required field `{field}`")


def require_id(context: str, value: Any) -> str:
    if not isinstance(value, str) or not ID_RE.match(value):
        fail(f"{context} has invalid id `{value}`")
    return value


def require_allowed(context: str, value: Any, allowed: set[str]) -> None:
    if value not in allowed:
        fail(f"{context} has unsupported value `{value}`")


def require_number_or_null(context: str, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{context} must be number or null")
    if not math.isfinite(float(value)):
        fail(f"{context} must be finite")
    if float(value) < 0.0:
        fail(f"{context} must not be negative")


def validate_sources(source_contract: dict[str, Any], source_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if source_data.get("schema") != "architectural_measurement_sources_v0":
        fail(f"{SOURCE_PATH.relative_to(ROOT)} schema must be architectural_measurement_sources_v0")
    if source_data.get("no_claims") != NO_CLAIMS:
        fail(f"{SOURCE_PATH.relative_to(ROOT)} no_claims must match required false claims")
    sources = source_data.get("sources")
    if not isinstance(sources, list):
        fail("sources must be a list")
    allowed_types = set(source_contract["allowed_source_types"])
    allowed_confidence = set(source_contract["allowed_confidence"])
    rows: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"sources[{index}] must be an object")
        context = f"sources[{index}]"
        require_fields(context, source, source_contract["required_fields"])
        source_id = require_id(f"{context}.source_id", source["source_id"])
        if source_id in rows:
            fail(f"duplicate source_id `{source_id}`")
        require_allowed(f"{context}.source_type", source["source_type"], allowed_types)
        require_allowed(f"{context}.confidence", source["confidence"], allowed_confidence)
        if source["use_allowed_for"] != "measurement_reference_only":
            fail(f"{context}.use_allowed_for must be measurement_reference_only")
        rows[source_id] = source
    return rows


def derive_missing_ratios(measurement: dict[str, Any], ratio_fields: list[str]) -> dict[str, Any]:
    raw = measurement["raw_measurements"]
    ratios = dict(measurement["derived_ratios"])

    span = raw.get("span_m") or raw.get("bay_width_m")
    if span and raw.get("rise_m") is None and raw.get("apex_height_m") is not None and raw.get("springline_height_m") is not None:
        raw["rise_m"] = round(float(raw["apex_height_m"]) - float(raw["springline_height_m"]), 6)
    span = raw.get("span_m") or raw.get("bay_width_m")
    if span:
        span_f = float(span)
        derived = {
            "rise_to_span": raw.get("rise_m"),
            "springline_to_span": raw.get("springline_height_m"),
            "pier_to_span": raw.get("pier_width_m"),
            "wall_thickness_to_span": raw.get("wall_thickness_m"),
            "column_radius_to_span": raw.get("column_radius_m"),
            "column_height_to_span": raw.get("column_height_m"),
            "rib_to_span": raw.get("vault_rib_thickness_m"),
        }
        for key, value in derived.items():
            if ratios.get(key) is None and value is not None:
                ratios[key] = round(float(value) / span_f, 6)
    if ratios.get("dome_to_plan_diameter") is None and raw.get("dome_diameter_m") is not None and raw.get("plan_diameter_m") is not None:
        ratios["dome_to_plan_diameter"] = round(float(raw["dome_diameter_m"]) / float(raw["plan_diameter_m"]), 6)

    for field in ratio_fields:
        ratios.setdefault(field, None)
    return ratios


def validate_measurements(
    measurement_contract: dict[str, Any],
    measurement_data: dict[str, Any],
    source_ids: set[str],
) -> list[dict[str, Any]]:
    if measurement_data.get("schema") != "architectural_extracted_measurements_v0":
        fail(f"{MEASUREMENT_PATH.relative_to(ROOT)} schema must be architectural_extracted_measurements_v0")
    if measurement_data.get("no_claims") != NO_CLAIMS:
        fail(f"{MEASUREMENT_PATH.relative_to(ROOT)} no_claims must match required false claims")
    measurements = measurement_data.get("measurements")
    if not isinstance(measurements, list):
        fail("measurements must be a list")
    allowed_terms = set(measurement_contract["allowed_term_candidates"])
    allowed_methods = set(measurement_contract["allowed_extraction_methods"])
    allowed_confidence = set(measurement_contract["allowed_confidence"])
    raw_fields = measurement_contract["raw_measurement_fields"]
    ratio_fields = measurement_contract["derived_ratio_fields"]
    ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, measurement in enumerate(measurements):
        if not isinstance(measurement, dict):
            fail(f"measurements[{index}] must be an object")
        context = f"measurements[{index}]"
        require_fields(context, measurement, measurement_contract["required_fields"])
        measurement_id = require_id(f"{context}.measurement_id", measurement["measurement_id"])
        if measurement_id in ids:
            fail(f"duplicate measurement_id `{measurement_id}`")
        ids.add(measurement_id)
        source_id = require_id(f"{context}.source_id", measurement["source_id"])
        if source_id not in source_ids:
            fail(f"{context} references unknown source_id `{source_id}`")
        require_allowed(f"{context}.architectural_term_candidate", measurement["architectural_term_candidate"], allowed_terms)
        require_allowed(f"{context}.extraction_method", measurement["extraction_method"], allowed_methods)
        require_allowed(f"{context}.confidence", measurement["confidence"], allowed_confidence)
        if measurement["do_not_copy_geometry"] is not True:
            fail(f"{context}.do_not_copy_geometry must be true")

        raw = measurement["raw_measurements"]
        ratios = measurement["derived_ratios"]
        if not isinstance(raw, dict) or not isinstance(ratios, dict):
            fail(f"{context} raw_measurements and derived_ratios must be objects")
        for field in raw_fields:
            raw.setdefault(field, None)
            require_number_or_null(f"{context}.raw_measurements.{field}", raw[field])
        for field in ratio_fields:
            ratios.setdefault(field, None)
            require_number_or_null(f"{context}.derived_ratios.{field}", ratios[field])
        normalized_measurement = dict(measurement)
        normalized_measurement["raw_measurements"] = raw
        normalized_measurement["derived_ratios"] = derive_missing_ratios(normalized_measurement, ratio_fields)
        normalized.append(normalized_measurement)
    return normalized


def write_report(sources: dict[str, dict[str, Any]], measurements: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_term: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for measurement in measurements:
        by_term[measurement["architectural_term_candidate"]] = by_term.get(measurement["architectural_term_candidate"], 0) + 1
        by_confidence[measurement["confidence"]] = by_confidence.get(measurement["confidence"], 0) + 1
    lines = [
        "# Architectural Measurement Validation v0",
        "",
        "Validates source-backed measurement records before they can influence architectural grammar ranges.",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| sources | {len(sources)} |",
        f"| measurements | {len(measurements)} |",
        "",
        "## Measurements By Term",
        "",
        "| Term | Count |",
        "| --- | ---: |",
    ]
    for term, count in sorted(by_term.items()):
        lines.append(f"| `{term}` | {count} |")
    lines.extend(["", "## Measurements By Confidence", "", "| Confidence | Count |", "| --- | ---: |"])
    for confidence, count in sorted(by_confidence.items()):
        lines.append(f"| `{confidence}` | {count} |")
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "- Measurements are grammar/proportion references only.",
            "- Source records must explicitly allow `measurement_reference_only`.",
            "- Measurement rows must keep `do_not_copy_geometry: true`.",
            "- Null is allowed for unknown values; fake precision is not.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(sources: dict[str, dict[str, Any]], measurements: list[dict[str, Any]]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "architectural_measurement_validation_v0",
        "created_at_utc": now_iso(),
        "source_count": len(sources),
        "measurement_count": len(measurements),
        "source_file": str(SOURCE_PATH.relative_to(ROOT)),
        "measurement_file": str(MEASUREMENT_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "rules": {
            "measurement_reference_only": True,
            "do_not_copy_geometry_required": True,
            "artwork_reused": False,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_production_approval": True,
        },
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    source_contract = load_json(SOURCE_CONTRACT)
    measurement_contract = load_json(MEASUREMENT_CONTRACT)
    sources = validate_sources(source_contract, load_json(SOURCE_PATH))
    measurements = validate_measurements(measurement_contract, load_json(MEASUREMENT_PATH), set(sources))
    write_report(sources, measurements)
    write_receipt(sources, measurements)
    print(f"validated {len(sources)} architectural measurement sources")
    print(f"validated {len(measurements)} architectural measurements")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
