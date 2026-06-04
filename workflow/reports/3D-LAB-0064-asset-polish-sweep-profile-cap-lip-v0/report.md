# 3D-LAB-0064 Asset Polish Sweep Profile Cap Lip v0

## Result

Promoted `sweep_profile` / `curve_bevel_profile` from future warning to first execution Blender polish logic.

```text
compiled asset_polish_tool_plan_v0
plus gameguy_asset_v0 source mesh
-> inset panels
-> raised shaft panel lips
-> boolean socket reveals
-> generated cap lower outer ogee lip
-> execution report
```

This slice now executes:

```text
inset_faces / inset_faces
extrude_along_normals / extrude_faces
boolean_cut / modifier_boolean
sweep_profile / curve_bevel_profile
modifier_bevel / chamfer_edges / bevel_edges
material_assign_by_part / material_assign
modifier_weighted_normal / weighted_normals
```

It still skips recognized future steps:

```text
uv_unwrap
```

## Changed

```text
scripts/validate_asset_polish_blender_adapter_v0.py
scripts/execute_asset_polish_blender_adapter_v0.py
scripts/validate_asset_polish_blender_execution_report_v0.py
tests/test_asset_polish_blender_adapter_v0.py
tests/test_asset_polish_blender_execution_report_v0.py
workflow/reports/3D-LAB-0064-asset-polish-sweep-profile-cap-lip-v0/report.md
workflow/reports/3D-LAB-0064-asset-polish-sweep-profile-cap-lip-v0/receipt.json
```

## Execution Behavior

The executor consumes:

```text
/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json
/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json
```

It uses the existing plan target:

```text
sweep_cap_lower_outer_ogee_lip
operation: sweep_profile
tool_id: curve_bevel_profile
target: newel.cap.lower_outer_ogee_lip
selector: edge_band cap_lower_outer_band
profile: small_ogee_over_bead
```

The adapter creates a generated mesh object named:

```text
sweep_cap_lower_outer_ogee_lip
```

The generated profile is a faceted square perimeter molding around the lower cap band:

```text
profile_level_count=6
perimeter_segment_count=8
vertex_count=48
face_count=40
cap_material_face_count=40
projection_m=0.018
height_m=0.032
```

After execution, the saved Blender report confirms:

```text
executed_step_count=9
skipped_future_step_count=1
sweep_profile_object_count=1
sweep_profile_face_count=40
sweep_cap_material_face_count=40
mesh_object_count=8
```

The saved blend was inspected:

```text
sweep_cap_lower_outer_ogee_lip vertex_count=48
sweep_cap_lower_outer_ogee_lip face_count=40
sweep_cap_lower_outer_ogee_lip cap_faces=40
sweep bounds min=-0.2666,-0.2666,1.1
sweep bounds max=0.2666,0.2666,1.132
square_cap bounds min=-0.25,-0.25,1.1
square_cap bounds max=0.25,0.25,1.24
cutter objects=0
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

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0064.json
WARN asset polish Blender adapter validation: status=warn supported=9 future=1 warnings=6 errors=0

python3 scripts/execute_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_executor_validate_only_0064.json
PASS asset polish Blender executor validation: supported=9 future=1 asset=blocky_fence_post_v0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=9 skipped_future=1 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=9 skipped_future=1

/Applications/Blender.app/Contents/MacOS/Blender --background /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend --python-expr '<sweep profile inspection>'
SWEEP_PROFILE_INSPECTION sweep.vertices=48 sweep.faces=40 sweep.cap_faces=40 sweep.bounds=(-0.2666,-0.2666,1.1)..(0.2666,0.2666,1.132)

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0064.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0064.json
PASS script orbit audit: scripts=87 KEEP_CANONICAL=28, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0064_asset_polish_sweep_profile_final.json
PASS generation pipeline validation: commands=43 json=270 include_blender=false
```

## Next

The next execution slice should make `uv_unwrap` real, then the first polish plan will have no future operations left. After that, the useful next step is a join/export pass for the polished asset.
