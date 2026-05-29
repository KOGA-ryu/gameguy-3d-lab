Packet-Type: task
Packet-ID: 3D-LAB-0003
Status: proposed
Owner: planner_dex
Target: gameguy-3d-lab

# 3D-LAB-0003: Contract Vocabulary Sweep

## Objective

Review remaining active contracts for inherited 2D, mosaic, ornament, contact-sheet, Zoo, or broad visual-lab vocabulary. Narrow terms to 3D architecture use, quarantine only clearly 2D-only contracts, or explicitly defer ambiguous terms.

This protects the clean repo language before validators and future C++ tools rely on these contracts.

## Scope

Work only in:

`/Users/kogaryu/gameguy-3d-lab`

Primary contracts:

- `contracts/cube_math_shape_recipe_v0.json`
- `contracts/plot_shape_taxonomy_v0.json`
- `contracts/architectural_shape_dictionary_v0.json`
- `contracts/architectural_measurement_record_v0.json`
- `contracts/architectural_measurement_source_v0.json`
- `contracts/map_authoring_contract_v0.json`
- `contracts/pathway_connection_contract_v0.json`
- `contracts/asset_mill_solid_recipe_v0.json`

Secondary pass:

- all remaining active `contracts/*.json`, excluding `contracts/quarantine_2d_mosaic_v0/`.

Allowed report outputs:

- `workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/report.md`
- `workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/vocabulary_decision_matrix.json`
- `workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/receipt.json`

## Non-Goals

- Do not touch the old Mac prototype repo.
- Do not edit quarantined 2D/mosaic contracts unless documenting that they remain quarantined.
- Do not generate assets, maps, renders, meshes, screenshots, or proof outputs.
- Do not run Blender.
- Do not port anything to C++.
- Do not rewrite contracts wholesale.
- Do not stage, commit, or push unless explicitly instructed after reporting.

## Required Inputs

Read before editing:

- `README.md`
- `FOLDER_OWNERSHIP.md`
- `contracts/README.md`
- `contracts/quarantine_2d_mosaic_v0/README.md`
- `workflow/reports/3D-LAB-0001-contract-folder-ownership-cleanup/report.md`
- `workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/report.md`

## Required Work

1. Search active contracts for inherited terms:
   - `pattern_lab`
   - `pattern_lab_2d`
   - `mosaic`
   - `tile`
   - `contact_sheet`
   - `zoo`
   - `ornament`
   - `sprite`
   - `aseprite`
   - `rendered`
   - `png`
   - `image`
2. For each hit, classify the term:
   - `VALID_3D_TERM`
   - `RENAME_TO_3D_TERM`
   - `REMOVE_2D_ONLY`
   - `QUARANTINE_CONTRACT`
   - `DEFER_REVIEW`
3. Make minimal edits only where the replacement is obvious.
4. Preserve JSON validity and contract intent.
5. Write the vocabulary decision matrix and report.

## Decision Rules

Keep terms that support:

- 3D architecture source data
- terrain or map graph source
- building graph source
- connector assets
- measured components
- geometry dictionary terms
- Blender proof scripts as source scripts
- future C++/Linux migration

Narrow or remove terms that imply:

- 2D Pattern Lab ownership
- mosaic tile output
- visual contact-sheet browsing
- rendered image approval
- Zoo-only art curation
- sprite/Aseprite workflows

If a term like `tile` appears in a terrain/topology context, do not remove it blindly. Classify whether it means terrain cell, map tile, or 2D mosaic tile.

## Output Requirements

Create:

`workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/`

Files:

- `report.md`
- `vocabulary_decision_matrix.json`
- `receipt.json`

The matrix must include records like:

```json
{
  "contract_path": "contracts/cube_math_shape_recipe_v0.json",
  "term": "contact_sheet",
  "decision": "DEFER_REVIEW",
  "reason": "Preview vocabulary remains ambiguous; not enough evidence to rename safely.",
  "edit_made": false
}
```

## Acceptance Criteria

- Primary contracts are reviewed.
- Secondary active contracts are scanned.
- Obvious 2D-only language is removed, renamed, or deferred.
- No quarantined 2D/mosaic contract is restored to active root.
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
python3 -m json.tool workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/vocabulary_decision_matrix.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/receipt.json >/dev/null
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

## Report Back

Report back with:

- Contracts reviewed.
- Terms removed or renamed.
- Terms deferred.
- Contracts quarantined, if any.
- Validation results.
- Recommended next task.
