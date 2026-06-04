# 3D-LAB-0094 Measurement-Backed ASCII Plan V0

## Goal

Correct the image-to-ASCII direction: ASCII is a cheap source planning layer,
not a preview gimmick.

## Added

- `contracts/gameguy_ascii_plan_v0.json`
- `data/architecture/ascii_plans/single_post_ascii_plan_fixture_v0.json`
- `docs/research/ascii_geometry_planning_v0/README.md`
- `docs/research/ascii_geometry_planning_v0/measurement_backed_ascii_grid_v0.md`
- `scripts/validate_gameguy_ascii_plan_v0.py`

## Updated

- `README.md`
- `contracts/README.md`
- `scripts/validate_generation_pipeline_v0.py`

## Design Decision

Every important ASCII character can carry measurement and tooling metadata:

```text
glyph + row/col + source pixel bbox + local X/Z bbox + region + operation hints
```

This lets the repo inspect and correct detailed forms cheaply before creating a
source recipe, compiling a tool plan, or touching Blender.

## Rejection Note

The generated post concept sheet is rejected as source direction. It should not
be used to choose post styles.

The accepted source direction is:

```text
measurement-backed ASCII plans
```

## Boundary

This slice does not generate final post styles, run an image-to-ASCII renderer,
compile assets, execute Blender, render images, or export meshes.

## Validation

Validation run:

- JSON parse for contract, fixture, and receipt
- Python compile for the ASCII plan validator and pipeline validator
- `python3 scripts/validate_gameguy_ascii_plan_v0.py`
- `git diff --check`
- git status check
