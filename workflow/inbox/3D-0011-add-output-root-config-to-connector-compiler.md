Packet-Type: task
Packet-ID: 3D-0011
Status: completed
Owner: planner_dex
Target: mac_3d_architecture

# 3D-0011: Add Output-Root Config To Connector Compiler

## Objective

Refactor `compile_connector_asset_placement_v0.py` so validation can run into an explicit output root instead of always dirtying canonical generated proof folders.

This is a behavior-preserving workflow cleanup. The compiler should still support the current default output paths, but tests and worker validation must be able to write to a temporary or task-local output directory.

## Scope

Allowed source edits:

- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`

Allowed report outputs:

- `/Users/kogaryu/game/goal/workflow/reports/3D-0011-add-output-root-config-to-connector-compiler/report.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0011-add-output-root-config-to-connector-compiler/output_root_comparison.json`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0011-add-output-root-config-to-connector-compiler/receipt.json`

Optional temporary validation output:

- `/Users/kogaryu/game/goal/workflow/tmp/3D-0011/`

## Non-Goals

- Do not touch `/Users/kogaryu/game/mosaic_dungeon_floor_v0/pattern_lab_2d/`.
- Do not edit `/Users/kogaryu/game/mosaic_dungeon_floor_v0/.gitignore`.
- Do not change connector recipe contents.
- Do not change connector placement policy contents unless validation proves a path typo.
- Do not redesign generated schema.
- Do not run Blender.
- Do not create meshes, renders, screenshots, or visual proof.
- Do not archive, delete, stage, or commit files.

## Required Inputs

Read these before editing:

- `/Users/kogaryu/game/goal/workflow/registry.md`
- `/Users/kogaryu/game/goal/workflow/decisions/3d_cleanup_policy_v0.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0010-connector-placement-policy-source-lane/report.md`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_placement_policy_v0.json`

## Required Work

1. Inspect current hardcoded output paths in `compile_connector_asset_placement_v0.py`.
2. Add a narrow CLI option or function parameter for output root.
3. Preserve current defaults when no output root is provided.
4. Make all generated connector output paths derive from the selected output root.
5. Ensure source inputs still load from canonical source paths unless explicitly configured by existing code.
6. Run the compiler once with default paths and once with a temporary output root.
7. Compare the default output and temporary output for behavioral equivalence.

Preferred CLI shape:

```bash
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py --output-root goal/workflow/tmp/3D-0011/connector_asset_kit_v0
```

If a different argument name is already more consistent with the repo, use it and document why.

## Output Requirements

Create this report folder:

`/Users/kogaryu/game/goal/workflow/reports/3D-0011-add-output-root-config-to-connector-compiler/`

Report files:

- `report.md`
- `output_root_comparison.json`
- `receipt.json`

The report must include:

- Files changed.
- New CLI/config interface.
- Which output paths are now configurable.
- Which source paths remain canonical.
- Default-run behavior comparison.
- Temporary-output-run behavior comparison.
- Validation commands run.
- Any changed metadata fields.
- Remaining risks.
- Recommended next worker task.

The receipt must include:

- `packet_id`
- `files_changed`
- `validation_run`
- `default_output_run`
- `temporary_output_run`
- `protected_paths_touched`
- `blender_run`
- `staged_or_committed`
- `production_claim`
- `structural_claim`
- `recommended_next_task`

## Acceptance Criteria

- Compiler supports an explicit output root.
- Current default output behavior remains available.
- Temporary output run does not write into canonical generated proof folders.
- Generated connector asset instance count remains `58`.
- Generated fit status remains `{'pass': 4, 'warn': 4, 'fail': 0}`.
- Connector source manifest still loads from canonical source.
- Connector placement policy still loads from canonical source.
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
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py --output-root goal/workflow/tmp/3D-0011/connector_asset_kit_v0
python3 -m json.tool mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/connector_asset_kit_v0_index.json >/dev/null
python3 -m json.tool goal/workflow/tmp/3D-0011/connector_asset_kit_v0/connector_asset_kit_v0_index.json >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0011-add-output-root-config-to-connector-compiler/output_root_comparison.json >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0011-add-output-root-config-to-connector-compiler/receipt.json >/dev/null
git diff -- mosaic_dungeon_floor_v0/pattern_lab_2d mosaic_dungeon_floor_v0/.gitignore
```

The final `git diff` may show pre-existing protected changes. The worker must state whether this task added any new protected diff. Expected answer: no.

## Report Back

Report back with:

- What changed.
- The exact output-root interface.
- Whether default behavior stayed stable.
- Whether temporary output stayed isolated.
- Whether protected 2D or `.gitignore` paths were untouched.
- The next narrow task.
