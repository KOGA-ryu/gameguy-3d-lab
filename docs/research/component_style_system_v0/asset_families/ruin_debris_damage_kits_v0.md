# Ruin, Debris, And Damage Kits V0

## Purpose

Ruin kits make generated spaces feel used and damaged. They also let one clean
asset family become many variants without redesigning the base geometry.

## Component Breakdown

Primary components:

- rubble stone
- broken slab
- fallen column
- cracked column segment
- broken arch piece
- fallen trim
- damaged railing
- broken stair
- wall crack insert
- debris pile
- chipped corner
- missing block
- splintered wood
- bent metal
- ash pile
- dust mound

Useful anatomy:

- fracture line
- broken face
- chipped edge
- rubble socket
- pile footprint
- scatter points
- parent asset reference
- damage mask
- decal optional layer

## Style Directions

Gothic ruin:

- broken tracery
- fallen ribs
- cracked piers
- chipped limestone

Cathedral ruin:

- collapsed arch fragments
- rubble along walls
- broken rose pieces

Wet sewer:

- cracked wet slabs
- rust flakes
- slime debris

Lava forge:

- charred debris
- cracked basalt
- ash piles

Rustic:

- broken planks
- splinters
- rope debris

## Geometric Shaping Ledger

`rubble_stone`

```text
source shapes: custom_polygon, cube, tetra-like low poly
operations: extrude, bevel_edges, displacement, material_mask
edit knobs: size range, chip amount, bevel width, scatter count
visible result: reusable loose stone piece
```

`broken_arch_piece`

```text
source shapes: arch_profile, custom_polygon
operations: boolean_cut, bevel_edges, compound_asset
edit knobs: missing segment, fracture roughness, thickness, material role
visible result: fallen or partial arch fragment
```

`fallen_column_segment`

```text
source shapes: circle, octagon, section_stack
operations: radial_stack, boolean_cut, bevel_edges, cap_ends
edit knobs: segment length, break angle, rib count, end chip amount
visible result: damaged column piece on floor
```

`debris_pile`

```text
source shapes: rubble_stone, rectangle footprint, scatter points
operations: array_random_seeded, compound_asset, material_mask
edit knobs: pile footprint, piece count, size variance, seed
visible result: deterministic debris cluster
```

`damage_insert`

```text
source shapes: crack path, custom_polygon
operations: boolean_cut, relief_stack, decal_optional
edit knobs: crack width, depth, branching, low-tier fallback material
visible result: localized damage that can be applied to a parent surface
```

## Blender Tool Groups

- mesh-from-points for irregular low-poly fragments
- seeded scatter/array for debris piles
- booleans for broken cuts and missing pieces
- bevel/weighted normals for damaged edges
- material slots for fresh break, old surface, dirt, soot
- optional decals for high-tier cracks/stains only

## First Build Targets

1. `rubble_stone_piece_set_v0`
2. `fallen_column_segment_v0`
3. `broken_arch_fragment_v0`
4. `debris_pile_seeded_v0`
5. `damaged_railing_variant_insert_v0`

## Boundary

This page does not require physics simulation. Debris placement should be
deterministic and source-owned unless a separate runtime physics lane is added.
