# Connector Asset Source Lane v0

This folder is the source lane for the 3D connector asset kit. Edit these files when changing connector assets or connector placement policy:

- `connector_asset_manifest_v0.json` lists the source connector recipes and their local recipe paths.
- `connector_asset_recipes_v0/*.json` defines the measured connector asset recipes used by the connector kit compiler.
- `connector_placement_policy_v0.json` maps supported connection types to connector asset IDs and placement roles.

Generated connector outputs live outside this source lane:

- `goal/architecture/connector_asset_kit_v0/`
- `goal/architecture/integrated_map_scene_v0/connector_asset_placement_v0/`
- `goal/receipts/connector_asset_placement_v0.receipt.json`

Do not edit generated connector outputs as source. Regenerate them through `scripts/compile_connector_asset_placement_v0.py`.

## Validation

Use a temporary output root when checking connector source changes without dirtying the normal generated output folders:

```bash
rm -rf /tmp/connector_asset_placement_v0_test
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py \
  --output-root /tmp/connector_asset_placement_v0_test \
  --integrated-graph-path /Users/kogaryu/game/mosaic_dungeon_floor_v0/goal/architecture/integrated_map_scene_v0/integrated_map_scene_v0_compiled.json \
  --no-regenerate-integrated
```

Expected current result:

- connector asset instances: `58`
- fit status counts: `{'pass': 4, 'warn': 4, 'fail': 0}`

Also check the source JSON files:

```bash
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
```

## Guardrails

- Keep the connector source lane scoped to 3D architecture connector assets.
- Do not edit `pattern_lab_2d/` for connector asset work.
- Do not edit `.gitignore` for connector asset work.
- Do not silently scale connector assets in placement.
- Do not add production, structural, fabrication, gym/museum approval, or historical accuracy claims.
- Add new connector recipes through the manifest instead of creating a parallel catalog.
- Use local repo sources only unless the task explicitly changes into research mode.
