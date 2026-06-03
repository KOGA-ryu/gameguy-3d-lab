#!/usr/bin/env python3
"""Classify repo scripts by their relationship to the canonical asset pump.

This is an audit tool only. It does not delete, move, rewrite, or execute the
scripts it classifies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
BUCKETS = (
    "KEEP_CANONICAL",
    "CONVERT_TO_ADAPTER",
    "REPLACE_BY_PUMP",
    "REFERENCE_ONLY",
    "DELETE_LATER",
)

OVERRIDES: dict[str, tuple[str, str]] = {
    "asset_pump_v0.py": ("KEEP_CANONICAL", "canonical source recipe to deterministic asset JSON generator"),
    "compile_blender_tool_plan_v0.py": ("KEEP_CANONICAL", "canonical source intent to staged Blender tool-plan JSON compiler"),
    "execute_blender_tool_plan_v0.py": ("KEEP_CANONICAL", "adapter that consumes gameguy_tool_plan_v0 and executes supported deterministic Blender steps"),
    "export_blender_asset_preview_v0.py": ("KEEP_CANONICAL", "first adapter that consumes gameguy_asset_v0 JSON"),
    "export_blender_measured_components_preview_v0.py": ("KEEP_CANONICAL", "adapter that consumes measured gameguy_asset_v0 JSON from the asset pump"),
    "validate_generation_pipeline_v0.py": ("KEEP_CANONICAL", "orchestrates canonical deterministic 3D generation validation gates"),
    "validate_reference_dissection_packet_v0.py": ("KEEP_CANONICAL", "guards reference-led shape and Blender tool dissection packets before geometry generation"),
    "validate_asset_generation_registry_v0.py": ("KEEP_CANONICAL", "guards the declared canonical generation recipe/tool-plan surface and reference-only boundaries"),
    "validate_blender_tool_plan_execution_report_v0.py": ("KEEP_CANONICAL", "guards Blender execution quality reports without importing Blender or source recipes"),
    "validate_gameguy_tool_plan_v0.py": ("KEEP_CANONICAL", "guards deterministic gameguy_tool_plan_v0 compiler output before Blender adapter execution"),
    "validate_geometry_dictionary.py": ("KEEP_CANONICAL", "guards legal geometry vocabulary used by recipes and pump"),
    "validate_connector_source_v0.py": ("KEEP_CANONICAL", "guards connector source manifest and placement policy"),
    "validate_gameguy_asset_v0.py": ("KEEP_CANONICAL", "guards deterministic gameguy_asset_v0 pump output"),
    "validate_measured_component_source_v0.py": ("KEEP_CANONICAL", "guards promoted measured component source recipes"),
    "validate_measured_molding_profiles_v0.py": ("KEEP_CANONICAL", "guards source-only measured molding and compound-pier profiles before generation"),
    "validate_railing_detail_profiles_v0.py": ("KEEP_CANONICAL", "guards source-owned 2D railing detail profiles and Blender tool stage sequencing"),
    "compile_sacred_graph_v0.py": ("KEEP_CANONICAL", "canonical sacred construction graph source compiler before asset lifting, folding, or Blender adapter work"),
    "validate_tiny_fixture_v0.py": ("KEEP_CANONICAL", "guards canonical source-only map/building/connector fixture"),
    "audit_script_orbit_v0.py": ("KEEP_CANONICAL", "tracks script cleanup buckets without deleting files"),
    "validate_contract.py": ("REFERENCE_ONLY", "legacy quarantined 2D mosaic contract validator; keep until quarantine is retired"),
}


def classify_script(path: Path) -> dict[str, str]:
    name = path.name
    if name in OVERRIDES:
        bucket, reason = OVERRIDES[name]
    elif name.startswith("blender_"):
        bucket = "REFERENCE_ONLY"
        reason = "legacy Blender proof script; active Blender work should use export_blender_* adapters that consume source or generated JSON"
    elif name.startswith("compile_"):
        bucket = "REFERENCE_ONLY"
        reason = "compiler lane remains reference material until its source value is ported or retired"
    elif name.startswith("create_"):
        bucket = "REFERENCE_ONLY"
        reason = "fixture/template creation helper; keep as reference until replaced by source fixtures"
    elif name.startswith("validate_"):
        bucket = "REFERENCE_ONLY"
        reason = "validator outside the current pump path; review before promoting or deleting"
    elif name.startswith("audit_"):
        bucket = "REFERENCE_ONLY"
        reason = "audit helper outside the current pump path; review before promoting or deleting"
    else:
        bucket = "REFERENCE_ONLY"
        reason = "unclassified script; review manually before any cleanup"

    return {
        "script": f"scripts/{name}",
        "bucket": bucket,
        "reason": reason,
    }


def build_report() -> dict[str, Any]:
    scripts = sorted(SCRIPT_DIR.glob("*.py"))
    rows = [classify_script(path) for path in scripts]
    counts = {bucket: 0 for bucket in BUCKETS}
    for row in rows:
        counts[row["bucket"]] += 1
    return {
        "schema": "script_orbit_audit_v0",
        "script_count": len(rows),
        "bucket_counts": counts,
        "buckets": {
            "KEEP_CANONICAL": "First-class path for source-to-geometry generation, source validation, or adapter validation.",
            "CONVERT_TO_ADAPTER": "Useful proof script, but Blender should only consume deterministic JSON.",
            "REPLACE_BY_PUMP": "Older asset-generation logic that should be absorbed by recipes, dictionary terms, or the pump.",
            "REFERENCE_ONLY": "Keep for study or future porting; do not treat as core engine logic.",
            "DELETE_LATER": "Candidate for removal after a separate confirmation task.",
        },
        "rules": {
            "deletes_files": False,
            "moves_files": False,
            "executes_classified_scripts": False,
            "blender_is_adapter_layer": True,
            "canonical_center": "source asset recipe -> profile/operation compiler -> deterministic asset geometry JSON",
        },
        "scripts": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit script cleanup buckets around the canonical asset pump.")
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable audit report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    if args.json_report:
        path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    counts = ", ".join(f"{bucket}={report['bucket_counts'][bucket]}" for bucket in BUCKETS)
    print(f"PASS script orbit audit: scripts={report['script_count']} {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
