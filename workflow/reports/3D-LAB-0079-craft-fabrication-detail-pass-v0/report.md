# 3D-LAB-0079 Craft Fabrication Detail Pass V0

## Goal

Detail the documentation with fabrication-informed craft methods so asset plans
can use real workshop vocabulary and mechanics when choosing drawing tags,
source fields, Blender tools, and operator checks.

## Added

- `data/architecture/taxonomy/craft_methods/craft_fabrication_methods_v0.json`
- `docs/research/craft_fabrication_methods_v0/README.md`
- `docs/research/craft_fabrication_methods_v0/craft_source_index_v0.md`
- `docs/research/craft_fabrication_methods_v0/asset_family_fabrication_build_plans_v0.md`
- `docs/research/craft_fabrication_methods_v0/operator_fabrication_handoff_v0.md`
- `scripts/validate_craft_fabrication_methods_v0.py`
- `tests/test_validate_craft_fabrication_methods_v0.py`

## Method Coverage

- full-scale tracing floor and template transfer
- stone dressing and carving sequence
- Gothic tracery layout, template, and cutout logic
- arch centering, voussoirs, and keystone layout
- rib vault ribs, webbing, and bosses
- timber frame-and-panel mortise/tenon logic
- wood moulding profile sequence
- wrought-iron scroll bending
- wrought-iron rivet/collar joins
- sheet metal bossing and repoussé/chasing reference

## Boundary

This is fabrication-informed modeling documentation only. It is not structural
advice, building-code guidance, conservation guidance, or fabrication-ready shop
drawings.

## Validation

```text
python3 -m json.tool data/architecture/taxonomy/craft_methods/craft_fabrication_methods_v0.json
PASS craft methods JSON parse

python3 -m py_compile scripts/validate_craft_fabrication_methods_v0.py
PASS py_compile

python3 scripts/validate_craft_fabrication_methods_v0.py
PASS craft fabrication method validation: methods=10 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_craft_fabrication_methods_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_component_style_sheets=5 reference_only=3
```

## Recommended Next Goal

Add `craft_method_ids` to per-asset workcards and draft `construction_graph_v0`
so UI tags can select fabrication-informed Blender tool sequences.
