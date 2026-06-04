# Arches And Arcades V0

## Purpose

Arches are the bridge between openings, walls, columns, doors, windows,
bridges, and ceilings. Arcades are repeated arch systems. This family deserves
its own lane because arch logic appears everywhere.

## Component Breakdown

Primary components:

- arch opening
- arch band
- voussoir
- keystone
- springline block
- impost block
- archivolt
- spandrel
- pier connector
- arcade bay
- blind arch
- bridge arch
- flying arch

Useful anatomy:

- span
- rise
- springline
- apex
- intrados
- extrados
- arch thickness
- voussoir count
- keystone center
- bay repeat line

## Style Directions

Gothic:

- pointed arches
- archivolts
- clustered pier spring points
- blind arcades

Romanesque:

- round arches
- thick voussoirs
- heavy impost blocks

Renaissance:

- ordered round arches
- pilaster-supported arcades
- regular bay spacing

Rustic/Ruin:

- broken arch fragments
- missing voussoirs
- collapsed arcade bays

Modern:

- simple rectangular or shallow arch frames

## Geometric Shaping Ledger

`arch_band`

```text
source shapes: arch_profile, pointed_arch_profile, capsule
operations: sweep, offset_profile, bevel_edges
edit knobs: span, rise, thickness, segment count, profile radius
visible result: curved structural or decorative arch frame
```

`voussoir`

```text
source shapes: trapezoid, custom_polygon
operations: array_radial, extrude, bevel_edges
edit knobs: count, wedge depth, joint gap, keystone scale
visible result: repeated wedge stones around arch
```

`keystone`

```text
source shapes: trapezoid, rectangle, custom profile
operations: extrude, bevel_edges, relief_stack
edit knobs: height, width, projection, ornament depth
visible result: center top stone or decorative emphasis
```

`arcade_bay`

```text
source shapes: rectangle, arch_profile, pointed_arch_profile
operations: array_linear, compound_asset, boolean_cut
edit knobs: bay count, pier width, arch span, arch height, repeat spacing
visible result: repeated arch system
```

`broken_arch_fragment`

```text
source shapes: arch_profile, custom_polygon
operations: boolean_cut, bevel_edges, displacement, material_mask
edit knobs: missing segment range, chip amount, rubble anchors
visible result: ruin-ready arch piece
```

## Blender Tool Groups

- curve/path sweep for arch bands
- mesh-from-points for pointed/round/custom profiles
- radial/arc placement for voussoirs
- arrays for arcades
- booleans for wall openings and blind arches
- bevel/weighted normals for stone definition
- material assignment for intrados, extrados, joints, keystone

## First Build Targets

1. `clean_round_arch_band_v0`
2. `gothic_pointed_arch_band_v0`
3. `voussoir_arch_with_keystone_v0`
4. `three_bay_arcade_module_v0`
5. `broken_arch_fragment_v0`

## Boundary

This page does not solve full wall integration or structural physics. Parent
wall/column recipes should own placement and connector rules.
