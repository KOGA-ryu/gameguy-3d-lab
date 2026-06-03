# 3D-LAB-0062 Asset Polish Extrude Lips Execution v0

## Result

Promoted `extrude_along_normals` / `extrude_faces` from future warning to first execution Blender polish logic.

```text
compiled asset_polish_tool_plan_v0
plus gameguy_asset_v0 source mesh
-> inset panel center faces
-> generate raised lip strips from face_border target
-> bevel and material assignment preserve trim faces
-> execution report
```

This slice now executes:

```text
inset_faces / inset_faces
extrude_along_normals / extrude_faces
modifier_bevel / chamfer_edges / bevel_edges
material_assign_by_part / material_assign
modifier_weighted_normal / weighted_normals
```

It still skips recognized future steps:

```text
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
workflow/reports/3D-LAB-0062-asset-polish-extrude-lips-execution-v0/report.md
workflow/reports/3D-LAB-0062-asset-polish-extrude-lips-execution-v0/receipt.json
```

## Execution Behavior

The executor consumes:

```text
/tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json
/tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json
```

It uses the existing plan target:

```text
raise_shaft_panel_beads
operation: extrude_along_normals
tool_id: extrude_faces
target: newel.shaft.panel_lips
selector: face_border from newel.shaft.side_panels
```

The generated lip geometry is a four-strip raised frame around each inset shaft panel. The operation creates:

```text
panel_face_count=4
lip_surface_count=16
added_vertex_count=128
added_face_count=80
```

After bevels are applied, the saved Blender report confirms:

```text
executed_step_count=7
skipped_future_step_count=3
extruded_lip_surface_count=16
trim_lip_face_count=272
gothic_stone_trim_highlight assigned_faces=272
```

The saved blend was inspected after bevel application:

```text
post_core trim faces=272
post_core panel faces=4
square_foot panel faces=4
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

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0062.json
WARN asset polish Blender adapter validation: status=warn supported=7 future=3 warnings=9 errors=0

python3 scripts/execute_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_executor_validate_only_0062.json
PASS asset polish Blender executor validation: supported=7 future=3 asset=blocky_fence_post_v0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=7 skipped_future=3 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=7 skipped_future=3

/Applications/Blender.app/Contents/MacOS/Blender --background /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend --python-expr '<polish face inspection>'
POLISH_FACE_INSPECTION post_core.trim=272 post_core.panel=4 square_foot.panel=4

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0062.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0062.json
PASS script orbit audit: scripts=87 KEEP_CANONICAL=28, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0062_asset_polish_extrude_lips_final.json
PASS generation pipeline validation: commands=43 json=268 include_blender=false
```

## Next

The next execution slice should make `boolean_cut` real for the east/west rail socket reveals. That gives the post actual receiving geometry for railing assemblies instead of only decorative panel work.
