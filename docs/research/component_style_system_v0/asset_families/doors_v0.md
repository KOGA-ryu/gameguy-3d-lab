# Doors And Portals V0

## Purpose

Doors and portals are access assets, visual anchors, and scale markers. They
need clean opening bounds first, then paneling, hardware, arch surrounds, and
ornament.

## Component Breakdown

Primary components:

- `door_slab`
- `stile`
- `rail`
- `door_panel`
- `door_jamb`
- `lintel`
- `portal_arch`
- `threshold`
- `hinge_strap`
- `surround`

Useful anatomy:

- leaf
- frame
- raised panel
- recessed panel
- jamb reveal
- arch surround
- tympanum field
- threshold block
- hinge side
- latch side

## Style Directions

Gothic:

- pointed portal arch
- vertical plank or panel rhythm
- iron hinge straps
- quatrefoil or blind tracery panels
- heavy stone surround

Romanesque:

- round arch surround
- thick jambs
- blocky voussoir rhythm

Renaissance:

- rectangular surround
- pediment
- ordered stile/rail proportions

Rustic:

- plank slab
- rough bevels
- visible straps and studs

Modern:

- flush slab
- clean frame
- minimal threshold

## Geometric Shaping Ledger

`door_slab`

```text
source shapes: rectangle, rounded_rectangle
operations: extrude, bevel_edges, relief_stack
edit knobs: width, height, thickness, panel inset depth, bevel width
visible result: main door leaf
```

`stile` and `rail`

```text
source shapes: rectangle, square
operations: extrude, array_linear, bevel_edges
edit knobs: member width, member depth, rail count, spacing
visible result: framed door grid
```

`door_panel`

```text
source shapes: rectangle, pointed_arch_profile, star_polygon, circle
operations: relief_stack, inset_faces, boolean_cut, offset_profile
edit knobs: inset depth, raised lip thickness, motif selection, panel count
visible result: recessed or raised decorative panel
```

`portal_arch`

```text
source shapes: pointed_arch_profile, arch_profile, trapezoid
operations: sweep, boolean_cut, section_stack, bevel_edges
edit knobs: span, springline, arch thickness, voussoir count, keystone height
visible result: arched stone or wood surround
```

`hinge_strap`

```text
source shapes: rectangle, capsule, circle, custom_polygon
operations: extrude, array_linear, mirror_axis, bevel_edges
edit knobs: strap length, strap width, rivet count, hinge side
visible result: surface hardware or ironwork
```

## Blender Tool Groups

- primitives for slabs, stiles, rails, jambs, and thresholds
- profile mesh from points for arch surrounds and hinge shapes
- boolean cuts for panel recesses and wall openings
- inset/relief stack for raised door panels
- array for rivets, boards, and repeated panels
- bevel/weighted normals for crisp wood/stone/metal edges
- material assignment for wood, stone, and metal regions

## First Build Targets

1. `clean_framed_door_v0`
2. `gothic_pointed_portal_surround_v0`
3. `gothic_plank_door_with_hinge_straps_v0`
4. `raised_panel_door_relief_stack_v0`
5. `arched_door_wall_module_v0`

## Boundary

This page does not define gameplay interaction, lock logic, animation, or wall
placement. Door swing and collision need separate game-system contracts.
