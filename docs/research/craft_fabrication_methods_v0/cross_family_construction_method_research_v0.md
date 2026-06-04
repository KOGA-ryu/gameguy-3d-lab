# Cross-Family Construction Method Research V0

This document maps real construction and craft methods into future game-asset
planning. It is not a shop manual and not preservation/conservation advice.

The useful translation is:

```text
real craft sequence -> visible construction logic -> source fields
-> Blender tool sequence -> operator checks
```

## Buildings And Architecture

### Traditional Masonry Wall

Real method logic:

```text
stone/brick units
-> bedding mortar
-> courses or rubble arrangement
-> joints/pointing
-> openings and structural breaks
-> weathering and repair marks
```

Visible asset cues:

- individual block or brick courses
- mortar joint rhythm
- bond pattern or irregular rubble logic
- corner quoins or heavier edge stones
- lintels, arches, or relieving features over openings
- patches where repair work interrupts the original wall

Source fields:

- `unit_pattern`
- `course_height_m`
- `joint_width_m`
- `bond_type`
- `corner_quoin_policy`
- `opening_support_type`
- `repair_patch_regions`
- `mortar_material_role`

Blender direction:

```text
mesh_from_pydata
array_linear
inset_faces
modifier_bevel
material_assign_by_part
procedural_noise_texture
procedural_bump_map
```

Operator checks:

- the wall reads as built from units, not one flat slab
- openings have visible support logic
- mortar and stone/brick have distinct material roles
- damage/repair follows joints or edges instead of random noise

### Lime Mortar, Repointing, And Breathable Masonry Read

Real method logic:

```text
existing joints
-> remove failed mortar carefully
-> match compatible mortar color/texture/depth
-> compact new mortar into joints
-> finish joint profile
```

Visible asset cues:

- mortar sits between masonry units
- joint profile changes shadow and age read
- patched areas can have different color or crispness
- incompatible hard repair can be shown as cracked adjacent stone/brick

Source fields:

- `joint_profile`
- `joint_depth_m`
- `mortar_color_variation`
- `repair_patch_age`
- `failed_joint_regions`
- `salt_or_water_stain_policy`

Blender direction:

```text
inset_faces
extrude_faces
material_assign_by_part
procedural_noise_texture
procedural_bump_map
modifier_bevel
```

Operator checks:

- mortar does not overpower the masonry unit silhouette
- repointed patches are localized
- moisture or salt marks follow plausible wall paths

### Timber-Framed Building

Real method logic:

```text
primary posts/sills/plates
-> braces and tie beams
-> pegged or shouldered joints
-> infill panels
-> plaster/wattle/brick/stone fill
-> weathering and repair
```

Visible asset cues:

- heavy timber grid
- diagonal braces
- peg marks
- infill panels set between beams
- frame direction and bay rhythm
- slight unevenness and repair scarfing

Source fields:

- `frame_bay_width_m`
- `post_section_m`
- `brace_angle`
- `peg_radius_m`
- `infill_material`
- `joint_marker_policy`
- `sag_or_warp_amount`

Blender direction:

```text
primitive_cube_add
mesh_from_pydata
modifier_array
modifier_mirror
modifier_bevel
material_assign_by_part
create_collision_proxy
```

Operator checks:

- the frame reads before plaster or infill detail
- braces connect logically to posts/rails
- panels are subordinate to the timber skeleton

### Roofs: Thatch, Slate, Tile, And Lead/Metal Detail

Real method logic:

```text
roof structure
-> battens/laths or support layer
-> roofing material courses
-> ridge/hip/verge details
-> flashing and drainage
-> maintenance/weathering
```

Visible asset cues:

- thatch has thick soft edges and ridge bundles
- slate/stone slate has overlapping courses
- tile has repeated ridges and shadows
- lead/metal flashing appears at junctions
- gutters and downspouts explain water paths

Source fields:

- `roof_pitch`
- `course_overlap_m`
- `ridge_detail_type`
- `thatch_edge_thickness_m`
- `slate_unit_variation`
- `flashing_regions`
- `drainage_path`
- `moss_growth_policy`

Blender direction:

```text
mesh_from_pydata
array_linear
modifier_solidify
modifier_bevel
modifier_displace
procedural_noise_texture
material_assign_by_part
create_lod_variant
```

Operator checks:

- roof reads as layered, not painted flat
- ridge and verge details are visible
- water wear follows roof edges and drainage
- low-compute version keeps silhouette and material bands

