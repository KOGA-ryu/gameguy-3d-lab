# Assembly Tool Cards V0

Assembly tools repeat, mirror, combine, and cut prepared parts.

## `modifier_boolean`

Plain English:

Use one object to cut, join, or intersect another object.

Best used for:

- rail sockets
- arched recesses
- window and door openings
- tracery voids
- mortise-like joints
- panel reveals and shadow cuts

Avoid when:

- the same effect can be done with a simple inset and extrusion
- the cutter is not named
- the cut depth is not known
- the resulting geometry must stay extremely low-poly with no cleanup pass

Key source fields:

```text
target_part_id
cutter_part_id
operation
cut_depth_m
cutter_profile_id
keep_cutter_for_evidence
```

How to use effectively:

- Build cutters from simple source profiles.
- Make cutters slightly deeper than the surface they cut.
- Name cutters by job: `rail_socket_left_cutter`, `pointed_arch_recess_cutter`.
- Keep cutter objects available in proof/adapter reports even if hidden in final
  preview.
- Follow booleans with normals, weld/merge, and bevel decisions.

Common mistakes:

- using booleans for every tiny groove
- losing track of which cutter created which recess
- cutters that barely intersect the target
- dirty geometry that hides non-manifold problems until export

Architectural examples:

- rectangular socket cut into a railing post
- lancet arch cut into a panel field
- quatrefoil void in a gothic screen
- door-frame hinge mortise

## `modifier_array`

Plain English:

Repeat one object in a linear or offset pattern.

Best used for:

- balusters
- beads
- ribs
- stair treads
- crenellations
- repeated window mullions
- repeated ceiling coffers

Avoid when:

- each repeat needs different shape decisions
- spacing is not defined
- the first item has not been approved

Key source fields:

```text
source_part_id
count
offset_m
axis
start_anchor
end_anchor
spacing_policy
```

How to use effectively:

- Approve one repeated unit first.
- Define spacing from sockets or construction centers.
- Keep count and offset in the source recipe.
- Use arrays for repeatable architecture, not for organic randomness.
- Convert or realize only when the asset needs per-instance edits.

Common mistakes:

- eyeballed spacing that breaks modular length
- array count that collides with end posts
- repeating high-detail meshes before LOD policy exists
- forgetting that railings and stairs may have code/safety spacing concerns

Architectural examples:

- row of balusters between newel posts
- bead strip below a cap
- vault ribs repeated across a bay
- rectangular stair tread stack

## `modifier_mirror`

Plain English:

Model one side and mirror it across a centerline.

Best used for:

- symmetric panels
- window tracery
- rail post faces
- door frames
- arches
- half-built ornamental motifs

Avoid when:

- the style is intentionally asymmetric
- the origin or mirror plane is not settled
- mirrored details should not meet at the center

Key source fields:

```text
mirror_axis
mirror_origin
source_half
merge_centerline
symmetry_policy
```

How to use effectively:

- Set the origin before adding the mirror.
- Model the clean half that has the fewest special cases.
- Use mirror before bevels when possible.
- Check centerline overlap before final export.
- For four-sided posts, mirror a face detail only if all faces share that detail.

Common mistakes:

- wrong object origin
- center seam gaps
- doubled geometry on the centerline
- mirrored sockets that should have different connector roles

Architectural examples:

- left/right half of a gothic guard panel
- symmetrical door surround
- window lancet pair
- front-face ornament on a newel post

