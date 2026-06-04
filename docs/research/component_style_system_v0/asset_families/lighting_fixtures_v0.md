# Lighting Fixtures V0

## Purpose

Lighting fixtures are small assets with outsized value. They communicate
scale, mood, navigation, danger, magic, and dungeon identity. They also need
explicit light anchors for Blender/game adapters later.

## Component Breakdown

Primary components:

- torch
- wall sconce
- brazier
- chandelier
- lantern
- candle
- candle cluster
- lamp chain
- lamp bracket
- flame holder
- crystal light
- magic rune light
- floor light marker
- light socket

Useful anatomy:

- mount plate
- arm/bracket
- bowl/cup
- candle stem
- wick/flame anchor
- chain
- glass enclosure
- glow mesh
- shadow caster
- attachment socket

## Style Directions

Gothic:

- iron sconces
- candle clusters
- chandeliers
- carved stone mounts

Dungeon/crypt:

- torches
- braziers
- smoky wall lamps

Arcane:

- crystal lights
- rune glow
- floating light anchors

Modern:

- simple fixtures
- clean light panels

Rustic:

- rough torches
- wood brackets
- iron hooks

## Geometric Shaping Ledger

`wall_sconce`

```text
source shapes: rectangle, circle, capsule
operations: extrude, sweep, bevel_edges, mirror_axis
edit knobs: mount size, arm length, cup radius, flame anchor height
visible result: wall-mounted light fixture
```

`brazier`

```text
source shapes: circle, octagon, bowl side profile
operations: radial_stack, modifier_screw, array_radial, bevel_edges
edit knobs: bowl radius, leg count, height, coal bed depth
visible result: floor-standing fire holder
```

`chandelier`

```text
source shapes: circle, curve path, capsule
operations: array_radial, sweep, compound_asset
edit knobs: arm count, ring radius, chain length, candle count
visible result: hanging multi-light fixture
```

`candle_cluster`

```text
source shapes: circle, cylinder, custom melted profile
operations: array_linear, array_radial, radial_stack
edit knobs: candle count, height variation, wax drip option, flame anchors
visible result: clustered candle prop or altar detail
```

`light_socket`

```text
source shapes: attachment_point, radial connector
operations: compound_asset, validation_export
edit knobs: light type, radius, color role, shadow policy
visible result: explicit anchor for game or Blender light object
```

## Blender Tool Groups

- cylinders/radial stacks for candles, bowls, cups
- curve/path sweep for brackets, chains, arms
- radial arrays for chandeliers and braziers
- emissive material slots for flames, crystals, runes
- attachment/socket metadata for actual light placement
- material assignment for iron, wax, stone, glass, emissive

## First Build Targets

1. `gothic_wall_sconce_v0`
2. `simple_brazier_v0`
3. `candle_cluster_v0`
4. `iron_chandelier_ring_v0`
5. `arcane_crystal_light_socket_v0`

## Boundary

This page does not define final lighting engine behavior. It defines fixture
geometry and light anchor metadata for later adapters.
