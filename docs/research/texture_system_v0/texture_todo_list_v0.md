# Texture TODO List V0

## Goal

Build a texture system that can support different architectural styles and
different dungeon identities without hand-authoring every asset from scratch.

The system should not only store images. It should store texture logic:

```text
material role
-> surface role
-> dungeon palette
-> wear state
-> hardware tier
-> final material layer stack
```

## TODO

### 1. Material Roles

Define reusable material roles:

- `base_stone`
- `carved_stone`
- `trim_stone`
- `floor_stone`
- `wet_stone`
- `old_wood`
- `polished_wood`
- `rotted_wood`
- `iron`
- `rusted_iron`
- `bronze`
- `glass`
- `stained_glass`
- `plaster`
- `ceramic_tile`
- `dirt`
- `mud`
- `ice`
- `lava_rock`
- `bone`
- `cloth`
- `emissive_magic`

### 2. Surface Roles

Define where a material sits on geometry:

- `top_surface`
- `bottom_surface`
- `vertical_face`
- `outer_edge`
- `inner_recess`
- `socket_shadow`
- `walkable_floor`
- `hand_contact`
- `waterline`
- `ceiling_underside`
- `trim_lip`
- `ornament_face`
- `carved_groove`
- `crack_inside`
- `support_base`

### 3. Dungeon Style Packs

Create dungeon palettes:

- `gothic_crypt`
- `cathedral_ruin`
- `wet_sewer`
- `mossy_aqueduct`
- `lava_forge`
- `ice_vault`
- `sandstone_tomb`
- `obsidian_temple`
- `wooden_mine`
- `iron_prison`
- `arcane_library`
- `overgrown_shrine`
- `bone_catacomb`
- `royal_castle`
- `abandoned_village`

Each dungeon style needs:

- base material families
- color palette
- roughness defaults
- dirt/grime behavior
- edge-wear behavior
- wetness behavior
- emissive behavior
- hardware tier fallbacks

### 4. Tileable Base Materials

Needed tileables:

- limestone
- sandstone
- basalt
- granite
- marble
- brick
- plaster
- old wood
- charred wood
- iron
- bronze
- glass
- ceramic tile
- dirt/mud
- ice
- lava rock
- bone

### 5. Damage And Age Layers

Needed overlays or procedural masks:

- cracks
- chips
- broken corners
- worn edges
- pitted stone
- scratched metal
- splintered wood
- eroded carvings
- missing plaster
- crumbling mortar
- softened stair nosings
- polished hand-contact areas

### 6. Grime And Environment Layers

Needed environment layers:

- dust
- soot
- water stains
- dampness
- moss
- lichen
- slime
- rust streaks
- mineral deposits
- mud splatter
- dark dirt inside recesses
- candle smoke marks
- algae at waterline

### 7. *** DECALS *** High-Cost Optional Layer

Big rule:

```text
lower-compute hardware does not get decals
```

Decals are still important for high-quality targets, but they must be optional.
Every asset must read correctly without them.

Decal candidates:

- cracks
- stains
- leaks
- scorch marks
- carved runes
- painted symbols
- blood or dark residue
- chipped paint
- wall markings
- floor scratches
- candle smoke marks
- impact marks
- moss patches
- slime splashes
- rust streaks

Fallbacks when decals are disabled:

- vertex color masks
- baked dirt/edge-wear masks
- trim-sheet strips
- material roughness variation
- procedural noise and bump
- geometry-owned recess shadow material
- darker material slot for grooves and sockets

### 8. Trim Sheets

Needed trim sheets:

- stone bevel trim
- carved border trim
- Gothic tracery trim
- rail/post collar trim
- door/window frame trim
- stair nosing trim
- cornice trim
- baseboard/plinth trim
- metal banding trim
- worn edge strips
- bead strip
- cove/ogee profile strip

### 9. Ornament Atlases

Needed atlas motifs:

- trefoils
- quatrefoils
- cinquefoils
- rosettes
- star bosses
- rivets
- nail heads
- hinge plates
- bead strips
- carved flowers
- circular medallions
- rune marks
- small relief panels

### 10. Utility Maps

Every material recipe may need:

- albedo/base color
- normal
- roughness
- metallic
- ambient occlusion
- height/displacement
- opacity
- emissive
- dirt mask
- edge-wear mask
- wetness mask
- moss mask
- vertex color mask

### 11. UV Strategy

Rules to define:

- blockouts use box projection
- posts and rails use cylindrical unwrap when round
- long trim uses trim-sheet strips
- panels use front-face UV islands
- ornaments use atlas islands
- repeated assets reuse shared trim sheets
- low-compute targets prefer fewer UV sets and fewer sampled maps

### 12. Blender Material Tool Sequence

Initial tool sequence:

```text
assign material slots by named part
-> apply base procedural material
-> add procedural noise
-> add bump/normal
-> add dirt/wear masks
-> add roughness variation
-> apply optional decals only above low hardware tier
-> validate material slots
-> export
```

## First Practical Slice

Start with:

```text
gothic_crypt_stone_material_stack_v0
```

Target parts:

- plinth base
- rail post shaft
- socket recess
- pointed-arch panel
- cap lip

Required result:

- works without decals
- has material roles by named part
- has edge wear, recess grime, and roughness variation
- can accept decals later on higher hardware tiers
