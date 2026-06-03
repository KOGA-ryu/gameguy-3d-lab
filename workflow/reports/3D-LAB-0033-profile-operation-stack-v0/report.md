# Profile Operation Stack v0

This slice promotes the column's shape source from one-off feature names into a reusable profile/operator grammar.

## Source Path

```text
geometry_dictionary/operations/profile_operation_stack.json
-> architectural_tool_plan_recipes_v0.json profile_operation_stack source block
-> scripts/compile_blender_tool_plan_v0.py
-> deterministic gameguy_tool_plan_v0 JSON with source_terms
-> scripts/validate_gameguy_tool_plan_v0.py
-> scripts/execute_blender_tool_plan_v0.py adapter
```

## Column Grammar

The canonical column source now declares:

```text
square_base
-> circle_transition
-> fluted_shaft
-> circle_transition
-> square_cap
```

The stack uses legal dictionary terms only:

- profiles: `square`, `circle`, `rectangle`
- operators: `profile_operation_stack`, `compound_asset`, `extrude`, `array_radial`
- geometry terms: `profile_operation_stack`, `compound_asset`, `extrude`, `array_radial`, `square`, `circle`, `rectangle`

The compiler expands that source into the same 31 deterministic Blender tool-plan steps as the previous column proof. Blender still receives only compiled primitive, assembly, material, UV, validation, preview, and export steps.

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

The source recipe and geometry dictionary now own the legal profile/operator vocabulary. The compiler validates that vocabulary and preserves it in `source_terms`. The Blender adapter remains a consumer of deterministic JSON and does not make source design decisions.
