# 3D-LAB-0049 Construction Geometry Taxonomy v0

## Result

Added a source-language taxonomy for the construction-geometry system that should drive future railing, window, arch, vault, column, and ornament work.

```text
construction field
-> selection / omission
-> role promotion
-> lift / fold / sweep / thicken / bevel
-> deterministic asset or tool-plan JSON
```

## Source Decisions

- The user's "master pattern creates everything" idea is now represented as `construction_field`.
- Visible geometry comes from `selected_subgraph`, `selective_omission`, and `role_promotion`.
- Nodes, edges, and cells are separate promotion targets.
- Muqarnas-like dome and ceiling work is framed as `muqarnas_cell_plan` plus `cascade_order`, `lift_operation`, and `fold_operation`.
- Railing refinement now has upstream vocabulary for panels, lips, ribs, bead strips, and four-sided wrapped details.
- Blender remains an adapter and should not contain selection or design decisions.

## Added Files

- `data/architecture/taxonomy/construction_geometry/construction_geometry_taxonomy_v0.json`
- `docs/asset_pump/procedural_construction_geometry_taxonomy_v0.md`
- `scripts/validate_construction_geometry_taxonomy_v0.py`
- `tests/test_validate_construction_geometry_taxonomy_v0.py`

## Updated Files

- `README.md`
- `data/architecture/asset_mill/asset_generation_registry_v0.json`
- `scripts/validate_asset_generation_registry_v0.py`
- `scripts/validate_generation_pipeline_v0.py`
- `tests/test_validate_asset_generation_registry_v0.py`
- `tests/test_validate_generation_pipeline_v0.py`

## Validation

```text
python3 scripts/validate_construction_geometry_taxonomy_v0.py
PASS construction geometry taxonomy validation: sources=9 terms=23 claims=5 repo_mappings=7

python3 -m unittest discover -s tests
OK, 138 tests

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 source_taxonomies=23 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --json-report /tmp/gameguy_pipeline_0049_final.json
PASS generation pipeline validation: commands=36 json=247 include_blender=false

python3 scripts/validate_generation_pipeline_v0.py --include-blender --json-report /tmp/gameguy_pipeline_blender_0049_final.json
PASS generation pipeline validation: commands=50 json=247 include_blender=true
```

## Next

Add `3D-LAB-0050 construction_cell_selection_v0`.

The useful next compiler should read the sacred graph, derive closed cells between rings/radials, select cells by orbit or band, label them with architectural roles, and preview selected cells in SVG before any Blender execution.
