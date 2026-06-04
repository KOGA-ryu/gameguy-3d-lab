# 3D-LAB-0063 Asset Polish Boolean Socket Reveals v0

## Result

Promoted `boolean_cut` / `modifier_boolean` from future warning to first execution Blender polish logic.

```text
compiled asset_polish_tool_plan_v0
plus gameguy_asset_v0 source mesh
-> inset panels
-> raised shaft panel lips
-> boolean cut east/west socket reveals into post_core
-> leave socket-shadow source parts visible
-> execution report
```

This slice now executes:

```text
inset_faces / inset_faces
extrude_along_normals / extrude_faces
boolean_cut / modifier_boolean
modifier_bevel / chamfer_edges / bevel_edges
material_assign_by_part / material_assign
modifier_weighted_normal / weighted_normals
```

It still skips recognized future steps:

```text
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
workflow/reports/3D-LAB-0063-asset-polish-boolean-socket-reveals-v0/report.md
workflow/reports/3D-LAB-0063-asset-polish-boolean-socket-reveals-v0/receipt.json
```

## Execution Behavior

The executor consumes:

```text
/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json
/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json
```

It uses the existing plan target:

```text
define_east_west_socket_reveals
operation: boolean_cut
tool_id: modifier_boolean
target: newel.rail_sockets.east_west
selector: part_ids rail_socket_east rail_socket_west
```

The adapter creates temporary east/west cutter boxes from the socket source-part bounds, expands the cutter inward to the requested `cut_depth_m`, applies `DIFFERENCE` booleans to `post_core`, then removes the temporary cutter objects. The original socket source parts remain visible as dark socket-shadow panels.

The generated boolean pass creates:

```text
boolean_cut_count=2
socket_shadow_panel_count=2
applied_modifier_count=2
failed_modifier_count=0
cut_depth_m=0.026
cutter_objects_removed=true
```

After bevel and material assignment, the saved Blender report confirms:

```text
executed_step_count=8
skipped_future_step_count=2
gothic_stone_socket_shadow assigned_faces=12
gothic_stone_trim_highlight assigned_faces=236
```

The saved blend was inspected after bevel application:

```text
cutter objects=0
mesh objects=7
rail_socket_east socket_shadow_faces=6
rail_socket_west socket_shadow_faces=6
post_core face_count=244
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

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0063.json
WARN asset polish Blender adapter validation: status=warn supported=8 future=2 warnings=8 errors=0

python3 scripts/execute_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_executor_validate_only_0063.json
PASS asset polish Blender executor validation: supported=8 future=2 asset=blocky_fence_post_v0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=8 skipped_future=2 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=8 skipped_future=2

/Applications/Blender.app/Contents/MacOS/Blender --background /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend --python-expr '<socket boolean inspection>'
SOCKET_BOOLEAN_INSPECTION cutters=0 mesh_objects=7 rail_socket_east.shadow_faces=6 rail_socket_west.shadow_faces=6 post_core.faces=244

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0063.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0063.json
PASS script orbit audit: scripts=87 KEEP_CANONICAL=28, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0063_asset_polish_boolean_sockets_final.json
PASS generation pipeline validation: commands=43 json=269 include_blender=false
```

## Next

The next execution slice should make `sweep_profile` real for the cap lower outer ogee lip. That gives the post a proper molded cap profile before the UV/material polish slice.
