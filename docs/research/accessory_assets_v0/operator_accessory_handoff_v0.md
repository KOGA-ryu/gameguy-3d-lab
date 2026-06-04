# Operator Accessory Handoff V0

This is the future UI/manual workcard shape for accessories. Accessories are
small, so their source fields must be blunt and explicit: attachment, front face,
socket ids, and material roles matter more than tiny sculpt detail.

## Minimum Workcard

```yaml
accessory_id:
family_id:
status_tier_ids:
style_ids:
reference_packet_id:
asset_role:
scale_reference:
attachment_mechanics:
visible_anatomy:
  - part_id:
    visible: true
    priority: primary
source_fields:
  bounds_m:
  front_face:
  strap_path:
  loop_profile:
  socket_ids:
  symbol_panel_id:
geometry_terms:
blender_tool_ids:
material_roles:
manual_edit_notes:
operator_checks:
```

## UI Tags To Support

Strap and leather:

- `strap`
- `flap`
- `stitch_line`
- `seam`
- `patch`
- `gusset`
- `cord_loop`

Metal hardware:

- `buckle_frame`
- `tongue`
- `keeper_loop`
- `ring`
- `hook`
- `rivet`
- `strap_plate`

Jewelry:

- `ring_band`
- `seal_face`
- `gem_socket`
- `chain_loop`
- `symbol_face`
- `pin`
- `terminal`

Keys and seals:

- `key_ring`
- `bow`
- `shank`
- `bit`
- `ward_cut`
- `stamp_face`
- `wax_socket`

Containers:

- `bag_body`
- `soft_body`
- `neck`
- `stopper`
- `case_body`
- `content_socket`
- `liquid_state`

Weapon and utility suspension:

- `scabbard_body`
- `throat`
- `chape`
- `hanger_strap`
- `belt_hook`
- `tool_socket`
- `socket_tree`

## Drafting To Blender Translation

If the operator draws a strap:

- use `rectangle_profile`, `capsule_profile`, `curve_bezier_add`,
  `curve_bevel_profile`, `modifier_bevel`

If the operator draws a loop/ring:

- use `circle_profile`, `radial_stack`, `primitive_torus_add`, or
  `primitive_cylinder_add`

If the operator marks holes/cuts:

- use `boolean_cut`, `modifier_boolean`, and dark material roles

If the operator marks a front symbol:

- use `relief_stack`, `socket`, `material_assign_by_part`
- keep the symbol id in source data

If the operator marks damage:

- use `custom_polygon_profile`, `boolean_cut`, `bisect_mesh`, `split_separate`,
  and material roles for dark interiors or corroded metal

## Manual Edit Focus

Check in this order:

1. Attachment mechanic
2. Family silhouette
3. Status read
4. Front-facing detail
5. Gameplay sockets
6. Material roles
7. Damage/wear variants
8. UV and texture pass

## Low-Compute Rule

Accessories are tiny. They must read through silhouette, material slots, sockets,
and a few bold parts. Decals and microscopic engravings are optional; they are
not allowed to carry the design.
