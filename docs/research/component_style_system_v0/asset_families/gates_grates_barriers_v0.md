# Gates, Grates, And Barriers V0

## Purpose

Gates and barriers control movement, line of sight, sound, progression, and
dungeon readability. They need strong gameplay semantics and clear connector
logic.

## Component Breakdown

Primary components:

- gate frame
- gate leaf
- portcullis
- iron bars
- sewer grate
- floor grate
- shutter
- fence panel
- barricade
- chain barrier
- lock plate
- hinge
- latch
- rail guide
- barrier socket

Useful anatomy:

- frame
- vertical bar
- horizontal rail
- diagonal brace
- hinge side
- latch side
- sliding track
- lock detail
- grate grid
- connector tab
- blocked volume

## Style Directions

Gothic:

- pointed gate frames
- iron straps
- tracery-like grilles

Dungeon:

- portcullis
- heavy bars
- rusted locks

Sewer:

- floor grates
- drain bars
- slimy metal

Rustic:

- wood barricades
- rope ties
- rough planks

Modern:

- simple barriers
- clean railings
- metal grilles

## Geometric Shaping Ledger

`iron_bar_grid`

```text
source shapes: rectangle, circle, capsule
operations: array_linear, extrude, bevel_edges, compound_asset
edit knobs: bar count, spacing, thickness, frame width
visible result: repeated gate or grate bars
```

`portcullis`

```text
source shapes: rectangle, triangle, capsule
operations: array_linear, extrude, bevel_edges, rail_socket
edit knobs: bar count, spike height, vertical travel guide, thickness
visible result: sliding spiked gate
```

`gate_frame`

```text
source shapes: rectangle, pointed_arch_profile, arch_profile
operations: extrude, sweep, boolean_cut, bevel_edges
edit knobs: opening width, height, frame thickness, arch option
visible result: structural frame around gate leaf
```

`hinge_lock_hardware`

```text
source shapes: rectangle, circle, capsule
operations: extrude, array_linear, bevel_edges
edit knobs: hinge count, rivet count, lock size, metal projection
visible result: readable hardware layer
```

`blocked_volume`

```text
source shapes: bounding_box, rectangle
operations: compound_asset, validation_export
edit knobs: collision width, collision height, passable state
visible result: gameplay barrier metadata
```

## Blender Tool Groups

- arrays for bars, grates, spikes, planks, rivets
- mesh-from-points for pointed frames and custom gates
- booleans for sockets and tracks
- bevel/weighted normals for metal/wood readability
- material slots for rust, shadow, edge wear, lock plate
- connector metadata for passability and animation anchors

## First Build Targets

1. `simple_iron_bar_gate_v0`
2. `gothic_pointed_gate_frame_v0`
3. `portcullis_low_poly_v0`
4. `sewer_floor_grate_v0`
5. `wood_barricade_plank_stack_v0`

## Boundary

This page does not define lock state, animation code, or final collision. Those
belong to gameplay and adapter contracts.
