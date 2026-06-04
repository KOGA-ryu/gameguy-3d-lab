# Walls And Vertical Bays V0

## Purpose

Walls are not just flat blocks. They organize openings, supports, bays,
buttresses, niches, arcades, courses, parapets, and surface detail. This family
should become the parent context that receives doors, windows, railings, trim,
and ceiling connections.

## Component Breakdown

Primary components:

- `pier`
- `buttress`
- `pilaster`
- `bay`
- `arcade`
- `course`
- `block`
- `niche`
- `blind_tracery_panel`
- `parapet`

Useful anatomy:

- wall field
- bay grid
- vertical support
- opening cut
- reveal
- course lines
- plinth course
- parapet cap
- buttress step
- surface panel

## Style Directions

Gothic:

- vertical bays
- buttresses
- pointed arcades
- blind tracery panels
- tall window openings

Romanesque:

- thick walls
- round arcades
- small openings
- heavy piers

Renaissance:

- ordered bay grids
- pilasters
- cornice courses
- rectangular openings

Rustic:

- rough blocks
- uneven courses
- chipped bevels
- displacement detail

Modern:

- large flat fields
- clean reveals
- simple openings

## Geometric Shaping Ledger

`bay`

```text
source shapes: rectangle, grid cell, construction_cell
operations: array_linear, compound_asset, selected_subgraph
edit knobs: bay width, bay height, repeat count, opening mask
visible result: repeated wall span
```

`pier`

```text
source shapes: square, rectangle, octagon, circle
operations: extrude, section_stack, bevel_edges, compound_asset
edit knobs: footprint, height, taper, base/cap stack, attached shaft count
visible result: vertical support mass
```

`buttress`

```text
source shapes: rectangle, trapezoid, triangle
operations: extrude, section_stack, bevel_edges, array_linear
edit knobs: projection, step count, slope, cap style, bay attachment
visible result: stepped exterior support
```

`arcade`

```text
source shapes: arch_profile, pointed_arch_profile, rectangle
operations: array_linear, boolean_cut, sweep, bevel_edges
edit knobs: arch count, span, springline, pier width, trim thickness
visible result: repeated arch opening or blind arcade
```

`blind_tracery_panel`

```text
source shapes: rectangle, pointed_arch_profile, circle, star_polygon
operations: relief_stack, selected_subgraph, offset_profile, bevel_edges
edit knobs: panel count, motif selection, recess depth, line thickness
visible result: decorative wall field without through-openings
```

## Blender Tool Groups

- cube/profile mesh for wall fields, piers, buttresses, and courses
- array for bay repetition, courses, block fields, and arcades
- booleans for door/window/niche openings
- curve/path sweep for arch trims and parapet caps
- relief stack for blind panels and stone courses
- bevel/weighted normals for readable masonry edges
- material assignment by support, field, trim, and cut reveal
- validation for openings, sockets, and child asset anchors

## First Build Targets

1. `clean_wall_bay_grid_v0`
2. `gothic_bay_with_pointed_window_socket_v0`
3. `stepped_buttress_wall_module_v0`
4. `blind_arcade_wall_panel_v0`
5. `parapet_wall_with_railing_socket_v0`

## Boundary

This page does not decide full building layout. It defines reusable wall
modules and child-asset anchors for later map assembly.
