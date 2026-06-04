# 3D-LAB-0084 Animal Asset Taxonomy V0

## Goal

Add an animal asset lane with role tiers, body-plan styles, families, starter
animals, visible anatomy, locomotion read, source support, geometry terms,
Blender tool IDs, source fields, operator checks, and lore hooks.

## Added

- `data/asset_taxonomy/animals_v0/animal_asset_taxonomy_v0.json`
- `docs/research/animal_assets_v0/README.md`
- `docs/research/animal_assets_v0/animal_source_index_v0.md`
- `docs/research/animal_assets_v0/animal_role_body_plan_system_v0.md`
- `docs/research/animal_assets_v0/animal_family_build_plans_v0.md`
- `docs/research/animal_assets_v0/animal_lore_book_hooks_v0.md`
- `docs/research/animal_assets_v0/operator_animal_handoff_v0.md`
- `scripts/validate_animal_asset_taxonomy_v0.py`
- `tests/test_validate_animal_asset_taxonomy_v0.py`

## Coverage

- 10 animal role tiers
- 13 animal body-plan styles
- 8 animal families
- 16 starter animal assets

## Boundary

This is game-asset planning and lore documentation only. It is not animal-care
guidance, welfare guidance, biological accuracy proof, historical authenticity
proof, animation runtime design, AI behavior design, or active generated-asset
input.

## Validation

```text
python3 -m json.tool data/asset_taxonomy/animals_v0/animal_asset_taxonomy_v0.json
PASS animal JSON parse

python3 -m py_compile scripts/validate_animal_asset_taxonomy_v0.py
PASS py_compile

python3 scripts/validate_animal_asset_taxonomy_v0.py
PASS animal asset taxonomy validation: role_tiers=10 styles=13 families=8 animals=16 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_animal_asset_taxonomy_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation
```

## Recommended Next Goal

Promote one small animal into a deterministic source-to-tool-plan recipe. Good
first candidates are `river_fish_v0`, `chicken_flock_bird_v0`, or `snake_v0`
because each has a strong silhouette and a small number of required parts.
