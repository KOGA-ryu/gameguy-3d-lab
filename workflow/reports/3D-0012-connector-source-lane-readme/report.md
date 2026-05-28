# 3D-0012: Connector Source Lane README

## Result

Added source-lane documentation for the 3D connector asset kit:

- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/README.md`

The README identifies the editable connector source files, the generated output folders, the preferred temp-output validation command, and the connector-lane guardrails.

## Why

The connector kit now has source recipes, a source manifest, a placement policy, and compiler support for temporary output roots. The source lane needed a local entry point so future workers know where to edit and how to validate without treating generated outputs as source.

## Files Changed

- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/README.md`
- `goal/workflow/reports/3D-0012-connector-source-lane-readme/report.md`
- `goal/workflow/reports/3D-0012-connector-source-lane-readme/receipt.json`

## Validation

Commands run:

```bash
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

Result: PASS for source JSON checks and compiler syntax check.

The protected diff command still shows a pre-existing `.gitignore` change for `pattern_lab_2d/outputs/batches/*`; this task did not edit `.gitignore` or `pattern_lab_2d`.

## Non-Goals Respected

- No Blender run.
- No meshes or renders created.
- No archive, delete, stage, or commit operation performed.
- No `pattern_lab_2d/` edits.
- No `.gitignore` edits by this task.

## Next Recommended Task

Use the connector source-lane README as the entry point for the next connector recipe or placement policy change, then validate through the temp output root before regenerating canonical goal outputs.
