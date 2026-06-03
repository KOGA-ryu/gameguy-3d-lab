# 3D-LAB-0061 Asset Polish Inset Faces Execution v0

## Result

Promoted `inset_faces` from a recognized future operation to a first execution Blender polish operation.

```text
compiled asset_polish_tool_plan_v0
plus gameguy_asset_v0 source mesh
-> Blender adapter
-> inset side faces into fielded panels
-> material assignment marks recessed panel faces
-> execution report
```

This slice now executes:

```text
inset_faces / inset_faces
modifier_bevel / chamfer_edges / bevel_edges
material_assign_by_part / material_assign
modifier_weighted_normal / weighted_normals
```

It still skips recognized future steps:

```text
extrude_along_normals
boolean_cut
sweep_profile
uv_unwrap
```

## Changed

```text
scripts/validate_asset_polish_blender_adapter_v0.py
scripts/execute_asset_polish_blender_adapter_v0.py
scripts/validate_asset_polish_blender_execution_report_v0.py
tests/test_asset_polish_blender_adapter_v0.py
tests/test_asset_polish_blender_execution_report_v0.py
workflow/reports/3D-LAB-0061-asset-polish-inset-faces-execution-v0/report.md
workflow/reports/3D-LAB-0061-asset-polish-inset-faces-execution-v0/receipt.json
```

## Execution Behavior

The executor consumes:

```text
/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json
/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json
```

It creates real recessed center faces and four reveal border faces per selected quad side face:

```text
inset_plinth_fielded_panels -> square_foot front/back/left/right
inset_shaft_side_panels -> post_core front/back/left/right
```

The executed Blender report confirms:

```text
inset_panel_face_count=8
inset_plinth_fielded_panels panel_face_count=4
inset_shaft_side_panels panel_face_count=4
gothic_stone_panel_shadow assigned_faces=8
```

The saved blend was also inspected after bevel application. The panel-shadow faces remain the four side-center faces on `square_foot` and the four side-center faces on `post_core`.

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
execute unresolved future operations
mutate source JSON
write mesh/media outputs into the repo
```

## Validation

```text
python3 -m py_compile scripts/validate_asset_polish_blender_adapter_v0.py scripts/execute_asset_polish_blender_adapter_v0.py scripts/validate_asset_polish_blender_execution_report_v0.py scripts/validate_asset_generation_registry_v0.py scripts/validate_generation_pipeline_v0.py scripts/audit_script_orbit_v0.py
PASS

python3 -m unittest tests/test_asset_polish_blender_adapter_v0.py tests/test_asset_polish_blender_execution_report_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 24 tests

python3 scripts/compile_asset_polish_tool_plan_v0.py --clean --out /tmp/gameguy_asset_polish_tool_plan_v0
PASS asset polish tool-plan compile: plans=1 steps=10 targets=8 out=/tmp/gameguy_asset_polish_tool_plan_v0

python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json --clean --out /tmp/gameguy_blocky_shape_grammar_asset_pump_v0
pumped assets=2 vertices=320 faces=228 out=/tmp/gameguy_blocky_shape_grammar_asset_pump_v0

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0061.json
WARN asset polish Blender adapter validation: status=warn supported=6 future=4 warnings=11 errors=0

python3 scripts/execute_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_executor_validate_only_0061.json
PASS asset polish Blender executor validation: supported=6 future=4 asset=blocky_fence_post_v0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=6 skipped_future=4 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=6 skipped_future=4

/Applications/Blender.app/Contents/MacOS/Blender --background /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend --python-expr '<panel face inspection>'
PANEL_FACE_INSPECTION square_foot=4 post_core=4

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0061.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0061.json
PASS script orbit audit: scripts=87 KEEP_CANONICAL=28, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0061_asset_polish_inset_faces_final.json
PASS generation pipeline validation: commands=43 json=267 include_blender=false
```

## Next

The next execution slice should make `extrude_along_normals` real for lips, raised ribs, and relief bands. That turns flat fielded panels into layered ornament instead of only recessed center faces.
