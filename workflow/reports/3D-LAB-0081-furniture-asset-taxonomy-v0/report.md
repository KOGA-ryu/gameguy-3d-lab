# 3D-LAB-0081 Furniture Asset Taxonomy V0

## Goal

Add a furniture prop lane with families, status/caste tiers, styles, visible
anatomy, source support, geometry terms, Blender tool IDs, source fields,
operator checks, and lore hooks.

## Added

- `data/asset_taxonomy/furniture_v0/furniture_asset_taxonomy_v0.json`
- `docs/research/furniture_assets_v0/README.md`
- `docs/research/furniture_assets_v0/furniture_source_index_v0.md`
- `docs/research/furniture_assets_v0/furniture_style_caste_system_v0.md`
- `docs/research/furniture_assets_v0/furniture_family_build_plans_v0.md`
- `docs/research/furniture_assets_v0/furniture_lore_book_hooks_v0.md`
- `docs/research/furniture_assets_v0/operator_furniture_handoff_v0.md`
- `scripts/validate_furniture_asset_taxonomy_v0.py`
- `tests/test_validate_furniture_asset_taxonomy_v0.py`

## Coverage

- 8 furniture caste/status tiers
- 8 furniture styles
- 6 furniture families
- 10 starter furniture assets

## Boundary

This is game-asset planning and lore documentation only. It is not fabrication
guidance, ergonomic/safety guidance, conservation guidance, historical
authenticity proof, or active generated-asset input.

## Validation

```text
python3 -m json.tool data/asset_taxonomy/furniture_v0/furniture_asset_taxonomy_v0.json
PASS furniture JSON parse

python3 -m py_compile scripts/validate_furniture_asset_taxonomy_v0.py
PASS py_compile

python3 scripts/validate_furniture_asset_taxonomy_v0.py
PASS furniture asset taxonomy validation: caste_tiers=8 styles=8 families=6 furniture=10 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_furniture_asset_taxonomy_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation
```

## Recommended Next Goal

Add per-furniture workcards and promote one simple furniture item, likely
`boarded_chest_coffer_v0` or `trestle_table_v0`, into a deterministic
source-to-tool-plan recipe.
