# Cooking And Recipe Method Research V0

This document maps cooking, recipe, kitchen, and preservation methods into
future game-asset planning.

The repo translation is:

```text
recipe/cooking method -> visible process evidence -> source fields
-> Blender/asset direction -> operator checks -> lore/readable hook
```

## Boundary

This is not recipe instruction, food-safety guidance, nutrition advice, kitchen
safety guidance, or historical authenticity proof. It is a planning map for
props, rooms, readable books, clues, and future asset recipes.

## Recipe Documents As Game Objects

### Recipe Manuscript Or Cookbook Page

Real-world logic:

```text
title or heading
-> ingredient names
-> action verbs
-> vessel/heat/equipment hints
-> finishing/serving note
-> marginal correction or owner note
```

Visible asset cues:

- page layout with short blocks, rubric/headings, or marginal marks
- stains near frequently used entries
- repeated ingredient words or symbols
- owner corrections, tally marks, or crossed-out substitutions
- bookmark/ribbon/loose scrap for useful recipes

Source fields:

- `recipe_document_type`
- `recipe_role`
- `ingredient_terms`
- `method_verbs`
- `equipment_terms`
- `serving_context`
- `page_stain_regions`
- `marginalia_type`
- `readable_reward`

Game use:

- readable kitchen book
- noble feast manual
- tavern cook's notebook
- monastic/refectory book
- apothecary-kitchen crossover manuscript
- dungeon clue encoded as ingredient/order list

Operator checks:

- the page reads as a recipe or kitchen note, not generic text
- stains and bookmarks point to useful entries
- recipe method connects to visible kitchen props nearby

### Household Receipt Book

Real-world logic:

```text
food recipes
medicine/herbal recipes
dyes/pigments/cleaning/craft recipes
household accounts
personal notes
```

Visible asset cues:

- mixed categories in one book
- kitchen, herb, cloth, pigment, and medicine terms appear together
- different handwriting colors or owner corrections
- domestic utility rather than courtly presentation

Source fields:

- `receipt_categories`
- `owner_role`
- `household_status`
- `cross_domain_terms`
- `handwriting_layers`
- `use_wear_regions`

Game use:

- connects food, medicine, dye, craft, and household systems
- lets recipe books become clue hubs
- supports player-readable "this family knew how to preserve food, dye cloth,
  and treat illness" world detail

Operator checks:

- the book's prop context matches its contents
- book can sit in kitchen, pantry, workshop, or apothecary without feeling wrong

### Feast Menu Or Serving Order

Real-world logic:

```text
occasion
rank/status
course order
serving vessels
display/spectacle
leftovers and storage
```

Visible asset cues:

- menu slip, wax-sealed order, or steward's list
- high-status ingredients or decorative serving notes
- platter counts, table placement, and assigned servants
- status difference between kitchen prep and hall display

Source fields:

- `feast_status`
- `course_count`
- `dish_roles`
- `vessel_assignments`
- `display_rules`
- `leftover_policy`
- `servant_route`

Game use:

- noble halls
- cathedral feast days
- tavern banquets
- poisoned goblet clues
- missing platter/ingredient puzzle

Operator checks:

- feast props are arranged by course/status
- serving vessels match dish roles
- display food has stronger silhouette than pantry food

## Kitchen Workflow Methods

### Ingredient Sorting, Washing, Cutting, Grinding, And Mixing

Cooking logic:

```text
raw ingredient
-> clean/sort
-> cut/grind/pound/sift
-> mix with liquid/fat/spice
-> move to cooking vessel
```

Visible asset cues:

- cutting boards with knife marks
- sorted piles, peels, stems, shells, bones, or trimmings
- mortar and pestle, quern, sieve, bowl, or trough
- ingredient state changes: whole, chopped, ground, soaked, mixed

Source fields:

- `ingredient_state`
- `prep_station_type`
- `cut_size_label`
- `grind_state`
- `waste_scraps`
- `mixing_vessel`
- `tool_marks`
- `workflow_stage`

Blender/asset direction:

