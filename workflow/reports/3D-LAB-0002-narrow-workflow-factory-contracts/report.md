# 3D-LAB-0002: Narrow Workflow And Factory Contracts

## Result

Reviewed and narrowed the five workflow/factory contracts requested by the packet:

- `contracts/lane_registry_v0.json`
- `contracts/factory_manifest_v0.json`
- `contracts/job_contract_v0.json`
- `contracts/artifact_manifest_v0.json`
- `contracts/curation_status_v0.json`

All five were classified as `KEEP_WITH_3D_LANGUAGE_EDIT`. No contract was quarantined.

## Edits Made

`lane_registry_v0.json` had the clearest active 2D leakage. It no longer lists `pattern_lab_2d` or `pattern_lab_3d` as required lane IDs. The lane list is now scoped to 3D lab work: research, measurement, architecture assets, terrain, map graphs, building graphs, connector assets, Blender proof scripts, validation, and workflow.

The generic factory contracts were kept but narrowed:

- `factory_manifest_v0.json` now describes a 3D architecture lab workflow index.
- `job_contract_v0.json` now describes 3D architecture lab workflow jobs.
- `artifact_manifest_v0.json` now describes 3D architecture lab workflow artifacts and includes scoped artifact kinds.
- `curation_status_v0.json` now uses review language in its purpose and rules, while keeping the existing filename/schema for compatibility.

`contracts/README.md` received a small clarification that active workflow/factory records are narrowed to 3D architecture lab lanes.

## Quarantine

No new contracts were quarantined. Existing quarantined 2D/mosaic contracts under `contracts/quarantine_2d_mosaic_v0/` were not edited or restored.

## Deferred Questions

- `curation_status_v0.json` still has a curation-oriented filename and schema value. The active purpose and rules now use review language, but a future version can rename the contract if downstream consumers are updated.
- Non-primary contracts still contain isolated ambiguous terms such as `slice_contact_sheet_png` in `contracts/cube_math_shape_recipe_v0.json`; that file was outside this packet's primary review scope.

## Validation

Commands run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
python3 -m json.tool workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/contract_decision_matrix.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0002-narrow-workflow-factory-contracts/receipt.json >/dev/null
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

Result: PASS for JSON validation and Python compile. The path/media scans printed no matching files.

## Non-Goals Respected

- Did not touch the old Mac prototype repo.
- Did not edit or restore quarantined 2D/mosaic contracts.
- Did not run Blender.
- Did not generate assets, maps, renders, meshes, screenshots, or proof outputs.
- Did not stage, commit, or push.

## Next Recommended Task

Review `contracts/cube_math_shape_recipe_v0.json` and `contracts/plot_shape_taxonomy_v0.json` for remaining ambiguous pattern/ornament/contact-sheet vocabulary, then either narrow those terms for 3D architecture use or defer them explicitly.
