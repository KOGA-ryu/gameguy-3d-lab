# 3D-LAB-0080 Musical Instrument Asset Taxonomy V0

## Goal

Add a musical-instrument prop and lore lane that documents instrument anatomy,
craft vocabulary, source support, geometry terms, Blender tool IDs, source
fields, operator checks, and book hooks.

## Added

- `data/asset_taxonomy/musical_instruments_v0/musical_instrument_asset_taxonomy_v0.json`
- `docs/research/musical_instrument_assets_v0/README.md`
- `docs/research/musical_instrument_assets_v0/instrument_source_index_v0.md`
- `docs/research/musical_instrument_assets_v0/instrument_family_build_plans_v0.md`
- `docs/research/musical_instrument_assets_v0/instrument_lore_book_hooks_v0.md`
- `docs/research/musical_instrument_assets_v0/operator_instrument_handoff_v0.md`
- `scripts/validate_musical_instrument_taxonomy_v0.py`
- `tests/test_validate_musical_instrument_taxonomy_v0.py`

## Instrument Coverage

- lute
- Gothic harp
- recorder
- shawm
- frame drum
- cast bell
- portative organ
- hurdy-gurdy

## Boundary

This is game-asset planning and lore documentation only. It is not acoustic
engineering, playable-audio work, fabrication guidance, conservation guidance,
or a historical authenticity claim.

## Validation

```text
python3 -m json.tool data/asset_taxonomy/musical_instruments_v0/musical_instrument_asset_taxonomy_v0.json
PASS musical instruments JSON parse

python3 -m py_compile scripts/validate_musical_instrument_taxonomy_v0.py
PASS py_compile

python3 scripts/validate_musical_instrument_taxonomy_v0.py
PASS musical instrument taxonomy validation: families=8 instruments=8 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_musical_instrument_taxonomy_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation
```

## Recommended Next Goal

Add per-instrument workcard templates for one simple prop, probably
`frame_drum_v0` or `cast_bell_v0`, because both can test source fields,
geometry terms, Blender tool plans, and low-compute detail toggles without
needing playable audio logic.
