# 3D-LAB-0050 Construction Cell Selection v0

## Result

Added the first source-only construction cell-selection compiler.

```text
sacred graph output
-> adjacent ring-band cells
-> named cell selections
-> deterministic cell-selection JSON
-> SVG selection preview
```

## Source Decisions

- V0 derives only simple adjacent ring-band radial cells.
- It intentionally avoids star-chord intersection solving and full planar subdivision.
- The default 22-division graph produces `66` cells: `3` adjacent ring bands times `22` radial slices.
- The first selections are:
  - `vault_web_cells_primary`
  - `outer_tracery_opening_cells`
  - `railing_recess_panel_cells`
- Blender remains downstream; it must not choose cells or hide role-promotion decisions.

## Added Files

- `data/architecture/sacred_geometry/construction_cell_selection_recipes_v0.json`
- `geometry_dictionary/operations/construction_cell_selection.json`
- `scripts/compile_construction_cell_selection_v0.py`
- `tests/test_compile_construction_cell_selection_v0.py`

## Validation

```text
python3 scripts/compile_construction_cell_selection_v0.py --validate-only
compiled construction cell selections=1 cells=66 out=<validate-only>

python3 scripts/compile_sacred_graph_v0.py --clean --out /tmp/gameguy_sacred_graph_v0_0050
compiled sacred graphs=1 points=89 edges=220 out=/tmp/gameguy_sacred_graph_v0_0050

python3 scripts/compile_construction_cell_selection_v0.py --clean --graph-manifest /tmp/gameguy_sacred_graph_v0_0050/manifest.json --out /tmp/gameguy_construction_cell_selection_v0_0050
compiled construction cell selections=1 cells=66 selected=26 out=/tmp/gameguy_construction_cell_selection_v0_0050

python3 -m unittest discover -s tests
OK, 143 tests

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 source_cell_selections=1 source_taxonomies=23 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --json-report /tmp/gameguy_pipeline_0050_final.json
PASS generation pipeline validation: commands=37 json=250 include_blender=false

python3 scripts/validate_generation_pipeline_v0.py --include-blender --json-report /tmp/gameguy_pipeline_blender_0050_final.json
PASS generation pipeline validation: commands=51 json=250 include_blender=true
```

## Preview

- SVG: `/tmp/gameguy_construction_cell_selection_v0_0050/svg/sacred_22_star_radial_cell_selection_v0.svg`
- PNG: `/tmp/gameguy_construction_cell_selection_v0_0050_preview/sacred_22_star_radial_cell_selection_v0.svg.png`

## Next

Use these selected cells as the source for the next visual refinement:

```text
selected construction cells
-> role promotion records
-> lift/fold/sweep/thicken operation stack
-> railing panel or vault-web prototype
```
