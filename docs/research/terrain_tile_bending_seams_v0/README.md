# Terrain Tile Bending And Seam Research v0

Research packet for crack-free hex terrain tiles that bend between elevations without duplicate seam vertices.

This is research documentation only. It does not implement code, create meshes, download images, scrape assets, or make production, structural, fabrication, Gym, or Museum approval claims.

## Purpose

Build Dex needs a terrain compiler path beyond flat hex tops with exposed sides. The next layer should allow each hex cell to become a small radial surface made from triangles. Neighboring cells must connect through shared vertices on borders and corners so elevation changes do not create holes.

## Packet Files

- `hex_radial_subdivision_notes_v0.md`: center-to-corner and center-to-midpoint fan patterns for hex cells.
- `shared_vertex_topology_notes_v0.md`: which vertices are shared, how they are keyed, and why duplicate seam vertices create cracks.
- `seam_stitching_and_crack_prevention_v0.md`: crack-prevention methods from terrain LOD and how they map to this project.
- `elevation_transition_rules_v0.md`: ramps, ledges, cliffs, terraces, and height assignment rules.
- `building_pad_and_road_flattening_v0.md`: plateau and route flattening constraints inside deformable terrain.
- `stalberg_build_acceleration_extract_v0.md`: Townscaper/Planet extraction focused on build-speed decisions, rule tables, and direct compiler shortcuts.
- `implementation_recommendation_v0.md`: exact recommended v0 vertex model, face model, seam ownership rule, height rule, validation checks, first test scene, and deferred complexity.
- `source_index.json`: machine-readable source list.
- `extracted_terms.json`: machine-readable technical terms and project mappings.
- `receipt.json`: validation and boundary receipt.

## Main Recommendation

Use a global top-surface vertex registry and indexed triangle faces:

1. Each hex owns one center vertex.
2. Each hex references six shared corner vertices.
3. Each hex may reference six shared edge midpoint vertices.
4. A v0 "bent" hex emits 12 triangles: two triangles per side, both sharing the cell center and edge midpoint.
5. A v0 "simple" hex emits 6 triangles: one triangle per side from center to adjacent corners.
6. Corner and edge midpoint vertices are globally shared by topological key, not recreated per cell.
7. Each shared vertex gets one final height before faces are emitted.
8. Hard seams are represented by policies and optional riser/cliff faces, not by duplicate top-surface seam vertices.

## Simplest v0 Algorithm

1. Generate all cell centers from the existing axial/cube hex grid.
2. Generate global corner vertex keys from the set of cells touching that corner.
3. Generate global edge midpoint keys from the undirected pair of adjacent cells, or from a boundary edge key.
4. Solve final height once for each shared corner and midpoint.
5. Emit top faces from vertex indices in the registry.
6. Emit vertical risers only for explicit `hard_step`, `cliff_drop`, or `chunk_boundary` policies.
7. Validate there are no duplicate top vertices at a seam and no boundary gaps between neighboring cells.

## Sources Used

The packet uses Red Blob Games for hex grid coordinates and face/edge/vertex relationships, Khronos/OpenGL and Unity documentation for indexed triangle mesh and triangle fan concepts, Blender API documentation for the eventual proof-render mesh output path, GPU Gems geometry clipmaps and Transvoxel for crack prevention and LOD seam concepts, Unity terrain docs for set-height flattening, Catlike Coding for shared grid generation patterns, FOLD for crease topology vocabulary, and Manifold documentation for mesh topology constraints.
