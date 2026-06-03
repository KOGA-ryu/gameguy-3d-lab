# 3D-LAB-0041 Railing Detail Tool-Plan Compiler

This slice turns the source-only railing 2D detail profiles into executable guard-panel tool-plan steps.

The new path is:

```text
railing_detail_profiles_v0.json
-> architectural_tool_plan_recipes_v0.json railing_detail_profile_stack
-> scripts/compile_blender_tool_plan_v0.py
-> deterministic gameguy_tool_plan_v0 JSON
-> scripts/execute_blender_tool_plan_v0.py adapter execution
```

## What Changed

- The gothic guard-panel recipe now selects six source detail profiles:
  - `railing_square_frame_block_v0`
  - `railing_pointed_arch_recess_v0`
  - `railing_capsule_vertical_slot_v0`
  - `railing_circle_bead_strip_v0`
  - `railing_ogee_molding_side_profile_v0`
  - `railing_trapezoid_transition_collar_v0`
- The guard-panel sequence policy now allows `railing_detail_profile_stack` plus deterministic `modifier_boolean`, `modifier_mirror`, and `modifier_array` assembly tools.
- The compiler validates the selected profile bundle, rejects mismatched guard-panel detail profile lists, records profile provenance in `source_terms`, and expands the stack into cutter, shadow, trim, mirror, boolean, and array steps.
- The Blender adapter now supports deterministic mirror and array execution for generated detail meshes.
- The execution report validator now distinguishes post socket booleans from guard-panel decorative detail booleans.

## Guard-Panel Result

`gothic_panel_guard_tool_plan_v0_compiled` now has:

- `57` steps
- `27` unique adapter tools
- `railing_detail_profile_stack`, `gothic_panel_guard_blocks`, and `finish_tool_stack`
- three boolean cutters applied to `center_guard_panel`
- mirrored capsule side details
- nine lower bead trim instances
- ogee trim and tapered socket-collar trim

The full Blender execution report records:

```text
applied boolean modifiers: 3
failed boolean modifiers: 0
material roles: 10
non-manifold before cleanup: 36
non-manifold after cleanup: 0
```

The pre-cleanup non-manifold count is now allowed only for this guard-panel quality profile, and the final validated count still must be `0`.

## Validation

```text
compiled tool plans=7 steps=230 tools=97 out=/tmp/gameguy_blender_tool_plan_v0_0041
PASS gameguy_tool_plan_v0 validation: 7 plans, 230 steps, 28 tools
PASS Blender tool-plan adapter validation: steps=57 tools=27
PASS Blender tool-plan execution quality validation: steps=57 non_manifold=0 material_roles=10 socket_panels=0
PASS generation pipeline validation: commands=31 json=235 include_blender=false
PASS generation pipeline validation: commands=45 json=235 include_blender=true
```

No repo-local media, mesh, render, export, or `.blend` files were produced.

## Boundary

Blender still does not decide the design. The source recipe and compiler decide the shapes and sequence. Blender consumes deterministic JSON and executes supported adapter steps.
