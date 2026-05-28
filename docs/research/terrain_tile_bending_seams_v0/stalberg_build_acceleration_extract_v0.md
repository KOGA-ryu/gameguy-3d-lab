# Stålberg Build Acceleration Extract v0

This is a build-facing extraction from Townscaper/Planet-style grid systems. It is not a clone plan, asset extraction, or visual reference packet. It captures technical patterns that reduce Build Dex decision time for terrain seams, elevation transitions, and authored procedural geometry.

## Source URLs

- https://www.boristhebrave.com/2022/12/18/how-does-planet-work/
- https://www.boristhebrave.com/docs/sylves/1/articles/tutorials/townscaper.html
- https://indiecade-europe.eu/en/programme/conferences
- https://github.com/pablogila/TileMapDual
- https://gamedev.net/forums/topic/712984-working-with-the-dual-graph-of-a-hex-grid/

## High-Value Extraction

### 1. Store Terrain Truth On Shared Vertices

In the Planet teardown, edits snap to vertices and store two hidden variables per vertex: height and terrain type. Tiles touching that vertex are recalculated from those corner states.

Direct project shortcut:

```text
Do not start by solving each hex independently.
Solve shared corner and edge-midpoint states first.
Cells consume the solved shared states.
```

Build impact:

- Fewer crack bugs.
- Fewer per-cell special cases.
- Easier debug tables: every visible seam can point back to one canonical vertex/edge record.

Recommended v0 data authority:

```json
{
  "shared_vertex_state": {
    "vertex_id": "corner:...",
    "height_band": 2,
    "height_m": 1.0,
    "terrain_type": "grass | stone | road | pad | water",
    "locks": ["road_centerline", "building_pad"],
    "incident_cells": []
  }
}
```

### 2. Use Dual-Triangle Regions For Hex Corners

The dual graph of a hex grid is triangular. A hex corner is naturally a triangle formed by the three neighboring hex centers. That makes corner transitions clearer than trying to reason only from one hex's six wedges.

Direct project shortcut:

```text
hex cells decide intent
dual corner triangles decide shared corner transition
hex wedges render from already-solved corner/edge states
```

Build impact:

- A bad corner transition has one owner: the dual triangle/corner region.
- Three-cell elevation conflicts become explicit.
- Corner smoothing can be separated from edge cliff/ledge policy.

### 3. Replace Case Explosion With Layered Modules

Planet has too many possible combinations if every triangle corner can have multiple heights and terrain types. The documented solution is to assemble one triangle from several pre-authored modules and reuse modules across heights through a vertical lattice/Marching-Cubes-like process.

Direct project shortcut:

```text
Do not author/emit one profile for every terrain+height combination.
Split into layers:
  base height profile
  cliff/ledge profile
  road profile
  pad/foundation profile
  material/biome overlay
```

Build impact:

- The first terrain compiler only needs a few height profiles.
- Roads and pads become constraints/overlays, not separate terrain systems.
- Large height differences can reuse the same side-wall/riser profile at multiple z bands.

### 4. Use Discrete Height Bands Before Continuous Heights

Planet uses a finite number of height levels. The key build-speed idea is to classify transitions by bands first, then generate continuous vertex heights afterward.

Recommended v0:

```text
height_band = integer 0..7 for 32x32x8 cube
height_m = height_band * cell_size_z or configured elevation step
```

Transition bands:

```json
[
  {
    "delta_band": 0,
    "topology_class": "same_height",
    "profile": "shared_flat"
  },
  {
    "delta_band": 1,
    "topology_class": "single_step",
    "profile": "soft_fold_or_terrace"
  },
  {
    "delta_band": 2,
    "topology_class": "cliff_start_end",
    "profile": "ledge_or_cliff_fault"
  },
  {
    "delta_band": "3_plus",
    "topology_class": "major_cliff",
    "profile": "stacked_vertical_wall"
  }
]
```

Build impact:

- Removes vague slope thresholds from the first proof.
- Fits the existing `32x32x8` map cube.
- Makes validation simple: every edge has an integer delta band.

### 5. Cliff Variants Start At Delta 2

Planet uses special cliff start/end variants when adjacent heights differ by 2 or more. That directly answers the "max climb/reach then fault" idea.

Recommended v0 rule:

