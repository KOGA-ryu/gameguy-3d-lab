# Image To ASCII Workbench V3

Headless image-to-ASCII renderer focused on dense detail. No UI, no Blender, no
asset generation.

## Install

```bash
cd image_to_ascii_workbench_v3
python3 -m pip install -r requirements.txt
```

## Basic Use

```bash
python3 -m image_to_ascii_workbench.cli input.png \
  --width 240 \
  --sampling super2x \
  --palette cp437-shade \
  --dither atkinson \
  --edge-mode sobel-hybrid \
  --edge-threshold 0.38 \
  --save-txt out.txt \
  --save-png out.png
```

If no `--save-*` option is provided, the ASCII text prints to stdout.

## Controls

- `--width`, `--height`: output character grid size.
- `--cell-aspect`: row correction for tall font cells. Default is `0.5`.
- `--sampling`: `center`, `average`, `median`, `super2x`, `super4x`.
- `--brightness`, `--contrast`, `--gamma`: tonal correction.
- `--black-point`, `--white-point`: clamp and remap image values before ASCII.
- `--dither`: `none`, `floyd-steinberg`, `atkinson`, `ordered`, `random`.
- `--edge-mode`: `off`, `sobel`, `sobel-hybrid`.
- `--palette`: `cp437-shade`, `dense`, `classic`, `blocks`, `binary`, `custom`.
- `--measure-font`: sort the chosen palette by actual glyph darkness in the selected font.
- `--save-txt`: UTF-8 ASCII/Unicode text output.
- `--save-cp437`: CP437 byte output with replacement for unsupported characters.
- `--save-png`: raster preview rendered from the ASCII text.

## Module Map

- `render_params.py`: render dataclass and option literals.
- `cp437.py`: CP437-style ramps.
- `palettes.py`: palette lookup and custom palette handling.
- `glyph_measure.py`: Pillow-based glyph darkness measurement.
- `sampling.py`: per-cell sampling strategies.
- `image_pipeline.py`: image load, resize, and tonal adjustment.
- `cell_buffer.py`: sampled luminance grid.
- `dither.py`: cell-space dithering.
- `edge_detect.py`: Sobel magnitude/direction and edge glyph mapping.
- `ascii_renderer.py`: density, dither, and edge composition.
- `exporters.py`: text, CP437, and PNG output.
- `cli.py`: command-line entry point.
