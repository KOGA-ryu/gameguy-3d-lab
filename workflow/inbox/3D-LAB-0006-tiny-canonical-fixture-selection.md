Packet-Type: task
Packet-ID: 3D-LAB-0006
Status: completed
Owner: planner_dex
Target: gameguy-3d-lab

# 3D-LAB-0006: Tiny Canonical Fixture Selection

## Objective

Select and define one tiny canonical fixture for future source-only validation tests.

This fixture should be small, human-readable, deterministic, and useful for map/path/building/connector validation. It should not be a generated proof map.

## Scope

Work only in:

`/Users/kogaryu/gameguy-3d-lab`

Allowed source fixture path:

- `data/architecture/test_fixtures/tiny_map_building_connector_fixture_v0.json`

Allowed docs/report outputs:

- `data/architecture/test_fixtures/README.md`
- `workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/report.md`
- `workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/fixture_decision_record.json`
- `workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/receipt.json`

## Non-Goals

- Do not generate maps from compilers.
- Do not run Blender.
- Do not create assets, renders, meshes, screenshots, or proof outputs.
- Do not create a large fixture.
- Do not model movement/pathfinding.
- Do not touch the old Mac prototype repo.
- Do not stage, commit, or push unless explicitly instructed after reporting.

## Fixture Requirements

The fixture should contain only enough data to test source validators:

- a small hex or map cell set, preferably fewer than 12 cells
- one building plug
- one connector/path segment
- one connector asset reference
- one terrain height change
- one no-claims block
- deterministic IDs

It should be readable by humans and safe to use as a future unit-test fixture.

## Output Requirements

Create:

- `data/architecture/test_fixtures/README.md`
- `data/architecture/test_fixtures/tiny_map_building_connector_fixture_v0.json`
- `workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/report.md`
- `workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/fixture_decision_record.json`
- `workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/receipt.json`

## Acceptance Criteria

- Fixture JSON parses.
- Fixture is small and human-readable.
- Fixture references existing connector asset IDs.
- Fixture includes map, terrain, building plug, and connector path concepts.
- Fixture does not include render/media/mesh/proof output.
- No old Mac prototype files are touched.
- Repo remains unstaged unless user explicitly says to commit.

## Validation

Run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
python3 -m json.tool data/architecture/test_fixtures/tiny_map_building_connector_fixture_v0.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/fixture_decision_record.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0006-tiny-canonical-fixture-selection/receipt.json >/dev/null
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

## Report Back

Report back with:

- Fixture path.
- Fixture contents summary.
- Why it is the canonical tiny fixture.
- Validation results.
- Recommended next task.
