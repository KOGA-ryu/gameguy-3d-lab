Packet-Type: task
Packet-ID: 3D-LAB-0005
Status: completed
Owner: planner_dex
Target: gameguy-3d-lab

# 3D-LAB-0005: No-Dirty Compiler Audit

## Objective

Audit compiler scripts for hardcoded output paths and generated-output side effects.

Do not refactor compilers in this task. Produce a matrix that tells future workers which compilers are safe, which support `--output-root`, and which need output-root refactors.

## Scope

Work only in:

`/Users/kogaryu/gameguy-3d-lab`

Review scripts matching:

- `scripts/compile_*.py`
- `scripts/create_*.py`
- `scripts/audit_*.py`
- `scripts/validate_*.py`

Allowed report outputs:

- `workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/report.md`
- `workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/compiler_output_matrix.json`
- `workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/receipt.json`

## Non-Goals

- Do not edit compiler behavior.
- Do not run compilers that write generated outputs.
- Do not run Blender.
- Do not generate assets, maps, renders, meshes, screenshots, or proof outputs.
- Do not touch the old Mac prototype repo.
- Do not stage, commit, or push unless explicitly instructed after reporting.

## Required Work

For each reviewed script, classify:

- `script_path`
- `script_kind`: `compile | create | audit | validate`
- `reads_source_paths`
- `writes_output_paths`
- `hardcoded_output_paths`
- `supports_output_root`
- `can_run_without_dirtying_repo`
- `depends_on_generated_fixture`
- `recommended_action`

Recommended actions:

- `KEEP_SAFE`
- `ADD_OUTPUT_ROOT`
- `ADD_READONLY_MODE`
- `SPLIT_SOURCE_AND_RENDER`
- `DEFER`

## Output Requirements

Create:

`workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/`

Files:

- `report.md`
- `compiler_output_matrix.json`
- `receipt.json`

## Acceptance Criteria

- Every matching compiler/create/audit/validate script is classified.
- No compiler is run if it writes generated outputs.
- Matrix JSON parses.
- Report clearly identifies top 5 output-root refactor targets.
- No media/proof/mesh files are created.
- No old Mac prototype files are touched.
- Repo remains unstaged unless user explicitly says to commit.

## Validation

Run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
python3 -m json.tool workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/compiler_output_matrix.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/receipt.json >/dev/null
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

## Report Back

Report back with:

- Number of scripts reviewed.
- Which scripts are safe.
- Which scripts need `--output-root`.
- Top 5 recommended refactors.
- Validation results.
- Recommended next task.