```text
mesh_from_pydata
primitive_cube_add
primitive_uv_sphere_add
modifier_array
modifier_bevel
material_assign_by_part
procedural_noise_texture
create_lod_variant
```

Operator checks:

- prepared and raw states are visually different
- scraps support the workflow instead of becoming random clutter
- small repeated food pieces have low-compute fallbacks

Lore hooks:

- a cut-size note can identify a careful cook, hurried flight, or interrupted
  preparation
- spice grinding can reveal trade or ritual value

### Hearth, Fire, Cauldron, And Stew Cooking

Cooking logic:

```text
fire or coals
-> suspended pot/cauldron or hearth vessel
-> liquid base
-> ingredients added
-> simmer/stew/boil state
-> serving transfer
```

Visible asset cues:

- hearth, ash bed, fire dogs, tripod, hooks, chains, cauldron
- soot above vessel
- liquid surface, steam/heat optional, floating chunks
- ladle, spoon, bowl, or serving socket nearby
- splash/stain ring around pot

Source fields:

- `heat_source_type`
- `vessel_type`
- `suspension_type`
- `liquid_fill_ratio`
- `ingredient_chunk_count`
- `steam_optional`
- `soot_regions`
- `serving_socket`

Blender/asset direction:

```text
radial_stack
primitive_torus_add
curve_bezier_add
curve_bevel_profile
material_assign_by_part
procedural_noise_texture
procedural_bump_map
```

Operator checks:

- pot and liquid are separate parts
- soot follows fire/vessel position
- serving tools explain how food leaves the pot

Lore hooks:

- abandoned hot/cold stew tells time passed
- missing ladle or clean bowl can suggest who ate last

### Roasting, Spit, Griddle, And Dry-Heat Cooking

Cooking logic:

```text
meat/bread/fish/vegetable
-> direct radiant heat, pan, griddle, or spit
-> char/browned surface
-> turn marks or support pins
-> serving platter
```

Visible asset cues:

- spit rod, hooks, prongs, pan, griddle, rack, or flat stone
- char marks on heat-facing side
- fat drip tray or ash/grease stain
- turning handle and supports
- platter/socket transition from cooking to serving

Source fields:

- `dry_heat_method`
- `spit_axis`
- `support_prongs`
- `char_regions`
- `fat_drip_regions`
- `turning_handle`
- `serving_state`

Blender/asset direction:

```text
curve_bezier_add
curve_bevel_profile
primitive_cylinder_add
primitive_cube_add
mesh_from_pydata
modifier_bevel
material_assign_by_part
```

Operator checks:

- heat marks face the heat source
- support hardware is visible
- cooked food reads different from raw or preserved food

Lore hooks:

- interrupted roast can show sudden evacuation
- fat drip and ash tell whether the kitchen was active recently

### Baking, Bread, Ovens, And Flatbread

Cooking logic:

```text
grain/flour
-> mix/knead
-> shape
-> rest/leaven or quick cook
-> oven, pan, stone, or griddle
-> scoring, crust, crumb, serving
```

Visible asset cues:

- flour sack, kneading trough, dough mass, rolling pin, peel, oven mouth
- scored loaf, crust/crumb contrast, flour dust
- flatbreads on pan/stone
- many loaves imply professional/community oven or bakery

Source fields:

- `grain_source`
- `flour_state`
- `dough_state`
- `kneading_surface`
- `loaf_shape`
- `score_pattern`
- `oven_type`
- `batch_count`
- `crumb_exposure`

Blender/asset direction:

```text
mesh_from_pydata
primitive_uv_sphere_add
modifier_displace
inset_faces
extrude_faces
material_assign_by_part
procedural_noise_texture
```

Operator checks:

- bread reads through crust score and body silhouette before texture
- bakery batches use instancing/LOD rather than many unique meshes
- oven or pan explains the bread type

Lore hooks:

- oven ownership implies settlement wealth and professional baking
- different loaf shapes can mark ration, offering, tavern, or feast

### Frying, Fat Cooking, And Pan Work

Cooking logic:

```text
pan or shallow vessel
-> fat/oil
-> small food pieces
-> browned/greasy surface
-> drain/serve
```

Visible asset cues:

