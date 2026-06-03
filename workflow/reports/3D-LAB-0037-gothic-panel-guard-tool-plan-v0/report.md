# Gothic Panel Guard Tool Plan v0

This slice turns the `gothic_panel_guard_reference_v0` dissection packet into the first generated guard-panel tool plan.

## Source Path

```text
gothic_panel_guard_reference_v0.json
-> architectural_tool_plan_recipes_v0.json guard_panel asset
-> asset_family_tool_sequence_policy_v0.json guard_panel policy
-> scripts/compile_blender_tool_plan_v0.py gothic_panel_guard_blocks
-> deterministic gameguy_tool_plan_v0 JSON
-> scripts/execute_blender_tool_plan_v0.py adapter
```

## Asset

```text
gothic_panel_guard_tool_plan_v0
```

The source recipe declares:

```text
left and right square piers
stepped pier bases
heavy pier caps
low-poly finials
solid center guard panel
panel socket collars
top coping rail
lower molding stack
raised center panel trim
low-vertex pointed-arch recess plates
finish_tool_stack
```

The pointed recesses use `mesh_from_pydata` with explicit low-vertex profile prisms. That keeps the complex silhouette source-owned without turning Blender into a design engine.

## Current Evidence

```text
compiled tool plans=7 steps=219 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 7 plans, 219 steps, 26 tools
PASS Blender tool-plan adapter validation: steps=46 tools=24
PASS Blender tool-plan execution quality validation: steps=46 non_manifold=0 material_roles=9 socket_panels=0
PASS generation pipeline validation: commands=29 json=229 include_blender=false
PASS generation pipeline validation: commands=43 json=229 include_blender=true
```

## Boundary

This is a reference-led decorative/game asset prototype. It is not a code-compliant guardrail, historical reconstruction, fabrication drawing, or production approval claim.
