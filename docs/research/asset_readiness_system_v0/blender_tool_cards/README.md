# Blender Tool Cards V0

This folder turns the first priority Blender tool queue into practical operator
notes.

These cards are not generic Blender tutorials. They are repo-specific notes for
architectural asset work where source recipes, drawing guides, and style sheets
own the design decisions.

Use the cards in this order:

```text
base form
-> assembly
-> shape refinement
-> curve/material cleanup
-> game proxy/export readiness
```

## Files

- `base_form_tool_cards_v0.md`
- `assembly_tool_cards_v0.md`
- `shape_refinement_tool_cards_v0.md`
- `curve_uv_material_tool_cards_v0.md`
- `game_proxy_tool_cards_v0.md`
- `tool_card_index_v0.json`

## Operator Rule

For every tool, ask three questions:

```text
what visible job does this tool perform?
what source field tells it how strong to be?
what mistake will make the asset harder to use later?
```

If the answer is not written down, the asset is not ready for a serious Blender
pass.

