# Asset QA Checklist V0

Use this checklist before an asset is archived, promoted, or turned into a
source recipe.

## Visual Read

- The silhouette reads correctly from gameplay distance.
- The close-up detail supports the style reference.
- Major forms are named: base, shaft, cap, rail, panel, rib, arch, socket, trim,
  or ornament.
- The asset has enough bevels/chamfers to catch light.
- Low-poly simplification looks intentional, not accidental.
- Decorative detail does not hide sockets or gameplay-critical parts.

## Geometry

- Dimensions are in meters.
- Origin and pivot are correct.
- Bounds match the intended footprint.
- Mesh has no obvious holes unless they are intended cutouts.
- Normals face outward.
- Booleans are applied or kept as named source cutters.
- Repeated parts have consistent spacing.
- Mirrored parts align at the centerline.
- Bevels do not destroy low-profile detail.

## Modularity

- Grid snap is declared.
- Sockets/connectors are named.
- Socket depth and alignment are visible or documented.
- Adjacent assets can meet without visible gaps.
- The asset can rotate or mirror without breaking its intended use.

## Materials And Textures

- Material roles are assigned by part.
- UV approach is declared.
- Trim-sheet or tileable material direction is declared.
- Lower-compute version works without decals.
- Recesses, lips, and bevels can carry grime/wear without hand painting every
  detail.

## Gameplay

- Collision proxy exists or the asset is marked decorative_only.
- Walkable/blocking/cover semantics are declared when relevant.
- Interactable states are declared when relevant.
- Anchors exist for lights, VFX, particles, sounds, or prompts when relevant.

## Performance

- LOD plan exists.
- Tiny detail can be removed without ruining the main silhouette.
- Repetition is handled with arrays, instances, or source repetition rules when
  possible.
- Decals are optional and disabled for low hardware.
- The asset has a clear export target.

## Source Ownership

- Reference packet exists.
- Drawing guide exists for any non-trivial shape.
- Blender tool sequence is documented.
- Design decisions live in docs, style sheets, or recipes.
- Blender adapter work does not invent the style.
- Corrections from the operator pass are recorded.

