#!/usr/bin/env python3
"""Export a Blender-importable OBJ for the low-poly character mannequin.

The recipe owns the character proportions and named body segments. This script
only validates that source recipe and emits a simple OBJ/MTL blockout that can
be imported into Blender when Blender is not available in the current shell.
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
DEFAULT_RECIPE = ROOT / "data" / "characters" / "low_poly_mannequin" / (
    "low_poly_character_mannequin_v0.json"
)
DEFAULT_OUT = Path("/tmp/gameguy_low_poly_character_mannequin_v0")
EXPECTED_SCHEMA = "low_poly_character_mannequin_recipe_v0"
SUPPORTED_PRIMITIVES = {"ellipsoid", "capsule", "box"}


Vector = tuple[float, float, float]
Face = tuple[int, ...]


@dataclass(frozen=True)
class MeshObject:
    name: str
    material: str
    vertices: list[Vector]
    faces: list[Face]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"JSON must be an object: {path}")
    return data


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{field} must be a list")
    return value


def require_vector(value: Any, field: str, length: int = 3) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    result: list[float] = []
    for index, item in enumerate(value):
        if not finite_number(item):
            fail(f"{field}[{index}] must be a finite number")
        result.append(float(item))
    return result


def require_positive(value: Any, field: str) -> float:
    if not finite_number(value) or float(value) <= 0:
        fail(f"{field} must be a positive finite number")
    return float(value)


def require_hex_color(value: Any, field: str) -> str:
    text = require_string(value, field)
    if len(text) != 7 or not text.startswith("#"):
        fail(f"{field} must be #RRGGBB")
    try:
        int(text[1:], 16)
    except ValueError:
        fail(f"{field} must be #RRGGBB")
    return text


def validate_recipe(recipe: dict[str, Any], recipe_path: Path) -> dict[str, Any]:
    if recipe.get("schema") != EXPECTED_SCHEMA:
        fail(f"{recipe_path} schema must be {EXPECTED_SCHEMA}")
    asset_id = require_string(recipe.get("asset_id"), "asset_id")
    require_string(recipe.get("asset_family"), "asset_family")
    require_string(recipe.get("style"), "style")

    coordinate_system = require_object(recipe.get("coordinate_system"), "coordinate_system")
    if coordinate_system.get("space") != "local_xyz_m":
        fail("coordinate_system.space must be local_xyz_m")
    if coordinate_system.get("origin") != "feet_center":
        fail("coordinate_system.origin must be feet_center")

    rules = require_object(recipe.get("rules"), "rules")
    for key in (
        "body_parts_are_separate_mesh_objects",
        "front_reference_controls_silhouette",
        "joint_loops_are_reserved_for_later_rigging",
        "obj_export_is_blender_importable",
    ):
        if rules.get(key) is not True:
            fail(f"rules.{key} must be true")

    materials = require_list(recipe.get("materials"), "materials")
    material_names: set[str] = set()
    for index, item in enumerate(materials):
        material = require_object(item, f"materials[{index}]")
        name = require_string(material.get("name"), f"materials[{index}].name")
        if name in material_names:
            fail(f"duplicate material name {name}")
        material_names.add(name)
        require_hex_color(material.get("color_hex"), f"materials[{index}].color_hex")

    parts = require_list(recipe.get("parts"), "parts")
    if len(parts) < 8:
        fail("parts must contain at least 8 body parts")
    part_names: set[str] = set()
    for index, item in enumerate(parts):
        part = require_object(item, f"parts[{index}]")
        name = require_string(part.get("name"), f"parts[{index}].name")
        if name in part_names:
            fail(f"duplicate part name {name}")
        part_names.add(name)
        primitive = require_string(part.get("primitive"), f"{name}.primitive")
        if primitive not in SUPPORTED_PRIMITIVES:
            fail(f"{name}.primitive unsupported: {primitive}")
        material = require_string(part.get("material"), f"{name}.material")
        if material not in material_names:
            fail(f"{name}.material references unknown material {material}")
        if primitive == "ellipsoid":
            require_vector(part.get("center_m"), f"{name}.center_m")
            radii = require_vector(part.get("radii_m"), f"{name}.radii_m")
            if any(radius <= 0 for radius in radii):
                fail(f"{name}.radii_m values must be positive")
            require_segments(part, name, minimum=6)
            require_rings(part, name, minimum=4)
        elif primitive == "capsule":
            start = require_vector(part.get("start_m"), f"{name}.start_m")
            end = require_vector(part.get("end_m"), f"{name}.end_m")
            if vec_length(vec_sub(tuple(end), tuple(start))) <= 1e-6:
                fail(f"{name}.start_m and end_m must be different")
            require_positive(part.get("radius_start_m"), f"{name}.radius_start_m")
            require_positive(part.get("radius_end_m"), f"{name}.radius_end_m")
            require_segments(part, name, minimum=6)
        else:
            require_vector(part.get("center_m"), f"{name}.center_m")
            size = require_vector(part.get("size_m"), f"{name}.size_m")
            if any(value <= 0 for value in size):
                fail(f"{name}.size_m values must be positive")

    return {
        "asset_id": asset_id,
        "material_count": len(materials),
        "part_count": len(parts),
    }


def require_segments(part: dict[str, Any], name: str, *, minimum: int) -> int:
    value = part.get("segments", 8)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{name}.segments must be an integer >= {minimum}")
    return value


def require_rings(part: dict[str, Any], name: str, *, minimum: int) -> int:
    value = part.get("rings", 4)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail(f"{name}.rings must be an integer >= {minimum}")
    return value


def vec_add(a: Vector, b: Vector) -> Vector:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a: Vector, b: Vector) -> Vector:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_mul(a: Vector, scalar: float) -> Vector:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def vec_dot(a: Vector, b: Vector) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_length(a: Vector) -> float:
    return math.sqrt(vec_dot(a, a))


def vec_normalize(a: Vector) -> Vector:
    length = vec_length(a)
    if length <= 1e-9:
        return (0.0, 0.0, 0.0)
    return (a[0] / length, a[1] / length, a[2] / length)


def ellipsoid_mesh(part: dict[str, Any]) -> tuple[list[Vector], list[Face]]:
    center = tuple(require_vector(part.get("center_m"), f"{part['name']}.center_m"))
    radii = tuple(require_vector(part.get("radii_m"), f"{part['name']}.radii_m"))
    segments = require_segments(part, part["name"], minimum=6)
    rings = require_rings(part, part["name"], minimum=4)
    vertices: list[Vector] = []
    faces: list[Face] = []

    vertices.append((center[0], center[1], center[2] + radii[2]))
    ring_indexes: list[list[int]] = []
    for ring in range(1, rings):
        phi = math.pi * ring / rings
        row: list[int] = []
        for segment in range(segments):
            theta = math.tau * segment / segments
            point = (
                center[0] + radii[0] * math.sin(phi) * math.cos(theta),
                center[1] + radii[1] * math.sin(phi) * math.sin(theta),
                center[2] + radii[2] * math.cos(phi),
            )
            row.append(len(vertices))
            vertices.append(round_vec(point))
        ring_indexes.append(row)
    bottom_index = len(vertices)
    vertices.append((center[0], center[1], center[2] - radii[2]))

    first = ring_indexes[0]
    for segment in range(segments):
        faces.append((0, first[(segment + 1) % segments], first[segment]))
    for row_index in range(len(ring_indexes) - 1):
        upper = ring_indexes[row_index]
        lower = ring_indexes[row_index + 1]
        for segment in range(segments):
            faces.append(
                (
                    upper[segment],
                    upper[(segment + 1) % segments],
                    lower[(segment + 1) % segments],
                    lower[segment],
                )
            )
    last = ring_indexes[-1]
    for segment in range(segments):
        faces.append((last[segment], last[(segment + 1) % segments], bottom_index))
    return vertices, faces


def capsule_mesh(part: dict[str, Any]) -> tuple[list[Vector], list[Face]]:
    start = tuple(require_vector(part.get("start_m"), f"{part['name']}.start_m"))
    end = tuple(require_vector(part.get("end_m"), f"{part['name']}.end_m"))
    radius_start = require_positive(part.get("radius_start_m"), f"{part['name']}.radius_start_m")
    radius_end = require_positive(part.get("radius_end_m"), f"{part['name']}.radius_end_m")
    segments = require_segments(part, part["name"], minimum=6)

    axis = vec_sub(end, start)
    direction = vec_normalize(axis)
    ref = (0.0, 0.0, 1.0)
    if abs(vec_dot(direction, ref)) > 0.92:
        ref = (1.0, 0.0, 0.0)
    normal = vec_normalize(vec_cross(direction, ref))
    binormal = vec_normalize(vec_cross(direction, normal))
    vertices: list[Vector] = []
    faces: list[Face] = []
    rings = 3

    start_cap = len(vertices)
    vertices.append(round_vec(vec_sub(start, vec_mul(direction, radius_start * 0.28))))
    ring_indexes: list[list[int]] = []
    for ring in range(rings + 1):
        t = ring / rings
        center = vec_add(start, vec_mul(axis, t))
        radius = radius_start + (radius_end - radius_start) * t
        fullness = 0.72 + 0.28 * math.sin(math.pi * t)
        row: list[int] = []
        for segment in range(segments):
            theta = math.tau * segment / segments
            radial = vec_add(vec_mul(normal, math.cos(theta)), vec_mul(binormal, math.sin(theta)))
            point = vec_add(center, vec_mul(radial, radius * fullness))
            row.append(len(vertices))
            vertices.append(round_vec(point))
        ring_indexes.append(row)
    end_cap = len(vertices)
    vertices.append(round_vec(vec_add(end, vec_mul(direction, radius_end * 0.28))))

    first = ring_indexes[0]
    for segment in range(segments):
        faces.append((start_cap, first[segment], first[(segment + 1) % segments]))
    for row_index in range(len(ring_indexes) - 1):
        upper = ring_indexes[row_index]
        lower = ring_indexes[row_index + 1]
        for segment in range(segments):
            faces.append(
                (
                    upper[segment],
                    upper[(segment + 1) % segments],
                    lower[(segment + 1) % segments],
                    lower[segment],
                )
            )
    last = ring_indexes[-1]
    for segment in range(segments):
        faces.append((last[segment], end_cap, last[(segment + 1) % segments]))
    return vertices, faces


def box_mesh(part: dict[str, Any]) -> tuple[list[Vector], list[Face]]:
    center = tuple(require_vector(part.get("center_m"), f"{part['name']}.center_m"))
    size = tuple(require_vector(part.get("size_m"), f"{part['name']}.size_m"))
    hx, hy, hz = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    cx, cy, cz = center
    vertices = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    return [round_vec(vertex) for vertex in vertices], faces


def round_vec(vertex: Vector) -> Vector:
    return (round(vertex[0], 6), round(vertex[1], 6), round(vertex[2], 6))


def build_mesh_objects(recipe: dict[str, Any]) -> list[MeshObject]:
    objects: list[MeshObject] = []
    for part in recipe["parts"]:
        primitive = part["primitive"]
        if primitive == "ellipsoid":
            vertices, faces = ellipsoid_mesh(part)
        elif primitive == "capsule":
            vertices, faces = capsule_mesh(part)
        elif primitive == "box":
            vertices, faces = box_mesh(part)
        else:
            fail(f"{part['name']}.primitive unsupported: {primitive}")
        objects.append(MeshObject(part["name"], part["material"], vertices, faces))
    return objects


def hex_to_rgb(color_hex: str) -> tuple[float, float, float]:
    value = color_hex.lstrip("#")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
    )


def write_mtl(recipe: dict[str, Any], mtl_path: Path) -> None:
    lines = ["# Generated by scripts/export_low_poly_character_mannequin_v0.py"]
    for material in recipe["materials"]:
        r, g, b = hex_to_rgb(material["color_hex"])
        lines.extend(
            [
                f"newmtl {material['name']}",
                f"Ka {r:.6f} {g:.6f} {b:.6f}",
                f"Kd {r:.6f} {g:.6f} {b:.6f}",
                "Ks 0.050000 0.050000 0.050000",
                "Ns 24.000000",
                "illum 2",
                "",
            ]
        )
    mtl_path.write_text("\n".join(lines), encoding="utf-8")


def write_obj(
    recipe: dict[str, Any],
    objects: list[MeshObject],
    obj_path: Path,
    mtl_path: Path,
) -> None:
    lines = [
        "# Generated by scripts/export_low_poly_character_mannequin_v0.py",
        f"# asset_id {recipe['asset_id']}",
        f"mtllib {mtl_path.name}",
        "",
    ]
    vertex_offset = 1
    for obj in objects:
        lines.append(f"o {obj.name}")
        lines.append(f"usemtl {obj.material}")
        for x, y, z in obj.vertices:
            lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
        for face in obj.faces:
            indexes = " ".join(str(vertex_offset + index) for index in face)
            lines.append(f"f {indexes}")
        lines.append("")
        vertex_offset += len(obj.vertices)
    obj_path.write_text("\n".join(lines), encoding="utf-8")


def make_report(
    recipe: dict[str, Any],
    recipe_path: Path,
    objects: list[MeshObject],
    *,
    generated: bool,
    out_root: Path | None,
) -> dict[str, Any]:
    vertex_count = sum(len(obj.vertices) for obj in objects)
    face_count = sum(len(obj.faces) for obj in objects)
    source_reference = require_object(recipe.get("source_reference"), "source_reference")
    source_image = source_reference.get("turnaround_sheet")
    source_image_path = None
    source_image_exists = False
    if isinstance(source_image, str) and source_image:
        source_image_path = ROOT / source_image
        source_image_exists = source_image_path.exists()
    report: dict[str, Any] = {
        "schema": "low_poly_character_mannequin_obj_report_v0",
        "adapter": "scripts/export_low_poly_character_mannequin_v0.py",
        "source_recipe": str(recipe_path),
        "recipe_schema": recipe["schema"],
        "asset_id": recipe["asset_id"],
        "asset_family": recipe["asset_family"],
        "style": recipe["style"],
        "part_count": len(objects),
        "object_count": len(objects),
        "vertex_count": vertex_count,
        "face_count": face_count,
        "generated_outputs_created": generated,
        "source_reference_image": str(source_image_path) if source_image_path else "",
        "source_reference_image_exists": source_image_exists,
        "rules": {
            "consumes_source_recipe": True,
            "imports_blender": False,
            "executes_blender": False,
            "writes_obj_mtl": generated,
            "body_parts_are_separate_mesh_objects": True,
        },
    }
    if out_root is not None:
        report["out_root"] = str(out_root)
        report["obj_path"] = str(out_root / f"{recipe['asset_id']}.obj")
        report["mtl_path"] = str(out_root / f"{recipe['asset_id']}.mtl")
    return report


def copy_reference_if_available(recipe: dict[str, Any], out_root: Path) -> str:
    source_reference = require_object(recipe.get("source_reference"), "source_reference")
    source_image = source_reference.get("turnaround_sheet")
    if not isinstance(source_image, str) or not source_image:
        return ""
    source_path = ROOT / source_image
    if not source_path.exists():
        return ""
    destination = out_root / source_path.name
    shutil.copy2(source_path, destination)
    return str(destination)


def export_obj_bundle(
    recipe: dict[str, Any],
    recipe_path: Path,
    objects: list[MeshObject],
    out_root: Path,
    json_report: Path | None,
) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    obj_path = out_root / f"{recipe['asset_id']}.obj"
    mtl_path = out_root / f"{recipe['asset_id']}.mtl"
    write_mtl(recipe, mtl_path)
    write_obj(recipe, objects, obj_path, mtl_path)
    copied_reference = copy_reference_if_available(recipe, out_root)
    report = make_report(recipe, recipe_path, objects, generated=True, out_root=out_root)
    if copied_reference:
        report["copied_reference_image"] = copied_reference
    if json_report is not None:
        report_path = json_report
    else:
        report_path = out_root / f"{recipe['asset_id']}_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS low-poly mannequin OBJ export: "
        f"objects={len(objects)} vertices={report['vertex_count']} faces={report['face_count']} "
        f"out={out_root}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the low-poly character mannequin v0 as OBJ/MTL."
    )
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    recipe_path = args.recipe if args.recipe.is_absolute() else ROOT / args.recipe
    recipe = load_json_object(recipe_path)
    validation = validate_recipe(recipe, recipe_path)
    objects = build_mesh_objects(recipe)

    if args.validate_only:
        if args.json_report:
            report_path = (
                args.json_report
                if args.json_report.is_absolute()
                else ROOT / args.json_report
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report = make_report(recipe, recipe_path, objects, generated=False, out_root=None)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS low-poly mannequin recipe validation: "
            f"parts={validation['part_count']} materials={validation['material_count']} "
            f"vertices={sum(len(obj.vertices) for obj in objects)}"
        )
        return 0

    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    report_path = None
    if args.json_report:
        report_path = (
            args.json_report
            if args.json_report.is_absolute()
            else ROOT / args.json_report
        )
    export_obj_bundle(recipe, recipe_path, objects, out_root, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
