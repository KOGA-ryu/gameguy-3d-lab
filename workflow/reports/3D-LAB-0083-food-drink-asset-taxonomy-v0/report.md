# 3D-LAB-0083 Food Drink Asset Taxonomy V0

## Goal

Add a food/drink prop lane with families, status tiers, styles, visible anatomy,
serving/storage state, source support, geometry terms, Blender tool IDs, source
fields, operator checks, and lore hooks.

## Added

- `data/asset_taxonomy/food_drink_v0/food_drink_asset_taxonomy_v0.json`
- `docs/research/food_drink_assets_v0/README.md`
- `docs/research/food_drink_assets_v0/food_drink_source_index_v0.md`
- `docs/research/food_drink_assets_v0/food_drink_style_status_system_v0.md`
- `docs/research/food_drink_assets_v0/food_drink_family_build_plans_v0.md`
- `docs/research/food_drink_assets_v0/food_drink_lore_book_hooks_v0.md`
- `docs/research/food_drink_assets_v0/operator_food_drink_handoff_v0.md`
- `scripts/validate_food_drink_asset_taxonomy_v0.py`
- `tests/test_validate_food_drink_asset_taxonomy_v0.py`

## Coverage

- 8 food/drink status tiers
- 10 food/drink styles
- 8 food/drink families
- 17 starter food/drink items

## Boundary

This is game-asset planning and lore documentation only. It is not recipe
instruction, food safety guidance, nutrition guidance, conservation guidance,
historical authenticity proof, or active generated-asset input.

## Validation

```text
python3 -m json.tool data/asset_taxonomy/food_drink_v0/food_drink_asset_taxonomy_v0.json
PASS food/drink JSON parse

python3 -m py_compile scripts/validate_food_drink_asset_taxonomy_v0.py
PASS py_compile

python3 scripts/validate_food_drink_asset_taxonomy_v0.py
PASS food/drink asset taxonomy validation: status_tiers=8 styles=10 families=8 food_drink=17 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_food_drink_asset_taxonomy_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation
```

## Recommended Next Goal

Add per-food/drink workcards and promote one simple item, likely
`stew_bowl_v0`, `ceramic_jug_v0`, or `round_loaf_bread_v0`, into a deterministic
source-to-tool-plan recipe.
