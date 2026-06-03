# Multi-Asset Tool Plan Recipes v0

This slice makes the Blender tool-plan lane compile more than one asset family from the same default source bundle.

## Source Path

```text
data/architecture/asset_mill/tool_plan_recipes/architectural_tool_plan_recipes_v0.json
-> scripts/compile_blender_tool_plan_v0.py
-> gameguy_tool_plan_v0 JSON
-> scripts/validate_gameguy_tool_plan_v0.py
-> scripts/execute_blender_tool_plan_v0.py --validate-only
```

## Compiled Plans

The default bundle now emits:

| Asset | Family | Steps | Unique tools |
| --- | --- | ---: | ---: |
| `gothic_stone_banister_post_tool_plan_v0` | `banister_post` | 32 | 24 |
| `gothic_stone_window_frame_tool_plan_v0` | `window_frame` | 25 | 22 |
| `gothic_stone_door_frame_tool_plan_v0` | `door_frame` | 25 | 22 |

The window frame uses a different sequence from the banister post. It creates four frame blocks, joins them, applies bevels and weighted normals, adds procedural stone material/detail, UVs, cleanup, bounds validation, proxy/LOD, preview, and export steps. It does not use banister-only radial rib or socket-boolean steps.

## Boundary

The compiler still does not import Blender or write mesh/media outputs. Blender remains an adapter that consumes compiled `gameguy_tool_plan_v0` JSON. Both default compiled plans are accepted by the execution adapter in validate-only mode.

## Validation

```text
python3 scripts/compile_blender_tool_plan_v0.py --validate-only
python3 scripts/compile_blender_tool_plan_v0.py --clean --out /tmp/gameguy_blender_tool_plan_v0
python3 scripts/validate_gameguy_tool_plan_v0.py --manifest /tmp/gameguy_blender_tool_plan_v0/manifest.json
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_window_frame_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_door_frame_tool_plan_v0_compiled.json --validate-only
```

Expected output:

```text
compiled tool plans=3 steps=82 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 3 plans, 82 steps, 24 tools
PASS Blender tool-plan adapter validation: steps=32 tools=24
PASS Blender tool-plan adapter validation: steps=25 tools=22
PASS Blender tool-plan adapter validation: steps=25 tools=22
```
