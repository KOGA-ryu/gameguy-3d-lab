# Low-Poly Modeling Script Notes v0

## Purpose

This note records how to build low-poly models in this repo without turning
Blender into the source of design decisions.

The useful pipeline is:

```text
reference / sketch / recipe
-> named forms and silhouette targets
-> deterministic low-poly mesh
-> bevel / normal / material finish
-> Blender preview/export
```

Low-poly does not mean "bad model with fewer vertices." It means the model uses
the smallest number of intentional planes needed to read clearly from the target
camera distance.

In this repo, low-poly should be treated as a construction grammar:

```text
source proportions
-> named silhouette planes
-> controlled edge breaks
-> deterministic vertices/faces
-> small bevels and normal polish
-> validated preview/export
```

That matters because the same asset may later need ASCII preview, Blender
preview, LOD export, collision, sockets, and material regions. The low-poly mesh
has to be understandable before it becomes pretty.

## Research Sources

- Blender Mesh API: `Mesh` data stores vertices, edges, loops, and polygons; `Mesh.from_pydata()` is the direct API for script-created vertices/faces.
  - https://docs.blender.org/api/current/bpy.types.Mesh.html
- Blender BMesh API: use when Python needs edit-style mesh operations instead of only creating compact mesh data.
  - https://docs.blender.org/api/current/bmesh.html
- Blender mesh-mode gotchas: be careful about object-mode mesh data vs edit-mode data when scripting.
  - https://docs.blender.org/api/current/info_gotchas_meshes.html
- Blender Object operators: `shade_flat`, `shade_smooth`, and smooth-by-angle are available, but operator context matters.
  - https://docs.blender.org/api/current/bpy.ops.object.html
- Blender Bevel modifier: non-destructive edge beveling, with width, segments, limit method, harden normals, and face strength.
  - https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html
- Blender Weighted Normal modifier: improves hard-surface shading and works well after bevels.
  - https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html
- Blender Decimate modifier: useful for reducing complex/sculpted meshes, but it should not replace intentional low-poly construction.
  - https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/decimate.html

## Low-Poly Model Types

Use different low-poly approaches depending on the source asset.

| Type | Good For | Script Strategy |
| --- | --- | --- |
| blockout mesh | walls, crates, posts, plinths, furniture | boxes, custom cuboids, bevel policy |
| radial stack | columns, posts, balusters, bottles, shafts | height/radius rings, low segment count, bevel bands |
| section stack | star columns, compound piers, non-round supports | 2D section contours lofted through height |
| profile sweep | moulding, trim, rails, ribs, scrolls | 2D profile plus path or straight extrusion |
| faceted surface patch | heads, bodies, terrain, vault cells | named planes and bend fields |
| ornament plate | tracery, panels, quatrefoils, relief | 2D closed shapes, inset/extrude/solidify |
| imported reduction | scanned/sculpted/reference mesh | decimate/remesh/retopo only after source is known |

## Low-Poly Shape Rules

1. Start with silhouette.
   If the outline does not read, bevels and textures will not save it.

2. Use large forms first.
   Build trunk, shaft, face mask, roof mass, rail body, or column body before trim.

3. Use named planes.
   Low-poly assets read through planes: front plane, side plane, top plane,
   cheek plane, jaw plane, plinth face, bevel face, cap slope.

4. Spend vertices at bends.
   Put geometry where the form changes direction: brow break, cheekbone, collar,
   socket lip, arch spring line, roof ridge, rail transition.

5. Use bevels as edge language.
   A one-segment bevel is often enough for stone, wood, metal, and stylized
   character forms. More segments should be deliberate.

6. Use weighted normals after bevels.
   Weighted normals can make low geometry look cleaner while preserving hard
   faceted surfaces.

7. Decimate only as a cleanup/LOD tool.
   For source-owned assets, the compiler should usually emit the low-poly mesh
   directly. Decimate is better for imported/sculpted/high-poly sources or LODs.

