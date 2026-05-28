#!/usr/bin/env python3
"""Render multiple review angles for hex_seam_policy_v0.

Run with Blender:

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/blender_hex_seam_policy_angle_review_v0.py

This creates angle renders plus a compact review report for what the seam proof
currently communicates and what needs work before this becomes a terrain asset
compiler.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import blender_hex_seam_policy_v0 as seam  # noqa: E402


OUT_DIR = ROOT / "goal" / "architecture" / "blender_tests"
BLEND_PATH = OUT_DIR / "hex_seam_policy_angle_review_v0.blend"
REPORT_JSON_PATH = OUT_DIR / "hex_seam_policy_angle_review_v0_report.json"
REPORT_MD_PATH = OUT_DIR / "hex_seam_policy_angle_review_v0_report.md"


def output_prefix() -> str:
    return os.environ.get("HEX_ANGLE_OUTPUT_PREFIX", "hex_seam_policy_angle_review_v0").strip() or "hex_seam_policy_angle_review_v0"


def output_paths() -> tuple[str, Path, Path, Path]:
    prefix = output_prefix()
    return (
        prefix,
        OUT_DIR / f"{prefix}.blend",
        OUT_DIR / f"{prefix}_report.json",
        OUT_DIR / f"{prefix}_report.md",
    )


def selected_graph_path() -> Path:
    graph_id = os.environ.get("HEX_GRAPH_ID", "").strip()
    if graph_id:
        path = seam.GRAPH_DIR / f"{graph_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"requested HEX_GRAPH_ID not found: {path}")
        return path
    graph_paths = sorted(seam.GRAPH_DIR.glob("*.json"))
    if not graph_paths:
        raise FileNotFoundError(f"no hex plot vertex graphs found in {seam.GRAPH_DIR}")
    return graph_paths[0]


def build_scene(graph: dict[str, Any]) -> list[bpy.types.Object]:
    materials = {
        "outer_flat": seam.make_material("mat_angle_outer_flat", (0.24, 0.38, 0.33, 1.0)),
        "lower_slope": seam.make_material("mat_angle_lower_slope", (0.33, 0.49, 0.35, 1.0)),
        "upper_slope": seam.make_material("mat_angle_upper_slope", (0.49, 0.58, 0.35, 1.0)),
        "hilltop": seam.make_material("mat_angle_hilltop", (0.65, 0.59, 0.37, 1.0)),
        "split_riser": seam.make_material("mat_angle_split_riser", (0.52, 0.43, 0.32, 1.0)),
        "split_cliff": seam.make_material("mat_angle_split_cliff", (0.36, 0.19, 0.16, 1.0)),
        "fold_meet_halfway": seam.make_material("mat_angle_fold_meet_halfway", (0.40, 0.50, 0.33, 1.0)),
        "corner_cap": seam.make_material("mat_angle_corner_seam_cap", (0.48, 0.39, 0.29, 1.0)),
        "chunk_skirt": seam.make_material("mat_angle_chunk_skirt", (0.18, 0.20, 0.19, 1.0)),
        "socket": seam.make_material("mat_angle_socket", (0.96, 0.60, 0.18, 1.0)),
    }
    created: list[bpy.types.Object] = []
    root = seam.create_empty(
        graph["graph_id"],
        (0.0, 0.0, 0.0),
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        None,
        {"graph_id": graph["graph_id"], "proof": "hex_seam_policy_angle_review_v0"},
    )
    created.append(root)
    created.append(seam.make_connected_top_mesh(graph, materials, root))
    created.append(seam.make_fold_meet_halfway_mesh(graph, materials["fold_meet_halfway"], root))
    created.append(seam.make_seam_wall_mesh(graph, "split_riser", "split_riser_mesh", materials["split_riser"], root))
    created.append(seam.make_seam_wall_mesh(graph, "split_cliff", "split_cliff_mesh", materials["split_cliff"], root))
    created.append(seam.make_corner_seam_cap_mesh(graph, materials["corner_cap"], root))
    created.append(seam.make_seam_wall_mesh(graph, "chunk_skirt", "chunk_skirt_mesh", materials["chunk_skirt"], root))
    created.append(seam.make_filtered_socket_marker_mesh(graph, materials, root))
    return created


def configure_scene() -> tuple[mathutils.Vector, float]:
    bpy.context.scene.world.color = (0.76, 0.78, 0.80)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -12.0, 16.0))
    light = bpy.context.object
    light.name = "hex_seam_angle_review_area_light"
    light.data.energy = 760.0
    light.data.size = 12.0

    mins, maxs = seam.scene_bounds()
    center = (mins + maxs) * 0.5
    span = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.display.shading.show_cavity = True
    bpy.context.scene.render.resolution_x = 1700
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    return center, span


def render_view(view: dict[str, Any], center: mathutils.Vector, span: float, prefix: str) -> dict[str, Any]:
    target = center + mathutils.Vector(tuple(view.get("target_offset", (0.0, 0.0, 0.0))))
    offset = mathutils.Vector(tuple(view["camera_offset"]))
    bpy.ops.object.camera_add(location=target + offset)
    cam = bpy.context.object
    cam.name = f"camera_{view['view_id']}"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * float(view["ortho_scale_mult"])
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    render_path = OUT_DIR / f"{prefix}_{view['view_id']}.png"
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)
    return {
        "view_id": view["view_id"],
        "render_path": str(render_path.relative_to(ROOT)),
        "camera_offset": view["camera_offset"],
        "target_offset": view.get("target_offset", (0.0, 0.0, 0.0)),
        "ortho_scale_mult": view["ortho_scale_mult"],
        "review_focus": view["review_focus"],
    }


def write_reports(
    graph: dict[str, Any],
    created: list[bpy.types.Object],
    rendered_views: list[dict[str, Any]],
    blend_path: Path,
    report_json_path: Path,
    report_md_path: Path,
) -> None:
    mesh_faces = {
        obj["mesh_role"]: len(obj.data.polygons)
        for obj in created
        if obj.type == "MESH" and "mesh_role" in obj
    }
    needs_work = [
        {
            "topic": "fold overlay geometry",
            "note": "Fold-meet-halfway seams are rendered as explicit overlay flaps for proof. The production mesh compiler should eventually cut top faces along fold insets instead of overlaying folded faces on top.",
        },
        {
            "topic": "top-down seam clutter",
            "note": "Top-down review shows the riser faces overpowering the hill as blocky wall shapes. The next debug renderer needs layer toggles: surface only, seams only, sockets only, and final combined.",
        },
        {
            "topic": "riser language",
            "note": "Split risers prove the seam contract, but they are still flat vertical quads. Next pass needs named edge profiles: stair_step, retaining_wall, broken_rock_riser, and smooth_embankment.",
        },
        {
            "topic": "cliff readability",
            "note": "Only five cliff faces exist in this hill proof, so the cliff material reads as small dark cuts. A cliff-heavy test site is needed before judging fall-edge readability.",
        },
        {
            "topic": "surface triangulation",
            "note": "The connected top mesh is coherent, but triangle facets are visible. Later terrain should support smoothing rules or deliberate faceted style selection.",
        },
        {
            "topic": "edge profile depth",
            "note": "The seam policy says what mesh behavior is legal, but it does not yet decide the detailed shape language of a seam. We need edge profiles that can turn a height delta into stairs, slope blends, retaining walls, fractured cliffs, or path ramps.",
        },
        {
            "topic": "socket display",
            "note": "Socket markers are filtered to high-elevation cells for this review. Long term, sockets need mode-specific visibility: build pads, cover anchors, roads, doors, and hazard edges should not all render the same.",
        },
        {
            "topic": "chunk boundary",
            "note": "The skirt proves boundary closure, but it still looks like a hard cut. Future chunk stitching needs neighbor-aware borders so adjacent map cubes can join without skirts between them.",
        },
        {
            "topic": "terrain semantics",
            "note": "The visual proof shows surfaces and seams, but it does not yet show route, cover, choke, climb, fall, or line-of-sight affordances as separate debug layers.",
        },
    ]
    report = {
        "schema": "hex_seam_policy_angle_review_v0",
        "graph_id": graph["graph_id"],
        "rendered_view_count": len(rendered_views),
        "rendered_views": rendered_views,
        "seam_policy_summary": graph["seam_policy_summary"],
        "vertex_split_summary": graph["vertex_split_summary"],
        "corner_seam_cap_count": len(graph.get("corner_seam_caps", [])),
        "seam_fact_count": len(graph["seam_facts"]),
        "mesh_faces": mesh_faces,
        "objects_created": len(created),
        "blend_path": str(blend_path.relative_to(ROOT)),
        "needs_work": needs_work,
        "next_recommended_slice": "Add edge profile variants for split_riser and split_cliff: stair_step, retaining_wall, broken_rock_cliff, smooth_embankment.",
    }
    report_json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Hex Seam Policy Angle Review v0",
        "",
        f"Graph: `{graph['graph_id']}`",
        "",
        "## Views",
        "",
        "| View | Focus | Output |",
        "| --- | --- | --- |",
    ]
    for view in rendered_views:
        lines.append(f"| `{view['view_id']}` | {view['review_focus']} | `{view['render_path']}` |")
    lines.extend(
        [
            "",
            "## Mesh Counts",
            "",
            f"- seam facts: `{len(graph['seam_facts'])}`",
            f"- vertex split summary: `{graph['vertex_split_summary']}`",
            f"- corner seam caps: `{len(graph.get('corner_seam_caps', []))}`",
            f"- seam policy summary: `{graph['seam_policy_summary']}`",
            f"- mesh faces: `{mesh_faces}`",
            "",
            "## Needs Work",
            "",
        ]
    )
    for item in needs_work:
        lines.append(f"- **{item['topic']}**: {item['note']}")
    lines.extend(
        [
            "",
            "## Next Slice",
            "",
            report["next_recommended_slice"],
            "",
        ]
    )
    report_md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seam.clear_scene()
    prefix, blend_path, report_json_path, report_md_path = output_paths()
    graph = seam.load_json(selected_graph_path())
    created = build_scene(graph)
    center, span = configure_scene()
    views = [
        {
            "view_id": "top_down",
            "camera_offset": (0.0, -0.01, 38.0),
            "ortho_scale_mult": 1.04,
            "review_focus": "overall footprint, chunk skirt silhouette, top-surface continuity",
        },
        {
            "view_id": "north_oblique",
            "camera_offset": (17.0, -24.0, 15.0),
            "ortho_scale_mult": 1.08,
            "review_focus": "main proof angle for hill shape, risers, and high sockets",
        },
        {
            "view_id": "south_oblique",
            "camera_offset": (-18.0, 23.0, 15.0),
            "ortho_scale_mult": 1.08,
            "review_focus": "opposite side seam visibility and hidden-face assumptions",
        },
        {
            "view_id": "east_low",
            "camera_offset": (26.0, -7.0, 7.0),
            "ortho_scale_mult": 0.82,
            "review_focus": "low-angle read of vertical risers and cliff cuts",
        },
        {
            "view_id": "hill_close",
            "camera_offset": (9.0, -11.0, 7.0),
            "target_offset": (0.0, 0.0, 1.0),
            "ortho_scale_mult": 0.43,
            "review_focus": "local seam quality, top triangulation, and build socket scale",
        },
    ]
    rendered_views = [render_view(view, center, span, prefix) for view in views]
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    write_reports(graph, created, rendered_views, blend_path, report_json_path, report_md_path)
    print(f"wrote {blend_path.relative_to(ROOT)}")
    print(f"wrote {report_json_path.relative_to(ROOT)}")
    print(f"wrote {report_md_path.relative_to(ROOT)}")
    for view in rendered_views:
        print(f"wrote {view['render_path']}")


if __name__ == "__main__":
    main()
