# Window-Frame Blender Execution Quality v0

This slice extends the Blender execution quality gate beyond the banister post.

## Source Path

```text
architectural_tool_plan_recipes_v0.json
-> scripts/compile_blender_tool_plan_v0.py
-> gameguy_tool_plan_v0 JSON
-> scripts/execute_blender_tool_plan_v0.py
-> scripts/validate_blender_tool_plan_execution_report_v0.py
```

## Added Proof

The full pipeline now executes and validates both default tool plans:

| Plan | Blender steps | Non-manifold edges | Material roles | Socket panels |
| --- | ---: | ---: | ---: | ---: |
| `gothic_stone_banister_post_tool_plan_v0_compiled` | 32 | 0 | 5 | 2 |
| `gothic_stone_window_frame_tool_plan_v0_compiled` | 25 | 0 | 1 | 0 |

The execution report validator is now asset-family aware:

- `banister_post` requires socket booleans, cutter cleanup, material-region preservation, and topology cleanup.
- `window_frame` requires frame material-region preservation, explicit no-socket-required evidence, and topology cleanup.

## Boundary

The Blender executor remains an adapter. It consumes compiled `gameguy_tool_plan_v0` JSON, does not read source intent recipes, does not run the compiler, and writes `.blend`, preview, and `.glb` outputs under `/tmp`.

## Validation

```text
python3 scripts/validate_generation_pipeline_v0.py --include-blender
```

Expected output:

```text
PASS generation pipeline validation: commands=26 json=214 include_blender=true
```

Relevant command evidence:

```text
PASS Blender tool-plan execution quality validation: steps=32 non_manifold=0 material_roles=5 socket_panels=2
PASS Blender tool-plan execution quality validation: steps=25 non_manifold=0 material_roles=1 socket_panels=0
```
