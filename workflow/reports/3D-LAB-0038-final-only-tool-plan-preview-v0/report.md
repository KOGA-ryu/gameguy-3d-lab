# Final-Only Tool Plan Preview v0

This slice fixes review previews for compiled Blender tool plans.

## Source Path

```text
architectural_tool_plan_recipes_v0.json finish_tool_stack.preview
-> scripts/compile_blender_tool_plan_v0.py render_workbench_preview params
-> deterministic gameguy_tool_plan_v0 JSON
-> scripts/execute_blender_tool_plan_v0.py helper visibility before camera framing
```

## Change

The shared finish stack now declares:

```text
preview.visibility = final_asset_only
preview.hide_validation_helpers = true
```

The compiler writes those fields into the `render_workbench_preview` step. The Blender adapter tags collision proxies and LOD variants as preview helpers, then hides them from viewport/render before camera framing when the compiled plan requests final-only visibility.

The helpers are still generated. They still exist in the `.blend`, execution report, and export evidence. They are only hidden from the Workbench review PNG.

## Current Evidence

```text
compiled tool plans=7 steps=219 tools=97 out=<validate-only>
PASS Blender tool-plan execution quality validation: steps=46 non_manifold=0 material_roles=9 socket_panels=0
preview_visibility.hidden_helpers = collision_proxy, gothic_panel_guard_tool_plan_v0_LOD1
PASS generation pipeline validation: commands=29 json=230 include_blender=false
PASS generation pipeline validation: commands=43 json=230 include_blender=true
```

## Boundary

This changes preview visibility only. It does not remove collision proxies, LOD variants, validation evidence, or exported helper objects.
