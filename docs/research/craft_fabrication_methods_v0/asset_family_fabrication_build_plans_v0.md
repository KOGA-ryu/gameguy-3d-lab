# Asset Family Fabrication Build Plans V0

These are not literal fabrication plans. They are craft-informed modeling plans:
what a real craft workflow suggests the repo should capture before Blender.

## Stone Railing Newel Or Post

Craft logic:

```text
square block
-> dressed faces
-> plinth/cap profile templates
-> face-panel layout
-> socket cuts
-> chiselled bevels, grooves, and tool finish
```

Real tools to understand:

- banker bench
- mallet
- point chisel
- claw chisel
- flat chisel
- straightedge/template

Repo source fields:

- `block_bounds_m`
- `face_roles`
- `plinth_profile`
- `cap_profile`
- `rail_socket_left/right`
- `face_panel_inset_m`
- `bevel_width_m`
- `groove_depth_m`

Blender direction:

```text
mesh_from_pydata
inset_faces
extrude_faces
modifier_boolean
modifier_bevel
modifier_weighted_normal
material_assign_by_part
create_collision_proxy
create_lod_variant
```

Operator checks:

- face reads as dressed stone before ornament
- sockets do not get hidden by decoration
- bevels preserve the panel and grooves

## Gothic Window Or Blind Tracery Panel

Craft logic:

```text
tracing geometry
-> selected lines
-> templates
-> stone bars and voids
-> cusps/foils
-> bevels and shadow arrises
```

Real tools to understand:

- tracing floor
- compass
- straightedge
- templates
- chisels and mallet

Repo source fields:

- `construction_graph`
- `selected_edges`
- `omitted_edges`
- `closed_cells`
- `bar_width_m`
- `cutter_depth_m`
- `cusp_radius_m`
- `bevel_width_m`

Blender direction:

```text
mesh_from_pydata
modifier_boolean
modifier_mirror
modifier_array
modifier_bevel
modifier_weighted_normal
```

Operator checks:

- every visible line comes from a selected construction line
- voids remain readable after beveling
- cusps and foils have consistent centers/radii

## Arch, Door Surround, Or Arcade Bay

Craft logic:

```text
springline/span/rise
-> centering
-> voussoir layout
-> keystone/crown
-> reveal/moulding profile
-> wall or pier socket
```

Real tools to understand:

- centering frame
- template
- level/plumb line
- mason's tools

Repo source fields:

- `span_m`
- `rise_m`
- `springline_z_m`
- `arch_thickness_m`
- `voussoir_count`
- `keystone_profile`
- `reveal_depth_m`

Blender direction:

```text
mesh_from_pydata
modifier_mirror
modifier_array
modifier_boolean
modifier_bevel
material_assign_by_part
```

Operator checks:

- springline is obvious
- arch reads as segmented stone or intentional carved band
- keystone/crown is not lost in trim

## Rib Vault Bay

Craft logic:

```text
bay grid
-> springing points
-> rib paths
-> bosses at intersections
-> web cells between ribs
-> surface finish
```

Real tools to understand:

- tracing floor
- compass/straightedge
- rib templates
- centering
- lifting/setting sequence

Repo source fields:

- `bay_bounds_m`
- `springing_points`
- `rib_paths`
- `rib_profile`
- `web_cells`
- `boss_points`
- `web_thickness_m`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
mesh_from_pydata
modifier_mirror
modifier_array
modifier_bevel
material_assign_by_part
```

Operator checks:

- ribs read before webbing
- web cells are separate from rib geometry
- bosses sit at actual intersections

## Wood Door Or Window Frame

Craft logic:

```text
stiles and rails
-> mortises and tenons
-> grooves/rebates
-> panel float/reveal
-> moulding profile
```

Real tools to understand:

- marking gauge
- try square
- saw
- mortise chisel
- shoulder/router plane
- clamps

Repo source fields:

- `stile_width_m`
- `rail_height_m`
- `mortise_size_m`
- `tenon_size_m`
- `panel_inset_m`
- `groove_depth_m`
- `reveal_width_m`

Blender direction:

```text
primitive_cube_add
mesh_from_pydata
modifier_boolean
inset_faces
extrude_faces
modifier_bevel
modifier_weighted_normal
```

Operator checks:

- stiles and rails are separate named parts
- panel reads as sitting inside the frame
- grooves and reveals are visible enough to survive texture simplification

## Wrought-Iron Railing, Gate, Or Grille

Craft logic:

```text
bar stock
-> heat/bend paths
-> scroll jigs
-> mirrored/repeated modules
-> collars/rivets/tenons
-> finish
```

Real tools to understand:

- forge
- anvil
- hammer
- tongs
- scroll jig
- bending fork
- rivet set

Repo source fields:

- `bar_path_points`
- `bar_radius_m`
- `bend_radius_m`
- `module_count`
- `join_points`
- `collar_positions`
- `rivet_radius_m`

Blender direction:

```text
curve_bezier_add
curve_bevel_profile
curve_to_mesh
modifier_mirror
modifier_array
primitive_cylinder_add
modifier_bevel
material_assign_by_part
```

Operator checks:

- scrolls read as bent bar, not flat wallpaper
- joins have collars/rivets where paths meet
- low LOD can remove rivets but keep bar rhythm

## Metal Relief Panel Or Hardware Plate

Craft logic:

```text
sheet outline
-> relief regions
-> broad raised forms
-> chased lines
-> bosses/punch marks
-> edge finishing
```

Real tools to understand:

- pitch bowl
- raising hammer
- chasing tools
- punches
- stakes

Repo source fields:

- `sheet_outline`
- `relief_regions`
- `depth_bands_m`
- `boss_centers`
- `chased_line_paths`
- `sheet_thickness_m`

Blender direction:

```text
mesh_from_pydata
inset_faces
extrude_faces
modifier_displace
modifier_bevel
modifier_weighted_normal
material_assign_by_part
```

Operator checks:

- broad relief reads without texture
- chased lines are separate from raised bosses
- low hardware can drop fine marks and keep main relief

