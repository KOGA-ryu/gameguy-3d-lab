# Food And Drink Style And Status System V0

Food props need three labels:

```text
what it is -> family
what scene/status it belongs to -> status tier
how it reads visually -> style
```

That lets one base asset produce many useful variants:

```text
loaf
-> ration loaf
-> refectory loaf
-> ritual offering bread
-> stale ruined loaf
```

## Status Tiers

| Tier | Read | Asset signals |
| --- | --- | --- |
| subsistence ration | survival, prison, guard, camp | dry bread, plain sack, small portions |
| common tavern | tavern, kitchen, barracks | stew bowls, tankards, trenchers, cheese |
| monastic refectory | ordered shared meals | repeated bowls, simple jugs, bread portions |
| market trade | goods for sale | baskets, sacks, jars, fresh produce, labels |
| noble banquet | wealth and display | platters, wine, meat, fish, tall goblets |
| ritual/festival | offering or holy-day food | central vessel, symbolic bread, clean placement |
| traveler pack | road survival | wrapped bread, flasks, compact bundles |
| spoiled ruin | time, abandonment, rot | broken vessels, mold roles, spills, shrunk forms |

## Style Sheets

`rustic_bread_grain_v0`

- loaves, flatbreads, grain sacks, crust scores, crumb edges

`fresh_market_produce_v0`

- fruit bodies, root tapers, stems, bundle ties, produce counts

`dairy_cheese_cut_v0`

- wheels, wedges, rind, cut face, holes, cloth wrap

`cured_smoked_salted_v0`

- preserved meats, salt marks, hanging hooks, smoked/dark surfaces

`cooked_platter_service_v0`

- large served food masses, platters, bones, fish spine hints, garnish sockets

`ceramic_earthenware_service_v0`

- bowls, jugs, plates, handles, rim lips, glaze bands

`wood_metal_table_service_v0`

- trenchers, tankards, metal platters, rim bands, wear zones

`glass_bottle_goblet_v0`

- bottles, goblets, necks, stems, corks, fill lines

`sack_basket_jar_storage_v0`

- sacks, jars, seals, labels, tied mouths, shelf/basket sockets

`spoiled_mold_decay_v0`

- rot spots, missing chunks, dark material roles, broken rims, spills

## Promotion Rule

Food and drink recipes must declare state before Blender work:

```text
whole/cut/full/empty/spilled/fresh/stale/rotten/sealed/broken
```

Those are source fields. Blender should not invent whether a bottle is full, a
loaf is cut, or a sack has spilled.
