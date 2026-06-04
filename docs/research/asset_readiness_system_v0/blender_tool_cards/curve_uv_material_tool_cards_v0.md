# Curve, UV, And Material Tool Cards V0

These tools turn modeled geometry into cleaner mesh and assign practical surface
roles.

## `curve_to_mesh`

Plain English:

Convert a curve object into mesh geometry.

Best used for:

- finalizing rib/rail/arch curves
- converting curve-based trim before export
- preparing curve forms for booleans, bevels, UVs, or LODs

Avoid when:

- the curve path is still being tuned
- non-destructive editing is still useful
- the object is only a construction guide

Key source fields:

```text
curve_object_id
conversion_policy
preserve_source_curve
target_mesh_name
```

How to use effectively:

- Keep the original curve as source evidence or hide it in the final preview.
- Convert only after bevel depth/profile is approved.
- Check normals and face density immediately after conversion.
- Follow with cleanup, material assignment, and LOD policy.

Common mistakes:

- converting too early
- losing the path that explains the ornament
- creating dense mesh from a tiny curve detail
- forgetting UVs after conversion

Architectural examples:

- vault rib converted for export
- curved balcony rail converted for material assignment
- arched trim converted for bevel cleanup

## `uv_cube_project`

Plain English:

Apply box-style UV projection to a mesh.

Best used for:

- blocky stone
- posts
- frames
- walls
- plinths
- rails with mostly planar sides

Avoid when:

- the asset needs hand-authored UV islands
- curved ornamental surfaces need continuous UV flow
- trim-sheet mapping needs exact island placement

Key source fields:

```text
target_object
cube_size
texel_density
material_role
uv_policy
```

How to use effectively:

- Use cube projection as the first practical UV pass for architectural blocks.
- Match cube size to intended texel density.
- Keep material roles separate so trim, recess, and worn edges can differ.
- Use more specific unwraps only for hero assets or curved ornament.

Common mistakes:

- stretching on curved or diagonal detail
- different cube sizes across connected modules
- ignoring material-role boundaries
- relying on decals that low hardware will not receive

Architectural examples:

- stone railing post
- wall bay block
- plinth base
- door/window frame blockout

## `material_assign_by_part`

Plain English:

Assign material slots to named mesh parts or face groups.

Best used for:

- semantic material roles
- trim versus field regions
- shadow recesses
- worn edges
- metal sockets
- moss/wet/soot zones

Avoid when:

- parts are not named
- material names describe final colors instead of roles
- every tiny face receives a unique material

Key source fields:

```text
mesh_parts
material_map
material_role
hardware_tier_policy
dungeon_style
```

How to use effectively:

- Assign roles first, final palettes later.
- Keep one part able to swap between dungeon styles.
- Use material roles to carry detail when decals are disabled.
- Record why a surface gets a special material role.

Common mistakes:

- color-first material naming
- too many slots for low-compute assets
- not distinguishing shadow recess from stone core
- forgetting collision/helper objects need non-render or helper materials

Architectural examples:

- plinth body as `stone_core`
- inset panel as `shadow_recess`
- cap arris as `worn_edge`
- rail socket as `metal_socket` or `dark_joint`

