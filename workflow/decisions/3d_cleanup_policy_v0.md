# 3D Cleanup Policy v0

## Purpose

Set the cleanup rules for remaining Mac-side 3D prototype work.

## Active Rule

No archive lane by default.

Every item must be classified as one of:

- `FIX_POLISH`
- `PROMOTE_SOURCE`
- `DELETE_GENERATED`
- `LEAVE_PROTECTED`
- `DEFER`

## Current 3D Position

Committed and accepted:

- Generated sludge cleanup.
- Pattern Lab 2D batch-output fix, owned separately from 3D.
- 3D compiler cleanup/refactor.
- 3D map authoring contracts.
- 3D source dependency closure.
- 3D generator dependency reviews.

Still dirty on the 3D side:

- v2 measured asset mill outputs.
- connector asset kit outputs.
- map editor reports.
- plug connection graph outputs.
- Blender proof scripts.
- v2 asset/connector compiler scripts.

## Treatment Rules

### Source-like Data

If useful as future source:

1. Move or regenerate into a deliberate source lane later.
2. Validate it.
3. Commit only after source/output boundaries are clear.

Examples:

- measured asset recipes
- connector asset recipes
- contracts
- authoring templates

### Generated Output

If reproducible and not source:

1. Confirm generator/source exists.
2. Confirm no other committed code requires the exact file as source.
3. Delete after approval.

Examples:

- generated graph JSON
- generated report Markdown
- generated proof manifests

### Proof Scripts

If a proof script is useful:

1. Polish it into a proper tool with explicit inputs and output root.
2. Keep it out of hidden global state.
3. Do not commit if it only works because of local generated leftovers.

If not useful:

1. Delete after approval.

### Protected Work

Leave protected unless explicitly assigned:

- `pattern_lab_2d/`
- `.gitignore`
- other Dex-owned files

## Next Recommended 3D Decision

Pick one:

1. `FIX_POLISH` the v2 measured asset and connector kit into a clean source lane.
2. `DELETE_GENERATED` the report-only map editor folder after confirming it is not needed.
3. Review Blender proof scripts and choose polish or delete.

