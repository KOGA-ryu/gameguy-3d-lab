# 3D-LAB-0089 Cooking Recipe Method Research V0

## Goal

Add cooking, recipe, kitchen workflow, and preservation research for future food
props, pantry/cellar scenes, readable recipe books, kitchen stations, and lore
hooks.

## Added

- `docs/research/food_drink_assets_v0/cooking_recipe_source_index_v0.md`
- `docs/research/food_drink_assets_v0/cooking_recipe_method_research_v0.md`
- `docs/research/food_drink_assets_v0/operator_cooking_recipe_handoff_v0.md`

## Updated

- `docs/research/food_drink_assets_v0/README.md`
- `README.md`

## Coverage

- recipe manuscripts and cookbook pages
- household receipt books
- feast menus and serving orders
- ingredient prep, sorting, cutting, grinding, mixing
- hearth/cauldron/stew cooking
- roasting, spit, griddle, and dry-heat cooking
- baking, bread, ovens, and flatbread
- frying/pan work
- drying
- salting, curing, brining, smoking
- pickling, fermentation, vinegar, crocks
- sugaring, preserves, syrups, and spiced fruit
- dairy processing
- brewing, wine, mead, and fermented drink
- kitchen station labels and future source-field candidates

## Boundary

This is research documentation for game-asset planning only. It is not recipe
instruction, food-safety guidance, kitchen safety guidance, nutrition advice,
historical authenticity proof, or active generated-asset input.

## Validation

```text
python3 -m json.tool workflow/reports/3D-LAB-0089-cooking-recipe-method-research-v0/receipt.json
PASS

python3 scripts/validate_food_drink_asset_taxonomy_v0.py
PASS

git diff --check
PASS
```

## Recommended Next Goal

Promote one small readable/process record only when a kitchen, pantry, food prop,
or readable-book feature needs it. Good candidates are `recipe_document_v0`,
`kitchen_station_v0`, `drying_rack_state_v0`, and
`fermentation_crock_state_v0`.
