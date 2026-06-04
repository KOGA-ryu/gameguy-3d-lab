# Roofs, Towers, And Spires V0

## Purpose

Roofs, towers, and spires create exterior silhouette and vertical landmarks.
They are essential for cathedrals, castles, gates, keeps, chapels, towers, and
ruined skylines.

## Component Breakdown

Primary components:

- roof plane
- ridge
- hip
- gable
- dormer
- tower shaft
- turret
- spire
- cone roof
- pyramid roof
- crenellation
- parapet cap
- pinnacle
- roof rib
- finial
- buttress cap

Useful anatomy:

- roof pitch
- eave line
- ridge line
- cap ring
- silhouette profile
- vertical stack
- roof tile line
- tower socket
- parapet course
- spire base

## Style Directions

Gothic:

- steep roofs
- spires
- pinnacles
- buttress caps
- tracery-like tower openings

Castle/Romanesque:

- towers
- battlements
- heavy parapets
- conical turret roofs

Renaissance:

- domes
- ordered roof lanterns
- clean cornices

Rustic:

- timber roofs
- damaged shingles
- uneven ridge lines

Modern:

- flat roof slabs
- clean parapets
- simple roof equipment

## Geometric Shaping Ledger

`roof_plane`

```text
source shapes: rectangle, triangle, custom_polygon
operations: extrude, bevel_edges, mirror_axis
edit knobs: pitch, length, width, thickness, overhang
visible result: sloped roof surface
```

`tower_shaft`

```text
source shapes: square, octagon, circle
operations: section_stack, extrude, bevel_edges, array_linear
edit knobs: height, footprint, wall thickness, opening count
visible result: vertical tower body
```

`spire`

```text
source shapes: triangle, octagon, circle
operations: section_stack, primitive_cone_add, bevel_edges, cap_ends
edit knobs: height, base radius, segment count, tip bevel
visible result: pointed roof or landmark top
```

`crenellation`

```text
source shapes: rectangle, square
operations: array_linear, extrude, bevel_edges
edit knobs: merlon width, gap width, height, parapet length
visible result: battlement edge
```

`dormer`

```text
source shapes: rectangle, triangle, arch_profile
operations: compound_asset, boolean_cut, bevel_edges
edit knobs: opening size, roof pitch, trim width, placement count
visible result: small roof opening or chapel-like roof detail
```

## Blender Tool Groups

- mesh primitives and mesh-from-points for roof planes
- section stack for towers and spires
- arrays for crenellations, roof tiles, and parapet details
- booleans for tower openings and dormers
- bevel/weighted normals for roof and stone edges
- material roles for roof, ridge, parapet, opening trim, spire

## First Build Targets

1. `steep_gothic_roof_module_v0`
2. `octagonal_tower_shaft_v0`
3. `low_poly_spire_v0`
4. `crenellated_parapet_strip_v0`
5. `tower_with_pinnacle_caps_v0`

## Boundary

This page does not define full building massing. Roof and tower pieces should
attach to wall/room/building recipes through explicit sockets.
