# Food And Drink Family Build Plans V0

These are modeling plans, not recipes or food-safety notes. Each plan identifies
source fields, geometry choices, likely Blender tools, and operator checks.

## Round Loaf

Build logic:

- rounded loaf body
- shallow crust scores
- optional crumb/cut edge
- serving state: whole, cut, ration, offering, stale

Blender direction:

- `mesh_from_pydata` or low UV sphere base
- `modifier_displace` for broad surface roughness
- shallow relief for scores
- material roles for crust, crumb, flour dust

Operator check:

- it reads as bread without texture detail

## Flatbread Wrap

Build logic:

- thin irregular sheet
- folded edge
- cord tie
- filling socket
- wrapped/open state

Blender direction:

- custom polygon mesh with small thickness
- curve for tie cord
- socket for optional filling

Operator check:

- filling can be disabled or swapped without rebuilding the bread

## Cheese Wedge

Build logic:

- wedge body
- rind edge
- cut face
- optional holes or crumbs
- freshness/spoilage state

Blender direction:

- triangular custom mesh
- material roles for rind and cut face
- shallow booleans for holes only when needed

Operator check:

- rind and cut face contrast at small scale

## Produce

Build logic:

- base fruit/root shape
- stem or leaf hint
- bundle tie for root bundles
- freshness/spoilage state

Blender direction:

- sphere/radial stack for fruit
- cone/section stack for roots
- arrays for bundles and scatter

Operator check:

- count and freshness are source fields, not hand edits

## Meat And Fish

Build logic:

- readable mass/silhouette first
- bone, spine, tail, or fat cues second
- platter/socket state third
- cooking/preservation/spoilage state

Blender direction:

- custom rounded meshes
- small cylinders or curves for bones/spines
- separate platter mesh
- material roles for cooked, bone, fat, char

Operator check:

- food and serving surface are separately selectable

## Stew Bowl

Build logic:

- bowl shell
- liquid surface
- optional ingredient chunks
- spoon socket
- full/empty/hot/cold state

Blender direction:

- radial profile for bowl
- separate disk for liquid
- small repeated chunks by array

Operator check:

- bowl works as empty and full from same source fields

## Drink Vessels

Build logic:

- body profile
- rim/neck/handle/stem/foot
- liquid line or fill surface
- contents id and fill state

Blender direction:

- `modifier_screw` or radial stack
- curves for handles
- material roles for glass, ceramic, metal, liquid

Operator check:

- contents and fill line are source data

## Storage

Build logic:

- sack/jar body
- tied mouth, stopper, label, seal
- contents id
- full/empty/spilled/sealed state

Blender direction:

- rounded custom mesh for sacks
- radial profile for jars
- curves for ties
- labels as simple front profiles

Operator check:

- label/seal/contents state can change without replacing mesh

## Spoilage

Build logic:

- original form remains readable
- localized mold spots or dark rot
- missing chunks only when the silhouette benefits
- deterministic scatter positions

Blender direction:

- low-cost material roles and small added spots
- `modifier_boolean` only for major missing chunks
- count can be reduced for low-compute scenes

Operator check:

- spoiled props read through silhouette and material roles, not decals