### Plaster, Stucco, And Render

Real method logic:

```text
base wall or lath
-> scratch/base coat
-> build-up coat
-> finish coat
-> ruled/incised/scored surface or painted finish
-> cracks and repair patches
```

Visible asset cues:

- surface sits over structural support
- cracks follow stress, openings, and edges
- patches have changed texture or color
- scored lines can imitate blocks or decorative panels

Source fields:

- `substrate_type`
- `coat_thickness_m`
- `finish_texture`
- `score_pattern`
- `crack_path_policy`
- `patch_regions`
- `limewash_or_paint_layer`

Blender direction:

```text
modifier_solidify
modifier_displace
procedural_noise_texture
procedural_bump_map
inset_faces
material_assign_by_part
```

Operator checks:

- plaster/render does not erase wall structure where it should remain visible
- cracks and patches are purposeful
- low-compute version uses material masks instead of dense geometry

## Furniture

### Frame-And-Panel Furniture

Real method logic:

```text
stiles and rails
-> mortise and tenon joints
-> grooves/rebates
-> floating or raised panel
-> moulded edges
-> finish and wear
```

Visible asset cues:

- separate vertical stiles and horizontal rails
- panels sit inside the frame
- reveals and shadow gaps around panels
- pegged or shouldered joints on heavy furniture
- worn handles and polished contact surfaces

Source fields:

- `stile_width_m`
- `rail_height_m`
- `panel_inset_m`
- `groove_depth_m`
- `tenon_marker_policy`
- `moulding_profile`
- `contact_wear_regions`

Blender direction:

```text
primitive_cube_add
mesh_from_pydata
inset_faces
extrude_faces
modifier_boolean
modifier_bevel
modifier_weighted_normal
material_assign_by_part
```

Operator checks:

- panels read as captured by the frame
- mouldings do not hide the construction joints
- wear appears where hands, bodies, and objects touch

### Carved Furniture And Sculpture-Like Woodwork

Real method logic:

```text
stock or block selection
-> rough axe/saw shape
-> chisel/gouge carving
-> undercut/detail carving
-> smoothing
-> paint/gilding/finish
```

Visible asset cues:

- main volume stays coherent under carving
- leaves, scrolls, feet, and volutes attach to structural rails or posts
- tool marks can remain in lower-status or rough objects
- high-status pieces get gilding, polish, or painted detail

Source fields:

- `carving_depth_m`
- `relief_layer_count`
- `undercut_policy`
- `tool_mark_strength`
- `ornament_anchor_parts`
- `finish_material`

Blender direction:

```text
mesh_from_pydata
inset_faces
extrude_faces
sculpt_draw
sculpt_crease
sculpt_scrape
modifier_bevel
procedural_bump_map
material_assign_by_part
```

Operator checks:

- ornament grows from a named support, not from nowhere
- relief depth is readable before texture
- low-compute version can collapse carving to raised/recessed fields

### Bentwood And Curved Furniture

Real method logic:

```text
wood strip or solid piece
-> steam/heat or laminate
-> bend around form
-> clamp and dry/set
-> assemble repeated curves
```

Visible asset cues:

- continuous curves rather than carved-from-block curves
- repeated chair backs, legs, or rails share one bend radius
- joints and fasteners appear where curves attach to frame

Source fields:

