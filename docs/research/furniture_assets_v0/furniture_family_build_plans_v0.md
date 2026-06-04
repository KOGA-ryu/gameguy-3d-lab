# Furniture Family Build Plans V0

These are modeling plans, not woodworking plans. Each plan identifies source
fields, geometry choices, likely Blender tools, and operator checks.

## Rough Plank Stool

Build logic:

- seat slab first
- legs second
- stretchers or peg heads only if they improve silhouette
- broken-leg variant belongs to `ruin_salvage_v0`

Blender direction:

- `primitive_cube_add` or `mesh_from_pydata` for seat and legs
- `modifier_array` for repeated legs when regular
- `modifier_bevel` and `modifier_weighted_normal` before material assignment
- `create_collision_proxy` as one simplified box

Operator check:

- the object reads as a stool before wood grain or grime

## Joined Bench

Build logic:

- long seat board
- end supports
- aprons and stretchers
- joinery hints as shallow relief or small cut marks

Blender direction:

- simple cuboids for board/rails/supports
- `modifier_boolean` or `inset_faces` for mortise marks
- `modifier_array` for repeated supports on long benches
- material slots for worn seat, dark underside, and pegs

Operator check:

- apron and stretchers are named, not fused into one anonymous box

## Boarded Chest Or Coffer

Build logic:

- box case and lid establish function
- straps, hinges, lock plate, and handles establish status/use
- Gothic or merchant variants add raised panels and front ornament
- salvage variant removes boards or breaks supports

Blender direction:

- `primitive_cube_add` or `mesh_from_pydata` for case and lid
- `modifier_array` for straps
- `modifier_boolean` for lock/keyhole/damage cuts
- `relief_stack` source intent for panel depth

Operator check:

- the lid reads as openable and the lock/straps are separate material parts

## Trestle Table

Build logic:

- tabletop boards
- trestle supports
- long stretcher
- peg holes to show removable construction
- wear lane on top

Blender direction:

- cuboids for tabletop boards and trestles
- `modifier_array` for support repetition
- `modifier_bevel` for all broad wooden edges
- material slot for worn eating/work surface

Operator check:

- table length can change without redesigning every support

## Panelled Cupboard

Build logic:

- carcass, shelves, doors
- raised panels and cornice
- hinges, lock plate, and display sockets
- Gothic/merchant style controls panel ornament

Blender direction:

- cuboids for carcass, shelves, and doors
- `inset_faces` or `relief_stack` for raised panels
- `modifier_boolean` for lock and door gaps
- `modifier_array` for shelves, panels, hinges

Operator check:

- it reads as a cupboard, not a chest: vertical case, doors, shelves, front
  display logic

## High-Back Chair

Build logic:

- seat frame and legs
- rear legs continue into back posts
- high back communicates status
- arms and cushion are tier toggles

Blender direction:

- cuboids for frame, legs, arms, back
- `modifier_mirror` for symmetry
- `modifier_boolean` or relief for back-panel detail
- cushion can start as low-poly rounded rectangle mesh

Operator check:

- back height, arms, and cushion are independently editable

## Canopy Bed

Build logic:

- bed frame and mattress first
- four posts and canopy frame second
- curtains as optional low-cost planes or folded strips
- headboard/footboard controls status

Blender direction:

- cuboids for frame, posts, canopy
- `primitive_plane_add` plus `modifier_solidify` for curtains
- `modifier_mirror` for post symmetry
- material slots carry textile/wood separation

Operator check:

- curtains are optional so lower-compute variants can keep the bed readable

## Lectern Or Reading Desk

Build logic:

- sloped top angle
- book-stop ledge
- side panels and base
- shelf/drawer/symbol panel as tier toggles

Blender direction:

- `mesh_from_pydata` for angled top and side panels
- `modifier_boolean` for sockets or front relief cuts
- `modifier_mirror` for symmetrical side supports
- separate `book_socket` from the wood mesh

Operator check:

- book/rest socket exists and is independent of visible mesh

## Workbench And Tool Rack

Build logic:

- thick bench top
- support frame
- lower shelf
- peg row and tool sockets
- scars and vise hint as optional details

Blender direction:

- cuboids for bench frame
- `modifier_array` for pegs and slots
- `modifier_boolean` for sockets and scar cuts
- keep actual tools separate unless the source recipe declares them

Operator check:

- tool slots are sockets, not baked guesses

## Throne Or Court Chair

Build logic:

- central-axis landmark
- raised seat
- high back
- wide arms
- crest/symbol panel
- dais socket

Blender direction:

- `modifier_mirror` around the central axis
- relief stack for symbol panel
- `primitive_uv_sphere_add` or simple caps for crest details
- `create_collision_proxy` remains ordinary seating/obstacle geometry

Operator check:

- it reads as authority furniture from silhouette before ornament
