# Railing Post Style Atlas V0

## Purpose

This atlas narrows railing work to one reusable object:

```text
one post -> many style variants
```

The post is the study object. Rails, guard panels, full runs, stair pitch, and
code-compliant railing assemblies are out of scope for this lane.

## Core Rule

Every variant should share the same comparable anatomy:

- `plinth`
- `base`
- `shaft`
- `collar`
- `cap`
- `finial`
- `rail_socket_hint`
- `face_panel`
- `side_detail`
- `material_regions`

That lets the repo compare style variants without changing the whole asset
family every time.

## Shared Envelope

Use a shared post envelope for early variants:

```text
height class: waist-high architectural post
footprint: square-reading or round-reading
rail sockets: hint geometry only, no rail generated
detail budget: low-poly by default
decals: off by default
finish: named material regions, bevels, weighted normals, UV hints
```

The rail socket hint is important because the post should still know how a rail
would attach later. It should not force the generator to build the rail.

## Variant Workcard Shape

Each post style needs this structure:

```text
style_id
plain_name
visual_read
base_post_anatomy
2d_source_shapes
shape_operations
blender_tool_sequence
edit_knobs
do_not_do_rules
manual_inspection_notes
promotion_status
```

## Tier A: Buildable With Existing Repo Language

These should be the first many-style set because they mostly use existing
geometry terms and Blender tool cards.

### `post_style.plain_square_reference_v0`

Visual read:

```text
simple square post with plinth, shaft, cap, and socket hints
```

2D shapes:

- square
- rectangle
- rounded rectangle

Operations:

- extrude
- bevel edges
- relief stack for shallow face panels

Blender tools:

- `primitive_cube_add`
- `modifier_bevel`
- `modifier_weighted_normal`
- `uv_smart_project`

Use:

This is the control object. Keep it plain so every styled post can be compared
against it.

### `post_style.gothic_buttress_newel_v0`

Visual read:

```text
square post that reads like a tiny buttress or pier
```

2D shapes:

- square
- trapezoid
- pointed arch profile
- rectangle

Operations:

- extrude
- radial duplicate on four sides
- blind arch relief
- bevel edges

Blender tools:

- `primitive_cube_add`
- `mesh_from_pydata`
- `object_duplicate_radial`
- `modifier_boolean`
- `modifier_bevel`

### `post_style.gothic_blind_tracery_box_v0`

Visual read:

```text
clean box post with recessed face panels and shallow tracery ornament
```

2D shapes:

- rectangle
- pointed arch profile
- circle
- quatrefoil or trefoil lobe pattern

Operations:

- inset/recess panel
- offset profile
- shallow relief
- optional boolean cut

Blender tools:

- `primitive_cube_add`
- `mesh_from_pydata`
- `modifier_boolean`
- `modifier_solidify`
- `modifier_bevel`

### `post_style.gothic_clustered_shaft_v0`

Visual read:

```text
compound-pier post with a center shaft and attached ribs
```

2D shapes:

- circle
- capsule
- octagon

Operations:

- radial stack
- radial duplicate
- section stack
- collar rings

Blender tools:

- `primitive_cylinder_add`
- `mesh_from_pydata`
- `object_duplicate_radial`
- `primitive_torus_add`
- `modifier_weighted_normal`

### `post_style.gothic_pinnacle_cap_v0`

Visual read:

```text
faceted post with stepped cap and detachable spire-like top
```

2D shapes:

- square
- octagon
- triangle
- cone profile

Operations:

- square-to-octagon transition
- stepped cap stack
- faceted cone or pyramid finial

Blender tools:

- `mesh_from_pydata`
- `primitive_cube_add`
- `primitive_cone_add`
- `modifier_bevel`

### `post_style.gothic_crocketed_finial_v0`

Visual read:

```text
post with repeated small projections along cap or finial edges
```

2D shapes:

- triangle
- capsule
- leaf-like low-poly wedge

Operations:

- array along edge
- radial duplicate around finial
- bevel small projections

Blender tools:

- `mesh_from_pydata`
- `modifier_array`
- `object_duplicate_radial`
- `modifier_bevel`

### `post_style.roman_squat_column_v0`

Visual read:

```text
round, heavier, older-looking post with simple base and capital
```

2D shapes:

- circle
- rectangle
- torus-like side profile

Operations:

- revolve or radial stack
- simple collar stack
- smooth shaft

Blender tools:

- `primitive_cylinder_add`
- `modifier_screw`
- `primitive_torus_add`
- `modifier_weighted_normal`

### `post_style.castle_crenel_cap_v0`

Visual read:

```text
square defensive post with blocky merlon-like cap teeth
```

2D shapes:

- square
- rectangle
- step profile

Operations:

- extrude block core
- array cap teeth
- bevel exposed corners

Blender tools:

- `primitive_cube_add`
- `modifier_array`
- `modifier_bevel`
- `mark_sharp`

### `post_style.rustic_timber_chamfered_v0`

Visual read:

```text
wooden post with chamfered corners, simple cap, and hand-cut unevenness
```

2D shapes:

