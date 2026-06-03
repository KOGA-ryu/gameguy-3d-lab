# Gameguy Tool Plan Validator v0

This slice adds a standalone validation gate for compiled `gameguy_tool_plan_v0` JSON before Blender adapter execution.

The path is:

```text
asset intent recipe
-> compile_blender_tool_plan_v0.py
-> deterministic gameguy_tool_plan_v0 manifest/plans
-> validate_gameguy_tool_plan_v0.py
-> Blender adapter later
```

## Added Gate

The new validator is:

```bash
python3 scripts/validate_gameguy_tool_plan_v0.py \
  --manifest /tmp/gameguy_blender_tool_plan_v0/manifest.json
```

It validates:

- `gameguy_tool_plan_manifest_v0` manifest shape.
- `gameguy_tool_plan_v0` plan schema.
- Required fields from `contracts/gameguy_tool_plan_v0.json`.
- Known tool IDs from `blender_tool_dictionary_v0`.
- Stable contiguous step order.
- Stage order and summary coverage.
- Deterministic steps and zero non-deterministic step count.
- Compiler boundary flags: no Blender import, no Blender execution, no generated media/mesh output.
- False no-claim flags.
- No media, mesh, render, export, or `.blend` files in the tool-plan output root.

## Current Evidence

Validated manifest:

```text
/tmp/gameguy_blender_tool_plan_v0/manifest.json
```

Current measured result:

- Plans: `1`
- Steps: `32`
- Unique tools: `24`
- Generated outputs created by validator: `false`

The validator is normal Python. It does not import Blender, run the compiler, read source intent recipes, or create media/mesh artifacts.

## Boundary

This is a compiled-plan gate, not a generator and not a Blender adapter. It makes the source-to-tool-plan JSON handoff explicit before any Blender execution.
