# 3D-LAB-0052 Pattern Segment Split v0

## Result

Added the first source-only pattern segment splitter.

```text
pattern field JSON
-> edge intersections
-> split candidate segments
-> named segment selections
-> deterministic segment JSON
-> SVG segment/intersection preview
```

## Source Decisions

- V0 splits straight edges at interior line intersections.
- Endpoint-only contacts are ignored as intersections.
- Tiny segments below the recipe threshold are rejected.
- Selected source traces are preserved as segment tags so selection can happen after splitting.
- This is still not a finished ornament: omission rules and shape extraction come next.
- No Blender, mesh, material, or tool-plan behavior is touched.

## Added Files

- `data/architecture/sacred_geometry/pattern_segment_recipes_v0.json`
- `geometry_dictionary/operations/pattern_segment_split.json`
- `scripts/compile_pattern_segments_v0.py`
- `tests/test_compile_pattern_segments_v0.py`

## Validation

```text
python3 scripts/compile_pattern_segments_v0.py --validate-only
compiled pattern segment sets=1 intersections=1020 segments=2402 out=<validate-only>

python3 scripts/compile_pattern_field_v0.py --clean --out /tmp/gameguy_pattern_field_v0_0052
compiled pattern fields=1 edges=540 selected=120 out=/tmp/gameguy_pattern_field_v0_0052

python3 scripts/compile_pattern_segments_v0.py --clean --pattern-field-manifest /tmp/gameguy_pattern_field_v0_0052/manifest.json --out /tmp/gameguy_pattern_segments_v0_0052
compiled pattern segment sets=1 intersections=1020 segments=2402 selected=1333 out=/tmp/gameguy_pattern_segments_v0_0052

python3 -m unittest tests/test_compile_pattern_segments_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_validate_generation_pipeline_v0.py tests/test_validate_construction_geometry_taxonomy_v0.py
OK, 19 tests

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0052_final.json
PASS generation pipeline validation: commands=38 json=256 include_blender=false
```

## Preview

- SVG: `/tmp/gameguy_pattern_segments_v0_0052/svg/multi_rosette_pattern_segments_v0.svg`
- PNG: `/tmp/gameguy_pattern_segments_v0_0052_preview/multi_rosette_pattern_segments_v0.svg.png`

No Blender-inclusive validation was run for this slice because the change does not touch Blender adapters, tool plans, meshes, materials, or execution reports.

## Next

Add omission and shape extraction:

```text
split pattern segments
-> omit guide segments
-> select closed loops and motif paths
-> promote selected shapes into railing panels, tracery, vault ribs, or relief profiles
```
