# Operator Furniture Handoff V0

This is the future UI/manual workcard shape for furniture. It should let the
operator rough a shape quickly, then hand Codex enough facts to plan geometry
and Blender tools.

## Minimum Workcard

```yaml
furniture_id:
family_id:
caste_tier_ids:
style_ids:
reference_packet_id:
asset_role:
scale_reference:
visible_anatomy:
  - part_id:
    visible: true
    priority: primary
source_fields:
  bounds_m:
  top_profile:
  leg_count:
  panel_grid:
  hardware_positions:
  socket_ids:
geometry_terms:
blender_tool_ids:
material_roles:
manual_edit_notes:
operator_checks:
```

## UI Tags To Support

Furniture body:

- `seat_slab`
- `top_board`
- `bench_top`
- `case`
- `carcass`
- `bed_frame`
- `high_back`

Supports:

- `leg`
- `post`
- `trestle`
- `stretcher`
- `apron`
- `foot`
- `base`

Storage and hardware:

- `lid`
- `door`
- `shelf`
- `hinge`
- `lock_plate`
- `strap`
- `handle`

Decorative/status:

- `raised_panel`
- `tracery_panel`
- `crest`
- `symbol_panel`
- `cornice`
- `canopy`
- `cushion`

Interaction:

- `loot_socket`
- `book_socket`
- `tool_slot`
- `crafting_socket`
- `sit_socket`
- `rest_socket`
- `dais_socket`

Damage and age:

- `missing_board`
- `broken_leg`
- `patch`
- `split`
- `char_mark`
- `waterline`
- `wear_lane`

## Drafting To Blender Translation

If the operator draws boards or slabs:

- use `rectangle_profile`, `extrude`, `primitive_cube_add`, or
  `mesh_from_pydata`

If the operator marks repeated supports:

- use `array_linear`, `modifier_array`, or `modifier_mirror`

If the operator marks panels:

- use `offset_profile`, `relief_stack`, `inset_faces`, `extrude_faces`, and
  `modifier_bevel`

If the operator marks hardware:

- use separate named solids, `modifier_array`, and material slots

If the operator marks damage:

- use `custom_polygon_profile`, `boolean_cut`, `bisect_mesh`, `split_separate`,
  and material roles for dark interiors or patched boards

## Manual Edit Focus

Check in this order:

1. Family silhouette
2. Caste/status read
3. Style anatomy
4. Interaction sockets
5. Material roles
6. Damage/wear variants
7. UV and texture pass

## Low-Compute Rule

Furniture has to read without decals. Use silhouette, material slots, bevels,
panel depth, sockets, and broad wear surfaces first. Decals can be a later
optional pass, not the source of the design.
