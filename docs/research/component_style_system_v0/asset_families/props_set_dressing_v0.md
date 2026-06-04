# Props And Set Dressing V0

## Purpose

Props and set dressing make rooms feel inhabited, abandoned, ritualized,
functional, or dangerous. This family should remain modular and style-aware so
the same environment can become crypt, library, sewer, forge, prison, or shrine.

## Component Breakdown

Primary components:

- crate
- barrel
- bench
- table
- chair
- shelf
- altar
- pedestal
- chest
- book pile
- scroll pile
- chain
- rope
- banner
- urn
- statue fragment
- weapon rack
- tool rack
- tomb marker

Useful anatomy:

- base footprint
- storage volume
- lid
- handle
- bracket
- strap
- shelf tier
- cloth panel
- scatter socket
- interactable marker

## Style Directions

Gothic crypt:

- altars
- tomb markers
- candle stands
- stone pedestals

Arcane library:

- shelves
- books
- scrolls
- desks
- crystal stands

Forge:

- anvils
- tool racks
- coal bins
- metal crates

Prison:

- chains
- shackles
- cages
- rough benches

Village/rustic:

- barrels
- crates
- stools
- carts
- sacks

## Geometric Shaping Ledger

`crate_or_chest`

```text
source shapes: cube, rectangle, rounded_rectangle
operations: extrude, bevel_edges, relief_stack, array_linear
edit knobs: size, lid height, plank count, metal strap count
visible result: storage prop
```

`altar_or_pedestal`

```text
source shapes: square, rectangle, octagon, profile stack
operations: section_stack, relief_stack, bevel_edges
edit knobs: footprint, height, base/cap layers, face ornament
visible result: ritual or display support
```

`shelf`

```text
source shapes: rectangle, cube
operations: array_linear, extrude, bevel_edges
edit knobs: shelf count, width, height, support style, back panel
visible result: repeated storage/display furniture
```

`chain_or_rope`

```text
source shapes: circle, capsule, curve path
operations: array_along_path, sweep, bevel_edges
edit knobs: link count, link size, sag, material
visible result: hanging or boundary detail
```

`cloth_banner`

```text
source shapes: rectangle, custom_polygon
operations: extrude, simple_deform, material_mask
edit knobs: width, height, bottom cut, bend amount, symbol slot
visible result: wall or hanging fabric prop
```

## Blender Tool Groups

- primitives for boxes, shelves, pedestals, simple furniture
- arrays for planks, straps, books, shelf tiers, rivets
- curve/path sweep for ropes and chains
- simple deformation for cloth/banner shape
- bevel/weighted normals for low-poly prop polish
- material slots for wood, metal, stone, cloth, paper

## First Build Targets

1. `stone_pedestal_prop_v0`
2. `wood_crate_with_straps_v0`
3. `arcane_bookshelf_blockout_v0`
4. `chain_loop_path_v0`
5. `crypt_altar_with_candle_sockets_v0`

## Boundary

This page does not define gameplay inventory or interactions. Interactable
state belongs to the mechanisms/interactables family.
