Packet-Type: task
Packet-ID: 3D-0008
Status: proposed
Owner: planner_dex
Target: mac_3d_architecture

# 3D-0008: Polish Connector Kit Source Lane

## Objective

Turn the current 3D connector asset kit from a mixed generated/proof folder into a clean source-lane decision.

The goal is not to redesign connector assets. The goal is to determine whether the connector recipes are useful enough to promote, then separate source-like connector recipes from generated reports/indexes.

## Scope

Work only in the 3D architecture domain.

Primary inputs:

- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/`
- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `mosaic_dungeon_floor_v0/contracts/pathway_connection_contract_v0.json`
- `mosaic_dungeon_floor_v0/data/architecture/map_templates/plug_connection_policy_v0.json`
- `goal/review/3d_generated_folder_review_v0/generated_folder_review.md`
- `goal/review/3d_generator_dependency_review_v0/dependency_review.md`
- `goal/workflow/decisions/3d_cleanup_policy_v0.md`

Candidate connector recipes:

- `measured_pathway_slab_unit_v1`
- `measured_threshold_landing_v1`
- `measured_ramp_pathway_unit_v1`
- `measured_stepped_pathway_unit_v1`
- `measured_bridge_deck_unit_v1`
- `measured_bridge_abutment_v1`
- `measured_bridge_rail_unit_v1`
- `measured_retaining_wall_unit_v1`
- `measured_curb_edge_unit_v1`

## Non-Goals

- Do not touch `mosaic_dungeon_floor_v0/pattern_lab_2d/`.
- Do not touch `.gitignore`.
- Do not create Blender renders.
- Do not create meshes.
- Do not change gameplay movement logic.
- Do not change connector dimensions unless a validation bug proves a dimension is invalid.
- Do not stage or commit.
- Do not archive anything.
- Do not delete anything unless the user explicitly approves after review.

## Required Inputs

Read:

- `goal/workflow/registry.md`
- `goal/workflow/decisions/3d_cleanup_policy_v0.md`
- `goal/review/3d_generated_folder_review_v0/generated_folder_review.md`
- `goal/review/3d_generator_dependency_review_v0/dependency_review.md`
- `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json`
- all JSON recipes under `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes/`
- `mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`

## Work Plan

1. Inspect the current connector recipes and index.
2. Classify each connector recipe as:
   - `PROMOTE_SOURCE`
   - `FIX_POLISH`
   - `DELETE_GENERATED`
   - `DEFER`
3. Decide the clean source-lane target path for promoted connector recipes.
4. If implementing source-lane promotion, create only the minimal source lane needed.
5. Keep generated reports/indexes out of source unless they are explicitly transformed into source manifests.
6. Update or create a validator only if needed to prove connector recipe integrity.
7. Write a report packet under `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/`.

## Preferred Source Lane

If recipes are promoted, prefer:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/
  connector_asset_recipes_v0/
    measured_pathway_slab_unit_v1.json
    measured_threshold_landing_v1.json
    ...
  connector_asset_manifest_v0.json
```

Keep old generated folder untouched unless explicitly told otherwise.

## Outputs

Required report packet:

```text
goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/
  report.md
  connector_recipe_decision_matrix.json
  receipt.json
```

If source promotion is implemented, also create:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0/*.json
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json
```

## Acceptance Criteria

- Every connector recipe is classified.
- The report clearly states whether connector recipes should be promoted, fixed, deleted, or deferred.
- If promoted, source recipes live under `data/architecture/assets/connectors/`, not `goal/architecture/`.
- Generated report/index output remains separate from source.
- No 2D files touched.
- `.gitignore` untouched.
- No Blender render or mesh output.
- No archive action.
- No staging or commit.

## Validation

Run:

```bash
cd /Users/kogaryu/game

find mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0 -name '*.json' -print0 \
  | xargs -0 -n 1 python3 -m json.tool >/dev/null

python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
```

If a new source manifest is created:

```bash
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 \
  | xargs -0 -n 1 python3 -m json.tool >/dev/null
```

Validate report receipt:

```bash
python3 -m json.tool goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/receipt.json >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/connector_recipe_decision_matrix.json >/dev/null
```

## Report Back

In final response, report:

- whether source promotion was implemented or only recommended
- files created
- validation commands run
- remaining risks
- exact next recommended worker task

