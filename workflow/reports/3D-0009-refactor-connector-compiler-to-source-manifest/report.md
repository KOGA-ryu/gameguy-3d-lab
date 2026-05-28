# 3D-0009: Refactor Connector Compiler To Source Manifest

## Result

Implemented the behavior-preserving refactor. `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py` now loads connector definitions from:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json
```

The old hardcoded `CONNECTOR_RECIPES` dictionary has been removed as the source of truth. The compiler validates the promoted manifest, loads all 9 expected connector asset IDs, validates each recipe shape/no-claim fields, and then regenerates the same connector recipe JSON into the generated output lane.

## Files Changed

- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json` regenerated with source-manifest provenance
- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_report.md` regenerated with source-manifest provenance
- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes/*.json` regenerated from promoted source recipes
- `mosaic_dungeon_floor_v0/goal/architecture/integrated_map_scene_v0/connector_asset_placement_v0/connector_asset_placement_v0.json` regenerated
- `mosaic_dungeon_floor_v0/goal/architecture/integrated_map_scene_v0/connector_asset_placement_v0/connector_asset_placement_v0_report.md` regenerated
- `goal/receipts/connector_asset_placement_v0.receipt.json` regenerated
- `goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/report.md`
- `goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/connector_source_manifest_comparison.json`
- `goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/receipt.json`

The validation run also triggered existing integrated-map generated outputs because `compile_connector_asset_placement_v0.py` calls `compile_integrated_map_scene_v0.main()` when the integrated graph is absent. No source gameplay movement logic was changed.

## Behavior Comparison

- Promoted source recipe count: `9`
- Generated connector index asset count: `9`
- All promoted source recipes match regenerated connector-kit recipes exactly: `True`
- All expected connector source IDs loaded: `True`
- Connector source recipe count loaded by compiler: `9`
- Connector asset instances generated: `58`
- Fit status counts: `{'pass': 4, 'warn': 4, 'fail': 0}`

Intentional metadata differences:

- Generated connector index now records `source_manifest`.
- Generated connector index rules now include `recipes_loaded_from_source_manifest`.
- Generated connector placement output now records `connector_source_manifest`, `connector_source_recipe_count`, and `all_expected_connector_source_ids_loaded`.
- Timestamps update when the compiler runs.

## Validation

Commands run:

```bash
python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 \
  | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json >/dev/null
find mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes -name '*.json' -print0 \
  | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/connector_source_manifest_comparison.json >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/receipt.json >/dev/null
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

JSON/compile validations passed. The protected diff command shows pre-existing `.gitignore` / `pattern_lab_2d` dirt unrelated to this task; this task did not edit those paths.

## Remaining Risks

- `compile_connector_asset_placement_v0.py` still hardcodes the connection-type to asset-ID mapping. That is placement policy, not connector recipe source data, but it can be promoted to policy data later.
- Running this compiler can still regenerate integrated-map proof outputs when the integrated graph is missing.
- The promoted connector recipes still reference the measured v1 generated index as a local asset catalog, inherited from the source-lane promotion.

## Next Recommended Worker Task

Create a 3D cleanup task to separate connector placement policy from compiler code: move the mapping from `connection_type` to connector asset IDs into a small source policy file under `data/architecture/assets/connectors/`, then make the compiler load that policy while preserving the current generated placement output.