- `bend_radius_m`
- `curve_path`
- `section_profile`
- `bend_repeat_count`
- `joint_socket_locations`
- `fastener_policy`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
curve_to_mesh
modifier_mirror
modifier_array
modifier_bevel
material_assign_by_part
```

Operator checks:

- curved parts have consistent radius families
- attachments are visible
- the object reads as bent members, not melted geometry

### Veneer, Marquetry, Inlay, And Surface Decoration

Real method logic:

```text
substrate panel
-> thin veneer/inlay pieces
-> cut pattern
-> lay and glue pieces
-> scrape/finish
-> polish or lacquer
```

Visible asset cues:

- decoration follows flat panels or curved but controlled surfaces
- pattern seams are thin and surface-bound
- high-status furniture gets different woods/metals/shells as material regions

Source fields:

- `substrate_part`
- `inlay_pattern`
- `veneer_materials`
- `seam_width_m`
- `surface_decoration_depth_m`
- `finish_gloss`

Blender direction:

```text
material_assign_by_part
procedural_noise_texture
uv_unwrap
uv_pack_islands
inset_faces
extrude_faces
modifier_bevel
```

Operator checks:

- inlay remains surface decoration unless intentionally raised
- material contrast is enough without decals on lower compute hardware
- pattern aligns with panel borders

### Upholstery And Soft Furnishings

Real method logic:

```text
frame
-> webbing/support
-> padding/stuffing
-> cover textile or leather
-> tacks/trim/fringe
-> wear and sag
```

Visible asset cues:

- cushion sits on a hard frame
- fabric pulls toward seams and tack lines
- soft parts sag or bulge differently from wood
- trim/tacks/fringe mark attachment

Source fields:

- `frame_part`
- `cushion_thickness_m`
- `seam_paths`
- `tack_spacing_m`
- `fabric_pattern`
- `sag_amount`
- `wear_contact_regions`

Blender direction:

```text
primitive_cube_add
modifier_bevel
modifier_lattice
modifier_displace
procedural_noise_texture
material_assign_by_part
curve_bezier_add
curve_bevel_profile
```

Operator checks:

- fabric reads separate from wood/metal
- seams/tacks explain the soft shape
- low-compute version keeps cushion silhouette and material contrast

## Musical Instruments

### Lute, Oud, Guitar-Like Plucked String Instruments

Real method logic:

```text
bowl or body ribs
-> soundboard
-> rosette/sound hole
-> neck and pegbox
-> bridge
-> strings and frets
-> decorative inlay
```

Visible asset cues:

- bowl back is ribbed or segmented
- soundboard is a distinct thin face
- rosette is a pierced or drawn pattern
- strings run bridge-to-pegbox
- pegbox angle and tuning pegs define the silhouette

Source fields:

- `body_outline`
- `rib_count`
- `soundboard_thickness_m`
- `rosette_pattern`
- `neck_length_m`
- `pegbox_angle`
- `course_count`
- `string_paths`

Blender direction:

```text
loft_sections
mesh_from_pydata
curve_bezier_add
curve_bevel_profile
modifier_mirror
modifier_array
modifier_boolean
modifier_bevel
material_assign_by_part
```

Operator checks:

- strings are anchored to bridge and pegbox
- rosette is centered and readable
- body reads hollow/light rather than a solid club

### Harp And Lyre-Like Frame Instruments

Real method logic:

```text
soundbox
-> neck/arm
-> pillar or frame
-> string row
-> tuning pins
-> carved or painted detail
```

Visible asset cues:

- frame makes a tension triangle/curve
- strings are parallel or fan according to frame
- soundbox is thicker than the strings and frame trim
- tuning pins mark the upper string anchors

Source fields:

- `frame_curve`
- `soundbox_profile`
- `string_count`
- `string_anchor_points`
- `tuning_pin_spacing`
- `pillar_section_profile`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
mesh_from_pydata
modifier_array
modifier_mirror
modifier_bevel
material_assign_by_part
```

Operator checks:

- string path logic is clear
- frame is strong enough visually to hold strings
- low-compute version reduces strings but keeps anchor rhythm

### Drums And Membranophones

Real method logic:

```text
shell/body
-> membrane/head
-> rim or hoop
-> lacing/tension cords/pegs
-> strap or stand
-> struck surface wear
```

Visible asset cues:

- drum shell and membrane are separate material regions
- tension system explains the head
- rim/hoop catches the edge
- worn center shows use

Source fields:

- `shell_profile`
- `head_diameter_m`
- `rim_profile`
- `tension_cord_count`
- `lacing_path`
- `strap_socket`
- `strike_wear_region`

Blender direction:

```text
radial_stack
primitive_cylinder_add
primitive_torus_add
curve_bezier_add
curve_bevel_profile
modifier_array
modifier_mirror
material_assign_by_part
procedural_bump_map
```

Operator checks:

- membrane reads thin and taut
- lacing connects rim to rim or rim to body
- shell shape controls instrument family read

### Wind Instruments

Real method logic:

```text
tube or bore
-> mouthpiece/reed
-> finger holes or keys
-> bell or flared end
-> binding/rings
-> material finish
```

Visible asset cues:

- bore axis is straight or intentionally curved
- finger holes follow usable spacing
- bell flare is readable
- mouthpiece/reed end differs from bell end

Source fields:

