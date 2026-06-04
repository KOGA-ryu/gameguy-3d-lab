# Terrain, Cliffs, And Water Edges V0

## Purpose

Buildings in this project sit on cliffs, ravines, cave floors, bridges, water
channels, roads, and foundations. Terrain pieces need to connect architectural
modules to the map instead of being a separate afterthought.

## Component Breakdown

Primary components:

- terrain tile
- cliff face
- ledge
- ravine edge
- cave wall
- rock outcrop
- path/road
- bridge footing
- water plane
- water edge
- shore/embankment
- retaining wall
- foundation pad
- terrain socket

Useful anatomy:

- top walkable surface
- vertical cut face
- slope
- ledge lip
- erosion line
- waterline
- path centerline
- cliff socket
- building pad
- hazard edge

## Style Directions

Gothic cliff monastery/cathedral:

- stone foundations merging into cliff
- retaining walls
- bridge approaches

Wet sewer/aqueduct:

- water channels
- algae edges
- damp walls

Lava forge:

- basalt ground
- glowing cracks
- hazard channels

Ice vault:

- icy ledges
- frozen water edges
- slick paths

Overgrown shrine:

- mossy rocks
- roots
- broken paving

## Geometric Shaping Ledger

`terrain_tile`

```text
source shapes: grid, rectangle, custom_polygon
operations: mesh_from_heightfield, bevel_edges, material_mask
edit knobs: size, height variation, slope, walkable mask
visible result: local ground module
```

`cliff_face`

```text
source shapes: custom_polygon, grid strip
operations: extrude, displacement, bevel_edges
edit knobs: height, roughness, ledge count, overhang, material bands
visible result: vertical or sloped rock wall
```

`water_edge`

```text
source shapes: rectangle, custom shoreline curve
operations: extrude, bevel_edges, material_mask
edit knobs: waterline height, bank width, algae band, edge softness
visible result: boundary between floor/terrain and water
```

`foundation_pad`

```text
source shapes: rectangle, custom_polygon
operations: extrude, bevel_edges, compound_asset
edit knobs: footprint, height, stair/road sockets, terrain blend lip
visible result: flat anchor for buildings or modules
```

`path_or_road`

```text
source shapes: curve path, rectangle, capsule
operations: sweep, array_linear, material_mask
edit knobs: width, curve points, edge wear, cobble/tile repeat
visible result: navigable route between modules
```

## Blender Tool Groups

- grid/mesh-from-points for terrain tiles
- displacement for cliff roughness and rock variation
- curve/path sweep for roads and water edges
- material masks for waterline, moss, hazard, walkable
- booleans for sockets and foundations
- bevel/weighted normals where architecture meets terrain

## First Build Targets

1. `flat_foundation_pad_v0`
2. `cliff_edge_building_socket_v0`
3. `ravine_ledge_path_v0`
4. `sewer_water_channel_edge_v0`
5. `basalt_lava_crack_floor_v0`

## Boundary

This page does not replace map-generation topology. It describes 3D terrain
asset families that should consume map/path/socket data later.