```text
delta 0: flat/shared
delta 1: soft fold, ramp, or step/terrace depending tags
delta >= 2: cliff/ledge/fault, not a stretched smooth slope
```

Build impact:

- Stops terrain from looking melted.
- Gives immediate control over when to bend and when to fault.
- Lets route-specific profiles override only when a road/ramp tag exists.

### 6. Delay Relaxation Until After Seams Are Welded

The Townscaper-grid writeup says per-hex relaxation would prevent chunks from joining exactly, so the grid is generated unrelaxed per chunk and relaxation is applied afterward to the whole grid.

Direct project shortcut:

```text
generate canonical vertices
weld/shared-key seams
solve heights
then apply any smoothing/relaxation only to allowed vertices
```

Build impact:

- Prevents cracks introduced by local smoothing.
- Keeps deterministic chunk generation compatible with global seam validation.
- Supports future organic deformation without breaking v0 topology.

### 7. Use Pattern Detection For Macro Features

Planet handles bridges as larger patterns of height and terrain classes, not as a single triangle case. This is important for roads, ramps, gates, and building pads.

Direct project shortcut:

```text
single seam rules handle edges
macro rules handle multi-cell arrangements
```

Recommended macro signatures:

```json
[
  "road_crosses_delta_1_edge",
  "road_requires_bridge_over_delta_2_plus",
  "building_pad_2x2_flat_cluster",
  "cliff_ring_around_plateau",
  "gate_or_stair_between_height_bands"
]
```

Build impact:

- Keeps seam rules small.
- Avoids burying bridges/stairs/building adapters in generic edge code.
- Gives curator/debug output readable feature names.

## Build Dex Order That Saves Time

Implement in this order:

```text
1. shared vertex/edge registry
2. integer height bands
3. dual corner triangle records
4. edge delta band records
5. profile lookup table
6. midpoint/corner height solve
7. indexed face emitter
8. validation table
9. optional layer overlays for road/pad
10. optional relaxation after weld
```

Do not implement first:

```text
continuous organic relaxation
full WFC
arbitrary authored mesh variants
multi-chunk streaming
complex curve roads
macro bridge replacement
```

## Minimal Rule Table For v0

```json
[
  {
    "rule_id": "flat_same_band",
    "priority": 10,
    "requires": {"delta_band": 0},
    "profile": "shared_flat",
    "mesh": "shared_midpoint_12_tri_top",
    "walkability": "walkable"
  },
  {
    "rule_id": "soft_single_band",
    "priority": 20,
    "requires": {"delta_band": 1},
    "profile": "soft_fold",
    "mesh": "shared_midpoint_12_tri_top",
    "walkability": "walkable_with_cost"
  },
  {
    "rule_id": "road_single_band_override",
    "priority": 80,
    "requires": {"delta_band": 1, "tags": ["road"]},
    "profile": "road_ramp",
    "mesh": "shared_midpoint_12_tri_top",
    "walkability": "walkable"
  },
  {
    "rule_id": "building_pad_boundary",
    "priority": 90,
    "requires": {"tags": ["building_pad_edge"]},
    "profile": "foundation_snap",
    "mesh": "pad_locked_top_plus_boundary_adapter",
    "walkability": "walkable_or_socket"
  },
  {
    "rule_id": "cliff_delta_two_plus",
    "priority": 30,
    "requires": {"delta_band_min": 2},
    "profile": "cliff_fault",
    "mesh": "upper_top_plus_vertical_wall",
    "walkability": "blocked_without_connector"
  }
]
```

## Direct Documentation Cleanup

Use these terms consistently in future docs:

- `intent_grid`: hex cells with gameplay/map intent.
- `shared_vertex_graph`: canonical corners and edge midpoints.
- `dual_corner_region`: triangle-like region around a hex-grid corner.
- `height_band`: integer elevation before continuous mesh height.
- `edge_delta_band`: integer band difference across an edge.
- `profile_rule`: data record selecting a terrain transition.
- `height_profile`: named solver for vertex heights.
- `mesh_profile`: named face-emission pattern.
- `macro_signature`: multi-cell pattern such as bridge, stair, gate, or flat pad.

## One-Sentence Compiler Contract

Build Dex should not decide terrain shape by branching over individual hexes; it should solve shared vertex states, classify edge/corner topology into height bands, choose a profile rule, and emit indexed faces from canonical vertices.

