# Implementation Crosswalk v0

This crosswalk maps researched concepts to the current engine pieces. It is implementation guidance only, not production approval.

## Engine Piece Mapping

| Engine piece | Direct recommendations | Sources |
| --- | --- | --- |
| `32x32x8 map cube` | Keep repo `map_cube_grid_v0` as bounded container. Use Red Blob only for horizontal hex coordinates and TTG only for terrace height concepts. | Red Blob, TTG, repo contracts |
| `hex/elevation cells` | Store `q`, `r`, derived/stored `s = -q-r`, plus vertical `z/final_height` separately. Use six Red Blob directions for edge profiles. | Red Blob |
| `terrain mesh compiler` | Compile internal cell records into vertex/face arrays; call Blender `Mesh.from_pydata`, `validate`, and `update`. | Red Blob, Blender Mesh API |
| `visible face meshing` | Emit top hex faces and vertical side/riser faces only where neighbor is absent or height delta exposes a face. Use selection/mask concepts from Sverchok if helper naming is useful. | Red Blob, Blender, Sverchok |
| `seam/fold grammar` | Classify each of six neighbor deltas as flat/step/ledge/cliff/boundary. Terrace snapping can produce stable bands. | Red Blob, TTG |
| `road/path layer` | Use Red Blob line/range/ring algorithms for paths and influence; use Tiled object polylines as optional import shape. | Red Blob, Tiled |
| `building plot layer` | Use Tiled rectangles/polygons or LDtk entities as template inputs; compile to existing floor plan/plot contracts. | Tiled, LDtk, repo floor plan contract |
| `asset placement layer` | Use Tiled object points or LDtk entities as sockets; store `socket_type`, `orientation`, `asset_ref`, and semantic tags. | Tiled, LDtk |
| `Blender proof renderer` | Use direct mesh arrays and optional curves; avoid edit-mode operators and booleans for v0. | Blender Mesh API |
| `future AI affordance graph` | Build graph nodes from hex cells and edges from neighbor directions; carry movement, visibility, hazard, cover, and connector tags. | Red Blob, Tiled custom properties, LDtk fields |

## Source-Specific Adoption

- Red Blob: adopt now.
- Tiled JSON: support first as external map-template/interchange input.
- LDtk: defer importer, but keep schema notes for future authored templates.
- WFC/model synthesis: defer solver; adopt socket/compatibility data shape now.
- TTG: adopt terrace parameter concepts; do not port Unity code.
- Blender API: adopt direct mesh creation now for proof renders.
- Sverchok: use conceptually for mesh-list pipeline; no dependency.
- CadQuery: future robust assets; no v0 dependency.
- Manifold: future robust booleans if needed; no v0 dependency.

## Build Order

1. Implement pure hex coordinate helper and validation.
2. Implement Tiled-style minimal JSON importer.
3. Compile map templates into internal `hex_terrain_fold_recipe_v0` / `hex_topology_site_recipe_v0` records.
4. Implement terrain visible-face mesh arrays.
5. Implement Blender proof renderer from arrays.
6. Add asset sockets and building plot adapters.
7. Add socket compatibility validator.
8. Defer WFC, LDtk, CadQuery, Manifold until data shapes are stable.

