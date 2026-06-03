# 3D-LAB-0059 Asset Polish Blender Adapter Validate Only v0

## Result

Added a validate-only Blender adapter boundary for compiled `asset_polish_tool_plan_v0` JSON.

```text
source polish recipe
-> deterministic compiled polish plan
-> validate-only Blender adapter report
```

This slice does not make the post. It only proves whether the compiled polish plan is ready for a future Blender executor.

## Added

```text
scripts/validate_asset_polish_blender_adapter_v0.py
tests/test_asset_polish_blender_adapter_v0.py
workflow/reports/3D-LAB-0059-asset-polish-blender-adapter-validate-only-v0/report.md
workflow/reports/3D-LAB-0059-asset-polish-blender-adapter-validate-only-v0/receipt.json
```

## Tightened

The source polish plan cleanup now uses the stable target names:

```text
newel.plinth.fielded_panel_faces
newel.cap.lower_outer_ogee_lip
```

The compiled sequence is now:

```text
inset_plinth_fielded_panels
inset_shaft_side_panels
raise_shaft_panel_beads
define_east_west_socket_reveals
sweep_cap_lower_outer_ogee_lip
chamfer_plinth_outer_arrises
bevel_all_visible_hard_edges
assign_gothic_stone_material_slots
apply_weighted_normals
smart_uv_unwrap_visible_parts
```

The compiler and compiled-plan validator now validate selector shapes and require `face_border.from_target` to resolve to another named target.

## Adapter Report

The new adapter reads the compiled polish plan and writes:

```text
asset_polish_blender_adapter_validation_report_v0
```

It reports:

```text
plan_id
source_recipe_id
validation_status
supported_step_count
future_step_count
errors
warnings
step_reports
target_reports
operation_reports
param_reports
stage_reports
```

The current plan reports:

```text
status=warn
supported_step_count=4
future_step_count=6
errors=0
```

Supported now:

```text
modifier_bevel / bevel_edges / chamfer_edges
material_assign_by_part / material_assign
modifier_weighted_normal / weighted_normals
```

Recognized future work:

```text
inset_faces
extrude_faces / extrude_along_normals
modifier_boolean / boolean_cut
curve_bevel_profile / sweep_profile
uv_smart_project / uv_unwrap
```

## Boundary

The adapter is validate-only. It does not:

```text
import Blender
create meshes
apply modifiers
render images
export mesh/media files
mutate source assets
```

## Validation

```text
python3 -m py_compile scripts/compile_asset_polish_tool_plan_v0.py scripts/validate_asset_polish_tool_plan_v0.py scripts/validate_asset_polish_blender_adapter_v0.py scripts/validate_asset_generation_registry_v0.py scripts/validate_generation_pipeline_v0.py scripts/audit_script_orbit_v0.py
PASS

python3 -m unittest tests/test_asset_polish_tool_plan_v0.py tests/test_asset_polish_blender_adapter_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 24 tests

python3 scripts/compile_asset_polish_tool_plan_v0.py --clean --out /tmp/gameguy_asset_polish_tool_plan_v0
PASS asset polish tool-plan compile: plans=1 steps=10 targets=8 out=/tmp/gameguy_asset_polish_tool_plan_v0

python3 scripts/validate_asset_polish_tool_plan_v0.py --manifest /tmp/gameguy_asset_polish_tool_plan_v0/manifest.json --json-report /tmp/gameguy_asset_polish_tool_plan_0059.json
PASS asset polish tool-plan validation: plans=1 steps=10 targets=8

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0059.json
WARN asset polish Blender adapter validation: status=warn supported=4 future=6 warnings=15 errors=0

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0059.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0059.json
PASS script orbit audit: scripts=85 KEEP_CANONICAL=26, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0059_asset_polish_blender_adapter_final.json
PASS generation pipeline validation: commands=42 json=265 include_blender=false
```

## Next

The first execution slice should implement only the supported families: bevel/chamfer, material assignment, and weighted normals. Inset/extrude/boolean/sweep/UV stay future until their selector semantics are proven.
