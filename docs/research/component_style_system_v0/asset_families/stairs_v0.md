# Stairs V0

## Purpose

Stairs are movement assets first and ornament assets second. They must carry
walkable geometry, turns, landings, rail connections, and readable proportions.
The decorative layer should sit on top of a clean traversal contract.

## Component Breakdown

Primary components:

- `tread`
- `riser`
- `stringer`
- `landing`
- `nosing`
- `central_newel`
- `stair_handrail`
- `stair_baluster`
- `skirt_board`
- `winder`

Useful anatomy:

- run
- flight
- landing
- pitch line
- inner stringer
- outer stringer
- step nosing
- stair throat
- newel core
- rail path
- baluster orbit or spacing line

## Style Directions

Gothic:

- stone treads
- pointed-arch side panels
- heavy newels
- clustered central cores for spiral stairs

Victorian:

- turned newels
- turned balusters
- thick handrails
- decorative brackets below treads

Art Nouveau:

- flowing rail curves
- organic stringer panels
- asymmetric infill

Modern:

- slab treads
- simple stringers
- glass or bar guards

Rustic:

- thick timber treads
- rough log rails
- visible brackets and pegs

## Geometric Shaping Ledger

`tread`

```text
source shapes: rectangle, trapezoid, rounded_rectangle
operations: extrude, bevel_edges, array_linear, cap_ends
edit knobs: width, depth, thickness, nosing projection, bevel width
visible result: walkable step surface
```

`riser`

```text
source shapes: rectangle, custom_polygon
operations: extrude, bevel_edges, relief_stack
edit knobs: height, inset depth, face panel style, material region
visible result: vertical face between treads
```

`stringer`

```text
source shapes: custom_polygon, rectangle, triangle
operations: extrude, boolean_cut, bevel_edges, array_linear
edit knobs: run length, rise count, side thickness, cut profile, trim lip
visible result: side support following stair pitch
```

`central_newel`

```text
source shapes: circle, octagon, capsule, side profile
operations: radial_stack, section_stack, modifier_screw, array_radial
edit knobs: core radius, turn count, collar positions, rail socket heights
visible result: spiral stair core or heavy turn post
```

`stair_handrail`

```text
source shapes: capsule, rounded_rectangle, custom profile
operations: curve_path_sweep, bevel_edges, cap_ends
edit knobs: pitch angle, rail thickness, grip profile, end return
visible result: sloped rail following the run
```

## Blender Tool Groups

- mesh primitives for tread/riser slabs
- `mesh_from_pydata` for stringer side profiles and winder steps
- curve/path sweep for sloped handrails
- array along a line for repeated treads and balusters
- radial repeat for spiral stairs
- boolean cuts for stringer tooth profiles and rail sockets
- bevel and weighted normals for stone/wood readability
- validation for walkable bounds and connector positions

## First Build Targets

1. `straight_stair_clean_run_v0`
2. `straight_stair_with_side_stringers_v0`
3. `gothic_stair_side_panel_pointed_arch_v0`
4. `spiral_stair_central_newel_blockout_v0`
5. `spiral_stair_with_repeated_winders_v0`

## Boundary

This page does not define player collision, accessibility, or building-code
compliance. Those need a separate measurement and gameplay movement policy.
