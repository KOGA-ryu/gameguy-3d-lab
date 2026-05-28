# Blender Mesh API Full Notes v0

## 1. Source URLs

- https://docs.blender.org/api/current/bpy.types.Mesh.html
- https://docs.blender.org/api/current/bmesh.html
- https://docs.blender.org/api/current/bmesh.ops.html
- https://docs.blender.org/api/current/bpy.types.Curve.html
- https://docs.blender.org/api/current/bpy.ops.object.html
- https://docs.blender.org/api/current/bpy.ops.mesh.html

## 2. What Documentation Was Read

- Blender `bpy.types.Mesh` API: mesh data, `from_pydata`, validation, update, transform, normals.
- Blender `bmesh` and `bmesh.ops`: editable mesh module and operators such as create cube, extrude face region, recalc face normals.
- Blender `bpy.types.Curve`: curve dimensions, bevel/extrude/fill/splines/resolution.
- Blender object and mesh operators: join, origin, selection, primitive add, extrusion, normals, triangulation, cleanup.

## 3. Relevant Technical Concepts

- For generated proof meshes, direct mesh creation from vertex/edge/face arrays is simpler and more deterministic than invoking edit-mode operators.
- `bpy.data.meshes.new()` creates mesh data; `mesh.from_pydata(vertices, edges, faces)` fills it.
- `mesh.validate()` can correct/remove invalid geometry and returns whether corrections occurred.
- `mesh.update(calc_edges=True)` updates mesh data and can force edge recalculation.
- `bpy.data.objects.new(name, mesh)` creates an object from mesh data.
- Link objects into collections using `collection.objects.link(obj)`.
- Materials attach to `mesh.materials`; polygons can assign `material_index`.
- Normals depend on face winding. Use consistent winding and optionally `mesh.flip_normals()` or BMesh normal recalculation.
- BMesh is useful when incremental topology editing is needed; v0 can avoid it for terrain chunks by generating final arrays.
- Curves are useful for roads, trim, rails, ribs, and proof splines; bevel depth turns a curve into visible tube-like geometry.

## 4. Relevant Data Fields / API Fields / Formulas

### Direct Mesh Creation

```python
mesh = bpy.data.meshes.new("terrain_mesh")
mesh.from_pydata(vertices, edges, faces)
mesh.validate(clean_customdata=True)
mesh.update(calc_edges=True)
obj = bpy.data.objects.new("terrain", mesh)
bpy.context.collection.objects.link(obj)
```

`vertices`:

```text
[(x, y, z), ...]
```

`edges`:

```text
[(vertex_index_a, vertex_index_b), ...]
```

Can be empty if faces fully imply edges and `calc_edges=True`.

`faces`:

```text
[(v0, v1, v2), (v0, v1, v2, v3), ...]
```

Use triangles/quads for predictable proof rendering. N-gons are acceptable in Blender but harder to audit.

### Mesh Methods

```text
Mesh.from_pydata(vertices, edges, faces, shade_flat=True)
Mesh.validate(verbose=False, clean_customdata=True)
Mesh.update(calc_edges=False, calc_edges_loose=False)
Mesh.transform(matrix, shape_keys=False)
Mesh.flip_normals()
Mesh.clear_geometry()
Mesh.set_sharp_from_angle(angle=pi)
```

### Mesh Data Collections

Useful properties:

```text
mesh.vertices
mesh.edges
mesh.polygons
mesh.materials
polygon.material_index
polygon.use_smooth
```

### BMesh

Useful pattern:

```python
import bmesh
bm = bmesh.new()
bm.from_mesh(mesh)
# mutate bm.verts / bm.edges / bm.faces or run bmesh.ops
bm.to_mesh(mesh)
bm.free()
```

Useful BMesh ops:

```text
bmesh.ops.create_cube(bm, size=..., matrix=..., calc_uvs=False)
bmesh.ops.extrude_face_region(bm, geom=...)
bmesh.ops.recalc_face_normals(bm, faces=...)
bmesh.ops.triangulate(bm, faces=...)
bmesh.ops.bevel(...)
```

### Curve API

Important fields:

```text
Curve.dimensions: "2D" | "3D"
Curve.splines
Curve.bevel_depth
Curve.bevel_resolution
Curve.resolution_u
Curve.render_resolution_u
Curve.fill_mode
Curve.extrude
```

Road/path proof curve:

```python
curve = bpy.data.curves.new("road_centerline", "CURVE")
curve.dimensions = "3D"
curve.bevel_depth = 0.05
polyline = curve.splines.new("POLY")
polyline.points.add(len(points) - 1)
for p, (x, y, z) in zip(polyline.points, points):
    p.co = (x, y, z, 1.0)
obj = bpy.data.objects.new("road_centerline", curve)
```

### Object Operators

Use sparingly in v0:

```text
bpy.ops.object.select_all(action="DESELECT" | "SELECT")
bpy.ops.object.join()
bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN", center="MEDIAN")
bpy.ops.object.modifier_apply(modifier=...)
```

### Mesh Operators

Mostly deferred because they require mode/context:

```text
bpy.ops.mesh.primitive_cube_add(size=..., location=...)
bpy.ops.mesh.extrude_region(...)
bpy.ops.mesh.bevel(...)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.mesh.remove_doubles(threshold=...)
bpy.ops.mesh.quads_convert_to_tris(...)
```

## 5. Minimal v0 Subset For Our Engine

- Use `Mesh.from_pydata` for terrain/building proof meshes.
- Generate vertices/faces in Python from internal JSON.
- Call `mesh.validate()` and `mesh.update(calc_edges=True)`.
- Assign materials by semantic category: top, cliff, ledge, road, plot, socket, wall, hazard.
- Use collections:
  - `terrain`
  - `buildings`
  - `roads`
  - `sockets`
  - `debug`
- Use curves only for optional road/path proof overlays.
- Avoid edit-mode mesh operators in v0.

## 6. Direct Project Mapping

- `32x32x8 map cube`: create a transparent/debug bounding box if needed using mesh arrays, not booleans.
- `hex/elevation cells`: one top face per hex, vertical riser faces for exposed deltas.
- `terrain mesh compiler`: outputs arrays; Blender consumes arrays.
- `visible face meshing`: materialize only exposed/top faces and optionally hide internal faces.
- `seam/fold grammar`: color edge profiles in debug overlays.
- `road/path layer`: curves or thin mesh strips from path points.
- `building plot layer`: rectangle/footprint meshes at plot elevation.
- `asset placement layer`: small marker meshes or empties at sockets.
- `Blender proof renderer`: minimal render scene with camera/light/materials.
- `future AI affordance graph`: not Blender-owned; use debug markers if useful.

## 7. Deferred Parts

- Boolean-heavy modeling.
- Modifier stacks as required output.
- Geometry Nodes.
- BMesh incremental editing unless array generation becomes awkward.
- Export pipelines beyond proof images.
- Complex curve bevel/profile generation.

## 8. Risks / Ambiguity

- Blender operators are context-sensitive and can fail in background mode if mode/selection is wrong.
- Face winding must be consistent to avoid inverted normals.
- N-gons can hide triangulation problems; prefer triangles/quads.
- `mesh.validate()` correcting data is a warning signal; receipts should record correction status.
- World units must match repo `abstract_meter` assumptions.

## 9. Build Dex Implementation Notes

- Build a single utility: `make_mesh_object(name, vertices, faces, material_slots, polygon_material_indices, collection_name)`.
- Keep object origins meaningful: terrain chunk origin at map cube origin; assets at local footprint center unless recipe says otherwise.
- Do not join objects by default; separate collections improve auditability.
- Always write a proof receipt with counts: vertices, faces, materials, validation corrected flag, bounds.

