# Columns, Piers, And Supports V0

## Purpose

Columns and piers carry the vertical rhythm of cathedrals, crypts, halls,
bridges, cloisters, and dungeons. They connect floors, arches, vaults, walls,
railings, and ceilings.

This family needs both simple reusable supports and rich compound variants.

## Component Breakdown

Primary components:

- column base
- plinth
- shaft
- fluted shaft
- clustered shaft
- half column
- attached shaft
- compound pier
- capital
- collar
- impost block
- column cap
- arch spring connector
- floor/ceiling socket

Useful anatomy:

- footprint
- base stack
- shaft profile
- entasis
- rib attachment
- collar bands
- capital bell
- abacus block
- springline point
- connector faces

## Style Directions

Gothic:

- clustered shafts
- compound piers
- attached ribs
- capitals supporting arches
- vertical emphasis

Classical/Renaissance:

- round columns
- base/capital orders
- fluting
- proportional shaft taper

Romanesque:

- heavy round or square piers
- simple capitals
- thick arch support

Rustic:

- rough posts
- irregular stone piers
- chipped bases

Modern:

- clean cylinders
- square posts
- exposed structural supports

## Geometric Shaping Ledger

`plinth_base`

```text
source shapes: square, octagon, rectangle
operations: section_stack, extrude, bevel_edges
edit knobs: footprint, height, chamfer, base layer count
visible result: grounded support base
```

`shaft`

```text
source shapes: circle, octagon, capsule, star_polygon
operations: radial_stack, section_stack, modifier_screw, bevel_edges
edit knobs: height, radius, segment count, entasis, taper
visible result: main vertical support body
```

`clustered_shaft`

```text
source shapes: circle, capsule, custom lobed profile
operations: array_radial, radial_stack, section_stack, join_objects
edit knobs: attached shaft count, rib radius, core radius, spacing, taper
visible result: compound Gothic support silhouette
```

`capital`

```text
source shapes: trapezoid, circle, square, custom side profile
operations: section_stack, profile_operation_stack, bevel_edges, relief_stack
edit knobs: capital height, bell radius, abacus width, collar count
visible result: transition from shaft to arch/ceiling support
```

`arch_spring_connector`

```text
source shapes: rectangle, arch_springline, socket
operations: compound_asset, boolean_cut, bevel_edges
edit knobs: springline height, connector width, socket depth, face direction
visible result: explicit place where an arch or rib lands
```

## Blender Tool Groups

- radial stack and section stack for shafts
- screw/revolve for classical-style profiles
- radial duplication for clustered shafts and ribs
- mesh-from-points for custom lobed cross sections
- bevel/weighted normals for hard stone forms
- booleans for sockets and connector pockets
- material assignment by base, shaft, collar, capital, socket

## First Build Targets

1. `clean_round_column_v0`
2. `gothic_clustered_shaft_pier_v0`
3. `compound_pier_with_arch_sockets_v0`
4. `half_column_wall_attached_v0`
5. `fluted_column_low_poly_v0`

## Boundary

This page does not make structural claims. Support roles are visual/gameplay
contracts unless a later structural-simulation lane is created.
