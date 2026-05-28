# Implementation Recommendation v0

## Source URLs

- https://www.redblobgames.com/grids/hexagons/
- https://www.redblobgames.com/grids/hexagons/implementation.html
- https://www.redblobgames.com/grids/parts/
- https://wikis.khronos.org/opengl/Primitive
- https://docs.unity.cn/550/Documentation/Manual/AnatomyofaMesh.html
- https://catlikecoding.com/unity/tutorials/procedural-meshes/modified-grid/
- https://docs.blender.org/api/current/bpy.types.Mesh.html
- https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-2-terrain-rendering-using-gpu-based-geometry
- https://transvoxel.org/
- https://edemaine.github.io/fold/
- https://github.com/elalish/manifold/wiki/Manifold-Library

## What Documentation Was Read

This recommendation is derived from the full packet sources:

- Red Blob for hex coordinates, neighbors, corner generation, and face/edge/vertex relationships.
- Khronos/OpenGL for triangle fan semantics.
- Unity and Catlike Coding for indexed shared-vertex mesh construction.
- Blender API for eventual proof renderer mesh array creation and validation.
- GPU Gems and Transvoxel for crack prevention at terrain seams and LOD boundaries.
- FOLD for crease graph vocabulary.
- Manifold for topology validation concepts.

## Exact v0 Vertex Model

Use a global top-surface vertex registry per compiled map cube.

```json
{
  "vertex_id": "string",
  "vertex_kind": "center | corner | edge_midpoint",
  "world_x": "number",
  "world_y": "number",
  "height_z": "number",
  "incident_cell_ids": ["string"],
  "incident_edge_ids": ["string"],
  "height_basis": "cell_center | averaged_incident_cells | edge_policy_solver | road_override | pad_override | boundary_rule",
  "constraint_ids": ["string"],
  "seam_locked": true
}
```

Rules:

- Center vertices are private to one cell.
- Corner vertices are shared by all cells touching that corner.
- Edge midpoint vertices are shared by both cells touching that edge.
- Boundary corner and midpoint vertices are shared only by incident in-map cells.
- No two top-surface vertices may have the same intended world x/y and different ids unless explicitly marked as side/riser render vertices outside the top registry.

Recommended ids:

```text
center:<q>:<r>:<s>
edge:<min_cell_id>|<max_cell_id>
edge_boundary:<cell_id>:<side_index>
edge_midpoint:<min_cell_id>|<max_cell_id>
edge_midpoint_boundary:<cell_id>:<side_index>
corner:cells:<sorted_incident_cell_ids>
corner_boundary:<quantized_world_x>:<quantized_world_y>:<sorted_incident_cell_ids>
```

## Exact v0 Face Model

Use indexed triangle faces.

```json
{
  "face_id": "string",
  "face_kind": "top_triangle | riser_triangle | cliff_triangle | boundary_skirt_triangle",
  "vertex_ids": ["v0", "v1", "v2"],
  "cell_id": "string",
  "edge_id": "string_or_null",
  "seam_policy": "string_or_null",
  "surface_tags": ["terrain"],
  "winding": "project_standard_upward"
}
```

No-midpoint top face pattern:

```text
for i in 0..5:
  triangle = (center, corner[i], corner[(i+1) mod 6])
```

Midpoint top face pattern:

```text
for i in 0..5:
  triangle_a = (center, corner[i], midpoint[i])
  triangle_b = (center, midpoint[i], corner[(i+1) mod 6])
```

Recommended v0 proof uses midpoints and therefore 12 top triangles per hex.

## Exact v0 Seam Ownership Rule

Interior edge ownership:

```text
edge owner = canonical undirected pair sorted by cell_id
edge_id = edge:<min_cell_id>|<max_cell_id>
edge_midpoint_id = edge_midpoint:<min_cell_id>|<max_cell_id>
```

Interior corner ownership:

```text
corner owner = canonical sorted set of incident cell ids touching the corner
corner_id = corner:cells:<sorted_incident_cell_ids>
```

Boundary edge ownership:

```text
edge_id = edge_boundary:<cell_id>:<side_index>
edge_midpoint_id = edge_midpoint_boundary:<cell_id>:<side_index>
```

Boundary corner ownership:

```text
corner_id = corner_boundary:<quantized_world_x>:<quantized_world_y>:<sorted_incident_cell_ids>
```

