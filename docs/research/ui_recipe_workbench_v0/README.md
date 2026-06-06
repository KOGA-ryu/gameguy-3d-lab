# UI Recipe Workbench V0

This lane defines a human control surface for the deterministic recipe pipeline.

The primary UI target is now a blank Blender tool-plan workbench, not a
single-recipe editor. It is not a modeling app and not a render gallery. It is a
compact plan editor:

```text
blank gameguy_tool_plan_v0
-> choose Blender tool scripts
-> edit params
-> validate plan
-> ASCII dry run
-> Blender adapter preview/export
```

It should open with no seeded sample geometry. The user builds an ordered list
of tool steps from the Blender tool dictionary.

Primary handoff:

- `blank_blender_tool_plan_workbench_handoff_v0.md`

Machine-readable UI contract:

- `blank_tool_plan_ui_template_notes_v0.md`
- `data/architecture/asset_mill/blender_tools/blender_tool_ui_templates_v0.json`
- `scripts/validate_blender_tool_ui_templates_v0.py`
- `scripts/create_blank_tool_plan_v0.py`

Specialized example handoff:

- `petal_scroll_recipe_workbench_handoff_v0.md`

The petal-scroll handoff remains useful as an example of a recipe-specific
operator surface, but it is not the first UI target.
