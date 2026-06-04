#!/usr/bin/env python3
"""Render ASCII dry-runs from compiled gameguy_tool_plan_v0 files.

This script does not import Blender or execute bpy. It consumes the same
compiled tool-plan JSON that the Blender adapter consumes, translates supported
base geometry steps into the donated ascii_blender_dryrun_v0 operation stream,
then renders front/side/top ASCII projections.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DONATED_ASCII_PACKAGE = ROOT / "ascii_blender_dryrun_v0"
DEFAULT_OUT = Path("/tmp/gameguy_tool_plan_ascii_dryrun_v0")

sys.path.insert(0, str(DONATED_ASCII_PACKAGE))

from ascii_blender_dryrun.ascii_backend import AsciiBackend  # noqa: E402
from ascii_blender_dryrun.ops import AddBox, AddCylinder, AddLabel, BuildOp, op_to_dict  # noqa: E402


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


def require_vector(value: Any, field: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        fail(f"{field} must be a {length}-number list")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            fail(f"{field}[{index}] must be a number")
        result.append(float(item))
    return result


def require_step_params(step: dict[str, Any]) -> dict[str, Any]:
    params = step.get("params")
    if not isinstance(params, dict):
        fail(f"{step.get('step_id', '<unknown>')}.params must be an object")
    return params


def alias(step: dict[str, Any]) -> str:
    return str(step.get("step_id") or step.get("tool_id") or "unnamed_step")


def material(params: dict[str, Any]) -> str:
    value = params.get("material_role")
    return value if isinstance(value, str) and value else "stone"


def positive_dimension(value: float) -> float:
    return max(round(value, 6), 0.001)


def bounds_from_vertices(vertices: list[list[float]]) -> tuple[list[float], list[float]]:
    mins = [min(vertex[index] for vertex in vertices) for index in range(3)]
    maxes = [max(vertex[index] for vertex in vertices) for index in range(3)]
    return mins, maxes


def primitive_cube_to_op(step: dict[str, Any]) -> AddBox:
    params = require_step_params(step)
    size = require_vector(params.get("size_m"), f"{alias(step)}.params.size_m", 3)
    location = require_vector(params.get("location_m"), f"{alias(step)}.params.location_m", 3)
    return AddBox(
        alias(step),
        width=positive_dimension(size[0]),
        depth=positive_dimension(size[1]),
        height=positive_dimension(size[2]),
        x=location[0],
        y=location[1],
        z=location[2],
        material=material(params),
    )


def primitive_cylinder_to_op(step: dict[str, Any]) -> AddCylinder:
    params = require_step_params(step)
    radius = float(params.get("radius_m", params.get("radius", 0.1)))
    depth = float(params.get("depth_m", params.get("depth", 0.1)))
    location = require_vector(params.get("location_m"), f"{alias(step)}.params.location_m", 3)
    return AddCylinder(
        alias(step),
        radius=positive_dimension(radius),
        height=positive_dimension(depth),
        x=location[0],
        y=location[1],
        z=location[2],
        vertices=max(4, int(params.get("vertices", 8))),
        material=material(params),
    )


def mesh_from_pydata_to_bbox_op(step: dict[str, Any]) -> AddBox:
    params = require_step_params(step)
    raw_vertices = params.get("vertices")
    if not isinstance(raw_vertices, list) or not raw_vertices:
        fail(f"{alias(step)}.params.vertices must be a non-empty list")
    vertices = [require_vector(vertex, f"{alias(step)}.params.vertices[{index}]", 3) for index, vertex in enumerate(raw_vertices)]
    mins, maxes = bounds_from_vertices(vertices)
    size = [maxes[index] - mins[index] for index in range(3)]
    location = [(mins[index] + maxes[index]) * 0.5 for index in range(3)]
    return AddBox(
        f"{alias(step)}_bbox",
        width=positive_dimension(size[0]),
        depth=positive_dimension(size[1]),
        height=positive_dimension(size[2]),
        x=round(location[0], 6),
        y=round(location[1], 6),
        z=round(location[2], 6),
        material=material(params),
    )


def plan_to_ops(plan: dict[str, Any]) -> tuple[list[BuildOp], dict[str, Any]]:
    if plan.get("schema") != "gameguy_tool_plan_v0":
        fail("plan schema must be gameguy_tool_plan_v0")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        fail("plan.steps must be a list")

    ops: list[BuildOp] = []
    supported: list[str] = []
    approximated: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    for step_value in steps:
        if not isinstance(step_value, dict):
            fail("plan.steps items must be objects")
        tool_id = step_value.get("tool_id")
        if tool_id == "primitive_cube_add":
            ops.append(primitive_cube_to_op(step_value))
            supported.append(alias(step_value))
        elif tool_id == "primitive_cylinder_add":
            ops.append(primitive_cylinder_to_op(step_value))
            supported.append(alias(step_value))
        elif tool_id == "mesh_from_pydata":
            ops.append(mesh_from_pydata_to_bbox_op(step_value))
            supported.append(alias(step_value))
            approximated.append({"step_id": alias(step_value), "reason": "mesh_from_pydata rendered as bounding box in v0"})
        elif tool_id in {
            "modifier_bevel",
            "modifier_boolean",
            "modifier_displace",
            "modifier_array",
            "modifier_mirror",
            "modifier_weighted_normal",
            "modifier_weld",
            "object_join",
            "render_workbench_preview",
            "export_gltf",
            "calculate_bounds",
            "validate_non_manifold",
        }:
            skipped.append({"step_id": alias(step_value), "tool_id": str(tool_id), "reason": "non-primitive effect recorded only in v0"})
        else:
            skipped.append({"step_id": alias(step_value), "tool_id": str(tool_id), "reason": "unsupported dry-run tool in v0"})

    if not ops:
        ops.append(AddLabel("empty_dryrun", "No supported primitive steps", 0.0, 0.0, 0.0))

    report = {
        "schema": "tool_plan_ascii_dryrun_report_v0",
        "plan_schema": plan.get("schema"),
        "plan_id": plan.get("plan_id"),
        "asset_id": plan.get("asset_id"),
        "asset_family": plan.get("asset_family"),
        "style": plan.get("style"),
        "step_count": len(steps),
        "dryrun_op_count": len(ops),
        "supported_step_count": len(supported),
        "approximated_step_count": len(approximated),
        "skipped_step_count": len(skipped),
        "supported_steps": supported,
        "approximated_steps": approximated,
        "skipped_steps": skipped,
        "rules": {
            "consumes_gameguy_tool_plan_v0": True,
            "imports_blender": False,
            "executes_blender": False,
            "uses_donated_ascii_backend": True,
            "renders_supported_primitives_only_in_v0": True,
        },
        "no_claims": {
            "final_blender_equivalence": False,
            "modifier_effects_rendered": False,
            "mesh_export_created": False,
            "render_created": False,
        },
    }
    return ops, report


def write_outputs(plan: dict[str, Any], out: Path, width: int, height: int) -> dict[str, Any]:
    ops, report = plan_to_ops(plan)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dryrun_operation_stream.json").write_text(json.dumps({"ops": [op_to_dict(op) for op in ops]}, indent=2) + "\n", encoding="utf-8")
    backend = AsciiBackend(width=width, height=height)
    previews = {}
    for projection in ("front", "side", "top"):
        path = out / f"{projection}_preview.txt"
        path.write_text(backend.render_projection(ops, projection) + "\n", encoding="utf-8")
        previews[projection] = str(path)
    report["outputs"] = {
        "operation_stream": str(out / "dryrun_operation_stream.json"),
        "front_preview": previews["front"],
        "side_preview": previews["side"],
        "top_preview": previews["top"],
    }
    (out / "ascii_dryrun_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render ASCII dry-run previews from a compiled Blender tool plan.")
    parser.add_argument("--plan", type=Path, required=True, help="Compiled gameguy_tool_plan_v0 JSON.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--width", type=int, default=96)
    parser.add_argument("--height", type=int, default=72)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = load_json(args.plan)
    report = write_outputs(plan, args.out, args.width, args.height)
    print(
        "PASS tool-plan ASCII dry-run: "
        f"{report['plan_id']} ops={report['dryrun_op_count']} "
        f"supported={report['supported_step_count']} skipped={report['skipped_step_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
