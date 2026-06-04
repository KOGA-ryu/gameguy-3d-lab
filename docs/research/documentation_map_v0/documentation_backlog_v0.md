# Documentation Backlog V0

This backlog is documentation only. It should be used while feature work is
blocked or waiting, so the repo can return to 3D assets with sharper language.

## Priority 1: Cross-Lane Foundations

1. Global style atlas

   Status: first pass added in `global_style_atlas_v0.md`.

   Purpose: define dungeon, cathedral, castle, village, market, cave, sewer,
   ruin, workshop, wilderness, and noble/interior looks.

   Needed docs:

   - style names
   - material palette
   - silhouette rules
   - decoration density
   - wear rules
   - low-compute fallback

2. Shape-language dictionary

   Status: first pass added in `shape_language_dictionary_v0.md`.

   Purpose: give the user vocabulary for "that lip, curve, rib, bead, lobe,
   frame, recess, star, arch, and panel thing."

   Needed docs:

   - shape name
   - plain-English description
   - where it appears
   - 2D drawing method
   - Blender method
   - common mistakes

3. Drawing-guide template

   Purpose: make manual sketches feed source recipes and Blender workcards.

   Needed docs:

   - side/front/top sketch fields
   - source point naming
   - profile extraction
   - line selection/omission fields
   - scale reference
   - correction capture form

4. Manual-edit capture form

   Purpose: when the user fixes something by hand, the repo captures the rule
   behind the fix instead of losing it.

   Needed docs:

   - what changed
   - what looked wrong
   - which part changed
   - new source field needed
   - Blender tool used
   - should this become a recipe rule?

## Priority 2: Missing Asset Family Lanes

1. Clothing and costume

   Needed subjects:

   - tunics, robes, cloaks, hoods, sleeves, belts, boots, gloves, hats
   - status/caste tiers
   - fabric materials
   - folds, seams, hems, fasteners
   - character attachment rules

2. Armor

   Needed subjects:

   - helmets, cuirasses, mail, lamellar, plates, shields, greaves, gauntlets
   - material and damage states
   - attachment points
   - silhouette by class/status
   - low-poly proxy versus hero armor

3. Weapons

   Needed subjects:

   - swords, axes, spears, bows, crossbows, daggers, maces, polearms
   - handles, guards, blades, heads, bindings, scabbards
   - collision proxy and hand sockets
   - display variants and broken variants

4. Plants, trees, and fungi

   Needed subjects:

   - trees, shrubs, vines, grasses, roots, moss, herbs, mushrooms
   - dungeon/cave variants
   - billboards versus mesh clusters
   - material and wind policy

5. Vehicles and transport

   Needed subjects:

   - carts, wagons, sledges, boats, handcarts, wheelbarrows
   - wheels, axles, yokes, cargo sockets, rope, planks
   - damage states and load variants

## Priority 3: Deepening Existing Lanes

1. Architecture

   Missing docs:

   - style atlas for Gothic, Romanesque, castle, village, ruin, sewer, cave,
     workshop, and noble interiors
   - construction guides for windows, vaults, arches, columns, railings, doors,
     stairs, and walls
   - ornament selection guide from sacred geometry fields
   - per-component Blender tool sequence sheets

2. Texture system

   Missing docs:

   - trim-sheet planning guide
   - UV decision tree
   - material slot naming convention
   - lower-compute material fallback guide
   - grime/water/soot/moss placement rules per room type

3. Furniture

   Missing docs:

   - furniture status atlas
   - joinery and wear notes
   - per-room furniture sets
   - prop clustering rules

4. Animals

   Missing docs:

   - silhouette drawing sheets
   - static pose library
   - rig/animation boundary notes
   - scatter-density and LOD policy
   - symbolic/statue conversion guide

5. Food and drink

   Missing docs:

   - kitchen and pantry set plans
   - market stall layouts
   - freshness/spoilage material states
   - serving vessel style atlas

6. Accessories

   Missing docs:

   - attachment-point guide
   - status/caste visual upgrade guide
   - personal clutter set plans
   - wearable versus pickup proxy differences

7. Instruments

   Missing docs:

   - storage/display variants
   - musician-space set dressing
   - sound-prop hooks
   - fragile/broken variants

## Priority 4: Player-Readable World Depth

Needed docs:

- readable book taxonomy
- book-page template
- clue-to-asset crosswalk
- guild/craft knowledge index
- environmental storytelling placement guide
- inspection reward guide
- inscription and signage guide

This matters because the user wants the player to be rewarded for noticing
details. A model is stronger when a book, sign, or craft note explains why its
parts exist.

## Priority 5: Production Organization

Needed docs:

- asset naming conventions across architecture and props
- source packet folder conventions
- reference packet checklist
- screenshot/contact-sheet review convention
- Blender manual pass checklist
- LOD/collision/export checklist
- commit/report template for documentation-only slices

These docs prevent the repo from becoming a pile of disconnected research.
