# 3D-LAB-0078 Imported Taxonomy Shape Crosswalk V0

## Goal

Create the first normalized crosswalk from imported taxonomy shape/proxy phrases
to repo-native geometry terms, Blender tool IDs, source fields, drafting tags,
asset families, and promotion status.

## Added

- `data/asset_taxonomy/normalized_domains_v0/shape_type_crosswalk_v0.json`
- `docs/research/imported_asset_taxonomies_v0/shape_type_crosswalk_v0.md`
- `scripts/validate_imported_taxonomy_crosswalk_v0.py`
- `tests/test_validate_imported_taxonomy_crosswalk_v0.py`

## Updated

- `README.md`
- `data/asset_taxonomy/README.md`
- `data/asset_taxonomy/imported_taxonomy_manifest_v0.json`
- `docs/research/imported_asset_taxonomies_v0/README.md`
- `docs/research/imported_asset_taxonomies_v0/organization_plan_v0.md`

## Coverage

V0 covers 26 representative imported shape families:

- dome and cone shells
- masks, shields, armor plates, lamellar rows, rivet grids
- quilted channels, woven sheets, cloth shells, flat pattern panels
- seam curves, stitch dash arrays, ribbon/binding strips
- capsule proxies, ellipsoid pads, joint proxies, cord curves
- rings, blades, spline plates, measuring ribbons, spools, peg/bar frames,
  buckle frames, and wire spirals

## Boundary

This crosswalk is source triage, not an active generator input. It does not
compile assets, run Blender, or promote imported terms into canonical recipes.

## Validation

```text
python3 -m json.tool data/asset_taxonomy/normalized_domains_v0/shape_type_crosswalk_v0.json
PASS crosswalk JSON parse

python3 scripts/validate_imported_taxonomy_crosswalk_v0.py
PASS imported taxonomy crosswalk validation: entries=26 sources=5 geometry_terms=75 tools=97

python3 -m unittest tests/test_validate_imported_taxonomy_crosswalk_v0.py
OK

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 source_component_style_sheets=5 reference_only=3
```

## Recommended Next Goal

Define the future drafting source schema, `construction_graph_v0`, using this
crosswalk's `drafting_tags` as the first vocabulary for lines, cells, cutters,
ribs, seams, sockets, profiles, and repeated motifs.

