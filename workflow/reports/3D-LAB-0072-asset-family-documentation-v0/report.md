# 3D-LAB-0072 Asset Family Documentation V0

## Goal

Continue the component style-system documentation beyond railings and organize
the other asset families in a human-readable way.

## Source Shape

```text
asset family
-> component breakdown
-> style directions
-> geometric shaping ledger
-> Blender tool groups
-> first build targets
```

## Files

- `docs/research/component_style_system_v0/asset_families/README.md`
- `docs/research/component_style_system_v0/asset_families/asset_family_doc_template_v0.md`
- `docs/research/component_style_system_v0/asset_families/family_style_matrix_v0.md`
- `docs/research/component_style_system_v0/asset_families/railings_v0.md`
- `docs/research/component_style_system_v0/asset_families/stairs_v0.md`
- `docs/research/component_style_system_v0/asset_families/windows_v0.md`
- `docs/research/component_style_system_v0/asset_families/doors_v0.md`
- `docs/research/component_style_system_v0/asset_families/trim_moulding_v0.md`
- `docs/research/component_style_system_v0/asset_families/ceilings_vaults_v0.md`
- `docs/research/component_style_system_v0/asset_families/walls_vertical_bays_v0.md`
- `docs/research/component_style_system_v0/README.md`
- `docs/research/component_style_system_v0/component_style_system_v0.md`
- `README.md`

## Handbook Coverage

Asset families documented:

- railings and balustrades
- stairs
- windows
- doors and portals
- trim and moulding
- ceilings and vaults
- walls and vertical bays

Each family page includes:

- purpose
- component breakdown
- style directions
- geometric shaping ledger
- Blender tool groups
- first build targets
- boundary/non-claims

## Style Matrix

`family_style_matrix_v0.md` adds a cross-family planning view for:

- Gothic
- Romanesque
- Renaissance
- Victorian
- Art Nouveau
- Islamic geometric
- Modern
- Rustic

## Validation

```text
python3 scripts/validate_component_style_sheets_v0.py
PASS component style sheet validation: domains=7 components=70 style_sheets=5 ledger_entries=11 sources=7 tools=23

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 source_component_style_sheets=5 reference_only=3

python3 -m json.tool workflow/reports/3D-LAB-0072-asset-family-documentation-v0/receipt.json
PASS
```

## Notes

This slice is documentation only. It does not add new machine-readable style
sheets for every family yet. That is intentional: the human handbook creates a
stable planning layer before the repo starts adding many JSON style bundles.

The next implementation slice should promote one family page into a new
machine-readable style-sheet bundle, or compile the existing Gothic railing
post sheet into a deterministic source recipe.
