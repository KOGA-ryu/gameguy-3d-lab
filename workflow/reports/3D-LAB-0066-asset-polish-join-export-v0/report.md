# 3D-LAB-0066 Asset Polish Join Export v0

## Result

Added the completed asset polish join/export adapter.

```text
completed asset_polish_blender_execution_report_v0
plus pre-join polished .blend
-> join visible polish mesh objects
-> preserve material slots and polish_uv0
-> save joined .blend
-> export GLB
-> validate join/export report
```

This slice does not add design logic. It consumes the already completed polish execution output:

```text
/tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
/tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_v0.blend
```

## Changed

```text
data/architecture/asset_mill/asset_generation_registry_v0.json
scripts/audit_script_orbit_v0.py
scripts/export_asset_polish_joined_v0.py
scripts/validate_asset_generation_registry_v0.py
scripts/validate_asset_polish_join_export_report_v0.py
scripts/validate_generation_pipeline_v0.py
tests/test_asset_polish_join_export_v0.py
tests/test_asset_mill_retirement_readiness_v0.py
tests/test_audit_script_orbit_v0.py
tests/test_validate_asset_generation_registry_v0.py
workflow/reports/3D-LAB-0013-asset-mill-retirement-readiness/replacement_decision.json
workflow/reports/3D-LAB-0066-asset-polish-join-export-v0/report.md
workflow/reports/3D-LAB-0066-asset-polish-join-export-v0/receipt.json
```

## Execution Behavior

The new adapter:

```text
scripts/export_asset_polish_joined_v0.py
```

performs:

```text
join_objects
save_blend_file
export_gltf
```

It writes generated outputs only under:

```text
/tmp/gameguy_asset_polish_join_export_v0
```

Generated files:

```text
/tmp/gameguy_asset_polish_join_export_v0/asset_polish_joined_v0.blend
/tmp/gameguy_asset_polish_join_export_v0/blocky_fence_post_polished_joined_v0.glb
/tmp/gameguy_asset_polish_join_export_v0/asset_polish_join_export_report_v0.json
```

The join/export report confirms:

```text
prejoin_mesh_object_count=8
prejoin_asset_polish_generated_object_count=1
prejoin_uv_loop_count=2160
joined_mesh_object_count=1
joined_object_name=blocky_fence_post_polished_joined_v0
joined_vertex_count=592
joined_face_count=552
joined_uv_layer=polish_uv0
joined_uv_loop_count=2160
joined_material_slot_count=7
glb_file_size_bytes=65352
```

The GLB was imported back into Blender as a smoke check:

```text
mesh_object_count=1
vertices=1659
faces=1056
materials=6
uv_layers=1
uv_loops=3168
```

The GLB counts differ from the joined `.blend` because glTF export/import triangulates/splits primitives for material and UV boundaries. The validation target is not identical Blender mesh topology; it is readable one-object export with materials and UVs present.

## Registry

The asset polish source bundle now declares:

```text
join_export_adapter: scripts/export_asset_polish_joined_v0.py
join_export_report_validator: scripts/validate_asset_polish_join_export_report_v0.py
```

The Blender-inclusive pipeline now has labels for:

```text
asset_polish_blender_join_export
asset_polish_join_export_report_validate
```

Script orbit now reports:

```text
scripts=89
KEEP_CANONICAL=30
REFERENCE_ONLY=59
DELETE_LATER=0
```

## Boundary

The join/export adapter does not:

```text
read source recipes
run the asset pump
invent polish operations
mutate source asset JSON
write generated mesh/media into the repo
```

## Validation

```text
python3 -m py_compile scripts/export_asset_polish_joined_v0.py scripts/validate_asset_polish_join_export_report_v0.py scripts/validate_asset_polish_blender_adapter_v0.py scripts/execute_asset_polish_blender_adapter_v0.py scripts/validate_asset_polish_blender_execution_report_v0.py scripts/validate_asset_generation_registry_v0.py scripts/validate_generation_pipeline_v0.py scripts/audit_script_orbit_v0.py
PASS

python3 -m unittest tests/test_asset_polish_blender_adapter_v0.py tests/test_asset_polish_blender_execution_report_v0.py tests/test_asset_polish_join_export_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 27 tests

python3 scripts/compile_asset_polish_tool_plan_v0.py --clean --out /tmp/gameguy_asset_polish_tool_plan_v0
PASS asset polish tool-plan compile: plans=1 steps=10 targets=8 out=/tmp/gameguy_asset_polish_tool_plan_v0

python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json --clean --out /tmp/gameguy_blocky_shape_grammar_asset_pump_v0
pumped assets=2 vertices=320 faces=228 out=/tmp/gameguy_blocky_shape_grammar_asset_pump_v0

python3 scripts/validate_asset_polish_blender_adapter_v0.py --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --json-report /tmp/gameguy_asset_polish_blender_adapter_0066.json
WARN asset polish Blender adapter validation: status=warn supported=10 future=0 warnings=5 errors=0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/execute_asset_polish_blender_adapter_v0.py -- --plan /tmp/gameguy_asset_polish_tool_plan_v0/plans/blocky_fence_post_asset_polish_plan_v0_compiled.json --asset /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/assets/blocky_fence_post_v0.json --out /tmp/gameguy_asset_polish_blender_execution_v0
PASS asset polish Blender execution: executed=10 skipped_future=0 out=/tmp/gameguy_asset_polish_blender_execution_v0

python3 scripts/validate_asset_polish_blender_execution_report_v0.py --report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json
PASS asset polish Blender execution report validation: executed=10 skipped_future=0

python3 scripts/export_asset_polish_joined_v0.py --execution-report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json --validate-only --json-report /tmp/gameguy_asset_polish_join_export_validate_only_0066.json
PASS asset polish join/export validation: source_meshes=8 source_uv_loops=2160 future=0

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/export_asset_polish_joined_v0.py -- --execution-report /tmp/gameguy_asset_polish_blender_execution_v0/asset_polish_execution_report_v0.json --out /tmp/gameguy_asset_polish_join_export_v0 --export-glb
PASS asset polish join/export: prejoin_meshes=8 joined_meshes=1 uv_loops=2160 glb_written=true out=/tmp/gameguy_asset_polish_join_export_v0

python3 scripts/validate_asset_polish_join_export_report_v0.py --report /tmp/gameguy_asset_polish_join_export_v0/asset_polish_join_export_report_v0.json
PASS asset polish join/export report validation: joined_meshes=1 glb_written=true

/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr '<glb import inspection>'
GLB_IMPORT_INSPECTION mesh_object_count=1 materials=6 uv_layers=1

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0066.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0066.json
PASS script orbit audit: scripts=89 KEEP_CANONICAL=30, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0066_join_export_final.json
PASS generation pipeline validation: commands=43 json=272 include_blender=false
```

## Next

The first asset polish lane now reaches an exportable GLB. The next useful slice is export inspection/packaging: validate exported material names, object naming, origin/bounds, and add a tiny game-engine-facing metadata report without moving GLB files into the repo.
