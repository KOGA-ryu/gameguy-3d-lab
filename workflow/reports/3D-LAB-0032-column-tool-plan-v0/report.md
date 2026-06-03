# Column Tool Plan v0

This slice makes the declared `column` tool-sequence policy real in the default tool-plan bundle.

## Source Path

```text
architectural_tool_plan_recipes_v0.json
-> asset_family_tool_sequence_policy_v0
-> scripts/compile_blender_tool_plan_v0.py
-> gameguy_tool_plan_v0 JSON
-> scripts/execute_blender_tool_plan_v0.py
-> scripts/validate_blender_tool_plan_execution_report_v0.py
```

## Added Asset

```text
gothic_stone_column_tool_plan_v0
```

The source recipe describes the intended shape sequence directly:

```text
square base
-> low-vertex circular transition ring
-> low-vertex fluted/ribbed shaft
-> low-vertex circular transition ring
-> square top cap
```

The column uses simple mesh primitives but keeps the shape more expressive through tool sequence and parameters:

- total size `0.56 m x 0.56 m x 1.38 m`
- base stack: `0.56 m`, `0.46 m`, and `0.36 m` square blocks
- circular transition rings: `8` vertices, `0.24 m` radius
- shaft core: `8` vertices, `0.17 m` radius, `0.82 m` height
- shaft ribs: `8` radial block ribs
- square cap: `0.36 m` neck and `0.54 m` top block

## Current Evidence

```text
compiled tool plans=5 steps=145 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 5 plans, 145 steps, 25 tools
PASS Blender tool-plan adapter validation: steps=31 tools=24
PASS Blender tool-plan execution quality validation: steps=31 non_manifold=0 material_roles=5 socket_panels=0
PASS generation pipeline validation: commands=26 json=225 include_blender=false
PASS generation pipeline validation: commands=36 json=225 include_blender=true
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

The column design lives in the source recipe and policy. The compiler emits deterministic `gameguy_tool_plan_v0` JSON. Blender only consumes that JSON and writes generated `.blend`, preview, and `.glb` outputs under `/tmp`.
