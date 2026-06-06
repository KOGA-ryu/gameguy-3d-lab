# UI Recipe Workbench V0

This lane defines a human control surface for the deterministic recipe pipeline.

The UI is not a modeling app and not a render gallery. It is a compact recipe
workbench:

```text
source recipe JSON
-> human-controlled layer stack
-> ASCII dry run
-> validation report
-> Blender adapter preview/export
```

Start with the single `AddPetalScroll` column ornament. Do not generalize the UI
until this one asset can be loaded, adjusted, previewed, validated, rendered, and
saved without hand-editing JSON.

Primary handoff:

- `petal_scroll_recipe_workbench_handoff_v0.md`

That handoff defines the compact workbench layout, layer stack, exact
`AddPetalScroll` recipe controls, default values, command bridge, validation
rules, and the UI defaults that should be removed during implementation review.
