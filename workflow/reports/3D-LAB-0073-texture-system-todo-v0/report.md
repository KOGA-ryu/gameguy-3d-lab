# 3D-LAB-0073 Texture System TODO V0

## Goal

Create the first texture-system planning lane and mark decals as a high-cost
optional detail layer.

## Source Shape

```text
material role
-> surface role
-> dungeon style palette
-> wear state
-> hardware tier
-> material/texture layer stack
```

## Files

- `docs/research/texture_system_v0/README.md`
- `docs/research/texture_system_v0/texture_todo_list_v0.md`
- `docs/research/texture_system_v0/material_asset_taxonomy_v0.md`
- `docs/research/texture_system_v0/dungeon_style_palette_matrix_v0.md`
- `docs/research/texture_system_v0/surface_wear_rules_v0.md`
- `docs/research/texture_system_v0/hardware_budget_and_decal_policy_v0.md`
- `README.md`

## Decal Policy

```text
*** DECALS ARE HIGH-COST OPTIONAL DETAIL ***
lower-compute hardware does not get decals
```

Fallbacks:

- base materials
- material slots
- trim sheets
- simple procedural noise
- baked or vertex-color masks
- roughness variation
- normal/bump detail where affordable

## Texture Asset Families

The TODO lane now tracks:

- tileable base materials
- damage and age layers
- grime and environment layers
- `*** DECALS ***`
- trim sheets
- ornament atlases
- utility maps
- dungeon style packs
- UV strategy
- Blender material tool sequence

## Validation

```text
python3 -m json.tool workflow/reports/3D-LAB-0073-texture-system-todo-v0/receipt.json
PASS

python3 scripts/validate_component_style_sheets_v0.py
PASS component style sheet validation: domains=7 components=70 style_sheets=5 ledger_entries=11 sources=7 tools=23

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 source_component_style_sheets=5 reference_only=3
```

## Notes

This slice is documentation only. It does not create texture images, bake maps,
execute Blender, or add material compilers yet.

The next practical implementation target should be:

```text
gothic_crypt_stone_material_stack_v0
```

That target should prove low/mid/high material tiers on one existing Gothic
railing post or panel.
