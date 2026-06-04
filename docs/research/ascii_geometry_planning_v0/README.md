# ASCII Geometry Planning V0

## Purpose

This lane corrects the direction for image-to-ASCII work.

ASCII is not just a preview or a novelty render. In this repo it should become a
cheap source planning layer:

```text
reference image / sketch / manual ASCII
-> measurement-backed ASCII grid
-> annotated characters and regions
-> source recipe or tool-plan hints
-> Blender only after promotion and validation
```

The user's point is that high-detail ASCII can be inspected cheaply before the
repo commits to Blender, rendering, or final geometry.

## Rejection Note

The generated post concept sheet is rejected as source direction. Do not use it
to select post styles.

The accepted direction is:

```text
detailed ASCII planning + measurements attached to characters
```

## New Contract

The planning contract is:

```text
contracts/gameguy_ascii_plan_v0.json
```

The first tiny fixture is:

```text
data/architecture/ascii_plans/single_post_ascii_plan_fixture_v0.json
```

## Local Prototype Audit

The local archive `ascii_blender_dryrun_v0.zip` was inspected as reference
material. It has a useful backend shape:

```text
typed operations -> ASCII projection -> validation -> Blender script emitter
```

Implementation update: the archive was later implemented directly at:

```text
ascii_blender_dryrun_v0/
```

The extracted package code is preserved from the zip. It is a standalone
dry-run prototype, not a rewrite of the measured ASCII plan contract.

The measured ASCII plan contract remains canonical for source planning because
it attaches source pixels, model-space bounds, regions, operation hints, and
Blender tool hints to selected characters.

Audit note:

```text
docs/research/ascii_geometry_planning_v0/ascii_blender_dryrun_zip_audit_v0.md
```

Validate with:

```bash
python3 scripts/validate_gameguy_ascii_plan_v0.py
```

## What A Character Can Mean

Each ASCII character cell can carry:

- row and column
- source pixel bounding box
- local model-space X/Z bounding box
- brightness
- edge strength
- edge direction
- geometry role
- region ID
- measurement references
- operation hints
- Blender tool hints
- depth intent such as raised, recessed, mass edge, or guide

That is the bridge from cheap ASCII inspection to later Blender tooling.

## Why This Matters

The repo can use ASCII to decide:

- silhouette
- cap/base/shaft proportions
- which detail zones are raised or recessed
- where sockets belong
- where cuts, bevels, panels, ribs, and collars should be
- which regions deserve Blender operations later

This lets the user reject or correct a plan before a render contract exists.

## Boundary

This lane does not generate final post styles, render images, execute Blender,
create meshes, or claim final art direction.

Blender tools listed in an ASCII plan are hints until a later compiler promotes
the plan into a source recipe or `gameguy_tool_plan_v0`.
