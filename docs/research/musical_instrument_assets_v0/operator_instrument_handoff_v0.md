# Operator Instrument Handoff V0

This is the handoff format for a future drawing UI or manual Blender pass. The
goal is to let the operator rough the object quickly, then hand Codex enough
structured facts to choose legal geometry terms and Blender tools.

## Minimum Workcard

```yaml
instrument_id:
reference_packet_id:
asset_role:
scale_reference:
visible_anatomy:
  - part_id:
    visible: true
    priority: primary
source_fields:
  body_outline_points:
  profile_rings:
  string_count:
  hole_positions_m:
  repeated_detail_count:
geometry_terms:
blender_tool_ids:
material_roles:
manual_edit_notes:
operator_checks:
```

## UI Tags To Support

Body and shell:

- `body_outline`
- `bowl_depth`
- `soundbox`
- `case_frame`
- `bell_profile`
- `hollow_cavity`

Strings and repeated lines:

- `string_course`
- `string_fan`
- `melody_string`
- `drone_string`
- `bridge`
- `tuning_pin`

Wind and holes:

- `bore_axis`
- `conical_bore`
- `tone_hole`
- `hole_order`
- `windway`
- `labium`
- `flared_bell`

Percussion and metal:

- `hoop`
- `skin_head`
- `rim_lip`
- `lacing`
- `soundbow`
- `lip`
- `clapper`

Mechanical parts:

- `bellows`
- `wind_chest`
- `pipe_array`
- `key_array`
- `wheel`
- `crank`
- `tangent`

## Drafting To Blender Translation

If the operator draws a side profile:

- use `radial_stack`, `section_stack`, `loft_sections`, or `modifier_screw`
- likely assets: bells, drums, pipes, recorder bodies, shawm bodies

If the operator draws a top outline:

- use `custom_polygon_profile`, `rounded_rectangle_profile`, `extrude`, and
  `loft_sections`
- likely assets: lute bodies, hurdy-gurdy bodies, organ cases, harp soundboxes

If the operator marks repeated points:

- use `array_linear`, `array_radial`, `object_duplicate_radial`, or
  `modifier_array`
- likely details: strings, tacks, pins, keys, pipes, ribs

If the operator marks holes:

- use `boolean_cut`
- likely details: recorder tone holes, shawm tone holes, pipe mouths, lute rose,
  keybox slots

If the operator marks shallow lips:

- use `offset_profile`, `relief_stack`, `bevel_edges`, `modifier_bevel`, and
  `modifier_weighted_normal`
- likely details: bell lips, drum rims, recorder joint bands, soundbox edges

## Manual Edit Focus

The first manual Blender pass should check:

- silhouette before ornament
- repeated detail count before material work
- holes and cutouts before bevels
- material slots before UVs
- low-poly editability before polish

## What Not To Do Yet

- do not promise playable instruments
- do not tune real strings, pipes, or holes
- do not generate unique carved ornament from a museum object
- do not bake textures until material roles and UV strategy are named
- do not make decals mandatory; lower-compute hardware must still read the prop
