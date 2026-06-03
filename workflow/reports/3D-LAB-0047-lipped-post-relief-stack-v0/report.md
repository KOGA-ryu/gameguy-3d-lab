# 3D-LAB-0047 Lipped Post Relief Stack Prototype

## Result

Added a source-owned `relief_stack` slice for varying ornamental thickness on a square railing/post context prototype.

```text
railing_plinth_ogee_base_side_profile_v0
-> tuned profiled plinth
-> square post core
-> four face-mounted recessed panels
-> raised outer lips
-> higher inner bead lips
-> profiled_plinth_lipped_post_context_tool_plan_v0
-> deterministic gameguy_tool_plan_v0 JSON
-> Blender adapter preview
```

## Source Decisions

- Blender remains an adapter: it consumes compiled cube/profile operations and does not own the ornament design.
- The lipped detail is controlled by source recipe parameters, not hand-modeled Blender decisions.
- Each post face receives one recessed field, four outer lip runs, and four inner bead runs.
- Projection depths increase by layer: `0.003m` recess, `0.012m` outer lip, `0.018m` inner bead.
- The relief uses a `0.001m` gap between lip/bead runs so Blender cleanup does not merge exact corner overlaps into bad topology.
- The post core stays square and blocky; the visual complexity comes from layered 2D rectangles extruded at different depths.

## Compiled Plan

- Asset: `profiled_plinth_lipped_post_context_tool_plan_v0`
- Family: `context_prototype`
- Plan: `profiled_plinth_lipped_post_context_tool_plan_v0_compiled`
- Steps: `59`
- Unique tools: `23`
- Source construction steps: `mesh_from_pydata`, `primitive_cube_add`, `join_objects`
- Relief operation: `relief_stack`
- Relief faces: `4`
- Relief parts: `36`
- Relief layers: `recess_field`, `outer_lip`, `inner_bead`
- Lip panel size: `0.108m x 0.42m`

## Blender Execution

- Render: `/tmp/gameguy_profiled_plinth_lipped_post_context_execution_v0_0047/tool_plan_execution_v0_workbench.png`
- Export: `/tmp/gameguy_profiled_plinth_lipped_post_context_execution_v0_0047/tool_plan_execution_v0.glb`
- Blend: `/tmp/gameguy_profiled_plinth_lipped_post_context_execution_v0_0047/tool_plan_execution_v0.blend`
- Final object: `1214` vertices, `2456` edges, `1318` faces
- Material roles: `base`, `shaft`, `recess`, `trim`, `rib`
- Non-manifold edges after cleanup: `0`

## Validation

```text
python3 -m unittest discover -s tests
OK, 129 tests

python3 scripts/compile_blender_tool_plan_v0.py --validate-only
compiled tool plans=10 steps=334 tools=97 out=<validate-only>

python3 scripts/validate_gameguy_tool_plan_v0.py --manifest /tmp/gameguy_blender_tool_plan_v0_0047_probe/manifest.json
PASS gameguy_tool_plan_v0 validation: 10 plans, 334 steps, 28 tools

python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0_0047_probe/plans/profiled_plinth_lipped_post_context_tool_plan_v0_compiled.json --validate-only
PASS Blender tool-plan adapter validation: steps=59 tools=23

python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_profiled_plinth_lipped_post_context_execution_v0_0047/tool_plan_execution_v0_report.json
PASS Blender tool-plan execution quality validation: steps=59 non_manifold=0 material_roles=5 socket_panels=0

python3 scripts/validate_generation_pipeline_v0.py --json-report /tmp/gameguy_pipeline_0047_final.json
PASS generation pipeline validation: commands=34 json=242 include_blender=false

python3 scripts/validate_generation_pipeline_v0.py --include-blender --json-report /tmp/gameguy_pipeline_blender_0047_final.json
PASS generation pipeline validation: commands=48 json=242 include_blender=true
```

## Next

The next slice should tune one ornamental face detail instead of broadening the asset family: add a source-selectable 2D profile shape for the recessed panel field, such as an arched panel or stepped quatrefoil panel, then reuse the same relief-stack projection logic.
