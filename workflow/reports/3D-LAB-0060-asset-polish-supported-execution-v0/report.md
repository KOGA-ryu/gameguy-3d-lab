# 3D-LAB-0060 Asset Polish Supported Execution v0

## Result

Added the first execution slice for compiled `asset_polish_tool_plan_v0`.

```text
compiled asset_polish_tool_plan_v0
plus gameguy_asset_v0 source mesh
-> Blender adapter
-> supported polish operations only
-> execution report
```

This slice executes only:

```text
modifier_bevel / chamfer_edges / bevel_edges
material_assign_by_part / material_assign
modifier_weighted_normal / weighted_normals
```

It skips recognized future steps:

```text
inset_faces
extrude_along_normals
boolean_cut
sweep_profile
uv_unwrap
```

## Added

```text
scripts/execute_asset_polish_blender_adapter_v0.py
scripts/validate_asset_polish_blender_execution_report_v0.py
tests/test_asset_polish_blender_execution_report_v0.py
workflow/reports/3D-LAB-0060-asset-polish-supported-execution-v0/report.md
workflow/reports/3D-LAB-0060-asset-polish-supported-execution-v0/receipt.json
```

## Execution Behavior

The executor consumes:

```text
/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json
/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json
```

It creates Blender objects from the asset mesh parts, then applies the supported polish operations to the source-part targets named by the compiled plan:

```text
chamfer_plinth_outer_arrises -> square_foot, lower_step_band
bevel_all_visible_hard_edges -> square_foot, lower_step_band, post_core, upper_step_band, square_cap
assign_gothic_stone_material_slots -> all source mesh parts by source material role
apply_weighted_normals -> square_foot, lower_step_band, post_core, upper_step_band, square_cap
```

The generated output stays under:

```text
/tmp/gameguy_asset_polish_blender_execution_v0
```

## Boundary

The executor does not:

```text
read source recipes
run the asset pump
invent new polish targets
execute future operations
mutate source JSON
write mesh/media outputs into the repo
```

## Validation

```text
python3 -m py_compile scripts/execute_asset_polish_blender_adapter_v0.py scripts/validate_asset_polish_blender_execution_report_v0.py scripts/validate_asset_polish_blender_adapter_v0.py scripts/validate_asset_generation_registry_v0.py scripts/validate_generation_pipeline_v0.py scripts/audit_script_orbit_v0.py
PASS

python3 -m unittest tests/test_asset_polish_blender_adapter_v0.py tests/test_asset_polish_blender_execution_report_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 24 tests

python3 scripts/compile_asset_polish_tool_plan_v0.py --clean --out /tmp/gameguy_asset_polish_tool_plan_v0
PASS asset polish tool-plan compile: plans=1 steps=10 targets=8 out=/tmp/gameguy_asset_polish_tool_plan_v0

python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json --clean --out /tmp/gameguy_blocky_shape_grammar_asset_pump_v0
pumped assets=2 vertices=320 faces=228 out=/tmp/gameguy_blocky_shape_grammar_asset_pump_v0

python3 scripts/execute_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_executor_validate_only_0060.json
PASS asset polish Blender executor validation: supported=4 future=6 asset=blocky_fence_post_v0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=4 skipped_future=6 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=4 skipped_future=6

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0060.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0060.json
PASS script orbit audit: scripts=87 KEEP_CANONICAL=28, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0060_asset_polish_executor_final.json
PASS generation pipeline validation: commands=43 json=266 include_blender=false
```

## Next

The next execution slice should make one future operation real, probably `inset_faces`, because that unlocks fielded panels and panel lips instead of only whole-part polish.
