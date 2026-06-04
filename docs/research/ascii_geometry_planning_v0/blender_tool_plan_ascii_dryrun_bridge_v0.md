# Blender Tool Plan ASCII Dry-Run Bridge V0

## Intent

The ASCII layer should be able to preview what the Blender adapter is about to
build before Blender is opened.

The first supported bridge is:

```text
gameguy_tool_plan_v0
-> render_tool_plan_ascii_dryrun_v0.py
-> donated ascii_blender_dryrun_v0 operation stream
-> front/side/top ASCII previews
```

This keeps the source of truth on the same compiled tool plan consumed by the
Blender adapter.

## Script

```text
scripts/render_tool_plan_ascii_dryrun_v0.py
```

Example:

```bash
python3 scripts/compile_blender_tool_plan_v0.py --out /tmp/gameguy_blender_tool_plan_v0
python3 scripts/render_tool_plan_ascii_dryrun_v0.py \
  --plan /tmp/gameguy_blender_tool_plan_v0/gothic_stone_banister_post_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_tool_plan_ascii_dryrun_v0/banister_post \
  --width 96 \
  --height 72
```

Outputs:

```text
dryrun_operation_stream.json
front_preview.txt
side_preview.txt
top_preview.txt
ascii_dryrun_report.json
```

## V0 Coverage

Rendered as actual dry-run forms:

- `primitive_cube_add`
- `primitive_cylinder_add`
- `mesh_from_pydata` as a bounding-box approximation

Recorded but not geometrically applied yet:

- booleans
- bevels
- arrays
- mirrors
- displace
- weld
- joins
- UV/material/export/preview steps

## Rule

The bridge does not scrape arbitrary `bpy` scripts.

Blender scripts must either consume `gameguy_tool_plan_v0` or emit a compatible
operation/tool-plan stream if they want an ASCII dry run. That is how the ASCII
output and Blender output stay tied to the same source instead of becoming two
separate guesses.

## Next Needed Work

1. Add array expansion to the dry-run bridge.
2. Add boolean cutter visualization.
3. Add bevel/lip marks as edge overlays.
4. Add per-region/layer previews so broad masses do not hide small detail.
