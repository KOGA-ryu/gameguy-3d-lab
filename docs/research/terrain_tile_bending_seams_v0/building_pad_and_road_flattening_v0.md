# Building Pad And Road Flattening v0

## Source URLs

- https://docs.unity.cn/2020.3/Documentation/Manual/terrain-SetHeight.html
- https://www.redblobgames.com/grids/hexagons/
- https://www.redblobgames.com/grids/parts/
- https://catlikecoding.com/unity/tutorials/procedural-meshes/modified-grid/
- https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-2-terrain-rendering-using-gpu-based-geometry

## What Documentation Was Read

- Unity terrain Set Height documentation for setting an area to a specific height, flattening terrain tiles, and using set height for plateaus, roads, platforms, and steps.
- Red Blob hex grid guide for coordinate and neighbor relationships.
- Red Blob grid-parts page for edge and vertex relationships.
- Catlike Coding shared grid tutorial for vertex-primary terrain-like grids.
- GPU Gems geometry clipmap transition concepts for smooth changes between terrain levels.

## Relevant Technical Concepts

Unity's Set Height tool is useful as a conceptual reference: flattening is a height operation over terrain samples. It raises lower samples and lowers higher samples toward a target height. For this project, roads and building pads should be expressed as height-solver constraints over the hex vertex graph, not as separate meshes dropped onto terrain.

Roads and pads should not break shared topology:

- A road crossing an edge modifies center, corner, and/or midpoint heights through constraints.
- A building pad locks a footprint to a target height or small grade.
- Neighbor cells still share the same corner and midpoint vertex ids.
- The road/pad output should include semantic tags for movement and asset sockets.

## Relevant Data Fields, API Fields, And Formulas

Recommended flatten constraint:

```json
{
  "constraint_id": "road_main_01",
  "constraint_type": "road_centerline | building_pad | plateau | stair_socket",
  "affected_cell_ids": [],
  "affected_vertex_ids": [],
  "target_height_m": 1.5,
  "falloff_cells": 1,
  "strength": 1.0,
  "priority": 50,
  "semantic_tags": ["road", "walkable", "asset_socket"]
}
```

Height solve priority:

```text
1. map bounds and cube z limits
2. explicit cliff/void constraints
3. building pad interior lock
4. road/path centerline lock
5. pad/road falloff blend
6. base terrain/fold height
7. smoothing/averaging for ordinary shared corners
```

Building pad v0:

```text
for each vertex inside pad footprint:
  height = pad_target_height
for each vertex on pad boundary:
  height = blend(pad_target_height, terrain_height, boundary_falloff)
```

Road v0:

```text
for each road cell center or midpoint on path:
  height = sampled road profile height
for adjacent road shoulder vertices:
  height = blend(road_height, terrain_height, shoulder_falloff)
```

Avoid introducing new arbitrary points in v0. Use existing centers, corners, and edge midpoints.

## Minimal v0 Subset For Our Engine

Building pads:

- lock all center vertices in pad cells to one target height;
- lock all corner and midpoint vertices fully inside the pad to the same height;
- blend one ring outside the pad if needed;
- set `buildable=true` and emit `foundation_snap` or `building_seam` policies at boundaries.

Roads:

- route along hex center-to-center paths;
- set crossing edge midpoints to road height;
- blend adjacent corner heights only if they are not locked by pads or cliffs;
- classify road edges as `road_blend` where walkable.

## Direct Project Mapping

This maps to existing `structure_socket_tags`, `movement_tags`, and `edge_profiles`:

- road interior: `movement_tags=["walkable","road"]`
- road edge: `edge_profile="ramp_candidate"` or `road_join`
- pad interior: `structure_socket_tags=["building_pad","foundation"]`
- pad boundary: `edge_profile="structure_edge"` and seam policy `foundation_snap`

## Deferred Parts

- Curved road splines with inserted vertices.
- Road meshes floating over terrain.
- Retaining walls around pads.
- Exact polygon clipping against hexes.
- Drainage/erosion terrain reshaping.
- Smooth continuous grade optimization over long roads.

## Risks And Ambiguity

- Roads crossing steep cliffs should not silently flatten the cliff. The classifier should require explicit bridge, stair, or ramp intent.
- Building pads can erase terrain features if priority is too broad. Keep pad footprints explicit.
- If road and pad constraints overlap, the higher-priority semantic constraint must be recorded in each affected vertex.

## Build Dex Implementation Notes

- Treat roads/pads as solver constraints, not post-process mesh edits.
- Store `height_basis` and `constraint_id` on every affected vertex.
- Add a validation that all vertices inside a building pad are within `height_epsilon_m` of the pad height.
- Add a validation that road edge midpoints along a path differ from neighboring road midpoints by no more than the walkable slope threshold unless a step connector is explicitly emitted.