- shallow pan, ladle, dripping rack, grease sheen
- small food pieces with browned edges
- dark oil residue or splatter near pan
- cloth or trencher nearby for serving

Source fields:

- `pan_type`
- `fat_material`
- `food_piece_count`
- `browning_regions`
- `grease_splatter_policy`
- `serving_transfer`

Blender/asset direction:

```text
radial_stack
mesh_from_pydata
modifier_array
modifier_bevel
material_assign_by_part
procedural_noise_texture
```

Operator checks:

- pan and food pieces are distinct
- fat/grease does not require decals on lower hardware
- browning is localized to cooked surfaces

Lore hooks:

- expensive oil/fat can mark status or trade
- greasy pan beside no food can imply someone fled after eating

## Preservation And Pantry Methods

### Drying

Preservation logic:

```text
cut/slice or hang
-> expose to air/low heat/sun/smokehouse environment
-> moisture removal
-> package in dry storage
```

Visible asset cues:

- drying racks, trays, strings, hooks, rafters
- thin sliced fruit/vegetable/meat/fish
- wrinkled or darkened material
- airy spacing between pieces
- dry storage jars/sacks after processing

Source fields:

- `drying_method`
- `slice_thickness_label`
- `rack_type`
- `air_gap_spacing`
- `hang_points`
- `dryness_state`
- `storage_container`

Blender/asset direction:

```text
mesh_from_pydata
modifier_array
curve_bezier_add
curve_bevel_profile
material_assign_by_part
create_lod_variant
```

Operator checks:

- dried pieces are spaced for air, not piled wet
- color/shape reads preserved rather than fresh
- repeated slices are budgeted for lower compute

Lore hooks:

- dried food near travel gear implies preparation for a journey
- empty drying racks can imply famine, theft, or recent packing

### Salting, Curing, Brining, And Smoking

Preservation logic:

```text
salt/brine/cure
-> container, barrel, crock, rack, or smokehouse
-> time/label/storage
-> preserved meat/fish/vegetable state
```

Visible asset cues:

- salt bins, barrels, crocks, hanging fish/meat, labels, hooks
- white salt crust or brine surface
- smoke stains, rafters, and hanging rows
- date marks, tied tags, sealed lids

Source fields:

- `preservation_method`
- `salt_or_brine_marker`
- `container_type`
- `hang_hook_count`
- `smoke_stain_regions`
- `label_text_role`
- `preserved_state`

Blender/asset direction:

```text
primitive_cylinder_add
radial_stack
curve_bezier_add
curve_bevel_profile
modifier_array
material_assign_by_part
procedural_noise_texture
```

Operator checks:

- preservation container explains the method
- smoked/cured items differ from roasted/cooked items
- labels/tags connect pantry clues to readable books

Lore hooks:

- smoked fish/meat can reveal trade routes or winter preparation
- mismatched label/container can be a clue

### Pickling, Fermentation, Vinegar, And Crocks

Preservation logic:

```text
prepared produce or liquid
-> brine/acid/fermentation vessel
-> bubbles/sediment/weight/cover
-> jar/crock/barrel storage
```

Visible asset cues:

- crock, jar, brine line, lid, cloth cover, weight stone
- bubbles/sediment optional as low-cost material detail
- labels, seals, tied cloth, shelf placement
- sour/vinegar trade or cellar context

Source fields:

- `fermentation_type_label`
- `brine_line_height`
- `container_material`
- `cover_type`
- `weight_object`
- `sediment_policy`
- `shelf_socket`
- `label_role`

Blender/asset direction:

```text
radial_stack
mesh_from_pydata
primitive_cylinder_add
modifier_solidify
material_assign_by_part
procedural_noise_texture
```

Operator checks:

- container/liquid/cover are distinct if visible
- bubbles/sediment are optional detail, not required geometry
- labels and seals support gameplay clues

Lore hooks:

- sour crocks can mark cellar age, trade, monastic kitchen, or household
  thrift

### Sugaring, Preserves, Syrups, And Spiced Fruit

Preservation logic:

