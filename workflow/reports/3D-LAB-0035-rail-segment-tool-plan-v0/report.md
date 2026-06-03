# Rail Segment Tool Plan v0

This slice adds the first canonical modular rail segment to the default architectural tool-plan bundle.

## Source Path

```text
architectural_tool_plan_recipes_v0.json rail_segment asset
-> asset_family_tool_sequence_policy_v0.json rail_segment policy
-> scripts/compile_blender_tool_plan_v0.py rail_segment_blocks
-> deterministic gameguy_tool_plan_v0 JSON
-> scripts/execute_blender_tool_plan_v0.py adapter
```

## Asset

```text
gothic_stone_rail_segment_tool_plan_v0
```

The source recipe declares a block-built rail:

```text
rail body
top cap
bottom lip
left connector tab
right connector tab
front raised band
rear raised band
finish_tool_stack
```

The connector tabs are source-authored as simple cube blocks sized to fit post sockets. Blender receives only compiled steps and material roles.

## Current Evidence

```text
compiled tool plans=6 steps=173 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 6 plans, 173 steps, 25 tools
PASS Blender tool-plan adapter validation: steps=28 tools=22
PASS Blender tool-plan execution quality validation: steps=28 non_manifold=0 material_roles=5 socket_panels=0
PASS generation pipeline validation: commands=27 json=226 include_blender=false
PASS generation pipeline validation: commands=39 json=226 include_blender=true
```

## Boundary

The rail segment is source-owned. Blender does not choose its block layout, connector dimensions, material regions, bevels, UVs, cleanup, preview, or export behavior.
