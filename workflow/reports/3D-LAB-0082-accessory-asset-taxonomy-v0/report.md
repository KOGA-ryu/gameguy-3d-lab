# 3D-LAB-0082 Accessory Asset Taxonomy V0

## Goal

Add a wearable/carried accessory prop lane with families, status tiers, styles,
visible anatomy, attachment mechanics, source support, geometry terms, Blender
tool IDs, source fields, operator checks, and lore hooks.

## Added

- `data/asset_taxonomy/accessories_v0/accessory_asset_taxonomy_v0.json`
- `docs/research/accessory_assets_v0/README.md`
- `docs/research/accessory_assets_v0/accessory_source_index_v0.md`
- `docs/research/accessory_assets_v0/accessory_style_status_system_v0.md`
- `docs/research/accessory_assets_v0/accessory_family_build_plans_v0.md`
- `docs/research/accessory_assets_v0/accessory_lore_book_hooks_v0.md`
- `docs/research/accessory_assets_v0/operator_accessory_handoff_v0.md`
- `scripts/validate_accessory_asset_taxonomy_v0.py`
- `tests/test_validate_accessory_asset_taxonomy_v0.py`

## Coverage

- 9 accessory status tiers
- 8 accessory styles
- 8 accessory families
- 12 starter accessories

## Boundary

This is game-asset planning and lore documentation only. It is not fabrication
guidance, costume safety guidance, conservation guidance, historical
authenticity proof, or active generated-asset input.

## Validation

```text
python3 -m json.tool data/asset_taxonomy/accessories_v0/accessory_asset_taxonomy_v0.json
PASS accessory JSON parse

python3 -m py_compile scripts/validate_accessory_asset_taxonomy_v0.py
PASS py_compile

python3 scripts/validate_accessory_asset_taxonomy_v0.py
PASS accessory asset taxonomy validation: status_tiers=9 styles=8 families=8 accessories=12 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_accessory_asset_taxonomy_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation
```

## Recommended Next Goal

Add per-accessory workcards and promote one simple accessory, likely
`leather_belt_buckle_v0` or `key_ring_warded_keys_v0`, into a deterministic
source-to-tool-plan recipe.
