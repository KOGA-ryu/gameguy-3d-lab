# Asset Mill Delete-Later Retirement v0

This slice removes the six replaced Asset Mill scripts that had been marked `DELETE_LATER`.

Removed scripts:

- `scripts/compile_asset_mill_solids_v0.py`
- `scripts/blender_asset_mill_smoke_test_v0.py`
- `scripts/compile_asset_mill_measured_components_v1.py`
- `scripts/compile_asset_mill_measured_components_v2.py`
- `scripts/blender_asset_mill_measured_components_v1.py`
- `scripts/blender_asset_mill_measured_components_v2.py`

## Replacement Path

Their active value is preserved by:

```text
source recipes
-> scripts/asset_pump_v0.py
-> gameguy_asset_v0 JSON
-> validate_gameguy_asset_v0.py
-> export_blender_* adapters
```

The near-finished Blender construction lane is preserved separately by:

```text
tool-plan source recipe
-> scripts/compile_blender_tool_plan_v0.py
-> validate_gameguy_tool_plan_v0.py
-> scripts/execute_blender_tool_plan_v0.py
-> validate_blender_tool_plan_execution_report_v0.py
```

## Current Evidence

Script orbit after deletion:

```text
PASS script orbit audit: scripts=73 KEEP_CANONICAL=15, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=58, DELETE_LATER=0
```

The generation pipeline validator remains the canonical full gate. Generated outputs remain under `/tmp`; no media, mesh, render, export, or `.blend` output is stored in the repo.

Measured component recipes now keep retired compiler paths only as `legacy_source_script` provenance. Generated measured assets expose that lineage under `source_provenance`; `source_script` is rejected as an active source key.

## Boundary

This is a retirement cleanup. It does not delete source recipes, contracts, geometry dictionary entries, validators, canonical pumps, canonical compilers, or adapters that consume deterministic JSON.
