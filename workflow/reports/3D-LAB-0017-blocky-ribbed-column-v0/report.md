# Blocky Ribbed Column v0

This slice adds a source-simple column recipe that produces a complex-looking architectural column from simple mesh parts.

The path is:

```text
blocky column source recipe
-> simple part compiler
-> deterministic gameguy_asset_v0 JSON
-> validate_gameguy_asset_v0.py
-> Blender adapter preview
```

The model is not a single high-count star loft. It is an assembly:

- square plinth box
- lower low-poly round collar
- simple shaft core
- 22 shallow oriented box ribs
- upper low-poly round necking
- square abacus box

Generated asset evidence:

- `asset_id`: `blocky_ribbed_column_v0`
- `asset_count`: 1
- `part_count`: 27
- `rib_count`: 22
- `rib_depth_m`: 0.04
- `vertex_count`: 264
- `face_count`: 186
- `dimensions_m`: `0.92 x 0.92 x 2.46`

No Blender source logic was added. The existing Blender adapter consumes the generated `gameguy_asset_v0` mesh JSON.
