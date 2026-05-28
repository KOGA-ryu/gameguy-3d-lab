# 3D-0010: Connector Placement Policy Source Lane

## Result

Implemented the next connector cleanup step without a new inbox packet.

The connector placement compiler now loads connection-type to connector-asset mapping from:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json
```

The compiler still loads connector recipe definitions from:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json
```

## Files Changed

- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json`
- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `mosaic_dungeon_floor_v0/goal/architecture/integrated_map_scene_v0/connector_asset_placement_v0/connector_asset_placement_v0.json`
- `mosaic_dungeon_floor_v0/goal/architecture/integrated_map_scene_v0/connector_asset_placement_v0/connector_asset_placement_v0_report.md`
- `mosaic_dungeon_floor_v0/goal/receipts/connector_asset_placement_v0.receipt.json`
- `goal/workflow/reports/3D-0010-connector-placement-policy-source-lane/report.md`
- `goal/workflow/reports/3D-0010-connector-placement-policy-source-lane/connector_placement_policy_comparison.json`
- `goal/workflow/reports/3D-0010-connector-placement-policy-source-lane/receipt.json`

## Behavior Check

- Connector asset instances: `58`
- Fit status counts: `{'pass': 4, 'warn': 4, 'fail': 0}`
- Source recipe count: `9`
- Placement policy connection types: `5`
- All supported connection types have policy: `true`

The compiler no longer duplicates the connection-type asset mapping in code. Role and fit-reason validation also derives from the source policy.

## Validation

Commands run:

```bash
python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json >/dev/null
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m json.tool mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json >/dev/null
find mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

Result: PASS for compile/JSON/generation checks.

The protected diff command still shows a pre-existing `.gitignore` change for `pattern_lab_2d/outputs/batches/*`; this task did not edit `.gitignore` or `pattern_lab_2d`.

## Remaining Risks

- `compile_connector_asset_placement_v0.py` can still regenerate integrated-map proof outputs if the integrated graph is absent.
- The connector source recipes still reference the measured v1 generated index as a local asset catalog.
- The expected connector asset IDs and supported connection types remain compiler acceptance constants; they are validation guardrails, not recipe/placement source data.

## Next Recommended Task

Review `compile_connector_asset_placement_v0.py` for output-root configurability so validation can run without dirtying generated proof folders unless explicitly requested.
