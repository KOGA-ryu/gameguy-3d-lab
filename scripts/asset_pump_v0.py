#!/usr/bin/env python3
"""Pump source asset recipes into deterministic geometry JSON.

This is the clean core of the 3D lab:

source recipe -> profile/operation compiler -> asset mesh JSON -> manifest

It intentionally does not write workflow reports, receipts, Blender files,
renders, or repo-local generated folders.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "data" / "architecture" / "asset_mill" / "recipes" / "simple_solids_v0.json"
DEFAULT_OUT = Path("/tmp/gameguy_asset_pump_v0")
FALSE_CLAIMS = {
    "production_approval": False,
    "structural_safety": False,
    "fabrication_ready": False,
    "gym_museum_approval": False,
}


@dataclass(frozen=True)
class Mesh:
    vertices: list[list[float]]
    faces: list[list[int]]

    def translated(self, offset: list[float]) -> "Mesh":
        return Mesh(
            vertices=[
                [
                    round(vertex[0] + offset[0], 6),
                    round(vertex[1] + offset[1], 6),
                    round(vertex[2] + offset[2], 6),
                ]
                for vertex in self.vertices
            ],
            faces=[face[:] for face in self.faces],
        )


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def finite_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        fail(f"{field} must be a finite number")
    return float(value)


def positive_float(value: Any, field: str) -> float:
    number = finite_float(value, field)
    if number <= 0.0:
        fail(f"{field} must be positive")
    return number


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def validate_claims(asset: dict[str, Any]) -> None:
    if asset.get("no_claims") != FALSE_CLAIMS:
        fail(f"{asset.get('asset_id', '<unknown>')} no_claims must exactly match false claim flags")


def polygon_points(sides: int, radius: float) -> list[list[float]]:
    if sides < 3:
        fail("polygon sides must be >= 3")
    return [
        [
            round(math.cos(math.tau * index / sides) * radius, 6),
            round(math.sin(math.tau * index / sides) * radius, 6),
        ]
        for index in range(sides)
    ]


def capsule_points(length: float, radius: float, segments: int) -> list[list[float]]:
    if segments < 6:
        fail("capsule segments must be >= 6")
    half_straight = max(length * 0.5 - radius, 0.001)
    half_segments = max(segments // 2, 3)
    points: list[list[float]] = []
    for index in range(half_segments + 1):
        angle = -math.pi * 0.5 + math.pi * index / half_segments
        points.append([round(half_straight + math.cos(angle) * radius, 6), round(math.sin(angle) * radius, 6)])
    for index in range(half_segments + 1):
        angle = math.pi * 0.5 + math.pi * index / half_segments
        points.append([round(-half_straight + math.cos(angle) * radius, 6), round(math.sin(angle) * radius, 6)])
    return points


def profile_points(profile: dict[str, Any]) -> list[list[float]]:
    profile_type = require_string(profile.get("type"), "profile.type")
    params = require_object(profile.get("params", {}), "profile.params")
    if profile_type == "rectangle":
        half_width = positive_float(params.get("width"), "profile.params.width") * 0.5
        half_depth = positive_float(params.get("depth"), "profile.params.depth") * 0.5
        return [[-half_width, -half_depth], [half_width, -half_depth], [half_width, half_depth], [-half_width, half_depth]]
    if profile_type == "square":
        half_size = positive_float(params.get("size"), "profile.params.size") * 0.5
        return [[-half_size, -half_size], [half_size, -half_size], [half_size, half_size], [-half_size, half_size]]
    if profile_type == "circle":
        return polygon_points(int(params.get("segments", 24)), positive_float(params.get("radius"), "profile.params.radius"))
    if profile_type == "triangle":
        half_width = positive_float(params.get("width"), "profile.params.width") * 0.5
        half_depth = positive_float(params.get("depth"), "profile.params.depth") * 0.5
        return [[-half_width, -half_depth], [half_width, -half_depth], [0.0, half_depth]]
    if profile_type == "trapezoid":
        bottom = positive_float(params.get("bottom_width"), "profile.params.bottom_width") * 0.5
        top = positive_float(params.get("top_width"), "profile.params.top_width") * 0.5
        half_depth = positive_float(params.get("depth"), "profile.params.depth") * 0.5
        return [[-bottom, -half_depth], [bottom, -half_depth], [top, half_depth], [-top, half_depth]]
    if profile_type == "regular_polygon":
        return polygon_points(int(params.get("sides")), positive_float(params.get("radius"), "profile.params.radius"))
    if profile_type == "octagon":
        return polygon_points(8, positive_float(params.get("radius"), "profile.params.radius"))
    if profile_type == "capsule":
        return capsule_points(
            positive_float(params.get("length"), "profile.params.length"),
            positive_float(params.get("radius"), "profile.params.radius"),
            int(params.get("segments", 12)),
        )
    fail(f"unsupported profile type: {profile_type}")


def extrude_mesh(points: list[list[float]], height: float) -> Mesh:
    if len(points) < 3:
        fail("extrude requires at least 3 profile points")
    bottom = [[round(x, 6), round(y, 6), 0.0] for x, y in points]
    top = [[round(x, 6), round(y, 6), round(height, 6)] for x, y in points]
    vertices = bottom + top
    count = len(points)
    faces: list[list[int]] = [list(reversed(range(count))), list(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append([index, nxt, nxt + count, index + count])
    return Mesh(vertices=vertices, faces=faces)


def loft_mesh(sections: list[dict[str, Any]]) -> Mesh:
    if len(sections) < 2:
        fail("loft_sections requires at least two sections")
    rings: list[list[list[float]]] = []
    for index, section in enumerate(sections):
        at = finite_float(section.get("at"), f"sections[{index}].at")
        points = profile_points(require_object(section.get("profile"), f"sections[{index}].profile"))
        rings.append([[round(x, 6), round(y, 6), round(at, 6)] for x, y in points])
    ring_size = len(rings[0])
    if any(len(ring) != ring_size for ring in rings):
        fail("loft_sections requires matching profile vertex counts")
    vertices = [vertex for ring in rings for vertex in ring]
    faces: list[list[int]] = [list(reversed(range(ring_size)))]
    last_start = (len(rings) - 1) * ring_size
    faces.append(list(range(last_start, last_start + ring_size)))
    for ring_index in range(len(rings) - 1):
        start = ring_index * ring_size
        next_start = (ring_index + 1) * ring_size
        for vertex_index in range(ring_size):
            nxt = (vertex_index + 1) % ring_size
            faces.append([start + vertex_index, start + nxt, next_start + nxt, next_start + vertex_index])
    return Mesh(vertices=vertices, faces=faces)


def bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    if not vertices:
        fail("cannot calculate bounds for empty mesh")
    return {
        "min": [round(min(vertex[axis] for vertex in vertices), 6) for axis in range(3)],
        "max": [round(max(vertex[axis] for vertex in vertices), 6) for axis in range(3)],
    }


def dimensions(bounds_m: dict[str, list[float]]) -> dict[str, float]:
    return {
        "width": round(bounds_m["max"][0] - bounds_m["min"][0], 6),
        "depth": round(bounds_m["max"][1] - bounds_m["min"][1], 6),
        "height": round(bounds_m["max"][2] - bounds_m["min"][2], 6),
    }


def connector_points(bounds_m: dict[str, list[float]], names: list[str]) -> list[dict[str, Any]]:
    min_x, min_y, min_z = bounds_m["min"]
    max_x, max_y, max_z = bounds_m["max"]
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    cz = (min_z + max_z) * 0.5
    table = {
        "north": ([cx, max_y, cz], [0.0, 1.0, 0.0]),
        "south": ([cx, min_y, cz], [0.0, -1.0, 0.0]),
        "east": ([max_x, cy, cz], [1.0, 0.0, 0.0]),
        "west": ([min_x, cy, cz], [-1.0, 0.0, 0.0]),
        "floor": ([cx, cy, min_z], [0.0, 0.0, -1.0]),
        "ceiling": ([cx, cy, max_z], [0.0, 0.0, 1.0]),
        "radial": ([cx, cy, cz], [0.0, 0.0, 1.0]),
    }
    connectors: list[dict[str, Any]] = []
    for name in names:
        if name not in table:
            continue
        position, direction = table[name]
        connectors.append(
            {
                "connector_id": name,
                "position_m": [round(value, 6) for value in position],
                "direction": direction,
            }
        )
    return connectors


def merged_mesh(parts: list[Mesh]) -> Mesh:
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for part in parts:
        offset = len(vertices)
        vertices.extend(part.vertices)
        faces.extend([[index + offset for index in face] for face in part.faces])
    return Mesh(vertices=vertices, faces=faces)


def require_asset_core(asset: dict[str, Any]) -> None:
    for field in (
        "asset_id",
        "asset_kind",
        "operation",
        "architectural_role",
        "generation_use",
        "semantic_tags",
        "connectors",
        "no_claims",
    ):
        if field not in asset:
            fail(f"{asset.get('asset_id', '<unknown>')} missing {field}")
    validate_claims(asset)


def compile_asset(asset: dict[str, Any], compiled: dict[str, dict[str, Any]]) -> dict[str, Any]:
    require_asset_core(asset)
    asset_id = require_string(asset["asset_id"], "asset_id")
    operation = require_string(asset["operation"], f"{asset_id}.operation")
    components: list[dict[str, Any]] = []
    if operation == "extrude":
        mesh = extrude_mesh(profile_points(require_object(asset.get("profile"), f"{asset_id}.profile")), positive_float(asset.get("height"), f"{asset_id}.height"))
    elif operation == "loft_sections":
        mesh = loft_mesh(require_list(asset.get("sections"), f"{asset_id}.sections"))
    elif operation == "compound_asset":
        parts: list[Mesh] = []
        for component in require_list(asset.get("components"), f"{asset_id}.components"):
            component = require_object(component, f"{asset_id}.component")
            ref = require_string(component.get("asset_ref"), f"{asset_id}.component.asset_ref")
            if ref not in compiled:
                fail(f"{asset_id} references unknown or later asset: {ref}")
            translation = [finite_float(value, f"{asset_id}.{ref}.translation") for value in component.get("translation", [0.0, 0.0, 0.0])]
            source_mesh = compiled[ref]["mesh"]
            part = Mesh(vertices=source_mesh["vertices"], faces=source_mesh["faces"]).translated(translation)
            parts.append(part)
            components.append(
                {
                    "instance_id": require_string(component.get("instance_id"), f"{asset_id}.component.instance_id"),
                    "asset_ref": ref,
                    "translation_m": [round(value, 6) for value in translation],
                }
            )
        mesh = merged_mesh(parts)
    else:
        fail(f"{asset_id} unsupported operation: {operation}")

    bounds_m = bounds(mesh.vertices)
    return {
        "schema": "gameguy_asset_v0",
        "asset_id": asset_id,
        "source_operation": operation,
        "asset_kind": asset["asset_kind"],
        "architectural_role": asset["architectural_role"],
        "generation_use": asset["generation_use"],
        "semantic_tags": asset["semantic_tags"],
        "connectors": connector_points(bounds_m, require_list(asset["connectors"], f"{asset_id}.connectors")),
        "components": components,
        "bounds_m": bounds_m,
        "dimensions_m": dimensions(bounds_m),
        "mesh": {
            "coordinate_space": "local_xyz_m",
            "vertices": mesh.vertices,
            "faces": mesh.faces,
        },
        "no_claims": asset["no_claims"],
    }


def load_bundle(path: Path) -> dict[str, Any]:
    bundle = load_json(path)
    if bundle.get("schema") != "asset_mill_recipe_bundle_v0":
        fail("bundle schema must be asset_mill_recipe_bundle_v0")
    assets = require_list(bundle.get("assets"), "assets")
    if not assets:
        fail("bundle assets must not be empty")
    return bundle


def write_outputs(compiled: dict[str, dict[str, Any]], out_root: Path, source_bundle: Path) -> None:
    asset_dir = out_root / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    manifest_assets = []
    for asset_id, asset in compiled.items():
        path = asset_dir / f"{asset_id}.json"
        path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
        manifest_assets.append(
            {
                "asset_id": asset_id,
                "path": str(path.relative_to(out_root)),
                "asset_kind": asset["asset_kind"],
                "architectural_role": asset["architectural_role"],
                "dimensions_m": asset["dimensions_m"],
                "vertex_count": len(asset["mesh"]["vertices"]),
                "face_count": len(asset["mesh"]["faces"]),
            }
        )
    manifest = {
        "schema": "gameguy_asset_pump_manifest_v0",
        "source_bundle": repo_display_path(source_bundle),
        "asset_count": len(compiled),
        "assets": manifest_assets,
        "rules": {
            "no_reports": True,
            "no_receipts": True,
            "no_blender": True,
            "no_media": True,
            "no_mesh_export_files": True,
        },
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def repo_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pump source asset recipes into deterministic geometry JSON.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true", help="Delete the output folder before writing. Refuses to clean outside /tmp.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle_path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    out_root = args.out
    if args.clean:
        resolved = out_root.resolve()
        if not (str(resolved).startswith("/tmp/") or str(resolved).startswith("/private/tmp/")):
            fail("--clean only deletes output folders under /tmp")
        shutil.rmtree(resolved, ignore_errors=True)
    if out_root.exists() and any(out_root.iterdir()):
        fail(f"output folder is not empty: {out_root}. Use --clean for /tmp outputs or choose a new folder.")

    bundle = load_bundle(bundle_path)
    compiled: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for asset in require_list(bundle["assets"], "assets"):
        asset = require_object(asset, "asset")
        asset_id = require_string(asset.get("asset_id"), "asset.asset_id")
        if asset_id in seen:
            fail(f"duplicate asset_id: {asset_id}")
        seen.add(asset_id)
        compiled[asset_id] = compile_asset(asset, compiled)

    write_outputs(compiled, out_root, bundle_path)
    total_vertices = sum(len(asset["mesh"]["vertices"]) for asset in compiled.values())
    total_faces = sum(len(asset["mesh"]["faces"]) for asset in compiled.values())
    print(f"pumped assets={len(compiled)} vertices={total_vertices} faces={total_faces} out={out_root}")


if __name__ == "__main__":
    main()