- `bore_path`
- `tube_radius_m`
- `finger_hole_positions`
- `bell_flare_profile`
- `mouthpiece_profile`
- `ring_band_positions`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
curve_to_mesh
modifier_boolean
primitive_torus_add
modifier_array
modifier_bevel
material_assign_by_part
```

Operator checks:

- holes are not random decoration
- mouthpiece and bell ends are visually distinct
- low-compute version keeps tube, holes, and flare

### Bells And Cast Metal Instruments

Real method logic:

```text
core/mold
-> cast bell form
-> lip and waist profile
-> crown/loop
-> clapper or striker
-> tuning/finish/patina
```

Visible asset cues:

- bell has a clear side profile
- lip is thicker/heavier
- crown/loop explains hanging
- clapper or striker is visible when needed
- patina/wear reinforces metal

Source fields:

- `bell_side_profile`
- `mouth_diameter_m`
- `wall_thickness_m`
- `crown_loop_profile`
- `clapper_socket`
- `patina_policy`

Blender direction:

```text
radial_stack
mesh_from_pydata
primitive_torus_add
modifier_solidify
modifier_bevel
material_principled_shader
procedural_noise_texture
material_assign_by_part
```

Operator checks:

- side profile reads as bell, not cup
- hanging loop/socket is named
- metal material has edge wear/patina, not flat yellow/gray

## Metalwork, Weapons, Accessories, And Hardware

### Forged Ironwork

Real method logic:

```text
bar stock
-> heat
-> taper/flatten/upset
-> bend or twist
-> punch/drift holes
-> rivet/collar/strap assembly
-> finish
```

Visible asset cues:

- scrolls and bars keep constant or intentionally tapered section
- joins use collars, rivets, wraps, or weld-like overlaps
- hammer marks and twist direction can explain handmade metal

Source fields:

- `bar_section_profile`
- `bend_paths`
- `taper_regions`
- `twist_angle`
- `rivet_positions`
- `collar_positions`
- `forge_scale_material`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
curve_to_mesh
modifier_simple_deform
primitive_cylinder_add
primitive_torus_add
modifier_bevel
material_assign_by_part
```

Operator checks:

- iron bars look bent/assembled, not extruded flat ornament
- rivets/collars explain joints
- repeated scrolls share a source curve

### Cast, Chased, Engraved, And Soldered Metal

Real method logic:

```text
model or mold
-> cast/base form
-> chase/engrave/incise details
-> solder or mechanically join smaller pieces
-> polish/patina
```

Visible asset cues:

- cast body can hold smoother complex mass
- chased/engraved lines sit on surface
- soldered or riveted additions have seams
- patina collects in recesses

Source fields:

- `base_cast_profile`
- `engraved_linework`
- `relief_depth_m`
- `join_type`
- `solder_seam_regions`
- `patina_recess_strength`

Blender direction:

```text
mesh_from_pydata
modifier_bevel
inset_faces
extrude_faces
curve_bezier_add
curve_bevel_profile
procedural_noise_texture
material_assign_by_part
```

Operator checks:

- engraved detail remains surface-bound
- added pieces have visible seams or fasteners
- patina emphasizes recesses, not every surface equally

## Ceramics, Food Containers, And Small Props

### Thrown Or Wheel-Like Vessels

Real method logic:

```text
clay body
-> centered rotational form
-> pulled wall/profile
-> trimmed foot
-> handle/spout attachments
-> firing
-> glaze or painted surface
```

Visible asset cues:

- vessel body is rotational or nearly rotational
- foot ring, lip, belly, neck, and handle are distinct
- glaze pools or color changes near edges/recesses

Source fields:

- `side_profile`
- `foot_ring_profile`
- `rim_profile`
- `handle_curve`
- `spout_profile`
- `glaze_material`
- `firing_color_variation`

Blender direction:

```text
radial_stack
mesh_from_pydata
curve_bezier_add
curve_bevel_profile
modifier_solidify
modifier_bevel
material_principled_shader
procedural_noise_texture
```

Operator checks:

- vessel reads hollow/thin
- rim and foot ring are visible
- handle/spout attachments have believable seams or pads

### Molded, Pressed, Pierced, And Decorated Ceramic

Real method logic:

```text
clay slab or mold
-> press or model relief
-> pierce/cut openings
-> assemble parts
-> fire
-> glaze/paint/lustre
```

Visible asset cues:

- relief and pierced openings come from repeated patterns
- tile designs sit in a moulded field
- assembled parts have seams or joins
- glaze emphasizes relief depth

Source fields:

- `mold_pattern`
- `relief_depth_m`
- `pierced_openings`
- `tile_repeat_unit`
- `glaze_pooling_policy`
- `painted_decoration_regions`

Blender direction:

