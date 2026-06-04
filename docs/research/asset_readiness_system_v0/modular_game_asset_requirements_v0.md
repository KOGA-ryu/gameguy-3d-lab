# Modular Game Asset Requirements V0

Good-looking geometry is not enough. A useful game asset also needs modular
rules, placement data, collision, material roles, and performance tiers.

## Required For Every 3D Asset

| Requirement | Why It Matters |
| --- | --- |
| asset ID | Keeps recipes, previews, exports, and notes connected. |
| family/component | Connects the asset to taxonomy and style sheets. |
| dimensions in meters | Prevents scale drift across maps. |
| origin and pivot | Controls snapping, rotation, replacement, and animation. |
| bounds | Allows validation and placement checks. |
| grid snap size | Makes modular kit assembly predictable. |
| sockets/connectors | Allows rails, walls, stairs, floors, and trim to connect. |
| material slots | Lets one mesh support multiple dungeon styles. |
| UV strategy | Keeps texture work from becoming per-asset chaos. |
| collision proxy | Makes gameplay reliable without using decorative mesh. |
| LOD tiers | Keeps dense assets usable on lower hardware. |
| hardware policy | Defines which details survive low, mid, and high settings. |
| export target | Defines whether the asset is `.blend`, `.glb`, `.fbx`, or proof-only. |

## Scale And Grid

Use meters. Each asset should declare:

```text
dimensions_m:
origin:
pivot:
grid_snap_m:
placement_footprint:
```

Example:

```text
dimensions_m: 0.45 x 1.20 x 0.45
origin: bottom_center
pivot: bottom_center
grid_snap_m: 0.25
placement_footprint: square_0_5m
```

## Sockets And Connectors

Sockets should be named before modeling.

Examples:

```text
rail_socket_left
rail_socket_right
wall_socket_back
floor_socket_bottom
arch_springline_left
arch_springline_right
ceiling_rib_socket_top
```

Each socket needs:

- local position
- local rotation
- accepted connector type
- visible socket depth
- whether it is gameplay-critical or decorative

## Collision

Do not use ornate visual mesh as collision by default.

Collision choices:

- simple box
- capsule
- cylinder
- convex hull
- compound proxy
- no collision, decorative only

Collision should follow gameplay read, not every decorative groove.

## LOD And Hardware Tiers

Define at least:

```text
LOD0: close asset
LOD1: gameplay distance
LOD2: far silhouette
collision_proxy: separate helper
```

Hardware policy:

- low: simple material slots, no decals, fewer small cutters, lower LOD sooner
- mid: procedural bump, trim sheets, limited optional detail
- high: decals and extra surface detail allowed where budget permits

The texture system rule still applies:

```text
*** DECALS ARE HIGH-COST OPTIONAL DETAIL ***
lower-compute hardware does not get decals
```

## Material Roles

Use semantic material roles rather than final color names.

Examples:

- stone_core
- shadow_recess
- worn_edge
- metal_socket
- moss_lower
- soot_upper
- waterline
- carved_detail
- trim_band
- collision_helper

## Variants And States

Assets should declare expected variants early.

Examples:

- clean
- worn
- cracked
- broken
- wet
- mossy
- lit
- unlit
- open
- closed
- locked
- damaged

The base shape should still work without all variants.

## Anchors

Declare anchors for later systems:

- light anchor
- VFX anchor
- particle anchor
- sound anchor
- interaction prompt anchor
- loot socket
- door hinge axis
- damage break point
- snap point

## Naming Rule

Use names that say what the asset is and where it belongs:

```text
family.component.style.variant.version
```

Example:

```text
railing.newel_post.gothic_blind_tracery.clean_v0
```

