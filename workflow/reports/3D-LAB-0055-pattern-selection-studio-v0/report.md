# 3D-LAB-0055 Pattern Selection Studio v0

## Result

Added a local browser studio for manual segment selection and coloring.

```text
deterministic segment JSON
-> browser SVG editor
-> click/box-select/color/role segments
-> deterministic selection recipe JSON
```

## Source Decisions

- The studio consumes `gameguy_pattern_segment_graph_v0`.
- It does not change the generated segment graph.
- User choices are saved as `pattern_selection_recipe_v0`.
- Default saved recipes live under `/tmp/gameguy_pattern_selection_studio_v0/selection_recipes/`.
- The app supports line click selection, visible-set selection, clearing, tag/id filtering, color, width, role, intersection toggle, download, save, and load.
- No Blender, mesh, material, or tool-plan behavior is touched.

## Run

```bash
python3 scripts/serve_pattern_selection_studio_v0.py
```

Default URL:

```text
http://127.0.0.1:8765
```

## Validation

```text
python3 scripts/serve_pattern_selection_studio_v0.py --validate-only
PASS pattern selection studio validation: segment_set=hex_rosette_pattern_segments_v0 segments=14324 default_selection=hex_rosette_user_selection_v0

python3 -m unittest tests/test_pattern_selection_studio_v0.py tests/test_audit_script_orbit_v0.py tests/test_asset_mill_retirement_readiness_v0.py
OK, 8 tests

python3 scripts/audit_script_orbit_v0.py --json-report /tmp/gameguy_script_orbit_0055.json
PASS script orbit audit: scripts=82 KEEP_CANONICAL=23, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=59, DELETE_LATER=0

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_0055_pattern_selection_studio.json
PASS generation pipeline validation: commands=38 json=259 include_blender=false
```

## Next

Use the studio to save the first user-selected motif recipe, then compile an omission preview:

```text
dense hex segment graph
-> user selection recipe
-> clean kept/omitted segment preview
-> closed-loop extraction
```
