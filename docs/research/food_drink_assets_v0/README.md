# Food And Drink Assets V0

This folder starts the food, drink, tableware, and pantry prop lane.

The machine-readable source is:

```text
data/asset_taxonomy/food_drink_v0/food_drink_asset_taxonomy_v0.json
```

Validate it with:

```bash
python3 scripts/validate_food_drink_asset_taxonomy_v0.py
```

## What This Lane Does

- names food/drink families such as bread/grain, produce, cheese, meat/fish,
  stew, drink vessels, table service, and pantry storage
- defines status tiers such as ration, tavern, refectory, market, banquet,
  ritual/festival, traveler pack, and spoiled ruin
- defines reusable visual styles for bread/grain, produce, cheese cuts, cured
  food, cooked platters, earthenware, wood/metal service, glass, sacks/jars, and
  spoilage
- maps visible anatomy to geometry terms and legal Blender tool IDs
- captures serving/storage state, source fields, operator checks, and lore hooks

## Starter Food And Drink

- round loaf of bread
- flatbread wrap
- cheese wedge
- apple fruit
- carrot/root bundle
- roasted meat joint
- fish on platter
- bowl of stew
- beer tankard
- wine goblet
- ceramic jug
- glass bottle
- grain sack
- spice jar
- wooden trencher or plate
- waterskin or food flask
- spoiled fruit scatter

## Documents

- `food_drink_source_index_v0.md` lists source links and their repo use.
- `food_drink_style_status_system_v0.md` explains status/style/family labels.
- `food_drink_family_build_plans_v0.md` maps starter assets to build sequences.
- `food_drink_lore_book_hooks_v0.md` captures player-facing book/detail hooks.
- `operator_food_drink_handoff_v0.md` defines future UI/manual workcard fields.

## Boundary

This is game-asset planning only. It is not recipe instruction, food safety
guidance, nutrition guidance, historical authenticity proof, conservation
guidance, or active generated-asset input.
