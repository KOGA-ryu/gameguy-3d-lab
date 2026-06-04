# Railings And Balustrades V0

## Purpose

Railings define edges, stairs, balconies, terraces, bridges, parapets, and
procession routes. They are also one of the best first families for the repo
because they combine repeated structure with visible ornament.

Near-term focus: do not build the full railing. Build one reusable post and
compare many post styles. The post style atlas is:

```text
docs/research/component_style_system_v0/railing_post_style_atlas_v0.md
```

The current machine-readable starter is:

```text
data/architecture/component_style_sheets/railings/gothic_railing_post_style_sheets_v0.json
```

## Component Breakdown

Primary components:

- `newel_post`
- `intermediate_post`
- `baluster`
- `handrail`
- `base_rail`
- `infill_panel`
- `rail_socket`
- `bracket`
- `cap`
- `finial`

Useful anatomy for posts:

- plinth
- base
- shaft
- collar
- capital or cap
- finial
- rail socket
- face panel
- side ornament

## Style Directions

Gothic:

- pointed arches
- blind tracery
- clustered shafts
- quatrefoil or trefoil motifs
- buttress-like post faces
- small pinnacles or crockets

Victorian:

- turned balusters
- bead bands
- scroll brackets
- dense repeated pickets

Art Nouveau:

- flowing rail lines
- curved infill
- plant-like or asymmetric motifs

Modern:

- simple posts
- flat rails
- cable, glass, or bar infill

Rustic:

- rough posts
- log rails
- chunky brackets
- uneven bevels and surface displacement

## Geometric Shaping Ledger

`newel_post`

```text
source shapes: square, octagon, circle, pointed_arch_profile, capsule
operations: extrude, radial_stack, section_stack, relief_stack, boolean_cut
edit knobs: footprint, height, shaft taper, cap height, socket depth, face mask
visible result: terminal post with named base, shaft, sockets, cap, ornament
```

`baluster`

```text
source shapes: circle, octagon, rounded_rectangle, side profile curve
operations: radial_stack, modifier_screw, section_stack, bevel_edges
edit knobs: spacing, height, belly radius, neck radius, collar count
visible result: repeated vertical support between rails
```

`handrail`

```text
source shapes: rounded_rectangle, capsule, circle, custom profile
operations: sweep, extrude, radial_stack, bevel_edges
edit knobs: length, grip thickness, underside cove, end cap, socket tab
visible result: top rail that reads as grip or stone cap
```

`infill_panel`

```text
source shapes: rectangle, pointed_arch_profile, circle, star_polygon
operations: relief_stack, boolean_cut, array_linear, mirror_axis, offset_profile
edit knobs: bay count, arch span, motif count, cut depth, raised trim width
visible result: panel, grille, or tracery field between posts
```

## Blender Tool Groups

- `primitive_cube_add` for post blocks, rails, panel fields
- `primitive_cylinder_add` and `modifier_screw` for turned or radial posts
- `mesh_from_pydata` for tracery profiles and custom cutters
- `modifier_boolean` for sockets and shallow recesses
- `modifier_array` and `object_duplicate_radial` for repeated balusters, beads,
  crockets, and post-side details
- `modifier_bevel`, `mark_sharp`, `modifier_weighted_normal` for readable edges
- `uv_smart_project`, `material_principled_shader`, `calculate_bounds`,
  `validate_non_manifold` for finish and validation

## First Build Targets

1. `post_style.plain_square_reference_v0`
2. `post_style.gothic_buttress_newel_v0`
3. `post_style.gothic_clustered_shaft_v0`
4. `post_style.castle_crenel_cap_v0`
5. `post_style.rustic_timber_chamfered_v0`

## Boundary

This page does not claim building-code compliance. Code-compliant guardrails
need a separate code/reference lane with jurisdiction, date, measurements, and
usage context.