If chunks are compiled independently later, replace local boundary ownership with a cross-chunk coordinate key. For v0, compile the whole 32x32x8 proof map with one registry.

## Exact v0 Height Assignment Rule

Every shared top-surface vertex gets exactly one `height_z` before face emission.

Height priority:

```text
1. hard map z bounds
2. explicit void/cliff/boundary constraints
3. building pad lock
4. road/path lock
5. road/pad falloff
6. seam policy solver
7. averaged incident terrain height
```

Center vertex:

```text
height_z = cell.final_height after base heightfield + fold offsets + pad/road override
```

Corner vertex:

```text
if locked by pad:
  height_z = pad height
else if locked by road/path constraint:
  height_z = road/path height
else:
  height_z = weighted average of incident cell final heights, excluding blocked voids
```

Edge midpoint:

```text
if locked by road crossing:
  height_z = road crossing height
else if seam_policy in [shared_surface, smooth_slope, road_blend]:
  height_z = average(edge corner heights and adjacent center heights)
else if seam_policy in [hard_step, cliff_drop]:
  height_z = seam_policy selected top height, usually lower walkable side or explicit ledge height
else if boundary:
  height_z = average(boundary edge corner heights and cell center height)
```

No cell may overwrite a shared corner or midpoint after it has been solved. If a later constraint wants a different value, the solver must rerun or report a conflict.

## Exact v0 Validation Checks

JSON/data checks:

- every cell has `q + r + s == 0`;
- every cell has one center id, six corner ids, and six midpoint ids when midpoint mode is enabled;
- every face references existing vertex ids;
- every shared vertex has one numeric `height_z`;
- every vertex has `height_basis`;
- all heights fit inside the map cube z bounds.

Topology checks:

- every interior edge has exactly two incident cells;
- both incident cells reference the same edge midpoint id;
- both incident cells reference the same two corner ids for that edge;
- no duplicate top-surface vertex ids occupy the same quantized x/y unless intentionally allowed by side geometry;
- no duplicate top-surface x/y has conflicting height;
- top face winding is consistent;
- no zero-area top triangle above `height_epsilon_m`;
- no T-junctions in v0: every interior edge has the same subdivision count on both sides.

Seam checks:

- every edge has a seam policy;
- `shared_surface` and `smooth_slope` emit no vertical seam wall;
- `hard_step` emits a riser or a connector fact;
- `cliff_drop` emits cliff side geometry or a blocked edge fact;
- `chunk_boundary` emits boundary side/skirt geometry or is marked intentionally open;
- road edges have movement tags;
- building pad edges have structure/foundation tags.

Debug checks:

- print a seam table sorted by `edge_id`;
- print duplicate-world-position groups;
- print vertices with multiple conflicting constraints;
- print edge policies with missing side geometry;
- print triangles with unexpected normal direction.

## Recommended First Test Scene

Use one compact 7-cell hex cluster:

```text
center cell at height 1.0
east neighbor at height 1.0 shared_surface
northeast neighbor at height 1.25 smooth_slope
northwest neighbor at height 1.5 road_blend crossing the shared edge
west neighbor at height 2.0 hard_step
southwest neighbor at height 3.0 cliff_drop
southeast neighbor at height 1.0 building_pad/foundation edge
```

Required proof assertions:

- center cell emits 12 top triangles in midpoint mode;
- all six edge midpoints exist;
- all six corners exist;
- shared_surface and smooth_slope have no duplicate seam vertices;
- hard_step and cliff_drop are explicit seam policies;
- road edge midpoint height is controlled by the road constraint;
- building pad vertices inside the pad are equal height;
- no interior seam has a hole.

## Deferred Complexities

- LOD and unequal edge subdivision.
- Stitch strips, skirts except outer boundary, and geometry clipmap transition bands.
- Transvoxel or voxel terrain.
- Arbitrary road splines with inserted samples.
- Full constrained Delaunay or polygon clipping.
- Physically accurate origami fold simulation.
- Render-attribute duplication for UV/hard-normal seams.
- Chunk streaming and cross-chunk vertex authorities.
- Full closed manifold terrain solids.

## Build Dex Implementation Notes

The simplest implementation should be a compiler pass sequence:

```text
cells -> edge/corner incidence -> global vertex registry -> constraint solve -> seam policy classify -> face emit -> validation report
```

Do not start with Blender. Blender should only consume the final vertices/faces after the data validation pass succeeds.

