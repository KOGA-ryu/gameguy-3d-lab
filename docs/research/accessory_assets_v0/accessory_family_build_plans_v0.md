# Accessory Family Build Plans V0

These are modeling plans, not fabrication plans. Each plan identifies source
fields, geometry choices, likely Blender tools, and operator checks.

## Leather Belt With Buckle

Build logic:

- strap first
- buckle frame, tongue, keeper loop, holes, and rivets second
- attachment sockets for pouches, keys, and scabbards

Blender direction:

- `mesh_from_pydata` or simple cuboids for strap
- `primitive_torus_add` or custom loop mesh for buckle
- `modifier_boolean` for belt holes
- `modifier_array` for holes and rivets

Operator check:

- buckle, strap, holes, and sockets are independently selectable

## Belt Pouch Or Coin Purse

Build logic:

- soft body profile
- flap or drawstring mouth
- belt loop and loot socket
- stitches/patches as optional style layers

Blender direction:

- `mesh_from_pydata` for soft rounded body
- curves for drawstring
- `modifier_array` for stitch marks
- material slots for leather/cloth/cord/dark mouth

Operator check:

- attachment socket and loot socket are separate

## Brooch Or Cloak Pin

Build logic:

- ring frame
- terminals
- pin
- bosses/gems/symbols by status tier
- cloth socket

Blender direction:

- `primitive_torus_add` or custom partial ring mesh
- cylinders for pin
- radial duplication for bosses
- material slots for metal and dark recesses

Operator check:

- the pin reads as functional, not pure ornament

## Signet Ring

Build logic:

- band
- seal face
- shoulders
- engraving or symbol panel
- identity socket

Blender direction:

- `primitive_torus_add` for band
- cylinder or custom mesh for seal face
- shallow relief for identity mark
- material role for dark engraving

Operator check:

- the signet face is source-owned and readable at prop scale

## Pendant Or Amulet

Build logic:

- pendant body
- chain/cord loop
- front symbol face
- optional gem socket
- wear/inventory socket

Blender direction:

- custom mesh or simple radial body
- curves for cord/chain
- relief stack for symbol face
- material slots for metal, gem, cord

Operator check:

- the pendant has a clear front-facing orientation

## Key Ring With Warded Keys

Build logic:

- ring
- repeated keys with bow, shank, bit, ward cuts
- optional tag
- access ids

Blender direction:

- `primitive_torus_add` for ring
- `mesh_from_pydata` for key silhouettes
- `modifier_boolean` for ward cuts
- radial or linear duplication for multiple keys

Operator check:

- each key can map to a different source access id

## Chatelaine Belt Hook

Build logic:

- belt hook
- hanging plate
- chains/rings
- tool sockets
- guild or household mark

Blender direction:

- custom metal plate mesh
- curves for simple chains
- torus/cylinders for rings
- sockets for attached tools

Operator check:

- attached tools are sockets, not baked guesses

## Satchel Or Messenger Bag

Build logic:

- bag body
- flap
- shoulder strap
- gussets
- closure
- content sockets

Blender direction:

- rounded cuboid/custom mesh body
- curve strap
- stitch arrays
- patch meshes for traveler variants

Operator check:

- content sockets are explicit and body wear can change by status tier

## Scabbard Belt Hanger

Build logic:

- tapered scabbard body
- throat and chape fittings
- hanger straps and belt loops
- weapon socket

Blender direction:

- tapered mesh from trapezoid/rounded profile
- separate metal fittings
- curves or flat straps for hangers
- material slots for leather and metal

Operator check:

- empty scabbard still reads as weapon suspension

## Spectacles And Case

Build logic:

- case body first
- lens rims and bridge optional
- lenses optional
- hinge and lining material
- lens/puzzle socket

Blender direction:

- capsule/rounded rectangle case mesh
- torus/circle rims
- simple lens disks with material role
- mirror rims around bridge

Operator check:

- case reads if the tiny spectacles are hidden for low compute

## Seal Matrix Or Stamp

Build logic:

- handle
- stamp face
- shoulder transition
- engraving
- wax/document socket

Blender direction:

- radial stack or cylinders
- shallow relief for symbol
- material slots for metal and dark engraving
- identity mark stays source-owned

Operator check:

- face orientation and identity id are explicit

## Waterskin Or Flask

Build logic:

- flattened soft body
- neck
- stopper
- cord loop
- seam path
- liquid state as source field

Blender direction:

- custom rounded body mesh
- cylinder neck/stopper
- curve cord
- seam curve or stitch marks
- simple collision proxy

Operator check:

- liquid state is not a material guess; it is a source/workcard field
