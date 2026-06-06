#!/usr/bin/env python3
"""Set up professional Blender reference planes from the mannequin turnaround.

The output is reference-only: no editable blockout mesh, no pose rig. It places
cropped orthographic image planes around the origin so a model can be built over
them in Blender.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import export_blender_low_poly_character_mannequin_v0 as scene_exporter


DEFAULT_REFERENCE = ROOT / "data" / "characters" / "references" / (
    "low_poly_mannequin_turnaround_v0.png"
)
DEFAULT_OUT = Path("/tmp/gameguy_low_poly_character_reference_planes_v0")
IMAGE_SIZE_PX = (1774, 887)
BODY_HEIGHT_M = 1.8


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def reference_views() -> list[dict[str, Any]]:
    return [
        {
            "view_id": "front",
            "label": "FRONT",
            "crop_px": [88, 138, 415, 758],
            "plane": "XZ",
            "offset_m": 0.62,
            "centerline_axis": "X",
            "primary": True,
        },
        {
            "view_id": "side",
            "label": "SIDE",
            "crop_px": [694, 138, 918, 758],
            "plane": "YZ",
            "offset_m": -0.62,
            "centerline_axis": "Y",
            "primary": True,
        },
        {
            "view_id": "back",
            "label": "BACK",
            "crop_px": [1198, 138, 1490, 758],
            "plane": "XZ_BACK",
            "offset_m": -0.62,
            "centerline_axis": "X",
            "primary": True,
        },
        {
            "view_id": "three_quarter_front",
            "label": "3/4 FRONT",
            "crop_px": [425, 138, 660, 758],
            "plane": "CARD",
            "location_m": [-1.35, 0.82, 0.9],
            "height_m": 0.95,
            "primary": False,
        },
        {
            "view_id": "three_quarter_back",
            "label": "3/4 BACK",
            "crop_px": [943, 138, 1176, 758],
            "plane": "CARD",
            "location_m": [1.35, 0.82, 0.9],
            "height_m": 0.95,
            "primary": False,
        },
        {
            "view_id": "top_head",
            "label": "TOP HEAD",
            "crop_px": [1558, 118, 1725, 296],
            "plane": "XY_TOP",
            "location_m": [0.0, 0.0, 1.98],
            "height_m": 0.42,
            "primary": False,
        },
    ]


def make_report(
    reference_image: Path,
    *,
    generated: bool,
    out_root: Path | None,
    render: bool,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "low_poly_character_reference_planes_report_v0",
        "adapter": "scripts/setup_low_poly_character_reference_planes_v0.py",
        "reference_image": str(reference_image),
        "reference_image_exists": reference_image.exists(),
        "image_size_px": list(IMAGE_SIZE_PX),
        "body_height_m": BODY_HEIGHT_M,
        "reference_view_count": len(reference_views()),
        "primary_orthographic_view_count": 3,
        "generated_outputs_created": generated,
        "render_requested": render,
        "rules": {
            "reference_only_scene": True,
            "creates_locked_image_planes": generated,
            "creates_front_side_back_planes": generated,
            "creates_three_quarter_cards": generated,
            "creates_top_head_plane": generated,
            "creates_orthographic_cameras": generated,
            "creates_scale_guides": generated,
            "creates_viewport_image_empties": generated,
            "packs_reference_images": generated,
            "creates_editable_mesh": False,
        },
    }
    if out_root is not None:
        report["out_root"] = str(out_root)
        report["blend_path"] = str(out_root / "low_poly_mannequin_reference_planes_v0.blend")
        if render:
            report["preview_path"] = str(
                out_root / "low_poly_mannequin_reference_planes_preview.png"
            )
    return report


def run_blender_export(
    reference_image: Path,
    out_root: Path,
    render: bool,
    json_report: Path | None,
) -> None:
    try:
        import bpy  # type: ignore
        import mathutils  # type: ignore
    except ModuleNotFoundError:
        fail(
            "Reference plane setup requires Blender Python. "
            "Use --validate-only with normal Python."
        )

    if not reference_image.exists():
        fail(f"missing reference image: {reference_image}")

    out_root.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collections = {
        "planes": scene_exporter.ensure_collection(bpy, "LOCKED_REFERENCE_PLANES"),
        "empties": scene_exporter.ensure_collection(bpy, "VIEWPORT_IMAGE_REFERENCES"),
        "cards": scene_exporter.ensure_collection(bpy, "LOCKED_REVIEW_CARDS"),
        "guides": scene_exporter.ensure_collection(bpy, "REFERENCE_SCALE_GUIDES"),
        "model": scene_exporter.ensure_collection(bpy, "MODEL_HERE"),
    }
    cropped_images = crop_reference_images(reference_image, out_root / "cropped_references")
    image = bpy.data.images.load(str(reference_image))
    materials = {
        "guide": make_material(bpy, "reference_guide_line", (0.05, 0.07, 0.09, 1.0)),
        "origin": make_material(bpy, "model_origin_marker", (0.1, 0.45, 1.0, 1.0)),
    }
    created_planes = []
    for view in reference_views():
        collection = collections["planes"] if view["primary"] else collections["cards"]
        created_planes.append(create_reference_plane(bpy, image, view, collection))
    created_empties = create_viewport_image_empties(
        bpy,
        cropped_images,
        collections["empties"],
    )

    create_scale_guides(bpy, materials, collections["guides"])
    create_origin_marker(bpy, materials, collections["model"])
    add_reference_cameras(bpy, mathutils)
    add_scene_context(bpy)
    bpy.ops.file.pack_all()

    blend_path = out_root / "low_poly_mannequin_reference_planes_v0.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    report = make_report(reference_image, generated=True, out_root=out_root, render=render)
    report["scene_object_count"] = len(bpy.context.scene.objects)
    report["locked_plane_names"] = [obj.name for obj in created_planes]
    report["viewport_image_empty_names"] = [obj.name for obj in created_empties]
    report["cropped_reference_dir"] = str(out_root / "cropped_references")
    if render:
        preview_path = out_root / "low_poly_mannequin_reference_planes_preview.png"
        scene_exporter.render_camera_view(bpy, "camera__reference_overview", preview_path)
        report["preview_path"] = str(preview_path)

    report_path = json_report if json_report is not None else out_root / (
        "low_poly_mannequin_reference_planes_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS low-poly mannequin reference planes export: "
        f"views={len(created_planes)} out={out_root}"
    )


def crop_reference_images(reference_image: Path, crop_dir: Path) -> dict[str, Path]:
    sips = shutil.which("sips")
    if sips is None:
        fail("cropping reference images requires macOS sips")
    crop_dir.mkdir(parents=True, exist_ok=True)
    cropped: dict[str, Path] = {}
    for view in reference_views():
        left, top, right, bottom = view["crop_px"]
        width = right - left
        height = bottom - top
        out_path = crop_dir / f"ref_{view['view_id']}.png"
        subprocess.run(
            [
                sips,
                "-c",
                str(height),
                str(width),
                "--cropOffset",
                str(top),
                str(left),
                str(reference_image),
                "--out",
                str(out_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cropped[view["view_id"]] = out_path
    return cropped


def make_material(bpy: Any, name: str, color: tuple[float, float, float, float]) -> Any:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    material.blend_method = "BLEND"
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Alpha"].default_value = color[3]
        shader.inputs["Roughness"].default_value = 0.8
    return material


def image_material_for_crop(
    bpy: Any,
    image: Any,
    view: dict[str, Any],
) -> Any:
    material = bpy.data.materials.new(f"REF_MAT__{view['view_id']}")
    material.diffuse_color = (1.0, 1.0, 1.0, 1.0)
    material.use_nodes = True
    material.blend_method = "OPAQUE"
    material.node_tree.nodes.clear()
    output = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    texture = material.node_tree.nodes.new(type="ShaderNodeTexImage")
    texture.image = image
    emission = material.node_tree.nodes.new(type="ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    material.node_tree.links.new(texture.outputs["Color"], emission.inputs["Color"])
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def crop_uvs(crop_px: list[int]) -> list[tuple[float, float]]:
    width, height = IMAGE_SIZE_PX
    left, top, right, bottom = crop_px
    u0 = left / width
    u1 = right / width
    v0 = 1.0 - (bottom / height)
    v1 = 1.0 - (top / height)
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def create_reference_plane(bpy: Any, image: Any, view: dict[str, Any], collection: Any) -> Any:
    crop = view["crop_px"]
    crop_width_px = crop[2] - crop[0]
    crop_height_px = crop[3] - crop[1]
    plane_height = float(view.get("height_m", BODY_HEIGHT_M))
    plane_width = plane_height * (crop_width_px / crop_height_px)
    plane = view["plane"]

    if plane == "XZ":
        y = float(view["offset_m"])
        vertices = xz_vertices(plane_width, BODY_HEIGHT_M, y)
    elif plane == "XZ_BACK":
        y = float(view["offset_m"])
        vertices = xz_vertices(plane_width, BODY_HEIGHT_M, y)
    elif plane == "YZ":
        x = float(view["offset_m"])
        vertices = yz_vertices(plane_width, BODY_HEIGHT_M, x)
    elif plane == "XY_TOP":
        location = tuple(float(value) for value in view["location_m"])
        vertices = xy_vertices(plane_width, plane_height, location)
    else:
        location = tuple(float(value) for value in view["location_m"])
        vertices = card_vertices(plane_width, plane_height, location)

    mesh = bpy.data.meshes.new(f"REF__{view['view_id']}_mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    mesh.uv_layers.new(name="UVMap")
    for loop, uv in zip(mesh.uv_layers.active.data, crop_uvs(crop), strict=False):
        loop.uv = uv
    obj = bpy.data.objects.new(f"REF_LOCKED__{view['view_id']}", mesh)
    obj.data.materials.append(image_material_for_crop(bpy, image, view))
    obj.hide_select = True
    obj.hide_viewport = True
    obj.show_transparent = True
    obj["reference_label"] = view["label"]
    obj["crop_px"] = crop
    obj["modeling_role"] = "locked_reference_image_plane"
    scene_exporter.link_to_collection(obj, collection)
    return obj


def create_viewport_image_empties(
    bpy: Any,
    cropped_images: dict[str, Path],
    collection: Any,
) -> list[Any]:
    created = []
    for view in reference_views():
        image = bpy.data.images.load(str(cropped_images[view["view_id"]]))
        obj = make_image_empty(bpy, image, view)
        obj["reference_label"] = view["label"]
        obj["modeling_role"] = "viewport_visible_locked_reference_image"
        scene_exporter.link_to_collection(obj, collection)
        created.append(obj)
    return created


def make_image_empty(bpy: Any, image: Any, view: dict[str, Any]) -> Any:
    width, height = reference_plane_dimensions(view)
    location = reference_empty_location(view, height)
    rotation = reference_empty_rotation(view)
    bpy.ops.object.empty_add(type="IMAGE", location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = f"IMG_REF_LOCKED__{view['view_id']}"
    obj.data = image
    obj.empty_display_size = width
    obj.empty_image_offset = (-0.5, -0.5)
    obj.empty_image_depth = "BACK"
    obj.show_empty_image_orthographic = True
    obj.show_empty_image_perspective = True
    obj.use_empty_image_alpha = True
    obj.hide_select = True
    return obj


def reference_plane_dimensions(view: dict[str, Any]) -> tuple[float, float]:
    crop = view["crop_px"]
    crop_width_px = crop[2] - crop[0]
    crop_height_px = crop[3] - crop[1]
    height = float(view.get("height_m", BODY_HEIGHT_M))
    width = height * (crop_width_px / crop_height_px)
    return width, height


def reference_empty_location(view: dict[str, Any], height: float) -> tuple[float, float, float]:
    plane = view["plane"]
    if plane == "XZ":
        return (0.0, float(view["offset_m"]), height / 2.0)
    if plane == "XZ_BACK":
        return (0.0, float(view["offset_m"]), height / 2.0)
    if plane == "YZ":
        return (float(view["offset_m"]), 0.0, height / 2.0)
    location = view.get("location_m")
    if isinstance(location, list):
        return tuple(float(value) for value in location)
    return (0.0, 0.0, height / 2.0)


def reference_empty_rotation(view: dict[str, Any]) -> tuple[float, float, float]:
    plane = view["plane"]
    if plane in {"XZ", "XZ_BACK", "CARD"}:
        return (math.radians(90.0), 0.0, 0.0)
    if plane == "YZ":
        return (math.radians(90.0), 0.0, math.radians(90.0))
    if plane == "XY_TOP":
        return (0.0, 0.0, 0.0)
    return (math.radians(90.0), 0.0, 0.0)


def xz_vertices(width: float, height: float, y: float) -> list[tuple[float, float, float]]:
    half_width = width / 2.0
    return [
        (-half_width, y, 0.0),
        (half_width, y, 0.0),
        (half_width, y, height),
        (-half_width, y, height),
    ]


def yz_vertices(width: float, height: float, x: float) -> list[tuple[float, float, float]]:
    half_width = width / 2.0
    return [
        (x, -half_width, 0.0),
        (x, half_width, 0.0),
        (x, half_width, height),
        (x, -half_width, height),
    ]


def xy_vertices(
    width: float,
    height: float,
    location: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    x, y, z = location
    return [
        (x - width / 2.0, y - height / 2.0, z),
        (x + width / 2.0, y - height / 2.0, z),
        (x + width / 2.0, y + height / 2.0, z),
        (x - width / 2.0, y + height / 2.0, z),
    ]


def card_vertices(
    width: float,
    height: float,
    location: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    x, y, z = location
    return [
        (x - width / 2.0, y, z - height / 2.0),
        (x + width / 2.0, y, z - height / 2.0),
        (x + width / 2.0, y, z + height / 2.0),
        (x - width / 2.0, y, z + height / 2.0),
    ]


def create_scale_guides(bpy: Any, materials: dict[str, Any], collection: Any) -> None:
    material = materials["guide"]
    for z_value, name in [
        (0.0, "feet"),
        (0.42, "knees"),
        (0.86, "hips"),
        (1.20, "chest"),
        (1.42, "shoulders"),
        (1.62, "eyes"),
        (1.8, "top_of_head"),
    ]:
        scene_exporter.create_curve_line(
            bpy,
            f"guide_front_height__{name}",
            (-0.8, 0.0, z_value),
            (0.8, 0.0, z_value),
            material,
            collection,
        )
        scene_exporter.create_curve_line(
            bpy,
            f"guide_side_height__{name}",
            (0.0, -0.5, z_value),
            (0.0, 0.5, z_value),
            material,
            collection,
        )
    scene_exporter.create_curve_line(
        bpy,
        "guide_world_centerline_z",
        (0.0, 0.0, 0.0),
        (0.0, 0.0, BODY_HEIGHT_M),
        material,
        collection,
    )


def create_origin_marker(bpy: Any, materials: dict[str, Any], collection: Any) -> None:
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0.0, 0.0, 0.0))
    empty = bpy.context.object
    empty.name = "MODEL_ORIGIN__build_character_here"
    empty.empty_display_size = 0.18
    scene_exporter.link_to_collection(empty, collection)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, BODY_HEIGHT_M / 2.0))
    bbox = bpy.context.object
    bbox.name = "MODEL_SCALE_BOX__1_8m_locked"
    bbox.scale = (0.42, 0.24, BODY_HEIGHT_M / 2.0)
    bbox.display_type = "WIRE"
    bbox.hide_select = True
    bbox.hide_render = True
    bbox.data.materials.append(materials["origin"])
    scene_exporter.link_to_collection(bbox, collection)


def add_reference_cameras(bpy: Any, mathutils: Any) -> None:
    front = scene_exporter.add_ortho_camera(
        bpy,
        mathutils,
        "camera__reference_front",
        (0.0, -4.0, 0.9),
        (0.0, 0.0, 0.9),
        2.05,
    )
    scene_exporter.add_ortho_camera(
        bpy,
        mathutils,
        "camera__reference_side",
        (4.0, 0.0, 0.9),
        (0.0, 0.0, 0.9),
        2.05,
    )
    scene_exporter.add_ortho_camera(
        bpy,
        mathutils,
        "camera__reference_back",
        (0.0, 4.0, 0.9),
        (0.0, 0.0, 0.9),
        2.05,
    )
    scene_exporter.add_ortho_camera(
        bpy,
        mathutils,
        "camera__reference_top",
        (0.0, 0.0, 4.0),
        (0.0, 0.0, 0.9),
        2.2,
    )
    scene_exporter.add_ortho_camera(
        bpy,
        mathutils,
        "camera__reference_overview",
        (2.2, -3.0, 1.55),
        (0.0, 0.0, 0.9),
        2.55,
    )
    bpy.context.scene.camera = front


def add_scene_context(bpy: Any) -> None:
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1400
    bpy.context.scene.world.color = (0.96, 0.96, 0.96)
    bpy.context.scene["stage"] = "low_poly_character_reference_planes_v0"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = sys.argv[1:] if argv is None else argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    parser = argparse.ArgumentParser(
        description="Set up professional Blender reference planes from a turnaround sheet."
    )
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args(argv)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reference_image = resolve_path(args.reference)
    if not reference_image.exists():
        fail(f"missing reference image: {reference_image}")

    if args.validate_only:
        if args.json_report:
            report_path = resolve_path(args.json_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report = make_report(
                reference_image,
                generated=False,
                out_root=None,
                render=args.render,
            )
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "PASS low-poly mannequin reference planes validation: "
            f"views={len(reference_views())}"
        )
        return 0

    out_root = resolve_path(args.out)
    report_path = resolve_path(args.json_report) if args.json_report else None
    run_blender_export(reference_image, out_root, args.render, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
