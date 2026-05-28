# Manifold Full Notes v0

## 1. Source URLs

- https://github.com/elalish/manifold
- https://github.com/elalish/manifold/wiki/Manifold-Library
- https://manifoldcad.org/docs/html/
- https://manifoldcad.org/docs/html/classmanifold_1_1_manifold.html
- https://manifoldcad.org/docs/jsuser/classes/Manifold.html

## 2. What Documentation Was Read

- Manifold repository README for goals, manifold mesh requirements, booleans, mesh IO notes, bindings, dependencies, and build flags.
- Manifold wiki page for manifoldness and topology/geometry distinctions.
- C++ and JS user documentation for `Manifold` class API, boolean operations, constructors, transforms, and status/measurement methods.

## 3. Relevant Technical Concepts

- Manifold focuses on robust operations on manifold triangle meshes representing solid objects.
- A manifold mesh is important when a boundary must define a solid reliably.
- Topology is treated separately from geometry: topology is exact index/connectivity; geometry is floating-point positions/properties.
- Robust boolean operations are the main value: union, difference, intersection, split, trim by plane.
- Inputs should be manifold; imported non-manifold meshes can fail or require repair.
- Manifold can track vertex properties, material/property boundaries, original IDs, and surface relationships.
- For our v0, Manifold is a future option, not a dependency.

## 4. Relevant Data Fields / API Fields / Formulas

### Manifold Class Information

Useful API names:

```text
Status()
IsEmpty()
NumVert()
NumEdge()
NumTri()
NumProp()
NumPropVert()
BoundingBox()
Genus()
GetTolerance()
SurfaceArea()
Volume()
MinGap(other, searchLength)
RayCast(origin, endpoint)
OriginalID()
AsOriginal()
```

### Transforms

```text
Translate(vec3)
Scale(vec3)
Rotate(xDegrees, yDegrees=0, zDegrees=0)
Mirror(vec3)
Transform(mat3x4)
Warp(function)
SetTolerance(double)
Simplify(tolerance=0)
```

### Booleans

C++ API names:

```text
Boolean(second, OpType)
operator+ / operator+= : union
operator- / operator-= : difference
operator^ / operator^= : intersection
Split(cutter)
SplitByPlane(normal, originOffset)
TrimByPlane(normal, originOffset)
MinkowskiSum(other)
MinkowskiDifference(other)
BatchBoolean(manifolds, OpType)
```

JS/TS API names:

```text
add(other)
subtract(other)
intersect(other)
split(cutter)
splitByPlane(normal, originOffset)
trimByPlane(normal, originOffset)
minkowskiSum(other)
minkowskiDifference(other)
static union(a, b) / union(manifolds)
static difference(a, b) / difference(manifolds)
static intersection(a, b) / intersection(manifolds)
```

### Constructors / Creation Concepts

Docs list constructors such as:

```text
cube(size, center)
cylinder(...)
sphere(...)
tetrahedron(...)
extrude(...)
revolve(...)
levelSet(...)
ofMesh(...)
```

### OpType

```text
OpType.Add       -> union
OpType.Subtract  -> difference
OpType.Intersect -> intersection
```

## 5. Minimal v0 Subset For Our Engine

Do not use Manifold in v0. Add only a future-readiness note:

```json
{
  "boolean_backend": "none_v0",
  "future_options": ["manifold", "cadquery", "blender_boolean"],
  "requires_manifold_input": true,
  "fallback": "avoid_booleans_generate_clean_mesh_arrays"
}
```

## 6. Direct Project Mapping

- `32x32x8 map cube`: not needed.
- `hex/elevation cells`: not needed for cell math.
- `terrain mesh compiler`: relevant only if boolean clipping/merging becomes necessary.
- `visible face meshing`: generate clean faces directly; avoid booleans.
- `seam/fold grammar`: not needed.
- `road/path layer`: future boolean cuts/embossing could use Manifold, deferred.
- `building plot layer`: future solid unions/subtractions for buildings may benefit.
- `asset placement layer`: future robust asset booleans may benefit.
- `Blender proof renderer`: Blender remains v0 proof renderer.
- `future AI affordance graph`: no direct need.

## 7. Deferred Parts

- Manifold dependency and bindings.
- Boolean CSG pipeline.
- Mesh repair.
- 3MF/glTF manifold metadata.
- SDF/level-set generation.
- Material/property propagation across booleans.

## 8. Risks / Ambiguity

- Manifold expects manifold inputs; our early Blender-generated debug meshes may not be suitable.
- Robust booleans do not remove the need for good asset grammar.
- Adding a boolean backend changes validation requirements substantially.
- STL can lose topology; avoid using STL as source of truth.

## 9. Build Dex Implementation Notes

- In v0, generate terrain/building meshes directly without boolean operations.
- If Blender booleans become fragile, evaluate Manifold as a separate backend in a dedicated factory lane.
- Preserve topology metadata: original face ids, material ids, semantic tags. These are needed if a future boolean backend must map surfaces back to gameplay roles.

