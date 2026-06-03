# Blender Tool Plan Dictionary v0

This slice adds the first source-side tool-planning layer for near-finished procedural assets.

The path is:

```text
asset intent recipe
-> Blender tool dictionary
-> staged tool-plan compiler
-> deterministic gameguy_tool_plan_v0 JSON
-> future Blender execution adapter
```

The new dictionary classifies scriptable Blender-capable operations by stage:

- `base_form`
- `assembly`
- `shape_refinement`
- `sculpt_detail`
- `retopo_cleanup`
- `uv_mapping`
- `material_texture`
- `validation_export`

Evidence:

- `blender_tool_dictionary_v0`: 97 tools
- `gothic_stone_banister_post_tool_plan_v0_compiled`: 32 ordered steps
- Unique tools used by the plan: 24
- Covered stages: 8
- Non-deterministic steps: 0

No Blender execution adapter was added in this slice. The compiler validates and writes a plan only; generated media and mesh outputs remain outside the repo.
