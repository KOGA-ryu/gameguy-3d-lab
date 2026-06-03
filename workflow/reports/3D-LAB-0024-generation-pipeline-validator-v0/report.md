# Generation Pipeline Validator v0

This slice adds a canonical orchestration gate for the deterministic 3D generation pipeline.

The path is:

```text
source recipes / dictionaries / contracts
-> asset pump and tool-plan compiler
-> deterministic gameguy_asset_v0 and gameguy_tool_plan_v0 JSON
-> validators and adapter validate-only checks
-> optional Blender execution/report quality gate
```

## Added Gate

The new pipeline validator is:

```bash
python3 scripts/validate_generation_pipeline_v0.py
```

For full Blender execution:

```bash
python3 scripts/validate_generation_pipeline_v0.py --include-blender
```

It orchestrates:

- JSON parse over source/contract/workflow trees.
- Python script compilation.
- Optional unit test discovery.
- Asset generation registry validation.
- Tool-plan compile, asset-family sequence policy enforcement, `gameguy_tool_plan_v0` validation, and Blender adapter validate-only.
- Optional Blender render/export plus execution report validation.
- Tiny fixture and measured component source validation.
- Simple, measured, section-stack, blocky-column, and blocky-shape asset pumps.
- `gameguy_asset_v0` validation for every pump output.
- Blender adapter validate-only checks for generated asset JSON.
- Script orbit audit.
- No `pattern_lab_2d` paths and no repo-local media/mesh/render/export artifacts.

## Current Evidence

Non-Blender pipeline result:

```text
PASS generation pipeline validation: commands=26 json=223 include_blender=false
```

Full Blender pipeline result:

```text
PASS generation pipeline validation: commands=36 json=223 include_blender=true
```

The full run includes:

- `gameguy_tool_plan_v0`: `5` plans, `145` steps, `25` tools
- Asset-family sequence policy: `5` target families
- Blender adapter validate-only: banister post, fence post, column, window frame, and door frame plans
- Banister Blender execution: `32` steps
- Banister execution report validation: non-manifold `0`, material roles `5`, socket panels `2`
- Fence-post Blender execution: `32` steps
- Fence-post execution report validation: non-manifold `0`, material roles `5`, socket panels `2`
- Column Blender execution: `31` steps
- Column execution report validation: non-manifold `0`, material roles `5`, socket panels `0`
- Window-frame Blender execution: `25` steps
- Window-frame execution report validation: non-manifold `0`, material roles `1`, socket panels `0`
- Door-frame Blender execution: `25` steps
- Door-frame execution report validation: non-manifold `0`, material roles `1`, socket panels `0`
- Script orbit after Asset Mill retirement: `73` scripts, `15` canonical, `0` `DELETE_LATER`

Generated outputs remain under `/tmp`; the validator rejects generated media/mesh files inside the repo.

## Boundary

This script is an orchestration validator. It does not add source design decisions, does not replace the asset pump or compiler, and does not make Blender first-class source logic.