8. Keep detail as named parts.
   A low-poly model can still be rich if every strip, rib, recess, bead, socket,
   panel, and shadow groove has a name and budget. Unnamed detail becomes
   impossible to edit later.

9. Separate geometry detail from shading detail.
   Geometry creates silhouette, bevels, relief, and physical contact. Normals,
   materials, UVs, and textures improve the read but should not be required for
   the object to make sense.

## Scriptable Blender Sequence

Preferred adapter sequence:

```text
1. Create mesh data.
2. Link object.
3. Assign material slots.
4. Set flat/smooth shading policy.
5. Add bevel modifier where recipe says so.
6. Add weighted normal modifier after bevel.
7. Optionally add decimate only for LOD/export variants.
8. Validate mesh counts, bounds, symmetry, sockets, and material IDs.
9. Render/export.
```

Repo-owned sequence:

```text
1. Read source recipe.
2. Compile named components into vertices/faces.
3. Attach provenance, material roles, sockets, and expected bounds.
4. Emit deterministic asset/tool-plan JSON.
5. Let Blender consume the JSON.
6. Blender creates mesh objects and applies only declared finish operations.
7. Blender writes a validation/report artifact.
```

Python shape creation pattern:

```python
mesh = bpy.data.meshes.new("asset_mesh")
mesh.from_pydata(vertices, edges, faces)
mesh.validate()
mesh.update()

obj = bpy.data.objects.new("asset_part", mesh)
bpy.context.collection.objects.link(obj)
```

Low-poly finish pattern:

```python
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.shade_flat(keep_sharp_edges=True)

bevel = obj.modifiers.new("source_bevel", "BEVEL")
bevel.width = bevel_m
bevel.segments = 1
bevel.affect = "EDGES"

weighted = obj.modifiers.new("source_weighted_normals", "WEIGHTED_NORMAL")
weighted.keep_sharp = True
obj.select_set(False)
```

LOD cleanup pattern:

```python
decimate = obj.modifiers.new("lod_decimate", "DECIMATE")
decimate.ratio = 0.55
```

Use that only when the source mesh is already too dense or when making a lower
detail export. Do not use it to hide a messy generator.

## Tool Mapping

| Modeling Need | Blender Tool | Script Note |
| --- | --- | --- |
| exact custom mesh | `Mesh.from_pydata()` | preferred for source-owned low-poly geometry |
| editable mesh operations | `bmesh` | useful when building faces, loops, and cleanup procedurally |
| boxy mass | `primitive_cube_add` or custom cuboid mesh | acceptable for rough blockouts and simple parts |
| cylindrical mass | `primitive_cylinder_add` or radial stack mesh | keep segment count explicit |
| conic/spire mass | `primitive_cone_add` or radial stack mesh | use flat shade for faceted stone/metal |
| panels/recesses | `inset_faces`, `extrude_faces` | source must own inset width and depth |
| chamfers/lips | `modifier_bevel` | one segment by default for low-poly readability |
| clean hard-surface light | `modifier_weighted_normal` | apply after bevels |
| symmetry | `modifier_mirror` | source owns mirror axis and centerline |
| repeated parts | `modifier_array`, radial duplication | source owns count, spacing, and naming |
| curved rails/ribs | curve path plus bevel profile | convert after path and thickness are approved |
| LOD reduction | `modifier_decimate` | export helper, not a primary generator |

## Recipe Fields To Own

A useful source recipe should own these fields before Blender runs:

```json
{
  "silhouette_role": "front_read",
  "target_view_distance": "medium",
  "poly_budget": {
    "target_vertices": 300,
    "target_faces": 250
  },
  "plane_language": ["front_plane", "side_plane", "bevel_face"],
  "bend_fields": [],
  "transition_fields": [],
  "bevel_policy": {
    "default_segments": 1,
    "edge_width_m": 0.004,
    "harden_normals": true
  },
  "normal_policy": {
    "shade": "flat",
    "weighted_normals": true
  },
  "material_regions": [
    {
      "material_id": "stone_core",
      "part_ids": ["shaft", "plinth", "cap"]
    }
  ],
  "socket_policy": {
    "origin": "bottom_center",
    "required_sockets": ["base_mount", "top_mount"]
  },
  "lod_policy": {
    "decimate_allowed": false
  },
  "qc_policy": {
    "bounds_required": true,
    "symmetry_required": false,
    "non_manifold_allowed": false
  }
}
```

