# Animal Family Build Plans V0

These build plans are not Blender scripts. They are planning records for future
source recipes, operator workcards, and Blender tool sequences.

## Domestic Companions

Starter assets: `village_dog_v0`, `barn_cat_v0`

Build order:

1. Draw side silhouette and front silhouette.
2. Block torso, head, legs, ears, and tail as separate named pieces.
3. Use `modifier_mirror` for left/right limbs and ears.
4. Use bevels and weighted normals for readable low-poly softness.
5. Assign material slots for fur, eye, nose, paw, and optional collar.
6. Capture static pose variants before animation work.

Key tools: `primitive_uv_sphere_add`, `primitive_ico_sphere_add`,
`mesh_from_pydata`, `curve_bezier_add`, `curve_bevel_profile`,
`modifier_mirror`, `modifier_lattice`, `modifier_bevel`,
`modifier_weighted_normal`.

## Equines, Mounts, And Pack Animals

Starter assets: `riding_horse_v0`, `pack_donkey_mule_v0`

Build order:

1. Loft the barrel torso from capsule/circle sections.
2. Add long neck and head as oriented capsule/custom polygon volumes.
3. Place four leg columns on a hoof grid.
4. Add mane/tail strips and long-ear or tack variants.
5. Reserve saddle, pack, bridle, yoke, or cargo sockets.
6. Create a collision proxy that follows the body and load bounds.

Key tools: `primitive_cylinder_add`, `primitive_uv_sphere_add`,
`mesh_from_pydata`, `curve_bezier_add`, `curve_bevel_profile`,
`modifier_mirror`, `modifier_lattice`, `modifier_bevel`,
`create_collision_proxy`.

## Livestock And Hoofed Farm Animals

Starter assets: `cattle_ox_v0`, `sheep_goat_small_ruminant_v0`,
`farm_pig_boar_v0`

Build order:

1. Start from the main body mass: heavy torso, fleece shell, or low swine oval.
2. Attach head shape and species marker: horn, snout, beard, fleece, or tusk.
3. Place hoof/leg supports under actual mass, not just at the corners.
4. Add optional work sockets: yoke, shearing state, pen gate, or butcher prop.
5. Use procedural noise/bump for fleece, bristle, mud, or rough hide.

Key tools: `primitive_uv_sphere_add`, `primitive_cylinder_add`,
`primitive_cone_add`, `primitive_torus_add`, `modifier_displace`,
`procedural_noise_texture`, `procedural_bump_map`, `modifier_mirror`,
`modifier_lattice`, `modifier_bevel`.

## Birds, Poultry, And Corvids

Starter assets: `chicken_flock_bird_v0`, `crow_raven_v0`

Build order:

1. Choose pose: ground bird, perched bird, or spread-wing emblem.
2. Block egg/wedge body, head, beak, wing, tail, and leg/perch pieces.
3. Use mirrored wing and tail construction where symmetry matters.
4. Keep beak direction readable at small size.
5. Create flock, cage, perch, statue, and banner material variants separately.

Key tools: `mesh_from_pydata`, `primitive_uv_sphere_add`,
`primitive_cone_add`, `modifier_mirror`, `modifier_solidify`,
`modifier_bevel`, `material_principled_shader`, `create_lod_variant`.

## Vermin And Nocturnal Animals

Starter assets: `rat_vermin_v0`, `cave_bat_v0`

Build order:

1. Use tiny body mass plus one dominant silhouette cue.
2. For rats, make the tail curve and pointed muzzle before surface detail.
3. For bats, make membrane span and finger ribs before body detail.
4. Build low-cost cluster/scatter variants early.
5. Mark density budget because these assets are often repeated.

Key tools: `curve_bezier_add`, `curve_polyline_add`, `curve_bevel_profile`,
`mesh_from_pydata`, `modifier_mirror`, `modifier_solidify`,
`modifier_bevel`, `create_lod_variant`.

## Wild Game And Predators

Starter assets: `deer_stag_hind_v0`, `gray_wolf_v0`, `snake_v0`

Build order:

1. Establish posture: alert prey, stalking predator, or coiled/striking curve.
2. Add species markers: antlers, long muzzle, fur ruff, head wedge, belly strip.
3. Use curve-based construction for antlers and snake bodies.
4. Create statue, trophy, pelt, or heraldic variants as separate material modes.
5. Keep combat-read silhouettes separate from decorative emblem silhouettes.

Key tools: `curve_bezier_add`, `curve_polyline_add`, `curve_bevel_profile`,
`curve_to_mesh`, `primitive_uv_sphere_add`, `primitive_cone_add`,
`mesh_from_pydata`, `modifier_lattice`, `modifier_mirror`,
`modifier_bevel`.

## Aquatic And Wetland Animals

Starter assets: `river_fish_v0`, `frog_toad_v0`

Build order:

1. Define waterline or ground-contact context first.
2. For fish, loft lens body, tail fork, and fin triangles.
3. For frogs/toads, block squat body, eyes, rear leg arcs, and webbed feet.
4. Use material slots and bump maps for wet read before decals.
5. Create market/pond/cistern variants separately.

Key tools: `primitive_uv_sphere_add`, `primitive_ico_sphere_add`,
`mesh_from_pydata`, `modifier_mirror`, `modifier_lattice`,
`modifier_bevel`, `procedural_bump_map`, `procedural_noise_texture`.