```text
fruit or spice
-> sweet/syrup preserve
-> jar, pot, or sealed container
-> high-status or medicinal overlap
```

Visible asset cues:

- small jars, sticky glaze, labels, tied covers
- fruit pieces in syrup or paste-like mass
- spice jar nearby
- noble, apothecary, or feast table context

Source fields:

- `preserve_type`
- `syrup_or_paste_state`
- `fruit_piece_count`
- `jar_size`
- `seal_type`
- `spice_link`
- `status_tier`

Blender/asset direction:

```text
radial_stack
primitive_uv_sphere_add
mesh_from_pydata
material_assign_by_part
procedural_noise_texture
```

Operator checks:

- preserved fruit looks different from fresh produce
- jar/seal scale suggests value
- spice/status link is visible through labels or context

Lore hooks:

- preserves can connect noble feasts, apothecary work, trade spice, and stored
  winter sweetness

### Dairy, Cheese, Butter, And Milk Processing

Processing logic:

```text
milk source
-> churn/curd/cut/drain/press
-> rind/storage
-> serving or travel state
```

Visible asset cues:

- churn, pail, cloth, press, draining board
- cheese wheel/wedge, rind, cut face, holes, crumbs
- butter crock or wrapped pat
- cellar shelf or travel ration context

Source fields:

- `dairy_process_stage`
- `churn_type`
- `draining_cloth`
- `press_weight`
- `rind_type`
- `cut_face_state`
- `storage_age_label`

Blender/asset direction:

```text
radial_stack
primitive_cylinder_add
mesh_from_pydata
modifier_boolean
modifier_bevel
material_assign_by_part
procedural_bump_map
```

Operator checks:

- cheese rind/cut face are separate material roles
- dairy equipment explains process stage
- cellar/pantry placement supports storage read

Lore hooks:

- cheese aging shelves and labels can reveal trade, rationing, or monastery
  production

### Brewing, Wine, Mead, And Fermented Drink

Processing logic:

```text
grain/fruit/honey
-> mash/press/ferment
-> barrel/cask/bottle
-> serving vessel
-> label/status/fill state
```

Visible asset cues:

- mash tub, press, barrel, cask, bung, tap, bottle, jug
- foam, sediment, cork, wax seal, label
- tavern cellar, noble wine rack, monastic brew context

Source fields:

- `drink_base`
- `fermentation_stage`
- `barrel_size`
- `bung_or_tap_state`
- `sediment_policy`
- `fill_ratio`
- `serving_vessel_type`
- `label_role`

Blender/asset direction:

```text
radial_stack
primitive_cylinder_add
primitive_torus_add
curve_bezier_add
curve_bevel_profile
material_assign_by_part
procedural_noise_texture
```

Operator checks:

- cask/bottle/jug forms are distinct
- tap/bung/seal explain storage state
- cellar arrangement supports access and serving

Lore hooks:

- barrel marks can show origin, tax, theft, poison, or feast preparation

## Kitchen Room And Station Types

Useful station labels:

- `hearth_station`
- `cauldron_station`
- `roasting_spit_station`
- `baking_oven_station`
- `prep_table_station`
- `grinding_sifting_station`
- `dairy_station`
- `preservation_rack_station`
- `smokehouse_station`
- `fermentation_crock_station`
- `cellar_storage_station`
- `serving_pass_station`
- `washing_drain_station`

Each station should record:

```text
station_id
heat_or_process_type
primary_tools
food_states_supported
material_wear
lighting_mood
asset_density_budget
readable_clue_hooks
low_compute_fallback
```

## Recipe-To-Asset Field Candidates

Potential future machine-readable records:

- `recipe_document_v0`
- `kitchen_station_v0`
- `cooking_method_v0`
- `preservation_method_v0`
- `ingredient_state_v0`
- `serving_order_v0`
- `pantry_label_v0`
- `feast_menu_v0`
- `stew_vessel_state_v0`
- `bread_batch_state_v0`
- `drying_rack_state_v0`
- `fermentation_crock_state_v0`
- `barrel_cask_state_v0`

Promote only when a concrete kitchen, pantry, food prop, readable book, or sound
feature needs it.
