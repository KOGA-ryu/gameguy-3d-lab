# Door-Frame Tool Plan v0

This slice proves the asset-family sequence policy scales beyond the existing banister post and window frame.

## Source Path

```text
architectural_tool_plan_recipes_v0.json
-> asset_family_tool_sequence_policy_v0
-> scripts/compile_blender_tool_plan_v0.py
-> gameguy_tool_plan_v0 JSON
-> scripts/validate_gameguy_tool_plan_v0.py
-> scripts/execute_blender_tool_plan_v0.py
-> scripts/validate_blender_tool_plan_execution_report_v0.py
```

## Added Asset

```text
gothic_stone_door_frame_tool_plan_v0
```

The new source recipe uses the `door_frame` policy with a rectangular stone frame:

- width `1.10 m`
- depth `0.20 m`
- height `1.75 m`
- side jamb width `0.16 m`
- threshold/sill height `0.12 m`
- header height `0.18 m`
- clear opening `0.78 m x 1.45 m`

## Current Evidence

```text
compiled tool plans=5 steps=145 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 5 plans, 145 steps, 25 tools
PASS Blender tool-plan adapter validation: steps=25 tools=22
PASS Blender tool-plan execution quality validation: steps=25 non_manifold=0 material_roles=1 socket_panels=0
PASS generation pipeline validation: commands=26 json=223 include_blender=false
PASS generation pipeline validation: commands=36 json=223 include_blender=true
```

The full default tool-plan bundle now contains:

| Plan | Family | Steps | Unique tools |
| --- | --- | ---: | ---: |
| `gothic_stone_banister_post_tool_plan_v0_compiled` | `banister_post` | 32 | 24 |
| `gothic_stone_fence_post_tool_plan_v0_compiled` | `fence_post` | 32 | 24 |
| `gothic_stone_column_tool_plan_v0_compiled` | `column` | 31 | 24 |
| `gothic_stone_window_frame_tool_plan_v0_compiled` | `window_frame` | 25 | 22 |
| `gothic_stone_door_frame_tool_plan_v0_compiled` | `door_frame` | 25 | 22 |

## Boundary

The door-frame design lives in the source recipe and sequence policy. Blender still consumes compiled deterministic JSON and writes `.blend`, preview, and `.glb` outputs only under `/tmp`.
