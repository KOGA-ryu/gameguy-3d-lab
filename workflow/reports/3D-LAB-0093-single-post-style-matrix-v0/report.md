# 3D-LAB-0093 Single Post Style Matrix V0

## Goal

Promote the post style atlas into source-side machine-readable data for one
post with multiple style variants.

## Added

- `data/architecture/component_style_sheets/railings/single_post_style_matrix_v0.json`
- `scripts/validate_single_post_style_matrix_v0.py`

## Updated

- `data/architecture/component_style_sheets/component_style_sheet_registry_v0.json`
- `scripts/validate_generation_pipeline_v0.py`
- `README.md`
- `docs/research/component_style_system_v0/README.md`
- `docs/research/component_style_system_v0/asset_families/railings_v0.md`
- `docs/research/component_style_system_v0/railing_post_style_atlas_v0.md`

## Matrix Variants

- `post_style.plain_square_reference_v0`
- `post_style.gothic_buttress_newel_v0`
- `post_style.gothic_clustered_shaft_v0`
- `post_style.castle_crenel_cap_v0`
- `post_style.rustic_timber_chamfered_v0`

## Boundary

This slice does not generate rails, infill panels, full railing runs, asset
geometry, tool plans, Blender output, renders, or exports.

## Validation

Validation run:

- JSON parse for registry, matrix, and receipt
- Python compile for the new validator and pipeline validator
- `python3 scripts/validate_single_post_style_matrix_v0.py`
- `python3 scripts/validate_component_style_sheets_v0.py`
- `git diff --check`
- git status check
