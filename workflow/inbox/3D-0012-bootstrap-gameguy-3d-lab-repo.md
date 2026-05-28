Packet-Type: task
Packet-ID: 3D-0012
Status: proposed
Owner: planner_dex
Target: mac_3d_architecture

# 3D-0012: Bootstrap `gameguy-3d-lab` Repo

## Objective

Create a clean standalone 3D/map/building lab repo from the useful 3D side of the current Mac prototype and push it to:

`git@github.com:KOGA-ryu/gameguy-3d-lab.git`

The current repo remains the historical prototype/reference. The new repo becomes the clean 3D architecture/map/building work lane.

## Scope

Source repo:

- `/Users/kogaryu/game`

Destination working folder:

- `/Users/kogaryu/gameguy-3d-lab`

Destination git remote:

- `git@github.com:KOGA-ryu/gameguy-3d-lab.git`

Allowed work:

- Create the destination folder.
- Copy only approved 3D/shared files into it.
- Initialize or reset git metadata in the destination.
- Configure the destination remote.
- Commit the clean baseline.
- Push the clean baseline to GitHub.
- Write a report packet in the source repo workflow reports.

## Non-Goals

- Do not mutate `/Users/kogaryu/game` except for the report packet.
- Do not move files out of the source repo.
- Do not delete source repo files.
- Do not copy `pattern_lab_2d/`.
- Do not copy 2D generated outputs, 2D scripts, 2D recipes, or ornament codex.
- Do not copy generated proof folders unless they are explicitly converted into small source fixtures.
- Do not copy `.git` from the source repo.
- Do not preserve the old git history in the new repo unless the user explicitly asks.
- Do not run Blender.
- Do not create renders, meshes, screenshots, or new generated proof outputs.

## Required Inputs

Read before acting:

- `/Users/kogaryu/game/goal/workflow/registry.md`
- `/Users/kogaryu/game/goal/workflow/decisions/3d_cleanup_policy_v0.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/report.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0009-refactor-connector-compiler-to-source-manifest/report.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0010-connector-placement-policy-source-lane/report.md`
- `/Users/kogaryu/game/goal/workflow/reports/3D-0011-connector-output-root-config/report.md`

## Approved Copy Set

Copy these source/shared lanes if present:

- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/data/architecture/`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/geometry_dictionary/`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/contracts/`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/docs/research/architectural_measurements/`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/docs/research/map_generation_full_docs_v0/`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/docs/research/terrain_tile_bending_seams_v0/`
- `/Users/kogaryu/game/goal/workflow/`

Copy selected 3D/map/building scripts only:

- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/compile_*`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/create_*`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/validate_*`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/blender_*`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0/scripts/audit_hex_terrain_deformation_v0.py`

After copying scripts, remove obvious 2D-only scripts from the destination if they slipped in:

- pattern lab contact sheets
- mosaic tile builders
- quilez visual lab renderers
- 2D ornament/category/flower scripts
- Aseprite scripts
- Zoo/package scripts

Use file content and names to decide. If unsure, leave the file out and record it in the report.

## Required Destination Shape

Create a clearer destination layout:

```text
/Users/kogaryu/gameguy-3d-lab/
  README.md
  data/architecture/
  geometry_dictionary/
  contracts/
  docs/research/
  scripts/
  workflow/
  .gitignore
```

Do not preserve `mosaic_dungeon_floor_v0/` as the root folder name in the new repo. Flatten the useful 3D/shared lanes into the destination structure above.

## Required README

Create `/Users/kogaryu/gameguy-3d-lab/README.md` with:

- What this repo is.
- What this repo is not.
- Source origin: Mac prototype repo.
- Current scope: 3D architecture, terrain, map graphs, connector assets, Blender proof scripts, workflow packets.
- Explicit exclusion: 2D Pattern Lab and ornament generation are not part of this repo.
- Current language: Python prototype scripts, future C++ port planned.
- Validation commands.
- No production, structural, fabrication, historical, or game-engine integration claims.

## Required `.gitignore`

Create a small destination `.gitignore` that excludes:

```text
__pycache__/
*.pyc
.DS_Store
.venv/
build/
dist/
target/
*.blend1
*.blend2
*.png
*.jpg
*.jpeg
*.gif
*.webp
*.obj
*.gltf
*.glb
*.fbx
goal/architecture/blender_tests/
goal/receipts/
```

Do not import the source repo `.gitignore`.

## Validation

Run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
git status --short
```

Also verify:

```bash
test ! -d pattern_lab_2d
find . -path '*pattern_lab_2d*' -print
find . -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
```

Expected:

- No `pattern_lab_2d` files.
- No media/mesh/proof render files.
- JSON parses.
- Python scripts compile or known Blender-only import limitations are documented.

## Git Requirements

In `/Users/kogaryu/gameguy-3d-lab`:

```bash
git init
git remote add origin git@github.com:KOGA-ryu/gameguy-3d-lab.git
git add .
git commit -m "Bootstrap 3D architecture lab"
git push -u origin main
```

If default branch is not `main`, create/switch to `main`.

If push fails due to auth or remote setup, stop and report the exact error. Do not attempt credential workarounds.

## Report Output

Create this report packet in the source repo:

`/Users/kogaryu/game/goal/workflow/reports/3D-0012-bootstrap-gameguy-3d-lab-repo/`

Files:

- `report.md`
- `copied_file_manifest.json`
- `excluded_file_manifest.json`
- `validation_report.json`
- `receipt.json`

The report must include:

- Destination path.
- Remote URL.
- Files copied.
- Files excluded and why.
- Validation commands and results.
- Commit hash in destination repo.
- Push result.
- Any blocked items.
- Next recommended task for the new repo.

## Acceptance Criteria

- `/Users/kogaryu/gameguy-3d-lab` exists.
- It is a git repo with remote `git@github.com:KOGA-ryu/gameguy-3d-lab.git`.
- It contains no `pattern_lab_2d`.
- It contains no media/render/mesh proof files.
- It contains source/shared 3D architecture lanes only.
- It has a clean baseline commit.
- It is pushed to GitHub, or push failure is clearly reported.
- Source repo is only modified by the report packet.

## Report Back

Report back with:

- New repo path.
- Remote URL.
- Commit hash.
- Push status.
- What was copied.
- What was intentionally excluded.
- Validation status.
- Next task.
