"""
ascii_ornate_post_sequence.py

Purpose:
Turn an ornament banister/newel post reference image into an ASCII proof inside
Blender.

Pipeline:
1. Load source image using Blender's built-in image loader.
2. Auto-crop white background.
3. Convert image into sampled luminance/ink grid.
4. Generate three ASCII passes:
   - silhouette pass
   - value/density pass
   - edge-hybrid pass
5. Create Blender text objects for each pass.
6. Animate visibility as a simple proof sequence.
7. Save .txt outputs and a .blend file.

No UI. No Pillow. No NumPy. Blender-only Python.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
import mathutils


# ============================================================
# USER SETTINGS
# ============================================================
SOURCE_IMAGE = "/Users/kogaryu/gameguy-3d-lab/image_to_ascii_workbench_v3/out/asset_zoo_input.png"
OUT_DIR = "//ascii_ornate_post_out"
WIDTH_CHARS = 96
FONT_ASPECT = 0.48

# Sampling quality per ASCII cell.
# 1 = center sample only
# 2 = 2x2 samples
# 3 = 3x3 samples
SUPERSAMPLE = 3

# Background cleanup. Higher means more near-white background becomes empty.
BACKGROUND_INK_CUTOFF = 0.055

# Tonal remap. These work on "ink" where 0 = white/background, 1 = black/solid.
BLACK_POINT = 0.03
WHITE_POINT = 0.82
GAMMA = 0.85
CONTRAST = 1.18

# Edge pass.
EDGE_THRESHOLD = 0.115
EDGE_STRENGTH_MIN_INK = 0.06

# Use CP437-ish visual grammar.
VALUE_RAMP = " .·░▒▓█"
DENSE_RAMP = " .,:;irsXA253hMHGS#9B&@"

# Set this to VALUE_RAMP for blocky CP437 proof, DENSE_RAMP for detail.
ACTIVE_RAMP = VALUE_RAMP

# Blender text display.
TEXT_SIZE = 0.105
LINE_SPACING = 0.78
CHAR_SPACING = 1.0
TEXT_COLOR = (0.88, 0.88, 0.86, 1.0)
TEXT_DIM_COLOR = (0.48, 0.48, 0.48, 1.0)
BG_COLOR = (0.015, 0.015, 0.015, 1.0)
SAVE_BLEND = True
RENDER_STILLS = False


# ============================================================
# BASIC BLENDER HELPERS
# ============================================================
def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def ensure_out_dir(path_text: str) -> Path:
    path = bpy.path.abspath(path_text)
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)


def make_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    dx = target[0] - obj.location.x
    dy = target[1] - obj.location.y
    dz = target[2] - obj.location.z
    direction = mathutils.Vector((dx, dy, dz))
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


# ============================================================
# IMAGE SAMPLING
# ============================================================
class ImageSampler:
    def __init__(self, image: bpy.types.Image):
        self.image = image
        self.w = image.size[0]
        self.h = image.size[1]
        # Blender image pixels are flat RGBA floats.
        # index = ((y * width) + x) * 4
        self.pixels = list(image.pixels[:])

    def rgba_at(self, x: float, y: float) -> tuple[float, float, float, float]:
        x = max(0, min(self.w - 1, int(x)))
        y = max(0, min(self.h - 1, int(y)))
        i = (y * self.w + x) * 4
        return (
            self.pixels[i + 0],
            self.pixels[i + 1],
            self.pixels[i + 2],
            self.pixels[i + 3],
        )

    def luminance_at(self, x: float, y: float) -> float:
        r, g, b, _a = self.rgba_at(x, y)
        return 0.2989 * r + 0.5866 * g + 0.1145 * b

    def ink_at(self, x: float, y: float) -> float:
        # ink: 0 = white/background, 1 = black/dark stroke
        return 1.0 - self.luminance_at(x, y)

    def auto_crop_bbox(self, cutoff: float = 0.045, step: int = 3, pad: int = 12) -> tuple[int, int, int, int]:
        min_x = self.w
        min_y = self.h
        max_x = 0
        max_y = 0
        found = False
        for y in range(0, self.h, step):
            for x in range(0, self.w, step):
                if self.ink_at(x, y) > cutoff:
                    found = True
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        if not found:
            return (0, 0, self.w - 1, self.h - 1)
        min_x = max(0, min_x - pad)
        min_y = max(0, min_y - pad)
        max_x = min(self.w - 1, max_x + pad)
        max_y = min(self.h - 1, max_y + pad)
        return (min_x, min_y, max_x, max_y)


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def tonal_remap(ink: float) -> float:
    # Black/white point remap.
    v = (ink - BLACK_POINT) / max(0.0001, WHITE_POINT - BLACK_POINT)
    v = clamp01(v)
    # Contrast around midpoint.
    v = clamp01((v - 0.5) * CONTRAST + 0.5)
    # Gamma.
    v = clamp01(v) ** (1.0 / max(0.05, GAMMA))
    return clamp01(v)


def sample_cell_ink(
    sampler: ImageSampler,
    crop: tuple[int, int, int, int],
    cell_x: int,
    cell_y: int,
    grid_w: int,
    grid_h: int,
) -> float:
    min_x, min_y, max_x, max_y = crop
    crop_w = max_x - min_x + 1
    crop_h = max_y - min_y + 1
    x0 = min_x + (cell_x / grid_w) * crop_w
    y0 = min_y + (cell_y / grid_h) * crop_h
    x1 = min_x + ((cell_x + 1) / grid_w) * crop_w
    y1 = min_y + ((cell_y + 1) / grid_h) * crop_h
    total = 0.0
    count = 0
    n = max(1, SUPERSAMPLE)
    for sy in range(n):
        for sx in range(n):
            tx = (sx + 0.5) / n
            ty = (sy + 0.5) / n
            px = x0 + (x1 - x0) * tx
            py = y0 + (y1 - y0) * ty
            total += sampler.ink_at(px, py)
            count += 1
    return total / max(1, count)


def build_ink_grid(sampler: ImageSampler, crop: tuple[int, int, int, int], width_chars: int) -> list[list[float]]:
    min_x, min_y, max_x, max_y = crop
    crop_w = max_x - min_x + 1
    crop_h = max_y - min_y + 1
    height_chars = max(1, int(round((crop_h / max(1, crop_w)) * width_chars * FONT_ASPECT)))
    grid = []
    for y in range(height_chars):
        row = []
        for x in range(width_chars):
            ink = sample_cell_ink(sampler, crop, x, y, width_chars, height_chars)
            row.append(tonal_remap(ink))
        grid.append(row)
    return grid


# ============================================================
# ASCII PASSES
# ============================================================
def ramp_char(value: float, ramp: str) -> str:
    value = clamp01(value)
    if value < BACKGROUND_INK_CUTOFF:
        return " "
    idx = int(round(value * (len(ramp) - 1)))
    idx = max(0, min(len(ramp) - 1, idx))
    return ramp[idx]


def silhouette_ascii(grid: list[list[float]]) -> str:
    lines = []
    for row in grid:
        chars = []
        for v in row:
            if v > 0.22:
                chars.append("█")
            elif v > 0.08:
                chars.append("░")
            else:
                chars.append(" ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def value_ascii(grid: list[list[float]], ramp: str = ACTIVE_RAMP) -> str:
    lines = []
    for row in grid:
        chars = [ramp_char(v, ramp) for v in row]
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def sobel_at(grid: list[list[float]], x: int, y: int) -> tuple[float, float]:
    h = len(grid)
    w = len(grid[0]) if h else 0

    def get(ix: int, iy: int) -> float:
        ix = max(0, min(w - 1, ix))
        iy = max(0, min(h - 1, iy))
        return grid[iy][ix]

    gx = -get(x - 1, y - 1) + get(x + 1, y - 1) - 2 * get(x - 1, y) + 2 * get(x + 1, y) - get(x - 1, y + 1) + get(x + 1, y + 1)
    gy = -get(x - 1, y - 1) - 2 * get(x, y - 1) - get(x + 1, y - 1) + get(x - 1, y + 1) + 2 * get(x, y + 1) + get(x + 1, y + 1)
    mag = math.sqrt(gx * gx + gy * gy)
    ang = math.atan2(gy, gx)
    return mag, ang


def angle_to_ascii_edge(angle: float) -> str:
    # Gradient angle points across the edge, not along it.
    # Add 90 degrees to get edge tangent direction.
    tangent = angle + math.pi / 2.0
    deg = (math.degrees(tangent) + 180.0) % 180.0
    if deg < 22.5 or deg >= 157.5:
        return "─"
    if deg < 67.5:
        return "/"
    if deg < 112.5:
        return "│"
    return "\\"


def edge_hybrid_ascii(grid: list[list[float]], ramp: str = ACTIVE_RAMP) -> str:
    h = len(grid)
    w = len(grid[0]) if h else 0
    lines = []
    for y in range(h):
        chars = []
        for x in range(w):
            v = grid[y][x]
            mag, ang = sobel_at(grid, x, y)
            if v > EDGE_STRENGTH_MIN_INK and mag > EDGE_THRESHOLD:
                chars.append(angle_to_ascii_edge(ang))
            else:
                chars.append(ramp_char(v, ramp))
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


# ============================================================
# BLENDER TEXT SCENE
# ============================================================
def add_background(width_units: float, height_units: float, mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.03))
    bg = bpy.context.object
    bg.name = "ascii_black_background_panel"
    bg.dimensions = (width_units, height_units, 0.02)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bg.data.materials.append(mat)
    return bg


def add_ascii_text(
    name: str,
    body: str,
    mat: bpy.types.Material,
    x: float,
    y: float,
    visible_frame_start: int,
    visible_frame_end: int,
) -> bpy.types.Object:
    bpy.ops.object.text_add(location=(x, y, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_curve"
    obj.data.body = body
    obj.data.align_x = "LEFT"
    obj.data.align_y = "TOP"
    obj.data.size = TEXT_SIZE
    obj.data.space_line = LINE_SPACING
    obj.data.space_character = CHAR_SPACING
    obj.data.extrude = 0.0
    obj.data.materials.append(mat)
    # Visibility sequence.
    for frame in [1, visible_frame_start - 1, visible_frame_start, visible_frame_end, visible_frame_end + 1]:
        if frame < 1:
            continue
        visible = visible_frame_start <= frame <= visible_frame_end
        obj.hide_viewport = not visible
        obj.hide_render = not visible
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)
        obj.keyframe_insert(data_path="hide_render", frame=frame)
    return obj


def setup_camera(ascii_w: int, ascii_h: int) -> tuple[float, float]:
    # Estimate physical panel size from character count.
    panel_w = ascii_w * TEXT_SIZE * 0.62
    panel_h = ascii_h * TEXT_SIZE * LINE_SPACING
    bpy.ops.object.camera_add(location=(0, 0, 12), rotation=(0, 0, 0))
    cam = bpy.context.object
    cam.name = "ascii_proof_orthographic_camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(panel_w * 1.15, panel_h * 1.15)
    bpy.context.scene.camera = cam
    return panel_w, panel_h


def write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    clear_scene()
    out_dir = ensure_out_dir(OUT_DIR)
    source_path = bpy.path.abspath(SOURCE_IMAGE)
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Source image not found: {source_path}\n"
            "Set SOURCE_IMAGE at the top of this script."
        )
    img = bpy.data.images.load(source_path)
    sampler = ImageSampler(img)
    crop = sampler.auto_crop_bbox(cutoff=0.035, step=3, pad=18)
    grid = build_ink_grid(sampler, crop, WIDTH_CHARS)
    ascii_sil = silhouette_ascii(grid)
    ascii_val = value_ascii(grid)
    ascii_edge = edge_hybrid_ascii(grid)
    write_text(out_dir / "ornate_post_01_silhouette.txt", ascii_sil)
    write_text(out_dir / "ornate_post_02_value.txt", ascii_val)
    write_text(out_dir / "ornate_post_03_edge_hybrid.txt", ascii_edge)
    mat_text = make_material("ascii_warm_white_text", TEXT_COLOR)
    mat_dim = make_material("ascii_dim_text", TEXT_DIM_COLOR)
    mat_bg = make_material("ascii_background_black", BG_COLOR)
    ascii_h = len(grid)
    ascii_w = WIDTH_CHARS
    panel_w, panel_h = setup_camera(ascii_w, ascii_h)
    add_background(panel_w * 1.20, panel_h * 1.20, mat_bg)
    x = -panel_w * 0.50
    y = panel_h * 0.50
    add_ascii_text("stage_01_silhouette_ascii", ascii_sil, mat_dim, x, y, 1, 40)
    add_ascii_text("stage_02_value_ascii", ascii_val, mat_text, x, y, 41, 80)
    add_ascii_text("stage_03_edge_hybrid_ascii", ascii_edge, mat_text, x, y, 81, 130)
    # Markers make timeline inspection easier.
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 130
    scene.timeline_markers.new("01 silhouette", frame=1)
    scene.timeline_markers.new("02 value pass", frame=41)
    scene.timeline_markers.new("03 edge hybrid final", frame=81)
    # Render settings.
    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 2400
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    if RENDER_STILLS:
        stills = [
            (1, "render_01_silhouette.png"),
            (41, "render_02_value.png"),
            (81, "render_03_edge_hybrid.png"),
        ]
        for frame, filename in stills:
            scene.frame_set(frame)
            scene.render.filepath = str(out_dir / filename)
            bpy.ops.render.render(write_still=True)
    if SAVE_BLEND:
        bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / "ornate_post_ascii_sequence.blend"))
    print("ASCII proof sequence complete.")
    print(f"Output directory: {out_dir}")
    print(f"Crop bbox: {crop}")
    print(f"ASCII grid: {ascii_w} x {ascii_h}")


if __name__ == "__main__":
    main()
