# Base Form Tool Cards V0

Base-form tools create the first physical mass. Use them before detail tools.

## `mesh_from_pydata`

Plain English:

Build a mesh directly from source vertices, edges, and faces.

Best used for:

- sacred-geometry cells promoted into closed mesh regions
- low-poly tracery plates and cutters
- compound pier cross-sections
- custom column or post footprints
- deterministic blockout geometry from recipe JSON

Avoid when:

- the form is a simple cube, cylinder, or cone
- the shape is only a curved path that should stay editable as a curve
- the source does not have valid indexed vertices and faces yet

Key source fields:

```text
vertices
edges
faces
profile_id
part_id
material_role
```

How to use effectively:

- Keep vertex order consistent around each profile.
- Name the part before creating the mesh.
- Store the source profile or drawing-guide reference with the part.
- Use this for exact shapes, not quick eyeballed modeling.
- Follow with normals cleanup and bevel/weighted-normal work.

Common mistakes:

- mismatched face indexes
- flipped normals
- using too many tiny vertices before the silhouette is settled
- baking decorative uncertainty into coordinates instead of an edit knob

Architectural examples:

- pointed tracery cutter for a railing panel
- lobed compound-pier footprint
- custom plinth ring footprint
- selected rosette cell turned into a raised boss

## `extrude_faces`

Plain English:

Give selected faces thickness or push them inward/outward.

Best used for:

- panel recesses
- raised lips
- trim plates
- ribs cut from 2D drawings
- shallow relief details
- negative-space cutters made from flat profiles

Avoid when:

- the result needs a lathe/revolved side profile
- a curve sweep would be more controllable
- the face selection is not named or repeatable

Key source fields:

```text
selected_face_set
translation_axis
distance_m
direction
material_role
```

How to use effectively:

- Use small measured depths for ornament.
- Push recess fields inward before beveling their lip.
- Use outward extrusion for raised trim and inward extrusion for shadow cuts.
- Keep cutter extrusions slightly deeper than the target surface.

Common mistakes:

- extruding along the wrong local axis
- making all relief the same depth
- extruding before insetting, which loses the panel border
- forgetting that very shallow lips still need bevels to read

Architectural examples:

- blind panel field sunk into a post face
- raised stone border around a window opening
- rib strip lifted from a ceiling construction drawing
- arched cutout cutter for a guard panel

## `modifier_screw`

Plain English:

Spin a 2D side profile around an axis to make a radial object.

Best used for:

- balusters
- round posts
- finials
- beads and collars
- torus-like ring stacks
- vase, mace, or baseball-bat profiles

Avoid when:

- the object is square or faceted by design
- each side needs different ornament
- the side profile is not decided yet

Key source fields:

```text
side_profile_points
axis
angle
steps
radius_m
height_m
```

How to use effectively:

- Start with a clean side silhouette.
- Use fewer steps for deliberately chunky low-poly styles.
- Use more steps only when the asset needs a smoother cylindrical read.
- Name important profile zones: foot, belly, neck, collar, cap.
- Add bevel and weighted normals after the screw form.

Common mistakes:

- too many radial steps before the shape is approved
- profile crosses the spin axis and creates self-intersections
- forgetting to cap the top/bottom
- using screw for a square post that should be a section stack instead

Architectural examples:

- turned Victorian baluster
- entasis rail or club-shaped rail
- bead stack under a cap
- cylindrical newel post with collar rings

