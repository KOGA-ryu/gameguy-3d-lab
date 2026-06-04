# Shape Refinement Tool Cards V0

Shape-refinement tools make simple forms read as intentional architecture.

## `inset_faces`

Plain English:

Create an inner face inside a selected face.

Best used for:

- recessed panels
- raised lips
- framed fields
- bevel-safe borders
- decorative face masks

Avoid when:

- the face is not planar enough
- the border width is unknown
- the target face is already too thin

Key source fields:

```text
target_face_set
thickness_m
inset_count
panel_role
follow_with_extrusion
```

How to use effectively:

- Inset before extruding a recess.
- Use one inset for a simple panel, two for raised lip plus inner field.
- Keep inset widths consistent across related assets.
- Use named face sets so the same operation can be regenerated.

Common mistakes:

- insetting tiny faces until they collapse
- inconsistent border widths between panels
- forgetting to bevel the raised border
- treating inset as decoration without deciding its material role

Architectural examples:

- fielded panel on a railing post
- door panel frame
- blind arcade recess
- wall bay panel

## `modifier_bevel`

Plain English:

Chamfer or round edges so the form catches light.

Best used for:

- stone arrises
- rail grip edges
- cap lips
- panel borders
- socket edges
- worn corners

Avoid when:

- the mesh has unresolved bad topology
- the bevel width is larger than the detail being preserved
- the asset needs sharp silhouette cuts

Key source fields:

```text
target_edges
width_m
segments
affect
limit_method
material_or_edge_role
```

How to use effectively:

- Use small bevels early to prove the visual read.
- Increase bevel width only on structural lips and touchable edges.
- Use one segment for chunky low-poly stone.
- Use two or three segments only when the asset is close-up or rounded.
- Pair with weighted normals.

Common mistakes:

- bevels that erase shallow relief
- same bevel width on every part
- beveling helper collision or cutter objects
- assuming bevels replace correct shape proportions

Architectural examples:

- chamfered plinth base
- softened handrail top
- rounded cap lip
- worn stone block edges

## `modifier_weighted_normal`

Plain English:

Adjust normals so flat and beveled faces shade cleanly without adding much mesh.

Best used for:

- low-poly stone
- beveled blocks
- rail posts
- columns
- panels with shallow lips
- hard-surface architecture

Avoid when:

- the mesh normals are already broken
- the object should look organically smooth
- sharp edges are not marked or preserved

Key source fields:

```text
target_object
keep_sharp
normal_policy
paired_bevel_step
```

How to use effectively:

- Add after bevels.
- Keep sharp edges where the silhouette must remain crisp.
- Use it to make simple geometry look finished, not to hide bad proportions.
- Compare flat, smooth, and weighted-normal previews from the gameplay angle.

Common mistakes:

- applying before bevels
- smoothing away intentional hard edges
- using it to hide non-manifold geometry
- forgetting that material roughness also affects the read

Architectural examples:

- chamfered railing post that still reads as stone
- low-poly column with clean highlight bands
- door frame with readable raised trim
- blocky vault rib with polished light response

## `curve_bevel_profile`

Plain English:

Give a curve thickness by assigning a round or custom profile.

Best used for:

- ribs
- rails
- arches
- pipes
- scrolls
- vine-like ornament
- curved trim

Avoid when:

- the object needs flat planar faces
- the path should be a boolean cutter instead
- the profile thickness is not known

Key source fields:

```text
curve_path_id
bevel_depth_m
bevel_resolution
profile_shape
material_role
```

How to use effectively:

- Draw the path first, then tune the thickness.
- Use low bevel resolution for chunky/low-compute assets.
- Use custom profile only when round thickness is not enough.
- Convert to mesh only after the path and thickness are approved.

Common mistakes:

- too much bevel resolution on tiny detail
- using round profiles where a rib needs a flat back
- converting to mesh too early
- forgetting that curve thickness affects intersections at corners

Architectural examples:

- gothic vault rib
- curved handrail
- arched window trim
- scroll bracket starter shape

