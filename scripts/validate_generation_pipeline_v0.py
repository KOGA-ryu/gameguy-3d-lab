#!/usr/bin/env python3
"""Validate the deterministic 3D generation pipeline.

This is an orchestration gate. It runs the canonical source, pump, tool-plan,
adapter, audit, and output-location checks without adding source design logic.
Generated artifacts are written under /tmp by the individual tools.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
TOOL_PLAN_OUT = Path("/tmp/gameguy_blender_tool_plan_v0")
TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_tool_plan_execution_v0")
FENCE_POST_TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_fence_post_tool_plan_execution_v0")
RAIL_SEGMENT_TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_rail_segment_tool_plan_execution_v0")
COLUMN_TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_column_tool_plan_execution_v0")
WINDOW_FRAME_TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_window_frame_tool_plan_execution_v0")
DOOR_FRAME_TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_door_frame_tool_plan_execution_v0")
GUARD_PANEL_TOOL_PLAN_EXECUTION_OUT = Path("/tmp/gameguy_blender_guard_panel_tool_plan_execution_v0")
SIMPLE_ASSET_OUT = Path("/tmp/gameguy_asset_pump_v0")
MEASURED_ASSET_OUT = Path("/tmp/gameguy_measured_asset_pump_v0")
SECTION_STACK_ASSET_OUT = Path("/tmp/gameguy_section_stack_asset_pump_v0")
BLOCKY_COLUMN_ASSET_OUT = Path("/tmp/gameguy_blocky_column_asset_pump_v0")
BLOCKY_SHAPE_ASSET_OUT = Path("/tmp/gameguy_blocky_shape_grammar_asset_pump_v0")
FORBIDDEN_OUTPUT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".blend",
    ".blend1",
    ".obj",
    ".gltf",
    ".glb",
    ".fbx",
}


@dataclass(frozen=True)
class CommandStep:
    label: str
    command: list[str]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def display_path_under(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def command_display(command: list[str]) -> str:
    return " ".join(command)


def load_json_file(path: Path) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {repo_path(path)}: line {exc.lineno} column {exc.colno}: {exc.msg}")


def validate_json_tree() -> int:
    roots = ("data", "contracts", "docs", "geometry_dictionary", "workflow")
    count = 0
    for root_name in roots:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.json")):
            load_json_file(path)
            count += 1
    return count


def find_pattern_lab_paths(root: Path = ROOT) -> list[str]:
    paths = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if "pattern_lab_2d" in str(path.relative_to(root)):
            paths.append(display_path_under(root, path))
    return sorted(paths)


def find_forbidden_output_files(root: Path = ROOT) -> list[str]:
    files = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file() and path.suffix.lower() in FORBIDDEN_OUTPUT_SUFFIXES:
            files.append(display_path_under(root, path))
    return sorted(files)


def python_script(script: str, *args: str | Path) -> list[str]:
    return [sys.executable, script, *(str(arg) for arg in args)]


def build_command_steps(*, include_blender: bool, skip_unit_tests: bool, blender_path: Path) -> list[CommandStep]:
    plan_path = TOOL_PLAN_OUT / "plans" / "gothic_stone_banister_post_tool_plan_v0_compiled.json"
    fence_post_plan_path = TOOL_PLAN_OUT / "plans" / "gothic_stone_fence_post_tool_plan_v0_compiled.json"
    rail_segment_plan_path = TOOL_PLAN_OUT / "plans" / "gothic_stone_rail_segment_tool_plan_v0_compiled.json"
    column_plan_path = TOOL_PLAN_OUT / "plans" / "gothic_stone_column_tool_plan_v0_compiled.json"
    window_frame_plan_path = TOOL_PLAN_OUT / "plans" / "gothic_stone_window_frame_tool_plan_v0_compiled.json"
    door_frame_plan_path = TOOL_PLAN_OUT / "plans" / "gothic_stone_door_frame_tool_plan_v0_compiled.json"
    guard_panel_plan_path = TOOL_PLAN_OUT / "plans" / "gothic_panel_guard_tool_plan_v0_compiled.json"
    steps = [
        CommandStep("python_compile", [sys.executable, "-m", "py_compile", *[str(path) for path in sorted((ROOT / "scripts").glob("*.py"))]]),
        CommandStep("generation_registry_validate", python_script("scripts/validate_asset_generation_registry_v0.py")),
        CommandStep("reference_dissection_validate", python_script("scripts/validate_reference_dissection_packet_v0.py")),
        CommandStep("measured_molding_profile_validate", python_script("scripts/validate_measured_molding_profiles_v0.py")),
        CommandStep("railing_detail_profile_validate", python_script("scripts/validate_railing_detail_profiles_v0.py")),
    ]
    if not skip_unit_tests:
        steps.append(CommandStep("unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]))
    steps.extend(
        [
            CommandStep("tool_plan_compile_validate_only", python_script("scripts/compile_blender_tool_plan_v0.py", "--validate-only")),
            CommandStep("tool_plan_compile", python_script("scripts/compile_blender_tool_plan_v0.py", "--clean", "--out", TOOL_PLAN_OUT)),
            CommandStep("tool_plan_validate", python_script("scripts/validate_gameguy_tool_plan_v0.py", "--manifest", TOOL_PLAN_OUT / "manifest.json")),
            CommandStep("blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", plan_path, "--validate-only")),
            CommandStep("fence_post_blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", fence_post_plan_path, "--validate-only")),
            CommandStep("rail_segment_blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", rail_segment_plan_path, "--validate-only")),
            CommandStep("column_blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", column_plan_path, "--validate-only")),
            CommandStep("window_frame_blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", window_frame_plan_path, "--validate-only")),
            CommandStep("door_frame_blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", door_frame_plan_path, "--validate-only")),
            CommandStep("guard_panel_blender_adapter_validate_only", python_script("scripts/execute_blender_tool_plan_v0.py", "--plan", guard_panel_plan_path, "--validate-only")),
        ]
    )
    if include_blender:
        steps.extend(
            [
                CommandStep(
                    "blender_execute_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(plan_path),
                        "--out",
                        str(TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                    ),
                ),
                CommandStep(
                    "blender_execute_fence_post_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(fence_post_plan_path),
                        "--out",
                        str(FENCE_POST_TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "fence_post_blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        FENCE_POST_TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                    ),
                ),
                CommandStep(
                    "blender_execute_rail_segment_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(rail_segment_plan_path),
                        "--out",
                        str(RAIL_SEGMENT_TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "rail_segment_blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        RAIL_SEGMENT_TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                    ),
                ),
                CommandStep(
                    "blender_execute_column_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(column_plan_path),
                        "--out",
                        str(COLUMN_TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "column_blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        COLUMN_TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                    ),
                ),
                CommandStep(
                    "blender_execute_window_frame_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(window_frame_plan_path),
                        "--out",
                        str(WINDOW_FRAME_TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "window_frame_blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        WINDOW_FRAME_TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                    ),
                ),
                CommandStep(
                    "blender_execute_door_frame_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(door_frame_plan_path),
                        "--out",
                        str(DOOR_FRAME_TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "door_frame_blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        DOOR_FRAME_TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                    ),
                ),
                CommandStep(
                    "blender_execute_guard_panel_tool_plan",
                    [
                        str(blender_path),
                        "--background",
                        "--python",
                        "scripts/execute_blender_tool_plan_v0.py",
                        "--",
                        "--plan",
                        str(guard_panel_plan_path),
                        "--out",
                        str(GUARD_PANEL_TOOL_PLAN_EXECUTION_OUT),
                        "--render",
                        "--export",
                    ],
                ),
                CommandStep(
                    "guard_panel_blender_execution_report_validate",
                    python_script(
                        "scripts/validate_blender_tool_plan_execution_report_v0.py",
                        "--report",
                        GUARD_PANEL_TOOL_PLAN_EXECUTION_OUT / "tool_plan_execution_v0_report.json",
                        "--max-non-manifold-edges-before-cleanup",
                        "40",
                    ),
                ),
            ]
        )
    steps.extend(
        [
            CommandStep("tiny_fixture_validate", python_script("scripts/validate_tiny_fixture_v0.py")),
            CommandStep("measured_source_validate", python_script("scripts/validate_measured_component_source_v0.py")),
            CommandStep("simple_asset_pump", python_script("scripts/asset_pump_v0.py", "--clean", "--out", SIMPLE_ASSET_OUT)),
            CommandStep("simple_asset_validate", python_script("scripts/validate_gameguy_asset_v0.py", "--manifest", SIMPLE_ASSET_OUT / "manifest.json")),
            CommandStep("simple_asset_adapter_validate", python_script("scripts/export_blender_asset_preview_v0.py", "--manifest", SIMPLE_ASSET_OUT / "manifest.json", "--validate-only")),
            CommandStep(
                "measured_asset_pump",
                python_script(
                    "scripts/asset_pump_v0.py",
                    "--bundle",
                    "data/architecture/asset_mill/recipes/measured_components_v0.json",
                    "--clean",
                    "--out",
                    MEASURED_ASSET_OUT,
                ),
            ),
            CommandStep("measured_asset_validate", python_script("scripts/validate_gameguy_asset_v0.py", "--manifest", MEASURED_ASSET_OUT / "manifest.json")),
            CommandStep(
                "measured_asset_adapter_validate",
                python_script("scripts/export_blender_measured_components_preview_v0.py", "--manifest", MEASURED_ASSET_OUT / "manifest.json", "--validate-only"),
            ),
            CommandStep(
                "section_stack_asset_pump",
                python_script(
                    "scripts/asset_pump_v0.py",
                    "--bundle",
                    "data/architecture/asset_mill/recipes/section_stack_assets_v0.json",
                    "--clean",
                    "--out",
                    SECTION_STACK_ASSET_OUT,
                ),
            ),
            CommandStep("section_stack_asset_validate", python_script("scripts/validate_gameguy_asset_v0.py", "--manifest", SECTION_STACK_ASSET_OUT / "manifest.json")),
            CommandStep(
                "blocky_column_asset_pump",
                python_script(
                    "scripts/asset_pump_v0.py",
                    "--bundle",
                    "data/architecture/asset_mill/recipes/blocky_column_assets_v0.json",
                    "--clean",
                    "--out",
                    BLOCKY_COLUMN_ASSET_OUT,
                ),
            ),
            CommandStep("blocky_column_asset_validate", python_script("scripts/validate_gameguy_asset_v0.py", "--manifest", BLOCKY_COLUMN_ASSET_OUT / "manifest.json")),
            CommandStep(
                "blocky_shape_asset_pump",
                python_script(
                    "scripts/asset_pump_v0.py",
                    "--bundle",
                    "data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json",
                    "--clean",
                    "--out",
                    BLOCKY_SHAPE_ASSET_OUT,
                ),
            ),
            CommandStep("blocky_shape_asset_validate", python_script("scripts/validate_gameguy_asset_v0.py", "--manifest", BLOCKY_SHAPE_ASSET_OUT / "manifest.json")),
            CommandStep("script_orbit_audit", python_script("scripts/audit_script_orbit_v0.py")),
        ]
    )
    return steps


def run_command_step(step: CommandStep) -> dict[str, Any]:
    completed = subprocess.run(step.command, cwd=ROOT, capture_output=True, text=True)
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        fail(f"{step.label} failed: {command_display(step.command)}")
    return {
        "label": step.label,
        "command": command_display(step.command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
    }


def validate_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    if args.include_blender and not args.blender.exists():
        fail(f"missing Blender executable: {args.blender}")
    json_file_count = validate_json_tree()
    command_results = []
    for step in build_command_steps(include_blender=args.include_blender, skip_unit_tests=args.skip_unit_tests, blender_path=args.blender):
        command_results.append(run_command_step(step))
    pattern_paths = find_pattern_lab_paths()
    if pattern_paths:
        fail(f"pattern_lab_2d paths are not allowed: {pattern_paths}")
    forbidden_outputs = find_forbidden_output_files()
    if forbidden_outputs:
        fail(f"media/mesh output files are not allowed in repo: {forbidden_outputs}")
    return {
        "schema": "gameguy_3d_generation_pipeline_validation_v0",
        "include_blender": bool(args.include_blender),
        "unit_tests_run": not bool(args.skip_unit_tests),
        "json_file_count": json_file_count,
        "command_count": len(command_results),
        "commands": command_results,
        "pattern_lab_path_count": len(pattern_paths),
        "repo_media_mesh_output_count": len(forbidden_outputs),
        "rules": {
            "generated_outputs_in_repo": False,
            "blender_is_adapter_layer": True,
            "source_recipes_compile_to_deterministic_json": True,
            "quality_validation_gate": bool(args.include_blender),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the deterministic 3D generation pipeline.")
    parser.add_argument("--include-blender", action="store_true", help="Run Blender execution and validate the execution report.")
    parser.add_argument("--blender", type=Path, default=DEFAULT_BLENDER, help="Blender executable used with --include-blender.")
    parser.add_argument("--skip-unit-tests", action="store_true", help="Skip `python -m unittest discover -s tests` inside this orchestration gate.")
    parser.add_argument("--json-report", type=Path, help="Optional path for a machine-readable validation report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_pipeline(args)
    if args.json_report:
        report_path = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS generation pipeline validation: "
        f"commands={result['command_count']} json={result['json_file_count']} "
        f"include_blender={str(result['include_blender']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
