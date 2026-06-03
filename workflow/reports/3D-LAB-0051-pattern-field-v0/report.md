# 3D-LAB-0051 Pattern Field v0

## Result

Added the first source-only multi-center rosette pattern-field compiler.

```text
pattern field recipe
-> rosette modules and instances
-> guide circles, radial rays, ring segments, star traces, connector lines
-> named selected trace groups
-> deterministic JSON
-> SVG construction preview
```

## Source Decisions

- V0 models the paper reference as a multi-center construction drawing, not a finished ornament.
- Large rosettes use `16` divisions and three rings.
- Small bridge rosettes use `8` divisions and two rings.
- Guide circles/rays/rings are emitted as faint construction geometry.
- Selected star traces and selected connector traces are emitted as dark motif candidates.
- No intersections, planar subdivision, Blender, mesh, or 3D role promotion are solved in this slice.

## Added Files

- `data/architecture/sacred_geometry/pattern_field_recipes_v0.json`
- `geometry_dictionary/operations/pattern_field.json`
- `scripts/compile_pattern_field_v0.py`
- `tests/test_compile_pattern_field_v0.py`

## Validation

```text
python3 scripts/compile_pattern_field_v0.py --validate-only
compiled pattern fields=1 edges=540 out=<validate-only>

python3 scripts/compile_pattern_field_v0.py --clean --out /tmp/gameguy_pattern_field_v0_0051
compiled pattern fields=1 edges=540 selected=120 out=/tmp/gameguy_pattern_field_v0_0051

python3 -m unittest tests/test_compile_pattern_field_v0.py tests/test_validate_asset_generation_registry_v0.py tests/test_validate_generation_pipeline_v0.py tests/test_validate_construction_geometry_taxonomy_v0.py
OK, 18 tests

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_taxonomies=23 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0051_final.json
PASS generation pipeline validation: commands=37 json=253 include_blender=false
```

## Preview

- SVG: `/tmp/gameguy_pattern_field_v0_0051/svg/multi_rosette_pattern_field_v0.svg`
- PNG: `/tmp/gameguy_pattern_field_v0_0051_preview/multi_rosette_pattern_field_v0.svg.png`

No Blender-inclusive validation was run for this slice because the change does not touch Blender adapters, tool plans, meshes, materials, or execution reports.

## Next

Add selection refinement:

```text
pattern field
-> compute intersections
-> split guide lines into candidate segments
-> omit guides
-> promote selected edges/cells into tracery, railing ornament, or vault ribs
```
