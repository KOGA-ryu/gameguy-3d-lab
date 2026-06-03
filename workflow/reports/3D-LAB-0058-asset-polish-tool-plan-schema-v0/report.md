# 3D-LAB-0058 Asset Polish Tool Plan Schema v0

## Result

Added the first source-owned asset polish plan compiler and validator.

```text
gameguy_asset_v0 source asset reference
-> named architectural polish targets
-> ordered polish operation sequence
-> deterministic asset_polish_tool_plan_v0 JSON
```

## Added

```text
geometry_dictionary/operations/asset_polish_tool_plan.json
data/architecture/asset_mill/polish_recipes/asset_polish_tool_plan_recipes_v0.json
scripts/compile_asset_polish_tool_plan_v0.py
scripts/validate_asset_polish_tool_plan_v0.py
tests/test_asset_polish_tool_plan_v0.py
```

The first recipe compiles a polish plan for `blocky_fence_post_v0`:

- `8` named targets
- `10` ordered steps
- `8` unique Blender tool dictionary IDs
- source asset schema: `gameguy_asset_v0`
- output schema: `asset_polish_tool_plan_v0`

It names targets such as:

```text
newel.plinth.outer_arrises
newel.plinth.panel_faces
newel.shaft.panel_lips
newel.rail_sockets.east_west
newel.cap.ogee_lip
newel.all.visible_parts
```

And operations such as:

```text
chamfer_edges
inset_faces
extrude_along_normals
boolean_cut
sweep_profile
bevel_edges
material_assign
weighted_normals
uv_unwrap
```

## Registry And Pipeline

Added a new canonical source lane:

```text
source_asset_polish_plan_bundles
```

Pipeline labels:

```text
asset_polish_tool_plan_compile_validate_only
asset_polish_tool_plan_compile
asset_polish_tool_plan_validate
```

Script orbit now classifies both new scripts as `KEEP_CANONICAL`.

## Validation

```text
python3 -m py_compile scripts/compile_asset_polish_tool_plan_v0.py scripts/validate_asset_polish_tool_plan_v0.py scripts/validate_asset_generation_registry_v0.py scripts/validate_generation_pipeline_v0.py scripts/audit_script_orbit_v0.py
PASS

python3 -m unittest tests/test_asset_polish_tool_plan_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 20 tests

python3 scripts/compile_asset_polish_tool_plan_v0.py --clean --out /tmp/gameguy_asset_polish_tool_plan_v0
PASS asset polish tool-plan compile: plans=1 steps=10 targets=8 out=/tmp/gameguy_asset_polish_tool_plan_v0

python3 scripts/validate_asset_polish_tool_plan_v0.py --manifest /tmp/gameguy_asset_polish_tool_plan_v0/manifest.json --json-report /tmp/gameguy_asset_polish_tool_plan_0058.json
PASS asset polish tool-plan validation: plans=1 steps=10 targets=8

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/gameguy_registry_0058.json
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0058.json
PASS script orbit audit: scripts=84 KEEP_CANONICAL=25, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0058_asset_polish_tool_plan_final.json
PASS generation pipeline validation: commands=41 json=264 include_blender=false
```

## Boundary

No Blender execution, generated mesh, generated media, or adapter behavior was added. The source recipe owns the design choices; Blender remains a future executor.

## Next

Add a Blender adapter path for `asset_polish_tool_plan_v0` only after the source plan is reviewed. The adapter should execute the compiled plan and must not decide new polish targets or operations.
