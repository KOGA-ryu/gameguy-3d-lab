# Hex Radial Subdivision Notes v0

## Source URLs

- https://www.redblobgames.com/grids/hexagons/
- https://www.redblobgames.com/grids/hexagons/implementation.html
- https://www.redblobgames.com/grids/parts/
- https://wikis.khronos.org/opengl/Primitive
- https://docs.blender.org/api/current/bpy.types.Mesh.html

## What Documentation Was Read

- Red Blob hex grid guide sections on axial/cube coordinates, neighbors, distances, hex-to-pixel, pixel-to-hex, map storage, and corners.
- Red Blob implementation section for `hex_corner_offset()` and `polygon_corners()`.
- Red Blob grid-parts page for hex faces, edges, vertices, border/corner relationships, and the idea that hex vertices and edges can be shared between adjacent cells.
- Khronos/OpenGL primitive documentation for `GL_TRIANGLE_FAN` behavior.
- Blender Mesh API summary for vertex arrays, edge arrays, loop/polygon representation, `from_pydata`, `validate`, and `update`.

## Relevant Technical Concepts

Hex cells are face-centered tiles. For drawing, Red Blob calculates a hex center from the hex coordinate, then calculates six corner offsets around that center. The implementation page gives the core rule:

- The six corner angles are spaced by 60 degrees.
- Flat-top corners start at 0 degrees.
- Pointy-top corners start at 30 degrees.
- `hex_corner_offset(layout, corner)` returns the x/y offset for one corner.
- `polygon_corners(layout, h)` adds six offsets to the cell center.

A triangle fan is the standard representation for subdividing a convex polygon from one fixed vertex to adjacent boundary vertex pairs. For a hex with center `C` and ordered corners `K0..K5`, the simple fan is:

```text
(C, K0, K1)
(C, K1, K2)
(C, K2, K3)
(C, K3, K4)
(C, K4, K5)
(C, K5, K0)
```

If each edge has a midpoint `M0..M5`, where `Mi` lies between `Ki` and `K(i+1 mod 6)`, the midpoint fan is:

```text
(C, K0, M0)
(C, M0, K1)
(C, K1, M1)
(C, M1, K2)
(C, K2, M2)
(C, M2, K3)
(C, K3, M3)
(C, M3, K4)
(C, K4, M4)
(C, M4, K5)
(C, K5, M5)
(C, M5, K0)
```

The midpoint fan gives one extra vertex per boundary edge. That makes it possible to bend a cell by raising or lowering an edge line without pulling the whole corner fan into a single steep triangle.

## Relevant Data Fields, API Fields, And Formulas

Recommended local cell fields:

```json
{
  "cell_id": "q_r_s",
  "q": 0,
  "r": 0,
  "s": 0,
  "center_vertex_id": "center:0:0:0",
  "corner_vertex_ids": ["... six ids ..."],
  "edge_midpoint_vertex_ids": ["... six ids or null ..."],
  "topology_role": "terrain | road | building_pad | cliff | boundary"
}
```

Corner position formula from Red Blob implementation, adapted to project naming:

```text
angle = 2*pi*(start_angle + corner_index)/6
corner_x = center_x + radius_x*cos(angle)
corner_y = center_y + radius_y*sin(angle)
```

For pointy-top hexes:

```text
start_angle = 0.5
corner angles = 30, 90, 150, 210, 270, 330 degrees
```

For flat-top hexes:

```text
start_angle = 0.0
corner angles = 0, 60, 120, 180, 240, 300 degrees
```

Edge midpoint formula:

```text
M_i.xy = (K_i.xy + K_next.xy) / 2
M_i.z = solved shared midpoint height
```

Face winding must be consistent across all top faces. Pick one winding for upward normals and use it everywhere. In Blender, faces can be passed as index tuples through `Mesh.from_pydata(vertices, edges, faces)`, then validated and updated.

## Minimal v0 Subset For Our Engine

Use pointy-top or flat-top consistently with the current map compiler. The research does not require changing the coordinate system. Existing contracts already use `q`, `r`, `s` cube/axial coordinates, so v0 should keep that.

Required v0 top mesh:

- Center vertex per hex.
- Six corner vertices per hex, referenced from a global corner registry.
- Optional six edge midpoint vertices per hex, referenced from a global edge registry.
- Six top triangles without midpoints, or twelve top triangles with midpoints.
- One material slot or surface tag per triangle group.

Recommended for the bending proof: use midpoints and emit twelve triangles, because the extra boundary samples make road, terrace, and slope rules easier to express without changing corner sharing.

## Direct Project Mapping

- `contracts/hex_terrain_fold_recipe_v0.json`: already emits per-cell final heights and six edge profiles.
- `contracts/hex_plot_vertex_graph_v0.json`: already requires six corner vertices and says corner vertices are shared by world x/y.
- `contracts/seam_policy_v0.json`: already separates shared surface, split riser, fold-meet-halfway, cliff, boundary skirt, foundation snap, and road blend concepts.

The new research packet recommends making the mesh compiler consume a global vertex graph before emitting faces. The existing proof scripts can keep their output lane unchanged, but Build Dex should derive mesh vertex arrays from the graph rather than creating each hex as an isolated mesh.

## Deferred Parts

- Adaptive triangulation inside a hex beyond six midpoints.
- Per-edge multiple samples for curved roads.
- Arbitrary polygon clipping for roads and building pads.
- LOD transition rings.
- GPU-driven height displacement.
- Non-heightfield overhangs, arches, caves, or voxel terrain.

## Risks And Ambiguity

- The current repo may have mixed flat-top and pointy-top assumptions in older proof scripts. The compiler must declare orientation once and run a visual/debug validation for corner order.
- Center vertices are not shared. That is intentional: the center belongs to one cell and carries that cell's local plateau/slope behavior.
- Corner and midpoint vertices should share position and height. If UVs or normals need hard discontinuities later, duplicate render vertices may be generated after the topology pass, but the seam topology must remain canonical.

## Build Dex Implementation Notes

- Build the global vertex registry first, then build faces by index.
- Do not compute corner heights independently per cell.
- Do not emit isolated per-hex top meshes if the cells are neighbors.
- Keep seam facts separate from top surface triangles.
- Use debug exports that list vertex ids, owners, final height, and all incident cells before any Blender proof render.

