# Asset Mill Retirement Readiness

This packet originally marked six replaced Asset Mill scripts as `DELETE_LATER`. They have now been removed from `scripts/` after canonical replacement validation.

The replacement path is now:

```text
source recipe -> scripts/asset_pump_v0.py -> gameguy_asset_v0 JSON -> validator/adapters
```

Retirement candidates:

- `scripts/compile_asset_mill_solids_v0.py`
- `scripts/blender_asset_mill_smoke_test_v0.py`
- `scripts/compile_asset_mill_measured_components_v1.py`
- `scripts/compile_asset_mill_measured_components_v2.py`
- `scripts/blender_asset_mill_measured_components_v1.py`
- `scripts/blender_asset_mill_measured_components_v2.py`

Their useful value is preserved by source recipes, `asset_pump_v0.py`, generated `gameguy_asset_v0`, the tool-plan validator, Blender adapters, and the generation pipeline validator.
