# Asset Mill Retirement Readiness

This packet marks six replaced Asset Mill scripts as `DELETE_LATER` without deleting or moving files.

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

They remain in the repo for now. Actual deletion should be a separate explicit task after running the current source validators, pump, generated-asset validator, and Blender adapter validation.
