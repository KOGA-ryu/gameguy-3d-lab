Packet-Type: task
Packet-ID: 3D-LAB-0002
Status: proposed
Owner: planner_dex
Target: gameguy-3d-lab

# 3D-LAB-0002: Narrow Workflow And Factory Contracts

## Objective

Review and narrow the generic workflow/factory contracts so they describe this repo's 3D architecture lab only, not inherited 2D Pattern Lab, mosaic tile, visual curation, or broad factory language.

The goal is clean contract language before validators, workers, and future C++ tools start depending on these records.

## Scope

Work only in:

`/Users/kogaryu/gameguy-3d-lab`

Primary contracts to review:

- `contracts/lane_registry_v0.json`
- `contracts/factory_manifest_v0.json`
- `contracts/job_contract_v0.json`
- `contracts/artifact_manifest_v0.json`
- `contracts/curation_status_v0.json`

Allowed docs/report outputs:

- `workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/report.md`
- `workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/contract_decision_matrix.json`
- `workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/receipt.json`

Optional:

- update `contracts/README.md` if the ownership wording needs a small clarification.

## Non-Goals

- Do not touch the old Mac prototype repo.
- Do not edit or restore quarantined 2D/mosaic contracts.
- Do not generate assets, maps, renders, meshes, Blender files, screenshots, or proof output.
- Do not run Blender.
- Do not port anything to C++.
- Do not rewrite the workflow system.
- Do not remove a contract only because it has generic language; classify it first.
- Do not stage, commit, or push unless explicitly instructed after reporting.

## Required Inputs

Read before editing:

- `README.md`
- `FOLDER_OWNERSHIP.md`
- `contracts/README.md`
- `contracts/quarantine_2d_mosaic_v0/README.md`
- `workflow/reports/3D-LAB-0001-contract-folder-ownership-cleanup/report.md`

## Required Work

1. Inspect the five primary contracts listed in Scope.
2. Classify each contract as one of:
   - `KEEP_AS_IS`
   - `KEEP_WITH_3D_LANGUAGE_EDIT`
   - `QUARANTINE_2D_OR_MOSAIC`
   - `DEFER_REVIEW`
3. For every field that mentions 2D Pattern Lab, mosaic tiles, image/contact-sheet curation, or broad factory lanes, decide whether to:
   - remove it,
   - rename it to a 3D/map/building equivalent,
   - keep it because it is genuinely shared workflow language,
   - quarantine the contract.
4. Make only minimal edits needed to remove inherited 2D/mosaic ambiguity.
5. Preserve JSON validity and schema intent.
6. Write a report and decision matrix.

## Decision Rules

Keep language that supports:

- 3D architecture source data
- terrain graphs
- map graphs
- building graphs
- connector assets
- measured architecture components
- geometry dictionaries
- Blender proof scripts
- future C++/Linux migration
- workflow packets and validation reports

Remove or quarantine language that is only about:

- 2D Pattern Lab
- mosaic tile output
- Aseprite export
- ornament contact sheets
- image curation dashboards
- rendered study approval
- Zoo-only visual browsing

If a term is ambiguous, do not invent a replacement. Record it as `DEFER_REVIEW`.

## Output Requirements

Create:

`workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/`

Files:

- `report.md`
- `contract_decision_matrix.json`
- `receipt.json`

The decision matrix must include one record per reviewed contract:

```json
{
  "contract_path": "contracts/lane_registry_v0.json",
  "decision": "KEEP_WITH_3D_LANGUAGE_EDIT",
  "2d_terms_found": [],
  "edits_made": [],
  "deferred_questions": [],
  "validation_status": "pass"
}
```

The receipt must include:

- `packet_id`
- `status`
- `files_changed`
- `contracts_reviewed`
- `contracts_quarantined`
- `validation_run`
- `old_repo_touched`
- `blender_run`
- `generated_outputs_created`
- `staged_or_committed`
- `recommended_next_task`

## Acceptance Criteria

- All five primary contracts are reviewed and classified.
- Any active contract language that is clearly 2D/mosaic-only is removed, narrowed, or explicitly deferred.
- No quarantined 2D/mosaic contracts are restored to active root.
- JSON validation passes.
- Python scripts still compile.
- No media/proof/mesh files are created.
- No old Mac prototype files are touched.
- Repo remains unstaged unless user explicitly says to commit.

## Validation

Run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
python3 -m json.tool workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/contract_decision_matrix.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/receipt.json >/dev/null
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

Expected:

- JSON and Python validation pass.
- `pattern_lab_2d` scan prints nothing.
- media/mesh/proof scan prints nothing.
- `git status --short` shows only the intentional contract/report/doc edits.

## Report Back

Report back with:

- Contracts reviewed.
- Contracts edited.
- Contracts quarantined, if any.
- Ambiguous terms deferred.
- Validation results.
- Recommended next task.
