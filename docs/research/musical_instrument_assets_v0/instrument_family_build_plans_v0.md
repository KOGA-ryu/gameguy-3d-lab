# Instrument Family Build Plans V0

These are modeling plans, not instrument-making plans. Their job is to describe
which source fields and Blender tools are likely to produce readable game props.

## Lute

Craft logic:

- body is a hollow bowl plus a thin soundboard
- back ribs are repeated curved strips, not texture-only decoration
- rose is a cutout or relief object on the soundboard
- strings, bridge, neck, pegbox, and pegs must stay separate

Source fields:

- `body_outline_points`
- `bowl_depth_m`
- `rib_count`
- `soundboard_thickness_m`
- `rose_pattern_id`
- `neck_length_m`
- `pegbox_angle_deg`
- `string_count`

Blender direction:

- `mesh_from_pydata` for bowl/soundboard meshes
- `modifier_mirror` for symmetrical body construction
- `modifier_array` or indexed curves for ribs and strings
- `curve_bezier_add`, `curve_bevel_profile`, `curve_to_mesh` for strings
- `modifier_boolean` for rose cutouts
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`

Operator check:

- the body reads as a hollow ribbed object before any texture work

## Gothic Harp

Craft logic:

- harp is a frame, a soundbox, and a fan of strings
- neck curve and pillar determine silhouette
- tuning pins and strings are repeated small details

Source fields:

- `frame_height_m`
- `frame_width_m`
- `soundbox_taper_points`
- `neck_curve_points`
- `pillar_profile`
- `string_count`
- `pin_spacing_m`

Blender direction:

- `mesh_from_pydata` for soundbox and frame solids
- `curve_bezier_add`, `curve_bevel_profile`, `curve_to_mesh` for neck and strings
- `modifier_array` for pins and strings when regular spacing is acceptable
- `modifier_boolean` for pin sockets or soundholes
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`

Operator check:

- the string fan shows changing lengths and the frame stays editable

## Recorder

Craft logic:

- recorder is a bore-axis object
- tone holes are ordered cuts along the body
- mouthpiece window, windway, and labium are the main identity details
- joint bands give shape without overbuilding

Source fields:

- `body_length_m`
- `head_diameter_m`
- `foot_diameter_m`
- `tone_hole_positions_m`
- `tone_hole_radii_m`
- `windway_slot`
- `labium_angle_deg`
- `joint_band_positions_m`

Blender direction:

- `primitive_cylinder_add` or radial-stack mesh for the body
- `modifier_boolean` for tone holes, windway, and window
- `modifier_bevel` to soften hole rims and mouthpiece edges
- `modifier_weighted_normal` for clean shading
- `uv_cube_project`, `material_assign_by_part`, procedural material tools

Operator check:

- holes, windway, and labium remain visible at small prop scale

## Shawm

Craft logic:

- shawm is a conical bore with a flared bell
- reed and staple must be separate from the wooden body
- holes are cut into the taper, not randomly placed on a cylinder

Source fields:

- `body_length_m`
- `mouth_diameter_m`
- `bell_diameter_m`
- `flare_profile`
- `tone_hole_positions_m`
- `tone_hole_radii_m`
- `reed_length_m`
- `staple_length_m`

Blender direction:

- `primitive_cone_add` or radial-stack mesh for the conical body
- `section_stack` style rings for bell flare
- `modifier_boolean` for holes
- `primitive_cylinder_add` for staple
- `mesh_from_pydata` for simple reed blades
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`

Operator check:

- the flare, reed, and tone-hole order tell the user this is not a recorder

## Frame Drum

Craft logic:

- drum is a hoop plus stretched membrane
- tacks, lacing, or jingles explain tension around the rim
- optional small details must be disableable for lower-compute props

Source fields:

- `diameter_m`
- `hoop_depth_m`
- `rim_lip_radius_m`
- `membrane_inset_m`
- `anchor_count`
- `anchor_radius_m`
- `jingle_count`
- `beater_length_m`

Blender direction:

- `primitive_cylinder_add` or `primitive_torus_add` for hoop/rim
- `object_duplicate_radial` or `modifier_array` for tacks and jingles
- `curve_bezier_add`, `curve_bevel_profile` for lacing cords
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`
- `procedural_bump_map` for membrane grain after geometry reads

Operator check:

- the membrane reads as a separate stretched skin, not a painted cylinder cap

## Cast Bell

Craft logic:

- bell comes from a side profile revolved around a center axis
- shoulder, waist, soundbow, and lip need visible thickness changes
- clapper is a separate hanging striker

Source fields:

- `profile_rings`
- `height_m`
- `mouth_diameter_m`
- `wall_thickness_hint_m`
- `soundbow_radius_m`
- `lip_radius_m`
- `crown_profile`
- `clapper_length_m`

Blender direction:

- `modifier_screw` or radial-stack mesh from the side profile
- `primitive_torus_add` for raised lip/soundbow rings when needed
- `primitive_uv_sphere_add` for clapper mass
- `curve_bezier_add` for hanger or clapper line
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`

Operator check:

- the side profile clearly shows crown, shoulder, waist, soundbow, and lip

## Portative Organ

Craft logic:

- case and wind chest are boxes
- pipes are an ordered height series
- bellows are folded material, not a plain rectangle
- keys and pipe mouths explain the mechanical relationship

Source fields:

- `case_bounds_m`
- `pipe_count`
- `pipe_height_series_m`
- `pipe_diameter_series_m`
- `key_count`
- `bellows_fold_count`
- `wind_chest_bounds_m`
- `pipe_mouth_shape`

Blender direction:

- `primitive_cube_add` for case, wind chest, keys, and bellows folds
- `primitive_cylinder_add` or `primitive_cone_add` for pipes
- `modifier_array` for pipes and keys
- `modifier_boolean` for pipe mouths
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`

Operator check:

- pipes, keys, wind chest, and bellows stay selectable as separate parts

## Hurdy-Gurdy

Craft logic:

- body is a soundbox but the wheel and crank are the identity
- keybox, keys, tangents, bridges, melody strings, and drones must be separated
- wheel contact zone should be obvious even before animation

Source fields:

- `body_outline_points`
- `body_depth_m`
- `wheel_radius_m`
- `wheel_exposure_ratio`
- `crank_length_m`
- `key_count`
- `key_spacing_m`
- `melody_string_count`
- `drone_string_count`

Blender direction:

- `mesh_from_pydata` for body and keybox
- `primitive_cylinder_add` and `primitive_circle_add` for wheel/axle hints
- `curve_bezier_add`, `curve_bevel_profile`, `curve_to_mesh` for strings
- `modifier_array` for keys
- `modifier_boolean` for wheel pocket and keybox slots
- `modifier_bevel`, `modifier_weighted_normal`, `material_assign_by_part`

Operator check:

- the player can point to wheel, crank, keybox, drones, melody strings, and
  bridges as separate visual facts
