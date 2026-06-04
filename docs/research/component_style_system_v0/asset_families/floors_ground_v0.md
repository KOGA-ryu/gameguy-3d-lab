# Floors And Ground Modules V0

## Purpose

Floors are the base layer of nearly every room, hall, bridge, crypt, courtyard,
and dungeon path. They define movement, scale, wear patterns, drainage, room
identity, and where other assets can anchor.

This family should be treated as structural gameplay geometry first and surface
detail second.

## Component Breakdown

Primary components:

- floor slab
- tile
- border tile
- mosaic field
- cracked slab
- landing pad
- curb
- drainage channel
- threshold plate
- bridge deck
- water edge
- floor socket
- hazard seam

Useful anatomy:

- walkable field
- outer border
- tile grid
- expansion seam
- broken edge
- inset channel
- raised curb
- anchor socket
- trim strip
- transition lip

## Style Directions

Gothic:

- stone flags
- border bands
- inlaid rosette or quatrefoil fields
- worn nave paths

Romanesque:

- heavy rectangular slabs
- simple block joints
- thick threshold stones

Islamic geometric:

- star grids
- rosette tile fields
- selected construction-cell mosaics

Wet sewer:

- slick stone
- drainage channels
- algae/slime bands

Lava forge:

- basalt plates
- glowing cracks
- metal grates

Ice vault:

- frosted stone
- ice panels
- slick edge highlights

## Geometric Shaping Ledger

`floor_slab`

```text
source shapes: rectangle, square, custom_polygon
operations: extrude, bevel_edges, compound_asset
edit knobs: width, depth, thickness, bevel width, material role
visible result: walkable base module
```

`tile_grid`

```text
source shapes: square, rectangle, construction_cell
operations: array_linear, selected_subgraph, relief_stack
edit knobs: tile size, joint width, grid count, omitted cells, pattern rotation
visible result: repeated floor tiles or mosaic cells
```

`border_band`

```text
source shapes: rectangle, custom profile, star_polygon
operations: extrude, trim_sheet, array_linear, bevel_edges
edit knobs: border width, inset depth, motif repeat, corner treatment
visible result: edge band around a floor field
```

`drainage_channel`

```text
source shapes: rectangle, capsule, trapezoid
operations: boolean_cut, relief_stack, bevel_edges
edit knobs: channel width, depth, slope, grate option, waterline material
visible result: floor groove, drain, or sewer runnel
```

`broken_edge`

```text
source shapes: custom_polygon, triangle, rectangle
operations: boolean_cut, bevel_edges, displacement, material_mask
edit knobs: chip count, edge roughness, crack depth, rubble socket
visible result: damaged floor boundary or ruin transition
```

## Blender Tool Groups

- mesh primitives for slabs and curbs
- `mesh_from_pydata` for custom tile fields and broken edges
- array for tile grids and border repeats
- boolean/relief stack for channels, cracks, and insets
- bevel/weighted normals for walkable stone readability
- material slots for walkable, border, recess, waterline, hazard
- UV box projection for blockouts and trim-sheet strips for borders

## First Build Targets

1. `clean_stone_floor_slab_v0`
2. `gothic_border_floor_tile_v0`
3. `selected_cell_mosaic_floor_v0`
4. `sewer_floor_with_drain_channel_v0`
5. `broken_floor_edge_rubble_socket_v0`

## Boundary

This page does not define navmesh, physics collision, accessibility, or final
material art. Those should be separate gameplay and texture policies.
