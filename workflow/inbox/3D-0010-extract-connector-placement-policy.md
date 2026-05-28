Packet-Type: task
Packet-ID: 3D-0010
Status: proposed
Owner: planner_dex
Target: mac_3d_architecture

# 3D-0010: Extract Connector Placement Policy

## Objective

Move connector placement behavior out of `compile_connector_asset_placement_v0.py` and into a small source policy file:

`/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json`

Preserve current generated behavior. This is a source-polish task, not a redesign.

## Scope

Allowed source edits:

- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json`

Allowed report outputs:

- `/Users/kogaryu/game/goal/workflow/reports/3D-0010-extract-connector-placement-policy/report.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0010-extract-connector-placement-policy/connector_placement_policy_comparison.json`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0010-extract-connector-placement-policy/receipt.json`

Existing source context:

- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0/`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/`

## Non-Goals

- Do not touch `/Users/kogaryu/game/mosaic_dungeon_floor_v0/pattern_lab_2d/`.
- Do not edit `/Users/kogaryu/game/mosaic_dungeon_floor_v0/.gitignore`.
- Do not run Blender.
- Do not create meshes, renders, screenshots, or new visual proof.
- Do not redesign connector dimensions.
- Do not add movement/pathfinding logic.
- Do not archive, delete, stage, or commit files.
- Do not change connector recipes unless validation proves the current source recipe is malformed.

## Required Inputs

Read these before editing:

- `/Users/kogaryu/game/goal/workflow/registry.md`
- `/Users/kogaryu/game/goal/workflow/decisions/3d_cleanup_policy_v0.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/report.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/report.md`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json`

## Required Work

1. Inspect the current connector placement logic in `compile_connector_asset_placement_v0.py`.
2. Identify all connection-type to connector-asset mappings currently embedded in code.
3. Create `connector_placement_policy_v0.json` as the source of truth for those mappings.
4. Refactor the compiler to load and validate the policy file.
5. Preserve current output behavior unless a mismatch is explicitly documented.
6. Write a comparison JSON proving what changed and what stayed the same.

The policy must cover the current behavior for:

- `road_threshold`
- `flat_pathway`
- `ramp_pathway`
- `stepped_pathway`
- `bridge_link`

The policy should explicitly encode current asset choices such as:

- `measured_threshold_landing_v1`
- `measured_pathway_slab_unit_v1`
- `measured_ramp_pathway_unit_v1`
- `measured_stepped_pathway_unit_v1`
- `measured_bridge_deck_unit_v1`
- `measured_bridge_abutment_v1`
- `measured_bridge_rail_unit_v1`

If the compiler currently derives repeated units, bridge rails, abutments, offsets, fit warnings, or no-scaling decisions from code, the policy should record the rule clearly while leaving numeric behavior unchanged.

## Output Requirements

Create this report folder:

`/Users/kogaryu/game/goal/workflow/reports/3D-0010-extract-connector-placement-policy/`

Report files:

- `report.md`
- `connector_placement_policy_comparison.json`
- `receipt.json`

The report must include:

- Files changed.
- Whether the compiler now loads placement policy from source JSON.
- Which behavior remains in code and why.
- Generated output comparison before/after, if available.
- Validation commands run.
- Any behavior mismatch.
- Remaining risks.
- Recommended next worker task.

The receipt must include:

- `packet_id`
- `files_changed`
- `validation_run`
- `protected_paths_touched`
- `blender_run`
- `staged_or_committed`
- `production_claim`
- `structural_claim`
- `recommended_next_task`

## Acceptance Criteria

- `compile_connector_asset_placement_v0.py` no longer owns the connection-type to connector-asset mapping as hardcoded behavior source.
- `connector_placement_policy_v0.json` declares every currently supported connection type.
- Connector asset IDs referenced by policy exist in `connector_asset_manifest_v0.json`.
- Generated connector placement behavior remains stable:
  - expected connector recipe count remains `9`
  - expected generated asset instance count remains `58`
  - expected fit status remains `{'pass': 4, 'warn': 4, 'fail': 0}`
- Any intentional metadata-only output changes are documented.
- No 2D files are touched.
- `.gitignore` is not edited.
- No Blender/renders/meshes are produced.
- No files are staged or committed.

## Validation

Run from `/Users/kogaryu/game`:

```bash
python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json >/dev/null
find mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0010-extract-connector-placement-policy/connector_placement_policy_comparison.json >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0010-extract-connector-placement-policy/receipt.json >/dev/null
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

The final `git diff` may show pre-existing protected changes. The worker must state whether this task added any new protected diff. Expected answer: no.

## Report Back

Report back with:

- What changed.
- What validation passed.
- Whether output behavior stayed stable.
- Whether protected 2D or `.gitignore` paths were untouched.
- The next narrow task.
