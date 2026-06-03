# Finish Tool Stack v0

This slice promotes repeated finishing operations from per-asset feature lists into a reusable source-owned finish stack.

## Source Path

```text
geometry_dictionary/operations/finish_tool_stack.json
-> architectural_tool_plan_recipes_v0.json finish_tool_stacks[]
-> scripts/compile_blender_tool_plan_v0.py
-> deterministic gameguy_tool_plan_v0 JSON with source_terms.finish_tool_stack
-> scripts/validate_gameguy_tool_plan_v0.py
-> scripts/execute_blender_tool_plan_v0.py adapter
```

## Default Stack

The canonical bundle now declares one shared stack:

```text
gothic_stone_finish_stack_v0
```

It expands to:

```text
hard_edge_bevels
-> weighted_normals
-> stone_surface_material
-> smart_uvs
-> collision_and_lod_proxy
-> preview_and_export_plan
```

The default assets now reference `finish_tool_stack` instead of listing those six finish features directly. The compiler validates the stack's feature names and tool IDs against the compiler expansion and the Blender tool dictionary before output.

## Current Evidence

```text
compiled tool plans=5 steps=145 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 5 plans, 145 steps, 25 tools
PASS Blender tool-plan adapter validation: steps=31 tools=24
PASS Blender tool-plan execution quality validation: steps=31 non_manifold=0 material_roles=5 socket_panels=0
PASS generation pipeline validation: commands=26 json=225 include_blender=false
PASS generation pipeline validation: commands=36 json=225 include_blender=true
```

## Boundary

Finishing choices now live in source recipe JSON. Blender still receives only compiled `gameguy_tool_plan_v0` steps and does not choose bevel, material, UV, cleanup, preview, or export behavior itself.
