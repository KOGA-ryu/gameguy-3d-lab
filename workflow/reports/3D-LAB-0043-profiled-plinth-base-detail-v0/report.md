# 3D-LAB-0043 Profiled Plinth Base Detail

## Result

Added the first standalone `profile_detail` prototype to the canonical tool-plan bundle.

The new source path is:

```text
railing_plinth_ogee_base_side_profile_v0
-> profiled_plinth_base_detail_tool_plan_v0
-> mesh_from_pydata custom polygon extrusion
-> shared finish_tool_stack
-> Blender adapter validate/render/export
```

This keeps the experiment focused on one detail instead of changing the whole railing assembly.

## Shape Contract

- Source profile: `data/architecture/asset_mill/profile_sources/railing_detail_profiles_v0.json`
- Source profile ID: `railing_plinth_ogee_base_side_profile_v0`
- Source control points: `14`
- Initial compiled mesh: `28` vertices, `16` faces
- Final rendered mesh after bevel/displace cleanup: `164` vertices, `313` edges, `151` faces
- Non-manifold edges: `0`
- Render: `/tmp/gameguy_profiled_plinth_detail_execution_v0/tool_plan_execution_v0_workbench.png`

The compiled detail deliberately does not use `primitive_cube_add` or `modifier_boolean`. It starts as one low-point custom polygon and then receives the normal shared finishing pass.

## Repo Changes

- Added `profile_detail` to the asset-family sequence policy.
- Added `profiled_plinth_base_detail_tool_plan_v0` to the architectural tool-plan recipe bundle.
- Added compiler validation, source-term capture, point generation, and step generation for `profiled_plinth_base_detail`.
- Added adapter support for single-object `join_objects` plans, so a one-shape prototype can finalize cleanly without invoking Blender's multi-object join operator.
- Added adapter validate-only coverage for the new profile-detail plan.
- Updated registry, README, and tests for the new eight-plan/eight-family tool-plan surface.

## Validation

```text
python3 -m unittest discover -s tests
124 tests passed

python3 scripts/validate_generation_pipeline_v0.py --json-report /tmp/gameguy_pipeline_0043_final.json
PASS generation pipeline validation: commands=32 json=237 include_blender=false

python3 scripts/validate_generation_pipeline_v0.py --include-blender --json-report /tmp/gameguy_pipeline_blender_0043_final.json
PASS generation pipeline validation: commands=46 json=237 include_blender=true

git diff --check
pass
```