```text
mesh_from_pydata
inset_faces
extrude_faces
modifier_boolean
modifier_array
modifier_bevel
material_assign_by_part
procedural_bump_map
```

Operator checks:

- relief depth is readable before material
- repeated tiles align
- low-compute version can use material/normal detail

## Textiles, Clothing, Banners, And Soft Props

### Woven Cloth And Tapestry

Real method logic:

```text
warp threads
-> weft threads
-> loom tension
-> discontinuous color areas or repeated weave
-> edge finishing
-> hanging or upholstery use
```

Visible asset cues:

- warp/weft direction informs fabric texture
- tapestry imagery is woven into surface, not painted-on randomly
- hanging textiles sag and have top attachment
- worn/faded side can differ from protected side

Source fields:

- `warp_direction`
- `weft_pattern`
- `fabric_weight`
- `hanging_points`
- `edge_finish_type`
- `woven_image_regions`
- `fade_policy`

Blender direction:

```text
primitive_plane_add
modifier_solidify
modifier_lattice
modifier_displace
uv_unwrap
procedural_noise_texture
material_assign_by_part
```

Operator checks:

- cloth has thickness and attachment logic
- weave direction aligns with object use
- hanging textile does not look like rigid stone

### Embroidery, Couching, And Applique

Real method logic:

```text
draw or transfer design
-> stitch outlines
-> fill areas
-> couch metal or raised threads
-> finish edges
```

Visible asset cues:

- stitched lines follow a transferred design
- raised thread/couching sits above cloth
- applique pieces have border seams
- high-status textiles use metallic or high-contrast thread

Source fields:

- `transfer_pattern`
- `stitch_line_paths`
- `fill_regions`
- `couched_thread_paths`
- `thread_materials`
- `raised_thread_height_m`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
material_assign_by_part
uv_unwrap
procedural_bump_map
modifier_solidify
```

Operator checks:

- embroidery follows designed paths
- thread sits on cloth instead of becoming a decal-only smear
- low-compute version uses material/bump paths

## Leather, Straps, Belts, Pouches, And Cases

### Cut, Folded, Stitched, And Riveted Leather Goods

Real method logic:

```text
pattern pieces
-> cut leather
-> fold or wet-form
-> stitch/rivet/strap
-> add buckle or clasp
-> oil/wear/polish
```

Visible asset cues:

- seams show how flat pieces became a volume
- folds and gussets explain capacity
- straps, buckles, rivets, and holes are named parts
- wear appears at bends, holes, and hand-contact areas

Source fields:

- `flat_pattern_pieces`
- `fold_lines`
- `seam_paths`
- `rivet_positions`
- `buckle_socket`
- `strap_width_m`
- `edge_wear_regions`

Blender direction:

```text
mesh_from_pydata
modifier_solidify
curve_bezier_add
curve_bevel_profile
primitive_torus_add
primitive_cube_add
modifier_bevel
material_assign_by_part
```

Operator checks:

- pouch/case has seam logic
- straps connect to hardware
- leather wear follows folds and holes

## Plants, Natural Props, And Terrain Materials

### Wattle, Basketry, Rope, And Woven Natural Forms

Real method logic:

```text
stakes or warp elements
-> woven weft rods/fibers
-> edge binding
-> handle/rim
-> wear and broken strands
```

Visible asset cues:

- over-under rhythm
- rim binding
- broken or protruding strands
- handles attach to structural stakes

Source fields:

- `stake_count`
- `weave_path`
- `weft_spacing_m`
- `rim_binding_profile`
- `handle_curve`
- `broken_strand_policy`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
modifier_array
modifier_mirror
mesh_from_pydata
material_assign_by_part
create_lod_variant
```

Operator checks:

- weave rhythm is readable at intended distance
- rim/handle explain the object
- low-compute version collapses weave into material bands

## Method Families To Promote Later

High-value future method records:

- `traditional_roof_layering_v0`
- `timber_frame_bay_joinery_v0`
- `frame_panel_furniture_joinery_v0`
- `bentwood_curve_forming_v0`
- `veneered_marquetry_surface_v0`
- `upholstery_frame_padding_cover_v0`
- `lute_ribbed_bowl_soundboard_v0`
- `drum_shell_membrane_tension_v0`
- `wind_instrument_bore_hole_bell_v0`
- `ceramic_vessel_profile_throwing_v0`
- `woven_textile_warp_weft_v0`
- `leather_pattern_fold_stitch_v0`

These should become machine-readable only when we start promoting source
recipes or tool-plan policies for those families.
