# 3D-LAB-0006: Tiny Canonical Fixture Selection

## Result

Selected and defined one canonical tiny source fixture:

```text
data/architecture/test_fixtures/tiny_map_building_connector_fixture_v0.json
```

Added fixture docs:

```text
data/architecture/test_fixtures/README.md
```

## Fixture Contents

The fixture contains:

- 7 axial hex cells
- one explicit terrain height change from `0.0m` to `0.5m`
- one tiny building record
- one building plug
- one road/path plug
- one connector/path segment
- one connector asset reference: `measured_pathway_slab_unit_v1`
- references to the connector manifest and placement policy
- a no-claims block

It is source-only and deterministic. It is not a generated proof map.

## Why This Fixture

This is the smallest useful shape for future source validators because it crosses the important seams without requiring generated outputs:

- map cell identity
- terrain height metadata
- building plug metadata
- connector/path declaration
- existing connector source asset ID
- no-claims enforcement

The fixture is intentionally not a movement/pathfinding test, not a renderer test, and not a Blender proof scene.

## Validation

Commands run from `/Users/kogaryu/gameguy-3d-lab`:

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

Result: PASS for fixture JSON, decision record JSON, receipt JSON, repo JSON, and Python compile. The path/media scans printed no matching files.

## Non-Goals Respected

- Did not generate maps from compilers.
- Did not run Blender.
- Did not create assets, renders, meshes, screenshots, or proof outputs.
- Did not create a large fixture.
- Did not model movement or pathfinding.
- Did not touch the old Mac prototype repo.
- Did not stage, commit, or push.

## Next Recommended Task

Add a small source-only fixture validator that checks this fixture against connector source data, then use it as the test fixture while adding read-only or output-root modes to the compiler chain.
