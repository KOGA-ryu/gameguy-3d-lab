# 3D-LAB-0053 Hex Rosette Pattern Field v0

## Result

Replaced the rectangular multi-rosette source layout with a hexagonal layout:

```text
one center rosette
-> six surrounding tangent rosettes
-> outer rings as guides only
-> selected star linework from the inner star ring
-> deterministic field and segment JSON
```

## Source Decisions

- The active field is now `hex_rosette_pattern_field_v0`.
- The segment graph is now `hex_rosette_pattern_segments_v0`.
- The layout uses `7` rosette instances: `1` center plus `6` surrounding.
- All rosettes use `12` divisions for sixfold symmetry.
- Outer circles remain construction boundaries, not selected star-trace linework.
- Selected rosette star traces are pinned to `ring:star`, not `ring:outer`.
- No Blender, mesh, material, or tool-plan behavior is touched.

## Validation

```text
python3 scripts/compile_pattern_field_v0.py --validate-only
compiled pattern fields=1 edges=432 out=<validate-only>

python3 scripts/compile_pattern_segments_v0.py --validate-only
compiled pattern segment sets=1 intersections=504 segments=1656 out=<validate-only>

python3 -m unittest tests/test_compile_pattern_field_v0.py tests/test_compile_pattern_segments_v0.py
OK, 8 tests

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0053_hex_rosette.json
PASS generation pipeline validation: commands=38 json=256 include_blender=false
```

## Output Counts

- Field edges: `432`
- Selected field edges: `96`
- Segment intersections: `504`
- Split segments: `1656`
- Selected segment references: `984`

## Preview

- Field SVG: `/tmp/gameguy_pattern_field_v0_0053/svg/hex_rosette_pattern_field_v0.svg`
- Field PNG: `/tmp/gameguy_pattern_field_v0_0053_preview/hex_rosette_pattern_field_v0.svg.png`
- Segment SVG: `/tmp/gameguy_pattern_segments_v0_0053/svg/hex_rosette_pattern_segments_v0.svg`
- Segment PNG: `/tmp/gameguy_pattern_segments_v0_0053_preview/hex_rosette_pattern_segments_v0.svg.png`

## Next

Add linework families inside this hex topology:

```text
hex rosette field
-> inner-ring chords and tangent connectors
-> split at intersections
-> omit guide lines
-> extract closed motif loops
```
