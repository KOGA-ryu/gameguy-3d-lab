# Operator Food And Drink Handoff V0

Food/drink props are small, repeated, and state-heavy. The workcard should focus
on source state, serving socket, contents id, material roles, and low-compute
readability.

## Minimum Workcard

```yaml
food_drink_id:
family_id:
status_tier_ids:
style_ids:
reference_packet_id:
asset_role:
scale_reference:
serving_mechanics:
visible_anatomy:
  - part_id:
    visible: true
    priority: primary
source_fields:
  bounds_m:
  portion_state:
  freshness_state:
  fill_ratio:
  contents_id:
  serving_socket:
  spill_socket:
geometry_terms:
blender_tool_ids:
material_roles:
manual_edit_notes:
operator_checks:
```

## UI Tags To Support

Bread and grain:

- `loaf_body`
- `crust_score`
- `flatbread`
- `crumb_edge`
- `grain_sack`
- `tied_mouth`

Produce:

- `fruit_body`
- `stem`
- `dimple`
- `root_taper`
- `bundle_tie`
- `mold_spot`

Dairy/meat/fish:

- `cheese_wedge`
- `rind`
- `cut_face`
- `meat_mass`
- `bone_hint`
- `fish_spine`

Drink and vessels:

- `bowl_profile`
- `rim_lip`
- `jug_body`
- `handle`
- `spout`
- `glass_body`
- `liquid_line`

Storage and table:

- `label`
- `seal`
- `stopper`
- `plate`
- `trencher`
- `food_socket`
- `shelf_socket`

State:

- `portion_state`
- `freshness_state`
- `serving_state`
- `fill_state`
- `contents_id`
- `spoilage_state`
- `broken_state`

## Drafting To Blender Translation

If the operator draws a food blob:

- use `custom_polygon_profile`, `rounded_rectangle_profile`,
  `primitive_uv_sphere_add`, `mesh_from_pydata`, and broad bevel/displace

If the operator draws a vessel profile:

- use `radial_stack`, `section_stack`, `modifier_screw`, rim lips, and material
  roles

If the operator marks fill/contents:

- add a separate liquid or contents part and store `contents_id` or `fill_ratio`
  in source data

If the operator marks cut/spoilage:

- use shallow booleans or material roles; keep the original silhouette readable

If the operator marks service placement:

- create `serving_socket`, `food_socket`, `shelf_socket`, or `spill_socket`

## Manual Edit Focus

Check in this order:

1. Item silhouette
2. Serving/storage state
3. Contents/fill state
4. Socket placement
5. Material roles
6. Optional garnish/spoilage details
7. UV and texture pass

## Low-Compute Rule

Food and drink assets are repeated scene clutter. They must read through broad
shape, material roles, and state fields. Decals, crumbs, foam, steam, labels,
and mold spots are optional detail, not the design foundation.
