Packet-Type: task
Packet-ID: 3D-LAB-0007
Status: completed
Owner: planner_dex
Target: gameguy-3d-lab

# 3D-LAB-0007: Add Output-Root To Integrated Map Scene Compiler

## Objective

Refactor `scripts/compile_integrated_map_scene_v0.py` so it can run without dirtying the repo by writing all generated outputs under an explicit output root.

This is the first no-dirty compiler refactor after the audit. The goal is not new map behavior. The goal is clean, repeatable validation.

## Scope

Work only in:

`/Users/kogaryu/gameguy-3d-lab`

Primary source file:

- `scripts/compile_integrated_map_scene_v0.py`

Allowed report outputs:

- `workflow/reports/3D-LAB-0007-output-root-integrated-map-scene/report.md`
- `workflow/reports/3D-LAB-0007-output-root-integrated-map-scene/output_root_validation.json`
- `workflow/reports/3D-LAB-0007-output-root-integrated-map-scene/receipt.json`

Temporary validation output:

- `/tmp/gameguy_3d_lab_0007_integrated_map_scene/`

## Non-Goals

- Do not change map design.
- Do not change terrain/building/connector semantics.
- Do not run Blender.
- Do not create renders, meshes, screenshots, or proof media.
- Do not commit generated outputs.
- Do not touch the old Mac prototype repo.
- Do not refactor downstream compilers unless strictly required to prevent accidental output writes.
- Do not port anything to C++.
- Do not stage, commit, or push unless explicitly instructed after reporting.

## Required Inputs

Read before editing:

- `workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/report.md`
- `workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/compiler_output_matrix.json`
- `scripts/compile_integrated_map_scene_v0.py`
- `data/architecture/map_templates/integrated_map_scene_v0.json`
- `data/architecture/test_fixtures/tiny_map_building_connector_fixture_v0.json`

## Required Work

1. Inspect hardcoded output paths in `compile_integrated_map_scene_v0.py`.
2. Add an explicit CLI output-root option.
3. Preserve default behavior when no output root is provided.
4. Ensure output paths derive from the selected output root when provided.
5. Add flags to prevent hidden downstream regeneration if the script currently triggers other compilers.
6. Make validation able to run into `/tmp/gameguy_3d_lab_0007_integrated_map_scene/`.
7. Report exactly which outputs are produced under the temp root.

Preferred CLI shape:

```bash
python3 scripts/compile_integrated_map_scene_v0.py
python3 scripts/compile_integrated_map_scene_v0.py \
  --output-root /tmp/gameguy_3d_lab_0007_integrated_map_scene \
  --no-regenerate-downstream
```

If the existing script requires a different flag name, use the narrowest consistent option and explain it.

## Output-Root Rules

When `--output-root` is passed:

- all generated integrated scene JSON/report/receipt outputs must go under that root.
- no files under repo `goal/` should be written.
- source input paths must remain in repo `data/`, `contracts/`, `geometry_dictionary/`, or explicitly passed fixtures.
- generated temp output must not be staged.

If the compiler cannot run without downstream generated fixtures yet, fail clearly and document the missing fixture dependency. Do not silently regenerate into repo `goal/`.

## Output Requirements

Create:

`workflow/reports/3D-LAB-0007-output-root-integrated-map-scene/`

Files:

- `report.md`
- `output_root_validation.json`
- `receipt.json`

`output_root_validation.json` must include:

- command run
- output_root
- files_written_under_output_root
- repo_goal_files_written
- behavior_counts_before_after_if_available
- validation_status
- warnings

The receipt must include:

- `packet_id`
- `status`
- `files_changed`
- `output_root_supported`
- `default_behavior_preserved`
- `temp_output_validation_passed`
- `repo_goal_dirtying_prevented`
- `blender_run`
- `generated_media_created`
- `old_repo_touched`
- `staged_or_committed`
- `recommended_next_task`

## Acceptance Criteria

- `compile_integrated_map_scene_v0.py` supports an explicit output root.
- Default behavior remains available.
- Temp-output validation does not write to repo `goal/`.
- If downstream generated fixtures block no-dirty execution, the script fails with an actionable message instead of regenerating repo outputs.
- JSON validation passes for temp outputs and reports.
- Python compile passes.
- No media/proof/mesh files are created.
- No old Mac prototype files are touched.
- Repo remains unstaged unless user explicitly says to commit.

## Validation

Run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
python3 -m py_compile scripts/compile_integrated_map_scene_v0.py
rm -rf /tmp/gameguy_3d_lab_0007_integrated_map_scene
python3 scripts/compile_integrated_map_scene_v0.py \
  --output-root /tmp/gameguy_3d_lab_0007_integrated_map_scene \
  --no-regenerate-downstream
find /tmp/gameguy_3d_lab_0007_integrated_map_scene -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0007-output-root-integrated-map-scene/output_root_validation.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0007-output-root-integrated-map-scene/receipt.json >/dev/null
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

Expected:

- validation passes or fails only with a clear missing-fixture explanation.
- no repo `goal/` output is written during temp-output validation.
- no media/mesh/proof output appears.

## Report Back

Report back with:

- CLI options added.
- Output paths made configurable.
- Whether downstream regeneration was blocked or avoided.
- Temp-output validation result.
- Any missing fixture dependencies.
- Recommended next task.
