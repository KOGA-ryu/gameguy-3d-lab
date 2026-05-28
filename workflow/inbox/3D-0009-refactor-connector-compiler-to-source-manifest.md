Packet-Type: task
Packet-ID: 3D-0009
Status: proposed
Owner: planner_dex
Target: mac_3d_architecture

# 3D-0009: Refactor Connector Compiler To Source Manifest

## Objective

Refactor the connector asset placement compiler so connector definitions come from the promoted source manifest instead of hardcoded in-script recipe data.

This is a behavior-preserving refactor. The current generated connector output must remain equivalent unless a real mismatch is found and reported.

## Scope

Work only in the 3D architecture domain.

Primary source lane:

- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0/*.json`

Primary script to edit:

- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`

Reference/generated comparison input:

- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json`
- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes/*.json`

Prior worker report:

- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/report.md`
- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/connector_recipe_decision_matrix.json`
- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/receipt.json`

## Non-Goals

- Do not touch `mosaic_dungeon_floor_v0/pattern_lab_2d/`.
- Do not touch `.gitignore`.
- Do not run Blender.
- Do not create meshes or renders.
- Do not change gameplay movement logic.
- Do not redesign connector dimensions.
- Do not delete generated connector output.
- Do not archive anything.
- Do not stage or commit.

## Required Inputs

Read:

- `goal/workflow/registry.md`
- `goal/workflow/decisions/3d_cleanup_policy_v0.md`
- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/report.md`
- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- all promoted connector recipe JSON files
- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`

## Required Work

1. Inspect the current `CONNECTOR_RECIPES` constant in `compile_connector_asset_placement_v0.py`.
2. Compare it to the promoted source manifest and source recipes.
3. Add a loader function for promoted connector source recipes.
4. Replace hardcoded recipe use with loaded source recipe data.
5. Preserve the generated connector kit/index/report behavior unless a mismatch is documented.
6. Add explicit validation that required connector asset IDs exist in the promoted manifest.
7. Add explicit validation that every loaded recipe has:
   - `asset_id`
   - `dimensions_m`
   - `semantic_roles`
   - `sockets`
   - no production/structural/fabrication/historical claims
8. Write a report packet under `goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/`.

## Implementation Notes

Preferred shape:

```python
CONNECTOR_SOURCE_MANIFEST_PATH = ROOT / "data" / "architecture" / "assets" / "connectors" / "connector_asset_manifest_v0.json"

def load_connector_source_recipes() -> dict[str, dict[str, Any]]:
    ...
```

Avoid global mutation. Avoid importing from Blender scripts. Keep this compiler stdlib-only.

If old generated recipe schema differs from promoted source recipe schema, adapt at the boundary with a small helper function. Do not mutate promoted source files unless the source file is objectively invalid and the report explains the fix.

## Outputs

Required report packet:

```text
goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/
  report.md
  connector_source_manifest_comparison.json
  receipt.json
```

Allowed source edits:

```text
mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
```

Allowed only if needed for objective source validation bug:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0/*.json
```

## Acceptance Criteria

- `compile_connector_asset_placement_v0.py` no longer depends on a hardcoded `CONNECTOR_RECIPES` dictionary as the source of connector truth.
- Connector definitions load from `connector_asset_manifest_v0.json`.
- All 9 expected connector asset IDs are loaded.
- Existing generated connector placement behavior is preserved or every difference is explicitly reported.
- Generated connector report/index can still be produced.
- No 2D files touched.
- `.gitignore` untouched.
- No Blender, no meshes, no renders.
- No archive/delete/stage/commit.

## Validation

Run from `/Users/kogaryu/game`:

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
```

Also run:

```bash
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

Expected: no changes from this task.

## Report Back

Final response must include:

- files changed
- whether compiler now loads promoted manifest
- whether generated connector output changed
- validation commands run
- risks remaining
- next recommended worker task

