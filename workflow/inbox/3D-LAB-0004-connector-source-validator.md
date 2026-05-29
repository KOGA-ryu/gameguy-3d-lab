Packet-Type: task
Packet-ID: 3D-LAB-0004
Status: completed
Owner: planner_dex
Target: gameguy-3d-lab

# 3D-LAB-0004: Connector Source Validator

## Objective

Add a small source validator for connector assets and connector placement policy.

The validator must check source JSON only. It must not require generated connector output, Blender, renders, or mesh files.

## Scope

Work only in:

`/Users/kogaryu/gameguy-3d-lab`

Allowed source files:

- `scripts/validate_connector_source_v0.py`
- `data/architecture/assets/connectors/README.md` if documentation needs one narrow update.

Inputs to validate:

- `data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- `data/architecture/assets/connectors/connector_asset_recipes_v0/*.json`
- `data/architecture/assets/connectors/connector_placement_policy_v0.json`

Allowed report outputs:

- `workflow/reports/3D-LAB-0004-connector-source-validator/report.md`
- `workflow/reports/3D-LAB-0004-connector-source-validator/validation_result.json`
- `workflow/reports/3D-LAB-0004-connector-source-validator/receipt.json`

## Non-Goals

- Do not run connector generation.
- Do not run Blender.
- Do not create assets, maps, renders, meshes, screenshots, or proof outputs.
- Do not edit connector recipe dimensions unless a JSON field is structurally invalid.
- Do not port anything to C++.
- Do not touch the old Mac prototype repo.
- Do not stage, commit, or push unless explicitly instructed after reporting.

## Required Checks

The validator must fail with actionable messages if:

- connector manifest JSON is missing or malformed.
- manifest recipe path is missing.
- a manifest-listed recipe file does not exist.
- a recipe JSON does not parse.
- a recipe `asset_id` does not match the manifest entry.
- duplicate connector IDs exist.
- placement policy JSON is missing or malformed.
- placement policy references an unknown connector asset ID.
- required connection types are missing.
- a connection type has no placement rule.
- bridge rules lack deck, rail, or abutment references.

Required connection types for v0:

- `road_threshold`
- `flat_pathway`
- `ramp_pathway`
- `stepped_pathway`
- `bridge_link`

Required source connector IDs for v0:

- `measured_pathway_slab_unit_v1`
- `measured_threshold_landing_v1`
- `measured_ramp_pathway_unit_v1`
- `measured_stepped_pathway_unit_v1`
- `measured_bridge_deck_unit_v1`
- `measured_bridge_abutment_v1`
- `measured_bridge_rail_unit_v1`
- `measured_retaining_wall_unit_v1`
- `measured_curb_edge_unit_v1`

## CLI

Add:

```bash
python3 scripts/validate_connector_source_v0.py
python3 scripts/validate_connector_source_v0.py --json-report /tmp/connector_source_validation.json
```

Default behavior should print a concise PASS/FAIL summary. `--json-report` should write machine-readable validation details.

## Output Requirements

Create:

`workflow/reports/3D-LAB-0004-connector-source-validator/`

Files:

- `report.md`
- `validation_result.json`
- `receipt.json`

## Acceptance Criteria

- `scripts/validate_connector_source_v0.py` exists.
- Validator runs without generated connector output.
- Validator passes on current connector source.
- Failure messages name the failing file, field, and connector ID where possible.
- JSON report parses.
- Python compile passes.
- No media/proof/mesh files are created.
- No old Mac prototype files are touched.
- Repo remains unstaged unless user explicitly says to commit.

## Validation

Run from `/Users/kogaryu/gameguy-3d-lab`:

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

## Report Back

Report back with:

- Validator behavior.
- Checks implemented.
- Validation result.
- Files changed.
- Recommended next task.