- square
- octagon
- rectangle

Operations:

- chamfer square to low octagon
- add shallow split or groove lines
- add uneven bevel widths

Blender tools:

- `primitive_cube_add`
- `modifier_bevel`
- `modifier_displace`
- `procedural_noise_texture`
- `material_principled_shader`

### `post_style.forge_riveted_iron_v0`

Visual read:

```text
dark metal post with bands, rivets, collars, and socket plates
```

2D shapes:

- circle
- rectangle
- rounded rectangle
- small disk

Operations:

- cylinder or box core
- band collars
- array rivets
- socket plates

Blender tools:

- `primitive_cylinder_add`
- `primitive_cube_add`
- `object_duplicate_radial`
- `modifier_array`
- `material_principled_shader`

## Tier B: Needs More Shape-Specific Decisions

These are valuable, but should wait until the Tier A variants expose what
controls the post needs.

### `post_style.victorian_turned_newel_v0`

Visual read:

```text
lathe-turned post with bulb, neck, bead bands, and rounded cap
```

Needs:

- side-profile drawing controls
- revolve profile validation
- bead spacing rules

Likely tools:

- `modifier_screw`
- `primitive_torus_add`
- `modifier_bevel`
- `shade_smooth`

### `post_style.art_nouveau_vine_post_v0`

Visual read:

```text
flowing vertical post with asymmetrical vine or tendril relief
```

Needs:

- curve path controls
- asymmetric side mask
- low-compute vine simplification

Likely tools:

- `curve_bezier_add`
- `curve_bevel_profile`
- `modifier_solidify`
- `modifier_bevel`

### `post_style.geometric_star_panel_post_v0`

Visual read:

```text
box post with star-grid panels selected from sacred geometry linework
```

Needs:

- source graph selection
- guide-line omission rules
- promotable line/cell tags

Likely tools:

- `mesh_from_pydata`
- `modifier_solidify`
- `modifier_boolean`
- `modifier_bevel`

### `post_style.moorish_lobed_arch_post_v0`

Visual read:

```text
post faces with horseshoe or lobed arch panels and geometric bands
```

Needs:

- lobed arch profile term
- border band profile
- face-panel proportion rules

Likely tools:

- `mesh_from_pydata`
- `modifier_boolean`
- `modifier_array`
- `modifier_bevel`

### `post_style.noble_marble_baluster_newel_v0`

Visual read:

```text
polished stone post with smooth entasis, bead bands, and clean cap
```

Needs:

- side-profile stack
- material region polish rules
- less chipped wear than dungeon stone

Likely tools:

- `modifier_screw`
- `primitive_torus_add`
- `shade_smooth`
- `uv_smart_project`

## Tier C: Later Hero Or Specialized Variants

These are useful for worldbuilding but should not be first generator targets.

- `post_style.crypt_reliquary_panel_post_v0`
- `post_style.sewer_cistern_pipe_post_v0`
- `post_style.mine_quarry_braced_post_v0`
- `post_style.workshop_clamped_tool_post_v0`
- `post_style.library_carved_lectern_post_v0`
- `post_style.ruined_broken_socket_post_v0`
- `post_style.wilderness_shrine_stacked_stone_post_v0`
- `post_style.market_rope_bound_post_v0`

## Variant Comparison Checks

Every post variant should answer:

- Does the silhouette read from 10 meters?
- Is the base stable and readable?
- Are rail socket hints present but not forcing a rail?
- Are all four sides intentionally handled?
- Are corners chamfered or deliberately sharp?
- Does the cap terminate the post cleanly?
- Are material regions named?
- Are high-cost details optional?
- Can a human edit the post without rebuilding the full railing?

## Do Not Do Rules

- Do not generate a full railing assembly in this lane.
- Do not require rail geometry to judge the post.
- Do not hide style choices in Blender scripts.
- Do not make decals required for the style to read.
- Do not make every variant share the same shaft silhouette.
- Do not apply ornament before the plinth, shaft, cap, and socket hints exist.

## Recommended Next Build Slice

Status: completed as `3D-LAB-0093 single_post_style_matrix_v0`.

The source-side matrix now lives at:

```text
data/architecture/component_style_sheets/railings/single_post_style_matrix_v0.json
```

Validate it with:

```bash
python3 scripts/validate_single_post_style_matrix_v0.py
```

## Next Promotion Slice

```text
3D-LAB-0094 single_post_matrix_to_asset_recipe_v0
```

Goal:

```text
Select one matrix variant, emit a tiny source asset recipe, compile
deterministic gameguy_asset_v0 JSON, and validate. No full railings. Blender
preview can wait until the recipe path is stable.
```

Best first generated variants:

1. `post_style.plain_square_reference_v0`
2. `post_style.gothic_buttress_newel_v0`
3. `post_style.gothic_clustered_shaft_v0`
4. `post_style.castle_crenel_cap_v0`
5. `post_style.rustic_timber_chamfered_v0`

That gives one clean base, two Gothic variants, one castle variant, and one
wood variant without forcing the repo back into complete railing assemblies.