Per-part fields should be boring and explicit:

```json
{
  "part_id": "front_panel_lip",
  "source_role": "raised_panel_border",
  "dimensions_m": [0.24, 0.012, 0.42],
  "operation_stack": ["mesh_from_pydata", "modifier_bevel", "modifier_weighted_normal"],
  "vertices_m": [],
  "faces": [],
  "material_id": "stone_edge",
  "bevel_m": 0.004,
  "shade": "flat"
}
```

## How This Applies To The Repo

For this repo, low-poly scripting should not start from Blender primitives when
the shape is important. It should start from source-owned geometry:

```text
2D contour
-> ring stack
-> profile sweep
-> bend field
-> transition field
-> mesh_from_pydata
-> bevel + weighted normals
```

Good low-poly assets in this repo should have:

- named source components
- deterministic vertices/faces
- explicit material IDs
- explicit bevel policy
- flat or weighted-normal shading policy
- cheap preview path before final Blender render
- validation report with bounds, symmetry, sockets, part counts, and face counts

The compiler should answer these questions before Blender opens:

```text
What is the silhouette?
Where are the plane breaks?
Which edges get bevels?
Which details are real geometry?
Which details are only material/normal/texture support?
What is the vertex/face budget?
What must remain editable?
What sockets, origins, and bounds are required?
```

## What Not To Do

- Do not start by sculpting a high-poly model and then decimating it unless the
  source is an imported/reference mesh.
- Do not let Blender modifiers decide the asset design.
- Do not add bevels before the silhouette works.
- Do not smooth everything. Low-poly needs controlled hard planes.
- Do not hide construction failures with texture, decals, or lighting.
- Do not let every asset default to a square box. Pick the correct low-poly
  grammar: radial stack, section stack, profile sweep, surface patch, or
  ornament plate.
- Do not treat ASCII, SVG, and Blender as separate art directions. They should
  all be different views of the same source recipe.

## Practical First Build Plan

For a new low-poly asset family:

1. Define the silhouette in ASCII, SVG, or source contour JSON.
2. Name the major forms and plane breaks.
3. Compile a blockout mesh with `mesh_from_pydata`.
4. Add one-segment bevels only on named arrises.
5. Add weighted normals.
6. Render front, side, and 3/4 views.
7. Only then add detail parts, transition surfaces, or LOD variants.

The key rule is simple: model with fewer vertices by making the vertices more
intentional.

## Quality-Control Checklist

Before a low-poly asset is accepted:

- silhouette reads from front, side, and 3/4 view
- vertex and face counts are reported
- no accidental dense rings or hidden high-poly detail
- bounds match source dimensions
- origin and sockets match placement rules
- material regions are named
- bevels do not erase small details
- weighted normals are applied only after bevels
- flat/smooth policy is visible in the report
- LOD/collision needs are either generated or explicitly deferred
- ASCII or thumbnail preview can identify the asset before full Blender render

## Scripting Notes For Next Implementation

The next useful script improvement would be a `low_poly_part_v0` contract inside
the tool-plan compiler:

```text
low_poly_part_v0
  part_id
  generator_type
  source_dimensions_m
  vertices_m / faces
  material_region
  bevel_policy
  normal_policy
  validation_policy
```

Then the Blender adapter can stay simple:

```text
for each part:
  create mesh from vertices/faces
  assign material
  apply declared bevel
  apply declared normals
  validate counts/bounds
```

That keeps the design in recipes and compilers, while Blender remains the
executor and preview/export surface.
