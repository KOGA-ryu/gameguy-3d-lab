# Reference And Drawing Guide Queue V0

This page defines how reference images become useful build instructions instead
of loose inspiration.

## Reference Packet

Each asset should get a compact reference packet before modeling.

Required fields:

```text
asset_id:
family:
component:
primary_reference:
secondary_references:
use_policy:
visible_anatomy:
shape_language:
ignored_details:
scale_hints:
material_hints:
code_or_safety_notes:
```

## Reference Image Rules

- Use references for morphology unless the source explicitly allows more.
- Do not copy a modern artist's exact design as final game art.
- Do not claim historical accuracy from one image.
- Do not claim building-code compliance from visual copying.
- Save source URL, title, date accessed, and why the image matters.
- Prefer references that show front, side, top, section, or construction lines.

## Drawing Guide

The drawing guide turns the reference into buildable geometry.

Required sections:

- master grid
- centerlines and axes
- primary circles or polygons
- arcs and tangent points
- selected visible linework
- omitted construction lines
- 2D profiles and cross-sections
- negative-space cutters
- extrusion depths
- bevel/chamfer notes
- material role regions
- sockets and connector positions

## Sacred-Geometry Pattern Guide

For rosettes, windows, vaults, screens, and ornament fields, use this sequence:

```text
construction grid
-> repeated module centers
-> radial divisions
-> circles and polygon intersections
-> selected lines
-> omitted lines
-> closed cells
-> visible ribs, panels, holes, or cutters
-> 3D operations
```

The important vocabulary is:

- construction line: a guide line that may not be visible in the final asset
- selected line: a guide line promoted to visible geometry
- omitted line: a guide line intentionally hidden
- cell: a closed 2D region created by intersections
- motif: a repeated visible shape made from selected cells or selected edges
- cutter: a 2D or 3D shape used to remove material
- rib: a raised structural or decorative line
- field: the background surface that receives cuts or relief
- boss: a raised node at rib intersections

## Converting Drawing Pieces To Blender Work

Use this mapping:

| Drawing Piece | Blender Direction |
| --- | --- |
| closed polygon cell | `mesh_from_pydata` face, then `extrude_faces` or cutter mesh |
| arc or rail path | `curve_bezier_add`, `curve_bevel_profile`, then `curve_to_mesh` |
| repeated motif | `modifier_array`, `object_duplicate_radial`, or `gn_instance_on_points` |
| mirrored tracery | model half, then `modifier_mirror` |
| recessed field | `inset_faces`, then shallow `extrude_faces` inward |
| open void | cutter mesh plus `modifier_boolean` |
| rib | curve path with bevel profile, or thin extruded strip |
| boss/bead | cylinder, torus, sphere, or low-poly custom mesh |

## Drawing Guides To Create Next

Priority queue:

1. Gothic railing post face panel guide.
2. Baseball-bat rail side profile guide.
3. Blind tracery infill panel guide.
4. Pointed arch window lancet guide.
5. Compound pier cross-section guide.
6. Ribbed vault bay guide.
7. Muqarnas cell-to-volume guide.
8. Rosette window selected-line guide.
9. Door surround moulding side-profile guide.
10. Stair rail newel-and-baluster spacing guide.

