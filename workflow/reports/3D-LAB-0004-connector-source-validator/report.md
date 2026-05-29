# 3D-LAB-0004: Connector Source Validator

## Result

Added a source-only connector validator:

```bash
python3 scripts/validate_connector_source_v0.py
python3 scripts/validate_connector_source_v0.py --json-report /tmp/connector_source_validation.json
```

The validator reads only:

- `data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- `data/architecture/assets/connectors/connector_asset_recipes_v0/*.json`
- `data/architecture/assets/connectors/connector_placement_policy_v0.json`

It does not run connector generation, Blender, renderers, or mesh output.

## Checks Implemented

The validator fails with actionable file/field/asset messages for:

- missing or malformed connector manifest JSON
- missing manifest recipe path
- missing manifest-listed recipe file
- malformed recipe JSON
- recipe `asset_id` mismatch against the manifest entry
- duplicate connector IDs
- missing required source connector IDs
- missing or malformed placement policy JSON
- placement policy references to unknown connector asset IDs
- missing required connection types
- connection types without placement rules
- bridge rules missing deck, rail, or abutment asset references

It also checks basic recipe shape for required fields, positive dimensions, non-empty sockets, non-empty semantic roles, non-empty proof primitive records, and required no-claim flags.

## Validation Result

Current connector source passes:

- recipes loaded: `9`
- required connection types: `5`
- errors: `0`

Machine-readable result:

- `workflow/reports/3D-LAB-0004-connector-source-validator/validation_result.json`

## Files Changed

- `scripts/validate_connector_source_v0.py`
- `data/architecture/assets/connectors/README.md`
- `workflow/reports/3D-LAB-0004-connector-source-validator/report.md`
- `workflow/reports/3D-LAB-0004-connector-source-validator/validation_result.json`
- `workflow/reports/3D-LAB-0004-connector-source-validator/receipt.json`

## Validation

Commands run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
python3 -m py_compile scripts/validate_connector_source_v0.py
python3 scripts/validate_connector_source_v0.py
python3 scripts/validate_connector_source_v0.py --json-report workflow/reports/3D-LAB-0004-connector-source-validator/validation_result.json
python3 -m json.tool workflow/reports/3D-LAB-0004-connector-source-validator/validation_result.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0004-connector-source-validator/receipt.json >/dev/null
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

Result: PASS for validator, JSON validation, and Python compile. The path/media scans printed no matching files.

## Non-Goals Respected

- Did not run connector generation.
- Did not run Blender.
- Did not create assets, maps, renders, meshes, screenshots, or proof outputs.
- Did not touch the old Mac prototype repo.
- Did not stage, commit, or push.

## Next Recommended Task

Proceed to `3D-LAB-0005`: audit compiler/create/audit/validate scripts for hardcoded output paths and generated-output side effects.
