#!/usr/bin/env python3
"""Compile Asset Mill simple solid recipes into measured JSON definitions.

This is not a renderer and not a mesh exporter. It converts profile + operation
recipes into reusable data the future Blender/engine layer can realize.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json"
OUT_ROOT = ROOT / "goal" / "architecture" / "asset_mill_v0"
SOLID_DIR = OUT_ROOT / "solids"
REPORT_DIR = OUT_ROOT / "reports"
RECEIPT_DIR = ROOT / "goal" / "receipts"

REQUIRED_NO_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}


@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def translated(self, t: tuple[float, float, float]) -> "Bounds":
        return Bounds(
            self.min_x + t[0],
            self.min_y + t[1],
            self.min_z + t[2],
            self.max_x + t[0],
            self.max_y + t[1],
            self.max_z + t[2],
        )

    def as_json(self) -> dict[str, list[float]]:
        return {
            "min": [round(self.min_x, 6), round(self.min_y, 6), round(self.min_z, 6)],
            "max": [round(self.max_x, 6), round(self.max_y, 6), round(self.max_z, 6)],
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def ensure_dirs() -> None:
    for path in (SOLID_DIR, REPORT_DIR, RECEIPT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_recipe_bundle() -> dict[str, Any]:
    if not RECIPE_PATH.exists():
        fail(f"missing recipe bundle: {RECIPE_PATH}")
    with RECIPE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema") != "asset_mill_recipe_bundle_v0":
        fail("recipe bundle schema must be asset_mill_recipe_bundle_v0")
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        fail("recipe bundle requires non-empty assets list")
    return data


def validate_no_claims(asset: dict[str, Any]) -> None:
    claims = asset.get("no_claims")
    if claims != REQUIRED_NO_CLAIMS:
        fail(f"{asset.get('asset_id')} no_claims must exactly match required false claims")


def require_fields(asset: dict[str, Any], fields: list[str]) -> None:
    for field in fields:
        if field not in asset:
            fail(f"{asset.get('asset_id')} missing required field: {field}")


def profile_points(profile: dict[str, Any]) -> list[list[float]]:
    ptype = profile.get("type")
    params = profile.get("params", {})
    if ptype == "rectangle":
        w = float(params["width"]) * 0.5
        d = float(params["depth"]) * 0.5
        return [[-w, -d], [w, -d], [w, d], [-w, d]]
    if ptype == "square":
        s = float(params["size"]) * 0.5
        return [[-s, -s], [s, -s], [s, s], [-s, s]]
    if ptype == "circle":
        radius = float(params["radius"])
        segments = int(params.get("segments", 24))
        return polygon_points(segments, radius)
    if ptype == "triangle":
        w = float(params["width"]) * 0.5
        d = float(params["depth"]) * 0.5
        return [[-w, -d], [w, -d], [0.0, d]]
    if ptype == "trapezoid":
        bw = float(params["bottom_width"]) * 0.5
        tw = float(params["top_width"]) * 0.5
        d = float(params["depth"]) * 0.5
        return [[-bw, -d], [bw, -d], [tw, d], [-tw, d]]
    if ptype == "regular_polygon":
        return polygon_points(int(params["sides"]), float(params["radius"]))
    if ptype == "octagon":
        return polygon_points(8, float(params["radius"]))
    if ptype == "capsule":
        length = float(params["length"])
        radius = float(params["radius"])
        segments = int(params.get("segments", 12))
        return capsule_points(length, radius, segments)
    fail(f"unsupported profile type: {ptype}")


def polygon_points(sides: int, radius: float) -> list[list[float]]:
    if sides < 3:
        fail("regular polygons require at least 3 sides")
    return [
        [round(math.cos(math.tau * i / sides) * radius, 6), round(math.sin(math.tau * i / sides) * radius, 6)]
        for i in range(sides)
    ]


def capsule_points(length: float, radius: float, segments: int) -> list[list[float]]:
    if segments < 6:
        fail("capsule segments must be >= 6")
    half = max(length * 0.5 - radius, 0.001)
    points: list[list[float]] = []
    half_segments = max(segments // 2, 3)
    for i in range(half_segments + 1):
        a = -math.pi * 0.5 + math.pi * i / half_segments
        points.append([round(half + math.cos(a) * radius, 6), round(math.sin(a) * radius, 6)])
    for i in range(half_segments + 1):
        a = math.pi * 0.5 + math.pi * i / half_segments
        points.append([round(-half + math.cos(a) * radius, 6), round(math.sin(a) * radius, 6)])
    return points


def bounds_from_points(points: list[list[float]], z0: float, z1: float) -> Bounds:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return Bounds(min(xs), min(ys), min(z0, z1), max(xs), max(ys), max(z0, z1))


def merge_bounds(bounds: list[Bounds]) -> Bounds:
    if not bounds:
        fail("cannot merge empty bounds")
    return Bounds(
        min(b.min_x for b in bounds),
        min(b.min_y for b in bounds),
        min(b.min_z for b in bounds),
        max(b.max_x for b in bounds),
        max(b.max_y for b in bounds),
        max(b.max_z for b in bounds),
    )


def connector_points(bounds: Bounds, connectors: list[str]) -> dict[str, list[float]]:
    cx = (bounds.min_x + bounds.max_x) * 0.5
    cy = (bounds.min_y + bounds.max_y) * 0.5
    cz = (bounds.min_z + bounds.max_z) * 0.5
    all_points = {
        "north": [cx, bounds.max_y, cz],
        "south": [cx, bounds.min_y, cz],
        "east": [bounds.max_x, cy, cz],
        "west": [bounds.min_x, cy, cz],
        "floor": [cx, cy, bounds.min_z],
        "ceiling": [cx, cy, bounds.max_z],
        "radial": [cx, cy, cz],
    }
    return {name: [round(v, 6) for v in all_points[name]] for name in connectors if name in all_points}


def approximate_area(points: list[list[float]]) -> float:
    area = 0.0
    count = len(points)
    for i in range(count):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % count]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def compile_primitive(asset: dict[str, Any]) -> dict[str, Any]:
    points = profile_points(asset["profile"])
    height = float(asset["height"])
    bounds = bounds_from_points(points, 0.0, height)
    return base_output(asset, bounds) | {
        "operation": "extrude",
        "geometry_outputs": {
            "profile_points_2d": points,
            "sections": [
                {"at": 0.0, "points": points},
                {"at": round(height, 6), "points": points},
            ],
            "bounds": bounds.as_json(),
            "connector_points": connector_points(bounds, asset["connectors"]),
            "component_refs": [],
            "approx_volume": round(approximate_area(points) * height, 6),
        },
    }


def compile_loft(asset: dict[str, Any]) -> dict[str, Any]:
    sections = []
    all_bounds = []
    for section in asset["sections"]:
        at = float(section["at"])
        points = profile_points(section["profile"])
        sections.append({"at": round(at, 6), "points": points})
        all_bounds.append(bounds_from_points(points, at, at))
    bounds = merge_bounds(all_bounds)
    return base_output(asset, bounds) | {
        "operation": "loft_sections",
        "geometry_outputs": {
            "profile_points_2d": [],
            "sections": sections,
            "bounds": bounds.as_json(),
            "connector_points": connector_points(bounds, asset["connectors"]),
            "component_refs": [],
            "approx_volume": null_volume_note(asset),
        },
    }


def null_volume_note(_: dict[str, Any]) -> str:
    return "not_computed_for_loft_v0"


def compile_compound(asset: dict[str, Any], compiled: dict[str, dict[str, Any]]) -> dict[str, Any]:
    component_refs = []
    bounds_list = []
    for component in asset["components"]:
        ref = component["asset_ref"]
        if ref not in compiled:
            fail(f"{asset['asset_id']} references unknown or later asset: {ref}")
        translation = tuple(float(v) for v in component.get("translation", [0.0, 0.0, 0.0]))
        ref_bounds_json = compiled[ref]["geometry_outputs"]["bounds"]
        ref_bounds = Bounds(
            float(ref_bounds_json["min"][0]),
            float(ref_bounds_json["min"][1]),
            float(ref_bounds_json["min"][2]),
            float(ref_bounds_json["max"][0]),
            float(ref_bounds_json["max"][1]),
            float(ref_bounds_json["max"][2]),
        ).translated(translation)  # type: ignore[arg-type]
        bounds_list.append(ref_bounds)
        component_refs.append(
            {
                "instance_id": component["instance_id"],
                "asset_ref": ref,
                "translation": [round(v, 6) for v in translation],
                "bounds": ref_bounds.as_json(),
            }
        )
    bounds = merge_bounds(bounds_list)
    return base_output(asset, bounds) | {
        "operation": "compound_asset",
        "geometry_outputs": {
            "profile_points_2d": [],
            "sections": [],
            "bounds": bounds.as_json(),
            "connector_points": connector_points(bounds, asset["connectors"]),
            "component_refs": component_refs,
            "approx_volume": "sum_components_not_computed_v0",
        },
    }


def base_output(asset: dict[str, Any], bounds: Bounds) -> dict[str, Any]:
    return {
        "schema": "compiled_asset_mill_solid_v0",
        "asset_id": asset["asset_id"],
        "asset_kind": asset["asset_kind"],
        "architectural_role": asset["architectural_role"],
        "generation_use": asset["generation_use"],
        "semantic_outputs": {
            "semantic_tags": asset["semantic_tags"],
            "child_slots": asset["child_slots"],
            "bounds_role_summary": infer_bounds_roles(bounds, asset["semantic_tags"]),
        },
        "connectors": asset["connectors"],
        "no_claims": asset["no_claims"],
        "source_recipe": str(RECIPE_PATH.relative_to(ROOT)),
    }


def infer_bounds_roles(bounds: Bounds, semantic_tags: list[str]) -> dict[str, Any]:
    width = bounds.max_x - bounds.min_x
    depth = bounds.max_y - bounds.min_y
    height = bounds.max_z - bounds.min_z
    return {
        "dimensions": {
            "width_x": round(width, 6),
            "depth_y": round(depth, 6),
            "height_z": round(height, 6),
        },
        "can_block_movement": "blocked" in semantic_tags or "solid_wall" in semantic_tags,
        "can_provide_cover": "cover" in semantic_tags or "cover_light" in semantic_tags,
        "can_be_walkable": "walkable" in semantic_tags,
        "can_mark_route": "route" in semantic_tags or "vertical_transition" in semantic_tags,
    }


def validate_asset(asset: dict[str, Any]) -> None:
    require_fields(
        asset,
        [
            "asset_id",
            "asset_kind",
            "operation",
            "architectural_role",
            "generation_use",
            "semantic_tags",
            "connectors",
            "child_slots",
            "no_claims",
        ],
    )
    validate_no_claims(asset)
    if asset["operation"] == "extrude":
        require_fields(asset, ["profile", "height", "axis"])
    elif asset["operation"] == "loft_sections":
        require_fields(asset, ["sections", "axis"])
    elif asset["operation"] == "compound_asset":
        require_fields(asset, ["components"])
    else:
        fail(f"{asset['asset_id']} unsupported operation {asset['operation']}")


def write_outputs(compiled: dict[str, dict[str, Any]]) -> dict[str, str]:
    paths: dict[str, str] = {}
    for asset_id, data in compiled.items():
        out = SOLID_DIR / f"{asset_id}.json"
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        paths[asset_id] = str(out.relative_to(ROOT))
    return paths


def write_index(compiled: dict[str, dict[str, Any]], paths: dict[str, str]) -> Path:
    index = {
        "schema": "asset_mill_compiled_index_v0",
        "created_at_utc": now_iso(),
        "source_recipe": str(RECIPE_PATH.relative_to(ROOT)),
        "asset_count": len(compiled),
        "assets": [
            {
                "asset_id": asset_id,
                "asset_kind": data["asset_kind"],
                "architectural_role": data["architectural_role"],
                "generation_use": data["generation_use"],
                "semantic_tags": data["semantic_outputs"]["semantic_tags"],
                "compiled_path": paths[asset_id],
            }
            for asset_id, data in compiled.items()
        ],
        "rules": {
            "no_images": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_structural_claims": True,
            "data_first": True,
        },
    }
    out = OUT_ROOT / "asset_mill_compiled_index_v0.json"
    out.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return out


def write_report(compiled: dict[str, dict[str, Any]], paths: dict[str, str], index_path: Path) -> Path:
    lines = [
        "# Asset Mill Solid Profiles v0",
        "",
        "This pass replaces visual-first shape work with measured data-first solid definitions.",
        "",
        "```text",
        "flat profile -> extrude / loft / compound -> measured solid JSON -> future Blender/engine realization",
        "```",
        "",
        "No images, meshes, Blender files, production approval, fabrication claims, or structural safety claims are created.",
        "",
        "## Outputs",
        "",
        f"- Source recipes: `{RECIPE_PATH.relative_to(ROOT)}`",
        f"- Compiled index: `{index_path.relative_to(ROOT)}`",
        f"- Compiled solids: `{SOLID_DIR.relative_to(ROOT)}/`",
        "",
        "## Compiled Assets",
        "",
        "| Asset | Kind | Role | Dimensions | Semantics | Output |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for asset_id, data in compiled.items():
        dims = data["semantic_outputs"]["bounds_role_summary"]["dimensions"]
        dim_text = f"{dims['width_x']} x {dims['depth_y']} x {dims['height_z']}"
        semantics = ", ".join(data["semantic_outputs"]["semantic_tags"])
        lines.append(f"| `{asset_id}` | {data['asset_kind']} | {data['architectural_role']} | {dim_text} | {semantics} | `{paths[asset_id]}` |")

    lines.extend(
        [
            "",
            "## Why This Is Useful",
            "",
            "- Each asset is a measured, parameterized construction object rather than a preview image.",
            "- Connectors expose where assets attach to floors, ceilings, neighbors, rails, panels, and future graph plots.",
            "- Semantic tags make later map/topology use possible: walkable, blocked, cover, support, route, barrier, landmark.",
            "- Compound assets prove the low-cost path: build useful objects from dumb solids before touching harder geometry.",
            "",
            "## Recommended Next Goal",
            "",
            "Add `plot_to_solid_assignment_v0`: a graph plot node chooses one of these compiled assets by role and dimensions, then emits placement data.",
            "",
        ]
    )
    out = REPORT_DIR / "asset_mill_solid_profiles_v0_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_receipt(compiled: dict[str, dict[str, Any]], paths: dict[str, str], index_path: Path, report_path: Path) -> Path:
    receipt = {
        "receipt_type": "asset_mill_solid_profiles_v0",
        "created_at_utc": now_iso(),
        "asset_count": len(compiled),
        "scope": "measured profile extrusion / loft / compound asset definitions",
        "files_created": {
            "contract": "contracts/asset_mill_solid_recipe_v0.json",
            "source_recipe": str(RECIPE_PATH.relative_to(ROOT)),
            "compiled_index": str(index_path.relative_to(ROOT)),
            "compiled_solids": paths,
            "report": str(report_path.relative_to(ROOT)),
            "receipt": "goal/receipts/asset_mill_solid_profiles_v0.receipt.json",
        },
        "rules": {
            "no_images": True,
            "no_mesh_files": True,
            "no_blender_files": True,
            "no_production_approval": True,
            "no_structural_claims": True,
            "no_fabrication_claims": True,
            "no_gym_museum_approval": True,
            "data_first": True,
        },
        "recommended_next_goal": "Add plot_to_solid_assignment_v0 so graph plots can request these measured solids by role and dimensions.",
    }
    out = RECEIPT_DIR / "asset_mill_solid_profiles_v0.receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return out


def compile_bundle(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    compiled: dict[str, dict[str, Any]] = {}
    ids = set()
    for asset in bundle["assets"]:
        validate_asset(asset)
        asset_id = asset["asset_id"]
        if asset_id in ids:
            fail(f"duplicate asset_id: {asset_id}")
        ids.add(asset_id)
        operation = asset["operation"]
        if operation == "extrude":
            compiled[asset_id] = compile_primitive(asset)
        elif operation == "loft_sections":
            compiled[asset_id] = compile_loft(asset)
        elif operation == "compound_asset":
            compiled[asset_id] = compile_compound(asset, compiled)
    return compiled


def main() -> None:
    ensure_dirs()
    bundle = load_recipe_bundle()
    compiled = compile_bundle(bundle)
    paths = write_outputs(compiled)
    index_path = write_index(compiled, paths)
    report_path = write_report(compiled, paths, index_path)
    receipt_path = write_receipt(compiled, paths, index_path, report_path)
    print(f"compiled {len(compiled)} asset mill solids")
    print(f"index: {index_path.relative_to(ROOT)}")
    print(f"report: {report_path.relative_to(ROOT)}")
    print(f"receipt: {receipt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
