# Elevation Transition Rules v0

## Source URLs

- https://www.redblobgames.com/grids/parts/
- https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-2-terrain-rendering-using-gpu-based-geometry
- https://transvoxel.org/
- https://docs.unity.cn/2020.3/Documentation/Manual/terrain-SetHeight.html
- https://edemaine.github.io/fold/
- https://github.com/elalish/manifold/wiki/Manifold-Library

## What Documentation Was Read

- Red Blob grid-parts edge, endpoint, and corner relationships.
- GPU Gems geometry clipmap transition-region concept.
- Transvoxel transition-cell concept for mismatched resolution boundaries.
- Unity terrain Set Height documentation for flattening plateaus, roads, platforms, and steps to a target height.
- FOLD overview for representing crease patterns as vertices, edges, faces, mountain-valley assignments, folded states, and user-defined mesh data.
- Manifold wiki for edge orientation and topology constraints.

## Relevant Technical Concepts

The compiler should classify elevation transitions before mesh emission. Do not infer ramps, cliffs, or terraces from triangle slope after the fact. A seam's role should be decided from:

- height delta between adjacent cell centers;
- height delta between shared corner vertices;
- movement tags;
- road/path tags;
- building pad tags;
- explicit cliff/ledge/fold tags;
- map boundary status.

Fold-inspired terrain is best treated as a crease graph:

- vertices: center, corners, and optional edge midpoints;
- edges: radial crease lines from center to boundary samples and seam edges between boundary samples;
- faces: triangles between crease edges;
- crease type: smooth, mountain, valley, hard step, cliff, riser, road blend, pad boundary.

The FOLD format is not a v0 dependency. Its useful concept is that a foldable surface needs explicit vertices, edges, faces, and edge properties. For this project, edge properties should live in seam/fold policy records.

## Relevant Data Fields, API Fields, And Formulas

Recommended transition thresholds:

```json
{
  "height_epsilon_m": 0.001,
  "flat_delta_max_m": 0.05,
  "walkable_slope_delta_max_m": 0.35,
  "step_delta_max_m": 0.75,
  "cliff_delta_min_m": 1.25,
  "terrace_preferred_increment_m": 0.5
}
```

These values are starting test parameters, not structural or production guidance.

Height delta:

```text
height_delta = abs(center_height_a - center_height_b)
```

Suggested v0 classification:

```text
if boundary:
  chunk_boundary
else if explicit cliff tag or height_delta >= cliff_delta_min:
  cliff_drop
else if road tag crosses edge and height_delta <= walkable_slope_delta_max:
  road_blend
else if building pad boundary:
  building_seam
else if height_delta <= flat_delta_max:
  shared_surface
else if height_delta <= walkable_slope_delta_max:
  smooth_slope
else if height_delta <= step_delta_max:
  hard_step
else:
  terrace_or_cliff_candidate
```

Shared corner height v0:

```text
corner_height = policy_weighted_average(incident_cell_center_heights, overrides)
```

Shared edge midpoint height v0:

```text
if edge has road override:
  midpoint_height = road_profile_height_at_edge
else if edge has building pad override:
  midpoint_height = pad_boundary_height
else if seam policy is shared_surface:
  midpoint_height = average(two corner heights)
else if seam policy is smooth_slope:
  midpoint_height = average(adjacent center heights and edge corner heights)
else if seam policy is hard_step or cliff_drop:
  midpoint_height = lower_or_upper_surface_policy_height
else:
  midpoint_height = average(incident cell heights)
```

For crack-free top surfaces, both cells must read the same midpoint vertex id and final height.

## Minimal v0 Subset For Our Engine

Start with five transition types:

- `shared_surface`: small/no delta.
- `smooth_slope`: walkable slope across shared top vertices.
- `hard_step`: small ledge/riser, movement with connector or cost.
- `cliff_drop`: blocked steep transition.
- `chunk_boundary`: map edge side face/skirt.

Roads and building pads should be overrides on height solving:

- road can flatten or smooth a line of midpoints and centers;
- building pad can lock center/corner/midpoint heights within a footprint;
- both must still emit shared seam vertices.

## Direct Project Mapping

The existing contracts already list `edge_types` such as `flat`, `step_up`, `step_down`, `ledge`, `cliff`, `ramp_candidate`, `structure_edge`, and `boundary`. The v0 compiler should map those to seam policies before building faces.

Recommended mapping:

```text
flat -> shared_surface
step_up/step_down -> hard_step unless route smoothing overrides
ledge -> hard_step or cliff_drop depending height_delta
cliff -> cliff_drop
ramp_candidate -> smooth_slope or road_blend
structure_edge -> building_seam/foundation_snap
boundary -> chunk_boundary
```

## Deferred Parts

- Physically accurate origami simulation.
- Fold flatness checks such as Kawasaki/Maekawa conditions.
- Multiple terraces inside one edge.
- Procedural retaining walls.
- Spline road cuts with dense inserted samples.
- Erosion-aware cliff/road blending.

## Risks And Ambiguity

- "One final height per shared vertex" prevents cracks but can visually soften cliffs unless side geometry and normals are handled carefully.
- If a hard step needs truly separate top heights at the same x/y, that is no longer a single heightfield seam. v0 should model that as side/riser geometry under an explicit seam policy rather than duplicating top seam vertices silently.
- Road and pad overrides can conflict. Building pads should generally win inside the pad footprint; roads should connect to pad boundary sockets.

## Build Dex Implementation Notes

- Do classification first, height solve second, face emission third.
- Keep the threshold values configurable in a recipe or compiler constants file.
- Emit warnings for ambiguous deltas near thresholds.
- Store the `height_basis` for every shared vertex so test failures can be traced.
- In the first proof, use exaggerated colors/materials for policies in debug output, but this packet does not create those assets.

