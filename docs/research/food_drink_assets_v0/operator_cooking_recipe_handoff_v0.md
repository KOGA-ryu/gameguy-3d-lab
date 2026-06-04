# Operator Cooking Recipe Handoff V0

This handoff defines what future UI/manual workcards should capture when a food,
kitchen, pantry, readable recipe, or cooking-station asset needs process logic.

## Required Fields

```text
cooking_asset_id
reference_packet_id
world_style_id
room_or_station_id
recipe_role_optional
method_label
ingredient_states
equipment_parts
heat_or_preservation_source
container_or_vessel
serving_or_storage_state
material_wear
readable_lore_hook
operator_checks
low_compute_fallback
```

## Recipe Role Labels

Use these labels before inventing new ones:

- `court_cookbook`
- `household_receipt_book`
- `tavern_cook_note`
- `monastic_refectory_note`
- `pantry_inventory`
- `feast_serving_order`
- `preservation_tag`
- `spice_trade_note`
- `poison_or_medicine_overlap`
- `travel_ration_note`
- `kitchen_warning_note`
- `ingredient_substitution_note`

## Cooking Method Labels

- `raw_prep`
- `grinding_or_pounding`
- `mixing_or_kneading`
- `stewing_or_simmering`
- `boiling`
- `roasting`
- `griddle_or_flatbread`
- `baking`
- `frying_or_pan_work`
- `drying`
- `smoking`
- `salting_or_curing`
- `brining`
- `pickling`
- `fermentation`
- `sugaring_or_preserve`
- `dairy_processing`
- `brewing_or_wine_making`

## Ingredient State Labels

- `whole`
- `peeled`
- `cut`
- `chopped`
- `ground`
- `sifted`
- `mixed`
- `dough`
- `raw`
- `cooked`
- `charred`
- `stewed`
- `dried`
- `smoked`
- `salted`
- `pickled`
- `fermenting`
- `sealed`
- `spoiled`
- `served`

## Equipment Fields

| Field | Purpose |
| --- | --- |
| `heat_source_type` | Hearth, coals, oven, griddle, pan, spit, smokehouse, or no-heat preservation. |
| `vessel_type` | Pot, cauldron, pan, bowl, crock, jar, barrel, cask, trough, basket, sack, or platter. |
| `tool_parts` | Knife, ladle, spoon, pestle, sieve, hook, chain, spit, peel, rack, cork, seal, label. |
| `container_state` | Open, covered, sealed, tied, stopped, corked, tapped, spilled, broken, empty, full. |
| `process_marks` | Soot, ash, flour dust, grease, brine line, salt crust, smoke stain, waterline, sticky glaze. |
| `serving_socket` | Where prepared food moves after cooking. |
| `storage_socket` | Shelf, rack, cellar, pantry, hanging point, barrel slot, or jar row placement. |

## Workcard Sentence Examples

```text
This stew station uses cauldron_station, stewing_or_simmering method, hearth
heat, suspended cauldron, liquid fill ratio, chunk count, soot region, ladle
socket, and cold/abandoned state.
```

```text
This recipe page uses household_receipt_book role, mixed food/herbal categories,
ingredient terms, method verbs, page stains, marginal correction, and nearby
herb/spice jars.
```

```text
This smokehouse prop uses smoking method, hanging fish rows, hook count, smoke
stain regions, salt bin, tag labels, and dried/smoked material state.
```

```text
This baking scene uses baking_oven_station, kneading trough, flour sack, dough
state, scored loaf batch, oven mouth, peel, and flour-dust wear.
```

## Operator Checks

- Does the cooking or preservation method have visible equipment?
- Does food state match the station?
- Are heat, smoke, brine, drying, or sealing marks placed where the method says
  they should be?
- Can the player infer room history from food, vessel, and residue state?
- Is the readable recipe connected to nearby props?
- Does the low-compute fallback keep broad shape, material roles, and state?

## Avoid

- writing real recipes into the source docs
- implying food safety, nutrition, or storage correctness
- placing random kitchen clutter without a station role
- using labels or stains as the only clue when the object silhouette is unclear
- making all food look either fresh or rotten with no process state between
