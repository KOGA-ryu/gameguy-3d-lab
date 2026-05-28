# Workflow Registry

This folder is the lightweight command surface for Mac-side cleanup, planning, review, and Dex handoffs.

It is not engine source.

## Folder Layout

```text
goal/workflow/
  inbox/
  reports/
  decisions/
  registry.md
```

## Folder Roles

- `inbox/`: work orders and prompts waiting for a Dex.
- `reports/`: completed worker/reviewer packets.
- `decisions/`: human-approved keep/fix/delete decisions.
- `registry.md`: active ownership rules and workflow structure.

## Ownership Boundaries

### 3D / Architecture Domain

Current active cleanup/build domain:

- `mosaic_dungeon_floor_v0/contracts/`
- `mosaic_dungeon_floor_v0/data/architecture/`
- `mosaic_dungeon_floor_v0/scripts/` for 3D architecture, terrain, building, pathway, Blender proof, and asset mill work
- `mosaic_dungeon_floor_v0/goal/architecture/` for generated proof outputs and reports

### Protected 2D Domain

Do not touch unless explicitly assigned by the user:

- `mosaic_dungeon_floor_v0/pattern_lab_2d/`
- 2D recipes
- 2D scripts
- 2D SVG/PNG outputs
- 2D ornament/asset codex material

### Gitignore

Do not change `.gitignore` from this workflow unless the user explicitly assigns that task.

## Decision Buckets

Use these exact buckets:

- `FIX_POLISH`: has value; improve or clean it.
- `PROMOTE_SOURCE`: commit as real source.
- `DELETE_GENERATED`: disposable generated output.
- `LEAVE_PROTECTED`: belongs to another Dex/domain.
- `DEFER`: not decided yet.

Do not use archive/reference as the default. If something has value, fix or polish it. If it has no value and is generated, delete it after approval.

## Packet Shape

Every future packet should live in one folder:

```text
goal/workflow/reports/<packet-id>/
  report.md
  receipt.json
  optional_matrix.json
```

Keep packet names stable and descriptive:

```text
3D-0007-generator-dependency-review
JAN-0002-generated-output-delete
REV-0003-code-quality-review
```

## Source And Output Rule

Engine source belongs in source folders:

- `contracts/`
- `data/`
- `scripts/`

Generated proof belongs in generated folders:

- `goal/architecture/`

Workflow evidence belongs here:

- `goal/workflow/`

Do not mix these lanes without an explicit promotion decision.

