# Material Asset Taxonomy V0

## Purpose

This taxonomy names the texture asset families the repo will need before
generating large sets of finished architectural assets.

## Base Materials

Stone:

- limestone
- sandstone
- basalt
- granite
- marble
- slate
- obsidian
- rubble stone
- carved stone
- wet stone

Wood:

- old oak
- dark stained wood
- rotted wood
- charred wood
- mine timber
- plank door wood
- polished handrail wood

Metal:

- wrought iron
- rusted iron
- bronze
- tarnished brass
- blackened steel
- gilded metal
- chain metal

Glass and ceramic:

- clear glass
- stained glass
- frosted glass
- cracked glass
- ceramic tile
- glazed tile

Soft or organic:

- cloth
- rope
- leather
- bone
- moss
- lichen
- slime
- roots

Special:

- ice
- lava rock
- glowing rune material
- emissive magic
- ash
- soot
- wax

## Layer Types

Base layer:

- color, roughness, normal, height

Wear layer:

- edge wear, chips, scratches, eroded corners

Grime layer:

- dirt, dust, soot, recess darkening

Moisture layer:

- wetness, waterline stain, slime, algae

Growth layer:

- moss, lichen, roots

Heat layer:

- scorch, char, glowing cracks, ash

Metal aging layer:

- rust, oxidation, tarnish, scratches

Paint/gilding layer:

- chipped paint, faded symbols, gold leaf, decorative bands

Emissive layer:

- magic lines, runes, crystal glow, forge heat

## Texture Asset Types

Tileable material:

- repeats across floors, walls, large blocks, and terrain.

Trim sheet:

- long strips for bevels, cornices, rails, frames, stair nosings, bands, and
  moulding.

Atlas:

- packed motifs such as rosettes, rivets, hinges, plaques, symbols, and small
  relief panels.

*** Decal:

- optional overlay for localized cracks, leaks, stains, marks, scorch, moss,
  symbols, impact damage, and story detail.
- lower-compute hardware does not get decals.

Mask:

- grayscale or vertex-color driven control map for dirt, edge wear, moss,
  wetness, roughness variation, and material blending.

Procedural recipe:

- source-owned material graph parameters that can generate base variation,
  bump, noise, wear, and grime without stored image files.

## Missing Asset Families

High priority:

- Gothic cold limestone tileable
- dark recess grime mask
- worn stone edge trim
- moss/lichen procedural mask
- wet sewer stone material
- rusted iron material
- old wood material
- stained glass starter atlas
- carved border trim sheet
- quatrefoil/rosette ornament atlas

Medium priority:

- soot/scorch layer
- mineral deposit layer
- mud splatter mask
- cracked plaster material
- chipped paint layer
- gilded trim material
- bone material
- ice/frost edge material

Deferred:

- high-density localized decals
- full PBR scanned material library
- bespoke hero-asset texture sets
- complex shader animation
