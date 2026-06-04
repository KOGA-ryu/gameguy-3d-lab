# Ceilings And Vaults V0

## Purpose

Ceilings and vaults are where the construction-geometry idea becomes most
important. A dense 2D field can select ribs, bosses, web cells, muqarnas cells,
dome segments, coffers, and rosettes, then lift or fold them into 3D.

## Component Breakdown

Primary components:

- `rib`
- `vault_web`
- `boss`
- `pendant`
- `dome_segment`
- `muqarnas_cell`
- `coffer`
- `rosette`
- `fan_rib`
- `arch_band`

Useful anatomy:

- bay
- spring point
- rib path
- web cell
- boss center
- pendant axis
- dome ring
- cell tier
- cascade order
- selected subgraph

## Style Directions

Gothic:

- pointed arch ribs
- rib vaults
- bosses at intersections
- fan ribs
- web surfaces between selected ribs

Islamic geometric / muqarnas:

- 2D cell plans
- tiered cell lifting
- rosette centers
- cascade order
- repeated but selected cells

Renaissance:

- coffers
- domes
- radial ribs
- ordered panels

Modern:

- clean ceiling grids
- simple panels
- exposed beams

## Geometric Shaping Ledger

`rib`

```text
source shapes: construction_edge, arch_profile, capsule, circle
operations: line_promotion, sweep, thicken_operation, bevel_edges
edit knobs: selected edge ids, rib thickness, profile radius, spring height
visible result: raised or structural-looking ceiling rib
```

`vault_web`

```text
source shapes: construction_cell, custom_polygon
operations: cell_promotion, lift_operation, fold_operation, bevel_edges
edit knobs: cell selection, height rule, concavity, subdivision, thickness
visible result: curved or folded surface between ribs
```

`boss`

```text
source shapes: circle, star_polygon, rosette
operations: node_promotion, radial_stack, array_radial, bevel_edges
edit knobs: node selection, radius, lobe count, depth, pendant option
visible result: ornament at rib intersections
```

`muqarnas_cell`

```text
source shapes: construction_cell, triangle, custom_polygon
operations: cell_promotion, lift_operation, cascade_order, section_stack
edit knobs: tier, cell height, fold direction, neighbor join policy
visible result: stepped niche or dome transition cell
```

`coffer`

```text
source shapes: rectangle, octagon, circle
operations: relief_stack, boolean_cut, bevel_edges, array_linear
edit knobs: panel size, recess depth, grid count, bevel width
visible result: repeated recessed ceiling panel
```

## Blender Tool Groups

- construction graph and cell-selection compilers before Blender
- `mesh_from_pydata` for lifted cells and rib paths
- curve/path sweep for ribs and arch bands
- radial repeat for dome ribs, rosettes, and bosses
- relief/boolean cuts for coffers
- bevel/weighted normals for ribs and cell edges
- material assignment by rib, web, boss, and cell tier
- validation for open seams, bounds, and named intersections

## First Build Targets

1. `single_bay_rib_vault_blockout_v0`
2. `selected_cell_vault_web_v0`
3. `center_boss_rosette_v0`
4. `muqarnas_cell_tier_proof_v0`
5. `coffered_ceiling_panel_v0`

## Boundary

This page does not solve final structural logic or physically accurate masonry.
It defines source geometry promotion for game-asset prototypes.
