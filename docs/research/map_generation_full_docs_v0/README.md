# Map Generation Full Docs v0

This packet extracts technical documentation needed for the map, terrain, and building generation engine. It is documentation only: no implementation, no meshes, no image downloads, no asset scraping, no production approval, no structural claim, and no Gym/Museum approval.

## Files

- `redblob_hex_full_notes_v0.md`: hex coordinate systems, algorithms, map storage, and 32x32x8 mapping.
- `tiled_full_notes_v0.md`: Tiled JSON/TMX fields and a minimal map-template subset.
- `ldtk_full_notes_v0.md`: LDtk project/level/layer/entity model and later-adoption guidance.
- `wfc_model_synthesis_full_notes_v0.md`: WFC/model synthesis, sockets, constraints, and deferred solver work.
- `terraced_terrain_full_notes_v0.md`: TTG terrace concepts and what maps to the hex terrain compiler.
- `blender_mesh_api_full_notes_v0.md`: minimum Blender Python mesh/curve/object APIs for proof renders.
- `sverchok_full_notes_v0.md`: conceptual node/data-flow reference for procedural geometry factories.
- `cadquery_full_notes_v0.md`: CAD workplane/profiles/booleans/export concepts for future robust assets.
- `manifold_full_notes_v0.md`: robust manifold mesh/boolean concepts for later boolean-heavy pipelines.
- `implementation_crosswalk_v0.md`: direct mapping into engine pieces.
- `open_questions_v0.md`: unresolved design choices for Build Dex.

Machine-readable outputs:

- `data/architecture/research/map_generation_full_docs_v0/source_index.json`
- `data/architecture/research/map_generation_full_docs_v0/extracted_terms.json`
- `data/architecture/research/map_generation_full_docs_v0/implementation_crosswalk.json`
- `data/architecture/research/map_generation_full_docs_v0/recommended_v0_data_shapes.json`

Receipt:

- `goal/receipts/map_generation_full_docs_v0.receipt.json`

## Build Dex Guidance

For v0, use Red Blob axial/cube math as the authoritative hex algorithm base, Tiled-style JSON as the first interchange shape, the existing repo contracts as the internal data shape, and Blender `Mesh.from_pydata` plus validation/update calls for proof renders. Treat LDtk, WFC/model synthesis, TTG, Sverchok, CadQuery, and Manifold as staged references: useful for architecture, but not dependencies for v0 unless a later task explicitly adopts them.

## Validation Expectations

- JSON files parse.
- Every source URL is present in `source_index.json`.
- Every implementation recommendation in `implementation_crosswalk.json` includes at least one `source_urls` entry.
- No images were downloaded.
- No raw HTML dumps were stored.
- No mesh files were created.

