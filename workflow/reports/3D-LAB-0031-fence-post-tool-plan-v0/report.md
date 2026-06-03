# Fence-Post Tool Plan v0

This slice proves the tool-plan lane can add another socketed post asset without moving design logic into Blender.

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
gothic_stone_fence_post_tool_plan_v0
```

The new source recipe uses the `fence_post` policy with parameterized post dimensions:

- total size `0.44 m x 0.44 m x 1.10 m`
- stepped square base blocks: `0.44 m`, `0.36 m`, and `0.30 m` square
- square post core: `0.20 m x 0.20 m x 0.78 m`
- radial rib count: `8`
- rail socket cutter size: `0.14 m x 0.20 m x 0.22 m`
- cap neck/top blocks: `0.28 m` and `0.38 m` square

The compiler now lets post-family recipes drive the stepped base, cap, rib source, rib radius/count, and rail-socket parameters. The default banister dimensions remain unchanged through helper defaults.

## Current Evidence

```text
compiled tool plans=5 steps=145 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 5 plans, 145 steps, 25 tools
PASS Blender tool-plan adapter validation: steps=32 tools=24
PASS Blender tool-plan execution quality validation: steps=32 non_manifold=0 material_roles=5 socket_panels=2
PASS generation pipeline validation: commands=26 json=221 include_blender=false
PASS generation pipeline validation: commands=36 json=221 include_blender=true
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

The fence-post design lives in the source recipe and sequence policy. Blender still consumes compiled deterministic JSON and writes `.blend`, preview, and `.glb` outputs only under `/tmp`.
