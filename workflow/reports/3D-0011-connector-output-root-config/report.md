# 3D-0011: Connector Output Root Config

## Result

Added output-root/config support to `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`.

The compiler now supports:

```bash
--output-root <path>
--integrated-graph-path <path>
--no-regenerate-integrated
```

Default behavior is preserved when no arguments are passed.

## Why

The previous compiler always wrote generated connector outputs to fixed repo paths and could regenerate integrated-map proof outputs if dependencies were missing. The new options let validation write connector output into a temporary root and fail instead of regenerating integrated-map outputs.

## Behavior Check

Temp-output validation command:

```bash
rm -rf /tmp/connector_asset_placement_v0_test
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py \
  --output-root /tmp/connector_asset_placement_v0_test \
  --integrated-graph-path /Users/kogaryu/game/mosaic_dungeon_floor_v0/goal/architecture/integrated_map_scene_v0/integrated_map_scene_v0_compiled.json \
  --no-regenerate-integrated
```

Result:

- connector asset instances: `58`
- fit status counts: `{'pass': 4, 'warn': 4, 'fail': 0}`
- all supported connection types have policy: `true`
- generated outputs were written under `/tmp/connector_asset_placement_v0_test`

## Files Changed

- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `goal/workflow/reports/3D-0011-connector-output-root-config/report.md`
- `goal/workflow/reports/3D-0011-connector-output-root-config/receipt.json`

## Validation

Commands run:

```bash
python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool /tmp/connector_asset_placement_v0_test/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json >/dev/null
find /tmp/connector_asset_placement_v0_test/goal/architecture/connector_asset_kit_v0/recipes -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m json.tool /tmp/connector_asset_placement_v0_test/goal/architecture/integrated_map_scene_v0/connector_asset_placement_v0/connector_asset_placement_v0.json >/dev/null
python3 -m json.tool /tmp/connector_asset_placement_v0_test/goal/receipts/connector_asset_placement_v0.receipt.json >/dev/null
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

Result: PASS for compile/temp-output JSON checks.

The protected diff command still shows a pre-existing `.gitignore` change for `pattern_lab_2d/outputs/batches/*`; this task did not edit `.gitignore` or `pattern_lab_2d`.

## Remaining Risks

- Default compiler execution still writes to the normal generated output folders by design.
- The integrated graph fixture is still generated output; validation should pass `--integrated-graph-path` and `--no-regenerate-integrated` when dirtying the repo is not desired.
- The connector recipes still reference the measured v1 generated index as a local asset catalog.

## Next Recommended Task

Add a short README or registry entry under `data/architecture/assets/connectors/` documenting the connector source files, placement policy, and preferred validation command using `--output-root`.
