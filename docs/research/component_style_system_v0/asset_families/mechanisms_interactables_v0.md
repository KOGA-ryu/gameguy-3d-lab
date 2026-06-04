# Mechanisms And Interactables V0

## Purpose

Mechanisms and interactables are assets that change state, communicate puzzle
logic, trigger movement, or alter traversal. They need geometry plus sockets,
states, and optional animation anchors.

## Component Breakdown

Primary components:

- lever
- pressure plate
- switch
- crank
- pulley
- chain wheel
- rotating gear
- sliding block
- door mechanism
- trap floor
- spike trap
- dart hole
- moving platform
- elevator pad
- key socket
- rune switch
- puzzle pedestal

Useful anatomy:

- idle state
- active state
- trigger surface
- pivot point
- slide path
- rotation axis
- socket
- state marker
- animation anchor
- collision region
- VFX/audio anchor

## Style Directions

Gothic crypt:

- stone levers
- rune sockets
- heavy pressure plates

Dungeon/prison:

- iron cranks
- chains
- portcullis mechanisms

Forge:

- gears
- pulleys
- heat valves

Arcane:

- glowing rune switches
- floating keys
- crystal sockets

Rustic:

- wooden levers
- rope pulleys
- simple doors and lifts

## Geometric Shaping Ledger

`lever`

```text
source shapes: cylinder, capsule, sphere, rectangle
operations: radial_stack, sweep, pivot_socket, bevel_edges
edit knobs: handle length, pivot height, rest angle, active angle
visible result: stateful lever with pivot metadata
```

`pressure_plate`

```text
source shapes: rectangle, rounded_rectangle, square
operations: extrude, bevel_edges, inset_faces, validation_export
edit knobs: footprint, thickness, travel distance, trigger region
visible result: floor trigger asset
```

`gear_or_wheel`

```text
source shapes: circle, star_polygon, rectangle teeth
operations: radial_stack, array_radial, bevel_edges
edit knobs: tooth count, radius, thickness, axle socket
visible result: rotating mechanism component
```

`trap_floor`

```text
source shapes: rectangle, tile grid, hinge line
operations: array_linear, boolean_cut, pivot_socket
edit knobs: tile count, hinge side, drop angle, hazard marker
visible result: stateful floor hazard
```

`key_socket`

```text
source shapes: circle, star_polygon, custom_polygon
operations: boolean_cut, relief_stack, emissive_optional
edit knobs: socket shape, depth, key id, glow policy
visible result: puzzle or lock receiver
```

## Blender Tool Groups

- primitives and radial stacks for levers, gears, wheels
- booleans for sockets and key shapes
- arrays/radial arrays for gear teeth and trap tiles
- metadata for pivot, slide, trigger, state, and VFX anchors
- material slots for inactive/active/emissive states
- validation for state names and connector directions

## First Build Targets

1. `stone_pressure_plate_v0`
2. `simple_lever_with_pivot_socket_v0`
3. `iron_crank_wheel_v0`
4. `trap_floor_tile_module_v0`
5. `arcane_key_socket_v0`

## Boundary

This page does not implement gameplay scripts or animation playback. It defines
geometry, state metadata, and adapter-ready anchors.
