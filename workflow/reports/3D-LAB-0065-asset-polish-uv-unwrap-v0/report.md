# 3D-LAB-0065 Asset Polish UV Unwrap v0

## Result

Promoted `uv_unwrap` / `uv_smart_project` from future warning to executed Blender polish logic.

```text
compiled asset_polish_tool_plan_v0
plus gameguy_asset_v0 source mesh
-> inset panels
-> raised shaft panel lips
-> boolean socket reveals
-> generated cap lower outer ogee lip
-> material assignment
-> weighted normals
-> smart UV unwrap visible mesh parts
-> execution report
```

The first polish plan now has no unresolved future operations:

```text
supported_step_count=10
future_step_count=0
executed_step_count=10
skipped_future_step_count=0
```

## Changed

```text
scripts/validate_asset_polish_blender_adapter_v0.py
scripts/execute_asset_polish_blender_adapter_v0.py
scripts/validate_asset_polish_blender_execution_report_v0.py
tests/test_asset_polish_blender_adapter_v0.py
tests/test_asset_polish_blender_execution_report_v0.py
workflow/reports/3D-LAB-0065-asset-polish-uv-unwrap-v0/report.md
workflow/reports/3D-LAB-0065-asset-polish-uv-unwrap-v0/receipt.json
```

## Execution Behavior

The executor consumes:

```text
/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json
/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json
```

It uses the existing plan step:

```text
step_id: smart_uv_unwrap_visible_parts
operation: uv_unwrap
tool_id: uv_smart_project
target: newel.all.visible_parts
selector: all_visible_mesh_parts
method: smart_uv_project
island_margin: 0.018
angle_limit_degrees: 66.0
```

The UV operation runs after geometry polish and material assignment. It applies an active UV layer named:

```text
polish_uv0
```

The saved Blender report confirms:

```text
mesh_object_count=8
uv_unwrap_object_count=8
uv_unwrap_loop_count=2160
uv_generated_object_count=1
quality_pass.uv_unwrap_applied=true
```

The saved blend was inspected:

```text
square_foot uv_loops=400 active_uv_layer=polish_uv0
lower_step_band uv_loops=384 active_uv_layer=polish_uv0
post_core uv_loops=976 active_uv_layer=polish_uv0
rail_socket_east uv_loops=24 active_uv_layer=polish_uv0
rail_socket_west uv_loops=24 active_uv_layer=polish_uv0
upper_step_band uv_loops=96 active_uv_layer=polish_uv0
square_cap uv_loops=96 active_uv_layer=polish_uv0
sweep_cap_lower_outer_ogee_lip uv_loops=160 active_uv_layer=polish_uv0
missing_uv_objects=[]
```

The generated output stays under:

```text
/tmp/gameguy_asset_polish_blender_execution_v0
```

## Boundary

The executor still does not:

```text
read source recipes
run the asset pump
invent new polish targets
mutate source JSON
write mesh/media outputs into the repo
join or export the asset
```

## Validation

```text
python3 -m py_compile scripts/validate_asset_polish_blender_adapter_v0.py scripts/execute_asset_polish_blender_adapter_v0.py scripts/validate_asset_polish_blender_execution_report_v0.py
PASS

python3 -m unittest tests/test_asset_polish_blender_adapter_v0.py tests/test_asset_polish_blender_execution_report_v0.py
OK, 8 tests

python3 scripts/compile_asset_polish_tool_plan_v0.py --clean --out /tmp/gameguy_asset_polish_tool_plan_v0
PASS asset polish tool-plan compile: plans=1 steps=10 targets=8 out=/tmp/gameguy_asset_polish_tool_plan_v0

python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json --clean --out /tmp/gameguy_blocky_shape_grammar_asset_pump_v0
pumped assets=2 vertices=320 faces=228 out=/tmp/gameguy_blocky_shape_grammar_asset_pump_v0

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0065.json
WARN asset polish Blender adapter validation: status=warn supported=10 future=0 warnings=5 errors=0

python3 scripts/execute_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_executor_validate_only_0065.json
PASS asset polish Blender executor validation: supported=10 future=0 asset=blocky_fence_post_v0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=10 skipped_future=0 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=10 skipped_future=0

/Applications/Blender.app/Contents/MacOS/Blender --background /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend --python-expr '<uv inspection>'
UV_INSPECTION mesh_object_count=8 total_uv_loops=2160 generated_uv_object_count=1 missing_uv_objects=[]

python3 -m unittest tests/test_asset_polish_blender_adapter_v0.py tests/test_asset_polish_blender_execution_report_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 24 tests

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0065.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0065.json
PASS script orbit audit: scripts=87 KEEP_CANONICAL=28, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0065_asset_polish_uv_final.json
PASS generation pipeline validation: commands=43 json=271 include_blender=false
```

## Next

The first polish plan is now fully executable. The next useful slice is a join/export pass that consumes this pre-join `.blend`, joins the separate polish objects into an exportable mesh, validates object/material/UV preservation, and writes export artifacts only under `/tmp`.
