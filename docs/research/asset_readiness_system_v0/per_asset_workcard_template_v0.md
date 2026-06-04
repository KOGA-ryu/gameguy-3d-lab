# Per-Asset Workcard Template V0

Copy this structure into a new asset note before building one asset.

```text
asset_id:
family:
component:
style:
version:
status:

goal:

primary_reference:
secondary_references:
use_policy:

visible_anatomy:

shape_language:

ignored_for_first_pass:

drawing_guide:
  master_grid:
  axes:
  primary_shapes:
  selected_lines:
  omitted_lines:
  profiles:
  cutters:
  ribs:
  panels:
  sockets:

scale:
  dimensions_m:
  origin:
  pivot:
  bounds:
  grid_snap_m:

connectors:

material_roles:

collision:

lod_plan:

hardware_policy:

blender_tool_sequence:
  base_form:
  assembly:
  shape_refinement:
  sculpt_detail:
  retopo_cleanup:
  uv_mapping:
  material_texture:
  validation_export:

operator_notes:

qa_result:

corrections_to_promote:
```

## Example: Railing Post Start

```text
asset_id: railing.newel_post.gothic_blind_tracery.clean_v0
family: railings
component: newel_post
style: gothic blind tracery
version: v0
status: reference-ready

goal:
  Create one modular post with plinth, shaft, cap, side sockets, and one
  readable blind-tracery face panel.

visible_anatomy:
  plinth, base collar, shaft, face panel, raised lip, tracery recess,
  rail_socket_left, rail_socket_right, cap, bevelled corners

shape_language:
  square footprint, inset rectangular field, pointed arch cut, raised border,
  small bead/lip bands, chamfered corners

blender_tool_sequence:
  base_form:
    primitive_cube_add, mesh_from_pydata
  assembly:
    modifier_mirror, modifier_boolean
  shape_refinement:
    inset_faces, modifier_bevel, modifier_weighted_normal
  uv_mapping:
    uv_cube_project, uv_pack_islands
  material_texture:
    material_assign_by_part, procedural_noise_texture, procedural_bump_map
  validation_export:
    origin_set, calculate_bounds, create_collision_proxy, create_lod_variant,
    render_workbench_preview
```

