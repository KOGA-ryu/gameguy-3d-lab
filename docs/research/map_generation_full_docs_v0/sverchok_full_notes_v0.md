# Sverchok Full Notes v0

## 1. Source URLs

- https://sverchok.readthedocs.io/
- https://sverchok.readthedocs.io/en/latest/geometry.html
- https://sverchok.readthedocs.io/en/latest/nodes.html
- https://sverchok.readthedocs.io/en/stable/nodes/modifier_change/extrude_edges.html
- https://sverchok.readthedocs.io/en/latest/nodes/modifier_change/triangulate.html
- https://sverchok.readthedocs.io/en/latest/nodes/analyzers/mesh_select.html

## 2. What Documentation Was Read

- Main Sverchok documentation and node index.
- Geometry introduction for vertices, edges, polygons/faces, normals, transformations, and matrices.
- Node docs for mesh selection, edge extrusion, triangulation, subdivision, and mesh modifiers.

## 3. Relevant Technical Concepts

- Sverchok is a procedural node system for Blender with geometry represented as lists.
- Mesh data flow commonly passes `Vertices`, `Edges`, and `Faces/Polygons` lists between nodes.
- Vertices are coordinate triples.
- Edges are pairs of vertex indices.
- Polygons/faces are lists of three or more vertex indices.
- Nodes are grouped as generators, analyzers, transforms, list operations, modifiers, and outputs.
- Many operations are data-flow equivalents of operations we can implement in our factory scripts: generate, transform, select, extrude, triangulate, subdivide, join, and output.
- Selection masks are first-class outputs, useful for selecting vertices/edges/faces by side, normal, plane, cylinder, sphere, bounding box, etc.

## 4. Relevant Data Fields / API Fields / Formulas

### Core Mesh Lists

```text
Vertices:
  [(x, y, z), ...]

Edges:
  [[v0, v1], [v1, v2], ...]

Faces / Polygons:
  [[v0, v1, v2], [v3, v4, v5, v6], ...]
```

### Extrude Edges Node Inputs/Outputs

Inputs:

```text
Vertices
Edges
Polygons
ExtrudeEdges
Matrices
```

Outputs:

```text
Vertices
Edges
Polygons
NewVertices
NewEdges
NewFaces
```

Conceptual mapping: Build Dex can generate new vertices by applying transformation matrices to selected boundary edges, then create connecting faces.

### Triangulate Node Inputs/Outputs

Inputs:

```text
Vertices
Edges
Polygons
Mask
```

Parameters:

```text
Quads mode: Beauty | Fixed | Fixed Alternate | Shortest Diagonal
Ngon mode: Beauty | Scanfill
```

Outputs:

```text
Vertices
Edges
Polygons
NewEdges
NewPolys
```

### Mesh Select Concepts

Inputs:

```text
Vertices
Edges
Faces
Direction
Center
Percent
Radius
```

Outputs:

```text
VerticesMask
EdgesMask
FacesMask
```

Supported selection concepts include side, normal, plane, cylinder, sphere, and bounding box. For our factory, masks can drive visible-face extraction, cliff face selection, and semantic material assignment.

## 5. Minimal v0 Subset For Our Engine

Do not depend on Sverchok in v0. Copy the conceptual data-flow model:

```text
generator -> list transform -> selector/mask -> mesh operation -> validator -> output manifest
```

Use explicit arrays:

```json
{
  "vertices": [[0, 0, 0], [1, 0, 0], [1, 1, 0]],
  "edges": [[0, 1], [1, 2], [2, 0]],
  "faces": [[0, 1, 2]],
  "face_tags": ["top"]
}
```

## 6. Direct Project Mapping

- `32x32x8 map cube`: generator stage creates bounded cell list.
- `hex/elevation cells`: vertices/faces generated from cell arrays.
- `terrain mesh compiler`: list pipeline mirrors Sverchok mesh-list flow.
- `visible face meshing`: selection masks decide exposed faces.
- `seam/fold grammar`: masks select fold/edge classes for material/debug output.
- `road/path layer`: transform path polylines into strip meshes or curves.
- `building plot layer`: generate footprint faces and vertical walls from plot records.
- `asset placement layer`: socket markers are generated and transformed by local matrices.
- `Blender proof renderer`: final mesh arrays go to Blender.
- `future AI affordance graph`: masks/tags can become graph facts.

## 7. Deferred Parts

- Sverchok as a runtime or authoring dependency.
- Node graph serialization.
- Blender UI node setup.
- Full modifier parity.
- Live procedural editing.

## 8. Risks / Ambiguity

- Sverchok docs are for a Blender add-on; node names and availability can differ by version.
- Copying node dependency would complicate headless factory runs.
- Conceptual list flow is useful, but direct API dependency is unnecessary for v0.

## 9. Build Dex Implementation Notes

- Implement pure Python mesh-list helpers with names inspired by the data flow: `select_faces`, `extrude_edges`, `triangulate_faces`, `apply_transform`, `merge_meshes`.
- Keep every helper deterministic and receipt-friendly.
- Store masks and semantic tags alongside mesh arrays for debugability.

