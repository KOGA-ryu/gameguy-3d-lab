#!/usr/bin/env python3
"""Compile validated architectural measurements into usable ratio ranges.

The output is the shape-grammar parameter envelope layer:

extracted measurements -> grouped ratios -> min/max/recommended ranges ->
weak term warnings
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT_CONTRACT = ROOT / "contracts" / "architectural_measurement_record_v0.json"
SOURCE_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "measurement_sources_v0.json"
MEASUREMENT_PATH = ROOT / "data" / "architecture" / "taxonomy" / "source_measurements" / "extracted_measurements_v0.json"
OUT_DIR = ROOT / "goal" / "architecture" / "architectural_taxonomy_v0"
RANGES_PATH = OUT_DIR / "proportion_ranges_v0.json"
REPORT_PATH = OUT_DIR / "architectural_measurement_taxonomy_report_v0.md"
RECEIPT_PATH = ROOT / "goal" / "receipts" / "architectural_proportion_ranges_v0.receipt.json"

NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
    "artwork_reused": False,
}

IMPORTANT_TERMS = [
    "pointed_arch_bay",
    "round_arch_bay",
    "octagonal_plan",
    "column_or_pier",
    "dome_or_vault",
]


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


def measurement_terms(measurement: dict[str, Any]) -> list[str]:
    term = measurement["architectural_term_candidate"]
    terms = [term]
    if term in {"column", "pier"}:
        terms.append("column_or_pier")
    if term in {"dome", "vault", "vault_rib"}:
        terms.append("dome_or_vault")
    if term == "radial_plan":
        terms.append("octagonal_plan")
    return terms


def finite_number(value: Any) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def derive_ratios(measurement: dict[str, Any], ratio_fields: list[str]) -> dict[str, float | None]:
    raw = measurement["raw_measurements"]
    ratios = dict(measurement["derived_ratios"])
    span = finite_number(raw.get("span_m")) or finite_number(raw.get("bay_width_m"))
    if span and finite_number(raw.get("rise_m")) is None and finite_number(raw.get("apex_height_m")) is not None and finite_number(raw.get("springline_height_m")) is not None:
        raw["rise_m"] = round(float(raw["apex_height_m"]) - float(raw["springline_height_m"]), 6)
    span = finite_number(raw.get("span_m")) or finite_number(raw.get("bay_width_m"))
    if span:
        derived = {
            "rise_to_span": finite_number(raw.get("rise_m")),
            "springline_to_span": finite_number(raw.get("springline_height_m")),
            "pier_to_span": finite_number(raw.get("pier_width_m")),
            "wall_thickness_to_span": finite_number(raw.get("wall_thickness_m")),
            "column_radius_to_span": finite_number(raw.get("column_radius_m")),
            "column_height_to_span": finite_number(raw.get("column_height_m")),
            "rib_to_span": finite_number(raw.get("vault_rib_thickness_m")),
        }
        for key, numerator in derived.items():
            if finite_number(ratios.get(key)) is None and numerator is not None:
                ratios[key] = round(numerator / span, 6)
    if finite_number(ratios.get("dome_to_plan_diameter")) is None:
        dome = finite_number(raw.get("dome_diameter_m"))
        plan = finite_number(raw.get("plan_diameter_m"))
        if dome is not None and plan:
            ratios["dome_to_plan_diameter"] = round(dome / plan, 6)
    return {field: finite_number(ratios.get(field)) for field in ratio_fields}


def range_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "median": None,
            "recommended_range": None,
            "status": "missing",
        }
    sorted_values = sorted(values)
    low = sorted_values[0]
    high = sorted_values[-1]
    med = float(median(sorted_values))
    if len(sorted_values) >= 3:
        recommended = [round(sorted_values[0], 6), round(sorted_values[-1], 6)]
        status = "usable"
    else:
        pad = max(abs(med) * 0.1, 0.01)
        recommended = [round(max(0.0, low - pad), 6), round(high + pad, 6)]
        status = "thin_evidence"
    return {
        "count": len(values),
        "min": round(low, 6),
        "max": round(high, 6),
        "median": round(med, 6),
        "recommended_range": recommended,
        "status": status,
    }


def compile_ranges() -> dict[str, Any]:
    contract = load_json(MEASUREMENT_CONTRACT)
    ratio_fields = contract["derived_ratio_fields"]
    source_data = load_json(SOURCE_PATH)
    measurement_data = load_json(MEASUREMENT_PATH)
    if source_data.get("no_claims") != NO_CLAIMS or measurement_data.get("no_claims") != NO_CLAIMS:
        fail("source and measurement no_claims must match required false claims")
    grouped: dict[str, dict[str, list[float]]] = {}
    measurement_counts: dict[str, int] = {}
    confidence_counts: dict[str, dict[str, int]] = {}
    for measurement in measurement_data["measurements"]:
        ratios = derive_ratios(measurement, ratio_fields)
        for term in measurement_terms(measurement):
            measurement_counts[term] = measurement_counts.get(term, 0) + 1
            confidence_counts.setdefault(term, {})
            confidence = measurement["confidence"]
            confidence_counts[term][confidence] = confidence_counts[term].get(confidence, 0) + 1
            grouped.setdefault(term, {field: [] for field in ratio_fields})
            for field, value in ratios.items():
                if value is not None:
                    grouped[term][field].append(value)

    terms: dict[str, Any] = {}
    for term, ratios in sorted(grouped.items()):
        terms[term] = {
            "measurement_count": measurement_counts.get(term, 0),
            "confidence_counts": confidence_counts.get(term, {}),
            "ratios": {
                field: range_summary(values)
                for field, values in ratios.items()
            },
        }

    weak_terms = []
    for term in IMPORTANT_TERMS:
        count = measurement_counts.get(term, 0)
        if count < 2:
            weak_terms.append({"term": term, "reason": "fewer_than_two_measurement_records", "measurement_count": count})
            continue
        ratio_counts = sum(1 for summary in terms.get(term, {}).get("ratios", {}).values() if summary["count"] > 0)
        if ratio_counts == 0:
            weak_terms.append({"term": term, "reason": "no_derived_ratio_values", "measurement_count": count})

    return {
        "schema": "architectural_proportion_ranges_v0",
        "created_at_utc": now_iso(),
        "source_file": str(SOURCE_PATH.relative_to(ROOT)),
        "measurement_file": str(MEASUREMENT_PATH.relative_to(ROOT)),
        "source_count": len(source_data["sources"]),
        "measurement_count": len(measurement_data["measurements"]),
        "terms": terms,
        "weak_terms": weak_terms,
        "rules": {
            "measurement_reference_only": True,
            "ranges_are_not_structural_rules": True,
            "thin_evidence_ranges_are_padded": True,
            "null_values_are_ignored": True,
            "artwork_reused": False,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_production_approval": True,
        },
    }


def write_report(ranges: dict[str, Any]) -> None:
    lines = [
        "# Architectural Measurement Taxonomy v0",
        "",
        "Compiles source-backed measurement records into ratio ranges for the architectural grammar.",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| sources | {ranges['source_count']} |",
        f"| measurements | {ranges['measurement_count']} |",
        f"| terms with ranges | {len(ranges['terms'])} |",
        f"| weak important terms | {len(ranges['weak_terms'])} |",
        "",
        "## Term Ranges",
        "",
    ]
    if not ranges["terms"]:
        lines.append("No measurement records have been added yet. The receiver is ready for research Dex output.")
        lines.append("")
    for term, data in ranges["terms"].items():
        lines.extend(
            [
                f"### `{term}`",
                "",
                f"- measurement count: `{data['measurement_count']}`",
                f"- confidence counts: `{data['confidence_counts']}`",
                "",
                "| Ratio | Count | Min | Max | Median | Recommended | Status |",
                "| --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for ratio, summary in data["ratios"].items():
            lines.append(
                f"| `{ratio}` | {summary['count']} | {summary['min']} | {summary['max']} | {summary['median']} | `{summary['recommended_range']}` | {summary['status']} |"
            )
        lines.append("")
    lines.extend(["## Weak Terms", ""])
    if ranges["weak_terms"]:
        for item in ranges["weak_terms"]:
            lines.append(f"- `{item['term']}`: {item['reason']} ({item['measurement_count']} records)")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Use Rule",
            "",
            "These ranges are grammar/proportion hints only. They are not structural rules, fabrication dimensions, production approvals, or copied historical geometry.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_receipt(ranges: dict[str, Any]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_type": "architectural_proportion_ranges_v0",
        "created_at_utc": now_iso(),
        "source_count": ranges["source_count"],
        "measurement_count": ranges["measurement_count"],
        "term_count": len(ranges["terms"]),
        "weak_terms": ranges["weak_terms"],
        "range_output": str(RANGES_PATH.relative_to(ROOT)),
        "report": str(REPORT_PATH.relative_to(ROOT)),
        "rules": ranges["rules"],
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ranges = compile_ranges()
    RANGES_PATH.write_text(json.dumps(ranges, indent=2) + "\n", encoding="utf-8")
    write_report(ranges)
    write_receipt(ranges)
    print(f"compiled architectural proportion ranges for {len(ranges['terms'])} terms")
    print(f"ranges: {RANGES_PATH.relative_to(ROOT)}")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"receipt: {RECEIPT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
