# Parametric Star Profile v0

This slice replaces the baked `custom_polygon` rings in the section-stack column source with a dictionary-backed `star_polygon` profile.

The source contract now lists `star_polygon` as a supported profile and `section_stack` as a supported operation.

The path remains:

```text
section-stack source recipe
-> parametric star profile rings
-> asset_pump_v0.py
-> gameguy_asset_v0 JSON
-> validate_gameguy_asset_v0.py
```

No Blender adapter was added in this slice. Blender remains downstream of deterministic JSON.

Generated asset evidence:

- `asset_id`: `star_column_22_v0`
- `asset_count`: 1
- `star_points`: 22
- `ring_count`: 7
- `ring_vertex_count`: 66
- `vertex_count`: 462
- `face_count`: 398
- `dimensions_m`: `0.958802 x 0.756728 x 2.46`
