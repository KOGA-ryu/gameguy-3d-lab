# Animal Role And Body-Plan System V0

The taxonomy separates role from body plan.

Role answers:

```text
what does the asset mean in the world?
```

Body plan answers:

```text
what shape/locomotion grammar will the asset use?
```

This avoids flattening everything into one vague `animal` bucket. A horse, ox,
deer, and goat all share hoofed cues, but they do different work in the game.
A dog and wolf share canine construction, but the posture, material, and lore
read are different.

## Role Tiers

| Role Tier | Meaning |
| --- | --- |
| `domestic_companion_v0` | settlement, household, hearth, barn, and workshop life |
| `working_mount_pack_v0` | transport, stable, cart, road, and trade-route use |
| `livestock_food_fiber_v0` | farm economy, hide, horn, wool, meat, and village context |
| `barnyard_poultry_v0` | flocks, cages, kitchens, yards, and low-cost ambient motion |
| `urban_vermin_v0` | cellars, alleys, pantries, ruins, and decay cues |
| `wild_game_prey_v0` | forests, parks, hunting grounds, and food-chain context |
| `wild_predator_v0` | threat, wilderness pressure, combat read, and caution symbols |
| `cave_nocturnal_v0` | caves, crypts, rafters, dark ceilings, and ambient clusters |
| `aquatic_wetland_v0` | ponds, rivers, cisterns, kitchens, damp dungeons, and waterline life |
| `omen_ritual_heraldic_v0` | statues, banners, graves, books, faction signs, and emblem conversion |

## Body-Plan Styles

| Body Plan | Core Shape Grammar |
| --- | --- |
| `small_quadruped_pet_v0` | capsule torso, rounded head, ear/tail silhouette, four small supports |
| `canine_predator_v0` | long muzzle, forward posture, tail angle, ruff or shoulder slope |
| `equine_mount_pack_v0` | barrel body, long neck, hoof columns, mane/tail strips, tack sockets |
| `hoofed_livestock_v0` | stocky or slender body, hoof stance, horn/antler/ear markers |
| `swine_body_v0` | low oval belly, snout disk, short legs, curled tail or tusk variant |
| `wool_fleece_ruminant_v0` | body core plus offset fleece shell and horn/beard options |
| `ground_bird_poultry_v0` | egg body, beak cone, comb tabs, wing patch, thin legs |
| `flying_bird_corvid_v0` | wedge body, beak wedge, wing slabs, tail fan, perch socket |
| `winged_bat_v0` | tiny body, broad membranes, rib curves, hanging socket |
| `rodent_vermin_v0` | tiny low capsule, pointed muzzle, round ears, long tail curve |
| `fish_streamlined_v0` | lens body, fin triangles, tail fork, scale bands |
| `snake_limber_body_v0` | spine curve, bevel radius, head wedge, belly strip |
| `amphibian_squat_v0` | squat body, large eyes, rear leg arcs, webbed feet |

## Asset Promotion Rule

Before an animal becomes a generated model, the workcard needs:

```text
reference packet -> silhouette sheet -> anatomy part list -> source dimensions
-> body-plan style -> Blender tool sequence -> QA checks
```

The source recipe should make the important silhouette first. Fur, feathers,
scales, and tiny surface detail are later passes unless they are essential to
recognizing the animal.
