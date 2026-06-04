# 3D-LAB-0071 Component Style Sheets V0

## Goal

Create the source layer that maps architectural component taxonomy names to
geometric shaping ledgers and legal Blender tool sequences.

## Source Shape

```text
domain taxonomy
-> component style-sheet registry
-> Gothic railing post style sheets
-> geometric shaping ledger per visible part
-> future source recipe or tool-plan compiler
```

## Files

- `docs/research/component_style_system_v0/README.md`
- `docs/research/component_style_system_v0/component_style_system_v0.md`
- `docs/research/component_style_system_v0/gothic_railing_post_research_findings_v0.md`
- `docs/research/component_style_system_v0/gothic_railing_post_build_plans_v0.md`
- `data/architecture/taxonomy/component_domains/component_domain_taxonomy_v0.json`
- `data/architecture/component_style_sheets/component_style_sheet_registry_v0.json`
- `data/architecture/component_style_sheets/railings/gothic_railing_post_style_sheets_v0.json`
- `geometry_dictionary/operations/component_style_sheet.json`
- `scripts/validate_component_style_sheets_v0.py`
- `tests/test_validate_component_style_sheets_v0.py`
- `data/architecture/asset_mill/asset_generation_registry_v0.json`
- `scripts/validate_asset_generation_registry_v0.py`
- `scripts/validate_generation_pipeline_v0.py`
- `README.md`

## Taxonomy

The component domain taxonomy defines:

```text
domains=7
components=70
style_families=10
```

Domains:

- `railings`
- `stairs`
- `windows`
- `doors`
- `trim_moulding`
- `ceilings`
- `walls`

## First Style Bundle

```text
bundle_id=gothic_railing_post_style_sheets_v0
domain=railings
style_family=gothic
style_sheets=5
ledger_entries=11
source_shape_terms=11
operation_terms=12
blender_tools=23
```

Style sheets:

- `gothic_railing_post.buttress_newel_v0`
- `gothic_railing_post.clustered_shaft_newel_v0`
- `gothic_railing_post.blind_tracery_box_newel_v0`
- `gothic_railing_post.pinnacle_newel_v0`
- `gothic_railing_post.crocketed_finial_newel_v0`

## Validation

```text
python3 scripts/validate_component_style_sheets_v0.py --json-report /tmp/component_style_sheet_validation_v0.json
PASS component style sheet validation: domains=7 components=70 style_sheets=5 ledger_entries=11 sources=7 tools=23

python3 scripts/validate_asset_generation_registry_v0.py --json-report /tmp/asset_generation_registry_validation_v0.json
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 source_component_style_sheets=5 reference_only=3

python3 -m unittest tests/test_validate_component_style_sheets_v0.py tests/test_validate_asset_generation_registry_v0.py
17 tests passed

find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
PASS

python3 -m py_compile scripts/*.py
PASS

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_component_style_sheets_v0_final.json
PASS generation pipeline validation: commands=50 json=285 include_blender=false
```

## Notes

This slice does not generate a new mesh. It gives the repo a scalable source
contract for railings first, and for stairs, windows, doors, trim, ceilings,
and walls later.

The next useful compiler slice is:

```text
3D-LAB-0072 component_style_sheet_to_post_recipe_v0
```

Recommended first target:

```text
gothic_railing_post.blind_tracery_box_newel_v0
```
