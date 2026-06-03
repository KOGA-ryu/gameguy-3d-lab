# Railing 2D Detail Profiles v0

This slice makes the missing 2D detail step explicit before generating more railing geometry.

## Source Path

```text
reference image detail language
-> 2D shape profile
-> placement region + detail role + application method
-> staged Blender tool sequence
-> future compiled guard/post/rail tool plan
```

## Shapes

```text
rectangle/square -> rail cores, panel frames, plinths, cap blocks
pointed_arch_profile -> gothic panel cutouts and post-face recesses
capsule -> vertical slots, flutes, and long rail shadow grooves
circle -> bead strips and ring bands
custom_polygon -> ogee/cyma molding side profiles
trapezoid -> square-to-shaft transition collars
custom_polygon/circle -> lobed compound post cross-sections
```

## Placement Contract

Every detail profile now declares:

```text
target_asset_family
placement_region
detail_role
application_method
geometry terms
profile terms
operations
Blender tool sequence
shape controls
```

That prevents the Blender adapter from inventing where details belong. The source says whether a 2D shape becomes a raised frame, recessed cut, repeated bead, side molding, transition collar, or lobed shaft.

## Tool Sequence

The canonical sequence is:

```text
base_form:
  primitive_cube_add
  mesh_from_pydata
  modifier_screw

assembly:
  modifier_boolean
  modifier_array
  object_duplicate_radial
  modifier_mirror
  join_objects

shape_refinement:
  modifier_bevel
  mark_sharp
  shade_smooth
  modifier_weighted_normal

sculpt_detail:
  modifier_displace

uv_mapping:
  uv_smart_project
  uv_pack_islands

material_texture:
  material_assign_by_part
  procedural_noise_texture
  procedural_bump_map

validation_export:
  calculate_bounds
  validate_non_manifold
  create_collision_proxy
  create_lod_variant
  render_workbench_preview
  export_gltf
```

## Current Evidence

```text
PASS railing detail profile validation: profiles=7 placements=21 sequence=8 tools=13
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=12 reference_only=3
PASS generation pipeline validation: commands=31 json=234 include_blender=false
PASS generation pipeline validation: commands=45 json=234 include_blender=true
```

## Boundary

This does not yet generate the detailed railing. It defines the missing source language and tool sequence so the next slice can compile a post-rail-post or guard-panel tool plan from 2D shapes without guessing.
