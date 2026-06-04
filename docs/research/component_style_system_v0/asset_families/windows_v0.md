# Windows V0

## Purpose

Windows combine opening geometry, frame logic, tracery, paneling, glass, and
wall integration. They are a strong target for the sacred-geometry lane because
one construction field can produce mullions, foils, rose patterns, and opening
cells through selection and omission.

## Component Breakdown

Primary components:

- `jamb`
- `sill`
- `head`
- `arch_head`
- `mullion`
- `transom`
- `tracery`
- `glass_panel`
- `reveal`
- `hood_mould`

Useful anatomy:

- opening
- light
- lancet
- mullion grid
- tracery head
- foil motif
- rose center
- glazing cell
- stone reveal
- drip or hood mould

## Style Directions

Gothic:

- lancet openings
- pointed arch heads
- bar tracery
- trefoil/quatrefoil/cinquefoil motifs
- rose window radial fields

Romanesque:

- round arches
- thick reveals
- paired small openings

Renaissance:

- rectangular frames
- pediments
- ordered mullion grids

Modern:

- clean frames
- large panes
- simple reveals

Islamic geometric:

- lattice screens
- rosette and star cell selections
- repeated panel modules

## Geometric Shaping Ledger

`jamb`

```text
source shapes: rectangle, square, custom profile
operations: extrude, bevel_edges, relief_stack
edit knobs: side thickness, reveal depth, bevel width, material region
visible result: left/right vertical frame or stone reveal
```

`sill`

```text
source shapes: rectangle, trapezoid, ogee side profile
operations: extrude, bevel_edges, profile_operation_stack
edit knobs: projection, slope, underside lip, end cap
visible result: bottom ledge with weathering or ornamental profile
```

`arch_head`

```text
source shapes: pointed_arch_profile, arch_profile, circle
operations: sweep, boolean_cut, offset_profile, bevel_edges
edit knobs: span, springline, apex height, trim thickness, cut depth
visible result: top frame or opening arch
```

`mullion`

```text
source shapes: rectangle, capsule, rounded_rectangle
operations: line_promotion, sweep, array_linear, bevel_edges
edit knobs: mullion count, width, depth, spacing, profile style
visible result: vertical stone or wood dividers
```

`tracery`

```text
source shapes: circle, star_polygon, pointed_arch_profile, construction_cell
operations: selected_subgraph, line_promotion, cell_promotion, offset_profile
edit knobs: selected line families, foil count, line thickness, opening mask
visible result: patterned window head or rose window linework
```

## Blender Tool Groups

- `mesh_from_pydata` for custom arch and tracery profiles
- curve/path sweep for mullions, arch bands, and hood moulds
- booleans for opening cuts and glazing pockets
- array/mirror for paired jambs and repeated mullions
- solidify/wireframe for lattice or tracery linework
- bevel/weighted normals for stone edges
- material assignment for stone, lead, and glass regions

## First Build Targets

1. `gothic_lancet_window_frame_v0`
2. `gothic_two_light_window_with_quatrefoil_v0`
3. `rose_window_selected_subgraph_v0`
4. `rectangular_window_clean_frame_v0`
5. `geometric_lattice_window_panel_v0`

## Boundary

This page does not decide lighting, transparency shaders, glass physics, or
wall-cut integration. Those should be separate adapter and placement policies.
