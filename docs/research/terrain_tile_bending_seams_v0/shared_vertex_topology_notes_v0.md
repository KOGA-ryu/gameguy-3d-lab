# Shared Vertex Topology Notes v0

## Source URLs

- https://www.redblobgames.com/grids/parts/
- https://www.redblobgames.com/grids/hexagons/
- https://catlikecoding.com/unity/tutorials/procedural-meshes/modified-grid/
- https://docs.unity.cn/550/Documentation/Manual/AnatomyofaMesh.html
- https://docs.blender.org/api/current/bpy.types.Mesh.html
- https://github.com/elalish/manifold/wiki/Manifold-Library

## What Documentation Was Read

- Red Blob grid-parts relationships for hex faces, edges, vertices, borders, corners, joins, endpoints, touches, and adjacent vertices.
- Red Blob main hex guide for axial/cube coordinate handling.
- Catlike Coding shared-grid mesh tutorial for vertex-primary grid generation and triangle indices over shared vertices.
- Unity mesh anatomy documentation for vertex arrays, triangle index arrays, vertex reuse, and normal implications.
- Blender Mesh API summary for mesh arrays and validation.
- Manifold wiki for topological manifoldness constraints and edge pairing rules.

## Relevant Technical Concepts

Red Blob's grid-parts page separates a grid into faces, edges, and vertices. For hex grids:

- A hex face has six bordering edges.
- A hex face has six corners.
- An interior edge joins two hex faces.
- An interior corner touches three hex faces.
- Edges can be shared between adjacent hexes.
- Vertices can be shared by the cells that meet at that point.

Catlike Coding's shared grid example changes the generation approach from "quad owns vertices" to "vertices are primary." That is the key idea for this project: terrain cells should reference shared vertex ids instead of owning private copies of their border vertices.

Unity's mesh documentation confirms the standard indexed mesh model: vertices live in one array and triangles are integer indices into that array. It also notes that shared vertices imply smooth surfaces for normal calculation, while doubled vertices create crisp edges. For this project, that means topology sharing and render-normal strategy must be separated:

- Topology sharing prevents cracks.
- Normal duplication or custom normals can still create visual hard edges later.

Manifold's wiki gives a stricter closed-solid rule: every triangle edge in a manifold solid is paired with exactly one opposite-oriented edge. Terrain heightfields are usually open surfaces, so v0 terrain top surfaces will not be closed solids by themselves. But the rule is still useful for validation of seam edges:

- Two neighboring top triangles may share an edge.
- Boundary, cliff, and riser edges must be intentionally unpaired or paired with side geometry.
- Accidental open seam edges between neighboring cells are errors.

## Relevant Data Fields, API Fields, And Formulas

Recommended v0 vertex record:

```json
{
  "vertex_id": "corner:cells:q0_r0_s0|q1_r1_s1|q2_r2_s2",
  "vertex_kind": "center | corner | edge_midpoint",
  "world_x": 0.0,
  "world_y": 0.0,
  "height_z": 0.0,
  "incident_cell_ids": [],
  "incident_edge_ids": [],
  "height_basis": "cell_center | averaged_incident_cells | road_override | pad_override | boundary_rule",
  "seam_locked": true
}
```

Recommended v0 edge midpoint record:

```json
{
  "vertex_id": "edge_midpoint:cell_a|cell_b",
  "vertex_kind": "edge_midpoint",
  "edge_id": "edge:cell_a|cell_b",
  "world_x": 0.0,
  "world_y": 0.0,
  "height_z": 0.0,
  "incident_cell_ids": ["cell_a", "cell_b"],
  "height_basis": "edge_policy_solver"
}
```

For boundary edges:

```text
edge_id = edge_boundary:<cell_id>:<side_index>
edge_midpoint_id = edge_midpoint_boundary:<cell_id>:<side_index>
```

For interior edges:

```text
edge_id = edge:<min_cell_id>|<max_cell_id>
edge_midpoint_id = edge_midpoint:<min_cell_id>|<max_cell_id>
```

For interior corners:

```text
corner_id = corner:cells:<sorted incident cell ids>
```

For boundary corners, where fewer than three incident cells exist:

```text
corner_id = corner_boundary:<rounded_world_x>:<rounded_world_y>:<sorted incident cell ids>
```

Use exact integer or rational coordinate derivation where possible. If a rounded world key is required, quantize to a deterministic grid and validate no two intended distinct corners collapse.

## Minimal v0 Subset For Our Engine

Use one global vertex registry per terrain chunk or map cube:

- Center vertices are private to a cell.
- Corner vertices are shared by all incident cells.
- Edge midpoint vertices are shared by the two incident cells.
- Boundary corners and boundary midpoints are owned by the boundary cell side.
- Chunk seam vertices must use a deterministic cross-chunk key if adjacent chunks are compiled separately.

For the current 32x32x8 proof, the simplest path is one map-level registry. Cross-chunk stitching can be deferred until terrain chunks are compiled independently.

## Direct Project Mapping

The existing `hex_plot_vertex_graph_v0` contract already names these ideas:

- `corner_vertices`
- `corner_vertex_ids`
- `corner_heights`
- `edges`
- `mesh_plan`
- `shared_corner_height_is_averaged_from_adjacent_cells_v0`
- `hard_seams_are_recorded_not_split_v0`

This packet extends that direction with optional `edge_midpoint_vertex_ids` and a stricter "no duplicate seam vertices" rule.

## Deferred Parts

- Render-vertex duplication for UV seams.
- Render-vertex duplication for hard normals while preserving topology ids.
- Half-edge mesh storage.
- Full manifold solid construction for terrain plus underside.
- Floating origin or world streaming chunk keys.
- Multi-resolution chunk boundaries.

## Risks And Ambiguity

- A vertex can be topologically shared but still need duplicate render attributes later. Treat topology ids as canonical and render buffer vertices as derived.
- Averaging incident cell heights can erase intentional cliffs. The height solver must obey seam policy before applying smoothing.
- Chunk-local compilation can reintroduce cracks unless boundary vertex ids and heights are generated from a shared authority.

## Build Dex Implementation Notes

- Create `corner_registry` and `edge_midpoint_registry` before face emission.
- Never create a seam vertex by local side index alone for an interior edge.
- Attach every top face edge to two facts: the vertex ids at its endpoints and the owning terrain policy.
- Add a debug validation that groups vertices by world x/y and reports duplicates with different ids or different heights.

