# Blocky Shape Grammar v0

This slice generalizes the blocky column proof into a reusable shape grammar for source-simple architectural assets.

The path is:

```text
blocky shape grammar source recipe
-> ordered simple part compiler
-> deterministic gameguy_asset_v0 JSON
-> validate_gameguy_asset_v0.py
-> Blender adapter preview
```

The grammar keeps complex-looking forms as assemblies of simple parts:

- `box`
- `cylinder`
- `radial_box_array`

The proof bundle contains two assets:

- `grammar_ribbed_column_v0`: column-like fixture using square boxes, low-poly round collars, a shaft core, and 22 shallow ribs.
- `blocky_fence_post_v0`: fence/banister post fixture using stepped square boxes and side rail sockets.

Generated asset evidence:

- `asset_count`: 2
- `total_vertices`: 320
- `total_faces`: 228
- `total_parts`: 34
- `grammar_ribbed_column_v0`: 27 expanded parts, 264 vertices, 186 faces, dimensions `0.92 x 0.92 x 2.46`
- `blocky_fence_post_v0`: 7 expanded parts, 56 vertices, 42 faces, dimensions `0.50 x 0.50 x 1.24`

No Blender source logic was added. The Blender adapter consumes generated `gameguy_asset_v0` mesh JSON.
