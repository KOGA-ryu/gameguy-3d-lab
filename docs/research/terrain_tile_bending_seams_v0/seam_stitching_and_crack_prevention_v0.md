# Seam Stitching And Crack Prevention v0

## Source URLs

- https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-2-terrain-rendering-using-gpu-based-geometry
- https://transvoxel.org/
- https://tulrich.com/geekstuff/chunklod.html
- https://www.redblobgames.com/grids/parts/
- https://catlikecoding.com/unity/tutorials/procedural-meshes/modified-grid/
- https://docs.unity.cn/550/Documentation/Manual/AnatomyofaMesh.html
- https://github.com/elalish/manifold/wiki/Manifold-Library

## What Documentation Was Read

- GPU Gems 2 chapter on GPU-based geometry clipmaps, especially nested regular grids, elevation texture sampling, transition regions, watertight mesh concerns, and morphing to coarser levels.
- Transvoxel overview for multiresolution voxel terrain boundary cracks and transition-cell stitching.
- Thatcher Ulrich's Chunked LOD page for chunked terrain LOD, geomorphing, screen-space error, and hardware-friendly terrain batching.
- Red Blob grid-parts page for edge/vertex sharing.
- Catlike Coding shared grid notes for indexed shared-vertex generation.
- Unity mesh anatomy docs for indexed vertex/triangle representation.
- Manifold wiki for edge-pairing and topology robustness constraints.

## Relevant Technical Concepts

Terrain cracks usually come from one of these causes:

- Neighboring chunks compute different positions for what should be the same boundary vertex.
- Neighboring chunks compute different heights for what should be the same boundary sample.
- A high-resolution edge has more vertices than a low-resolution neighbor and the extra vertices are not constrained to the coarse edge.
- The renderer uses visually different normals/attributes across a boundary, which may look like a crack even if geometry is closed.
- Boundary skirts hide holes but do not solve topology.

Geometry clipmaps treat terrain as elevation samples over nested grids. Their crack prevention strategy is not "duplicate and hope"; it uses nested grids plus transition regions where fine geometry morphs toward coarser geometry. The important v0 lesson is that seams need an explicit transition rule, not independent mesh generation.

Transvoxel solves a harder voxel problem by inserting transition cells between different resolutions. It is not a v0 implementation target for hex heightfields, but the concept is relevant: mismatched resolution boundaries need generated connector geometry.

Chunked LOD systems often use geomorphing, skirts, or stitch strips. For this project, LOD is deferred, but the validation concepts carry over:

- boundary samples must be deterministic;
- adjacent patches must agree on endpoints;
- if one side has extra samples, they must lie on the lower-resolution edge or be connected by stitch faces.

## Relevant Data Fields, API Fields, And Formulas

Recommended seam record:

```json
{
  "edge_id": "edge:cell_a|cell_b",
  "cell_a": "cell_a",
  "cell_b": "cell_b",
  "side_a": 0,
  "side_b": 3,
  "corner_vertex_ids": ["corner_left", "corner_right"],
  "edge_midpoint_vertex_id": "edge_midpoint:cell_a|cell_b",
  "height_low": 0.0,
  "height_high": 1.0,
  "height_delta": 1.0,
  "seam_policy": "shared_surface | smooth_slope | hard_step | cliff_drop | terrace | road_blend | building_seam | chunk_boundary",
  "top_surface_shared": true
}
```

Recommended no-crack checks:

```text
For every interior edge:
  both adjacent cells reference the same left corner id
  both adjacent cells reference the same right corner id
  both adjacent cells reference the same edge midpoint id when midpoints are enabled
  each shared vertex has exactly one final height
  top faces do not leave an unmatched boundary edge unless the seam policy expects side geometry
```

LOD-derived deferred stitch rule:

```text
If side A has vertices [A0, A1, A2] and side B has vertices [B0, B1],
then A0 == B0, A2 == B1, and A1.height must lie on or be connected to segment B0-B1.
```

For v0, avoid this problem by making every hex edge use the same endpoint-plus-midpoint pattern.

## Minimal v0 Subset For Our Engine

No terrain LOD in v0. All neighboring hexes use the same edge subdivision count:

- no midpoint mode: both sides have two edge endpoints;
- midpoint mode: both sides have two endpoints plus one shared midpoint.

This removes T-junctions from the first implementation. The only remaining seam risk is duplicate vertices or mismatched heights.

## Direct Project Mapping

Existing `seam_policy_v0.json` already covers:

- `shared_surface`
- `split_riser`
- `fold_meet_halfway`
- `split_cliff`
- `chunk_skirt`
- `foundation_snap`
- `road_blend`
- `blocked_wall`

For the bending layer, map these to mesh behavior:

- `shared_surface`: top vertices shared, no side face.
- `smooth_slope`: top vertices shared, midpoint height blended, no side face.
- `hard_step`: top seam still references shared x/y endpoints, but vertical riser side faces are emitted from low/high duplicate vertical positions or from side-wall vertices.
- `cliff_drop`: same as hard step, but movement blocked and face treated as cliff wall.
- `fold_meet_halfway`: deferred unless the design explicitly needs two sloped panels meeting at a mid-edge crease.
- `chunk_boundary`: generate boundary skirt or vertical side to base plane.

## Deferred Parts

- Geometry clipmap transition regions.
- Transvoxel transition cells.
- T-junction repair for unequal edge subdivision.
- Runtime LOD morphing.
- Skirts as general crack hiding.
- Multi-resolution chunk streaming.

## Risks And Ambiguity

- A skirt can hide a crack but still leave invalid topological data. Use skirts only for map/chunk outer boundaries in v0.
- `fold_meet_halfway` can accidentally split shared seam topology if implemented with per-cell midpoint vertices. It must use one shared midpoint key or be deferred.
- LOD references use square grids or voxel grids. Their lesson is seam determinism, not direct algorithm copying into hex v0.

## Build Dex Implementation Notes

- Implement no LOD first.
- Require equal subdivision on both sides of every interior hex edge.
- Fail validation if an interior edge produces unpaired top boundary edges.
- Treat vertical cliff/riser faces as extra side geometry attached to a seam policy, not as separate top surfaces.
- Produce a seam debug table for every edge: vertex ids, heights, policy, incident cells, emitted face count.

