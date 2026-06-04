# Texture System V0

This folder is the planning lane for materials, texture assets, dungeon style
palettes, surface wear rules, UV/trim-sheet strategy, and hardware budgets.

The working rule is:

```text
geometry names surfaces
-> material roles interpret those surfaces
-> dungeon style chooses palette and aging
-> hardware tier chooses which layers survive
-> Blender/material adapter applies or previews
```

## Documents

- `texture_todo_list_v0.md` is the main working list.
- `material_asset_taxonomy_v0.md` names texture asset families.
- `dungeon_style_palette_matrix_v0.md` maps dungeon styles to material moods.
- `surface_wear_rules_v0.md` defines where grime, edge wear, moss, soot, rust,
  and wetness belong.
- `hardware_budget_and_decal_policy_v0.md` defines the decal rule: decals are a
  high-cost optional layer and lower-compute hardware does not get decals.

## Boundary

These docs do not create image files, bake textures, run Blender, or claim final
art direction. They define the source vocabulary and TODOs for later material
recipes.

## Core Contract

The texture system should eventually compile from:

```text
material + surface_role + dungeon_style + wear_state + hardware_tier
```

Example:

```text
stone + plinth_base + gothic_crypt + old_wet + mid
```

Expected result:

```text
cold limestone base
dark grime in bevels/recesses
pale worn exposed edges
moss near lower surfaces
no decals unless hardware tier allows them
```
