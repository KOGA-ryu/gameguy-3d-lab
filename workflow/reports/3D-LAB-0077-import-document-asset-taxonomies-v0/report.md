# 3D-LAB-0077 Import Document Asset Taxonomies V0

## Goal

Import and organize the asset taxonomy seed JSON files found in the user's local
Documents folder.

## Imported JSON Seeds

- `armor_history_taxonomy_seed.json`
- `armor_making_taxonomy_seed.json`
- `human_meat_taxonomy_seed.json`
- `human_textile_taxonomy_seed.json`
- `sewing_equipment_taxonomy_seed.json`

## Added

- `data/asset_taxonomy/README.md`
- `data/asset_taxonomy/imported_taxonomy_manifest_v0.json`
- raw seed copies under `data/asset_taxonomy/imported_seeds_v0/`
- imported-taxonomy research docs under
  `docs/research/imported_asset_taxonomies_v0/`

## Boundary

This slice preserves and organizes raw source taxonomy seeds. It does not:

- import `.docx` spec sheets
- normalize the seeds into canonical schemas
- add generator support
- run Blender
- add the imported domains to architecture taxonomy

## Validation

```text
for f in data/asset_taxonomy/imported_seeds_v0/*.json; do python3 -m json.tool "$f" >/tmp/"$(basename "$f")" || exit 1; done
PASS imported seed JSON parse: files=5

python3 -m json.tool data/asset_taxonomy/imported_taxonomy_manifest_v0.json
PASS manifest JSON parse

python3 -m json.tool workflow/reports/3D-LAB-0077-import-document-asset-taxonomies-v0/receipt.json
PASS receipt JSON parse

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 source_component_style_sheets=5 reference_only=3
```

## Recommended Next Goal

Build a normalized `shape_type_crosswalk_v0.json` that maps imported
`shape_type`, `shape_vocab`, and `blender_proxy` phrases to geometry dictionary
terms, Blender tool cards, required source fields, and promotion status.
